from __future__ import annotations

from pathlib import Path

import cv2
import imagehash
from PIL import Image


def read_image_dimensions(path: Path) -> tuple[int, int]:
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    height, width = image.shape[:2]
    return width, height


def compute_perceptual_hash(path: Path) -> str:
    with Image.open(path) as image:
        return str(imagehash.phash(image))


def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
