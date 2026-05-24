from __future__ import annotations

import argparse
from pathlib import Path

from ai.utils.io import read_json, write_json


def compare_models(evaluation_reports: list[Path], output: Path) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for report_path in evaluation_reports:
        report = read_json(report_path)
        metrics = report.get("metrics", {})
        weights = Path(str(report.get("weights", "")))
        model_size_mb = round(weights.stat().st_size / (1024 * 1024), 3) if weights.exists() else None
        rows.append(
            {
                "report": str(report_path),
                "weights": str(weights),
                "model_size_mb": model_size_mb,
                "map50": metrics.get("map50"),
                "map5095": metrics.get("map5095"),
                "precision": metrics.get("precision"),
                "recall": metrics.get("recall"),
                "f1_score": metrics.get("f1_score"),
                "latency_p50_ms": metrics.get("latency_p50_ms"),
                "throughput_fps": metrics.get("throughput_fps"),
            }
        )
    ranked = sorted(rows, key=lambda row: (row.get("map5095") is not None, row.get("map5095") or -1), reverse=True)
    report = {"models": ranked, "best_by_map5095": ranked[0] if ranked else None}
    write_json(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare CivicEye YOLO model evaluation reports.")
    parser.add_argument("--reports", nargs="+", required=True, type=Path)
    parser.add_argument("--output", default=Path("reports/model_comparison.json"), type=Path)
    args = parser.parse_args()
    print(compare_models(args.reports, args.output))


if __name__ == "__main__":
    main()
