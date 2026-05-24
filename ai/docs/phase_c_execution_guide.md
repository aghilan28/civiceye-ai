# CivicEye Phase C: Real Dataset Execution and Training Guide

Phase C executes the real pothole model pipeline. It does not fabricate images, labels, checkpoints, or metrics. If a dataset quality gate fails, training is skipped unless an engineer explicitly runs with `--allow-quality-fail`.

## Real Dataset Imported

The default Phase C source is configured in `configs/dataset_sources_phase_c.yaml`:

- Source: `jaygala24_ivcnz_pothole_yolo`
- Format: YOLO
- License: MIT
- URL: `https://github.com/jaygala24/pothole-detection/releases/download/v1.0.0/Pothole.Dataset.IVCNZ.zip`

Execution output for `v0.2.0`:

- Canonical manifest: `datasets/manifests/pothole_real_v0.2.0.json`
- Ingestion report: `telemetry/ingestion/v0.2.0_ingestion_report.json`
- Validation report: `telemetry/validation/pothole_real_v0.2.0_report.json`
- Split manifest: `versions/v0.2.0/manifest.json`
- YOLO export: `exports/yolo/pothole_v0.2.0`
- YOLO export validation: `telemetry/validation/pothole_v0.2.0_yolo_export_report.json`
- Phase C execution report: `reports/phase_c/v0.2.0_execution_report.json`

## Current Quality Gate

The imported public dataset contains real pothole images and annotations, but no negative road images. CivicEye blocks production training by default because the detector still needs explicit examples of clean roads, shadows, puddles, oil stains, lane markings, asphalt patches, and debris.

The current validated export is useful for a real positive-corpus baseline, but not yet a production-ready false-positive detector.

## Execute Phase C

From the repository root:

```powershell
py -3.12 -m ai.scripts.run_phase_c --version v0.2.0
```

This executes ingestion, validation, split generation, YOLO export, YOLO export validation, and the training gate.

To force a baseline training run on the positive-only corpus:

```powershell
py -3.12 -m ai.scripts.run_phase_c --version v0.2.0 --train --allow-quality-fail
```

Use the forced mode only for research baselines. Do not promote that checkpoint to production without adding negative road images and rerunning validation.

## Add Negative Samples

Place curated negative images here:

```text
ai/raw/local_negative_roads/
```

Recommended folders:

```text
clean_roads/
shadows/
puddles/
oil_stains/
lane_markings/
asphalt_patches/
debris/
night_roads/
rain_roads/
motion_blur/
```

Then run with `configs/dataset_sources_local_phase_c.yaml` or add the negative source to `configs/dataset_sources_phase_c.yaml`.

## Train

Install the full training stack in the target environment:

```powershell
cd ai
pip install -r requirements.txt
```

Train the Phase C YOLOv8n detector:

```powershell
cd ..
py -3.12 -m ai.training.train_yolov8 --config ai/configs/training/pothole_yolov8n_phase_c.yaml
```

The training system automatically selects CUDA when available, logs GPU memory, enables AMP on CUDA, scales batch size under low VRAM, writes checkpoint lineage, and logs metrics/artifacts to MLflow.

## Evaluate

```powershell
py -3.12 -m ai.scripts.evaluate_model --weights ai/checkpoints/pothole_yolov8n_phase_c/yolov8n_v0.2.0_phase_c/best.pt --data ai/exports/yolo/pothole_v0.2.0/data.yaml --output-dir ai/reports/evaluation/yolov8n_v0.2.0_phase_c
```

Evaluation records mAP@50, mAP@50:95, precision, recall, F1, false-positive rate, false-negative rate, latency, raw Ultralytics metrics, and validation artifacts.

## Hard-Negative Mining

```powershell
py -3.12 -m ai.scripts.mine_hard_negatives --weights ai/checkpoints/pothole_yolov8n_phase_c/yolov8n_v0.2.0_phase_c/best.pt --images-dir ai/raw/local_negative_roads --output-dir ai/reports/hard_negatives/yolov8n_v0.2.0_phase_c
```

The report ranks false-positive-prone categories and produces retraining priorities.

## Export and Validate Deployment Artifacts

```powershell
py -3.12 -m ai.scripts.export_model --weights ai/checkpoints/pothole_yolov8n_phase_c/yolov8n_v0.2.0_phase_c/best.pt --output-dir ai/exports/models/pothole_yolov8n_v0.2.0 --formats onnx torchscript
```

Use TensorRT engine export only on a compatible NVIDIA deployment machine:

```powershell
py -3.12 -m ai.scripts.export_model --weights ai/checkpoints/pothole_yolov8n_phase_c/yolov8n_v0.2.0_phase_c/best.pt --output-dir ai/exports/models/pothole_yolov8n_v0.2.0_trt --formats engine --device 0
```

## Benchmark

```powershell
py -3.12 -m ai.scripts.benchmark_inference --weights ai/checkpoints/pothole_yolov8n_phase_c/yolov8n_v0.2.0_phase_c/best.pt --source ai/exports/yolo/pothole_v0.2.0/images/test --device auto --iterations 25
```

Benchmark CPU, CUDA, ONNX Runtime, TorchScript, and TensorRT separately before deployment.

## Compare Models

```powershell
py -3.12 -m ai.scripts.compare_models --reports ai/reports/evaluation/yolov8n_v0.2.0_phase_c/evaluation_report.json ai/reports/evaluation/yolov8s_v0.2.0_phase_c/evaluation_report.json --output ai/reports/model_comparison/v0.2.0.json
```
