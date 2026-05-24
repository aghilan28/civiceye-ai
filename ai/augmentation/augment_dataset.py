from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import albumentations as A
import cv2

from ai.utils.io import read_manifest, read_yaml, write_manifest
from ai.utils.schema import BoundingBox


def build_transform(config: dict[str, object]) -> A.Compose:
    transforms: list[A.BasicTransform] = []
    transform_config = config["transforms"]

    if transform_config["brightness_contrast"]["enabled"]:
        transforms.append(
            A.RandomBrightnessContrast(
                brightness_limit=transform_config["brightness_contrast"]["brightness_limit"],
                contrast_limit=transform_config["brightness_contrast"]["contrast_limit"],
                p=transform_config["brightness_contrast"]["probability"],
            )
        )

    if transform_config["gaussian_blur"]["enabled"]:
        transforms.append(A.GaussianBlur(blur_limit=transform_config["gaussian_blur"]["blur_limit"], p=transform_config["gaussian_blur"]["probability"]))

    if transform_config["motion_blur"]["enabled"]:
        transforms.append(A.MotionBlur(blur_limit=transform_config["motion_blur"]["blur_limit"], p=transform_config["motion_blur"]["probability"]))

    if transform_config["rain"]["enabled"]:
        transforms.append(
            A.RandomRain(
                drop_length=transform_config["rain"]["drop_length"],
                drop_width=transform_config["rain"]["drop_width"],
                blur_value=transform_config["rain"]["blur_value"],
                p=transform_config["rain"]["probability"],
            )
        )

    if transform_config["shadow"]["enabled"]:
        transforms.append(A.RandomShadow(shadow_dimension=transform_config["shadow"]["shadow_dimension"], p=transform_config["shadow"]["probability"]))

    if transform_config["jpeg_compression"]["enabled"]:
        transforms.append(
            A.ImageCompression(
                quality_lower=transform_config["jpeg_compression"]["quality_lower"],
                quality_upper=transform_config["jpeg_compression"]["quality_upper"],
                p=transform_config["jpeg_compression"]["probability"],
            )
        )

    if transform_config["perspective"]["enabled"]:
        transforms.append(A.Perspective(scale=transform_config["perspective"]["scale"], p=transform_config["perspective"]["probability"]))

    return A.Compose(
        transforms,
        bbox_params=A.BboxParams(format="yolo", label_fields=["class_labels"], min_visibility=0.55),
    )


def augment_manifest(manifest_path: Path, config_path: Path, output_root: Path, output_manifest: Path) -> None:
    manifest = read_manifest(manifest_path)
    config = read_yaml(config_path)
    transform = build_transform(config)
    augmented_items = list(manifest.items)
    copies = int(config["max_augmented_copies_per_image"])

    for item in manifest.items:
        image = cv2.imread(str(item.image_path))
        if image is None:
            continue
        bboxes = [[a.x_center, a.y_center, a.width, a.height] for a in item.annotations]
        class_labels = [a.class_id for a in item.annotations]

        for copy_index in range(copies):
            transformed = transform(image=image, bboxes=bboxes, class_labels=class_labels)
            output_path = output_root / f"{item.image_path.stem}_aug{copy_index}{item.image_path.suffix}"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), transformed["image"])
            annotations = [
                BoundingBox(
                    x_center=float(box[0]),
                    y_center=float(box[1]),
                    width=float(box[2]),
                    height=float(box[3]),
                    class_id=int(label),
                    class_name="pothole",
                    severity=item.annotations[index].severity if index < len(item.annotations) else "moderate",
                )
                for index, (box, label) in enumerate(zip(transformed["bboxes"], transformed["class_labels"], strict=False))
            ]
            augmented_items.append(
                replace(
                    item,
                    image_id=f"{item.image_id}_aug{copy_index}",
                    image_path=output_path.resolve(),
                    annotations=annotations,
                    perceptual_hash=None,
                )
            )

    write_manifest(output_manifest, replace(manifest, items=augmented_items), Path.cwd())


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply conservative field-condition augmentations.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--config", default=Path("configs/augmentation/pothole_field_conditions.yaml"), type=Path)
    parser.add_argument("--output-root", default=Path("processed/augmented"), type=Path)
    parser.add_argument("--output-manifest", default=Path("processed/augmented_manifest.json"), type=Path)
    args = parser.parse_args()
    augment_manifest(args.manifest, args.config, args.output_root, args.output_manifest)
    print(f"Augmented manifest written to {args.output_manifest}")


if __name__ == "__main__":
    main()
