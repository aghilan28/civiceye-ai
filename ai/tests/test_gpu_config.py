from __future__ import annotations

from ai.training.config import DeviceConfig
from ai.training.gpu import resolve_device


def test_cpu_fallback_scales_large_batch() -> None:
    profile = resolve_device(DeviceConfig(device="cpu", mixed_precision=True), requested_batch_size=16)

    assert profile.selected == "cpu"
    assert profile.mixed_precision_enabled is False
    assert profile.batch_size == 4
    assert profile.batch_scaled is True
