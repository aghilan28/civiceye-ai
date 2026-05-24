from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

import cv2
import numpy as np

from backend.config import settings
from backend.gpu.device import get_device_info
from backend.inference.annotator import annotate_frame
from backend.inference.model_loader import model_loader
from backend.inference.severity import edge_sharpness, estimate_severity
from backend.models.schemas import BoundingBox, Detection, ImagePredictionResponse, InferenceTelemetry
from backend.telemetry.metrics import metrics_store


class InferenceEngine:
    def __init__(self) -> None:
        self.loader = model_loader

    def predict_frame(
        self,
        frame: np.ndarray,
        source_id: str,
        session_id: str,
        frame_index: int | None = None,
        gps: dict[str, float] | None = None,
    ) -> tuple[list[Detection], float]:
        height, width = frame.shape[:2]
        started = perf_counter()
        results = self.loader.model.predict(
            frame,
            conf=settings.confidence_threshold,
            iou=settings.iou_threshold,
            imgsz=settings.image_size,
            device=self.loader.device_info.device,
            half=self.loader.device_info.half_precision,
            verbose=False,
        )
        latency_ms = (perf_counter() - started) * 1000
        detections: list[Detection] = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
                confidence = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                x1i, y1i, x2i, y2i = int(x1), int(y1), int(x2), int(y2)
                box_width = max(0.0, x2 - x1)
                box_height = max(0.0, y2 - y1)
                area_ratio = (box_width * box_height) / max(1.0, float(width * height))
                sharpness = edge_sharpness(frame, (x1i, y1i, x2i, y2i))
                severity = estimate_severity(area_ratio, confidence, sharpness)
                class_name = self.loader.model.names.get(cls_id, str(cls_id))
                detections.append(
                    Detection(
                        id=str(uuid4()),
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        confidence=round(confidence, 6),
                        severity=severity,
                        frame_index=frame_index,
                        source_id=source_id,
                        session_id=session_id,
                        class_id=cls_id,
                        class_name=class_name,
                        bbox=BoundingBox(
                            x1=x1,
                            y1=y1,
                            x2=x2,
                            y2=y2,
                            x_center=((x1 + x2) / 2) / width,
                            y_center=((y1 + y2) / 2) / height,
                            width=box_width / width,
                            height=box_height / height,
                            area_ratio=area_ratio,
                        ),
                        sharpness=round(sharpness, 3),
                        gps=gps,
                    )
                )
        metrics_store.record_inference(latency_ms, len(detections), model_type="POTHOLE", source=source_id)
        return detections, round(latency_ms, 3)

    def predict_image(self, image_bytes: bytes, source_id: str, session_id: str) -> tuple[ImagePredictionResponse, np.ndarray]:
        array = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Uploaded image could not be decoded by OpenCV")
        detections, latency_ms = self.predict_frame(frame, source_id=source_id, session_id=session_id)
        annotated = annotate_frame(frame, detections)
        height, width = frame.shape[:2]
        confidence_mean = sum(item.confidence for item in detections) / len(detections) if detections else 0.0
        severity_summary = {severity: 0 for severity in ("small", "medium", "severe")}
        for detection in detections:
            severity_summary[detection.severity.value] += 1
        device = get_device_info()
        response = ImagePredictionResponse(
            request_id=str(uuid4()),
            source_id=source_id,
            session_id=session_id,
            image_width=width,
            image_height=height,
            pothole_count=len(detections),
            severity_summary=severity_summary,
            confidence_mean=round(confidence_mean, 6),
            annotated_image_url="",
            detections=detections,
            telemetry=InferenceTelemetry(
                model_version=self.loader.model_version,
                device=device.device,
                cuda_available=device.cuda_available,
                half_precision=device.half_precision,
                latency_ms=latency_ms,
                fps=round(1000 / latency_ms, 3) if latency_ms > 0 else None,
                gpu_name=device.gpu_name,
                vram_used_mb=device.vram_used_mb,
                vram_total_mb=device.vram_total_mb,
            ),
        )
        return response, annotated


inference_engine = InferenceEngine()
