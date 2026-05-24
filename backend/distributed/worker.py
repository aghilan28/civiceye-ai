from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import cv2

from backend.config import settings
from backend.database.postgres import postgres_pool
from backend.distributed.auth import sign_worker_payload, signed_payload_body
from backend.distributed.orchestration import distributed_orchestrator
from backend.gpu.device import get_device_info
from backend.inference.engine import inference_engine
from backend.inference.model_loader import model_loader
from backend.runtime.diagnostics import source_uri_to_path
from backend.services.analytics import summarize_detections


class WorkerRuntimeError(RuntimeError):
    pass


class DistributedInferenceWorker:
    def __init__(self, worker_id: str, queue_names: list[str], api_base_url: str | None = None) -> None:
        self.worker_id = worker_id
        self.queue_names = queue_names
        self.api_base_url = api_base_url.rstrip("/") if api_base_url else ""
        self.active_jobs = 0
        self.max_concurrent_jobs = int(os.getenv("CIVICEYE_WORKER_CONCURRENCY", "1"))
        self.heartbeat_interval = int(os.getenv("CIVICEYE_WORKER_HEARTBEAT_INTERVAL_SECONDS", "15"))
        self.heartbeat_jitter = int(os.getenv("CIVICEYE_WORKER_HEARTBEAT_JITTER_SECONDS", str(settings.worker_heartbeat_jitter_seconds)))
        self.worker_runtime_version = os.getenv("CIVICEYE_WORKER_RUNTIME_VERSION", settings.worker_runtime_version)
        self.drain_requested = False

    async def run_forever(self) -> None:
        if not self.api_base_url:
            await postgres_pool.connect()
        if not model_loader.model and model_loader.weights_path.exists():
            model_loader.load()
        await self.register()
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        try:
            while True:
                if self.drain_requested and self.active_jobs == 0:
                    await self.deregister(reason="drain_complete")
                    return
                if not self.api_base_url:
                    await distributed_orchestrator.recover_timeouts()
                claimed = await self.claim_job()
                if claimed is None:
                    await asyncio.sleep(2)
                    continue
                await self.execute_job(claimed)
        finally:
            heartbeat_task.cancel()
            if not self.api_base_url:
                await postgres_pool.close()

    async def register(self) -> None:
        payload = self._registration_payload()
        if self.api_base_url:
            timestamp, signature = sign_worker_payload(settings.worker_shared_secret, payload)
            request_payload = {**payload, "timestamp": timestamp, "signature": signature}
            self._post_json("/api/v1/distributed/workers/register", request_payload)
            return
        timestamp, signature = sign_worker_payload(settings.worker_shared_secret, payload)
        await distributed_orchestrator.register_worker(
            worker_id=self.worker_id,
            payload=payload,
            timestamp=timestamp,
            signature=signature,
            remote_address="local-worker-process",
        )

    async def claim_job(self) -> dict[str, Any] | None:
        if self.api_base_url:
            signed = self._signed_payload({"worker_id": self.worker_id, "queue_names": self.queue_names})
            response = self._post_json(f"/api/v1/distributed/workers/{self.worker_id}/claim", signed)
            return response.get("job")
        return await distributed_orchestrator.claim_job(self.worker_id, self.queue_names)

    async def drain(self, reason: str = "drain_requested") -> None:
        self.drain_requested = True
        if self.api_base_url:
            self._post_json(f"/api/v1/distributed/workers/{self.worker_id}/drain", self._signed_payload({"worker_id": self.worker_id, "reason": reason}))
            return
        await distributed_orchestrator.mark_worker_draining(self.worker_id, reason=reason)

    async def deregister(self, reason: str = "deregister_requested") -> None:
        if self.api_base_url:
            self._post_json(
                f"/api/v1/distributed/workers/{self.worker_id}/deregister",
                self._signed_payload({"worker_id": self.worker_id, "reason": reason}),
            )
            return
        await distributed_orchestrator.deregister_worker(self.worker_id, reason=reason)

    async def execute_job(self, job: dict[str, Any]) -> None:
        self.active_jobs += 1
        started = perf_counter()
        try:
            source_path = source_uri_to_path(job["source_uri"])
            if source_path is None or not source_path.exists():
                raise WorkerRuntimeError(
                    "Inference job source is not accessible from this worker. "
                    "Use shared object storage, file:// paths mounted into the worker, or civiceye:// runtime storage URIs."
                )
            await self.report_progress(job, 10.0, "source_ready")
            result = self._infer_media(source_path, job)
            await self.report_progress(job, 90.0, "inference_complete")
            latency_ms = int((perf_counter() - started) * 1000)
            telemetry = {"worker": self._telemetry_payload(), "completed_at": datetime.now(timezone.utc).isoformat()}
            if self.api_base_url:
                self._post_json(
                    f"/api/v1/distributed/workers/{self.worker_id}/jobs/{job['id']}/complete",
                    self._signed_payload(
                        {
                            "worker_id": self.worker_id,
                            "claim_id": job["claim_id"],
                            "trace_id": job.get("trace_id"),
                            "result": result,
                            "latency_ms": latency_ms,
                            "telemetry": telemetry,
                        }
                    ),
                )
            else:
                await distributed_orchestrator.complete_job(self.worker_id, job["id"], job["claim_id"], result, latency_ms, telemetry, trace_id=job.get("trace_id"))
        except Exception as exc:
            telemetry = {"worker": self._telemetry_payload(), "failed_at": datetime.now(timezone.utc).isoformat()}
            if self.api_base_url:
                self._post_json(
                    f"/api/v1/distributed/workers/{self.worker_id}/jobs/{job['id']}/fail",
                    self._signed_payload(
                        {
                            "worker_id": self.worker_id,
                            "claim_id": job["claim_id"],
                            "trace_id": job.get("trace_id"),
                            "error": str(exc),
                            "telemetry": telemetry,
                        }
                    ),
                )
            else:
                await distributed_orchestrator.fail_job(self.worker_id, job["id"], job["claim_id"], str(exc), telemetry, trace_id=job.get("trace_id"))
        finally:
            self.active_jobs = max(0, self.active_jobs - 1)

    async def report_progress(self, job: dict[str, Any], progress_percent: float, stage: str) -> None:
        payload = {
            "worker_id": self.worker_id,
            "claim_id": job["claim_id"],
            "trace_id": job.get("trace_id"),
            "progress_percent": progress_percent,
            "stage": stage,
            "telemetry": {"worker": self._telemetry_payload()},
        }
        try:
            if self.api_base_url:
                self._post_json(
                    f"/api/v1/distributed/workers/{self.worker_id}/jobs/{job['id']}/progress",
                    self._signed_payload(payload),
                )
                return
            await distributed_orchestrator.progress_job(
                self.worker_id,
                job["id"],
                job["claim_id"],
                progress_percent,
                stage,
                payload["telemetry"],
            )
        except Exception:
            return

    async def _heartbeat_loop(self) -> None:
        while True:
            try:
                payload = {
                    "worker_id": self.worker_id,
                    "active_job_count": self.active_jobs,
                    "gpu": self._gpu_payload(),
                    "capabilities": self._registration_payload()["capabilities"],
                    "queue_names": self.queue_names,
                    "supported_models": [settings.model_version],
                    "supported_classes": ["pothole"],
                    "telemetry": self._telemetry_payload(),
                    "runtime_version": self.worker_runtime_version,
                }
                timestamp, signature = sign_worker_payload(settings.worker_shared_secret, payload)
                payload = {**payload, "timestamp": timestamp, "signature": signature}
                if self.api_base_url:
                    self._post_json(f"/api/v1/distributed/workers/{self.worker_id}/heartbeat", payload)
                else:
                    await distributed_orchestrator.heartbeat(self.worker_id, payload)
            except Exception:
                pass
            await asyncio.sleep(self._heartbeat_delay())

    def _registration_payload(self) -> dict[str, Any]:
        device = get_device_info()
        return {
            "worker_id": self.worker_id,
            "queue_names": self.queue_names,
            "capabilities": {
                "cuda_available": device.cuda_available,
                "device": device.device,
                "half_precision": device.half_precision,
                "runtime": "torch-ultralytics-yolov8",
                "runtime_version": self.worker_runtime_version,
            },
            "supported_models": [settings.model_version],
            "supported_classes": ["pothole"],
            "gpu": self._gpu_payload(),
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "runtime_version": self.worker_runtime_version,
            "telemetry": self._telemetry_payload(),
        }

    def _gpu_payload(self) -> dict[str, Any]:
        device = get_device_info()
        return {
            "count": 1 if device.cuda_available else 0,
            "name": device.gpu_name,
            "vram_total_mb": int(device.vram_total_mb) if device.vram_total_mb is not None else None,
            "vram_used_mb": int(device.vram_used_mb) if device.vram_used_mb is not None else None,
        }

    def _telemetry_payload(self) -> dict[str, Any]:
        return {
            "model": model_loader.metadata(),
            "queues": self.queue_names,
            "heartbeat_at": datetime.now(timezone.utc).isoformat(),
            "runtime_version": self.worker_runtime_version,
        }

    def _heartbeat_delay(self) -> float:
        jitter = max(0, self.heartbeat_jitter)
        if jitter == 0:
            return float(self.heartbeat_interval)
        return float(self.heartbeat_interval + (hash(self.worker_id) % jitter) / 10)

    def _signed_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        signed = signed_payload_body(payload)
        timestamp, signature = sign_worker_payload(settings.worker_shared_secret, signed)
        return {**signed, "timestamp": timestamp, "signature": signature}

    def _infer_media(self, source_path: Path, job: dict[str, Any]) -> dict[str, Any]:
        suffix = source_path.suffix.lower()
        source_id = f"distributed:{job['id']}"
        session_id = job["id"]
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            response, _ = inference_engine.predict_image(source_path.read_bytes(), source_id=source_id, session_id=session_id)
            return {
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "worker_id": self.worker_id,
                "queue_names": self.queue_names,
                "source_uri": job["source_uri"],
                "execution_mode": "image_yolo",
                "analytics": {
                    "image_width": response.image_width,
                    "image_height": response.image_height,
                    "detection_count": response.pothole_count,
                    "confidence_mean": response.confidence_mean,
                    "severity_summary": response.severity_summary,
                    "telemetry": response.telemetry.model_dump(mode="json"),
                },
                "detections": [detection.model_dump(mode="json") for detection in response.detections],
            }
        if suffix in {".mp4", ".mov", ".m4v", ".avi"}:
            return self._infer_video(source_path, source_id=source_id, session_id=session_id, source_uri=job["source_uri"])
        raise WorkerRuntimeError(f"Unsupported inference source type: {source_path.suffix}")

    def _infer_video(self, source_path: Path, source_id: str, session_id: str, source_uri: str) -> dict[str, Any]:
        capture = cv2.VideoCapture(str(source_path))
        if not capture.isOpened():
            raise WorkerRuntimeError(f"OpenCV could not open video {source_path}")
        started = perf_counter()
        detections = []
        processed_frames = 0
        frame_index = 0
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                should_infer = settings.frame_skip == 0 or frame_index % (settings.frame_skip + 1) == 0
                if should_infer:
                    frame_detections, _ = inference_engine.predict_frame(
                        frame,
                        source_id=source_id,
                        session_id=session_id,
                        frame_index=frame_index,
                    )
                    detections.extend(frame_detections)
                    processed_frames += 1
                frame_index += 1
        finally:
            capture.release()
        duration = max(0.001, perf_counter() - started)
        analytics = summarize_detections(detections, processed_frames, duration)
        return {
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "worker_id": self.worker_id,
            "queue_names": self.queue_names,
            "source_uri": source_uri,
            "execution_mode": "video_yolo",
            "frames_seen": frame_index,
            "frames_inferred": processed_frames,
            "analytics": analytics,
            "detections": [detection.model_dump(mode="json") for detection in detections],
        }

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload, default=str).encode("utf-8")
        request = Request(
            f"{self.api_base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise WorkerRuntimeError(f"Worker API request failed {exc.code}: {detail}") from exc
        except URLError as exc:
            raise WorkerRuntimeError(f"Worker API request failed: {exc}") from exc


async def main() -> None:
    queues = [item.strip() for item in os.getenv("CIVICEYE_QUEUE_NAMES", os.getenv("CIVICEYE_QUEUE_NAME", "gpu.high")).split(",") if item.strip()]
    worker = DistributedInferenceWorker(
        worker_id=os.getenv("CIVICEYE_WORKER_ID", f"gpu-worker-{os.getpid()}"),
        queue_names=queues,
        api_base_url=os.getenv("CIVICEYE_BACKEND_URL", ""),
    )
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
