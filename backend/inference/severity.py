from __future__ import annotations

import cv2
import numpy as np

from backend.models.schemas import Severity


def edge_sharpness(frame: np.ndarray, xyxy: tuple[int, int, int, int]) -> float:
    x1, y1, x2, y2 = xyxy
    crop = frame[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]
    if crop.size == 0:
        return 0.0
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def estimate_severity(area_ratio: float, confidence: float, sharpness: float) -> Severity:
    score = (area_ratio * 18.0) + (confidence * 0.55) + min(sharpness / 900.0, 0.35)
    if score >= 0.92 or area_ratio >= 0.08:
        return Severity.severe
    if score >= 0.58 or area_ratio >= 0.025:
        return Severity.medium
    return Severity.small

