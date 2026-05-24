# CivicEye AI Workspace

This directory is the computer-vision workspace for CivicEye. It is separated from the web application so dataset engineering, annotation quality, training, evaluation, export, and production inference can evolve as real ML systems.

Phase A created the dataset foundation. Phase B adds the first real detector:

- Pothole detection with YOLOv8
- Research-grade validation and hard-negative analysis
- GPU-aware training and checkpoint management
- Exportable deployment artifacts
- Normalized production inference outputs

The architecture is intentionally extensible for future smart-city classes such as garbage accumulation, drainage overflow, road cracks, broken streetlights, and water leakage.

## Directory Map

```text
ai/
  annotations/        Annotation standards and converted labels
  augmentation/       Field-condition augmentation configs and scripts
  benchmarks/         Inference and export performance reports
  checkpoints/        Captured best.pt, last.pt, and checkpoint lineage
  configs/            Dataset, training, augmentation, and environment configs
  datasets/           Dataset manifests and curated dataset roots
  docs/               Training, evaluation, export, and labeling documentation
  evaluation/         Validation, metrics, hard-negative, and visualization tools
  experiments/        Ultralytics and MLflow experiment outputs
  exports/            YOLO datasets and exported model artifacts
  inference/          Production inference adapters and normalization contracts
  logs/               Runtime logs
  metrics/            Aggregated model metric outputs
  models/             Model registry metadata
  notebooks/          Research notebooks only, never production pipeline logic
  processed/          Validated and normalized images/labels
  raw/                Immutable source drops from Roboflow, Kaggle, municipal, field capture
  reports/            Evaluation, hard-negative, benchmark, and inference reports
  scripts/            CLI pipeline entrypoints
  telemetry/          Dataset validation, training, and inference telemetry
  tests/              Pipeline integrity tests
  trainers/           Production trainer implementations
  training/           Training config, device, tracking, and checkpoint systems
  utils/              Shared Python utilities
  validation/         Dataset quality-control tooling
  versions/           Dataset version manifests
  visualizations/     Prediction overlays and inspection grids
```

## Phase B Entry Points

Train:

```powershell
py -3.12 -m ai.training.train_yolov8 --config ai/configs/training/pothole_yolov8n.yaml
```

Evaluate:

```powershell
py -3.12 -m ai.scripts.evaluate_model --weights <best.pt> --data <data.yaml>
```

Export model:

```powershell
py -3.12 -m ai.scripts.export_model --weights <best.pt> --formats onnx torchscript
```

Run inference:

```powershell
py -3.12 -m ai.scripts.run_inference --weights <best.pt> --source <image-or-dir> --model-version <version>
```

Benchmark:

```powershell
py -3.12 -m ai.scripts.benchmark_inference --weights <best.pt> --source <image-or-dir>
```

## Production Workflow

1. Register image sources in `configs/dataset_sources.yaml`.
2. Place raw dataset drops under `raw/<source_name>/`.
3. Convert annotations into the CivicEye canonical manifest.
4. Validate image integrity, annotation geometry, duplicates, and split leakage.
5. Generate reproducible train/validation/test splits.
6. Export a YOLOv8 dataset package.
7. Train with `training/train_yolov8.py`.
8. Evaluate mAP, precision, recall, false positives, false negatives, latency, and hard negatives.
9. Capture `best.pt`, `last.pt`, checkpoint lineage, telemetry, and MLflow artifacts.
10. Export ONNX, TorchScript, and TensorRT-ready artifacts.
11. Run normalized inference and deployment benchmarks.

## First Model

The first production model detects potholes only. Negative images are first-class citizens and should include clean roads, shadows, puddles, lane markings, oil stains, road patches, cracks, debris, and other road surfaces that are not potholes.

See `docs/phase_b_training_system.md` for the full training, evaluation, GPU, export, and troubleshooting guide.

Phase C real-data execution is documented in `docs/phase_c_execution_guide.md`.

Phase D negative cycling and hard-negative training is documented in `docs/phase_d_negative_cycling.md`.
