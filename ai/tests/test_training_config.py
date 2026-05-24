from __future__ import annotations

from pathlib import Path

import pytest

from ai.training.config import TrainingConfig


def test_training_config_supports_phase_b_fields() -> None:
    config = TrainingConfig.from_yaml(Path("configs/training/pothole_yolov8n.yaml"))

    assert config.model == "yolov8n.pt"
    assert config.device.device == "auto"
    assert config.device.mixed_precision is True
    assert config.evaluation.iou_threshold == 0.5
    assert config.export.formats == ("onnx", "torchscript")
    assert config.classes == ("pothole",)


def test_training_config_rejects_unknown_builtin_model() -> None:
    with pytest.raises(ValueError):
        TrainingConfig.from_dict(
            {
                "experiment_name": "bad",
                "run_name": "bad",
                "dataset_version": "v0",
                "yolo_data_yaml": "exports/yolo/pothole_v0/data.yaml",
                "model": "yolov8x.pt",
            }
        )
