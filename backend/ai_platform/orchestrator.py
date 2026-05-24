from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from backend.ai_platform.catalog import MODEL_CATALOG, model_spec
from backend.ai_platform.registry import model_registry_service
from backend.distributed.orchestration import distributed_orchestrator
from backend.models.enterprise import InferenceJobCreate, InferenceJobResponse
from backend.telemetry.metrics import metrics_store


@dataclass(frozen=True)
class InferenceRoute:
    model_type: str
    model_id: str
    queue_name: str
    worker_pool: str
    gpu_required: bool
    priority: int
    reason: str


class AIOrchestrator:
    def __init__(self) -> None:
        self._telemetry: list[dict[str, Any]] = []

    def route(self, payload: InferenceJobCreate) -> InferenceRoute:
        model = model_registry_service.resolve_for_request(payload)
        spec = model_spec(payload.model_type)
        priority_class = "emergency" if payload.priority >= 90 else "high" if payload.priority >= 70 else "standard"
        if payload.queue_name:
            queue_name = payload.queue_name
        elif model.gpu_required:
            queue_name = f"gpu.{priority_class}"
        else:
            queue_name = f"cpu.{priority_class}"
        return InferenceRoute(
            model_type=payload.model_type,
            model_id=model.id,
            queue_name=queue_name,
            worker_pool="gpu-inference-workers" if model.gpu_required else "cpu-inference-workers",
            gpu_required=model.gpu_required,
            priority=payload.priority,
            reason=f"{spec.canonical_class} routed using active registry model {model.version}",
        )

    async def enqueue(self, payload: InferenceJobCreate, *, persisted_job: InferenceJobResponse | None = None) -> InferenceJobResponse:
        route = self.route(payload)
        now = datetime.now(timezone.utc)
        job = persisted_job or InferenceJobResponse(
            id=str(uuid4()),
            municipality_id=payload.municipality_id,
            incident_id=payload.incident_id,
            model_id=route.model_id,
            model_type=payload.model_type,
            source_uri=payload.source_uri,
            status="QUEUED",
            queue_name=route.queue_name,
            batch_key=payload.batch_key,
            priority=payload.priority,
            attempts=0,
            latency_ms=None,
            result={},
            error=None,
            scheduled_at=now,
            started_at=None,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )
        await self._push_redis(job)
        self._telemetry.append(
            {
                "event": "job_enqueued",
                "job_id": job.id,
                "route": route.__dict__,
                "timestamp": now.isoformat(),
            }
        )
        return job

    async def orchestrate_batch(self, payloads: list[InferenceJobCreate]) -> dict[str, Any]:
        batch_key = payloads[0].batch_key or f"batch-{uuid4()}" if payloads else f"batch-{uuid4()}"
        started = perf_counter()
        jobs = await asyncio.gather(
            *[
                self.enqueue(
                    InferenceJobCreate(
                        **{
                            **payload.model_dump(),
                            "batch_key": batch_key,
                        }
                    )
                )
                for payload in payloads
            ]
        )
        consensus = self.consensus_score([job.model_type for job in jobs], [job.priority / 100 for job in jobs])
        latency_ms = round((perf_counter() - started) * 1000, 3)
        metrics_store.record_queue("batch_enqueued", len(jobs), queue_name=batch_key)
        return {
            "batch_key": batch_key,
            "job_ids": [job.id for job in jobs],
            "consensus_score": consensus,
            "latency_ms": latency_ms,
            "model_types": [job.model_type for job in jobs],
        }

    def consensus_score(self, model_types: list[str], confidences: list[float]) -> float:
        if not model_types:
            return 0.0
        weights = [MODEL_CATALOG.get(model_type, MODEL_CATALOG["POTHOLE"]).severity_weight for model_type in model_types]
        weighted = sum(conf * weight for conf, weight in zip(confidences, weights))
        return round(min(1.0, weighted / max(sum(weights), 0.0001)), 5)

    async def _push_redis(self, job: InferenceJobResponse) -> None:
        await distributed_orchestrator.publish_job(job.model_dump(mode="python"))

    def queue_snapshot(self) -> dict[str, Any]:
        return {"source": "postgres_redis_streams", "memory_jobs": 0}

    def telemetry(self) -> dict[str, Any]:
        return {
            "queue": self.queue_snapshot(),
            "model_registry": model_registry_service.telemetry(),
            "recent_events": self._telemetry[-100:],
        }


ai_orchestrator = AIOrchestrator()
