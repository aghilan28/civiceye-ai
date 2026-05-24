from __future__ import annotations

from ai.inference.severity import estimate_pothole_severity


def test_severity_estimation_uses_scale_and_confidence() -> None:
    assert estimate_pothole_severity(0.05, 0.05, 0.4) == "minor"
    assert estimate_pothole_severity(0.2, 0.2, 0.7) == "moderate"
    assert estimate_pothole_severity(0.3, 0.3, 0.8) == "severe"
    assert estimate_pothole_severity(0.4, 0.4, 0.95) == "critical"
