from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter
from typing import Any

from ultralytics import YOLO

from ai.evaluation.hard_negative import HardNegativeFinding, categorize_hard_negative, write_hard_negative_report
from ai.evaluation.metrics import latency_summary, parse_ultralytics_metrics
from ai.training.config import EvaluationConfig
from ai.training.gpu import resolve_device
from ai.utils.io import write_json


def evaluate_model(
    weights: Path,
    data_yaml: Path,
    output_dir: Path,
    confidence: float = 0.25,
    iou: float = 0.5,
    device: str = "auto",
) -> dict[str, Any]:
    if not weights.exists():
        raise FileNotFoundError(f"Weights not found: {weights}")
    if not data_yaml.exists():
        raise FileNotFoundError(f"YOLO data yaml not found: {data_yaml}")

    profile = resolve_device(
        config=type("DeviceConfigShim", (), {
            "device": device,
            "mixed_precision": True,
            "allow_cpu_fallback": True,
            "min_free_vram_gb": 1.0,
            "batch_scale_safety": 0.8,
        })(),
        requested_batch_size=1,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(weights))
    started = perf_counter()
    validation = model.val(
        data=str(data_yaml),
        conf=confidence,
        iou=iou,
        device=profile.selected,
        plots=True,
        save_json=True,
        project=str(output_dir),
        name="validation",
        exist_ok=True,
    )
    validation_seconds = perf_counter() - started
    raw_metrics = getattr(validation, "results_dict", {}) or {}
    metrics = parse_ultralytics_metrics(raw_metrics).to_dict()
    report = {
        "weights": str(weights),
        "data_yaml": str(data_yaml),
        "device": profile.to_dict(),
        "thresholds": {"confidence": confidence, "iou": iou},
        "validation_seconds": round(validation_seconds, 3),
        "metrics": metrics,
        "raw_metrics": raw_metrics,
    }
    write_json(output_dir / "evaluation_report.json", report)
    return report


def extract_hard_negatives(
    weights: Path,
    images_dir: Path,
    output_dir: Path,
    confidence: float = 0.25,
    device: str = "auto",
    categories: tuple[str, ...] = EvaluationConfig().hard_negative_categories,
) -> Path:
    if not images_dir.exists():
        raise FileNotFoundError(f"Hard-negative image directory not found: {images_dir}")
    model = YOLO(str(weights))
    findings: list[HardNegativeFinding] = []
    results = model.predict(source=str(images_dir), conf=confidence, device=device, stream=True, verbose=False)
    for result in results:
        image_path = str(result.path)
        for box in result.boxes:
            cls_id = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
            cls_name = model.names.get(cls_id, str(cls_id))
            conf = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
            xyxy = tuple(float(v) for v in box.xyxy[0].tolist())
            findings.append(
                HardNegativeFinding(
                    image_path=image_path,
                    confidence=conf,
                    predicted_class=cls_name,
                    suspected_category=categorize_hard_negative(image_path, categories),
                    bbox_xyxy=xyxy,
                )
            )
    return write_hard_negative_report(findings, output_dir / "hard_negative_report.json")


def benchmark_inference(weights: Path, source: Path, output_dir: Path, device: str = "auto", iterations: int = 25) -> dict[str, Any]:
    model = YOLO(str(weights))
    latencies: list[float] = []
    for _ in range(iterations):
        started = perf_counter()
        list(model.predict(source=str(source), device=device, verbose=False, stream=True))
        latencies.append((perf_counter() - started) * 1000)
    report = {"weights": str(weights), "source": str(source), "device": device, "iterations": iterations, "latency": latency_summary(latencies)}
    write_json(output_dir / "inference_benchmark.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained CivicEye YOLOv8 detector.")
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("reports/evaluation"), type=Path)
    parser.add_argument("--confidence", default=0.25, type=float)
    parser.add_argument("--iou", default=0.5, type=float)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    print(evaluate_model(args.weights, args.data, args.output_dir, args.confidence, args.iou, args.device))


if __name__ == "__main__":
    main()
