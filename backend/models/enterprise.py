from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


AIModelType = Literal[
    "POTHOLE",
    "ROAD_CRACK",
    "FLOODING",
    "GARBAGE_OVERFLOW",
    "ILLEGAL_DUMPING",
    "LANE_DEGRADATION",
    "ROAD_OBSTRUCTION",
    "MANHOLE_DAMAGE",
    "FALLEN_TREE",
    "STREETLIGHT_FAILURE",
    "DRAINAGE_BLOCKAGE",
    "TRAFFIC_SIGNAL_FAILURE",
    "ROAD_EROSION",
    "INFRASTRUCTURE_COLLAPSE",
]
DeploymentTarget = Literal[
    "CLOUD_GPU",
    "CLOUD_CPU",
    "AWS_GPU_EC2",
    "GCP_GPU_VM",
    "AZURE_GPU_VM",
    "RUNPOD_GPU",
    "VAST_GPU",
    "LAMBDA_LABS_GPU",
    "EDGE_JETSON_NANO",
    "EDGE_JETSON_XAVIER",
    "EDGE_JETSON_ORIN",
    "EDGE_CORAL_TPU",
    "EDGE_TFLITE",
    "EDGE_COREML",
    "VEHICLE_DASHCAM",
]
InferenceJobStatus = Literal["QUEUED", "RETRY", "RUNNING", "COMPLETED", "FAILED", "DEAD_LETTER", "CANCELLED"]
InferenceWorkerState = Literal["ONLINE", "DRAINING", "OFFLINE", "EXPIRED", "FAILED"]
EmergencySeverity = Literal["WATCH", "ELEVATED", "SEVERE", "DISASTER"]
TenantPlan = Literal["STARTER", "GROWTH", "ENTERPRISE", "MISSION_CRITICAL"]
BillingStatus = Literal["TRIAL", "ACTIVE", "PAST_DUE", "SUSPENDED", "CANCELLED"]


class MapIncidentFeature(BaseModel):
    incident_id: str
    incident_code: str
    latitude: float
    longitude: float
    severity: str
    confidence: float
    status: str
    municipality: str
    district: str | None
    assigned_department: str | None
    sla_due_at: datetime
    detected_at: datetime
    updated_at: datetime
    media: list[dict[str, Any]] = Field(default_factory=list)


class DistrictOverlay(BaseModel):
    district_id: str
    name: str
    incident_count: int
    critical_count: int
    sla_risk_count: int
    degradation_score: float
    boundary_geojson: dict[str, Any] | None = None


class MapIntelligenceResponse(BaseModel):
    municipality_id: str
    incidents: list[MapIncidentFeature]
    districts: list[DistrictOverlay]
    heatmap_points: list[dict[str, Any]]
    risk_assets: list[dict[str, Any]]
    active_repairs: list[dict[str, Any]]
    worker_telemetry: list[dict[str, Any]]
    updated_at: datetime


class ModelRegistryCreate(BaseModel):
    municipality_id: str | None = None
    model_type: AIModelType
    version: str
    artifact_uri: str
    metrics: dict[str, Any]
    training_metadata: dict[str, Any]
    supported_classes: list[str]
    deployment_target: DeploymentTarget
    latency_p50_ms: int = Field(ge=0)
    latency_p95_ms: int = Field(ge=0)
    gpu_required: bool = False
    edge_compatible: bool = False
    active: bool = False
    rollback_version: str | None = None
    benchmark_profile: dict[str, Any] = Field(default_factory=dict)
    deployment_metadata: dict[str, Any] = Field(default_factory=dict)


class ModelRegistryResponse(ModelRegistryCreate):
    id: str
    promoted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InferenceJobCreate(BaseModel):
    municipality_id: str
    incident_id: str | None = None
    model_type: AIModelType
    source_uri: str
    priority: int = Field(default=50, ge=1, le=100)
    queue_name: str | None = None
    requested_models: list[AIModelType] = Field(default_factory=list)
    consensus_required: bool = False
    batch_key: str | None = None


class InferenceJobResponse(BaseModel):
    id: str
    municipality_id: str
    incident_id: str | None
    model_id: str
    model_type: AIModelType
    source_uri: str
    status: InferenceJobStatus
    queue_name: str
    batch_key: str | None = None
    priority: int
    attempts: int
    latency_ms: int | None
    result: dict[str, Any]
    error: str | None
    scheduled_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WorkerRegistrationRequest(BaseModel):
    worker_id: str
    queue_names: list[str] = Field(default_factory=lambda: ["gpu.high"])
    capabilities: dict[str, Any]
    supported_models: list[str] = Field(default_factory=list)
    supported_classes: list[str] = Field(default_factory=lambda: ["pothole"])
    gpu: dict[str, Any] = Field(default_factory=dict)
    max_concurrent_jobs: int = Field(default=1, ge=1, le=64)
    runtime_version: str | None = None
    telemetry: dict[str, Any] = Field(default_factory=dict)
    timestamp: int
    signature: str


class SignedWorkerRequest(BaseModel):
    worker_id: str
    timestamp: int
    signature: str


class WorkerHeartbeatRequest(SignedWorkerRequest):
    active_job_count: int = Field(default=0, ge=0)
    gpu: dict[str, Any] = Field(default_factory=dict)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    queue_names: list[str] = Field(default_factory=list)
    supported_models: list[str] = Field(default_factory=list)
    supported_classes: list[str] = Field(default_factory=list)
    runtime_version: str | None = None
    telemetry: dict[str, Any] = Field(default_factory=dict)


class WorkerClaimRequest(SignedWorkerRequest):
    queue_names: list[str] = Field(default_factory=lambda: ["gpu.high"])


class WorkerJobCompleteRequest(SignedWorkerRequest):
    claim_id: str
    trace_id: str | None = None
    result: dict[str, Any]
    latency_ms: int = Field(ge=0)
    telemetry: dict[str, Any] = Field(default_factory=dict)


class WorkerJobFailureRequest(SignedWorkerRequest):
    claim_id: str
    trace_id: str | None = None
    error: str
    telemetry: dict[str, Any] = Field(default_factory=dict)


class WorkerJobProgressRequest(SignedWorkerRequest):
    claim_id: str
    trace_id: str | None = None
    progress_percent: float = Field(ge=0, le=100)
    stage: str
    telemetry: dict[str, Any] = Field(default_factory=dict)


class WorkerDrainRequest(SignedWorkerRequest):
    reason: str = "drain_requested"


class WorkerDeregisterRequest(SignedWorkerRequest):
    reason: str = "deregister_requested"


class DeadLetterReplayRequest(BaseModel):
    job_id: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


class InferenceJobCancelRequest(BaseModel):
    reason: str = "cancel_requested"


class WorkerResponse(BaseModel):
    id: str
    worker_id: str
    state: InferenceWorkerState
    queue_names: list[str]
    capabilities: dict[str, Any]
    supported_models: list[str]
    supported_classes: list[str]
    gpu_count: int
    gpu_name: str | None
    cuda_version: str | None
    torch_version: str | None
    vram_total_mb: int | None
    vram_used_mb: int | None
    active_job_count: int
    max_concurrent_jobs: int
    last_heartbeat_at: datetime | None
    registered_at: datetime
    expires_at: datetime | None
    failure_reason: str | None
    remote_address: str | None
    telemetry: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class WorkerClaimResponse(BaseModel):
    job: dict[str, Any] | None


class AgentRecommendation(BaseModel):
    agent_name: str
    decision_type: str
    confidence: float
    recommendation: dict[str, Any]
    trace: dict[str, Any]
    reasoning: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    telemetry_references: list[str] = Field(default_factory=list)
    gis_evidence: list[dict[str, Any]] = Field(default_factory=list)
    incident_correlations: list[str] = Field(default_factory=list)


class IntelligenceSnapshotResponse(BaseModel):
    municipality_id: str
    city_health_score: float
    queue_pressure: dict[str, Any]
    gpu_telemetry: dict[str, Any]
    websocket_health: dict[str, Any]
    model_drift: list[dict[str, Any]]
    agent_recommendations: list[AgentRecommendation]
    predictions: list[dict[str, Any]]
    emergency_events: list[dict[str, Any]]
    updated_at: datetime


class FieldTaskResponse(BaseModel):
    id: str
    incident_id: str
    incident_code: str
    status: str
    priority: int
    road_name: str | None
    latitude: float
    longitude: float
    severity: str
    sla_due_at: datetime
    notes: str | None
    before_media: list[dict[str, Any]]
    after_media: list[dict[str, Any]]


class EmergencyEventCreate(BaseModel):
    municipality_id: str
    district_id: str | None = None
    incident_id: str | None = None
    event_type: str
    severity: EmergencySeverity
    centroid_lat: float | None = Field(default=None, ge=-90, le=90)
    centroid_lng: float | None = Field(default=None, ge=-180, le=180)
    impact_radius_meters: int | None = Field(default=None, ge=1)
    command_log: list[dict[str, Any]] = Field(default_factory=list)


class EmergencyEventResponse(EmergencyEventCreate):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime


class TenantProvisionRequest(BaseModel):
    municipality_name: str
    city: str
    state: str
    country: str = "IN"
    plan: TenantPlan = "ENTERPRISE"
    admin_email: str
    admin_name: str
    enabled_models: list[AIModelType] = Field(default_factory=list)
    storage_region: str = "ap-south-1"
    billing_email: str | None = None


class TenantProvisionResponse(BaseModel):
    municipality_id: str
    tenant_slug: str
    admin_user_id: str
    plan: TenantPlan
    isolated_channels: list[str]
    storage_namespace: str
    ai_config: dict[str, Any]
    billing_account: dict[str, Any]
    created_at: datetime


class UsageMeterRecord(BaseModel):
    municipality_id: str
    metric: str
    quantity: float = Field(gt=0)
    unit: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class BillingInvoiceResponse(BaseModel):
    municipality_id: str
    plan: TenantPlan
    status: BillingStatus
    invoice_id: str
    period_start: datetime
    period_end: datetime
    usage: list[dict[str, Any]]
    subtotal_usd: float
    total_usd: float
    generated_at: datetime


class CopilotRequest(BaseModel):
    municipality_id: str
    incident_id: str | None = None
    agent_names: list[str] = Field(default_factory=list)
    include_emergency: bool = True
    include_routing: bool = True


class CopilotResponse(BaseModel):
    municipality_id: str
    recommendations: list[AgentRecommendation]
    autonomous_actions: list[dict[str, Any]]
    updated_at: datetime


class GraphAnalysisResponse(BaseModel):
    municipality_id: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    cascading_failures: list[dict[str, Any]]
    hotspots: list[dict[str, Any]]
    dependency_risks: list[dict[str, Any]]
    updated_at: datetime


class DisasterOverlayResponse(BaseModel):
    municipality_id: str
    flood_overlays: list[dict[str, Any]]
    emergency_heatmap: list[dict[str, Any]]
    district_scores: list[dict[str, Any]]
    evacuation_routes: list[dict[str, Any]]
    infrastructure_stress: list[dict[str, Any]]
    updated_at: datetime


class CostOptimizationResponse(BaseModel):
    municipality_id: str
    gpu_autoscaling: dict[str, Any]
    spot_capacity: dict[str, Any]
    inference_batching: dict[str, Any]
    storage_lifecycle: dict[str, Any]
    redis_memory: dict[str, Any]
    cdn: dict[str, Any]
    recommendations: list[dict[str, Any]]
    updated_at: datetime
