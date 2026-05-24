from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai.utils.io import write_json


@dataclass(frozen=True)
class CheckpointRecord:
    best: Path | None
    last: Path | None
    export_ready: Path | None
    metric_name: str
    metric_value: float | None


class CheckpointManager:
    def __init__(self, checkpoint_dir: Path, metric_name: str = "metrics/mAP50-95(B)") -> None:
        self.checkpoint_dir = checkpoint_dir
        self.metric_name = metric_name
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def capture_from_ultralytics_run(self, run_dir: Path, metrics: dict[str, Any]) -> CheckpointRecord:
        weights_dir = run_dir / "weights"
        best_source = weights_dir / "best.pt"
        last_source = weights_dir / "last.pt"
        best_dest = self._copy_if_exists(best_source, "best.pt")
        last_dest = self._copy_if_exists(last_source, "last.pt")
        export_ready = best_dest or last_dest
        metric_value = _metric(metrics, self.metric_name)
        record = CheckpointRecord(best_dest, last_dest, export_ready, self.metric_name, metric_value)
        write_json(
            self.checkpoint_dir / "checkpoint_lineage.json",
            {
                "best": str(best_dest) if best_dest else None,
                "last": str(last_dest) if last_dest else None,
                "export_ready": str(export_ready) if export_ready else None,
                "selection_metric": self.metric_name,
                "selection_metric_value": metric_value,
                "source_run_dir": str(run_dir),
            },
        )
        return record

    def interrupted_marker(self, run_dir: Path, error: BaseException) -> Path:
        marker = self.checkpoint_dir / "INTERRUPTED.json"
        write_json(marker, {"source_run_dir": str(run_dir), "error": repr(error)})
        return marker

    def _copy_if_exists(self, source: Path, name: str) -> Path | None:
        if not source.exists():
            return None
        destination = self.checkpoint_dir / name
        shutil.copy2(source, destination)
        return destination


def _metric(metrics: dict[str, Any], metric_name: str) -> float | None:
    value = metrics.get(metric_name)
    if isinstance(value, int | float):
        return float(value)
    return None
