from __future__ import annotations

from uuid import uuid4

from backend.models.schemas import DistributedInferencePlan, DistributedInferenceTask, QueuePriority, WorkerPoolPlan


class DistributedInferenceScheduler:
    def plan(self, task: DistributedInferenceTask) -> DistributedInferencePlan:
        queue = self._queue_name(task)
        pool = WorkerPoolPlan(
            queue=queue,
            worker_pool="gpu-inference-workers" if task.requires_gpu else "cpu-inference-workers",
            min_replicas=2 if task.priority in {QueuePriority.emergency, QueuePriority.high} else 1,
            max_replicas=24 if task.requires_gpu else 12,
            gpu_required=task.requires_gpu,
            routing_key=f"{task.tenant_id}.{task.priority.value}.{task.model_id}",
            autoscaling_signal="redis_queue_depth,gpu_utilization,p95_inference_latency",
        )
        return DistributedInferencePlan(
            task_id=task.task_id,
            queue_backend="redis",
            scheduler="celery",
            selected_queue=queue,
            worker_pool=pool,
            tenant_partition_key=f"tenant:{task.tenant_id}",
            trace_id=str(uuid4()),
        )

    def _queue_name(self, task: DistributedInferenceTask) -> str:
        if task.priority == QueuePriority.emergency:
            return "civiceye.inference.emergency"
        if task.requires_gpu:
            return "civiceye.inference.gpu"
        if len(task.detection_types) > 3:
            return "civiceye.inference.bulk"
        return "civiceye.inference.cpu"


distributed_scheduler = DistributedInferenceScheduler()
