from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    small = "small"
    medium = "medium"
    severe = "severe"


class JobState(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class DetectionType(str, Enum):
    pothole = "pothole"
    road_crack = "road_crack"
    flooding = "flooding"
    waterlogging = "waterlogging"
    garbage_overflow = "garbage_overflow"
    illegal_dumping = "illegal_dumping"
    lane_degradation = "lane_degradation"
    road_obstruction = "road_obstruction"
    manhole_damage = "manhole_damage"
    damaged_streetlight = "damaged_streetlight"
    fallen_tree = "fallen_tree"
    drainage_blockage = "drainage_blockage"
    traffic_signal_failure = "traffic_signal_failure"
    road_erosion = "road_erosion"
    infrastructure_collapse_indicator = "infrastructure_collapse_indicator"


class DeploymentTarget(str, Enum):
    cloud_gpu = "cloud_gpu"
    cloud_cpu = "cloud_cpu"
    runpod_gpu = "runpod_gpu"
    vast_gpu = "vast_gpu"
    lambda_labs_gpu = "lambda_labs_gpu"
    jetson_nano = "jetson_nano"
    jetson_xavier = "jetson_xavier"
    jetson_orin = "jetson_orin"
    raspberry_pi_coral = "raspberry_pi_coral"
    low_power_edge = "low_power_edge"
    dashcam = "dashcam"
    vehicle_mount = "vehicle_mount"
    ios_coreml = "ios_coreml"
    android_tflite = "android_tflite"


class ModelFramework(str, Enum):
    ultralytics_yolov8 = "ultralytics_yolov8"
    onnxruntime = "onnxruntime"
    tensorrt = "tensorrt"
    tensorflow_lite = "tensorflow_lite"
    coreml = "coreml"
    pytorch = "pytorch"


class PrecisionMode(str, Enum):
    fp32 = "fp32"
    fp16 = "fp16"
    int8 = "int8"


class QueuePriority(str, Enum):
    emergency = "emergency"
    high = "high"
    normal = "normal"
    bulk = "bulk"


class TenantRole(str, Enum):
    platform_admin = "platform_admin"
    citizen = "citizen"
    municipality_admin = "municipality_admin"
    emergency_operator = "emergency_operator"
    supervisor = "supervisor"
    contractor = "contractor"
    system_admin = "system_admin"
    operator = "operator"
    field_supervisor = "field_supervisor"
    field_worker = "field_worker"
    auditor = "auditor"


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    x_center: float
    y_center: float
    width: float
    height: float
    area_ratio: float


class Detection(BaseModel):
    id: str
    timestamp: str
    confidence: float
    severity: Severity
    frame_index: int | None = None
    source_id: str
    session_id: str
    class_id: int
    class_name: str
    bbox: BoundingBox
    sharpness: float
    gps: dict[str, float] | None = None


class GeoPoint(BaseModel):
    lat: float
    lon: float


class IncidentRecord(BaseModel):
    incident_id: str
    tenant_id: str
    district_id: str
    issue_type: DetectionType
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    location: GeoPoint
    occurred_at: str
    status: str = "open"
    repair_completed_at: str | None = None
    repair_failed: bool = False
    source_id: str | None = None
    linked_asset_id: str | None = None


class RepairRecord(BaseModel):
    repair_id: str
    tenant_id: str
    district_id: str
    incident_id: str
    completed_at: str
    reopened_within_days: int | None = None
    cost: float | None = None


class WeatherObservation(BaseModel):
    district_id: str
    observed_at: str
    rainfall_mm: float = 0
    temperature_c: float | None = None
    flood_warning: bool = False


class TenantConfig(BaseModel):
    tenant_id: str
    city_name: str
    storage_namespace: str
    allowed_roles: list[TenantRole] = Field(default_factory=list)
    model_thresholds: dict[DetectionType, float] = Field(default_factory=dict)
    enabled_detection_types: list[DetectionType] = Field(default_factory=list)
    branding: dict[str, str] = Field(default_factory=dict)


class ModelMetrics(BaseModel):
    map50: float | None = None
    map50_95: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    false_positive_rate: float | None = None


class TrainingMetadata(BaseModel):
    dataset_version: str
    trained_at: str
    git_sha: str | None = None
    experiment_id: str | None = None
    mlflow_run_id: str | None = None
    wandb_run_id: str | None = None
    training_image_count: int | None = None
    validation_image_count: int | None = None


class GpuRequirements(BaseModel):
    min_vram_mb: int
    preferred_vram_mb: int
    cuda_required: bool = False
    tensor_cores_recommended: bool = False


class LatencyBenchmark(BaseModel):
    target: DeploymentTarget
    precision: PrecisionMode
    batch_size: int
    p50_ms: float
    p95_ms: float
    fps: float


class ModelRegistryEntry(BaseModel):
    model_id: str
    version: str
    framework: ModelFramework
    artifact_uri: str
    metrics: ModelMetrics
    training_metadata: TrainingMetadata
    supported_classes: list[DetectionType]
    deployment_targets: list[DeploymentTarget]
    gpu_requirements: GpuRequirements
    edge_compatible: bool
    latency_benchmarks: list[LatencyBenchmark] = Field(default_factory=list)
    active: bool = False
    rollback_version: str | None = None
    signature_sha256: str | None = None


class ModelRegistryResponse(BaseModel):
    models: list[ModelRegistryEntry]
    active_model_ids: list[str]
    supported_detection_types: list[DetectionType]


class ModelLoadRequest(BaseModel):
    model_id: str
    version: str | None = None
    tenant_id: str | None = None
    warm: bool = True
    priority: QueuePriority = QueuePriority.normal


class ModelLoadPlan(BaseModel):
    model_id: str
    version: str
    selected_device: str
    precision: PrecisionMode
    lazy_load: bool
    gpu_memory_budget_mb: int
    concurrency_limit: int
    reason: str


class EdgeDeploymentRequest(BaseModel):
    model_id: str
    version: str
    target: DeploymentTarget
    precision: PrecisionMode = PrecisionMode.fp16
    offline_hours: int = 12
    uplink_kbps: int = 512


class EdgeDeploymentPlan(BaseModel):
    model_id: str
    version: str
    target: DeploymentTarget
    export_format: str
    optimization_steps: list[str]
    telemetry_batch_bytes: int
    sync_interval_seconds: int
    incident_upload_policy: str
    state_update_policy: str
    compatible: bool
    blockers: list[str] = Field(default_factory=list)


class DistributedInferenceTask(BaseModel):
    task_id: str
    tenant_id: str
    model_id: str
    detection_types: list[DetectionType]
    source_uri: str
    priority: QueuePriority = QueuePriority.normal
    requires_gpu: bool = True
    deadline_ms: int | None = None


class WorkerPoolPlan(BaseModel):
    queue: str
    worker_pool: str
    min_replicas: int
    max_replicas: int
    gpu_required: bool
    routing_key: str
    autoscaling_signal: str


class DistributedInferencePlan(BaseModel):
    task_id: str
    queue_backend: str
    scheduler: str
    selected_queue: str
    worker_pool: WorkerPoolPlan
    tenant_partition_key: str
    trace_id: str


class DistrictHealthScore(BaseModel):
    tenant_id: str
    district_id: str
    road_health_index: float
    drainage_reliability_score: float
    lighting_infrastructure_score: float
    civic_cleanliness_score: float
    repair_effectiveness_score: float
    overall_health_score: float
    degradation_trend: float
    maintenance_urgency: float
    recurrence_pressure: float
    infrastructure_instability_rating: float
    evidence: list[str]


class PredictiveRisk(BaseModel):
    tenant_id: str
    district_id: str
    pothole_recurrence_risk: float
    infrastructure_failure_risk: float
    district_deterioration_risk: float
    seasonal_damage_spike_risk: float
    flood_prone_zone_risk: float
    repair_failure_probability: float
    evidence: list[str]


class IncidentCluster(BaseModel):
    cluster_id: str
    tenant_id: str
    district_id: str
    issue_types: list[DetectionType]
    incident_ids: list[str]
    centroid: GeoPoint
    temporal_span_hours: float
    radius_meters: float
    recurrence_count: int
    correlation_summary: str


class CopilotRecommendation(BaseModel):
    recommendation_id: str
    tenant_id: str
    priority: QueuePriority
    title: str
    summary: str
    recommended_department: str
    sla_risk: float
    actions: list[str]
    explainability: list[str]


class FieldWorker(BaseModel):
    worker_id: str
    tenant_id: str
    district_id: str
    location: GeoPoint
    skills: list[DetectionType]
    active_jobs: int = 0
    available: bool = True


class RouteStop(BaseModel):
    incident_id: str
    eta_minutes: float
    location: GeoPoint
    priority: QueuePriority


class RepairRoute(BaseModel):
    worker_id: str
    tenant_id: str
    total_distance_km_estimate: float
    fuel_efficiency_score: float
    sla_compliance_score: float
    workload_balance_score: float
    stops: list[RouteStop]


class InferenceTelemetry(BaseModel):
    model_version: str
    device: str
    cuda_available: bool
    half_precision: bool
    latency_ms: float
    fps: float | None = None
    gpu_name: str | None = None
    vram_used_mb: float | None = None
    vram_total_mb: float | None = None


class ImagePredictionResponse(BaseModel):
    request_id: str
    source_id: str
    session_id: str
    image_width: int
    image_height: int
    pothole_count: int
    severity_summary: dict[str, int]
    confidence_mean: float
    annotated_image_url: str
    detections: list[Detection]
    telemetry: InferenceTelemetry


class VideoJobResponse(BaseModel):
    job_id: str
    state: JobState
    source_id: str
    status_url: str
    results_url: str


class VideoJobStatus(BaseModel):
    job_id: str
    state: JobState
    progress: float
    frame_index: int
    total_frames: int
    detections: int
    fps: float
    error: str | None = None


class VideoResults(BaseModel):
    job_id: str
    state: JobState
    processed_video_url: str | None = None
    detection_log_url: str | None = None
    analytics: dict[str, Any]
    detections: list[Detection]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
    weights_path: str
    device: str
    cuda_available: bool
