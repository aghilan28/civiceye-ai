from __future__ import annotations

from collections import Counter

from backend.models.schemas import Detection


def summarize_detections(detections: list[Detection], processed_frames: int, duration_seconds: float) -> dict[str, object]:
    severity = Counter(detection.severity.value for detection in detections)
    confidence_mean = sum(detection.confidence for detection in detections) / len(detections) if detections else 0.0
    detections_per_minute = (len(detections) / max(duration_seconds, 1.0)) * 60.0
    return {
        "pothole_count": len(detections),
        "processed_frames": processed_frames,
        "duration_seconds": round(duration_seconds, 3),
        "severity_distribution": {
            "small": severity.get("small", 0),
            "medium": severity.get("medium", 0),
            "severe": severity.get("severe", 0),
        },
        "confidence_mean": round(confidence_mean, 6),
        "detections_per_minute": round(detections_per_minute, 3),
    }

