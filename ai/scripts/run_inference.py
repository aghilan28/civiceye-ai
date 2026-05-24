from __future__ import annotations

import argparse
from pathlib import Path

from ai.inference.predictor import CivicEyeYOLOPredictor
from ai.utils.io import write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Run normalized CivicEye YOLOv8 inference.")
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--confidence", default=0.25, type=float)
    parser.add_argument("--iou", default=0.5, type=float)
    parser.add_argument("--output", default=Path("reports/inference/predictions.json"), type=Path)
    args = parser.parse_args()

    predictor = CivicEyeYOLOPredictor(args.weights, args.model_version, args.device, args.confidence, args.iou)
    results = [result.to_dict() for result in predictor.predict(args.source)]
    write_json(args.output, {"predictions": results})
    print(f"Wrote {len(results)} inference result(s) to {args.output}")


if __name__ == "__main__":
    main()
