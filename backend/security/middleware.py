from __future__ import annotations

import re
from collections import defaultdict, deque
from time import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.config import settings
from backend.telemetry.logger import log_event
from backend.telemetry.metrics import metrics_store
from backend.telemetry.tracing import trace_from_headers


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        tenant_id = request.headers.get("X-CivicEye-Tenant-Id") or request.headers.get("X-Municipality-Id")
        context = trace_from_headers(request.headers, tenant_id=tenant_id)
        request.state.correlation_id = context.correlation_id
        request.state.request_id = context.request_id
        request.state.trace_id = context.trace_id
        request.state.tenant_id = tenant_id
        started = time()
        log_event("civiceye.request", "request_started", f"{request.method} {request.url.path}", municipality_id=tenant_id)
        response = await call_next(request)
        elapsed_ms = (time() - started) * 1000
        metrics_store.record_db_latency("http_request", elapsed_ms)
        response.headers.update(context.to_headers())
        response.headers["X-CivicEye-Request-Id"] = context.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), geolocation=(self), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data: blob: https:; media-src 'self' blob: https:; "
            "connect-src 'self' http: https: ws: wss:; frame-ancestors 'none'"
        )
        log_event("civiceye.request", "request_completed", f"{request.method} {request.url.path}", status=response.status_code)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=settings.rate_limit_per_minute * 2))

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client = request.client.host if request.client else "unknown"
        now = time()
        hits = self._hits[client]
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= settings.rate_limit_per_minute:
            return Response("Rate limit exceeded", status_code=429)
        hits.append(now)
        return await call_next(request)


_SUSPICIOUS_UPLOAD_RE = re.compile(rb"(<script|javascript:|<iframe|onerror\s*=)", re.IGNORECASE)


def validate_upload_safety(data: bytes, content_type: str | None, allowed_prefixes: tuple[str, ...]) -> None:
    from fastapi import HTTPException

    if content_type and not content_type.startswith(allowed_prefixes):
        raise HTTPException(status_code=415, detail="Unsupported upload content type")
    probe = data[: min(len(data), 4096)]
    if _SUSPICIOUS_UPLOAD_RE.search(probe):
        raise HTTPException(status_code=400, detail="Upload failed malware-safe content inspection")
