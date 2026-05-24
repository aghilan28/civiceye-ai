from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from time import time

from prometheus_client import Counter, Gauge, Histogram


INFERENCE_LATENCY = Histogram(
    "civiceye_inference_latency_ms",
    "AI inference latency in milliseconds",
    ["model_type", "source"],
    buckets=(10, 25, 50, 75, 100, 150, 250, 500, 1000, 2500, 5000),
)
INFERENCE_LIFECYCLE = Histogram(
    "civiceye_inference_lifecycle_seconds",
    "Distributed inference lifecycle timings",
    ["stage", "model_type", "queue_name"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 15, 30, 60, 120, 300, 600),
)
INFERENCE_DETECTIONS = Counter("civiceye_inference_detections_total", "AI detections emitted", ["model_type"])
INFERENCE_FAILURES = Counter("civiceye_inference_failures_total", "AI inference failures", ["model_type"])
QUEUE_DEPTH = Gauge("civiceye_queue_depth", "Distributed inference queue depth", ["queue_name", "status"])
QUEUE_LATENCY = Histogram(
    "civiceye_queue_latency_seconds",
    "Age of queued or retried inference jobs in seconds",
    ["queue_name", "status"],
    buckets=(1, 5, 15, 30, 60, 120, 300, 600, 1800, 3600),
)
DEAD_LETTER_COUNT = Gauge("civiceye_dead_letter_jobs", "Inference jobs currently in dead-letter state", ["queue_name"])
REPLAY_RECOVERY_COUNT = Counter("civiceye_replay_recovery_total", "Replay recovery actions", ["queue_name", "status"])
WORKER_REGISTRATIONS = Gauge("civiceye_worker_registrations", "Registered workers by lifecycle state", ["state"])
WORKER_HEARTBEATS = Gauge("civiceye_worker_heartbeat_age_seconds", "Seconds since the last worker heartbeat", ["worker_id", "state"])
WORKER_HEARTBEAT_FAILURES = Counter("civiceye_worker_heartbeat_failures_total", "Worker heartbeat failures", ["worker_id", "reason"])
WORKER_JOBS = Counter("civiceye_worker_jobs_total", "Distributed inference jobs completed by workers", ["worker_id", "status"])
WORKER_STATE = Gauge("civiceye_worker_state", "Worker state by lifecycle phase", ["worker_id", "state"])
WORKER_SATURATION = Gauge("civiceye_worker_saturation_ratio", "Worker active jobs divided by max concurrent jobs", ["worker_id", "state"])
WORKER_DRAINING = Gauge("civiceye_worker_draining", "Worker draining state", ["worker_id"])
WEBSOCKET_CLIENTS = Gauge("civiceye_websocket_clients", "Connected websocket clients", ["region"])
WEBSOCKET_EVENTS = Counter("civiceye_websocket_events_total", "Websocket events propagated", ["event_type", "region"])
WEBSOCKET_BYTES = Counter("civiceye_websocket_bytes_total", "Websocket bytes sent or received", ["direction", "region"])
GPU_UTILIZATION = Gauge("civiceye_gpu_utilization_percent", "GPU utilization percent", ["device"])
GPU_MEMORY = Gauge("civiceye_gpu_memory_mb", "GPU memory in MB", ["device", "kind"])
DB_LATENCY = Histogram("civiceye_db_latency_ms", "Database operation latency", ["operation"], buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000))
DEPENDENCY_HEALTH = Gauge("civiceye_dependency_health", "Runtime dependency health, 1 is healthy", ["dependency"])
DEPENDENCY_RECONNECTS = Counter("civiceye_dependency_reconnects_total", "Dependency reconnect attempts", ["dependency", "status"])
REDIS_STREAM_LAG = Gauge("civiceye_redis_stream_lag", "Redis stream pending message count", ["stream", "group"])
REDIS_STREAM_LENGTH = Gauge("civiceye_redis_stream_length", "Redis stream length", ["stream"])
ORCHESTRATION_EVENTS = Counter("civiceye_orchestration_events_total", "Distributed orchestration lifecycle events", ["event_type"])
ORCHESTRATION_ROUTING_LATENCY = Histogram(
    "civiceye_orchestration_routing_latency_seconds",
    "Latency spent making orchestration routing decisions",
    ["queue_name", "model_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
)
ORCHESTRATION_RETRIES = Counter("civiceye_orchestration_retries_total", "Orchestration retry attempts", ["reason", "queue_name"])
ROUTING_DECISIONS = Counter("civiceye_routing_decisions_total", "Distributed routing decisions", ["queue_name", "reason"])
JOB_PROGRESS = Gauge("civiceye_inference_job_progress_percent", "Inference job progress percentage", ["job_id", "worker_id"])
DLQ_REPLAYED = Counter("civiceye_dead_letter_replayed_total", "Dead-letter jobs replayed", ["queue_name"])
RECOVERY_ACTIONS = Counter("civiceye_recovery_actions_total", "Runtime recovery actions executed", ["action", "status"])
TENANT_USAGE = Counter("civiceye_tenant_usage_total", "Tenant metered usage", ["municipality_id", "metric", "unit"])
OPERATIONAL_VALIDATION = Gauge("civiceye_operational_validation_status", "Operational validation status by flow", ["flow_name"])


@dataclass
class MetricsStore:
    latencies_ms: deque[float] = field(default_factory=lambda: deque(maxlen=512))
    failures: int = 0
    frames_processed: int = 0
    detections: int = 0
    queues: dict[str, dict[str, int]] = field(default_factory=dict)
    dependencies: dict[str, bool] = field(default_factory=dict)
    orchestration_events: dict[str, int] = field(default_factory=dict)
    websocket_events: int = 0
    db_latency_ms: deque[float] = field(default_factory=lambda: deque(maxlen=512))
    started_at: float = field(default_factory=time)
    lock: Lock = field(default_factory=Lock)

    def record_inference(self, latency_ms: float, detections: int, frames: int = 1, model_type: str = "POTHOLE", source: str = "runtime") -> None:
        with self.lock:
            self.latencies_ms.append(latency_ms)
            self.detections += detections
            self.frames_processed += frames
        INFERENCE_LATENCY.labels(model_type=model_type, source=source).observe(latency_ms)
        INFERENCE_DETECTIONS.labels(model_type=model_type).inc(detections)

    def record_failure(self, model_type: str = "POTHOLE") -> None:
        with self.lock:
            self.failures += 1
        INFERENCE_FAILURES.labels(model_type=model_type).inc()

    def record_queue(self, status: str, depth: int, queue_name: str = "default") -> None:
        with self.lock:
            self.queues.setdefault(queue_name, {})[status] = depth
        QUEUE_DEPTH.labels(queue_name=queue_name, status=status).set(depth)
        if status == "DEAD_LETTER":
            DEAD_LETTER_COUNT.labels(queue_name=queue_name).set(depth)

    def record_queue_latency(self, queue_name: str, status: str, latency_seconds: float) -> None:
        QUEUE_LATENCY.labels(queue_name=queue_name, status=status).observe(max(0.0, latency_seconds))

    def record_worker_heartbeat(self, worker_id: str, state: str, heartbeat_age_seconds: float) -> None:
        WORKER_HEARTBEATS.labels(worker_id=worker_id, state=state).set(heartbeat_age_seconds)
        WORKER_STATE.labels(worker_id=worker_id, state=state).set(1)
        WORKER_DRAINING.labels(worker_id=worker_id).set(1 if state == "DRAINING" else 0)

    def record_worker_registration_count(self, state: str, count: int) -> None:
        WORKER_REGISTRATIONS.labels(state=state).set(count)

    def record_worker_saturation(self, worker_id: str, state: str, active_jobs: int, max_jobs: int) -> None:
        denominator = max(1, max_jobs)
        WORKER_SATURATION.labels(worker_id=worker_id, state=state).set(active_jobs / denominator)

    def record_worker_heartbeat_failure(self, worker_id: str, reason: str) -> None:
        WORKER_HEARTBEAT_FAILURES.labels(worker_id=worker_id or "unknown", reason=reason).inc()

    def record_worker_job(self, worker_id: str, status: str) -> None:
        WORKER_JOBS.labels(worker_id=worker_id, status=status).inc()

    def record_dependency(self, dependency: str, healthy: bool) -> None:
        with self.lock:
            self.dependencies[dependency] = healthy
        DEPENDENCY_HEALTH.labels(dependency=dependency).set(1 if healthy else 0)

    def record_dependency_reconnect(self, dependency: str, status: str) -> None:
        DEPENDENCY_RECONNECTS.labels(dependency=dependency, status=status).inc()

    def record_redis_stream_lag(self, stream: str, group: str, pending: int) -> None:
        REDIS_STREAM_LAG.labels(stream=stream, group=group).set(pending)

    def record_redis_stream_length(self, stream: str, length: int) -> None:
        REDIS_STREAM_LENGTH.labels(stream=stream).set(length)

    def record_orchestration_event(self, event_type: str) -> None:
        with self.lock:
            self.orchestration_events[event_type] = self.orchestration_events.get(event_type, 0) + 1
        ORCHESTRATION_EVENTS.labels(event_type=event_type).inc()

    def record_routing(self, queue_name: str, reason: str) -> None:
        ROUTING_DECISIONS.labels(queue_name=queue_name, reason=reason).inc()

    def record_routing_latency(self, queue_name: str, model_type: str, latency_seconds: float) -> None:
        ORCHESTRATION_ROUTING_LATENCY.labels(queue_name=queue_name, model_type=model_type).observe(max(0.0, latency_seconds))

    def record_orchestration_retry(self, reason: str, queue_name: str) -> None:
        ORCHESTRATION_RETRIES.labels(reason=reason, queue_name=queue_name).inc()

    def record_inference_lifecycle(self, stage: str, model_type: str, queue_name: str, seconds: float) -> None:
        INFERENCE_LIFECYCLE.labels(stage=stage, model_type=model_type, queue_name=queue_name).observe(max(0.0, seconds))

    def record_job_progress(self, job_id: str, worker_id: str, progress_percent: float) -> None:
        JOB_PROGRESS.labels(job_id=job_id, worker_id=worker_id).set(progress_percent)

    def record_dlq_replay(self, queue_name: str, count: int = 1) -> None:
        DLQ_REPLAYED.labels(queue_name=queue_name).inc(count)
        REPLAY_RECOVERY_COUNT.labels(queue_name=queue_name, status="replayed").inc(count)

    def record_recovery_action(self, action: str, status: str = "ok") -> None:
        RECOVERY_ACTIONS.labels(action=action, status=status).inc()
        self.record_orchestration_event(f"recovery_{action}_{status}")

    def record_websocket(self, event_type: str, region: str, clients: int) -> None:
        with self.lock:
            self.websocket_events += 1
        WEBSOCKET_CLIENTS.labels(region=region).set(clients)
        WEBSOCKET_EVENTS.labels(event_type=event_type, region=region).inc()

    def record_websocket_bytes(self, direction: str, region: str, byte_count: int) -> None:
        WEBSOCKET_BYTES.labels(direction=direction, region=region).inc(max(0, byte_count))

    def record_gpu(self, device: str, utilization_percent: float | None, used_mb: float | None, total_mb: float | None) -> None:
        if utilization_percent is not None:
            GPU_UTILIZATION.labels(device=device).set(utilization_percent)
        if used_mb is not None:
            GPU_MEMORY.labels(device=device, kind="used").set(used_mb)
        if total_mb is not None:
            GPU_MEMORY.labels(device=device, kind="total").set(total_mb)

    def record_db_latency(self, operation: str, latency_ms: float) -> None:
        with self.lock:
            self.db_latency_ms.append(latency_ms)
        DB_LATENCY.labels(operation=operation).observe(latency_ms)

    def record_tenant_usage(self, municipality_id: str, metric: str, quantity: float, unit: str) -> None:
        TENANT_USAGE.labels(municipality_id=municipality_id, metric=metric, unit=unit).inc(quantity)

    def record_validation(self, flow_name: str, ok: bool) -> None:
        OPERATIONAL_VALIDATION.labels(flow_name=flow_name).set(1 if ok else 0)

    def snapshot(self) -> dict[str, float | int]:
        with self.lock:
            latencies = list(self.latencies_ms)
            avg = sum(latencies) / len(latencies) if latencies else 0.0
            p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1] if len(latencies) >= 2 else avg
            uptime = max(1.0, time() - self.started_at)
            return {
                "uptime_seconds": round(uptime, 2),
                "latency_avg_ms": round(avg, 3),
                "latency_p95_ms": round(p95, 3),
                "failures": self.failures,
                "frames_processed": self.frames_processed,
                "detections": self.detections,
                "throughput_fps": round(self.frames_processed / uptime, 3),
                "websocket_events": self.websocket_events,
                "queue_depth": self.queues,
                "dependencies": dict(self.dependencies),
                "orchestration_events": dict(self.orchestration_events),
                "db_latency_avg_ms": round(sum(self.db_latency_ms) / len(self.db_latency_ms), 3) if self.db_latency_ms else 0,
            }


metrics_store = MetricsStore()
