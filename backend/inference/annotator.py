from __future__ import annotations

import cv2
import numpy as np

from backend.models.schemas import Detection, Severity


COLORS: dict[Severity, tuple[int, int, int]] = {
    Severity.small: (54, 211, 153),
    Severity.medium: (36, 191, 251),
    Severity.severe: (113, 113, 251),
}


def annotate_frame(frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
    output = frame.copy()
    for detection in detections:
        x1 = int(detection.bbox.x1)
        y1 = int(detection.bbox.y1)
        x2 = int(detection.bbox.x2)
        y2 = int(detection.bbox.y2)
        color = COLORS[detection.severity]
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 3)
        label = f"{detection.severity.value.upper()} {detection.confidence:.0%}"
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.58, 2)
        cv2.rectangle(output, (x1, max(0, y1 - text_h - 12)), (x1 + text_w + 12, y1), color, -1)
        cv2.putText(output, label, (x1 + 6, max(16, y1 - 7)), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (5, 8, 22), 2, cv2.LINE_AA)
    return output

