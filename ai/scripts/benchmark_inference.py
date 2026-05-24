from __future__ import annotations

import argparse
from pathlib import Path

from ai.evaluation.evaluate_yolov8 import benchmark_inference


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark CivicEye YOLOv8 inference latency.")
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("benchmarks/inference"), type=Path)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--iterations", default=25, type=int)
    args = parser.parse_args()
    print(benchmark_inference(args.weights, args.source, args.output_dir, args.device, args.iterations))


if __name__ == "__main__":
    main()
