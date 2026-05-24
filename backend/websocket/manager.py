from __future__ import annotations

import asyncio
import base64
from time import perf_counter
from collections import defaultdict, deque
from time import time
from uuid import uuid4

import cv2
import numpy as np
from fastapi import WebSocket

from backend.config import settings
from backend.inference.annotator import annotate_frame
from backend.inference.engine import inference_engine
from backend.models.schemas import Detection
from backend.security.auth import websocket_principal
from backend.telemetry.metrics import metrics_store


class WebSocketConnectionManager:
    def __init__(self) -> None:
        self.active: dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()
        self._message_hits: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=settings.websocket_max_messages_per_minute * 2))

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = str(uuid4())
        async with self.lock:
            self.active[session_id] = websocket
        return session_id

    async def disconnect(self, session_id: str) -> None:
        async with self.lock:
            self.active.pop(session_id, None)

    async def send_json(self, session_id: str, payload: dict) -> None:
        websocket = self.active.get(session_id)
        if websocket is not None:
            await websocket.send_json(payload)
            metrics_store.record_websocket_bytes("sent", settings.websocket_region, len(str(payload).encode("utf-8")))

    def rate_limited(self, session_id: str) -> bool:
        now = time()
        hits = self._message_hits[session_id]
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= settings.websocket_max_messages_per_minute:
            metrics_store.record_websocket("rate_limited", settings.websocket_region, len(self.active))
            return True
        hits.append(now)
        return False


connection_manager = WebSocketConnectionManager()


def decode_data_url_image(payload: str) -> np.ndarray:
    data = payload.split(",", 1)[1] if "," in payload else payload
    image_bytes = base64.b64decode(data)
    array = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("WebSocket frame could not be decoded")
    return frame


def encode_jpeg_data_url(frame: np.ndarray) -> str:
    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
    if not ok:
        raise RuntimeError("Failed to encode annotated live frame")
    return "data:image/jpeg;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")


async def handle_live_prediction(websocket: WebSocket) -> None:
    principal = websocket_principal(websocket)
    if settings.require_auth and principal is None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "error": "websocket_auth_required"})
        await websocket.close(code=4401)
        return
    session_id = await connection_manager.connect(websocket)
    frame_index = 0
    source_id = websocket.query_params.get("source_id", "webcam")
    await connection_manager.send_json(session_id, {"type": "connected", "sessionId": session_id})
    try:
        while True:
            message = await websocket.receive_json()
            metrics_store.record_websocket_bytes("received", settings.websocket_region, len(str(message).encode("utf-8")))
            if connection_manager.rate_limited(session_id):
                await connection_manager.send_json(session_id, {"type": "error", "error": "websocket_rate_limited", "sessionId": session_id})
                continue
            if message.get("type") == "ping":
                await connection_manager.send_json(session_id, {"type": "pong", "sessionId": session_id})
                continue
            frame_payload = message.get("frame")
            if not isinstance(frame_payload, str):
                await connection_manager.send_json(session_id, {"type": "error", "error": "Missing frame payload"})
                continue
            gps = message.get("gps") if isinstance(message.get("gps"), dict) else None
            started = perf_counter()
            frame = decode_data_url_image(frame_payload)
            detections, latency_ms = inference_engine.predict_frame(
                frame,
                source_id=source_id,
                session_id=session_id,
                frame_index=frame_index,
                gps=gps,
            )
            annotated = annotate_frame(frame, detections)
            elapsed = perf_counter() - started
            payload = {
                "type": "inference",
                "sessionId": session_id,
                "frameIndex": frame_index,
                "latencyMs": latency_ms,
                "fps": round(1 / elapsed, 3) if elapsed > 0 else 0,
                "detections": [detection.model_dump(mode="json") for detection in detections],
                "potholeCount": len(detections),
                "annotatedFrame": encode_jpeg_data_url(annotated),
            }
            await connection_manager.send_json(session_id, payload)
            frame_index += 1
    finally:
        await connection_manager.disconnect(session_id)
