from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def _path_from_env(name: str, default: Path) -> Path:
    value = os.getenv(name)
    return Path(value).expanduser().resolve() if value else default.resolve()


@dataclass(frozen=True)
class BackendSettings:
    app_name: str = "CivicEye AI Backend"
    api_version: str = "2.0.0"
    model_version: str = os.getenv("CIVICEYE_MODEL_VERSION", "pothole-yolov8-v0.2.0")
    weights_path: Path = _path_from_env("CIVICEYE_MODEL_WEIGHTS", ROOT_DIR / "ai" / "checkpoints" / "best.pt")
    fallback_weights_path: Path = _path_from_env("CIVICEYE_FALLBACK_WEIGHTS", ROOT_DIR / "yolov8n.pt")
    storage_dir: Path = _path_from_env("CIVICEYE_STORAGE_DIR", ROOT_DIR / "runtime" / "ai")
    confidence_threshold: float = float(os.getenv("CIVICEYE_CONFIDENCE", "0.25"))
    iou_threshold: float = float(os.getenv("CIVICEYE_IOU", "0.50"))
    image_size: int = int(os.getenv("CIVICEYE_IMAGE_SIZE", "960"))
    frame_skip: int = max(0, int(os.getenv("CIVICEYE_FRAME_SKIP", "1")))
    batch_size: int = max(1, int(os.getenv("CIVICEYE_BATCH_SIZE", "4")))
    max_upload_mb: int = int(os.getenv("CIVICEYE_MAX_UPLOAD_MB", "768"))
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "")
    jwt_secret: str = os.getenv("CIVICEYE_JWT_SECRET", "change-me-before-production")
    jwt_issuer: str = os.getenv("CIVICEYE_JWT_ISSUER", "civiceye")
    access_token_minutes: int = int(os.getenv("CIVICEYE_ACCESS_TOKEN_MINUTES", "30"))
    refresh_token_days: int = int(os.getenv("CIVICEYE_REFRESH_TOKEN_DAYS", "14"))
    require_auth: bool = os.getenv("CIVICEYE_REQUIRE_AUTH", "false").lower() in {"1", "true", "yes"}
    websocket_region: str = os.getenv("CIVICEYE_REGION", "local")
    websocket_node_id: str = os.getenv("CIVICEYE_NODE_ID", "local-api")
    websocket_event_channel: str = os.getenv("CIVICEYE_WS_REDIS_CHANNEL", "civiceye:events")
    redis_queue_prefix: str = os.getenv("CIVICEYE_REDIS_QUEUE_PREFIX", "civiceye:queue")
    inference_stream: str = os.getenv("CIVICEYE_INFERENCE_STREAM", "civiceye:inference:jobs")
    inference_consumer_group: str = os.getenv("CIVICEYE_INFERENCE_CONSUMER_GROUP", "civiceye-workers")
    inference_dlq_stream: str = os.getenv("CIVICEYE_INFERENCE_DLQ_STREAM", "civiceye:inference:dead-letter")
    inference_checkpoint_hash: str = os.getenv("CIVICEYE_INFERENCE_CHECKPOINT_HASH", "civiceye:inference:checkpoints")
    worker_shared_secret: str = os.getenv("CIVICEYE_WORKER_SHARED_SECRET", "")
    worker_runtime_version: str = os.getenv("CIVICEYE_WORKER_RUNTIME_VERSION", api_version)
    worker_heartbeat_ttl_seconds: int = int(os.getenv("CIVICEYE_WORKER_HEARTBEAT_TTL_SECONDS", "45"))
    worker_heartbeat_jitter_seconds: int = int(os.getenv("CIVICEYE_WORKER_HEARTBEAT_JITTER_SECONDS", "20"))
    worker_zombie_grace_seconds: int = int(os.getenv("CIVICEYE_WORKER_ZOMBIE_GRACE_SECONDS", "120"))
    inference_job_timeout_seconds: int = int(os.getenv("CIVICEYE_INFERENCE_JOB_TIMEOUT_SECONDS", "300"))
    inference_max_attempts: int = int(os.getenv("CIVICEYE_INFERENCE_MAX_ATTEMPTS", "3"))
    inference_retry_backoff_seconds: int = int(os.getenv("CIVICEYE_INFERENCE_RETRY_BACKOFF_SECONDS", "30"))
    enable_local_cpu_fallback: bool = os.getenv("CIVICEYE_ENABLE_LOCAL_CPU_FALLBACK", "true").lower() in {"1", "true", "yes"}
    dependency_connect_attempts: int = int(os.getenv("CIVICEYE_DEPENDENCY_CONNECT_ATTEMPTS", "12"))
    dependency_retry_seconds: float = float(os.getenv("CIVICEYE_DEPENDENCY_RETRY_SECONDS", "2"))
    dependency_probe_timeout_seconds: float = float(os.getenv("CIVICEYE_DEPENDENCY_PROBE_TIMEOUT_SECONDS", "5"))
    kafka_bootstrap_servers: str = os.getenv("CIVICEYE_KAFKA_BOOTSTRAP_SERVERS", "")
    object_storage_provider: str = os.getenv("CIVICEYE_OBJECT_STORAGE_PROVIDER", "local")
    object_storage_bucket: str = os.getenv("CIVICEYE_OBJECT_STORAGE_BUCKET", "civiceye-media")
    object_storage_endpoint: str = os.getenv("CIVICEYE_OBJECT_STORAGE_ENDPOINT", "")
    object_storage_region: str = os.getenv("CIVICEYE_OBJECT_STORAGE_REGION", os.getenv("AWS_REGION", "us-east-1"))
    object_storage_access_key: str = os.getenv("CIVICEYE_OBJECT_STORAGE_ACCESS_KEY", os.getenv("AWS_ACCESS_KEY_ID", ""))
    object_storage_secret_key: str = os.getenv("CIVICEYE_OBJECT_STORAGE_SECRET_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", ""))
    object_storage_public_base_url: str = os.getenv("CIVICEYE_OBJECT_STORAGE_PUBLIC_BASE_URL", "")
    object_storage_signed_url_seconds: int = int(os.getenv("CIVICEYE_OBJECT_STORAGE_SIGNED_URL_SECONDS", "900"))
    object_storage_artifact_ttl_days: int = int(os.getenv("CIVICEYE_OBJECT_STORAGE_ARTIFACT_TTL_DAYS", "30"))
    model_registry_path: Path = _path_from_env("CIVICEYE_MODEL_REGISTRY_PATH", ROOT_DIR / "ai" / "models" / "registry.json")
    model_checksum_required: bool = os.getenv("CIVICEYE_MODEL_CHECKSUM_REQUIRED", "false").lower() in {"1", "true", "yes"}
    worker_replay_window_seconds: int = int(os.getenv("CIVICEYE_WORKER_REPLAY_WINDOW_SECONDS", "300"))
    websocket_session_ttl_seconds: int = int(os.getenv("CIVICEYE_WEBSOCKET_SESSION_TTL_SECONDS", "3600"))
    websocket_max_messages_per_minute: int = int(os.getenv("CIVICEYE_WEBSOCKET_MAX_MESSAGES_PER_MINUTE", "120"))
    inference_signature_required: bool = os.getenv("CIVICEYE_INFERENCE_SIGNATURE_REQUIRED", "false").lower() in {"1", "true", "yes"}
    inference_shared_secret: str = os.getenv("CIVICEYE_INFERENCE_SHARED_SECRET", "")
    civic_api_prefix: str = os.getenv("CIVICEYE_API_PREFIX", "/api/v1")
    rate_limit_per_minute: int = int(os.getenv("CIVICEYE_RATE_LIMIT_PER_MINUTE", "240"))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CIVICEYE_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    )

    @property
    def resolved_weights_path(self) -> Path:
        if self.weights_path.exists():
            return self.weights_path
        if self.fallback_weights_path.exists():
            return self.fallback_weights_path
        return self.weights_path


settings = BackendSettings()
