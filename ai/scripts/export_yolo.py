from __future__ import annotations

import argparse
import shutil
from collections import Counter
from pathlib import Path

from ai.utils.io import read_manifest, write_json, write_yaml


def write_label(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def export_yolo(version: str, manifest_path: Path, output_root: Path) -> Path:
    manifest = read_manifest(manifest_path)
    export_dir = output_root / "yolo" / f"pothole_{version}"

    for split in ["train", "val", "test"]:
        (export_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (export_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    for item in manifest.items:
        if not item.split:
            raise ValueError(f"Item {item.image_id} has no split")

        image_destination = export_dir / "images" / item.split / item.image_path.name
        label_destination = export_dir / "labels" / item.split / f"{item.image_path.stem}.txt"
        shutil.copy2(item.image_path, image_destination)
        write_label(label_destination, [annotation.to_yolo_line() for annotation in item.annotations])

    split_counts = Counter(item.split or "unassigned" for item in manifest.items)
    annotation_counts = Counter()
    for item in manifest.items:
        annotation_counts[item.split or "unassigned"] += len(item.annotations)

    write_yaml(
        export_dir / "data.yaml",
        {
            "path": str(export_dir.resolve()),
            "train": "images/train",
            "val": "images/val",
            "test": "images/test",
            "names": {0: "pothole"},
        },
    )
    write_json(
        export_dir / "export_manifest.json",
        {
            "version": version,
            "source_manifest": str(manifest_path),
            "export_dir": str(export_dir.resolve()),
            "image_counts": dict(split_counts),
            "annotation_counts": dict(annotation_counts),
            "names": {0: "pothole"},
        },
    )
    return export_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CivicEye dataset version to YOLOv8 format.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output-root", default=Path("exports"), type=Path)
    args = parser.parse_args()

    manifest_path = args.manifest or Path("versions") / args.version / "manifest.json"
    export_dir = export_yolo(args.version, manifest_path, args.output_root)
    print(f"YOLO export written to {export_dir}")


if __name__ == "__main__":
    main()
