from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.database.postgres import DatabaseUnavailable
from backend.distributed.auth import WorkerAuthenticationError, verify_signed_worker_request
from backend.distributed.orchestration import distributed_orchestrator
from backend.config import settings
from backend.models.enterprise import (
    DeadLetterReplayRequest,
    InferenceJobCancelRequest,
    WorkerDeregisterRequest,
    WorkerDrainRequest,
    WorkerClaimRequest,
    WorkerClaimResponse,
    WorkerHeartbeatRequest,
    WorkerJobCompleteRequest,
    WorkerJobFailureRequest,
    WorkerJobProgressRequest,
    WorkerRegistrationRequest,
    WorkerResponse,
)
from backend.security.auth import Principal, require_permission


router = APIRouter(prefix="/api/v1/distributed", tags=["distributed-inference-runtime"])


def worker_row(row: dict) -> WorkerResponse:
    data = dict(row)
    return WorkerResponse(
        id=data["id"],
        worker_id=data.get("workerId", data.get("worker_id")),
        state=data["state"],
        queue_names=list(data.get("queueNames", data.get("queue_names", []))),
        capabilities=data["capabilities"],
        supported_models=list(data.get("supportedModels", data.get("supported_models", []))),
        supported_classes=list(data.get("supportedClasses", data.get("supported_classes", []))),
        gpu_count=data.get("gpuCount", data.get("gpu_count")),
        gpu_name=data.get("gpuName", data.get("gpu_name")),
        cuda_version=data.get("cudaVersion", data.get("cuda_version")),
        torch_version=data.get("torchVersion", data.get("torch_version")),
        vram_total_mb=data.get("vramTotalMb", data.get("vram_total_mb")),
        vram_used_mb=data.get("vramUsedMb", data.get("vram_used_mb")),
        active_job_count=data.get("activeJobCount", data.get("active_job_count")),
        max_concurrent_jobs=data.get("maxConcurrentJobs", data.get("max_concurrent_jobs")),
        last_heartbeat_at=data.get("lastHeartbeatAt", data.get("last_heartbeat_at")),
        registered_at=data.get("registeredAt", data.get("registered_at")),
        expires_at=data.get("expiresAt", data.get("expires_at")),
        failure_reason=data.get("failureReason", data.get("failure_reason")),
        remote_address=data.get("remoteAddress", data.get("remote_address")),
        telemetry=data["telemetry"],
        created_at=data.get("createdAt", data.get("created_at")),
        updated_at=data.get("updatedAt", data.get("updated_at")),
    )


@router.post("/workers/register", response_model=WorkerResponse, status_code=201)
async def register_worker(payload: WorkerRegistrationRequest, request: Request) -> WorkerResponse:
    try:
        signed_payload = payload.model_dump(exclude={"timestamp", "signature"})
        row = await distributed_orchestrator.register_worker(
            worker_id=payload.worker_id,
            payload=signed_payload,
            timestamp=payload.timestamp,
            signature=payload.signature,
            remote_address=request.client.host if request.client else None,
        )
        return worker_row(row)
    except WorkerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/workers/{worker_id}/heartbeat", response_model=WorkerResponse)
async def worker_heartbeat(worker_id: str, payload: WorkerHeartbeatRequest) -> WorkerResponse:
    try:
        verified = verify_signed_worker_request(secret=settings.worker_shared_secret, payload=payload.model_dump(), worker_id=worker_id)
        row = await distributed_orchestrator.heartbeat(worker_id, verified)
        return worker_row(row)
    except WorkerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/workers/{worker_id}/claim", response_model=WorkerClaimResponse)
async def claim_job(worker_id: str, payload: WorkerClaimRequest) -> WorkerClaimResponse:
    try:
        verified = verify_signed_worker_request(secret=settings.worker_shared_secret, payload=payload.model_dump(), worker_id=worker_id)
        return WorkerClaimResponse(job=await distributed_orchestrator.claim_job(worker_id, verified.get("queue_names") or payload.queue_names))
    except WorkerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/workers/{worker_id}/jobs/{job_id}/complete")
async def complete_job(worker_id: str, job_id: str, payload: WorkerJobCompleteRequest) -> dict[str, bool]:
    try:
        verified = verify_signed_worker_request(secret=settings.worker_shared_secret, payload=payload.model_dump(), worker_id=worker_id)
        await distributed_orchestrator.complete_job(
            worker_id,
            job_id,
            verified["claim_id"],
            verified["result"],
            verified["latency_ms"],
            verified.get("telemetry") or {},
            trace_id=verified.get("trace_id"),
        )
        return {"ok": True}
    except WorkerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/workers/{worker_id}/jobs/{job_id}/fail")
async def fail_job(worker_id: str, job_id: str, payload: WorkerJobFailureRequest) -> dict[str, str]:
    try:
        verified = verify_signed_worker_request(secret=settings.worker_shared_secret, payload=payload.model_dump(), worker_id=worker_id)
        status_value = await distributed_orchestrator.fail_job(
            worker_id,
            job_id,
            verified["claim_id"],
            verified["error"],
            verified.get("telemetry") or {},
            trace_id=verified.get("trace_id"),
        )
        return {"status": status_value}
    except WorkerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/topology")
async def topology(principal: Principal = Depends(require_permission("ai:manage"))) -> dict:
    try:
        await distributed_orchestrator.expire_workers()
        await distributed_orchestrator.recover_timeouts()
        return await distributed_orchestrator.topology()
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/workers/{worker_id}/jobs/{job_id}/progress")
async def progress_job(worker_id: str, job_id: str, payload: WorkerJobProgressRequest) -> dict[str, bool]:
    try:
        verified = verify_signed_worker_request(secret=settings.worker_shared_secret, payload=payload.model_dump(), worker_id=worker_id)
        await distributed_orchestrator.progress_job(
            worker_id,
            job_id,
            verified["claim_id"],
            float(verified["progress_percent"]),
            verified["stage"],
            verified.get("telemetry") or {},
        )
        return {"ok": True}
    except WorkerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/workers/{worker_id}/drain", response_model=WorkerResponse)
async def drain_worker(worker_id: str, payload: WorkerDrainRequest) -> WorkerResponse:
    try:
        verified = verify_signed_worker_request(secret=settings.worker_shared_secret, payload=payload.model_dump(), worker_id=worker_id)
        row = await distributed_orchestrator.mark_worker_draining(worker_id, verified.get("reason") or "drain_requested")
        return worker_row(row)
    except WorkerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/workers/{worker_id}/deregister", response_model=WorkerResponse)
async def deregister_worker(worker_id: str, payload: WorkerDeregisterRequest) -> WorkerResponse:
    try:
        verified = verify_signed_worker_request(secret=settings.worker_shared_secret, payload=payload.model_dump(), worker_id=worker_id)
        row = await distributed_orchestrator.deregister_worker(worker_id, verified.get("reason") or "deregister_requested")
        return worker_row(row)
    except WorkerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, payload: InferenceJobCancelRequest, principal: Principal = Depends(require_permission("ai:manage"))) -> dict:
    try:
        return await distributed_orchestrator.cancel_job(job_id, payload.reason)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/dead-letter/replay")
async def replay_dead_letter(payload: DeadLetterReplayRequest, principal: Principal = Depends(require_permission("ai:manage"))) -> dict:
    try:
        rows = await distributed_orchestrator.replay_dead_letter(limit=payload.limit, job_id=payload.job_id)
        return {"replayed": len(rows), "jobs": rows}
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
