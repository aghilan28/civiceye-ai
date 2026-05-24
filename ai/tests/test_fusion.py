from __future__ import annotations

from ai.datasets.fusion import fuse_positive_and_negative_manifests, fusion_summary
from ai.utils.schema import BoundingBox, DatasetItem, DatasetManifest


def test_fuse_positive_and_negative_manifests_preserves_negative_labels_empty() -> None:
    positive = DatasetManifest(
        dataset_id="positive",
        version="v1",
        created_at="now",
        description="positive",
        annotation_version="v1",
        source_ids=["pos"],
        items=[
            DatasetItem(
                image_id="p1",
                image_path=__file__,
                source_id="pos",
                width=640,
                height=480,
                has_pothole=True,
                annotations=[BoundingBox(0.5, 0.5, 0.2, 0.2)],
                perceptual_hash="p1",
            )
        ],
    )
    negative = DatasetManifest(
        dataset_id="negative",
        version="v1",
        created_at="now",
        description="negative",
        annotation_version="v1",
        source_ids=["neg"],
        items=[
            DatasetItem(
                image_id="n1",
                image_path=__file__,
                source_id="neg",
                width=640,
                height=480,
                has_pothole=False,
                annotations=[BoundingBox(0.5, 0.5, 0.2, 0.2)],
                perceptual_hash="n1",
            )
        ],
    )

    fused = fuse_positive_and_negative_manifests(positive, negative, "fused", "v2")
    summary = fusion_summary(fused)

    assert summary["positive_images"] == 1
    assert summary["negative_images"] == 1
    assert all(not item.annotations for item in fused.items if not item.has_pothole)
