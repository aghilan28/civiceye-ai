from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
from typing import Annotated, Any
from uuid import uuid4

import jwt
from fastapi import Depends, Header, HTTPException, WebSocket, status

from backend.config import settings


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "citizen": {"incident:create", "incident:read", "media:upload"},
    "municipality_admin": {
        "incident:create",
        "incident:read",
        "incident:assign",
        "incident:resolve",
        "analytics:read",
        "ai:manage",
        "tenant:manage",
        "billing:read",
    },
    "field_worker": {"incident:read", "incident:resolve", "field:update", "media:upload"},
    "contractor": {"incident:read", "incident:resolve", "field:update"},
    "emergency_operator": {"incident:read", "incident:escalate", "emergency:manage", "analytics:read"},
    "supervisor": {"incident:read", "incident:assign", "incident:resolve", "analytics:read", "field:manage"},
    "system_admin": {
        "incident:create",
        "incident:read",
        "incident:assign",
        "incident:resolve",
        "incident:escalate",
        "analytics:read",
        "ai:manage",
        "tenant:manage",
        "billing:read",
        "billing:write",
        "system:manage",
    },
    "platform_admin": {
        "incident:create",
        "incident:read",
        "incident:assign",
        "incident:resolve",
        "incident:escalate",
        "analytics:read",
        "ai:manage",
        "tenant:manage",
        "billing:read",
        "billing:write",
        "system:manage",
    },
    "admin": {"incident:read", "incident:assign", "incident:resolve", "analytics:read", "tenant:manage"},
    "operator": {"incident:create", "incident:read", "incident:assign", "incident:escalate", "analytics:read"},
}

ROLE_TO_DB_ENUM: dict[str, str] = {
    "citizen": "CITIZEN",
    "municipality_admin": "MUNICIPALITY_ADMIN",
    "field_worker": "FIELD_WORKER",
    "contractor": "CONTRACTOR",
    "emergency_operator": "EMERGENCY_OPERATOR",
    "supervisor": "SUPERVISOR",
    "system_admin": "SYSTEM_ADMIN",
    "platform_admin": "SYSTEM_ADMIN",
    "admin": "MUNICIPALITY_ADMIN",
    "operator": "SUPERVISOR",
}


class SessionRegistry:
    def __init__(self) -> None:
        self._active_refresh_tokens: dict[str, str] = {}
        self._revoked_sessions: set[str] = set()
        self._seen_signatures: dict[str, float] = {}

    def register_refresh(self, session_id: str, token_id: str) -> None:
        self._active_refresh_tokens[session_id] = token_id
        self._revoked_sessions.discard(session_id)

    def revoke(self, session_id: str) -> None:
        self._active_refresh_tokens.pop(session_id, None)
        self._revoked_sessions.add(session_id)

    def is_revoked(self, session_id: str) -> bool:
        return session_id in self._revoked_sessions

    def validate_refresh(self, session_id: str, token_id: str | None) -> bool:
        return self._active_refresh_tokens.get(session_id) == token_id

    def seen(self, signature: str, window_seconds: int) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        self._seen_signatures = {key: value for key, value in self._seen_signatures.items() if now - value <= window_seconds}
        if signature in self._seen_signatures:
            return True
        self._seen_signatures[signature] = now
        return False


session_registry = SessionRegistry()


def validate_jwt_secret_strength() -> None:
    weak = {"", "change-me-before-production", "replace-with-production-secret"}
    if settings.jwt_secret in weak or len(settings.jwt_secret) < 24:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CIVICEYE_JWT_SECRET must be a high-entropy secret before authentication is enabled",
        )


def _secret_candidates() -> list[str]:
    secrets = [settings.jwt_secret]
    previous = os.getenv("CIVICEYE_JWT_SECRET_PREVIOUS", "")
    if previous:
        secrets.append(previous)
    return [secret for secret in secrets if secret]


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str
    municipality_id: str | None
    session_id: str
    device_id: str | None = None
    token_id: str | None = None
    expires_at: datetime | None = None

    def can(self, permission: str) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, set()) or self.role in {"system_admin", "platform_admin"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def issue_token(
    *,
    user_id: str,
    role: str,
    municipality_id: str | None,
    session_id: str | None = None,
    device_id: str | None = None,
    refresh: bool = False,
) -> str:
    validate_jwt_secret_strength()
    lifetime = timedelta(days=settings.refresh_token_days) if refresh else timedelta(minutes=settings.access_token_minutes)
    token_id = str(uuid4())
    issued_at = _now()
    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "sub": user_id,
        "role": role,
        "municipality_id": municipality_id,
        "sid": session_id or str(uuid4()),
        "device_id": device_id,
        "jti": token_id,
        "typ": "refresh" if refresh else "access",
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + lifetime).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    if refresh:
        session_registry.register_refresh(payload["sid"], token_id)
    return token


def decode_token(token: str, *, expected_type: str = "access") -> Principal:
    validate_jwt_secret_strength()
    payload = None
    for secret in _secret_candidates():
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                issuer=settings.jwt_issuer,
                leeway=30,
                options={"require": ["exp", "iat", "iss", "sub", "sid", "jti", "typ"]},
            )
            break
        except jwt.PyJWTError:
            continue
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    if payload.get("typ") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    session_id = str(payload.get("sid") or "")
    subject = str(payload.get("sub") or "")
    token_id = str(payload.get("jti") or "")
    if not session_id or not subject or not token_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token claims")
    if session_registry.is_revoked(session_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been revoked")
    if expected_type == "refresh" and not session_registry.validate_refresh(session_id, token_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been rotated")
    return Principal(
        user_id=subject,
        role=str(payload.get("role") or "citizen"),
        municipality_id=payload.get("municipality_id"),
        session_id=session_id,
        device_id=payload.get("device_id"),
        token_id=token_id,
        expires_at=datetime.fromtimestamp(int(payload.get("exp") or 0), tz=timezone.utc) if payload.get("exp") else None,
    )


def optional_principal(authorization: Annotated[str | None, Header()] = None) -> Principal | None:
    if not authorization:
        if settings.require_auth:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header is required")
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is required")
    return decode_token(token)


def require_principal(principal: Annotated[Principal | None, Depends(optional_principal)]) -> Principal:
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required")
    return principal


def require_permission(permission: str):
    def dependency(principal: Annotated[Principal, Depends(require_principal)]) -> Principal:
        if not principal.can(permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission}")
        return principal

    return dependency


def websocket_principal(websocket: WebSocket) -> Principal | None:
    token = websocket.query_params.get("token")
    if not token:
        authorization = websocket.headers.get("authorization", "")
        scheme, _, candidate = authorization.partition(" ")
        token = candidate if scheme.lower() == "bearer" else None
    if not token:
        return None
    try:
        return decode_token(token)
    except HTTPException:
        return None


def validate_request_signature(signature: str, *, replay_window_seconds: int = 300) -> None:
    if session_registry.seen(signature, replay_window_seconds):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Replay detected")
