from __future__ import annotations


def estimate_pothole_severity(
    normalized_width: float,
    normalized_height: float,
    confidence: float,
    context_multiplier: float = 1.0,
) -> str:
    area_ratio = max(0.0, min(1.0, normalized_width * normalized_height * context_multiplier))
    if area_ratio >= 0.12 or (confidence >= 0.92 and area_ratio >= 0.07):
        return "critical"
    if area_ratio >= 0.06 or confidence >= 0.85:
        return "severe"
    if area_ratio >= 0.025 or confidence >= 0.68:
        return "moderate"
    return "minor"
