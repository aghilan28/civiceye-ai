from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from ultralytics import YOLO

from ai.inference.severity import estimate_pothole_severity


@dataclass(frozen=True)
class InferenceDetection:
    issue_type: str
    confidence: float
    severity: str
    class_id: int
    class_name: str
    bbox_xyxy: tuple[float, float, float, float]
    bbox_normalized: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InferenceResult:
    request_id: str
    model_version: str
    source: str
    image_width: int
    image_height: int
    inference_ms: float
    device: str
    detections: list[InferenceDetection]
    telemetry: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["detections"] = [detection.to_dict() for detection in self.detections]
        return payload


class CivicEyeYOLOPredictor:
    def __init__(self, weights: Path, model_version: str, device: str = "auto", confidence: float = 0.25, iou: float = 0.5) -> None:
        if not weights.exists():
            raise FileNotFoundError(f"Model weights not found: {weights}")
        self.weights = weights
        self.model_version = model_version
        self.device = device
        self.confidence = confidence
        self.iou = iou
        self.model = YOLO(str(weights))

    def predict(self, source: str | Path) -> list[InferenceResult]:
        started = perf_counter()
        raw_results = list(
            self.model.predict(
                source=str(source),
                conf=self.confidence,
                iou=self.iou,
                device=self.device,
                verbose=False,
                stream=True,
            )
        )
        total_ms = (perf_counter() - started) * 1000
        per_image_ms = total_ms / max(1, len(raw_results))
        outputs: list[InferenceResult] = []
        for result in raw_results:
            height, width = result.orig_shape
            detections = [self._normalize_box(box, width, height) for box in result.boxes]
            outputs.append(
                InferenceResult(
                    request_id=str(uuid4()),
                    model_version=self.model_version,
                    source=str(result.path),
                    image_width=width,
                    image_height=height,
                    inference_ms=round(per_image_ms, 3),
                    device=self.device,
                    detections=detections,
                    telemetry={
                        "weights": str(self.weights),
                        "confidence_threshold": self.confidence,
                        "iou_threshold": self.iou,
                        "detection_count": len(detections),
                    },
                )
            )
        return outputs

    def _normalize_box(self, box: Any, width: int, height: int) -> InferenceDetection:
        cls_id = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
        class_name = self.model.names.get(cls_id, str(cls_id))
        confidence = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
        normalized_width = max(0.0, min(1.0, (x2 - x1) / width))
        normalized_height = max(0.0, min(1.0, (y2 - y1) / height))
        return InferenceDetection(
            issue_type=class_name,
            confidence=confidence,
            severity=estimate_pothole_severity(normalized_width, normalized_height, confidence),
            class_id=cls_id,
            class_name=class_name,
            bbox_xyxy=(x1, y1, x2, y2),
            bbox_normalized={
                "x_center": ((x1 + x2) / 2) / width,
                "y_center": ((y1 + y2) / 2) / height,
                "width": normalized_width,
                "height": normalized_height,
            },
        )
