from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.database.postgres import DatabaseUnavailable, postgres_pool
from backend.models.enterprise import (
    BillingInvoiceResponse,
    CopilotRequest,
    CopilotResponse,
    CostOptimizationResponse,
    DisasterOverlayResponse,
    EmergencyEventCreate,
    EmergencyEventResponse,
    FieldTaskResponse,
    GraphAnalysisResponse,
    InferenceJobCreate,
    InferenceJobResponse,
    IntelligenceSnapshotResponse,
    MapIntelligenceResponse,
    ModelRegistryCreate,
    ModelRegistryResponse,
    TenantProvisionRequest,
    TenantProvisionResponse,
    UsageMeterRecord,
)
from backend.security.auth import Principal, require_permission
from backend.services.enterprise_intelligence import enterprise_intelligence_service


router = APIRouter(prefix="/api/v1", tags=["civiceye-enterprise-intelligence"])


def enforce_tenant(principal: Principal, municipality_id: str | None) -> None:
    if municipality_id is None or principal.role in {"system_admin", "platform_admin"}:
        return
    if principal.municipality_id != municipality_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant access denied")


def enforce_platform(principal: Principal) -> None:
    if principal.role not in {"system_admin", "platform_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform administration is required")


@router.get("/operations/map/intelligence", response_model=MapIntelligenceResponse)
async def map_intelligence(
    municipality_id: str = Query(...),
    principal: Principal = Depends(require_permission("analytics:read")),
) -> MapIntelligenceResponse:
    enforce_tenant(principal, municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.map_intelligence(connection, municipality_id)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/intelligence/snapshot", response_model=IntelligenceSnapshotResponse)
async def intelligence_snapshot(
    municipality_id: str = Query(...),
    principal: Principal = Depends(require_permission("analytics:read")),
) -> IntelligenceSnapshotResponse:
    enforce_tenant(principal, municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.intelligence_snapshot(connection, municipality_id)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/ai/models", response_model=list[ModelRegistryResponse])
async def list_models(
    municipality_id: str | None = None,
    principal: Principal = Depends(require_permission("ai:manage")),
) -> list[ModelRegistryResponse]:
    enforce_tenant(principal, municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.list_models(connection, municipality_id)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/ai/models", response_model=ModelRegistryResponse, status_code=201)
async def register_model(
    payload: ModelRegistryCreate,
    principal: Principal = Depends(require_permission("ai:manage")),
) -> ModelRegistryResponse:
    enforce_tenant(principal, payload.municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.register_model(connection, payload)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/ai/models/{model_type}/{version}/promote", response_model=ModelRegistryResponse)
async def promote_model(
    model_type: str,
    version: str,
    municipality_id: str | None = None,
    principal: Principal = Depends(require_permission("ai:manage")),
) -> ModelRegistryResponse:
    enforce_tenant(principal, municipality_id)
    from backend.ai_platform.registry import model_registry_service

    try:
        return model_registry_service.promote(model_type, version, municipality_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/ai/models/{model_type}/rollback", response_model=ModelRegistryResponse)
async def rollback_model(
    model_type: str,
    municipality_id: str | None = None,
    principal: Principal = Depends(require_permission("ai:manage")),
) -> ModelRegistryResponse:
    enforce_tenant(principal, municipality_id)
    from backend.ai_platform.registry import model_registry_service

    try:
        return model_registry_service.rollback(model_type, municipality_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/ai/models/benchmarks")
async def model_benchmarks(
    model_type: str | None = None,
    principal: Principal = Depends(require_permission("ai:manage")),
) -> list[dict]:
    from backend.ai_platform.registry import model_registry_service

    return model_registry_service.benchmark_report(model_type)


@router.get("/ai/orchestration/telemetry")
async def orchestration_telemetry(principal: Principal = Depends(require_permission("ai:manage"))) -> dict:
    from backend.ai_platform.orchestrator import ai_orchestrator

    return ai_orchestrator.telemetry()


@router.post("/ai/inference/jobs", response_model=InferenceJobResponse, status_code=202)
async def enqueue_inference(
    payload: InferenceJobCreate,
    principal: Principal = Depends(require_permission("ai:manage")),
) -> InferenceJobResponse:
    enforce_tenant(principal, payload.municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            try:
                return await enterprise_intelligence_service.enqueue_inference(connection, payload)
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/ai/inference/batch")
async def enqueue_inference_batch(
    payload: list[InferenceJobCreate],
    principal: Principal = Depends(require_permission("ai:manage")),
) -> dict:
    for item in payload:
        enforce_tenant(principal, item.municipality_id)
    from backend.ai_platform.orchestrator import ai_orchestrator

    return await ai_orchestrator.orchestrate_batch(payload)


@router.get("/field/tasks", response_model=list[FieldTaskResponse])
async def field_tasks(
    municipality_id: str = Query(...),
    field_worker_id: str | None = None,
    principal: Principal = Depends(require_permission("incident:read")),
) -> list[FieldTaskResponse]:
    enforce_tenant(principal, municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.field_tasks(connection, municipality_id, field_worker_id)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/emergency/events", response_model=EmergencyEventResponse, status_code=201)
async def create_emergency(
    payload: EmergencyEventCreate,
    principal: Principal = Depends(require_permission("emergency:manage")),
) -> EmergencyEventResponse:
    enforce_tenant(principal, payload.municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.create_emergency(connection, payload)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/tenants/provision", response_model=TenantProvisionResponse, status_code=201)
async def provision_tenant(
    payload: TenantProvisionRequest,
    principal: Principal = Depends(require_permission("tenant:manage")),
) -> TenantProvisionResponse:
    enforce_platform(principal)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.provision_tenant(connection, payload)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/billing/usage")
async def meter_usage(
    payload: UsageMeterRecord,
    principal: Principal = Depends(require_permission("billing:write")),
) -> dict:
    enforce_tenant(principal, payload.municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.meter_usage(connection, payload)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/billing/invoice", response_model=BillingInvoiceResponse)
async def invoice(
    municipality_id: str = Query(...),
    principal: Principal = Depends(require_permission("billing:read")),
) -> BillingInvoiceResponse:
    enforce_tenant(principal, municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.invoice(connection, municipality_id)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/copilot/recommendations", response_model=CopilotResponse)
async def copilot(
    payload: CopilotRequest,
    principal: Principal = Depends(require_permission("analytics:read")),
) -> CopilotResponse:
    enforce_tenant(principal, payload.municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.copilot(connection, payload)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/knowledge-graph/analysis", response_model=GraphAnalysisResponse)
async def graph_analysis(
    municipality_id: str = Query(...),
    principal: Principal = Depends(require_permission("analytics:read")),
) -> GraphAnalysisResponse:
    enforce_tenant(principal, municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.graph_analysis(connection, municipality_id)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/emergency/overlays", response_model=DisasterOverlayResponse)
async def disaster_overlays(
    municipality_id: str = Query(...),
    principal: Principal = Depends(require_permission("incident:read")),
) -> DisasterOverlayResponse:
    enforce_tenant(principal, municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.disaster_overlays(connection, municipality_id)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/cost/optimization", response_model=CostOptimizationResponse)
async def cost_optimization(
    municipality_id: str = Query(...),
    principal: Principal = Depends(require_permission("system:manage")),
) -> CostOptimizationResponse:
    enforce_tenant(principal, municipality_id)
    try:
        async with postgres_pool.acquire() as connection:
            return await enterprise_intelligence_service.cost_optimization(connection, municipality_id)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
