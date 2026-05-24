from __future__ import annotations

import asyncio
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from backend.config import ROOT_DIR, settings
from backend.database.postgres import DatabaseUnavailable, postgres_pool
from backend.distributed.orchestration import distributed_orchestrator
from backend.distributed.redis_client import redis_coordinator
from backend.gpu.device import get_device_info
from backend.inference.model_loader import model_loader
from backend.storage.files import storage_service
from backend.websocket.operations_bus import operation_bus


@dataclass(frozen=True)
class RuntimeCheck:
    name: str
    status: str
    required: bool
    detail: str
    remediation: str | None = None
    metadata: dict[str, Any] | None = None


class RuntimeDiagnostics:
    async def collect(self, include_model_load: bool = False) -> dict[str, Any]:
        checks = [
            self.environment(),
            self.model_artifact(include_model_load=include_model_load),
            self.storage(),
            self.object_storage(),
            await self.postgres(),
            await self.redis(),
            await self.distributed_queue(),
            await self.worker_connectivity(),
            await self.dead_letter_queue(),
            self.websocket(),
            self.auth(),
            await self.kubernetes_manifests(),
            self.provider_deployment_assets(),
        ]
        status = "ok" if all(check.status == "ok" or not check.required for check in checks) else "degraded"
        if any(check.status == "failed" and check.required for check in checks):
            status = "failed"
        return {
            "status": status,
            "service": settings.app_name,
            "api_version": settings.api_version,
            "checks": [asdict(check) for check in checks],
            "gpu": asdict(get_device_info()),
            "model": model_loader.metadata(),
        }

    def environment(self) -> RuntimeCheck:
        missing = [
            name
            for name in ("DATABASE_URL", "REDIS_URL", "CIVICEYE_JWT_SECRET", "CIVICEYE_WORKER_SHARED_SECRET")
            if not os.getenv(name)
        ]
        weak_secret = settings.jwt_secret in {"", "change-me-before-production", "replace-with-production-secret"}
        weak_worker_secret = settings.worker_shared_secret in {"", "change-me-before-production", "replace-with-production-secret"}
        if missing or weak_secret or weak_worker_secret:
            detail = "Missing or unsafe production environment values."
            remediation = "Set DATABASE_URL, REDIS_URL, CIVICEYE_JWT_SECRET, and CIVICEYE_WORKER_SHARED_SECRET before launch."
            return RuntimeCheck(
                name="environment",
                status="failed",
                required=True,
                detail=detail,
                remediation=remediation,
                metadata={"missing": missing, "weak_jwt_secret": weak_secret, "weak_worker_secret": weak_worker_secret},
            )
        return RuntimeCheck(name="environment", status="ok", required=True, detail="Required runtime environment is present.")

    def model_artifact(self, include_model_load: bool) -> RuntimeCheck:
        path = settings.resolved_weights_path
        if not path.exists():
            return RuntimeCheck(
                name="ai_model_artifact",
                status="failed",
                required=True,
                detail=f"YOLO weights not found at {path}.",
                remediation="Set CIVICEYE_MODEL_WEIGHTS to the trained best.pt artifact.",
            )
        if include_model_load:
            try:
                model_loader.load()
            except Exception as exc:
                return RuntimeCheck(
                    name="ai_model_artifact",
                    status="failed",
                    required=True,
                    detail=f"YOLO model failed to load: {exc}",
                    remediation="Verify ultralytics, torch/CUDA compatibility, and the best.pt artifact.",
                )
        return RuntimeCheck(
            name="ai_model_artifact",
            status="ok",
            required=True,
            detail="YOLO weights are present and loadable." if include_model_load else "YOLO weights are present.",
            metadata={"weights_path": str(path), "loaded": model_loader.loaded},
        )

    def storage(self) -> RuntimeCheck:
        try:
            settings.storage_dir.mkdir(parents=True, exist_ok=True)
            probe = settings.storage_dir / ".civiceye-write-probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return RuntimeCheck(
                name="media_storage",
                status="ok",
                required=True,
                detail="Runtime storage directory is writable.",
                metadata={"storage_dir": str(settings.storage_dir)},
            )
        except Exception as exc:
            return RuntimeCheck(
                name="media_storage",
                status="failed",
                required=True,
                detail=f"Runtime storage is not writable: {exc}",
                remediation="Mount a writable persistent volume for CIVICEYE_STORAGE_DIR.",
            )

    def object_storage(self) -> RuntimeCheck:
        diagnostics = storage_service.diagnostics()
        if diagnostics["provider"] != "local" and not diagnostics["credentials_configured"]:
            return RuntimeCheck(
                name="object_storage",
                status="failed",
                required=True,
                detail=f"{diagnostics['provider']} object storage is selected but credentials are not configured.",
                remediation="Set CIVICEYE_OBJECT_STORAGE_ACCESS_KEY and CIVICEYE_OBJECT_STORAGE_SECRET_KEY or switch provider to local.",
                metadata=diagnostics,
            )
        supported = {"local", "s3", "minio", "r2"}
        if diagnostics["provider"] not in supported:
            return RuntimeCheck(
                name="object_storage",
                status="failed",
                required=True,
                detail=f"Unsupported object storage provider: {diagnostics['provider']}.",
                remediation=f"Use one of {sorted(supported)}.",
                metadata=diagnostics,
            )
        return RuntimeCheck(
            name="object_storage",
            status="ok",
            required=True,
            detail="Object storage provider configuration is internally valid.",
            metadata=diagnostics,
        )

    async def postgres(self) -> RuntimeCheck:
        try:
            async with postgres_pool.acquire() as connection:
                version = await connection.fetchval("SELECT version()")
                postgis = await connection.fetchval("SELECT COALESCE(extversion, '') FROM pg_extension WHERE extname = 'postgis'")
                migration_count = await connection.fetchval(
                    "SELECT count(*)::int FROM information_schema.tables WHERE table_schema = 'public'"
                )
            return RuntimeCheck(
                name="postgres_postgis",
                status="ok",
                required=True,
                detail="PostgreSQL connection succeeded.",
                metadata={"version": version, "postgis": postgis or "not_installed", "public_tables": migration_count},
            )
        except DatabaseUnavailable as exc:
            return RuntimeCheck(
                name="postgres_postgis",
                status="failed",
                required=True,
                detail=str(exc),
                remediation="Set DATABASE_URL and run Prisma migrations against a PostGIS-enabled database.",
            )
        except Exception as exc:
            return RuntimeCheck(
                name="postgres_postgis",
                status="failed",
                required=True,
                detail=f"PostgreSQL validation failed: {exc}",
                remediation="Verify database reachability, credentials, migrations, and PostGIS extension availability.",
            )

    async def redis(self) -> RuntimeCheck:
        if not settings.redis_url:
            return RuntimeCheck(
                name="redis",
                status="failed",
                required=True,
                detail="REDIS_URL is not configured.",
                remediation="Set REDIS_URL to the production Redis endpoint used for queues and websocket coordination.",
            )
        try:
            import redis.asyncio as redis

            client = redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
            pong = await client.ping()
            info = await client.info(section="server")
            persistence = await client.config_get("appendonly")
            await client.aclose()
            return RuntimeCheck(
                name="redis",
                status="ok",
                required=True,
                detail="Redis connection succeeded.",
                metadata={"ping": bool(pong), "redis_version": info.get("redis_version"), "appendonly": persistence.get("appendonly")},
            )
        except Exception as exc:
            return RuntimeCheck(
                name="redis",
                status="failed",
                required=True,
                detail=f"Redis validation failed: {exc}",
                remediation="Verify Redis is reachable and supports persistence for queue reliability.",
            )

    async def distributed_queue(self) -> RuntimeCheck:
        try:
            async with postgres_pool.acquire() as connection:
                tables = await connection.fetch(
                    """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name IN ('inference_jobs','inference_workers','inference_job_events')
                    """
                )
                counts = await connection.fetch(
                    """
                    SELECT "queueName" AS queue_name, status::text AS status, count(*)::int AS count
                    FROM inference_jobs
                    GROUP BY "queueName", status
                    """
                )
            table_names = {row["table_name"] for row in tables}
            missing = {"inference_jobs", "inference_workers", "inference_job_events"} - table_names
            if missing:
                return RuntimeCheck(
                    name="distributed_queue",
                    status="failed",
                    required=True,
                    detail=f"Distributed queue persistence tables are missing: {sorted(missing)}.",
                    remediation="Run Prisma migrations before starting the backend or workers.",
                )
            if settings.redis_url:
                async with redis_coordinator.client() as client:
                    try:
                        await client.xgroup_create(settings.inference_stream, settings.inference_consumer_group, id="0", mkstream=True)
                    except Exception as exc:
                        if "BUSYGROUP" not in str(exc):
                            raise
                    stream_info = await client.xinfo_stream(settings.inference_stream)
                    group_info = await client.xinfo_groups(settings.inference_stream)
            return RuntimeCheck(
                name="distributed_queue",
                status="ok",
                required=True,
                detail="Postgres inference queue tables and Redis stream are reachable.",
                metadata={
                    "queues": [dict(row) for row in counts],
                    "stream": settings.inference_stream,
                    "stream_info": stream_info if settings.redis_url else None,
                    "consumer_groups": group_info if settings.redis_url else None,
                },
            )
        except Exception as exc:
            return RuntimeCheck(
                name="distributed_queue",
                status="failed",
                required=True,
                detail=f"Distributed queue validation failed: {exc}",
                remediation="Verify migrations are applied and Redis stream access is available.",
            )

    async def worker_connectivity(self) -> RuntimeCheck:
        try:
            topology = await distributed_orchestrator.topology()
            online = [worker for worker in topology["workers"] if worker["state"] == "ONLINE"]
            gpu_online = [worker for worker in online if worker["gpu_count"] > 0]
            status = "ok" if online else "degraded"
            return RuntimeCheck(
                name="worker_connectivity",
                status=status,
                required=False,
                detail="Online workers are registered." if online else "No inference workers are currently registered.",
                remediation="Start a CPU fallback worker or remote GPU worker for queued inference execution." if not online else None,
                metadata={"online_workers": len(online), "online_gpu_workers": len(gpu_online), "stale_workers": topology["stale_workers"]},
            )
        except Exception as exc:
            return RuntimeCheck(
                name="worker_connectivity",
                status="failed",
                required=False,
                detail=f"Worker topology validation failed: {exc}",
                remediation="Verify the distributed inference migration and worker heartbeat table.",
            )

    async def dead_letter_queue(self) -> RuntimeCheck:
        try:
            async with postgres_pool.acquire() as connection:
                dead = await connection.fetchval("SELECT count(*)::int FROM inference_jobs WHERE status = 'DEAD_LETTER'")
                retry = await connection.fetchval("SELECT count(*)::int FROM inference_jobs WHERE status = 'RETRY'")
            redis_detail: dict[str, Any] = {}
            if settings.redis_url:
                async with redis_coordinator.client() as client:
                    try:
                        redis_detail = await client.xinfo_stream(settings.inference_dlq_stream)
                    except Exception:
                        redis_detail = {"stream": settings.inference_dlq_stream, "exists": False}
            return RuntimeCheck(
                name="dead_letter_queue",
                status="ok",
                required=True,
                detail="Dead-letter queue state is inspectable.",
                metadata={"dead_letter_jobs": dead or 0, "retry_jobs": retry or 0, "redis_dlq": redis_detail},
            )
        except Exception as exc:
            return RuntimeCheck(
                name="dead_letter_queue",
                status="failed",
                required=True,
                detail=f"Dead-letter queue validation failed: {exc}",
                remediation="Verify inference job migrations and Redis DLQ stream access.",
            )

    def websocket(self) -> RuntimeCheck:
        health = operation_bus.health()
        return RuntimeCheck(
            name="websocket",
            status="ok",
            required=True,
            detail="Websocket operation bus is initialized.",
            metadata=health,
        )

    def auth(self) -> RuntimeCheck:
        if settings.require_auth and settings.jwt_secret in {"", "change-me-before-production", "replace-with-production-secret"}:
            return RuntimeCheck(
                name="auth",
                status="failed",
                required=True,
                detail="Authentication is required but JWT secret is unsafe.",
                remediation="Set a high-entropy CIVICEYE_JWT_SECRET.",
            )
        if settings.worker_shared_secret in {"", "change-me-before-production", "replace-with-production-secret"}:
            return RuntimeCheck(
                name="worker_auth",
                status="failed",
                required=True,
                detail="Worker shared secret is missing or unsafe.",
                remediation="Set CIVICEYE_WORKER_SHARED_SECRET on backend and every remote worker.",
            )
        return RuntimeCheck(name="worker_auth", status="ok", required=True, detail="Worker registration signatures are configured.")

    async def kubernetes_manifests(self) -> RuntimeCheck:
        required = [
            ROOT_DIR / "deploy" / "helm" / "gpu-worker" / "Chart.yaml",
            ROOT_DIR / "deploy" / "helm" / "gpu-worker" / "templates" / "deployment.yaml",
            ROOT_DIR / "deploy" / "helm" / "gpu-worker" / "values.yaml",
            ROOT_DIR / "deploy" / "gpu-worker" / "docker-compose.gpu-worker.yml",
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            return RuntimeCheck(
                name="cloud_gpu_deployment",
                status="failed",
                required=True,
                detail=f"GPU deployment assets are missing: {missing}",
                remediation="Create standalone GPU worker compose and Helm deployment assets.",
            )
        deployment = (ROOT_DIR / "deploy" / "helm" / "gpu-worker" / "templates" / "deployment.yaml").read_text(encoding="utf-8")
        missing_probe = "readinessProbe" not in deployment or "livenessProbe" not in deployment
        if missing_probe:
            return RuntimeCheck(
                name="cloud_gpu_deployment",
                status="failed",
                required=True,
                detail="GPU worker Helm deployment is missing readiness or liveness probes.",
                remediation="Add Kubernetes probes before deployment.",
            )
        return RuntimeCheck(name="cloud_gpu_deployment", status="ok", required=True, detail="GPU worker deployment assets and probes are present.")

    def provider_deployment_assets(self) -> RuntimeCheck:
        providers = {
            "runpod": ROOT_DIR / "deploy" / "gpu-worker" / "deploy-runpod.sh",
            "vast": ROOT_DIR / "deploy" / "gpu-worker" / "deploy-vast.sh",
            "aws": ROOT_DIR / "deploy" / "gpu-worker" / "deploy-cloud-vm.sh",
            "gcp": ROOT_DIR / "deploy" / "gpu-worker" / "deploy-cloud-vm.sh",
            "azure": ROOT_DIR / "deploy" / "gpu-worker" / "deploy-cloud-vm.sh",
            "lambda": ROOT_DIR / "deploy" / "gpu-worker" / "deploy-cloud-vm.sh",
        }
        missing = [name for name, path in providers.items() if not path.exists()]
        docs = ROOT_DIR / "docs" / "gpu-worker-deployment.md"
        if missing or not docs.exists():
            return RuntimeCheck(
                name="provider_gpu_deployment",
                status="failed",
                required=True,
                detail=f"Missing provider deployment assets: {missing}; docs_present={docs.exists()}",
                remediation="Add provider scripts and deployment troubleshooting docs.",
            )
        return RuntimeCheck(
            name="provider_gpu_deployment",
            status="ok",
            required=True,
            detail="Provider deployment scripts and GPU worker docs are present.",
            metadata={"providers": sorted(providers)},
        )


def source_uri_to_path(source_uri: str) -> Path | None:
    parsed = urlparse(source_uri)
    if parsed.scheme == "file":
        path = unquote(parsed.path)
        if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
            path = path[1:]
        return Path(path)
    if parsed.scheme in {"", "local"}:
        candidate = Path(parsed.path if parsed.scheme else source_uri)
        return candidate if candidate.exists() else None
    if parsed.scheme == "civiceye":
        relative = parsed.netloc + parsed.path
        candidate = settings.storage_dir / relative.lstrip("/")
        return candidate if candidate.exists() else None
    return None


runtime_diagnostics = RuntimeDiagnostics()


async def main() -> None:
    import json

    diagnostics = await runtime_diagnostics.collect(include_model_load=os.getenv("CIVICEYE_VALIDATE_MODEL_LOAD") == "1")
    print(json.dumps(diagnostics, indent=2, default=str))
    if diagnostics["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
