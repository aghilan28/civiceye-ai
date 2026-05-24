# CivicEye Phase B: YOLOv8 Pothole Detection Training System

Phase B turns the AI workspace into a real model-training and evaluation system for the first CivicEye detector: pothole detection. The pipeline is intentionally single-detector today, but the configuration and package boundaries are class-agnostic so future road cracks, drainage, garbage, water leakage, and ensemble work can reuse the same training shape.

## Architecture

- `training/config.py` loads reproducible YAML experiment configs and validates model, device, tracking, evaluation, and export settings.
- `trainers/yolov8_pothole_trainer.py` owns the Ultralytics YOLOv8 training lifecycle.
- `training/gpu.py` detects CUDA, records VRAM, scales batch size when available memory is below policy, and falls back to CPU when allowed.
- `training/checkpoints.py` captures `best.pt`, `last.pt`, export-ready weights, and checkpoint lineage.
- `training/tracking.py` logs params, metrics, artifacts, and failure state to MLflow and optionally W&B.
- `evaluation/evaluate_yolov8.py` runs validation, hard-negative extraction, and inference benchmarks.
- `inference/predictor.py` returns production-normalized detections with confidence, severity, normalized coordinates, model version, and telemetry.
- `exports/export_model.py` exports deployment artifacts including ONNX and TorchScript.

## Training

Prepare a YOLO dataset export first:

```powershell
cd ai
py -3.12 -m ai.scripts.export_yolo --version v0.1.0 --manifest datasets/manifests/pothole_v0.1.0.json --output-root exports
```

Run the baseline:

```powershell
cd ..
py -3.12 -m ai.training.train_yolov8 --config ai/configs/training/pothole_yolov8n.yaml
```

Candidate configs are available for `yolov8n.pt`, `yolov8s.pt`, and `yolov8m.pt`. Use `resume_checkpoint` to recover interrupted runs and `pretrained_weights` to start from a prior CivicEye checkpoint.

## GPU Optimization

The trainer uses automatic device selection when `device: auto` is set. CUDA runs enable mixed precision when configured; CPU fallback disables AMP and scales overly large batch sizes down to a safe value. Every run writes a device profile and GPU memory snapshots under `telemetry/training/<run_name>/`.

## Evaluation

Run validation against the YOLO split:

```powershell
cd ..
py -3.12 -m ai.scripts.evaluate_model --weights ai/checkpoints/pothole_yolov8n_baseline/yolov8n_v0.1.0_baseline/best.pt --data ai/exports/yolo/pothole_v0.1.0/data.yaml --output-dir ai/reports/evaluation/yolov8n_v0.1.0
```

The report includes mAP@50, mAP@50:95, precision, recall, false-positive rate, false-negative rate, thresholds, device metadata, and raw Ultralytics metrics. Ultralytics plots and JSON predictions are preserved in the validation output directory.

## Hard Negatives

Hard-negative mining ranks false-positive-prone samples such as puddles, road patches, shadows, oil stains, road markings, cracks, and debris. Filenames or folder names should include those category labels when possible.

```powershell
cd ..
py -3.12 -m ai.scripts.mine_hard_negatives --weights ai/checkpoints/pothole_yolov8n_baseline/yolov8n_v0.1.0_baseline/best.pt --images-dir ai/raw/hard_negatives --output-dir ai/reports/hard_negatives/yolov8n_v0.1.0
```

## Export

Export the best checkpoint:

```powershell
cd ..
py -3.12 -m ai.scripts.export_model --weights ai/checkpoints/pothole_yolov8n_baseline/yolov8n_v0.1.0_baseline/best.pt --output-dir ai/exports/models/pothole_yolov8n_v0.1.0 --formats onnx torchscript
```

The export manifest records source weights, image size, export flags, artifact paths, and TensorRT readiness. TensorRT engine export can be requested with `--formats engine` on a compatible NVIDIA environment.

## Inference

Run normalized inference:

```powershell
cd ..
py -3.12 -m ai.scripts.run_inference --weights ai/exports/models/pothole_yolov8n_v0.1.0/best.pt --source ai/processed/sample_images --model-version pothole_yolov8n_v0.1.0 --output ai/reports/inference/pothole_yolov8n_v0.1.0.json
```

Each detection includes `issue_type`, `confidence`, severity (`minor`, `moderate`, `severe`, `critical`), absolute and normalized coordinates, model version, inference latency, and telemetry metadata.

## Benchmarking

```powershell
cd ..
py -3.12 -m ai.scripts.benchmark_inference --weights ai/checkpoints/pothole_yolov8n_baseline/yolov8n_v0.1.0_baseline/best.pt --source ai/processed/sample_images --device auto --iterations 25
```

Run separate CPU, CUDA, ONNX Runtime, and TensorRT benchmarks before deployment. TensorRT measurements require an engine export on the target NVIDIA platform.

## Troubleshooting

- Missing `data.yaml`: run the YOLO dataset export before training.
- CUDA out of memory: reduce `batch_size`, lower `image_size`, or increase `device_config.min_free_vram_gb` so the scaler becomes more conservative.
- CPU fallback is slow: set `device: 0` to require CUDA and fail fast if the GPU is unavailable.
- No MLflow UI: start it from `ai` with `mlflow ui --backend-store-uri ./experiments/mlruns`.
- TensorRT export fails: verify NVIDIA driver, CUDA, TensorRT, and Ultralytics export support on the same machine.
