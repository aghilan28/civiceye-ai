from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ai.utils.images import compute_perceptual_hash, is_supported_image, read_image_dimensions
from ai.utils.schema import DatasetManifest


@dataclass
class ValidationIssue:
    severity: str
    image_id: str
    code: str
    message: str


@dataclass
class ValidationReport:
    dataset_id: str
    version: str
    total_images: int
    positive_images: int
    negative_images: int
    annotation_count: int
    issues: list[ValidationIssue] = field(default_factory=list)
    split_counts: dict[str, int] = field(default_factory=dict)
    source_counts: dict[str, int] = field(default_factory=dict)
    severity_counts: dict[str, int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "passed": self.passed,
            "total_images": self.total_images,
            "positive_images": self.positive_images,
            "negative_images": self.negative_images,
            "annotation_count": self.annotation_count,
            "split_counts": self.split_counts,
            "source_counts": self.source_counts,
            "severity_counts": self.severity_counts,
            "issues": [issue.__dict__ for issue in self.issues],
        }


def validate_manifest(manifest: DatasetManifest, min_width: int = 320, min_height: int = 240) -> ValidationReport:
    issues: list[ValidationIssue] = []
    hash_to_ids: dict[str, list[str]] = defaultdict(list)
    split_image_ids: dict[str, set[str]] = defaultdict(set)
    severity_counts: Counter[str] = Counter()

    for item in manifest.items:
        if not item.image_path.exists():
            issues.append(ValidationIssue("error", item.image_id, "IMAGE_MISSING", str(item.image_path)))
            continue

        if not is_supported_image(item.image_path):
            issues.append(ValidationIssue("error", item.image_id, "UNSUPPORTED_IMAGE", item.image_path.suffix))

        try:
            width, height = read_image_dimensions(item.image_path)
            if width < min_width or height < min_height:
                issues.append(
                    ValidationIssue(
                        "warning",
                        item.image_id,
                        "LOW_RESOLUTION",
                        f"{width}x{height} below recommended {min_width}x{min_height}",
                    )
                )
        except ValueError as error:
            issues.append(ValidationIssue("error", item.image_id, "CORRUPT_IMAGE", str(error)))

        if item.has_pothole and not item.annotations:
            issues.append(ValidationIssue("error", item.image_id, "POSITIVE_WITHOUT_LABEL", "Positive image has no bounding boxes"))

        if not item.has_pothole and item.annotations:
            issues.append(ValidationIssue("error", item.image_id, "NEGATIVE_WITH_LABEL", "Negative image contains annotations"))

        for annotation in item.annotations:
            severity_counts[annotation.severity] += 1
            if not annotation.is_valid():
                issues.append(ValidationIssue("error", item.image_id, "INVALID_BBOX", str(annotation)))

        try:
            image_hash = item.perceptual_hash or compute_perceptual_hash(item.image_path)
            hash_to_ids[image_hash].append(item.image_id)
        except Exception as error:  # noqa: BLE001 - validation should collect all dataset issues
            issues.append(ValidationIssue("warning", item.image_id, "HASH_FAILED", str(error)))

        if item.split:
            split_image_ids[item.split].add(item.image_id)

    for image_hash, image_ids in hash_to_ids.items():
        if len(image_ids) > 1:
            for image_id in image_ids:
                issues.append(ValidationIssue("warning", image_id, "POSSIBLE_DUPLICATE", image_hash))

    for split_a, ids_a in split_image_ids.items():
        for split_b, ids_b in split_image_ids.items():
            if split_a >= split_b:
                continue
            leaked = ids_a.intersection(ids_b)
            for image_id in leaked:
                issues.append(ValidationIssue("error", image_id, "SPLIT_LEAKAGE", f"{split_a}/{split_b}"))

    positive_images = sum(1 for item in manifest.items if item.has_pothole)
    negative_images = len(manifest.items) - positive_images

    if positive_images == 0:
        issues.append(ValidationIssue("error", "DATASET", "NO_POSITIVES", "Dataset has no pothole images"))

    if negative_images == 0:
        issues.append(ValidationIssue("error", "DATASET", "NO_NEGATIVES", "Dataset has no negative road images"))

    return ValidationReport(
        dataset_id=manifest.dataset_id,
        version=manifest.version,
        total_images=len(manifest.items),
        positive_images=positive_images,
        negative_images=negative_images,
        annotation_count=sum(len(item.annotations) for item in manifest.items),
        issues=issues,
        split_counts=dict(Counter(item.split or "unassigned" for item in manifest.items)),
        source_counts=dict(Counter(item.source_id for item in manifest.items)),
        severity_counts=dict(severity_counts),
    )
