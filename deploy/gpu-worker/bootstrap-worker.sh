#!/usr/bin/env sh
set -eu

python3 - <<'PY'
from backend.gpu.device import get_device_info
device = get_device_info()
if not device.cuda_available:
    raise SystemExit("CUDA is not available. Verify NVIDIA driver, container runtime, and GPU allocation.")
print({"device": device.device, "gpu_name": device.gpu_name, "vram_total_mb": device.vram_total_mb})
PY

python3 -m backend.distributed.worker
