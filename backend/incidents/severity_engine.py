from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class SeverityEvidence:
    bbox_area_ratio: float
    image_scale: float
    edge_variance: float
    frame_persistence: int
    confidence_values: list[float]


def classify_incident_severity(evidence: SeverityEvidence) -> str:
    confidence = mean(evidence.confidence_values) if evidence.confidence_values else 0.0
    persistence_score = min(evidence.frame_persistence / 8.0, 1.0)
    edge_score = min(evidence.edge_variance / 1200.0, 1.0)
    area_score = min(evidence.bbox_area_ratio / 0.11, 1.0)
    scale_score = min(max(evidence.image_scale, 0.0), 1.0)
    score = (area_score * 0.34) + (confidence * 0.24) + (edge_score * 0.16) + (persistence_score * 0.18) + (scale_score * 0.08)

    if score >= 0.82 or evidence.bbox_area_ratio >= 0.105 or (confidence >= 0.9 and evidence.frame_persistence >= 6):
        return "CRITICAL"
    if score >= 0.62 or evidence.bbox_area_ratio >= 0.06 or evidence.frame_persistence >= 4:
        return "HIGH"
    if score >= 0.38 or evidence.bbox_area_ratio >= 0.025:
        return "MEDIUM"
    return "LOW"


def repair_priority_for_severity(severity: str) -> int:
    return {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 45, "LOW": 20}.get(severity, 20)


def sla_hours_for_severity(severity: str) -> int:
    return {"CRITICAL": 4, "HIGH": 24, "MEDIUM": 72, "LOW": 168}.get(severity, 168)
