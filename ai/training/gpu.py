from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter

from ai.training.config import DeviceConfig


BYTES_PER_GB = 1024**3


@dataclass(frozen=True)
class DeviceProfile:
    requested: str
    selected: str
    cuda_available: bool
    device_name: str
    total_vram_gb: float
    free_vram_gb: float
    reserved_vram_gb: float
    allocated_vram_gb: float
    mixed_precision_enabled: bool
    batch_size: int
    batch_scaled: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def resolve_device(config: DeviceConfig, requested_batch_size: int) -> DeviceProfile:
    requested = config.device
    if requested == "cpu":
        return DeviceProfile(
            requested=requested,
            selected="cpu",
            cuda_available=False,
            device_name="cpu",
            total_vram_gb=0.0,
            free_vram_gb=0.0,
            reserved_vram_gb=0.0,
            allocated_vram_gb=0.0,
            mixed_precision_enabled=False,
            batch_size=max(1, min(requested_batch_size, 4)),
            batch_scaled=requested_batch_size > 4,
        )

    torch = _torch()
    cuda_available = torch.cuda.is_available()
    selected = requested
    batch_size = requested_batch_size
    batch_scaled = False

    if requested == "auto":
        selected = "0" if cuda_available else "cpu"
    if selected != "cpu" and not cuda_available:
        if not config.allow_cpu_fallback:
            raise RuntimeError("CUDA was requested but no CUDA device is available")
        selected = "cpu"

    if selected == "cpu":
        return DeviceProfile(
            requested=requested,
            selected="cpu",
            cuda_available=cuda_available,
            device_name="cpu",
            total_vram_gb=0.0,
            free_vram_gb=0.0,
            reserved_vram_gb=0.0,
            allocated_vram_gb=0.0,
            mixed_precision_enabled=False,
            batch_size=max(1, min(requested_batch_size, 4)),
            batch_scaled=requested_batch_size > 4,
        )

    device_index = int(str(selected).split(",")[0])
    torch.cuda.set_device(device_index)
    free_bytes, total_bytes = torch.cuda.mem_get_info(device_index)
    allocated = torch.cuda.memory_allocated(device_index)
    reserved = torch.cuda.memory_reserved(device_index)
    free_gb = free_bytes / BYTES_PER_GB
    total_gb = total_bytes / BYTES_PER_GB

    if free_gb < config.min_free_vram_gb:
        scaled = max(1, int(requested_batch_size * config.batch_scale_safety * max(free_gb, 0.5) / config.min_free_vram_gb))
        batch_scaled = scaled < requested_batch_size
        batch_size = scaled

    return DeviceProfile(
        requested=requested,
        selected=selected,
        cuda_available=cuda_available,
        device_name=torch.cuda.get_device_name(device_index),
        total_vram_gb=round(total_gb, 3),
        free_vram_gb=round(free_gb, 3),
        reserved_vram_gb=round(reserved / BYTES_PER_GB, 3),
        allocated_vram_gb=round(allocated / BYTES_PER_GB, 3),
        mixed_precision_enabled=config.mixed_precision,
        batch_size=batch_size,
        batch_scaled=batch_scaled,
    )


def snapshot_gpu_memory(device: str) -> dict[str, float | str | bool]:
    torch = _torch()
    if device == "cpu" or not torch.cuda.is_available():
        return {"device": "cpu", "cuda_available": torch.cuda.is_available()}
    index = int(str(device).split(",")[0])
    free_bytes, total_bytes = torch.cuda.mem_get_info(index)
    return {
        "device": str(device),
        "cuda_available": True,
        "free_vram_gb": round(free_bytes / BYTES_PER_GB, 3),
        "total_vram_gb": round(total_bytes / BYTES_PER_GB, 3),
        "allocated_vram_gb": round(torch.cuda.memory_allocated(index) / BYTES_PER_GB, 3),
        "reserved_vram_gb": round(torch.cuda.memory_reserved(index) / BYTES_PER_GB, 3),
        "max_allocated_vram_gb": round(torch.cuda.max_memory_allocated(index) / BYTES_PER_GB, 3),
    }


class TimedStage:
    def __enter__(self) -> "TimedStage":
        self.started_at = perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        self.finished_at = perf_counter()
        self.elapsed_seconds = self.finished_at - self.started_at


def _torch():
    try:
        import torch
    except ImportError as error:
        raise RuntimeError(
            "PyTorch is required for GPU profiling and YOLOv8 training. "
            "Install the CUDA or CPU build that matches your deployment target."
        ) from error
    return torch
