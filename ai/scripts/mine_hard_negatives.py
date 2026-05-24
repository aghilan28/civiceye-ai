from __future__ import annotations

import argparse
from pathlib import Path

from ai.evaluation.evaluate_yolov8 import extract_hard_negatives


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract confidence-ranked hard negatives for retraining.")
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--images-dir", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("reports/hard_negatives"), type=Path)
    parser.add_argument("--confidence", default=0.25, type=float)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    print(extract_hard_negatives(args.weights, args.images_dir, args.output_dir, args.confidence, args.device))


if __name__ == "__main__":
    main()
