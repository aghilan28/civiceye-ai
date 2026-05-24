from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, Depends
from fastapi.responses import FileResponse

from backend.config import settings
from backend.gpu.device import get_device_info
from backend.inference.engine import inference_engine
from backend.inference.model_loader import model_loader
from backend.models.schemas import HealthResponse, ImagePredictionResponse, JobState, VideoJobResponse, VideoJobStatus, VideoResults
from backend.queues.jobs import video_job_queue
from backend.runtime.diagnostics import runtime_diagnostics
from backend.security.middleware import validate_upload_safety
from backend.storage.files import storage_service
from backend.telemetry.metrics import metrics_store
from backend.websocket.manager import handle_live_prediction
from backend.security.auth import Principal, require_permission


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    device = get_device_info()
    return HealthResponse(
        status="ok" if model_loader.loaded or settings.resolved_weights_path.exists() else "model_missing",
        model_loaded=model_loader.loaded,
        model_version=settings.model_version,
        weights_path=str(settings.resolved_weights_path),
        device=device.device,
        cuda_available=device.cuda_available,
    )


@router.get("/runtime/metrics")
async def runtime_metrics() -> dict:
    return {"inference": metrics_store.snapshot(), "model": model_loader.metadata()}


@router.get("/runtime/diagnostics")
async def runtime_health(include_model_load: bool = False) -> dict:
    return await runtime_diagnostics.collect(include_model_load=include_model_load)


@router.get("/api/v1/storage/diagnostics")
async def storage_diagnostics(principal: Principal = Depends(require_permission("ai:manage"))) -> dict:
    return storage_service.diagnostics()


@router.post("/api/v1/storage/signed-upload")
async def signed_upload_url(payload: dict, principal: Principal = Depends(require_permission("media:upload"))) -> dict:
    object_key = str(payload.get("object_key") or "")
    content_type = str(payload.get("content_type") or "application/octet-stream")
    if not object_key or ".." in object_key or object_key.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid object key")
    return storage_service.signed_upload_url(object_key, content_type)


@router.post("/predict/image", response_model=ImagePredictionResponse)
async def predict_image(
    image: UploadFile = File(...),
    source_id: str = Form(default="upload"),
    session_id: str | None = Form(default=None),
) -> ImagePredictionResponse:
    data = await image.read()
    validate_upload_safety(data, image.content_type, ("image/",))
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Upload exceeds configured size limit")
    try:
        response, annotated = inference_engine.predict_image(data, source_id=source_id, session_id=session_id or str(uuid4()))
        path = storage_service.save_annotated_image(annotated)
        response.annotated_image_url = storage_service.public_url(path)
        return response
    except Exception as exc:
        metrics_store.record_failure()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/predict/video", response_model=VideoJobResponse)
async def predict_video(
    video: UploadFile = File(...),
    source_id: str = Form(default="video-upload"),
    session_id: str | None = Form(default=None),
    municipality_id: str = Form(default="MUNI-BLR"),
) -> VideoJobResponse:
    filename = video.filename or "upload.mp4"
    suffix = Path(filename).suffix or ".mp4"
    if suffix.lower() not in {".mp4", ".mov", ".m4v", ".avi"}:
        raise HTTPException(status_code=415, detail="Only mp4, mov, m4v, and avi videos are accepted")
    data = await video.read()
    validate_upload_safety(data, video.content_type, ("video/", "application/octet-stream"))
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Upload exceeds configured size limit")
    path = storage_service.save_upload(data, suffix)
    job = await video_job_queue.enqueue(path, source_id=source_id, session_id=session_id or str(uuid4()), municipality_id=municipality_id)
    return VideoJobResponse(
        job_id=job.id,
        state=JobState.queued,
        source_id=job.source_id,
        status_url=f"/predict/status/{job.id}",
        results_url=f"/predict/results/{job.id}",
    )


@router.get("/predict/status/{job_id}", response_model=VideoJobStatus)
async def video_status(job_id: str) -> VideoJobStatus:
    job = await video_job_queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Video job not found")
    return video_job_queue.status(job)


@router.get("/predict/results/{job_id}", response_model=VideoResults)
async def video_results(job_id: str) -> VideoResults:
    job = await video_job_queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Video job not found")
    return video_job_queue.results(job)


@router.websocket("/predict/live")
async def predict_live(websocket: WebSocket) -> None:
    await handle_live_prediction(websocket)


@router.get("/files/{relative_path:path}")
async def files(relative_path: str) -> FileResponse:
    path = storage_service.resolve_public_path(relative_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
