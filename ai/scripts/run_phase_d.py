from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from ai.utils.io import read_json, write_json


def run_phase_d(args: argparse.Namespace) -> Path:
    ai_root = Path(args.ai_root).resolve()
    version = args.version
    negative_version = f"{version}_negatives"
    positive_manifest = ai_root / args.positive_manifest
    negative_manifest = ai_root / "datasets" / "manifests" / f"negative_road_context_{version}.json"
    fused_manifest = ai_root / "datasets" / "manifests" / f"pothole_negative_aware_{version}.json"
    split_manifest = ai_root / "versions" / version / "manifest.json"
    yolo_export = ai_root / "exports" / "yolo" / f"pothole_{version}"
    report_path = ai_root / "reports" / "phase_d" / f"{version}_execution_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    steps: list[dict[str, object]] = []

    _run_step(
        steps,
        "ingest_negative_sources",
        [
            sys.executable,
            "-m",
            "ai.scripts.ingest_dataset",
            "--sources-config",
            str(ai_root / "configs" / args.negative_sources_config),
            "--dataset-id",
            "civiceye-road-context-negatives",
            "--version",
            negative_version,
            "--raw-root",
            str(ai_root / "raw"),
            "--output-manifest",
            str(negative_manifest),
            "--download",
        ],
        cwd=ai_root.parent,
        allow_failure=True,
    )

    can_continue = negative_manifest.exists()
    if can_continue:
        _run_step(
            steps,
            "fuse_positive_negative",
            [
                sys.executable,
                "-m",
                "ai.scripts.fuse_negative_dataset",
                "--positive-manifest",
                str(positive_manifest),
                "--negative-manifest",
                str(negative_manifest),
                "--output-manifest",
                str(fused_manifest),
                "--version",
                version,
                "--max-negative-ratio",
                str(args.max_negative_ratio),
            ],
            cwd=ai_root.parent,
        )
        validation_report = ai_root / "telemetry" / "validation" / f"pothole_negative_aware_{version}_report.json"
        _run_step(
            steps,
            "validate_fused_manifest",
            [
                sys.executable,
                "-m",
                "ai.scripts.validate_dataset",
                "--manifest",
                str(fused_manifest),
                "--output",
                str(validation_report),
            ],
            cwd=ai_root.parent,
            allow_failure=True,
        )
        validation = read_json(validation_report) if validation_report.exists() else {}
        quality_gate_passed = bool(validation.get("passed", False))
        _run_step(
            steps,
            "create_splits",
            [
                sys.executable,
                "-m",
                "ai.scripts.create_splits",
                "--manifest",
                "datasets/manifests/" + fused_manifest.name,
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
                str(ai_root / "telemetry" / "validation" / f"pothole_{version}_yolo_export_report.json"),
            ],
            cwd=ai_root.parent,
        )
        if args.train and quality_gate_passed:
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
                    "reason": "train flag was not set" if not args.train else "quality gate failed",
                }
            )
    else:
        quality_gate_passed = False
        steps.append(
            {
                "name": "fuse_positive_negative",
                "status": "skipped",
                "reason": "negative manifest was not created; check Roboflow access and ROBOFLOW_API_KEY",
            }
        )

    report = {
        "version": version,
        "positive_manifest": str(positive_manifest),
        "negative_manifest": str(negative_manifest),
        "fused_manifest": str(fused_manifest),
        "split_manifest": str(split_manifest),
        "yolo_export": str(yolo_export),
        "roboflow_api_key_present": bool(os.environ.get("ROBOFLOW_API_KEY")),
        "quality_gate_passed": quality_gate_passed,
        "training_requested": bool(args.train),
        "steps": steps,
    }
    write_json(report_path, report)
    return report_path


def _run_step(
    steps: list[dict[str, object]],
    name: str,
    command: list[str],
    cwd: Path,
    allow_failure: bool = False,
    env_pythonpath: str | None = None,
) -> None:
    env = os.environ.copy()
    if env_pythonpath:
        env["PYTHONPATH"] = env_pythonpath
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    steps.append(
        {
            "name": name,
            "command": command,
            "cwd": str(cwd),
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
            "status": "passed" if result.returncode == 0 else "failed",
        }
    )
    if result.returncode != 0 and not allow_failure:
        raise RuntimeError(f"Phase D step failed: {name}\n{result.stderr}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute Phase D negative cycling and hard-negative training.")
    parser.add_argument("--ai-root", default="ai")
    parser.add_argument("--version", default="v0.3.0")
    parser.add_argument("--positive-manifest", default="datasets/manifests/pothole_real_v0.2.0.json")
    parser.add_argument("--negative-sources-config", default="dataset_sources_phase_d_negatives.yaml")
    parser.add_argument("--training-config", default="pothole_yolov8n_phase_d.yaml")
    parser.add_argument("--max-negative-ratio", default=1.25, type=float)
    parser.add_argument("--train", action="store_true")
    args = parser.parse_args()
    print(f"Phase D execution report written to {run_phase_d(args)}")


if __name__ == "__main__":
    main()
