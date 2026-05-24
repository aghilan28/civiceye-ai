from __future__ import annotations

import argparse
from pathlib import Path

from ai.trainers.yolov8_pothole_trainer import YOLOv8PotholeTrainer
from ai.training.config import TrainingConfig


def train(config_path: Path) -> dict[str, object]:
    config = TrainingConfig.from_yaml(config_path)
    return YOLOv8PotholeTrainer(config).train()


def main() -> None:
    parser = argparse.ArgumentParser(description="Train CivicEye YOLOv8 infrastructure detectors.")
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    summary = train(args.config)
    print(summary["metrics"])


if __name__ == "__main__":
    main()
