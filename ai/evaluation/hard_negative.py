from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai.utils.io import write_json


DEFAULT_HARD_NEGATIVE_CATEGORIES = (
    "puddle",
    "road_patch",
    "shadow",
    "oil_stain",
    "road_marking",
    "crack",
    "debris",
)


@dataclass(frozen=True)
class HardNegativeFinding:
    image_path: str
    confidence: float
    predicted_class: str
    suspected_category: str
    bbox_xyxy: tuple[float, float, float, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_path": self.image_path,
            "confidence": self.confidence,
            "predicted_class": self.predicted_class,
            "suspected_category": self.suspected_category,
            "bbox_xyxy": list(self.bbox_xyxy),
        }


def categorize_hard_negative(image_path: str, configured_categories: tuple[str, ...] = DEFAULT_HARD_NEGATIVE_CATEGORIES) -> str:
    lowered = image_path.lower().replace("-", "_")
    for category in configured_categories:
        if category in lowered:
            return category
    return "unknown"


def write_hard_negative_report(findings: list[HardNegativeFinding], output_path: Path) -> Path:
    category_counts = Counter(f.suspected_category for f in findings)
    confidence_bands = {
        "0.25_0.50": sum(1 for f in findings if 0.25 <= f.confidence < 0.5),
        "0.50_0.75": sum(1 for f in findings if 0.5 <= f.confidence < 0.75),
        "0.75_1.00": sum(1 for f in findings if f.confidence >= 0.75),
    }
    write_json(
        output_path,
        {
            "total_findings": len(findings),
            "category_counts": dict(category_counts),
            "confidence_bands": confidence_bands,
            "findings": [finding.to_dict() for finding in findings],
            "retraining_priority": [
                category for category, _ in category_counts.most_common()
            ],
        },
    )
    return output_path
