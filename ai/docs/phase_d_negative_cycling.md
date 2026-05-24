# CivicEye Phase D: Negative Cycling and Hard-Negative Training

Phase D teaches the pothole detector what normal roads look like. Negative datasets are used as context only; their labels are ignored for pothole training unless they are part of a curated positive pothole manifest.

## Negative Sources

Configured in `configs/dataset_sources_phase_d_negatives.yaml`:

- `autonomous-driving-wzdzy`: lane and traffic-light context, CC BY 4.0, Roboflow Universe.
- `autonomous-driving-40ukk`: road, lane, sidewalk, vehicle context, CC BY 4.0, Roboflow Universe.
- `bdd100k-e3s18`: BDD100K vehicle/driving context, CC BY 4.0, Roboflow Universe.
- `cityscapes-hgg49`: CityScapes instance segmentation context, CC BY 4.0, Roboflow Universe.
- `cityscapes-wqjba`: Cityscapes object detection context, CC BY 4.0, Roboflow Universe.
- `road-segmentation-olxqu`: road segmentation context including road, shallow, puddle-adjacent, and urban surfaces, CC BY 4.0, Roboflow Universe.

Roboflow Universe pages are public, but dataset export download requires `ROBOFLOW_API_KEY`.

## Download Access

Set the API key before running Phase D:

```powershell
$env:ROBOFLOW_API_KEY = "<your-api-key>"
```

Run:

```powershell
py -3.12 -m ai.scripts.run_phase_d --version v0.3.0
```

If no key is present, the pipeline writes an access-blocker report instead of pretending data was downloaded.

## Negative Filtering

The filter in `datasets/negative_filter.py` scores each candidate image using:

- road/asphalt dominance in the lower frame
- lane/reflection visibility
- surface texture density
- object/clutter penalty
- hard-negative keyword tags such as puddle, shadow, patch, wet, reflection, oil, lane, manhole, drain, and asphalt
- minimum resolution checks

Accepted images become negative examples with empty YOLO label files. Existing non-pothole labels from driving datasets are deliberately ignored to avoid class-schema corruption.

## Fusion

Fuse positives and road-context negatives:

```powershell
py -3.12 -m ai.scripts.fuse_negative_dataset --positive-manifest ai/datasets/manifests/pothole_real_v0.2.0.json --negative-manifest ai/datasets/manifests/negative_road_context_v0.3.0.json --output-manifest ai/datasets/manifests/pothole_negative_aware_v0.3.0.json --version v0.3.0
```

The fusion system:

- keeps pothole-positive annotations
- forces negatives to empty annotation lists
- deduplicates by perceptual hash
- balances negatives across sources
- writes `telemetry/fusion/<version>_fusion_report.json`

## Training

After fused validation passes:

```powershell
py -3.12 -m ai.training.train_yolov8 --config ai/configs/training/pothole_yolov8n_phase_d.yaml
```

Training uses the Phase B trainer: CUDA detection, AMP, VRAM-aware batch scaling, checkpoint lineage, MLflow/W&B tracking, and failure recovery.

## Evaluation

```powershell
py -3.12 -m ai.scripts.evaluate_model --weights ai/checkpoints/pothole_yolov8n_phase_d_negative_aware/yolov8n_v0.3.0_negative_aware/best.pt --data ai/exports/yolo/pothole_v0.3.0/data.yaml --output-dir ai/reports/evaluation/yolov8n_v0.3.0_negative_aware
```

Primary deployment metrics:

- mAP@50 and mAP@50:95
- precision, recall, F1
- false-positive and false-negative rates
- inference latency and throughput
- failure categories for puddles, shadows, asphalt patches, wet roads, reflections, and lane markings

## Export

```powershell
py -3.12 -m ai.scripts.export_model --weights ai/checkpoints/pothole_yolov8n_phase_d_negative_aware/yolov8n_v0.3.0_negative_aware/best.pt --output-dir ai/exports/models/pothole_yolov8n_v0.3.0_negative_aware --formats onnx torchscript
```

TensorRT engine export should be run on the deployment NVIDIA machine:

```powershell
py -3.12 -m ai.scripts.export_model --weights ai/checkpoints/pothole_yolov8n_phase_d_negative_aware/yolov8n_v0.3.0_negative_aware/best.pt --output-dir ai/exports/models/pothole_yolov8n_v0.3.0_tensorrt --formats engine --device 0
```

## Current Execution Status

The local Phase D run produced:

- `reports/phase_d/v0.3.0_execution_report.json`
- `telemetry/ingestion/v0.3.0_negatives_ingestion_report.json`

It did not download Roboflow data because `ROBOFLOW_API_KEY` was not set. No model weights or metrics were fabricated.
