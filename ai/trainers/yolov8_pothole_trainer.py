from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from ultralytics import YOLO

from ai.training.checkpoints import CheckpointManager
from ai.training.config import TrainingConfig
from ai.training.gpu import TimedStage, resolve_device
from ai.training.telemetry import TrainingTelemetry
from ai.training.tracking import ExperimentTracker
from ai.utils.io import write_json


class YOLOv8PotholeTrainer:
    def __init__(self, config: TrainingConfig) -> None:
        self.config = config
        self.device_profile = resolve_device(config.device, config.batch_size)
        self.run_dir = config.run_dir
        self.telemetry = TrainingTelemetry(Path("telemetry") / "training" / config.run_name)
        self.checkpoints = CheckpointManager(config.checkpoint_dir)

    def train(self) -> dict[str, Any]:
        self._validate_inputs()
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.telemetry.log_event("run_started", {"run_name": self.config.run_name})
        self.telemetry.log_event("device_profile", self.device_profile.to_dict())
        self.telemetry.log_gpu_snapshot("before_train", self.device_profile.selected)

        with ExperimentTracker(self.config.tracking, self.config.experiment_name, self.config.run_name) as tracker:
            tracker.log_params(self.config.to_flat_params())
            tracker.log_params({"selected_device": self.device_profile.selected, "effective_batch_size": self.device_profile.batch_size})
            model = YOLO(str(self.config.resume_checkpoint or self.config.pretrained_weights or self.config.model))
            try:
                with TimedStage() as stage:
                    results = model.train(**self._ultralytics_train_kwargs())
            except BaseException as error:
                self.checkpoints.interrupted_marker(self.run_dir, error)
                self.telemetry.log_event("run_failed", {"error": repr(error)})
                raise

            metrics = getattr(results, "results_dict", {}) or {}
            checkpoint_record = self.checkpoints.capture_from_ultralytics_run(self.run_dir, metrics)
            summary = {
                "config": asdict(self.config),
                "device_profile": self.device_profile.to_dict(),
                "training_seconds": round(stage.elapsed_seconds, 3),
                "metrics": metrics,
                "checkpoints": {
                    "best": str(checkpoint_record.best) if checkpoint_record.best else None,
                    "last": str(checkpoint_record.last) if checkpoint_record.last else None,
                    "export_ready": str(checkpoint_record.export_ready) if checkpoint_record.export_ready else None,
                    "selection_metric": checkpoint_record.metric_name,
                    "selection_metric_value": checkpoint_record.metric_value,
                },
            }
            self.telemetry.log_gpu_snapshot("after_train", self.device_profile.selected)
            tracker.log_metrics(metrics)
            tracker.log_artifact(self.telemetry.write_summary(summary), "telemetry")
            tracker.log_artifact(self.config.checkpoint_dir, "checkpoints")
            write_json(self.run_dir / "phase_b_training_summary.json", summary)
            return summary

    def _ultralytics_train_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "data": str(self.config.yolo_data_yaml),
            "epochs": self.config.epochs,
            "imgsz": self.config.image_size,
            "batch": self.device_profile.batch_size,
            "workers": self.config.workers,
            "device": self.device_profile.selected,
            "amp": self.device_profile.mixed_precision_enabled,
            "optimizer": self.config.optimizer,
            "patience": self.config.patience,
            "seed": self.config.seed,
            "project": str(self.config.project),
            "name": self.config.run_name,
            "exist_ok": True,
            "cos_lr": self.config.scheduler == "cosine",
            "plots": True,
            "save": True,
            "save_period": 1,
            "val": True,
            "resume": bool(self.config.resume_checkpoint),
        }
        if self.config.learning_rate is not None:
            kwargs["lr0"] = self.config.learning_rate
        if self.config.weight_decay is not None:
            kwargs["weight_decay"] = self.config.weight_decay
        return kwargs

    def _validate_inputs(self) -> None:
        if not self.config.yolo_data_yaml.exists():
            raise FileNotFoundError(
                f"YOLO data yaml not found: {self.config.yolo_data_yaml}. "
                "Run ai/scripts/export_yolo.py before training."
            )
        if self.config.resume_checkpoint and not self.config.resume_checkpoint.exists():
            raise FileNotFoundError(f"Resume checkpoint not found: {self.config.resume_checkpoint}")
