from __future__ import annotations

from ai.evaluation.hard_negative import categorize_hard_negative


def test_hard_negative_category_from_filename() -> None:
    assert categorize_hard_negative("samples/night_shadow_001.jpg") == "shadow"
    assert categorize_hard_negative("samples/unknown_surface.jpg") == "unknown"
