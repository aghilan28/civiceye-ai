from __future__ import annotations

import json
from pathlib import Path

from backend.config import ROOT_DIR, settings
from backend.gpu.device import get_device_info
from backend.models.schemas import (
    DeploymentTarget,
    DetectionType,
    GpuRequirements,
    LatencyBenchmark,
    ModelFramework,
    ModelLoadPlan,
    ModelLoadRequest,
    ModelMetrics,
    ModelRegistryEntry,
    ModelRegistryResponse,
    PrecisionMode,
    TrainingMetadata,
)


class ModelRegistry:
    def __init__(self, registry_path: Path | None = None) -> None:
        self.registry_path = registry_path or ROOT_DIR / "ai" / "models" / "registry.json"

    def list_models(self) -> list[ModelRegistryEntry]:
        configured = self._read_registry_file()
        models = [ModelRegistryEntry(**item) for item in configured]
        if not models:
            models.append(self._default_pothole_model())
        return models

    def response(self) -> ModelRegistryResponse:
        models = self.list_models()
        supported = sorted({issue for model in models for issue in model.supported_classes}, key=lambda item: item.value)
        return ModelRegistryResponse(
            models=models,
            active_model_ids=[f"{model.model_id}:{model.version}" for model in models if model.active],
            supported_detection_types=supported,
        )

    def resolve(self, model_id: str, version: str | None = None) -> ModelRegistryEntry:
        candidates = [model for model in self.list_models() if model.model_id == model_id]
        if version:
            candidates = [model for model in candidates if model.version == version]
        if not candidates:
            raise KeyError(f"Model {model_id}:{version or 'active'} is not registered")
        active = [model for model in candidates if model.active]
        return active[0] if active else sorted(candidates, key=lambda model: model.version)[-1]

    def loading_plan(self, request: ModelLoadRequest) -> ModelLoadPlan:
        model = self.resolve(request.model_id, request.version)
        device = get_device_info()
        selected_device = device.device if device.cuda_available and model.gpu_requirements.cuda_required else "cpu"
        precision = PrecisionMode.fp16 if device.cuda_available else PrecisionMode.fp32
        if DeploymentTarget.jetson_nano in model.deployment_targets:
            precision = PrecisionMode.int8
        available_vram = int(device.vram_total_mb or model.gpu_requirements.min_vram_mb)
        concurrency_limit = max(1, min(8, available_vram // max(1, model.gpu_requirements.min_vram_mb)))
        return ModelLoadPlan(
            model_id=model.model_id,
            version=model.version,
            selected_device=selected_device,
            precision=precision,
            lazy_load=not request.warm,
            gpu_memory_budget_mb=min(available_vram, model.gpu_requirements.preferred_vram_mb),
            concurrency_limit=concurrency_limit,
            reason="Selected from registry using CUDA availability, model VRAM requirement, and edge precision policy.",
        )

    def _read_registry_file(self) -> list[dict]:
        if not self.registry_path.exists():
            return []
        with self.registry_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload.get("models", [])

    def _default_pothole_model(self) -> ModelRegistryEntry:
        return ModelRegistryEntry(
            model_id="pothole-yolov8",
            version=settings.model_version,
            framework=ModelFramework.ultralytics_yolov8,
            artifact_uri=str(settings.resolved_weights_path),
            metrics=ModelMetrics(),
            training_metadata=TrainingMetadata(
                dataset_version="pothole-real-v0.2.0",
                trained_at="2026-05-16T00:00:00Z",
                experiment_id="local-yolov8-pothole-training",
            ),
            supported_classes=[DetectionType.pothole],
            deployment_targets=[
                DeploymentTarget.cloud_gpu,
                DeploymentTarget.cloud_cpu,
                DeploymentTarget.jetson_xavier,
                DeploymentTarget.dashcam,
                DeploymentTarget.vehicle_mount,
            ],
            gpu_requirements=GpuRequirements(min_vram_mb=2048, preferred_vram_mb=6144, cuda_required=False),
            edge_compatible=True,
            latency_benchmarks=[
                LatencyBenchmark(
                    target=DeploymentTarget.cloud_gpu,
                    precision=PrecisionMode.fp16,
                    batch_size=1,
                    p50_ms=0,
                    p95_ms=0,
                    fps=0,
                )
            ],
            active=True,
            rollback_version="pothole-yolov8-v0.1.0",
        )


model_registry = ModelRegistry()
