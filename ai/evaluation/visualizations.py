from __future__ import annotations

from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


def draw_detections(
    image_path: Path,
    detections: Iterable[dict[str, object]],
    output_path: Path,
    color: tuple[int, int, int] = (0, 0, 255),
) -> Path:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Unable to read image for visualization: {image_path}")
    for detection in detections:
        x1, y1, x2, y2 = [int(v) for v in detection["bbox_xyxy"]]
        label = f"{detection.get('class_name', 'pothole')} {float(detection.get('confidence', 0.0)):.2f}"
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(image, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image)
    return output_path


def create_inspection_grid(image_paths: list[Path], output_path: Path, tile_size: int = 320) -> Path:
    tiles: list[np.ndarray] = []
    for path in image_paths:
        image = cv2.imread(str(path))
        if image is None:
            continue
        tiles.append(cv2.resize(image, (tile_size, tile_size)))
    if not tiles:
        raise ValueError("No valid images supplied for inspection grid")
    columns = min(4, len(tiles))
    rows = int(np.ceil(len(tiles) / columns))
    canvas = np.zeros((rows * tile_size, columns * tile_size, 3), dtype=np.uint8)
    for index, tile in enumerate(tiles):
        row = index // columns
        col = index % columns
        canvas[row * tile_size : (row + 1) * tile_size, col * tile_size : (col + 1) * tile_size] = tile
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), canvas)
    return output_path
