from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from types import TracebackType
from typing import Any

from ai.training.config import TrackingConfig


class ExperimentTracker(AbstractContextManager["ExperimentTracker"]):
    def __init__(self, config: TrackingConfig, experiment_name: str, run_name: str) -> None:
        self.config = config
        self.experiment_name = experiment_name
        self.run_name = run_name
        self.mlflow = None
        self.wandb_run = None
        self.run_id: str | None = None

    def __enter__(self) -> "ExperimentTracker":
        if self.config.mlflow_enabled:
            import mlflow

            self.mlflow = mlflow
            mlflow.set_tracking_uri(self.config.mlflow_tracking_uri)
            mlflow.set_experiment(self.experiment_name)
            active_run = mlflow.start_run(run_name=self.run_name, tags=self.config.tags)
            self.run_id = active_run.info.run_id
        if self.config.wandb_enabled:
            import wandb

            self.wandb_run = wandb.init(
                project=self.config.wandb_project,
                name=self.run_name,
                tags=list(self.config.tags.values()),
                reinit=True,
            )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.mlflow:
            if exc_value:
                self.mlflow.set_tag("status", "failed")
                self.mlflow.log_param("failure_type", exc_type.__name__ if exc_type else "unknown")
            self.mlflow.end_run()
        if self.wandb_run:
            self.wandb_run.finish(exit_code=1 if exc_value else 0)

    def log_params(self, params: dict[str, Any]) -> None:
        safe_params = {key: _stringify(value) for key, value in params.items()}
        if self.mlflow:
            self.mlflow.log_params(safe_params)
        if self.wandb_run:
            self.wandb_run.config.update(safe_params, allow_val_change=True)

    def log_metrics(self, metrics: dict[str, Any], step: int | None = None) -> None:
        numeric = {key: float(value) for key, value in metrics.items() if isinstance(value, int | float)}
        if self.mlflow:
            for key, value in numeric.items():
                self.mlflow.log_metric(key, value, step=step)
        if self.wandb_run:
            self.wandb_run.log(numeric, step=step)

    def log_artifact(self, path: Path, artifact_path: str | None = None) -> None:
        if not path.exists():
            return
        if self.mlflow:
            if path.is_dir():
                self.mlflow.log_artifacts(str(path), artifact_path=artifact_path)
            else:
                self.mlflow.log_artifact(str(path), artifact_path=artifact_path)
        if self.wandb_run and path.is_file():
            import wandb

            self.wandb_run.log({path.name: wandb.Artifact(path.stem, type="artifact")})


def _stringify(value: Any) -> str | int | float | bool:
    if isinstance(value, str | int | float | bool):
        return value
    return str(value)
