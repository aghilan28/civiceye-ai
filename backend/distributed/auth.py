from __future__ import annotations

import hashlib
import hmac
import json
import time
from secrets import compare_digest
from typing import Any

from backend.config import settings
from backend.security.auth import session_registry
from backend.telemetry.metrics import metrics_store


class WorkerAuthenticationError(RuntimeError):
    pass


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def sign_worker_payload(secret: str, payload: dict[str, Any], timestamp: int | None = None) -> tuple[int, str]:
    if not secret:
        raise WorkerAuthenticationError("CIVICEYE_WORKER_SHARED_SECRET is required for signed worker authentication")
    issued_at = timestamp or int(time.time())
    body = f"{issued_at}.{canonical_json(payload)}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return issued_at, signature


def verify_worker_payload(
    *,
    secret: str,
    payload: dict[str, Any],
    timestamp: int,
    signature: str,
    max_skew_seconds: int = 300,
) -> None:
    if not secret:
        raise WorkerAuthenticationError("CIVICEYE_WORKER_SHARED_SECRET is not configured")
    if abs(int(time.time()) - timestamp) > max_skew_seconds:
        metrics_store.record_worker_heartbeat_failure(str(payload.get("worker_id") or "unknown"), "timestamp_skew")
        raise WorkerAuthenticationError("Worker signature timestamp is outside the accepted replay window")
    _, expected = sign_worker_payload(secret, payload, timestamp)
    if not compare_digest(expected, signature):
        metrics_store.record_worker_heartbeat_failure(str(payload.get("worker_id") or "unknown"), "bad_signature")
        raise WorkerAuthenticationError("Worker registration signature is invalid")
    replay_key = f"worker:{payload.get('worker_id','unknown')}:{timestamp}:{signature}"
    if session_registry.seen(replay_key, settings.worker_replay_window_seconds):
        metrics_store.record_worker_heartbeat_failure(str(payload.get("worker_id") or "unknown"), "replay")
        raise WorkerAuthenticationError("Worker signed request replay detected")


def signed_payload_body(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in {"signature", "timestamp"}}


def verify_signed_worker_request(*, secret: str, payload: dict[str, Any], worker_id: str | None = None) -> dict[str, Any]:
    timestamp = payload.get("timestamp")
    signature = payload.get("signature")
    if timestamp is None or not signature:
        raise WorkerAuthenticationError("Signed worker request requires timestamp and signature")
    body = signed_payload_body(payload)
    if worker_id is not None and body.get("worker_id") != worker_id:
        raise WorkerAuthenticationError("Signed worker request worker_id does not match route")
    verify_worker_payload(secret=secret, payload=body, timestamp=int(timestamp), signature=str(signature))
    return body


def validate_worker_secret_strength(secret: str) -> None:
    weak = {"", "change-me-before-production", "replace-with-production-secret", "replace-with-worker-shared-secret"}
    if secret in weak or len(secret) < 24:
        raise WorkerAuthenticationError("CIVICEYE_WORKER_SHARED_SECRET must be a high-entropy shared secret")
