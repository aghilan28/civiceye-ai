from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceInfo:
    device: str
    cuda_available: bool
    gpu_name: str | None
    half_precision: bool
    vram_used_mb: float | None
    vram_total_mb: float | None


def get_device_info() -> DeviceInfo:
    try:
        import torch
    except Exception:
        return DeviceInfo("cpu", False, None, False, None, None)

    if not torch.cuda.is_available():
        return DeviceInfo("cpu", False, None, False, None, None)

    index = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(index)
    used = torch.cuda.memory_allocated(index) / (1024 * 1024)
    total = props.total_memory / (1024 * 1024)
    return DeviceInfo(
        device=f"cuda:{index}",
        cuda_available=True,
        gpu_name=props.name,
        half_precision=True,
        vram_used_mb=round(used, 2),
        vram_total_mb=round(total, 2),
    )

