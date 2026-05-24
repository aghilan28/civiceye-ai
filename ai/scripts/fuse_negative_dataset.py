from __future__ import annotations

import argparse
from pathlib import Path

from ai.datasets.fusion import fuse_positive_and_negative_manifests, fusion_summary
from ai.utils.io import read_manifest, write_json, write_manifest


def fuse_datasets(
    positive_manifest_path: Path,
    negative_manifest_path: Path,
    output_manifest_path: Path,
    dataset_id: str,
    version: str,
    max_negative_ratio: float,
) -> Path:
    ai_root = _infer_ai_root(output_manifest_path)
    positive = read_manifest(positive_manifest_path, root=ai_root)
    negative = read_manifest(negative_manifest_path, root=ai_root)
    fused = fuse_positive_and_negative_manifests(positive, negative, dataset_id, version, max_negative_ratio)
    write_manifest(output_manifest_path, fused, ai_root)
    write_json(ai_root / "telemetry" / "fusion" / f"{version}_fusion_report.json", fusion_summary(fused))
    return output_manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Fuse pothole positives with road-context hard negatives.")
    parser.add_argument("--positive-manifest", required=True, type=Path)
    parser.add_argument("--negative-manifest", required=True, type=Path)
    parser.add_argument("--output-manifest", required=True, type=Path)
    parser.add_argument("--dataset-id", default="civiceye-pothole-negative-aware")
    parser.add_argument("--version", required=True)
    parser.add_argument("--max-negative-ratio", default=1.25, type=float)
    args = parser.parse_args()
    print(
        fuse_datasets(
            args.positive_manifest,
            args.negative_manifest,
            args.output_manifest,
            args.dataset_id,
            args.version,
            args.max_negative_ratio,
        )
    )


def _infer_ai_root(output_manifest: Path) -> Path:
    resolved = output_manifest.resolve()
    for parent in resolved.parents:
        if parent.name == "ai":
            return parent
    return Path.cwd()


if __name__ == "__main__":
    main()
