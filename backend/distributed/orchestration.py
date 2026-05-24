from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
import hashlib
from typing import Any
from uuid import uuid4

from asyncpg import Connection

from backend.config import settings
from backend.database.postgres import postgres_pool
from backend.distributed.auth import WorkerAuthenticationError, verify_worker_payload
from backend.distributed.redis_client import redis_coordinator
from backend.gpu.device import get_device_info
from backend.telemetry.metrics import metrics_store
from backend.websocket.operations_bus import operation_bus


WORKER_SELECT = """
SELECT id, "workerId" AS worker_id, state, "queueNames" AS queue_names, capabilities, "supportedModels" AS supported_models,
       "supportedClasses" AS supported_classes, "gpuCount" AS gpu_count, "gpuName" AS gpu_name, "cudaVersion" AS cuda_version,
       "torchVersion" AS torch_version, "vramTotalMb" AS vram_total_mb, "vramUsedMb" AS vram_used_mb,
       "activeJobCount" AS active_job_count, "maxConcurrentJobs" AS max_concurrent_jobs, "lastHeartbeatAt" AS last_heartbeat_at,
       "registeredAt" AS registered_at, "expiresAt" AS expires_at, "failureReason" AS failure_reason,
       "remoteAddress" AS remote_address, telemetry, "createdAt" AS created_at, "updatedAt" AS updated_at
FROM inference_workers
"""


def _json_dict(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


@dataclass(frozen=True)
class QueueRoute:
    queue_name: str
    requires_gpu: bool
    reason: str


class DistributedInferenceOrchestrator:
    def _job_claim_id(self, job_id: str, worker_id: str) -> str:
        digest = hashlib.sha256(f"{job_id}:{worker_id}:{settings.worker_shared_secret}".encode("utf-8")).hexdigest()
        return digest[:24]

    async def ensure_runtime(self) -> None:
        await postgres_pool.connect()
        await redis_coordinator.connect()
        await redis_coordinator.ensure_consumer_group(settings.inference_stream, settings.inference_consumer_group)
        metrics_store.record_dependency("orchestrator", True)

    def _assert_worker_compatible(self, runtime_version: str) -> None:
        worker_major = runtime_version.split(".", 1)[0]
        backend_major = settings.worker_runtime_version.split(".", 1)[0]
        if worker_major != backend_major:
            raise WorkerAuthenticationError(
                f"Worker runtime version {runtime_version} is incompatible with backend runtime {settings.worker_runtime_version}"
            )

    async def register_worker(
        self,
        *,
        worker_id: str,
        payload: dict[str, Any],
        timestamp: int,
        signature: str,
        remote_address: str | None = None,
    ) -> dict[str, Any]:
        signed = {key: value for key, value in payload.items() if key not in {"signature", "timestamp"}}
        verify_worker_payload(secret=settings.worker_shared_secret, payload=signed, timestamp=timestamp, signature=signature)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=settings.worker_heartbeat_ttl_seconds)
        if payload.get("worker_id") and payload["worker_id"] != worker_id:
            raise WorkerAuthenticationError("Worker payload worker_id does not match registration target")
        queue_names = payload.get("queue_names") or [payload.get("queue_name") or "gpu.high"]
        capabilities = payload.get("capabilities") or {}
        gpu = payload.get("gpu") or {}
        runtime_version = str(payload.get("runtime_version") or settings.worker_runtime_version)
        self._assert_worker_compatible(runtime_version)
        supported_models = payload.get("supported_models") or [settings.model_version]
        async with postgres_pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                INSERT INTO inference_workers (
                  id, "workerId", state, "queueNames", capabilities, "supportedModels", "supportedClasses",
                  "gpuCount", "gpuName", "cudaVersion", "torchVersion", "vramTotalMb", "vramUsedMb",
                  "activeJobCount", "maxConcurrentJobs", "lastHeartbeatAt", "registeredAt", "expiresAt",
                  "remoteAddress", telemetry, "updatedAt"
                )
                VALUES ($1, $2, 'ONLINE'::"InferenceWorkerState", $3, $4::jsonb, $5, $6,
                        $7, $8, $9, $10, $11, $12, 0, $13, $14, $14, $15, $16, $17::jsonb, now())
                ON CONFLICT ("workerId") DO UPDATE
                SET state = 'ONLINE'::"InferenceWorkerState",
                    "queueNames" = EXCLUDED."queueNames",
                    capabilities = EXCLUDED.capabilities,
                    "supportedModels" = EXCLUDED."supportedModels",
                    "supportedClasses" = EXCLUDED."supportedClasses",
                    "gpuCount" = EXCLUDED."gpuCount",
                    "gpuName" = EXCLUDED."gpuName",
                    "cudaVersion" = EXCLUDED."cudaVersion",
                    "torchVersion" = EXCLUDED."torchVersion",
                    "vramTotalMb" = EXCLUDED."vramTotalMb",
                    "vramUsedMb" = EXCLUDED."vramUsedMb",
                    "maxConcurrentJobs" = EXCLUDED."maxConcurrentJobs",
                    "lastHeartbeatAt" = EXCLUDED."lastHeartbeatAt",
                    "expiresAt" = EXCLUDED."expiresAt",
                    "failureReason" = NULL,
                    "remoteAddress" = EXCLUDED."remoteAddress",
                    telemetry = EXCLUDED.telemetry,
                    "updatedAt" = now()
                RETURNING *
                """,
                str(uuid4()),
                worker_id,
                queue_names,
                json.dumps({**capabilities, "runtime_version": runtime_version}),
                supported_models,
                payload.get("supported_classes") or ["pothole"],
                int(gpu.get("count") or (1 if capabilities.get("cuda_available") else 0)),
                gpu.get("name"),
                capabilities.get("cuda_version"),
                capabilities.get("torch_version"),
                gpu.get("vram_total_mb"),
                gpu.get("vram_used_mb"),
                int(payload.get("max_concurrent_jobs") or 1),
                now,
                expires,
                remote_address,
                json.dumps(payload.get("telemetry") or {}),
                )
        metrics_store.record_worker_registration_count("ONLINE", 1)
        await self._emit_worker_event("worker_registered", worker_id)
        metrics_store.record_orchestration_event("worker_registered")
        return dict(row)

    async def heartbeat(self, worker_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=settings.worker_heartbeat_ttl_seconds)
        gpu = payload.get("gpu") or {}
        capabilities = payload.get("capabilities") or {}
        async with postgres_pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                UPDATE inference_workers
                SET state = CASE WHEN state = 'DRAINING' THEN state ELSE 'ONLINE'::"InferenceWorkerState" END,
                    "activeJobCount" = $2,
                    "queueNames" = COALESCE($3, "queueNames"),
                    capabilities = CASE WHEN $4::jsonb = '{}'::jsonb THEN capabilities ELSE $4::jsonb END,
                    "supportedModels" = COALESCE($5, "supportedModels"),
                    "supportedClasses" = COALESCE($6, "supportedClasses"),
                    "vramUsedMb" = $7,
                    "lastHeartbeatAt" = $8,
                    "expiresAt" = $9,
                    "failureReason" = NULL,
                    telemetry = $10::jsonb,
                    "updatedAt" = now()
                WHERE "workerId" = $1
                RETURNING *
                """,
                worker_id,
                int(payload.get("active_job_count") or 0),
                payload.get("queue_names") or None,
                json.dumps({**capabilities, "runtime_version": payload.get("runtime_version") or settings.worker_runtime_version}),
                payload.get("supported_models") or None,
                payload.get("supported_classes") or None,
                gpu.get("vram_used_mb"),
                now,
                expires,
                json.dumps(payload.get("telemetry") or {}),
            )
            if row is None:
                raise WorkerAuthenticationError(f"Worker {worker_id} has not registered")
        metrics_store.record_worker_heartbeat(worker_id, row["state"], 0)
        metrics_store.record_worker_saturation(worker_id, row["state"], int(row["activeJobCount"] or 0), int(row["maxConcurrentJobs"] or 1))
        metrics_store.record_orchestration_event("worker_heartbeat")
        return dict(row)

    def route_for_job(self, *, model_type: str, priority: int, requested_queue: str | None, gpu_required: bool) -> QueueRoute:
        started = datetime.now(timezone.utc)
        if requested_queue:
            metrics_store.record_routing(requested_queue, "requested_queue")
            metrics_store.record_routing_latency(requested_queue, model_type, (datetime.now(timezone.utc) - started).total_seconds())
            return QueueRoute(requested_queue, gpu_required, "requested_queue")
        priority_class = "emergency" if priority >= 90 else "high" if priority >= 70 else "standard"
        queue = f"gpu.{priority_class}" if gpu_required else f"cpu.{priority_class}"
        reason = f"{model_type} priority {priority} routed by capability"
        metrics_store.record_routing(queue, reason)
        metrics_store.record_routing_latency(queue, model_type, (datetime.now(timezone.utc) - started).total_seconds())
        return QueueRoute(queue, gpu_required, reason)

    async def publish_job(self, job: dict[str, Any]) -> None:
        payload = {
            "job_id": job["id"],
            "queue_name": job["queue_name"],
            "municipality_id": job["municipality_id"],
            "model_id": job["model_id"],
            "model_type": job.get("model_type"),
            "source_uri": job["source_uri"],
            "priority": job["priority"],
            "attempts": job["attempts"],
            "deadline_at": job.get("deadline_at").isoformat() if job.get("deadline_at") else None,
        }
        async with redis_coordinator.client() as client:
            await redis_coordinator.ensure_consumer_group(settings.inference_stream, settings.inference_consumer_group)
            await client.xadd(settings.inference_stream, {"job": json.dumps(payload, default=str)}, maxlen=100000, approximate=True)
            await client.publish(f"{settings.redis_queue_prefix}:notifications", json.dumps({"type": "job_enqueued", **payload}, default=str))
            await redis_coordinator.record_checkpoint("last_job_published", json.dumps({"job_id": job["id"], "queue_name": job["queue_name"]}))
        metrics_store.record_queue_latency(job["queue_name"], "QUEUED", 0.0)
        metrics_store.record_orchestration_event("job_published")

    async def claim_job(self, worker_id: str, queue_names: list[str]) -> dict[str, Any] | None:
        await self.expire_workers()
        async with postgres_pool.acquire() as connection:
            async with connection.transaction():
                worker = await connection.fetchrow(
                    """
                    SELECT * FROM inference_workers
                    WHERE "workerId" = $1
                      AND state = 'ONLINE'
                      AND "expiresAt" > now()
                    FOR UPDATE
                    """,
                    worker_id,
                )
                if worker is None:
                    raise WorkerAuthenticationError(f"Worker {worker_id} is not online or heartbeat has expired")
                registered_queues = list(worker["queueNames"] or [])
                allowed_queues = [queue for queue in queue_names if queue in registered_queues]
                if not allowed_queues:
                    raise WorkerAuthenticationError(f"Worker {worker_id} is not registered for requested queues")
                if worker["activeJobCount"] >= worker["maxConcurrentJobs"]:
                    metrics_store.record_orchestration_retry("worker_saturated", queue_names[0] if queue_names else "unknown")
                    return None
                row = await connection.fetchrow(
                    """
                    SELECT ij.id, ij."municipalityId" AS municipality_id, ij."incidentId" AS incident_id,
                           ij."modelId" AS model_id, amr."modelType"::text AS model_type, ij."sourceUri" AS source_uri,
                           ij.status::text AS status, ij."queueName" AS queue_name, ij."batchKey" AS batch_key,
                           ij.priority, ij.attempts, ij."deadlineAt" AS deadline_at, ij.result, ij.error,
                           ij.telemetry, ij."scheduledAt" AS scheduled_at, ij."createdAt" AS created_at, ij."updatedAt" AS updated_at
                    FROM inference_jobs ij
                    JOIN ai_model_registry amr ON amr.id = ij."modelId"
                    WHERE ij.status IN ('QUEUED','RETRY')
                      AND ij."queueName" = ANY($1::text[])
                      AND amr.version = ANY($2::text[])
                      AND (ij."retryAfter" IS NULL OR ij."retryAfter" <= now())
                    ORDER BY ij.priority DESC, ij."scheduledAt" ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """,
                    allowed_queues,
                    list(worker["supportedModels"] or []),
                )
                if row is None:
                    return None
                claim_id = str(uuid4())
                trace_id = str(uuid4())
                timeout = timedelta(seconds=settings.inference_job_timeout_seconds)
                await connection.execute(
                    """
                    UPDATE inference_jobs
                    SET status = 'RUNNING'::"InferenceJobStatus",
                        "workerId" = $2,
                        "startedAt" = COALESCE("startedAt", now()),
                        "deadlineAt" = now() + $3::interval,
                        attempts = attempts + 1,
                        telemetry = telemetry || $4::jsonb,
                        "updatedAt" = now()
                    WHERE id = $1
                    """,
                    row["id"],
                    worker_id,
                    timeout,
                    json.dumps({"claim_id": claim_id, "trace_id": trace_id, "claimed_at": datetime.now(timezone.utc).isoformat()}),
                )
                await connection.execute(
                    """
                    UPDATE inference_workers
                    SET "activeJobCount" = "activeJobCount" + 1, "updatedAt" = now()
                    WHERE "workerId" = $1
                    """,
                    worker_id,
                )
                await connection.execute(
                    """
                    INSERT INTO inference_job_events (id, "jobId", "workerId", event, payload)
                    VALUES ($1, $2, $3, 'claimed', $4::jsonb)
                    """,
                    claim_id,
                    row["id"],
                    worker_id,
                    json.dumps({"queue_names": allowed_queues, "timeout_seconds": settings.inference_job_timeout_seconds, "claim_id": claim_id, "trace_id": trace_id}),
                )
        claimed = dict(row)
        claimed["worker_id"] = worker_id
        claimed["claim_id"] = claim_id
        claimed["trace_id"] = trace_id
        await self._emit_job_event("inference_job_claimed", claimed["id"], worker_id)
        metrics_store.record_orchestration_event("job_claimed")
        return claimed

    async def complete_job(self, worker_id: str, job_id: str, claim_id: str, result: dict[str, Any], latency_ms: int, telemetry: dict[str, Any], trace_id: str | None = None) -> None:
        async with postgres_pool.acquire() as connection:
            async with connection.transaction():
                job = await connection.fetchrow(
                    "SELECT id, status::text AS status, \"workerId\" AS worker_id, telemetry FROM inference_jobs WHERE id = $1 FOR UPDATE",
                    job_id,
                )
                if job is None:
                    raise RuntimeError(f"Inference job {job_id} was not found")
                if job["worker_id"] != worker_id:
                    raise RuntimeError(f"Inference job {job_id} is not claimed by worker {worker_id}")
                if job["status"] == "COMPLETED":
                    return
                if claim_id != _json_dict(job["telemetry"]).get("claim_id"):
                    raise RuntimeError("Inference job claim token mismatch")
                await connection.execute(
                    """
                    UPDATE inference_jobs
                    SET status = 'COMPLETED'::"InferenceJobStatus",
                        result = $3::jsonb,
                        "latencyMs" = $4,
                        error = NULL,
                        telemetry = telemetry || $5::jsonb,
                        "completedAt" = now(),
                        "updatedAt" = now()
                    WHERE id = $1 AND "workerId" = $2
                    """,
                    job_id,
                    worker_id,
                    json.dumps(result),
                    latency_ms,
                    json.dumps(telemetry),
                )
                await self._record_job_event(connection, job_id, worker_id, "completed", {"latency_ms": latency_ms})
                await self._release_worker(connection, worker_id)
        metrics_store.record_worker_job(worker_id, "COMPLETED")
        metrics_store.record_job_progress(job_id, worker_id, 100.0)
        await self._emit_job_event("inference_job_completed", job_id, worker_id)
        metrics_store.record_orchestration_event("job_completed")

    async def fail_job(self, worker_id: str, job_id: str, claim_id: str, error: str, telemetry: dict[str, Any] | None = None, trace_id: str | None = None) -> str:
        next_status = "RETRY"
        async with postgres_pool.acquire() as connection:
            async with connection.transaction():
                job = await connection.fetchrow("SELECT attempts, status::text AS status, \"workerId\" AS worker_id, telemetry FROM inference_jobs WHERE id = $1 FOR UPDATE", job_id)
                if job is None:
                    raise RuntimeError(f"Inference job {job_id} was not found")
                if job["worker_id"] != worker_id:
                    raise RuntimeError(f"Inference job {job_id} is not claimed by worker {worker_id}")
                if claim_id != _json_dict(job["telemetry"]).get("claim_id"):
                    raise RuntimeError("Inference job claim token mismatch")
                if job["status"] in {"FAILED", "DEAD_LETTER", "CANCELLED"}:
                    return job["status"]
                next_status = "DEAD_LETTER" if job["attempts"] >= settings.inference_max_attempts else "RETRY"
                retry_after = None if next_status == "DEAD_LETTER" else datetime.now(timezone.utc) + timedelta(seconds=settings.inference_retry_backoff_seconds * max(1, job["attempts"]))
                await connection.execute(
                    """
                    UPDATE inference_jobs
                    SET status = $3::"InferenceJobStatus",
                        error = $4,
                        "retryAfter" = $5,
                        telemetry = telemetry || $6::jsonb,
                        "completedAt" = CASE WHEN $3 = 'DEAD_LETTER' THEN now() ELSE "completedAt" END,
                        "updatedAt" = now()
                    WHERE id = $1 AND "workerId" = $2
                    """,
                    job_id,
                    worker_id,
                    next_status,
                    error,
                    retry_after,
                    json.dumps(telemetry or {}),
                )
                await self._record_job_event(connection, job_id, worker_id, "failed", {"error": error, "next_status": next_status})
                if next_status == "DEAD_LETTER":
                    await self._move_to_dlq(job_id, error)
                await self._release_worker(connection, worker_id)
        metrics_store.record_worker_job(worker_id, next_status)
        if next_status == "RETRY":
            metrics_store.record_orchestration_retry("job_retry", str(await self._queue_name_for_job(job_id)))
        await self._emit_job_event("inference_job_failed", job_id, worker_id, {"status": next_status})
        metrics_store.record_orchestration_event("job_failed")
        return next_status

    async def progress_job(self, worker_id: str, job_id: str, claim_id: str, progress_percent: float, stage: str, telemetry: dict[str, Any] | None = None) -> None:
        async with postgres_pool.acquire() as connection:
            async with connection.transaction():
                job = await connection.fetchrow("SELECT \"workerId\" AS worker_id, telemetry FROM inference_jobs WHERE id = $1 FOR UPDATE", job_id)
                if job is None:
                    raise RuntimeError(f"Inference job {job_id} was not found")
                if job["worker_id"] != worker_id:
                    raise RuntimeError(f"Inference job {job_id} is not claimed by worker {worker_id}")
                if claim_id != _json_dict(job["telemetry"]).get("claim_id"):
                    raise RuntimeError("Inference job claim token mismatch")
                await connection.execute(
                    """
                    UPDATE inference_jobs
                    SET telemetry = telemetry || $3::jsonb,
                        "updatedAt" = now()
                    WHERE id = $1 AND "workerId" = $2
                    """,
                    job_id,
                    worker_id,
                    json.dumps({"progress_percent": progress_percent, "stage": stage, **(telemetry or {})}),
                )
        metrics_store.record_job_progress(job_id, worker_id, progress_percent)
        metrics_store.record_orchestration_event("job_progress")

    async def cancel_job(self, job_id: str, reason: str, municipality_id: str | None = None) -> dict[str, Any]:
        async with postgres_pool.acquire() as connection:
            async with connection.transaction():
                row = await connection.fetchrow(
                    """
                    UPDATE inference_jobs
                    SET status = 'CANCELLED'::"InferenceJobStatus",
                        error = $2,
                        "retryAfter" = NULL,
                        "updatedAt" = now()
                    WHERE id = $1 AND status IN ('QUEUED','RETRY','RUNNING')
                    RETURNING id, "workerId" AS worker_id, "queueName" AS queue_name, status::text AS status
                    """,
                    job_id,
                    reason,
                )
                if row is None:
                    raise RuntimeError(f"Inference job {job_id} could not be cancelled")
                if row["worker_id"]:
                    await self._release_worker(connection, row["worker_id"])
        metrics_store.record_orchestration_event("job_cancelled")
        return dict(row)

    async def mark_worker_draining(self, worker_id: str, reason: str = "drain_requested") -> dict[str, Any]:
        async with postgres_pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                UPDATE inference_workers
                SET state = 'DRAINING'::"InferenceWorkerState",
                    "failureReason" = $2,
                    "updatedAt" = now()
                WHERE "workerId" = $1
                RETURNING *
                """,
                worker_id,
                reason,
            )
            if row is None:
                raise WorkerAuthenticationError(f"Worker {worker_id} is not registered")
        metrics_store.record_orchestration_event("worker_draining")
        metrics_store.record_worker_registration_count("DRAINING", 1)
        return dict(row)

    async def deregister_worker(self, worker_id: str, reason: str = "deregister_requested") -> dict[str, Any]:
        async with postgres_pool.acquire() as connection:
            async with connection.transaction():
                row = await connection.fetchrow(
                    """
                    UPDATE inference_workers
                    SET state = 'OFFLINE'::"InferenceWorkerState",
                        "failureReason" = $2,
                        "expiresAt" = now(),
                        "updatedAt" = now()
                    WHERE "workerId" = $1
                    RETURNING *
                    """,
                    worker_id,
                    reason,
                )
                if row is None:
                    raise WorkerAuthenticationError(f"Worker {worker_id} is not registered")
                await self.recover_worker_jobs(connection, worker_id, reason="worker_deregistered")
        metrics_store.record_orchestration_event("worker_deregistered")
        metrics_store.record_worker_registration_count("OFFLINE", 1)
        return dict(row)

    async def replay_dead_letter(self, limit: int = 50, job_id: str | None = None) -> list[dict[str, Any]]:
        async with postgres_pool.acquire() as connection:
            rows = await connection.fetch(
                f"""
                SELECT id, "queueName" AS queue_name, error
                FROM inference_jobs
                WHERE status = 'DEAD_LETTER' {('AND id = $1' if job_id else '')}
                ORDER BY "updatedAt" DESC
                LIMIT {limit if not job_id else 1}
                """,
                *( [job_id] if job_id else [] ),
            )
            for row in rows:
                await connection.execute(
                    """
                    UPDATE inference_jobs
                    SET status = 'RETRY'::"InferenceJobStatus",
                        "retryAfter" = now(),
                        error = NULL,
                        "updatedAt" = now()
                    WHERE id = $1
                    """,
                    row["id"],
                )
                metrics_store.record_dlq_replay(row["queue_name"])
        metrics_store.record_orchestration_event("dead_letter_replayed")
        return [dict(row) for row in rows]

    async def startup_recovery(self) -> dict[str, int]:
        await redis_coordinator.ensure_consumer_group(settings.inference_stream, settings.inference_consumer_group)
        expired_workers = await self.expire_workers()
        timed_out_jobs = await self.recover_timeouts()
        orphaned_jobs = await self.recover_orphaned_jobs()
        republished_jobs = await self.republish_active_jobs()
        pending_messages = await redis_coordinator.recover_pending_messages(settings.inference_stream, settings.inference_consumer_group)
        metrics_store.record_recovery_action("startup", "ok")
        return {
            "expired_workers": expired_workers,
            "timed_out_jobs": timed_out_jobs,
            "orphaned_jobs": orphaned_jobs,
            "republished_jobs": republished_jobs,
            "pending_messages_reclaimed": pending_messages,
        }

    async def expire_workers(self) -> int:
        async with postgres_pool.acquire() as connection:
            rows = await connection.fetch(
                """
                UPDATE inference_workers
                SET state = 'EXPIRED'::"InferenceWorkerState",
                    "failureReason" = 'heartbeat_expired',
                    "updatedAt" = now()
                WHERE state IN ('ONLINE','DRAINING') AND "expiresAt" <= now()
                RETURNING "workerId"
                """
            )
            for row in rows:
                await self.recover_worker_jobs(connection, row["workerId"], reason="worker_heartbeat_expired")
                metrics_store.record_orchestration_event("worker_expired")
                metrics_store.record_recovery_action("worker_expired", "ok")
        return len(rows)

    async def recover_timeouts(self) -> int:
        async with postgres_pool.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT id, "workerId" AS worker_id, attempts
                FROM inference_jobs
                WHERE status = 'RUNNING' AND "deadlineAt" <= now()
                """
            )
            for row in rows:
                worker_id = row["worker_id"]
                next_status = "DEAD_LETTER" if row["attempts"] >= settings.inference_max_attempts else "RETRY"
                retry_after = None if next_status == "DEAD_LETTER" else datetime.now(timezone.utc) + timedelta(seconds=settings.inference_retry_backoff_seconds)
                await connection.execute(
                    """
                    UPDATE inference_jobs
                    SET status = $2::"InferenceJobStatus",
                        error = 'inference_job_timeout',
                        "workerId" = NULL,
                        "retryAfter" = $3,
                        telemetry = telemetry || $4::jsonb,
                        "updatedAt" = now()
                    WHERE id = $1
                    """,
                    row["id"],
                    next_status,
                    retry_after,
                    json.dumps({"timeout": True, "timed_out_worker_id": worker_id}),
                )
                await self._record_job_event(connection, row["id"], worker_id, "timeout_recovered", {"next_status": next_status})
                if worker_id:
                    await self._release_worker(connection, worker_id)
                if next_status == "DEAD_LETTER":
                    await self._move_to_dlq(row["id"], "inference_job_timeout")
                metrics_store.record_orchestration_event("job_timeout")
                metrics_store.record_recovery_action("job_timeout", "ok")
        return len(rows)

    async def recover_orphaned_jobs(self) -> int:
        async with postgres_pool.acquire() as connection:
            async with connection.transaction():
                rows = await connection.fetch(
                    """
                    UPDATE inference_jobs
                    SET status = 'RETRY'::"InferenceJobStatus",
                        error = 'orphaned_running_job_recovered',
                        "workerId" = NULL,
                        "retryAfter" = now(),
                        telemetry = telemetry || $1::jsonb,
                        "updatedAt" = now()
                    WHERE status = 'RUNNING'
                      AND (
                        "workerId" IS NULL OR NOT EXISTS (
                          SELECT 1 FROM inference_workers iw
                          WHERE iw."workerId" = inference_jobs."workerId"
                            AND iw.state = 'ONLINE'
                            AND iw."expiresAt" > now()
                        )
                      )
                    RETURNING id, "workerId" AS worker_id
                    """,
                    json.dumps({"recovered_at": datetime.now(timezone.utc).isoformat(), "reason": "orphaned_running_job"}),
                )
                for row in rows:
                    await self._record_job_event(connection, row["id"], row["worker_id"], "orphan_recovered", {"next_status": "RETRY"})
                    metrics_store.record_recovery_action("orphan_job", "ok")
        return len(rows)

    async def republish_active_jobs(self, limit: int = 1000) -> int:
        async with postgres_pool.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT ij.id, ij."municipalityId" AS municipality_id, ij."modelId" AS model_id,
                       amr."modelType"::text AS model_type, ij."sourceUri" AS source_uri,
                       ij."queueName" AS queue_name, ij.priority, ij.attempts, ij."deadlineAt" AS deadline_at
                FROM inference_jobs ij
                JOIN ai_model_registry amr ON amr.id = ij."modelId"
                WHERE ij.status IN ('QUEUED','RETRY')
                  AND (ij."retryAfter" IS NULL OR ij."retryAfter" <= now())
                ORDER BY ij.priority DESC, ij."scheduledAt" ASC
                LIMIT $1
                """,
                limit,
            )
        for row in rows:
            await self.publish_job(dict(row))
            metrics_store.record_recovery_action("job_republish", "ok")
        return len(rows)

    async def recover_worker_jobs(self, connection: Connection, worker_id: str, reason: str) -> int:
        rows = await connection.fetch(
            """
            SELECT id, attempts FROM inference_jobs
            WHERE "workerId" = $1 AND status = 'RUNNING'
            FOR UPDATE
            """,
            worker_id,
        )
        for row in rows:
            next_status = "DEAD_LETTER" if row["attempts"] >= settings.inference_max_attempts else "RETRY"
            await connection.execute(
                """
                UPDATE inference_jobs
                SET status = $3::"InferenceJobStatus",
                    error = $4,
                    "workerId" = NULL,
                    "retryAfter" = CASE WHEN $3 = 'RETRY' THEN now() + $5::interval ELSE NULL END,
                    "updatedAt" = now()
                WHERE id = $1
                """,
                row["id"],
                worker_id,
                next_status,
                reason,
                timedelta(seconds=settings.inference_retry_backoff_seconds),
            )
            await self._record_job_event(connection, row["id"], worker_id, "recovered", {"reason": reason, "next_status": next_status})
            metrics_store.record_orchestration_event("job_recovered")
        return len(rows)

    async def _queue_name_for_job(self, job_id: str) -> str:
        async with postgres_pool.acquire() as connection:
            row = await connection.fetchrow("SELECT \"queueName\" AS queue_name FROM inference_jobs WHERE id = $1", job_id)
            return str(row["queue_name"] if row else "unknown")

    async def topology(self) -> dict[str, Any]:
        async with postgres_pool.acquire() as connection:
            worker_rows = await connection.fetch(WORKER_SELECT + ' ORDER BY "lastHeartbeatAt" DESC NULLS LAST')
            queue_rows = await connection.fetch(
                """
                SELECT "queueName" AS queue_name, status::text AS status, count(*)::int AS count
                FROM inference_jobs
                GROUP BY "queueName", status
                ORDER BY "queueName", status
                """
            )
            stale = await connection.fetchval(
                "SELECT count(*)::int FROM inference_workers WHERE state IN ('ONLINE','DRAINING') AND \"expiresAt\" <= now()"
            )
        workers = [dict(row) for row in worker_rows]
        for worker in workers:
            last = worker.get("last_heartbeat_at")
            age = (datetime.now(timezone.utc) - last).total_seconds() if last else -1
            metrics_store.record_worker_heartbeat(worker["worker_id"], worker["state"], age)
            metrics_store.record_dependency("worker", worker["state"] == "ONLINE")
        return {
            "workers": workers,
            "queues": [dict(row) for row in queue_rows],
            "stale_workers": stale or 0,
            "local_device": asdict(get_device_info()),
        }

    async def _move_to_dlq(self, job_id: str, error: str) -> None:
        try:
            async with redis_coordinator.client() as client:
                await client.xadd(settings.inference_dlq_stream, {"job_id": job_id, "error": error}, maxlen=50000, approximate=True)
        except Exception:
            return

    async def _release_worker(self, connection: Connection, worker_id: str) -> None:
        await connection.execute(
            """
            UPDATE inference_workers
            SET "activeJobCount" = GREATEST("activeJobCount" - 1, 0), "updatedAt" = now()
            WHERE "workerId" = $1
            """,
            worker_id,
        )
        metrics_store.record_orchestration_event("worker_released")

    async def _record_job_event(self, connection: Connection, job_id: str, worker_id: str | None, event: str, payload: dict[str, Any]) -> None:
        await connection.execute(
            """
            INSERT INTO inference_job_events (id, "jobId", "workerId", event, payload)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            """,
            str(uuid4()),
            job_id,
            worker_id,
            event,
            json.dumps(payload),
        )

    async def _emit_worker_event(self, event_type: str, worker_id: str) -> None:
        await operation_bus.broadcast({"type": event_type, "worker_id": worker_id, "channel": "ai-runtime"})
        metrics_store.record_orchestration_event(event_type)

    async def _emit_job_event(self, event_type: str, job_id: str, worker_id: str | None, extra: dict[str, Any] | None = None) -> None:
        await operation_bus.broadcast({"type": event_type, "job_id": job_id, "worker_id": worker_id, "channel": "ai-runtime", **(extra or {})})
        metrics_store.record_orchestration_event(event_type)


distributed_orchestrator = DistributedInferenceOrchestrator()
