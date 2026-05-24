from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from uuid import uuid4

from backend.ai_platform.catalog import MODEL_CATALOG, model_spec
from backend.config import settings
from backend.gpu.device import get_device_info
from backend.models.enterprise import AIModelType, DeploymentTarget, InferenceJobCreate, InferenceJobResponse, ModelRegistryCreate, ModelRegistryResponse


@dataclass
class RuntimeBenchmark:
    model_type: str
    version: str
    p50_ms: float
    p95_ms: float
    throughput_fps: float
    recall: float
    precision: float
    source: str
    measured_at: str


@dataclass
class RuntimeModelVersion:
    id: str
    municipality_id: str | None
    model_type: str
    version: str
    artifact_uri: str
    metrics: dict[str, Any]
    training_metadata: dict[str, Any]
    supported_classes: list[str]
    deployment_target: str
    latency_p50_ms: int
    latency_p95_ms: int
    gpu_required: bool
    edge_compatible: bool
    active: bool
    promoted_at: datetime | None = None
    rollback_version: str | None = None
    benchmark_profile: dict[str, Any] = field(default_factory=dict)
    deployment_metadata: dict[str, Any] = field(default_factory=dict)
    checksum: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_payload(cls, payload: ModelRegistryCreate) -> "RuntimeModelVersion":
        return cls(
            id=str(uuid4()),
            municipality_id=payload.municipality_id,
            model_type=payload.model_type,
            version=payload.version,
            artifact_uri=payload.artifact_uri,
            metrics=dict(payload.metrics),
            training_metadata=dict(payload.training_metadata),
            supported_classes=list(payload.supported_classes),
            deployment_target=payload.deployment_target,
            latency_p50_ms=payload.latency_p50_ms,
            latency_p95_ms=payload.latency_p95_ms,
            gpu_required=payload.gpu_required,
            edge_compatible=payload.edge_compatible,
            active=payload.active,
            promoted_at=datetime.now(timezone.utc) if payload.active else None,
            rollback_version=payload.rollback_version,
            benchmark_profile=dict(payload.benchmark_profile),
            deployment_metadata=dict(payload.deployment_metadata),
            checksum=payload.deployment_metadata.get("checksum") or payload.metrics.get("checksum"),
        )

    def to_response(self) -> ModelRegistryResponse:
        return ModelRegistryResponse(
            id=self.id,
            municipality_id=self.municipality_id,
            model_type=self.model_type,  # type: ignore[arg-type]
            version=self.version,
            artifact_uri=self.artifact_uri,
            metrics=self.metrics,
            training_metadata=self.training_metadata,
            supported_classes=self.supported_classes,
            deployment_target=self.deployment_target,  # type: ignore[arg-type]
            latency_p50_ms=self.latency_p50_ms,
            latency_p95_ms=self.latency_p95_ms,
            gpu_required=self.gpu_required,
            edge_compatible=self.edge_compatible,
            active=self.active,
            promoted_at=self.promoted_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def validate_checksum(self) -> bool:
        if not self.checksum:
            return not settings.model_checksum_required
        payload = asdict(self)
        payload.pop("checksum", None)
        candidate = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        return candidate.startswith(self.checksum[:12]) or candidate == self.checksum


class ModelRegistryService:
    def __init__(self) -> None:
        self._models: dict[str, list[RuntimeModelVersion]] = {}
        self._benchmarks: list[RuntimeBenchmark] = []
        self._events: list[dict[str, Any]] = []
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        for model_type, spec in MODEL_CATALOG.items():
            payload = ModelRegistryCreate(
                municipality_id=None,
                model_type=model_type,  # type: ignore[arg-type]
                version=f"{settings.model_version}-{model_type.lower()}",
                artifact_uri=str(settings.resolved_weights_path),
                metrics={"seeded": True, "class": spec.canonical_class},
                training_metadata={
                    "dataset_version": "civiceye-bootstrap",
                    "trained_at": datetime.now(timezone.utc).isoformat(),
                    "source": "runtime-seed",
                },
                supported_classes=[spec.canonical_class],
                deployment_target="CLOUD_GPU",  # type: ignore[arg-type]
                latency_p50_ms=42,
                latency_p95_ms=78,
                gpu_required=spec.gpu_required,
                edge_compatible=spec.edge_compatible,
                active=(model_type == "POTHOLE"),
                rollback_version=None,
                benchmark_profile={"p50_ms": 42, "p95_ms": 78, "fps": 19.0},
                deployment_metadata={"source": "seed"},
            )
            self.register(payload, bootstrap=True)
        self._persist_registry()

    def list_models(self, municipality_id: str | None = None) -> list[ModelRegistryResponse]:
        models = [model for collection in self._models.values() for model in collection]
        if municipality_id is not None:
            models = [model for model in models if model.municipality_id in {None, municipality_id}]
        return [model.to_response() for model in sorted(models, key=lambda item: (item.model_type, item.version), reverse=True)]

    def get_active(self, model_type: str, municipality_id: str | None = None) -> RuntimeModelVersion | None:
        candidates = [
            model
            for model in self._models.get(model_type, [])
            if model.active and (model.municipality_id in {None, municipality_id})
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: item.updated_at)[-1]

    def register(self, payload: ModelRegistryCreate, *, bootstrap: bool = False) -> ModelRegistryResponse:
        spec = model_spec(payload.model_type)
        if payload.supported_classes and spec.canonical_class not in payload.supported_classes:
            payload.supported_classes.append(spec.canonical_class)
        model = RuntimeModelVersion.from_payload(payload)
        collection = self._models.setdefault(payload.model_type, [])
        if payload.active:
            for existing in collection:
                if existing.municipality_id == payload.municipality_id:
                    existing.active = False
                    existing.updated_at = datetime.now(timezone.utc)
        collection.append(model)
        self._persist_registry()
        self._benchmarks.append(
            RuntimeBenchmark(
                model_type=payload.model_type,
                version=payload.version,
                p50_ms=payload.latency_p50_ms,
                p95_ms=payload.latency_p95_ms,
                throughput_fps=max(1.0, round(1000 / max(payload.latency_p50_ms, 1), 3)),
                recall=float(payload.metrics.get("recall", 0.0)),
                precision=float(payload.metrics.get("precision", 0.0)),
                source="bootstrap" if bootstrap else "runtime",
                measured_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        self._events.append(
            {
                "action": "register",
                "model_type": payload.model_type,
                "version": payload.version,
                "municipality_id": payload.municipality_id,
                "active": payload.active,
                "bootstrap": bootstrap,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        return model.to_response()

    def promote(self, model_type: str, version: str, municipality_id: str | None = None) -> ModelRegistryResponse:
        candidates = self._models.get(model_type, [])
        promoted = None
        for model in candidates:
            if model.version == version and model.municipality_id in {None, municipality_id}:
                promoted = model
            elif model.municipality_id in {None, municipality_id}:
                model.active = False
                model.updated_at = datetime.now(timezone.utc)
        if promoted is None:
            raise KeyError(f"Model {model_type}:{version} not found")
        promoted.active = True
        promoted.promoted_at = datetime.now(timezone.utc)
        promoted.updated_at = promoted.promoted_at
        self._events.append(
            {
                "action": "promote",
                "model_type": model_type,
                "version": version,
                "municipality_id": municipality_id,
                "timestamp": promoted.promoted_at.isoformat(),
            }
        )
        self._persist_registry()
        return promoted.to_response()

    def rollback(self, model_type: str, municipality_id: str | None = None) -> ModelRegistryResponse:
        active = self.get_active(model_type, municipality_id)
        if active is None or active.rollback_version is None:
            raise KeyError(f"No rollback version available for {model_type}")
        result = self.promote(model_type, active.rollback_version, municipality_id)
        self._events.append(
            {
                "action": "rollback",
                "model_type": model_type,
                "version": active.rollback_version,
                "municipality_id": municipality_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._persist_registry()
        return result

    def benchmark_report(self, model_type: str | None = None) -> list[dict[str, Any]]:
        rows = self._benchmarks if model_type is None else [item for item in self._benchmarks if item.model_type == model_type]
        return [row.__dict__ for row in rows]

    def telemetry(self) -> dict[str, Any]:
        device = get_device_info()
        return {
            "device": device.__dict__,
            "registered_models": sum(len(models) for models in self._models.values()),
            "active_models": [model.to_response().model_dump(mode="json") for model in self._active_models()],
            "events": list(self._events[-50:]),
            "benchmarks": self.benchmark_report(),
            "checksums_valid": all(model.validate_checksum() for models in self._models.values() for model in models),
            "registry_path": str(settings.model_registry_path),
        }

    def _active_models(self) -> list[RuntimeModelVersion]:
        return [model for models in self._models.values() for model in models if model.active]

    def history(self) -> list[dict[str, Any]]:
        return list(self._events)

    def resolve_for_request(self, payload: InferenceJobCreate) -> RuntimeModelVersion:
        active = self.get_active(payload.model_type, payload.municipality_id)
        if active is not None:
            return active
        candidates = [
            model
            for model in self._models.get(payload.model_type, [])
            if model.municipality_id in {None, payload.municipality_id}
        ]
        if not candidates:
            raise ValueError(f"No active model available for {payload.model_type}")
        return sorted(candidates, key=lambda item: item.updated_at)[-1]

    def model_distribution(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for model in self._active_models():
            counts[model.model_type] = counts.get(model.model_type, 0) + 1
        return counts

    def _persist_registry(self) -> None:
        settings.model_registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "models": [model.to_response().model_dump(mode="json") for models in self._models.values() for model in models],
            "events": self._events[-200:],
        }
        settings.model_registry_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


model_registry_service = ModelRegistryService()
