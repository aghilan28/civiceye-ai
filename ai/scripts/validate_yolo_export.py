from __future__ import annotations

import argparse
from pathlib import Path

from ai.utils.io import read_yaml, write_json


def validate_yolo_export(export_dir: Path, output: Path) -> dict[str, object]:
    data_yaml = export_dir / "data.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(f"Missing YOLO data.yaml: {data_yaml}")
    data = read_yaml(data_yaml)
    issues: list[dict[str, str]] = []
    counts: dict[str, dict[str, int]] = {}
    for split in ("train", "val", "test"):
        image_dir = export_dir / "images" / split
        label_dir = export_dir / "labels" / split
        images = sorted(path for path in image_dir.glob("*") if path.is_file()) if image_dir.exists() else []
        labels = sorted(path for path in label_dir.glob("*.txt")) if label_dir.exists() else []
        counts[split] = {"images": len(images), "labels": len(labels)}
        if not image_dir.exists():
            issues.append({"severity": "error", "code": "MISSING_IMAGE_DIR", "message": str(image_dir)})
        if not label_dir.exists():
            issues.append({"severity": "error", "code": "MISSING_LABEL_DIR", "message": str(label_dir)})
        label_stems = {path.stem for path in labels}
        for image in images:
            if image.stem not in label_stems:
                issues.append({"severity": "warning", "code": "IMAGE_WITHOUT_LABEL", "message": str(image)})
        for label in labels:
            for line_number, line in enumerate(label.read_text(encoding="utf-8").splitlines(), start=1):
                parts = line.split()
                if len(parts) != 5:
                    issues.append({"severity": "error", "code": "BAD_LABEL_LINE", "message": f"{label}:{line_number}"})
                    continue
                values = [float(value) for value in parts[1:]]
                if not all(0.0 <= value <= 1.0 for value in values) or values[2] <= 0 or values[3] <= 0:
                    issues.append({"severity": "error", "code": "INVALID_LABEL_GEOMETRY", "message": f"{label}:{line_number}"})
    report = {
        "export_dir": str(export_dir),
        "data_yaml": data,
        "counts": counts,
        "passed": not any(issue["severity"] == "error" for issue in issues),
        "issues": issues,
    }
    write_json(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a YOLO export before training.")
    parser.add_argument("--export-dir", required=True, type=Path)
    parser.add_argument("--output", default=Path("telemetry/validation/yolo_export_report.json"), type=Path)
    args = parser.parse_args()
    report = validate_yolo_export(args.export_dir, args.output)
    if not report["passed"]:
        raise SystemExit(f"YOLO export validation failed. Report written to {args.output}")
    print(f"YOLO export validation passed. Report written to {args.output}")


if __name__ == "__main__":
    main()
