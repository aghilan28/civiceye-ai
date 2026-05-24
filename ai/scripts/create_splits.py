from __future__ import annotations

import argparse
import random
from dataclasses import replace
from pathlib import Path

from ai.utils.io import read_manifest, read_yaml, write_manifest
from ai.utils.schema import DatasetItem


def split_items(items: list[DatasetItem], ratios: dict[str, float], seed: int) -> list[DatasetItem]:
    grouped: dict[str, list[DatasetItem]] = {}
    for item in items:
        severity = item.annotations[0].severity if item.annotations else "none"
        key = f"{item.has_pothole}:{severity}:{item.source_id}"
        grouped.setdefault(key, []).append(item)

    rng = random.Random(seed)
    split_results: list[DatasetItem] = []

    for group_items in grouped.values():
        shuffled = group_items[:]
        rng.shuffle(shuffled)
        total = len(shuffled)
        train_end = int(total * ratios["train"])
        val_end = train_end + int(total * ratios["val"])

        for index, item in enumerate(shuffled):
            if index < train_end:
                split_name = "train"
            elif index < val_end:
                split_name = "val"
            else:
                split_name = "test"
            split_results.append(replace(item, split=split_name))

    return sorted(split_results, key=lambda item: item.image_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create reproducible train/val/test splits.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--config", default=Path("configs/splits/pothole_70_20_10.yaml"), type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output-dir", default=Path("versions"), type=Path)
    args = parser.parse_args()

    manifest = read_manifest(args.manifest)
    config = read_yaml(args.config)
    split_items_result = split_items(manifest.items, config["ratios"], int(config["seed"]))
    next_manifest = replace(manifest, version=args.version, items=split_items_result)
    output_path = args.output_dir / args.version / "manifest.json"
    write_manifest(output_path, next_manifest, Path.cwd())
    print(f"Split manifest written to {output_path}")


if __name__ == "__main__":
    main()
