#!/usr/bin/env sh
set -eu

command -v nvidia-smi >/dev/null 2>&1 || {
  echo "nvidia-smi is not available. Install NVIDIA driver and NVIDIA Container Toolkit." >&2
  exit 1
}
nvidia-smi >/tmp/civiceye-nvidia-smi.txt

python3 - <<'PY'
from backend.gpu.device import get_device_info
from backend.config import settings
from backend.inference.model_loader import model_loader
from pathlib import Path
from urllib.request import urlopen
import os
device = get_device_info()
if not device.cuda_available:
    raise SystemExit("GPU validation failed: torch.cuda.is_available() returned false")
if not Path(settings.resolved_weights_path).exists():
    raise SystemExit(f"Model weights missing: {settings.resolved_weights_path}")
if not settings.worker_shared_secret or len(settings.worker_shared_secret) < 24:
    raise SystemExit("CIVICEYE_WORKER_SHARED_SECRET must be set to a high-entropy value")
metadata = model_loader.metadata()
if os.getenv("CIVICEYE_VALIDATE_MODEL_PRELOAD", "1") == "1":
    model_loader.load()
    metadata = model_loader.metadata()
backend_url = os.getenv("CIVICEYE_BACKEND_URL", "").rstrip("/")
if backend_url:
    with urlopen(f"{backend_url}/health", timeout=10) as response:
        if response.status >= 400:
            raise SystemExit(f"Backend health returned HTTP {response.status}")
print({
    "status": "ok",
    "device": device.device,
    "gpu_name": device.gpu_name,
    "vram_total_mb": device.vram_total_mb,
    "vram_used_mb": device.vram_used_mb,
    "model": str(settings.resolved_weights_path),
    "model_loaded": metadata.get("loaded"),
    "backend_checked": bool(backend_url),
})
PY
