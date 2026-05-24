from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


Severity = Literal["none", "minor", "moderate", "severe", "critical"]
SplitName = Literal["train", "val", "test"]


@dataclass(frozen=True)
class BoundingBox:
    x_center: float
    y_center: float
    width: float
    height: float
    class_id: int = 0
    class_name: str = "pothole"
    severity: Severity = "moderate"
    annotation_confidence: float = 1.0

    def is_valid(self) -> bool:
        values = [self.x_center, self.y_center, self.width, self.height]
        return (
            all(0.0 <= value <= 1.0 for value in values)
            and self.width > 0.0
            and self.height > 0.0
            and 0.0 <= self.annotation_confidence <= 1.0
        )

    def to_yolo_line(self) -> str:
        return (
            f"{self.class_id} {self.x_center:.6f} {self.y_center:.6f} "
            f"{self.width:.6f} {self.height:.6f}"
        )


@dataclass(frozen=True)
class ImageMetadata:
    lighting: str
    weather: str
    camera_type: str
    road_texture: str
    capture_angle: str
    city: str | None = None
    geo_hash: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class DatasetItem:
    image_id: str
    image_path: Path
    source_id: str
    width: int | None
    height: int | None
    has_pothole: bool
    annotations: list[BoundingBox] = field(default_factory=list)
    metadata: ImageMetadata | None = None
    split: SplitName | None = None
    perceptual_hash: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any], root: Path) -> "DatasetItem":
        annotations = [BoundingBox(**annotation) for annotation in payload.get("annotations", [])]
        metadata_payload = payload.get("metadata")
        metadata = ImageMetadata(**metadata_payload) if metadata_payload else None
        return cls(
            image_id=payload["image_id"],
            image_path=(root / payload["image_path"]).resolve(),
            source_id=payload["source_id"],
            width=payload.get("width"),
            height=payload.get("height"),
            has_pothole=bool(payload.get("has_pothole", False)),
            annotations=annotations,
            metadata=metadata,
            split=payload.get("split"),
            perceptual_hash=payload.get("perceptual_hash"),
        )

    def to_dict(self, root: Path) -> dict[str, Any]:
        try:
            image_path = str(self.image_path.resolve().relative_to(root.resolve())).replace("\\", "/")
        except ValueError:
            image_path = str(self.image_path).replace("\\", "/")
        return {
            "image_id": self.image_id,
            "image_path": image_path,
            "source_id": self.source_id,
            "width": self.width,
            "height": self.height,
            "has_pothole": self.has_pothole,
            "annotations": [annotation.__dict__ for annotation in self.annotations],
            "metadata": self.metadata.__dict__ if self.metadata else None,
            "split": self.split,
            "perceptual_hash": self.perceptual_hash,
        }


@dataclass(frozen=True)
class DatasetManifest:
    dataset_id: str
    version: str
    created_at: str
    description: str
    annotation_version: str
    source_ids: list[str]
    items: list[DatasetItem]

    @classmethod
    def from_dict(cls, payload: dict[str, Any], root: Path) -> "DatasetManifest":
        return cls(
            dataset_id=payload["dataset_id"],
            version=payload["version"],
            created_at=payload["created_at"],
            description=payload["description"],
            annotation_version=payload["annotation_version"],
            source_ids=list(payload.get("source_ids", [])),
            items=[DatasetItem.from_dict(item, root) for item in payload.get("items", [])],
        )

    def to_dict(self, root: Path) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "created_at": self.created_at,
            "description": self.description,
            "annotation_version": self.annotation_version,
            "source_ids": self.source_ids,
            "items": [item.to_dict(root) for item in self.items],
        }
