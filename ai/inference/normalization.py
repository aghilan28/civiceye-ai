from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.inference.severity import estimate_pothole_severity
from ai.utils.schema import BoundingBox


@dataclass(frozen=True)
class NormalizedDetection:
    issue_type: str
    confidence: float
    severity: str
    bounding_box: BoundingBox
    recommended_department: str


def severity_from_confidence(confidence: float, area_ratio: float) -> str:
    return estimate_pothole_severity(area_ratio, 1.0, confidence)


def normalize_yolov8_prediction(prediction: dict[str, Any]) -> NormalizedDetection:
    box = BoundingBox(
        x_center=float(prediction["x_center"]),
        y_center=float(prediction["y_center"]),
        width=float(prediction["width"]),
        height=float(prediction["height"]),
        annotation_confidence=float(prediction.get("confidence", 1.0)),
    )
    confidence = float(prediction["confidence"])
    severity = severity_from_confidence(confidence, box.width * box.height)
    return NormalizedDetection(
        issue_type="pothole",
        confidence=confidence,
        severity=severity,
        bounding_box=box,
        recommended_department="roads",
    )
