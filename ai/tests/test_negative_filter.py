from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from ai.datasets.negative_filter import score_negative_image


def test_negative_filter_accepts_asphalt_like_lower_frame(tmp_path: Path) -> None:
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    image[:220, :] = (120, 170, 210)
    image[220:, :] = (92, 92, 92)
    cv2.line(image, (260, 479), (330, 220), (230, 230, 230), 8)
    path = tmp_path / "wet_lane_shadow_road.jpg"
    cv2.imwrite(str(path), image)

    score = score_negative_image(path)

    assert score.accepted is True
    assert "wet" in score.hard_negative_tags
    assert "lane" in score.hard_negative_tags


def test_negative_filter_rejects_tiny_image(tmp_path: Path) -> None:
    image = np.zeros((80, 100, 3), dtype=np.uint8)
    path = tmp_path / "tiny.jpg"
    cv2.imwrite(str(path), image)

    score = score_negative_image(path)

    assert score.accepted is False
    assert score.reason == "resolution_below_threshold"
