from __future__ import annotations

import threading
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from backend.config import settings
from backend.gpu.device import DeviceInfo, get_device_info


class ModelLoader:
    _instance: "ModelLoader | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "ModelLoader":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._model: Any | None = None
        self._load_lock = threading.Lock()
        self.weights_path = settings.resolved_weights_path
        self.device_info: DeviceInfo = get_device_info()
        self.model_version = settings.model_version
        self._initialized = True

    @property
    def loaded(self) -> bool:
        return self._model is not None

    @property
    def model(self) -> Any:
        if self._model is None:
            self.load()
        if self._model is None:
            raise RuntimeError("YOLO model failed to load")
        return self._model

    def load(self) -> Any:
        with self._load_lock:
            if self._model is not None:
                return self._model
            if not self.weights_path.exists():
                raise FileNotFoundError(
                    f"CivicEye YOLO weights were not found at {self.weights_path}. "
                    "Set CIVICEYE_MODEL_WEIGHTS to the trained best.pt path."
                )
            from ultralytics import YOLO

            self._model = YOLO(str(self.weights_path))
            if self.device_info.cuda_available:
                self._model.to(self.device_info.device)
            self.warmup()
            return self._model

    def warmup(self) -> float:
        image = np.zeros((settings.image_size, settings.image_size, 3), dtype=np.uint8)
        started = perf_counter()
        self._model.predict(
            image,
            conf=settings.confidence_threshold,
            iou=settings.iou_threshold,
            imgsz=settings.image_size,
            device=self.device_info.device,
            half=self.device_info.half_precision,
            verbose=False,
        )
        return round((perf_counter() - started) * 1000, 3)

    def metadata(self) -> dict[str, str | bool | float | None]:
        self.device_info = get_device_info()
        return {
            "model_version": self.model_version,
            "weights_path": str(Path(self.weights_path)),
            "loaded": self.loaded,
            "device": self.device_info.device,
            "cuda_available": self.device_info.cuda_available,
            "gpu_name": self.device_info.gpu_name,
            "half_precision": self.device_info.half_precision,
            "vram_used_mb": self.device_info.vram_used_mb,
            "vram_total_mb": self.device_info.vram_total_mb,
        }


model_loader = ModelLoader()

