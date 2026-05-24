from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ai.utils.io import read_yaml


SUPPORTED_MODELS = {"yolov8n.pt", "yolov8s.pt", "yolov8m.pt"}
SeverityLabel = Literal["minor", "moderate", "severe", "critical"]


@dataclass(frozen=True)
class TrackingConfig:
    mlflow_enabled: bool = True
    mlflow_tracking_uri: str = "file:./experiments/mlruns"
    wandb_enabled: bool = False
    wandb_project: str = "civiceye-pothole-detection"
    tags: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationConfig:
    confidence_thresholds: tuple[float, ...] = (0.25, 0.5, 0.75)
    iou_threshold: float = 0.5
    save_predictions: bool = True
    save_confusion_matrix: bool = True
    save_pr_curve: bool = True
    hard_negative_categories: tuple[str, ...] = (
        "puddle",
        "road_patch",
        "shadow",
        "oil_stain",
        "road_marking",
        "crack",
        "debris",
    )


@dataclass(frozen=True)
class ExportConfig:
    formats: tuple[str, ...] = ("onnx", "torchscript")
    dynamic: bool = True
    simplify: bool = True
    opset: int = 12
    half: bool = False
    int8: bool = False
    include_tensorrt_ready_metadata: bool = True


@dataclass(frozen=True)
class DeviceConfig:
    device: str = "auto"
    mixed_precision: bool = True
    allow_cpu_fallback: bool = True
    min_free_vram_gb: float = 2.0
    batch_scale_safety: float = 0.8


@dataclass(frozen=True)
class TrainingConfig:
    experiment_name: str
    run_name: str
    dataset_version: str
    yolo_data_yaml: Path
    model: str = "yolov8n.pt"
    pretrained_weights: Path | None = None
    resume_checkpoint: Path | None = None
    epochs: int = 80
    image_size: int = 960
    batch_size: int = 16
    workers: int = 8
    optimizer: str = "auto"
    scheduler: str = "cosine"
    learning_rate: float | None = None
    weight_decay: float | None = None
    patience: int = 18
    seed: int = 42
    project: Path = Path("experiments/pothole_detection")
    augmentation_profile: str = "pothole_field_conditions"
    classes: tuple[str, ...] = ("pothole",)
    severity_labels: tuple[SeverityLabel, ...] = ("minor", "moderate", "severe", "critical")
    device: DeviceConfig = field(default_factory=DeviceConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    export: ExportConfig = field(default_factory=ExportConfig)

    @property
    def run_dir(self) -> Path:
        return self.project / self.run_name

    @property
    def checkpoint_dir(self) -> Path:
        return Path("checkpoints") / self.experiment_name / self.run_name

    @classmethod
    def from_yaml(cls, path: Path) -> "TrainingConfig":
        if not path.exists() and not path.is_absolute():
            ai_root_path = Path(__file__).resolve().parents[1] / path
            if ai_root_path.exists():
                path = ai_root_path
        payload = read_yaml(path)
        if not isinstance(payload, dict):
            raise ValueError(f"Training config {path} must contain a mapping")
        return cls.from_dict(payload, base_dir=path.parent)

    @classmethod
    def from_dict(cls, payload: dict[str, Any], base_dir: Path | None = None) -> "TrainingConfig":
        required = ["experiment_name", "run_name", "dataset_version", "yolo_data_yaml"]
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(f"Training config missing required keys: {', '.join(missing)}")

        model = str(payload.get("model", "yolov8n.pt"))
        pretrained_weights = _optional_path(payload.get("pretrained_weights"))
        resume_checkpoint = _optional_path(payload.get("resume_checkpoint"))
        if pretrained_weights:
            model = str(pretrained_weights)
        elif model not in SUPPORTED_MODELS and not Path(model).exists():
            raise ValueError(
                f"Unsupported model '{model}'. Use one of {sorted(SUPPORTED_MODELS)} or a weight path."
            )

        tracking_payload = payload.get("tracking", payload.get("mlflow", {})) or {}
        tracking = TrackingConfig(
            mlflow_enabled=bool(tracking_payload.get("mlflow_enabled", tracking_payload.get("enabled", True))),
            mlflow_tracking_uri=str(tracking_payload.get("mlflow_tracking_uri", tracking_payload.get("tracking_uri", "file:./experiments/mlruns"))),
            wandb_enabled=bool(tracking_payload.get("wandb_enabled", False)),
            wandb_project=str(tracking_payload.get("wandb_project", "civiceye-pothole-detection")),
            tags=dict(tracking_payload.get("tags", {})),
        )
        device_payload = payload.get("device_config", {})
        configured_device = str(payload.get("device", device_payload.get("device", "auto")))
        device = DeviceConfig(
            device=configured_device,
            mixed_precision=bool(payload.get("mixed_precision", device_payload.get("mixed_precision", True))),
            allow_cpu_fallback=bool(device_payload.get("allow_cpu_fallback", True)),
            min_free_vram_gb=float(device_payload.get("min_free_vram_gb", 2.0)),
            batch_scale_safety=float(device_payload.get("batch_scale_safety", 0.8)),
        )
        evaluation_payload = payload.get("evaluation", {}) or {}
        evaluation = EvaluationConfig(
            confidence_thresholds=tuple(float(v) for v in evaluation_payload.get("confidence_thresholds", [0.25, 0.5, 0.75])),
            iou_threshold=float(evaluation_payload.get("iou_threshold", 0.5)),
            save_predictions=bool(evaluation_payload.get("save_predictions", True)),
            save_confusion_matrix=bool(evaluation_payload.get("save_confusion_matrix", True)),
            save_pr_curve=bool(evaluation_payload.get("save_pr_curve", True)),
            hard_negative_categories=tuple(evaluation_payload.get("hard_negative_categories", EvaluationConfig().hard_negative_categories)),
        )
        export_payload = payload.get("export", {}) or {}
        export = ExportConfig(
            formats=tuple(export_payload.get("formats", ["onnx", "torchscript"])),
            dynamic=bool(export_payload.get("dynamic", True)),
            simplify=bool(export_payload.get("simplify", True)),
            opset=int(export_payload.get("opset", 12)),
            half=bool(export_payload.get("half", False)),
            int8=bool(export_payload.get("int8", False)),
            include_tensorrt_ready_metadata=bool(export_payload.get("include_tensorrt_ready_metadata", True)),
        )

        return cls(
            experiment_name=str(payload["experiment_name"]),
            run_name=str(payload["run_name"]),
            dataset_version=str(payload["dataset_version"]),
            yolo_data_yaml=_path(payload["yolo_data_yaml"], base_dir),
            model=model,
            pretrained_weights=pretrained_weights,
            resume_checkpoint=resume_checkpoint,
            epochs=int(payload.get("epochs", 80)),
            image_size=int(payload.get("image_size", payload.get("imgsz", 960))),
            batch_size=int(payload.get("batch_size", payload.get("batch", 16))),
            workers=int(payload.get("workers", 8)),
            optimizer=str(payload.get("optimizer", "auto")),
            scheduler=str(payload.get("scheduler", "cosine")),
            learning_rate=_optional_float(payload.get("learning_rate", payload.get("lr0"))),
            weight_decay=_optional_float(payload.get("weight_decay")),
            patience=int(payload.get("patience", 18)),
            seed=int(payload.get("seed", 42)),
            project=_path(payload.get("project", "experiments/pothole_detection"), base_dir),
            augmentation_profile=str(payload.get("augmentation_profile", "pothole_field_conditions")),
            classes=tuple(payload.get("classes", ["pothole"])),
            severity_labels=tuple(payload.get("severity_labels", ["minor", "moderate", "severe", "critical"])),
            device=device,
            tracking=tracking,
            evaluation=evaluation,
            export=export,
        )

    def to_flat_params(self) -> dict[str, str | int | float | bool]:
        return {
            "experiment_name": self.experiment_name,
            "run_name": self.run_name,
            "dataset_version": self.dataset_version,
            "model": self.model,
            "epochs": self.epochs,
            "image_size": self.image_size,
            "batch_size": self.batch_size,
            "workers": self.workers,
            "optimizer": self.optimizer,
            "scheduler": self.scheduler,
            "learning_rate": self.learning_rate or "ultralytics_default",
            "weight_decay": self.weight_decay or "ultralytics_default",
            "mixed_precision": self.device.mixed_precision,
            "augmentation_profile": self.augmentation_profile,
            "classes": ",".join(self.classes),
        }


def _optional_float(value: Any) -> float | None:
    return None if value in (None, "") else float(value)


def _optional_path(value: Any) -> Path | None:
    return None if value in (None, "") else Path(str(value))


def _path(value: Any, base_dir: Path | None) -> Path:
    path = Path(str(value))
    if path.is_absolute() or base_dir is None:
        return path
    return path
