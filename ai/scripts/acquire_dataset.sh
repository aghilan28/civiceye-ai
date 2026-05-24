#!/usr/bin/env bash
# CivicEye — Dataset Acquisition Launcher (bash)
# Usage:
#   export ROBOFLOW_API_KEY="your_key_here"
#   bash ai/scripts/acquire_dataset.sh
#
# Or inline:
#   ROBOFLOW_API_KEY="your_key_here" bash ai/scripts/acquire_dataset.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RF_WORKSPACE="${RF_WORKSPACE:-smartathon}"
RF_PROJECT="${RF_PROJECT:-new-pothole-detection}"
SKIP_INSTALL="${SKIP_INSTALL:-0}"

echo "═══════════════════════════════════════════════════════════"
echo "  CivicEye — Roboflow Dataset Acquisition"
echo "═══════════════════════════════════════════════════════════"
echo "  Root     : $PROJECT_ROOT"
echo "  Workspace: $RF_WORKSPACE"
echo "  Project  : $RF_PROJECT"
echo ""

# ── Validate API key ──────────────────────────────────────────────────────────
if [[ -z "${ROBOFLOW_API_KEY:-}" ]]; then
    echo "❌  ROBOFLOW_API_KEY is not set."
    echo ""
    echo "   export ROBOFLOW_API_KEY='paste_your_key_here'"
    echo "   bash ai/scripts/acquire_dataset.sh"
    echo ""
    echo "   Get your key at: https://app.roboflow.com/ → Account → Roboflow API"
    exit 1
fi

# ── Install dependencies ──────────────────────────────────────────────────────
if [[ "$SKIP_INSTALL" != "1" ]]; then
    echo "[1/3] Installing Python dependencies …"
    REQ="$PROJECT_ROOT/ai/requirements-acquire.txt"
    if [[ -f "$REQ" ]]; then
        pip install -r "$REQ" -q
    else
        pip install roboflow pyyaml tqdm -q
    fi
    echo "      ✓ Dependencies ready"
fi

# ── Set environment ───────────────────────────────────────────────────────────
export RF_WORKSPACE
export RF_PROJECT
export CIVICEYE_ROOT="$PROJECT_ROOT"

# ── Run acquisition ───────────────────────────────────────────────────────────
echo "[2/3] Running dataset acquisition …"
python3 "$SCRIPT_DIR/download_roboflow_dataset.py"

# ── Done ──────────────────────────────────────────────────────────────────────
DATASET_PATH="$PROJECT_ROOT/ai/datasets/raw/pothole_dataset"
echo ""
echo "[3/3] Dataset acquisition complete!"
echo "      Path   : $DATASET_PATH"
echo "      Config : $DATASET_PATH/data.yaml"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Ready for YOLOv8 training:"
echo "  yolo detect train data=$DATASET_PATH/data.yaml \\"
echo "       model=yolov8n.pt epochs=50 imgsz=640"
echo "═══════════════════════════════════════════════════════════"
