from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.config import settings
from backend.security.auth import Principal, decode_token, issue_token, require_principal, session_registry


router = APIRouter(prefix="/api/v1/auth", tags=["civiceye-auth"])


class LoginRequest(BaseModel):
    email: str
    password: str
    municipality_id: str | None = None
    role: str = "municipality_admin"
    device_id: str | None = None


class RefreshRequest(BaseModel):
    refreshToken: str


class AuthUser(BaseModel):
    id: str
    name: str
    email: str
    role: str
    municipalityId: str | None = None


class AuthSession(BaseModel):
    user: AuthUser
    accessToken: str
    refreshToken: str
    expiresAt: str


@router.post("/login", response_model=AuthSession)
async def login(payload: LoginRequest) -> AuthSession:
    if len(payload.password) < 8:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    session_id = str(uuid4())
    user_id = f"user-{payload.email.lower()}"
    access = issue_token(
        user_id=user_id,
        role=payload.role,
        municipality_id=payload.municipality_id,
        session_id=session_id,
        device_id=payload.device_id,
    )
    refresh = issue_token(
        user_id=user_id,
        role=payload.role,
        municipality_id=payload.municipality_id,
        session_id=session_id,
        device_id=payload.device_id,
        refresh=True,
    )
    return AuthSession(
        user=AuthUser(
            id=user_id,
            name=payload.email.split("@", 1)[0].replace(".", " ").title(),
            email=payload.email,
            role=payload.role,
            municipalityId=payload.municipality_id,
        ),
        accessToken=access,
        refreshToken=refresh,
        expiresAt=(datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)).isoformat(),
    )


@router.post("/refresh", response_model=AuthSession)
async def refresh(payload: RefreshRequest) -> AuthSession:
    principal = decode_token(payload.refreshToken, expected_type="refresh")
    access = issue_token(
        user_id=principal.user_id,
        role=principal.role,
        municipality_id=principal.municipality_id,
        session_id=principal.session_id,
        device_id=principal.device_id,
    )
    refresh_token = issue_token(
        user_id=principal.user_id,
        role=principal.role,
        municipality_id=principal.municipality_id,
        session_id=principal.session_id,
        device_id=principal.device_id,
        refresh=True,
    )
    email = principal.user_id.removeprefix("user-")
    return AuthSession(
        user=AuthUser(
            id=principal.user_id,
            name=email.split("@", 1)[0].replace(".", " ").title(),
            email=email,
            role=principal.role,
            municipalityId=principal.municipality_id,
        ),
        accessToken=access,
        refreshToken=refresh_token,
        expiresAt=(datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)).isoformat(),
    )


@router.post("/logout")
async def logout(principal: Principal = Depends(require_principal)) -> dict[str, bool]:
    session_registry.revoke(principal.session_id)
    return {"ok": True}
