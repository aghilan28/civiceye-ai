#!/usr/bin/env python3
"""
CivicEye — Dataset Validation Check (standalone)
=================================================
Run this to re-validate an already-downloaded dataset
WITHOUT re-downloading from Roboflow.

Usage:
    python ai/scripts/validate_dataset.py
    python ai/scripts/validate_dataset.py --path ai/datasets/raw/pothole_dataset
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("❌  PyYAML not found. Run: pip install pyyaml")

LOG_FORMAT = "%(asctime)s │ %(levelname)-8s │ %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt="%H:%M:%S")
log = logging.getLogger("civiceye.validate")

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
SPLITS     = ("train", "valid", "test")


def _count(directory: Path, exts: tuple) -> int:
    if not directory.exists():
        return 0
    return sum(1 for p in directory.iterdir() if p.suffix.lower() in exts)


def validate(dataset_path: Path) -> bool:
    log.info(f"Validating: {dataset_path}")
    passed = True

    # ── data.yaml ─────────────────────────────────────────────────────────────
    yaml_path = dataset_path / "data.yaml"
    if not yaml_path.exists():
        log.error("❌  data.yaml not found")
        return False

    with open(yaml_path) as fh:
        cfg = yaml.safe_load(fh)

    log.info(f"Classes ({cfg.get('nc', '?')}): {cfg.get('names', [])}")
    log.info("")

    # ── splits ────────────────────────────────────────────────────────────────
    total_images = 0
    total_labels = 0

    log.info(f"  {'Split':<8} {'Images':>8} {'Labels':>8} {'Status'}")
    log.info(f"  {'-'*8} {'-'*8} {'-'*8} {'-'*12}")

    for split in SPLITS:
        img_dir = dataset_path / split / "images"
        lbl_dir = dataset_path / split / "labels"
        n_img   = _count(img_dir, IMAGE_EXTS)
        n_lbl   = _count(lbl_dir, (".txt",))
        ok      = n_img > 0 and n_lbl > 0 and n_img == n_lbl
        icon    = "✓" if ok else ("⚠" if n_img == 0 else "❌")
        log.info(f"  {split:<8} {n_img:>8,} {n_lbl:>8,} {icon}")
        if not ok and n_img > 0:
            passed = False
        total_images += n_img
        total_labels += n_lbl

    log.info(f"  {'TOTAL':<8} {total_images:>8,} {total_labels:>8,}")
    log.info("")

    # ── manifest ──────────────────────────────────────────────────────────────
    manifest = dataset_path / "civiceye_manifest.json"
    if manifest.exists():
        with open(manifest) as fh:
            m = json.load(fh)
        log.info(f"CivicEye manifest: version={m.get('version')} acquired_at={m.get('acquired_at')}")
    else:
        log.warning("civiceye_manifest.json not found — run full acquisition to generate it")

    if passed and total_images > 0:
        log.info("✅  Dataset is valid and ready for training")
    elif total_images == 0:
        log.error("❌  No images found — dataset may not have downloaded correctly")
        passed = False
    else:
        log.warning("⚠  Dataset has mismatches — check above")

    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description="CivicEye dataset validator")
    parser.add_argument(
        "--path",
        default=None,
        help="Path to dataset root (default: auto-detect from project structure)",
    )
    args = parser.parse_args()

    if args.path:
        dataset_path = Path(args.path).resolve()
    else:
        root = Path(__file__).resolve().parent.parent.parent
        dataset_path = root / "ai" / "datasets" / "raw" / "pothole_dataset"

    if not dataset_path.exists():
        log.error(f"Dataset path does not exist: {dataset_path}")
        log.error("Run the acquisition script first:")
        log.error("  python ai/scripts/download_roboflow_dataset.py")
        sys.exit(1)

    ok = validate(dataset_path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
