# Training Guide

## Setup

```bash
cd ai
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Validate Dataset

```bash
python scripts/validate_dataset.py --manifest datasets/manifests/pothole_v0.1.0.json
```

## Create Splits

```bash
python scripts/create_splits.py --manifest datasets/manifests/pothole_v0.1.0.json --version v0.1.0
```

## Export YOLOv8 Format

```bash
python scripts/export_yolo.py --version v0.1.0
```

## Train

```bash
python training/train_yolov8.py --config configs/training/pothole_yolov8n.yaml
```

## Promotion Criteria

A model should not be promoted unless:

- validation mAP is stable
- false positives on negatives are reviewed
- rainy/low-light subset performance is measured
- manual QA confirms bounding boxes are operationally useful
- inference latency is compatible with the deployment target
