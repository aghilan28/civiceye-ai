from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import yaml

try:
    from ai.datasets.negative_filter import NegativeFilterConfig, score_negative_image
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from ai.datasets.negative_filter import NegativeFilterConfig, score_negative_image


ROBOFLOW_API_ROOT = "https://api.roboflow.com"
EXPORT_FORMAT = "yolov8"
RANDOM_SEED = 42

POSITIVE_DATASETS = [
    {"workspace": "smartathon", "project": "new-pothole-detection", "version": None},
    {"workspace": "brad-dwyer", "project": "pothole-voxrl", "version": None},
    {"workspace": "baka-1ravj", "project": "road-damage-det", "version": None},
    {"workspace": "aegis", "project": "pothole-detection-i00zy", "version": None},
    {"workspace": "potholes-r7qcn", "project": "pothole-jujbl", "version": None},
    {"workspace": "jerry-cooper-tlzkx", "project": "pothole_detection-hfnqo", "version": None},
]

NEGATIVE_DATASETS = [
    {"workspace": "eastsky", "project": "bdd100k-e3s18", "version": None},
    {"workspace": "transportation-0bexg", "project": "autonomous-driving-40ukk", "version": None},
    {"workspace": "cityscapeseyolo", "project": "cityscapes-hgg49", "version": None},
    {"workspace": "yoav9113-gmail-com", "project": "cityscapes-wqjba", "version": None},
    {"workspace": "object-detection-yy9t1", "project": "road-segmentation-olxqu", "version": None},
]

SPLITS = ("train", "valid", "test")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
LABEL_SUFFIX = ".txt"


@dataclass(frozen=True)
class RoboflowSource:
    role: str
    workspace: str
    project: str
    version: int | None = None
    format: str = EXPORT_FORMAT

    @property
    def source_id(self) -> str:
        return f"{self.role}_{self.workspace}_{self.project}".lower().replace("-", "_").replace("/", "_")


@dataclass
class DatasetTelemetry:
    source: RoboflowSource
    status: str = "pending"
    resolved_version: int | None = None
    download_seconds: float | None = None
    extraction_dir: str | None = None
    images_seen: int = 0
    images_accepted: int = 0
    labels_seen: int = 0
    labels_written: int = 0
    rejected_images: int = 0
    duplicate_images: int = 0
    invalid_labels: int = 0
    missing_labels: int = 0
    empty_labels: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["source"] = asdict(self.source)
        return payload


@dataclass
class PipelinePaths:
    repo_root: Path
    ai_root: Path
    raw_root: Path
    merged_root: Path
    logs_root: Path
    telemetry_root: Path
    train_runs_root: Path


def main() -> None:
    paths = build_paths()
    configure_logging(paths.logs_root)
    started_at = time.perf_counter()
    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        raise SystemExit(
            "ROBOFLOW_API_KEY is required. Set it in PowerShell with "
            "$env:ROBOFLOW_API_KEY='<your-key>' and rerun this script."
        )

    sources = [RoboflowSource("positive", **item) for item in POSITIVE_DATASETS]
    sources.extend(RoboflowSource("negative", **item) for item in NEGATIVE_DATASETS)
    telemetry: list[DatasetTelemetry] = []
    seen_hashes: set[str] = set()

    clean_merged_dataset(paths.merged_root)
    validate_api_key(api_key)

    for source in sources:
        record = DatasetTelemetry(source=source)
        telemetry.append(record)
        try:
            process_source(source, record, paths, api_key, seen_hashes)
        except Exception as error:  # noqa: BLE001 - each source should fail independently
            record.status = "failed"
            record.errors.append(repr(error))
            logging.exception("Source failed: %s/%s", source.workspace, source.project)

    ensure_merged_structure(paths.merged_root)
    merged_report = validate_merged_dataset(paths.merged_root)
    manifest_path = write_civiceye_manifest(paths.merged_root, telemetry, merged_report)
    write_data_yaml(paths.merged_root)

    pipeline_report = {
        "created_at": datetime.now(UTC).isoformat(),
        "duration_seconds": round(time.perf_counter() - started_at, 3),
        "roboflow_sources": [record.to_dict() for record in telemetry],
        "merged_dataset": merged_report,
        "manifest": str(manifest_path),
        "data_yaml": str(paths.merged_root / "data.yaml"),
    }
    write_json(paths.telemetry_root / "download_merge_report.json", pipeline_report)
    logging.info("Merged dataset report: %s", json.dumps(merged_report, indent=2))

    if merged_report["positive_images"] == 0:
        raise SystemExit("No positive pothole images were merged. Training was not launched.")
    if merged_report["negative_images"] == 0:
        raise SystemExit("No negative road-context images were merged. Training was not launched.")
    if not merged_report["passed"]:
        raise SystemExit("Merged dataset validation failed. Training was not launched.")

    launch_training(paths)


def build_paths() -> PipelinePaths:
    ai_root = Path(__file__).resolve().parents[1]
    repo_root = ai_root.parent
    return PipelinePaths(
        repo_root=repo_root,
        ai_root=ai_root,
        raw_root=ai_root / "raw" / "roboflow_downloads",
        merged_root=ai_root / "datasets" / "merged" / "pothole_combined",
        logs_root=ai_root / "logs" / "download_merge",
        telemetry_root=ai_root / "telemetry" / "download_merge",
        train_runs_root=ai_root / "experiments" / "pothole_combined",
    )


def configure_logging(logs_root: Path) -> None:
    logs_root.mkdir(parents=True, exist_ok=True)
    log_file = logs_root / f"download_merge_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )
    logging.info("CivicEye Roboflow download + merge pipeline started")


def validate_api_key(api_key: str) -> None:
    url = f"{ROBOFLOW_API_ROOT}/?api_key={urllib.parse.quote(api_key)}"
    payload = request_json(url, "validate Roboflow API key")
    logging.info("Roboflow API key validated: %s", payload.get("welcome", "ok"))


def process_source(
    source: RoboflowSource,
    record: DatasetTelemetry,
    paths: PipelinePaths,
    api_key: str,
    seen_hashes: set[str],
) -> None:
    logging.info("Processing %s source %s/%s", source.role, source.workspace, source.project)
    try:
        version = resolve_version(source, api_key)
    except RuntimeError as exc:
        logging.warning(
            "Skipping inaccessible dataset %s/%s — version resolution failed: %s",
            source.workspace,
            source.project,
            exc,
        )
        record.status = "skipped"
        record.errors.append(repr(exc))
        return
    record.resolved_version = version
    dataset_dir = download_and_extract(source, version, paths.raw_root, api_key, record)
    record.extraction_dir = str(dataset_dir)
    validate_extracted_yolo(dataset_dir)
    merge_dataset(source, dataset_dir, paths.merged_root, record, seen_hashes)
    record.status = "merged"
    logging.info(
        "Merged %s/%s v%s: accepted=%s rejected=%s duplicates=%s",
        source.workspace,
        source.project,
        version,
        record.images_accepted,
        record.rejected_images,
        record.duplicate_images,
    )


def resolve_version(source: RoboflowSource, api_key: str) -> int:
    override_name = f"CIVICEYE_ROBOFLOW_VERSION_{source.project.upper().replace('-', '_').replace('_', '_')}"
    if os.environ.get(override_name):
        return int(os.environ[override_name])
    if source.version:
        return int(source.version)
    url = f"{ROBOFLOW_API_ROOT}/{source.workspace}/{source.project}?api_key={urllib.parse.quote(api_key)}"
    payload = request_json(url, f"resolve latest version for {source.workspace}/{source.project}")
    versions = payload.get("versions") or payload.get("project", {}).get("versions") or []
    version_numbers: list[int] = []
    for item in versions:
        if isinstance(item, int):
            version_numbers.append(item)
        elif isinstance(item, dict):
            candidate = item.get("version") or item.get("id") or item.get("name")
            try:
                version_numbers.append(int(str(candidate).split("/")[-1]))
            except (TypeError, ValueError):
                continue
    if not version_numbers:
        raise RuntimeError(f"Could not resolve dataset versions for {source.workspace}/{source.project}: "
                           f"dataset may be private, deleted, or inaccessible with the current API key")
    latest = max(version_numbers)
    logging.info("Resolved latest version for %s/%s: %s", source.workspace, source.project, latest)
    return latest


def download_and_extract(
    source: RoboflowSource,
    version: int,
    raw_root: Path,
    api_key: str,
    record: DatasetTelemetry,
) -> Path:
    target_dir = raw_root / source.role / source.workspace / source.project / f"v{version}"
    extracted_dir = target_dir / "extracted"
    done_marker = target_dir / ".download_complete"
    if done_marker.exists() and validate_extracted_yolo(extracted_dir, raise_on_error=False):
        logging.info("Skipping existing valid download: %s", extracted_dir)
        return extracted_dir

    target_dir.mkdir(parents=True, exist_ok=True)
    archive_path = target_dir / f"{source.project}_v{version}_{source.format}.zip"
    export_url = (
        f"{ROBOFLOW_API_ROOT}/{source.workspace}/{source.project}/{version}/{source.format}"
        f"?api_key={urllib.parse.quote(api_key)}"
    )
    started = time.perf_counter()
    export_payload = request_json(export_url, f"request export link for {source.workspace}/{source.project}/{version}")
    # Roboflow v2 wraps the link under export.link; fall back to top-level keys for older API shapes.
    download_url = (
        export_payload.get("export", {}).get("link")
        or export_payload.get("link")
        or export_payload.get("download")
        or export_payload.get("url")
    )
    if not download_url:
        raise RuntimeError(
            f"Could not resolve Roboflow export download link: {export_payload}"
        )
    download_file_with_retries(str(download_url), archive_path)
    record.download_seconds = round(time.perf_counter() - started, 3)

    if extracted_dir.exists():
        shutil.rmtree(extracted_dir)
    safe_extract_zip(archive_path, extracted_dir)
    validate_extracted_yolo(extracted_dir)
    done_marker.write_text(datetime.now(UTC).isoformat(), encoding="utf-8")
    return extracted_dir


def request_json(url: str, action: str, retries: int = 3) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as error:
            last_error = error
            wait_seconds = 2**attempt
            logging.warning("%s failed on attempt %s/%s: %r", action, attempt, retries, error)
            time.sleep(wait_seconds)
    raise RuntimeError(f"Failed to {action}") from last_error


def download_file_with_retries(url: str, output_path: Path, retries: int = 3) -> None:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            tmp_path = output_path.with_suffix(output_path.suffix + ".part")
            with urllib.request.urlopen(url, timeout=240) as response, tmp_path.open("wb") as handle:
                shutil.copyfileobj(response, handle)
            tmp_path.replace(output_path)
            if output_path.stat().st_size <= 0:
                raise RuntimeError(f"Downloaded file is empty: {output_path}")
            return
        except Exception as error:  # noqa: BLE001 - download retry should catch transient failures
            last_error = error
            logging.warning("Download failed on attempt %s/%s: %r", attempt, retries, error)
            time.sleep(2**attempt)
    raise RuntimeError(f"Failed to download {url}") from last_error


def safe_extract_zip(archive_path: Path, output_dir: Path) -> None:
    if not zipfile.is_zipfile(archive_path):
        raise RuntimeError(f"Downloaded archive is not a valid zip: {archive_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_root = output_dir.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            destination = (output_dir / member.filename).resolve()
            if not str(destination).startswith(str(output_root)):
                raise RuntimeError(f"Unsafe zip member path: {member.filename}")
        archive.extractall(output_dir)


def validate_extracted_yolo(dataset_dir: Path, raise_on_error: bool = True) -> bool:
    issues: list[str] = []
    data_yaml = find_data_yaml(dataset_dir)
    if not data_yaml:
        issues.append("missing data.yaml")
    for split in SPLITS:
        image_dir = find_split_dir(dataset_dir, split, "images")
        label_dir = find_split_dir(dataset_dir, split, "labels")
        if not image_dir:
            issues.append(f"missing {split}/images")
            continue
        if not label_dir:
            issues.append(f"missing {split}/labels")
            continue
        images = list_images(image_dir)
        labels = list(label_dir.glob("*.txt"))
        if not images:
            issues.append(f"empty {split}/images")
        label_stems = {label.stem for label in labels}
        for image_path in images:
            if image_path.stem not in label_stems:
                issues.append(f"missing label for {image_path}")
    if issues and raise_on_error:
        raise RuntimeError(f"Invalid YOLO export at {dataset_dir}: {issues[:12]}")
    return not issues


def merge_dataset(
    source: RoboflowSource,
    dataset_dir: Path,
    merged_root: Path,
    record: DatasetTelemetry,
    seen_hashes: set[str],
) -> None:
    for split in SPLITS:
        image_dir = find_split_dir(dataset_dir, split, "images")
        label_dir = find_split_dir(dataset_dir, split, "labels")
        if not image_dir or not label_dir:
            continue
        for image_path in list_images(image_dir):
            record.images_seen += 1
            label_path = label_dir / f"{image_path.stem}.txt"
            if label_path.exists():
                record.labels_seen += 1
            else:
                record.missing_labels += 1

            image = cv2.imread(str(image_path))
            if image is None:
                record.rejected_images += 1
                continue
            digest = sha256_file(image_path)
            if digest in seen_hashes:
                record.duplicate_images += 1
                continue
            if source.role == "negative":
                quality = score_negative_image(image_path, NegativeFilterConfig())
                if not quality.accepted:
                    record.rejected_images += 1
                    continue
                normalized_lines: list[str] = []
            else:
                normalized_lines, invalid_count = normalize_positive_labels(label_path)
                record.invalid_labels += invalid_count
                if not normalized_lines:
                    record.empty_labels += 1
                    record.rejected_images += 1
                    continue

            safe_stem = f"{source.source_id}_{split}_{image_path.stem}".replace(" ", "_")
            output_image = merged_root / split / "images" / f"{safe_stem}{image_path.suffix.lower()}"
            output_label = merged_root / split / "labels" / f"{safe_stem}{LABEL_SUFFIX}"
            output_image.parent.mkdir(parents=True, exist_ok=True)
            output_label.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, output_image)
            output_label.write_text("\n".join(normalized_lines) + ("\n" if normalized_lines else ""), encoding="utf-8")
            seen_hashes.add(digest)
            record.images_accepted += 1
            record.labels_written += 1


def normalize_positive_labels(label_path: Path) -> tuple[list[str], int]:
    if not label_path.exists():
        return [], 1
    lines: list[str] = []
    invalid = 0
    for raw_line in label_path.read_text(encoding="utf-8").splitlines():
        parts = raw_line.strip().split()
        if len(parts) < 5:
            invalid += 1
            continue
        try:
            x_center, y_center, width, height = [float(value) for value in parts[1:5]]
        except ValueError:
            invalid += 1
            continue
        if not all(0.0 <= value <= 1.0 for value in (x_center, y_center, width, height)):
            invalid += 1
            continue
        if width <= 0.0 or height <= 0.0:
            invalid += 1
            continue
        lines.append(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
    return lines, invalid


def clean_merged_dataset(merged_root: Path) -> None:
    if merged_root.exists():
        shutil.rmtree(merged_root)
    ensure_merged_structure(merged_root)


def ensure_merged_structure(merged_root: Path) -> None:
    for split in SPLITS:
        (merged_root / split / "images").mkdir(parents=True, exist_ok=True)
        (merged_root / split / "labels").mkdir(parents=True, exist_ok=True)


def validate_merged_dataset(merged_root: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    split_counts: dict[str, dict[str, int]] = {}
    positive_images = 0
    negative_images = 0
    annotation_count = 0
    hashes: dict[str, str] = {}

    for split in SPLITS:
        image_dir = merged_root / split / "images"
        label_dir = merged_root / split / "labels"
        images = list_images(image_dir)
        labels = sorted(label_dir.glob("*.txt"))
        split_counts[split] = {"images": len(images), "labels": len(labels)}
        label_stems = {label.stem for label in labels}
        for image_path in images:
            image = cv2.imread(str(image_path))
            if image is None:
                issues.append({"severity": "error", "code": "CORRUPT_IMAGE", "message": str(image_path)})
            digest = sha256_file(image_path)
            if digest in hashes:
                issues.append({"severity": "error", "code": "DUPLICATE_IMAGE", "message": f"{image_path} duplicates {hashes[digest]}"})
            hashes[digest] = str(image_path)
            label_path = label_dir / f"{image_path.stem}.txt"
            if image_path.stem not in label_stems:
                issues.append({"severity": "error", "code": "MISSING_LABEL", "message": str(image_path)})
                continue
            label_lines = label_path.read_text(encoding="utf-8").splitlines()
            if label_lines:
                positive_images += 1
            else:
                negative_images += 1
            for line_index, line in enumerate(label_lines, start=1):
                parts = line.split()
                if len(parts) != 5 or parts[0] != "0":
                    issues.append({"severity": "error", "code": "INVALID_LABEL_FORMAT", "message": f"{label_path}:{line_index}"})
                    continue
                values = [float(value) for value in parts[1:]]
                if not all(0.0 <= value <= 1.0 for value in values) or values[2] <= 0.0 or values[3] <= 0.0:
                    issues.append({"severity": "error", "code": "INVALID_LABEL_GEOMETRY", "message": f"{label_path}:{line_index}"})
                    continue
                annotation_count += 1

    if positive_images == 0:
        issues.append({"severity": "error", "code": "NO_POSITIVES", "message": "No positive pothole images were merged"})
    if negative_images == 0:
        issues.append({"severity": "error", "code": "NO_NEGATIVES", "message": "No negative road-context images were merged"})

    return {
        "path": str(merged_root),
        "passed": not any(issue["severity"] == "error" for issue in issues),
        "split_counts": split_counts,
        "positive_images": positive_images,
        "negative_images": negative_images,
        "annotation_count": annotation_count,
        "issues": issues[:500],
    }


def write_civiceye_manifest(
    merged_root: Path,
    telemetry: list[DatasetTelemetry],
    merged_report: dict[str, Any],
) -> Path:
    items: list[dict[str, Any]] = []
    for split in SPLITS:
        for image_path in list_images(merged_root / split / "images"):
            label_path = merged_root / split / "labels" / f"{image_path.stem}.txt"
            label_lines = label_path.read_text(encoding="utf-8").splitlines() if label_path.exists() else []
            items.append(
                {
                    "image_id": image_path.stem,
                    "image_path": str(image_path.relative_to(merged_root)).replace("\\", "/"),
                    "label_path": str(label_path.relative_to(merged_root)).replace("\\", "/"),
                    "split": split,
                    "has_pothole": bool(label_lines),
                    "annotation_count": len(label_lines),
                    "sha256": sha256_file(image_path),
                }
            )
    manifest = {
        "dataset_id": "civiceye-pothole-combined",
        "created_at": datetime.now(UTC).isoformat(),
        "description": "Merged Roboflow pothole positives with road-context negatives for CivicEye YOLOv8 training.",
        "class_names": {0: "pothole"},
        "items": items,
        "source_telemetry": [record.to_dict() for record in telemetry],
        "validation": merged_report,
    }
    output_path = merged_root / "civiceye_manifest.json"
    write_json(output_path, manifest)
    return output_path


def write_data_yaml(merged_root: Path) -> None:
    payload = {
        "path": str(merged_root.resolve()),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "names": {0: "pothole"},
    }
    with (merged_root / "data.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def launch_training(paths: PipelinePaths) -> None:
    try:
        import torch
        from ultralytics import YOLO
    except ImportError as error:
        raise SystemExit(
            "Training dependencies are missing. Install them with "
            f"'{sys.executable} -m pip install -r {paths.ai_root / 'requirements.txt'}'. "
            "No training was launched."
        ) from error

    device = "0" if torch.cuda.is_available() else "cpu"
    batch: int | str = -1 if torch.cuda.is_available() else 4
    amp = bool(torch.cuda.is_available())
    run_name = f"pothole_combined_yolov8n_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    logging.info("Launching YOLOv8 training: device=%s batch=%s amp=%s", device, batch, amp)
    model = YOLO("yolov8n.pt")
    results = model.train(
        data=str(paths.merged_root / "data.yaml"),
        imgsz=640,
        epochs=50,
        batch=batch,
        device=device,
        amp=amp,
        workers=8,
        optimizer="auto",
        patience=12,
        seed=RANDOM_SEED,
        project=str(paths.train_runs_root),
        name=run_name,
        exist_ok=True,
        plots=True,
        save=True,
        val=True,
    )
    metrics = getattr(results, "results_dict", {}) or {}
    write_json(paths.telemetry_root / "training_result.json", {"run_name": run_name, "device": device, "metrics": metrics})
    logging.info("Training completed with metrics: %s", metrics)


def find_data_yaml(dataset_dir: Path) -> Path | None:
    candidates = list(dataset_dir.rglob("data.yaml"))
    return candidates[0] if candidates else None


def find_split_dir(dataset_dir: Path, split: str, kind: str) -> Path | None:
    aliases = [split]
    if split == "valid":
        aliases.append("val")
    for alias in aliases:
        candidates = [
            dataset_dir / alias / kind,
            dataset_dir / kind / alias,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
    matches = [path for path in dataset_dir.rglob(kind) if path.parent.name.lower() in aliases]
    return matches[0] if matches else None


def list_images(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        return []
    return sorted(path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
