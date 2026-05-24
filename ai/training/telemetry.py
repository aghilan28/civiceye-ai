from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai.training.gpu import snapshot_gpu_memory
from ai.utils.io import write_json


@dataclass
class TrainingTelemetry:
    output_dir: Path
    events: list[dict[str, Any]] = field(default_factory=list)

    def log_event(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {"event_type": event_type, **payload}
        self.events.append(event)
        write_json(self.output_dir / "telemetry_events.json", {"events": self.events})

    def log_gpu_snapshot(self, stage: str, device: str) -> None:
        self.log_event("gpu_memory", {"stage": stage, **snapshot_gpu_memory(device)})

    def write_summary(self, payload: dict[str, Any]) -> Path:
        path = self.output_dir / "training_summary.json"
        write_json(path, payload)
        return path
