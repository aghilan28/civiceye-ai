from __future__ import annotations

from pathlib import Path
from backend.database.postgres import postgres_pool
from backend.models.enterprise import InferenceJobCreate
from backend.models.schemas import JobState, VideoJobStatus, VideoResults
from backend.services.enterprise_intelligence import enterprise_intelligence_service


STATE_MAP = {
    "QUEUED": JobState.queued,
    "RETRY": JobState.queued,
    "RUNNING": JobState.running,
    "COMPLETED": JobState.completed,
    "FAILED": JobState.failed,
    "DEAD_LETTER": JobState.failed,
    "CANCELLED": JobState.cancelled,
}


class DurableVideoJobQueue:
    async def enqueue(self, input_path: Path, source_id: str, session_id: str, municipality_id: str = "MUNI-BLR"):
        source_uri = input_path.resolve().as_uri()
        payload = InferenceJobCreate(
            municipality_id=municipality_id,
            model_type="POTHOLE",
            source_uri=source_uri,
            priority=70,
            requested_models=["POTHOLE"],
            batch_key=session_id,
        )
        async with postgres_pool.acquire() as connection:
            response = await enterprise_intelligence_service.enqueue_inference(connection, payload)
        return response

    async def get(self, job_id: str) -> dict | None:
        async with postgres_pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT id, status::text AS status, result, error, "latencyMs" AS latency_ms,
                       "startedAt" AS started_at, "completedAt" AS completed_at, "sourceUri" AS source_uri
                FROM inference_jobs
                WHERE id = $1
                """,
                job_id,
            )
        return dict(row) if row else None

    def status(self, job: dict) -> VideoJobStatus:
        result = job.get("result") or {}
        analytics = result.get("analytics") if isinstance(result, dict) else {}
        frame_index = int(result.get("frames_seen") or 0) if isinstance(result, dict) else 0
        progress = 1.0 if job["status"] in {"COMPLETED", "FAILED", "DEAD_LETTER", "CANCELLED"} else 0.0
        detections = len(result.get("detections") or []) if isinstance(result, dict) else 0
        return VideoJobStatus(
            job_id=job["id"],
            state=STATE_MAP.get(job["status"], JobState.failed),
            progress=progress,
            frame_index=frame_index,
            total_frames=frame_index,
            detections=detections,
            fps=float((analytics or {}).get("fps") or 0),
            error=job.get("error"),
        )

    def results(self, job: dict) -> VideoResults:
        result = job.get("result") or {}
        analytics = result.get("analytics") if isinstance(result, dict) else {}
        return VideoResults(
            job_id=job["id"],
            state=STATE_MAP.get(job["status"], JobState.failed),
            processed_video_url=None,
            detection_log_url=None,
            analytics=analytics or {},
            detections=[],
        )


video_job_queue = DurableVideoJobQueue()
