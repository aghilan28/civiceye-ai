from __future__ import annotations

import json
import hashlib
import hmac
from pathlib import Path
from time import time
from typing import Any
from urllib.parse import quote, urlencode
from uuid import uuid4

import cv2
import numpy as np

from backend.config import settings
from backend.telemetry.logger import log_event


class StorageService:
    def __init__(self) -> None:
        self.root = settings.storage_dir
        self.uploads = self.root / "uploads"
        self.outputs = self.root / "outputs"
        self.logs = self.root / "logs"
        for path in (self.uploads, self.outputs, self.logs):
            path.mkdir(parents=True, exist_ok=True)
        self.provider = settings.object_storage_provider.lower()

    def save_upload(self, data: bytes, suffix: str) -> Path:
        safe_suffix = suffix if suffix.startswith(".") else f".{suffix}"
        path = self.uploads / f"{uuid4()}{safe_suffix.lower()}"
        path.write_bytes(data)
        log_event("civiceye.storage", "media_persisted", "Upload persisted", status=self.provider, civiceye_object_key=self.object_key(path))
        return path

    def save_annotated_image(self, image: np.ndarray) -> Path:
        path = self.outputs / f"{uuid4()}.jpg"
        ok = cv2.imwrite(str(path), image, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not ok:
            raise RuntimeError(f"Failed to write annotated image to {path}")
        log_event("civiceye.storage", "artifact_persisted", "Annotated inference artifact persisted", status=self.provider, civiceye_object_key=self.object_key(path))
        return path

    def save_json(self, payload: dict, name: str | None = None) -> Path:
        path = self.logs / f"{name or uuid4()}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log_event("civiceye.storage", "json_artifact_persisted", "JSON artifact persisted", status=self.provider, civiceye_object_key=self.object_key(path))
        return path

    def public_url(self, path: Path) -> str:
        key = self.object_key(path)
        if self.provider != "local" and settings.object_storage_public_base_url:
            return f"{settings.object_storage_public_base_url.rstrip('/')}/{quote(key)}"
        return f"/files/{key}"

    def object_key(self, path: Path) -> str:
        return path.resolve().relative_to(self.root.resolve()).as_posix()

    def resolve_public_path(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if not str(candidate).startswith(str(self.root.resolve())):
            raise ValueError("Invalid file path")
        return candidate

    def signed_upload_url(self, object_key: str, content_type: str, expires_seconds: int | None = None) -> dict[str, Any]:
        if self.provider == "local":
            return {
                "provider": "local",
                "method": "PUT",
                "url": f"/api/v1/storage/local-upload/{quote(object_key)}",
                "expires_at_epoch": int(time()) + (expires_seconds or settings.object_storage_signed_url_seconds),
                "headers": {"Content-Type": content_type},
            }
        return self._s3_presigned_url("PUT", object_key, content_type, expires_seconds)

    def signed_download_url(self, object_key: str, expires_seconds: int | None = None) -> dict[str, Any]:
        if self.provider == "local":
            return {
                "provider": "local",
                "method": "GET",
                "url": f"/files/{quote(object_key)}",
                "expires_at_epoch": int(time()) + (expires_seconds or settings.object_storage_signed_url_seconds),
                "headers": {},
            }
        return self._s3_presigned_url("GET", object_key, "", expires_seconds)

    def diagnostics(self) -> dict[str, Any]:
        has_credentials = bool(settings.object_storage_access_key and settings.object_storage_secret_key)
        return {
            "provider": self.provider,
            "bucket": settings.object_storage_bucket,
            "endpoint": settings.object_storage_endpoint or "aws-s3",
            "region": settings.object_storage_region,
            "credentials_configured": self.provider == "local" or has_credentials,
            "artifact_ttl_days": settings.object_storage_artifact_ttl_days,
            "storage_root": str(self.root),
        }

    def _s3_presigned_url(self, method: str, object_key: str, content_type: str, expires_seconds: int | None) -> dict[str, Any]:
        if not settings.object_storage_access_key or not settings.object_storage_secret_key:
            raise RuntimeError(f"{self.provider} object storage requires access key and secret key")
        expires = expires_seconds or settings.object_storage_signed_url_seconds
        endpoint = settings.object_storage_endpoint.rstrip("/")
        if not endpoint:
            endpoint = f"https://{settings.object_storage_bucket}.s3.{settings.object_storage_region}.amazonaws.com"
            canonical_uri = "/" + quote(object_key)
            host = f"{settings.object_storage_bucket}.s3.{settings.object_storage_region}.amazonaws.com"
            base_url = endpoint
        else:
            canonical_uri = "/" + quote(settings.object_storage_bucket) + "/" + quote(object_key)
            host = endpoint.split("://", 1)[-1]
            base_url = endpoint
        algorithm = "AWS4-HMAC-SHA256"
        service = "s3"
        now = time()
        amz_date = _amz_date(now)
        date_stamp = amz_date[:8]
        credential_scope = f"{date_stamp}/{settings.object_storage_region}/{service}/aws4_request"
        signed_headers = "host"
        query = {
            "X-Amz-Algorithm": algorithm,
            "X-Amz-Credential": f"{settings.object_storage_access_key}/{credential_scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(expires),
            "X-Amz-SignedHeaders": signed_headers,
        }
        canonical_query = urlencode(sorted(query.items()), quote_via=quote)
        canonical_request = "\n".join([method, canonical_uri, canonical_query, f"host:{host}\n", signed_headers, "UNSIGNED-PAYLOAD"])
        string_to_sign = "\n".join([algorithm, amz_date, credential_scope, hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()])
        signing_key = _s3_signing_key(settings.object_storage_secret_key, date_stamp, settings.object_storage_region)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        return {
            "provider": self.provider,
            "method": method,
            "url": f"{base_url}{canonical_uri}?{canonical_query}&X-Amz-Signature={signature}",
            "expires_at_epoch": int(now) + expires,
            "headers": {"Content-Type": content_type} if content_type else {},
            "bucket": settings.object_storage_bucket,
            "object_key": object_key,
        }


def _amz_date(epoch_seconds: float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _s3_signing_key(secret_key: str, date_stamp: str, region: str) -> bytes:
    key_date = hmac.new(("AWS4" + secret_key).encode("utf-8"), date_stamp.encode("utf-8"), hashlib.sha256).digest()
    key_region = hmac.new(key_date, region.encode("utf-8"), hashlib.sha256).digest()
    key_service = hmac.new(key_region, b"s3", hashlib.sha256).digest()
    return hmac.new(key_service, b"aws4_request", hashlib.sha256).digest()


storage_service = StorageService()
