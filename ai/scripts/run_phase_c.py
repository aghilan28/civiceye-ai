from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from ai.utils.io import read_json, write_json


def run_phase_c(args: argparse.Namespace) -> Path:
    ai_root = Path(args.ai_root).resolve()
    version = args.version
    manifest = ai_root / "datasets" / "manifests" / f"pothole_real_{version}.json"
    split_manifest = ai_root / "versions" / version / "manifest.json"
    yolo_export = ai_root / "exports" / "yolo" / f"pothole_{version}"
    execution_report = ai_root / "reports" / "phase_c" / f"{version}_execution_report.json"
    execution_report.parent.mkdir(parents=True, exist_ok=True)

    steps: list[dict[str, object]] = []
    _run_step(
        steps,
        "ingest",
        [
            sys.executable,
            "-m",
            "ai.scripts.ingest_dataset",
            "--sources-config",
            str(ai_root / "configs" / args.sources_config),
            "--dataset-id",
            "civiceye-pothole-real",
            "--version",
            version,
            "--raw-root",
            str(ai_root / "raw"),
            "--output-manifest",
            str(manifest),
            "--download",
        ],
        cwd=ai_root.parent,
    )
    validation_report = ai_root / "telemetry" / "validation" / f"pothole_real_{version}_report.json"
    _run_step(
        steps,
        "validate_manifest",
        [
            sys.executable,
            "-m",
            "ai.scripts.validate_dataset",
            "--manifest",
            str(manifest),
            "--output",
            str(validation_report),
        ],
        cwd=ai_root.parent,
        allow_failure=True,
    )
    validation_payload = read_json(validation_report) if validation_report.exists() else {}
    production_gate_passed = bool(validation_payload.get("passed", False))

    _run_step(
        steps,
        "create_splits",
        [
            sys.executable,
            "-m",
            "ai.scripts.create_splits",
            "--manifest",
            "datasets/manifests/" + manifest.name,
            "--config",
            "configs/splits/pothole_70_20_10.yaml",
            "--version",
            version,
            "--output-dir",
            "versions",
        ],
        cwd=ai_root,
        env_pythonpath=str(ai_root.parent),
    )
    _run_step(
        steps,
        "export_yolo",
        [
            sys.executable,
            "-m",
            "ai.scripts.export_yolo",
            "--version",
            version,
            "--manifest",
            "versions/" + version + "/manifest.json",
            "--output-root",
            "exports",
        ],
        cwd=ai_root,
        env_pythonpath=str(ai_root.parent),
    )
    yolo_validation = ai_root / "telemetry" / "validation" / f"pothole_{version}_yolo_export_report.json"
    _run_step(
        steps,
        "validate_yolo_export",
        [
            sys.executable,
            "-m",
            "ai.scripts.validate_yolo_export",
            "--export-dir",
            str(yolo_export),
            "--output",
            str(yolo_validation),
        ],
        cwd=ai_root.parent,
    )

    can_train = production_gate_passed or args.allow_quality_fail
    if can_train and args.train:
        _run_step(
            steps,
            "train",
            [
                sys.executable,
                "-m",
                "ai.training.train_yolov8",
                "--config",
                str(ai_root / "configs" / "training" / args.training_config),
            ],
            cwd=ai_root.parent,
            allow_failure=True,
        )
    else:
        steps.append(
            {
                "name": "train",
                "status": "skipped",
                "reason": "quality_gate_failed" if not production_gate_passed else "train flag was not set",
            }
        )

    report = {
        "version": version,
        "manifest": str(manifest),
        "split_manifest": str(split_manifest),
        "yolo_export": str(yolo_export),
        "production_quality_gate_passed": production_gate_passed,
        "training_requested": bool(args.train),
        "ultralytics_available": shutil.which("yolo") is not None,
        "steps": steps,
    }
    write_json(execution_report, report)
    return execution_report


def _run_step(
    steps: list[dict[str, object]],
    name: str,
    command: list[str],
    cwd: Path,
    allow_failure: bool = False,
    env_pythonpath: str | None = None,
) -> None:
    env = None
    if env_pythonpath:
        import os

        env = os.environ.copy()
        env["PYTHONPATH"] = env_pythonpath
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    step = {
        "name": name,
        "command": command,
        "cwd": str(cwd),
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "status": "passed" if result.returncode == 0 else "failed",
    }
    steps.append(step)
    if result.returncode != 0 and not allow_failure:
        raise RuntimeError(f"Phase C step failed: {name}\n{result.stderr}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute the real CivicEye Phase C dataset/training pipeline.")
    parser.add_argument("--ai-root", default="ai")
    parser.add_argument("--version", default="v0.2.0")
    parser.add_argument("--sources-config", default="dataset_sources_phase_c.yaml")
    parser.add_argument("--training-config", default="pothole_yolov8n_phase_c.yaml")
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--allow-quality-fail", action="store_true")
    args = parser.parse_args()
    print(f"Phase C execution report written to {run_phase_c(args)}")


if __name__ == "__main__":
    main()
