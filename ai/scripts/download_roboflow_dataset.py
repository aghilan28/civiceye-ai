#!/usr/bin/env python3
"""
CivicEye — Roboflow Dataset Acquisition Pipeline
=================================================
Downloads the "New pothole detection" dataset from the Smartathon workspace
in YOLOv8 format, validates the export, generates statistics, and integrates
the dataset into the CivicEye AI workspace.

Usage:
    ROBOFLOW_API_KEY=<key> python ai/scripts/download_roboflow_dataset.py

Environment variables:
    ROBOFLOW_API_KEY   (required) Your Roboflow private API key
    RF_WORKSPACE       (optional) Override workspace slug  [default: smartathon]
    RF_PROJECT         (optional) Override project slug    [default: auto-detect]
    RF_VERSION         (optional) Override dataset version [default: latest]
    CIVICEYE_ROOT      (optional) Override project root    [default: script parent/../..]
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── third-party (installed by this script's requirements) ──────────────────────
try:
    import yaml
except ImportError:
    sys.exit("❌  PyYAML not found. Run: pip install pyyaml")

try:
    from roboflow import Roboflow
    from roboflow.core.project import Project
    from roboflow.core.version import Version
except ImportError:
    sys.exit("❌  roboflow SDK not found. Run: pip install roboflow")

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None  # graceful degradation

# ── logging setup ─────────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s │ %(levelname)-8s │ %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt="%H:%M:%S")
log = logging.getLogger("civiceye.acquire")

# ── constants ─────────────────────────────────────────────────────────────────
DEFAULT_WORKSPACE  = "smartathon"
DEFAULT_PROJECT    = "new-pothole-detection"          # Roboflow slug form
EXPORT_FORMAT      = "yolov8"
DATASET_SPLITS     = ("train", "valid", "test")
MAX_RETRIES        = 3
RETRY_DELAY_SEC    = 5


# ══════════════════════════════════════════════════════════════════════════════
# Data-classes
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SplitStats:
    name: str
    images: int = 0
    labels: int = 0
    matched: int = 0
    unmatched_images: List[str] = field(default_factory=list)
    unmatched_labels: List[str] = field(default_factory=list)
    class_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def healthy(self) -> bool:
        return self.images > 0 and self.labels > 0 and self.unmatched_images == [] and self.unmatched_labels == []


@dataclass
class AcquisitionReport:
    timestamp: str
    workspace: str
    project: str
    version: int
    format: str
    dataset_path: str
    total_images: int
    total_labels: int
    splits: Dict[str, SplitStats] = field(default_factory=dict)
    class_names: List[str] = field(default_factory=list)
    class_distribution: Dict[str, int] = field(default_factory=dict)
    yaml_valid: bool = False
    yaml_path: str = ""
    download_duration_sec: float = 0.0
    validation_passed: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_paths() -> Tuple[Path, Path, Path]:
    """Return (civiceye_root, datasets_dir, scripts_dir)."""
    env_root = os.environ.get("CIVICEYE_ROOT")
    if env_root:
        root = Path(env_root).resolve()
    else:
        # script is at ai/scripts/ → root is two levels up
        root = Path(__file__).resolve().parent.parent.parent
    datasets_dir = root / "ai" / "datasets" / "raw" / "pothole_dataset"
    scripts_dir  = root / "ai" / "scripts"
    return root, datasets_dir, scripts_dir


def _get_api_key() -> str:
    key = os.environ.get("ROBOFLOW_API_KEY", "").strip()
    if not key:
        log.error("ROBOFLOW_API_KEY environment variable is not set.")
        log.error("Export it before running:")
        log.error("  Linux/macOS : export ROBOFLOW_API_KEY=your_key_here")
        log.error("  Windows CMD : set ROBOFLOW_API_KEY=your_key_here")
        log.error("  PowerShell  : $env:ROBOFLOW_API_KEY='your_key_here'")
        sys.exit(1)
    return key


def _retry(fn, label: str, retries: int = MAX_RETRIES, delay: float = RETRY_DELAY_SEC):
    """Call fn() with exponential-back-off retry on exception."""
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == retries:
                raise
            wait = delay * attempt
            log.warning(f"{label} — attempt {attempt}/{retries} failed: {exc}. Retrying in {wait}s …")
            time.sleep(wait)


def _count_files(directory: Path, extensions: Tuple[str, ...]) -> List[Path]:
    if not directory.exists():
        return []
    return sorted([p for p in directory.iterdir() if p.suffix.lower() in extensions])


def _parse_label_file(label_path: Path) -> Dict[str, int]:
    """Return {class_id_str: count} from a YOLO .txt label file."""
    counts: Dict[str, int] = {}
    try:
        with open(label_path, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                cls = line.split()[0]
                counts[cls] = counts.get(cls, 0) + 1
    except Exception:
        pass
    return counts


# ══════════════════════════════════════════════════════════════════════════════
# Core acquisition
# ══════════════════════════════════════════════════════════════════════════════

def authenticate(api_key: str, workspace: str) -> Tuple[Roboflow, object]:
    log.info(f"Authenticating with Roboflow (workspace: {workspace}) …")
    rf = Roboflow(api_key=api_key)
    ws = _retry(lambda: rf.workspace(workspace), "workspace lookup")
    log.info("✓ Authentication successful")
    return rf, ws


def resolve_project(ws, project_slug: str) -> Project:
    log.info(f"Resolving project '{project_slug}' …")
    project: Project = _retry(lambda: ws.project(project_slug), "project lookup")
    log.info(f"✓ Project found: {project.name}")
    return project


def resolve_version(project: Project, version_number: Optional[int]) -> Version:
    if version_number:
        log.info(f"Fetching version {version_number} …")
        version: Version = _retry(lambda: project.version(version_number), "version lookup")
    else:
        log.info("Fetching latest version …")
        versions = _retry(lambda: project.versions(), "versions listing")
        if not versions:
            sys.exit("❌  No versions found in project. Generate a dataset version in Roboflow UI first.")
        version = versions[-1]          # latest
    log.info(f"✓ Using dataset version {version.version}")
    return version


def download_dataset(version: Version, dest: Path, fmt: str) -> Path:
    """
    Download dataset to dest directory.
    Roboflow SDK places files inside a sub-folder named after the project version.
    We detect that folder and return it.
    """
    dest.mkdir(parents=True, exist_ok=True)

    log.info(f"Downloading dataset (format={fmt}) …")
    log.info(f"Destination: {dest}")

    t0 = time.time()
    dataset = _retry(
        lambda: version.download(fmt, location=str(dest), overwrite=True),
        "dataset download",
    )
    elapsed = time.time() - t0
    log.info(f"✓ Download completed in {elapsed:.1f}s")

    # The SDK creates the dataset under dest/<project>-<version>/
    # Detect it automatically.
    candidates = [p for p in dest.iterdir() if p.is_dir()]
    if len(candidates) == 1:
        inner = candidates[0]
        log.info(f"Detected dataset root: {inner.name}")
        return inner, elapsed
    elif len(candidates) > 1:
        # Pick the one that contains data.yaml
        for c in candidates:
            if (c / "data.yaml").exists():
                log.info(f"Detected dataset root (by data.yaml): {c.name}")
                return c, elapsed
    # Fallback — return dest itself
    return dest, elapsed


def flatten_into_dest(inner: Path, dest: Path) -> None:
    """
    If SDK placed files inside a sub-directory, move them up to dest.
    i.e.  dest/new-pothole-detection-3/{train,valid,test,data.yaml}
          → dest/{train,valid,test,data.yaml}
    """
    if inner == dest:
        return
    log.info(f"Flattening: {inner.name}/ → {dest.name}/")
    for item in inner.iterdir():
        target = dest / item.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(item), str(target))
    inner.rmdir()
    log.info("✓ Dataset directory flattened")


# ══════════════════════════════════════════════════════════════════════════════
# Validation
# ══════════════════════════════════════════════════════════════════════════════

def validate_yaml(dataset_path: Path, report: AcquisitionReport) -> Dict:
    yaml_path = dataset_path / "data.yaml"
    if not yaml_path.exists():
        report.errors.append("data.yaml not found")
        log.error("❌  data.yaml not found")
        return {}

    with open(yaml_path) as fh:
        cfg = yaml.safe_load(fh)

    required_keys = {"train", "val", "nc", "names"}
    missing = required_keys - set(cfg.keys())
    if missing:
        report.errors.append(f"data.yaml missing keys: {missing}")
        log.error(f"❌  data.yaml missing keys: {missing}")
        return cfg

    report.class_names = cfg.get("names", [])
    report.yaml_valid  = True
    report.yaml_path   = str(yaml_path)

    # Patch paths to be absolute so training scripts work from any cwd
    cfg["train"] = str(dataset_path / "train" / "images")
    cfg["val"]   = str(dataset_path / "valid" / "images")
    if "test" in cfg:
        cfg["test"] = str(dataset_path / "test" / "images")

    with open(yaml_path, "w") as fh:
        yaml.dump(cfg, fh, default_flow_style=False, sort_keys=False)

    log.info(f"✓ data.yaml valid — {cfg['nc']} classes: {cfg['names']}")
    return cfg


def validate_split(split: str, dataset_path: Path, class_names: List[str]) -> SplitStats:
    stats = SplitStats(name=split)
    img_dir = dataset_path / split / "images"
    lbl_dir = dataset_path / split / "labels"

    if not img_dir.exists():
        log.warning(f"  [{split}] images/ directory not found — split may be absent")
        return stats
    if not lbl_dir.exists():
        log.warning(f"  [{split}] labels/ directory not found")
        return stats

    img_files = {p.stem: p for p in _count_files(img_dir, (".jpg", ".jpeg", ".png", ".bmp", ".webp"))}
    lbl_files = {p.stem: p for p in _count_files(lbl_dir, (".txt",))}

    stats.images = len(img_files)
    stats.labels = len(lbl_files)

    # Match check
    img_stems = set(img_files.keys())
    lbl_stems = set(lbl_files.keys())
    matched   = img_stems & lbl_stems
    stats.matched           = len(matched)
    stats.unmatched_images  = sorted(img_stems - lbl_stems)[:10]   # cap report to 10
    stats.unmatched_labels  = sorted(lbl_stems - img_stems)[:10]

    # Class distribution
    for stem in matched:
        cls_counts = _parse_label_file(lbl_files[stem])
        for cls_id, cnt in cls_counts.items():
            try:
                cls_name = class_names[int(cls_id)] if class_names else cls_id
            except (IndexError, ValueError):
                cls_name = f"cls_{cls_id}"
            stats.class_counts[cls_name] = stats.class_counts.get(cls_name, 0) + cnt

    status_icon = "✓" if stats.healthy else "⚠"
    log.info(
        f"  {status_icon} [{split:5s}] images={stats.images:5d}  labels={stats.labels:5d}  "
        f"matched={stats.matched:5d}  unmatched_img={len(stats.unmatched_images)}  "
        f"unmatched_lbl={len(stats.unmatched_labels)}"
    )
    return stats


def run_validation(dataset_path: Path, report: AcquisitionReport) -> None:
    log.info("── Validation ────────────────────────────────────────────────")
    yaml_cfg = validate_yaml(dataset_path, report)

    total_images = 0
    total_labels = 0
    global_class_dist: Dict[str, int] = {}

    for split in DATASET_SPLITS:
        stats = validate_split(split, dataset_path, report.class_names)
        report.splits[split] = stats
        total_images += stats.images
        total_labels += stats.labels
        for cls, cnt in stats.class_counts.items():
            global_class_dist[cls] = global_class_dist.get(cls, 0) + cnt

    report.total_images      = total_images
    report.total_labels      = total_labels
    report.class_distribution = global_class_dist

    # Decide overall validation pass
    critical_errors = [e for e in report.errors]
    has_images      = total_images > 0
    has_labels      = total_labels > 0

    if not has_images:
        report.errors.append("No images found in any split")
    if not has_labels:
        report.errors.append("No labels found in any split")

    report.validation_passed = (
        report.yaml_valid
        and has_images
        and has_labels
        and not critical_errors
    )

    if report.validation_passed:
        log.info("✓ Validation PASSED")
    else:
        log.error("❌  Validation FAILED")
        for e in report.errors:
            log.error(f"   • {e}")


# ══════════════════════════════════════════════════════════════════════════════
# Reporting
# ══════════════════════════════════════════════════════════════════════════════

def _bar(value: int, total: int, width: int = 30) -> str:
    if total == 0:
        return " " * width
    filled = int(round(value / total * width))
    return "█" * filled + "░" * (width - filled)


def print_report(report: AcquisitionReport) -> None:
    SEP = "═" * 70
    sep = "─" * 70

    print(f"\n{SEP}")
    print(f"  CivicEye — Dataset Acquisition Report")
    print(f"  {report.timestamp}")
    print(SEP)
    print(f"  Workspace  : {report.workspace}")
    print(f"  Project    : {report.project}")
    print(f"  Version    : {report.version}")
    print(f"  Format     : {report.format}")
    print(f"  Path       : {report.dataset_path}")
    print(f"  Download   : {report.download_duration_sec:.1f}s")
    print(sep)

    print("  SPLIT DISTRIBUTION")
    print(f"  {'Split':<8} {'Images':>8} {'Labels':>8} {'Matched':>8}")
    print(f"  {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    for split, stats in report.splits.items():
        print(f"  {split:<8} {stats.images:>8,} {stats.labels:>8,} {stats.matched:>8,}")
    print(f"  {'TOTAL':<8} {report.total_images:>8,} {report.total_labels:>8,}")
    print(sep)

    if report.class_distribution:
        print("  CLASS DISTRIBUTION")
        total_annotations = sum(report.class_distribution.values())
        for cls, cnt in sorted(report.class_distribution.items(), key=lambda x: -x[1]):
            pct  = cnt / total_annotations * 100 if total_annotations else 0
            bar  = _bar(cnt, total_annotations)
            print(f"  {cls:<25} {bar}  {cnt:>7,}  ({pct:5.1f}%)")
        print(f"  {'Total annotations':<25} {'':30}  {total_annotations:>7,}")
    print(sep)

    status = "✓  PASSED" if report.validation_passed else "❌  FAILED"
    print(f"  Validation : {status}")
    if report.warnings:
        for w in report.warnings:
            print(f"  ⚠  {w}")
    if report.errors:
        for e in report.errors:
            print(f"  ❌  {e}")
    print(f"{SEP}\n")


def save_report(report: AcquisitionReport, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = report.timestamp.replace(":", "-").replace(" ", "_")
    out = reports_dir / f"acquisition_{ts}.json"

    # Convert dataclasses recursively
    def _serial(obj):
        if isinstance(obj, SplitStats):
            return asdict(obj)
        raise TypeError(f"Not serializable: {type(obj)}")

    payload = {
        "timestamp":             report.timestamp,
        "workspace":             report.workspace,
        "project":               report.project,
        "version":               report.version,
        "format":                report.format,
        "dataset_path":          report.dataset_path,
        "total_images":          report.total_images,
        "total_labels":          report.total_labels,
        "class_names":           report.class_names,
        "class_distribution":    report.class_distribution,
        "splits":                {k: asdict(v) for k, v in report.splits.items()},
        "yaml_valid":            report.yaml_valid,
        "yaml_path":             report.yaml_path,
        "download_duration_sec": report.download_duration_sec,
        "validation_passed":     report.validation_passed,
        "errors":                report.errors,
        "warnings":              report.warnings,
    }

    with open(out, "w") as fh:
        json.dump(payload, fh, indent=2)

    log.info(f"Report saved → {out}")
    return out


def write_dataset_manifest(dataset_path: Path, report: AcquisitionReport) -> None:
    """Write a machine-readable manifest consumed by CivicEye's validation pipeline."""
    manifest = {
        "name":               report.project,
        "version":            report.version,
        "format":             report.format,
        "acquired_at":        report.timestamp,
        "total_images":       report.total_images,
        "total_labels":       report.total_labels,
        "class_names":        report.class_names,
        "class_distribution": report.class_distribution,
        "splits": {
            split: {
                "images": stats.images,
                "labels": stats.labels,
                "matched": stats.matched,
            }
            for split, stats in report.splits.items()
        },
        "validation_passed": report.validation_passed,
    }
    out = dataset_path / "civiceye_manifest.json"
    with open(out, "w") as fh:
        json.dump(manifest, fh, indent=2)
    log.info(f"CivicEye manifest written → {out}")


# ══════════════════════════════════════════════════════════════════════════════
# Pipeline discovery helper (prints how to find slug from URL)
# ══════════════════════════════════════════════════════════════════════════════

def _print_slug_guide() -> None:
    print("""
┌─────────────────────────────────────────────────────────────────┐
│  How to find your Roboflow project slug                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Open the project in Roboflow UI                             │
│  2. Look at the browser URL:                                    │
│                                                                 │
│     https://app.roboflow.com/<workspace>/<project>/            │
│                              ^^^^^^^^^^^  ^^^^^^^              │
│                              workspace    project slug         │
│                                                                 │
│  Example:                                                       │
│     https://app.roboflow.com/smartathon/new-pothole-detection/  │
│     → workspace = smartathon                                    │
│     → project   = new-pothole-detection                        │
│                                                                 │
│  Set these as env vars:                                         │
│     export RF_WORKSPACE=smartathon                              │
│     export RF_PROJECT=new-pothole-detection                     │
│     export RF_VERSION=3   # optional — omit for latest         │
└─────────────────────────────────────────────────────────────────┘
""")


# ══════════════════════════════════════════════════════════════════════════════
# Entrypoint
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    import datetime

    log.info("══════════════════════════════════════════════════════════")
    log.info("  CivicEye — Roboflow Dataset Acquisition Pipeline")
    log.info("══════════════════════════════════════════════════════════")

    # ── config from env ───────────────────────────────────────────────────────
    api_key        = _get_api_key()
    workspace_slug = os.environ.get("RF_WORKSPACE", DEFAULT_WORKSPACE).strip()
    project_slug   = os.environ.get("RF_PROJECT",   DEFAULT_PROJECT).strip()
    version_str    = os.environ.get("RF_VERSION",   "").strip()
    version_number = int(version_str) if version_str.isdigit() else None

    root, datasets_dir, scripts_dir = _resolve_paths()

    log.info(f"CivicEye root : {root}")
    log.info(f"Dataset dest  : {datasets_dir}")
    log.info(f"Workspace     : {workspace_slug}")
    log.info(f"Project       : {project_slug}")
    log.info(f"Version       : {version_number or 'latest'}")

    _print_slug_guide()

    # ── report scaffold ───────────────────────────────────────────────────────
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = AcquisitionReport(
        timestamp    = ts,
        workspace    = workspace_slug,
        project      = project_slug,
        version      = version_number or 0,
        format       = EXPORT_FORMAT,
        dataset_path = str(datasets_dir),
        total_images = 0,
        total_labels = 0,
    )

    # ── authenticate ──────────────────────────────────────────────────────────
    try:
        rf, ws = authenticate(api_key, workspace_slug)
    except Exception as exc:
        log.error(f"Authentication failed: {exc}")
        log.error("Check your ROBOFLOW_API_KEY and workspace slug.")
        sys.exit(1)

    # ── project ───────────────────────────────────────────────────────────────
    try:
        project = resolve_project(ws, project_slug)
    except Exception as exc:
        log.error(f"Could not find project '{project_slug}': {exc}")
        log.error("Verify the slug using the URL guide above, then set RF_PROJECT=<slug>")
        sys.exit(1)

    # ── version ───────────────────────────────────────────────────────────────
    try:
        version = resolve_version(project, version_number)
        report.version = version.version
    except Exception as exc:
        log.error(f"Could not resolve dataset version: {exc}")
        sys.exit(1)

    # ── download ──────────────────────────────────────────────────────────────
    log.info("── Download ──────────────────────────────────────────────────")
    try:
        inner_path, elapsed = download_dataset(version, datasets_dir, EXPORT_FORMAT)
        report.download_duration_sec = elapsed
    except Exception as exc:
        log.error(f"Download failed: {exc}")
        report.errors.append(f"Download failed: {exc}")
        sys.exit(1)

    # Flatten if SDK nested into a sub-folder
    flatten_into_dest(inner_path, datasets_dir)

    # ── validate ──────────────────────────────────────────────────────────────
    log.info("── Validation ────────────────────────────────────────────────")
    run_validation(datasets_dir, report)

    # ── persist artifacts ─────────────────────────────────────────────────────
    reports_dir = root / "ai" / "reports"
    write_dataset_manifest(datasets_dir, report)
    report_path = save_report(report, reports_dir)

    # ── human-readable report ─────────────────────────────────────────────────
    print_report(report)

    # ── final summary ─────────────────────────────────────────────────────────
    if report.validation_passed:
        log.info("✅  Dataset acquisition complete — ready for YOLOv8 training")
        log.info(f"   data.yaml : {datasets_dir / 'data.yaml'}")
        log.info(f"   Report    : {report_path}")
        log.info("")
        log.info("   Next step (example):")
        log.info(f"   yolo detect train data={datasets_dir / 'data.yaml'} model=yolov8n.pt epochs=50 imgsz=640")
    else:
        log.error("❌  Acquisition completed WITH ERRORS — review report before training")
        sys.exit(1)


if __name__ == "__main__":
    main()
