from __future__ import annotations

import argparse
from pathlib import Path

from ai.datasets.ingestion.download import download_source
from ai.datasets.ingestion.normalizers import merge_manifests, normalize_dataset
from ai.datasets.ingestion.sources import load_sources, source_to_dict
from ai.utils.io import write_json, write_manifest


def ingest_sources(
    sources_config: Path,
    dataset_id: str,
    version: str,
    raw_root: Path,
    output_manifest: Path,
    download: bool = False,
    force_download: bool = False,
) -> Path:
    sources = load_sources(sources_config)
    manifests = []
    telemetry = {"dataset_id": dataset_id, "version": version, "sources": []}
    for source in sources:
        try:
            if download:
                dataset_root = download_source(source, raw_root, force=force_download)
            elif source.local_path:
                dataset_root = source.local_path
            else:
                dataset_root = raw_root / source.source_id
            manifest = normalize_dataset(source, dataset_root, dataset_id, version)
            manifests.append(manifest)
            telemetry["sources"].append(
                {
                    **source_to_dict(source),
                    "resolved_root": str(dataset_root),
                    "status": "ingested",
                    "images": len(manifest.items),
                    "positive_images": sum(1 for item in manifest.items if item.has_pothole),
                    "negative_images": sum(1 for item in manifest.items if not item.has_pothole),
                    "annotations": sum(len(item.annotations) for item in manifest.items),
                }
            )
        except Exception as error:  # noqa: BLE001 - ingestion should report every inaccessible source
            telemetry["sources"].append(
                {
                    **source_to_dict(source),
                    "resolved_root": None,
                    "status": "failed",
                    "error": repr(error),
                    "images": 0,
                    "positive_images": 0,
                    "negative_images": 0,
                    "annotations": 0,
                }
            )

    ai_root = _infer_ai_root(output_manifest)
    if not manifests:
        write_json(ai_root / "telemetry" / "ingestion" / f"{version}_ingestion_report.json", telemetry)
        raise RuntimeError(f"No dataset sources could be ingested for {version}")

    merged = merge_manifests(dataset_id, version, manifests)
    write_manifest(output_manifest, merged, ai_root)
    telemetry["merged"] = {
        "images": len(merged.items),
        "positive_images": sum(1 for item in merged.items if item.has_pothole),
        "negative_images": sum(1 for item in merged.items if not item.has_pothole),
        "annotations": sum(len(item.annotations) for item in merged.items),
        "source_ids": merged.source_ids,
        "negative_quality_gate": {
            "has_negatives": any(not item.has_pothole for item in merged.items),
            "negative_sources": sorted({item.source_id for item in merged.items if not item.has_pothole}),
        },
    }
    write_json(ai_root / "telemetry" / "ingestion" / f"{version}_ingestion_report.json", telemetry)
    return output_manifest


def _infer_ai_root(output_manifest: Path) -> Path:
    resolved = output_manifest.resolve()
    for parent in resolved.parents:
        if parent.name == "ai":
            return parent
    return Path.cwd()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest real external datasets into a CivicEye canonical manifest.")
    parser.add_argument("--sources-config", required=True, type=Path)
    parser.add_argument("--dataset-id", default="civiceye-pothole-real")
    parser.add_argument("--version", required=True)
    parser.add_argument("--raw-root", default=Path("raw"), type=Path)
    parser.add_argument("--output-manifest", required=True, type=Path)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()
    output = ingest_sources(
        args.sources_config,
        args.dataset_id,
        args.version,
        args.raw_root,
        args.output_manifest,
        args.download,
        args.force_download,
    )
    print(f"Ingested manifest written to {output}")


if __name__ == "__main__":
    main()
