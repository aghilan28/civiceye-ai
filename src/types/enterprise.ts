export type MapIncidentFeature = {
  incident_id: string;
  incident_code: string;
  latitude: number;
  longitude: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  status: string;
  municipality: string;
  district: string | null;
  assigned_department: string | null;
  sla_due_at: string;
  detected_at: string;
  updated_at: string;
  media: Array<{ type: string; url: string | null; objectKey: string }>;
};

export type DistrictOverlay = {
  district_id: string;
  name: string;
  incident_count: number;
  critical_count: number;
  sla_risk_count: number;
  degradation_score: number;
  boundary_geojson: GeoJSON.Geometry | null;
};

export type MapIntelligence = {
  municipality_id: string;
  incidents: MapIncidentFeature[];
  districts: DistrictOverlay[];
  heatmap_points: Array<{ incident_id: string; coordinates: [number, number]; weight: number }>;
  risk_assets: Array<Record<string, unknown>>;
  active_repairs: Array<Record<string, unknown>>;
  worker_telemetry: Array<Record<string, unknown>>;
  updated_at: string;
};

export type ModelRegistryEntry = {
  id: string;
  municipality_id: string | null;
  model_type: string;
  version: string;
  artifact_uri: string;
  metrics: Record<string, unknown>;
  training_metadata: Record<string, unknown>;
  supported_classes: string[];
  deployment_target: string;
  latency_p50_ms: number;
  latency_p95_ms: number;
  gpu_required: boolean;
  edge_compatible: boolean;
  active: boolean;
  rollback_version?: string | null;
  benchmark_profile?: Record<string, unknown>;
  deployment_metadata?: Record<string, unknown>;
  promoted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type InferenceJob = {
  id: string;
  municipality_id: string;
  incident_id: string | null;
  model_id: string;
  model_type: string;
  source_uri: string;
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";
  queue_name: string;
  batch_key?: string | null;
  priority: number;
  attempts: number;
  latency_ms: number | null;
  result: Record<string, unknown>;
  error: string | null;
  scheduled_at: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type IntelligenceSnapshot = {
  municipality_id: string;
  city_health_score: number;
  queue_pressure: Record<string, number>;
  gpu_telemetry: Record<string, unknown>;
  websocket_health: Record<string, unknown>;
  model_drift: Array<Record<string, unknown>>;
  agent_recommendations: Array<{
    agent_name: string;
    decision_type: string;
    confidence: number;
    recommendation: Record<string, unknown>;
    trace: Record<string, unknown>;
  }>;
  predictions: Array<Record<string, unknown>>;
  emergency_events: Array<Record<string, unknown>>;
  updated_at: string;
};

export type TenantProvisionRequest = {
  municipality_name: string;
  city: string;
  state: string;
  country?: string;
  plan?: "STARTER" | "GROWTH" | "ENTERPRISE" | "MISSION_CRITICAL";
  admin_email: string;
  admin_name: string;
  enabled_models?: string[];
  storage_region?: string;
  billing_email?: string | null;
};

export type TenantProvisionResponse = {
  municipality_id: string;
  tenant_slug: string;
  admin_user_id: string;
  plan: "STARTER" | "GROWTH" | "ENTERPRISE" | "MISSION_CRITICAL";
  isolated_channels: string[];
  storage_namespace: string;
  ai_config: Record<string, unknown>;
  billing_account: Record<string, unknown>;
  created_at: string;
};

export type CopilotRecommendation = {
  agent_name: string;
  decision_type: string;
  confidence: number;
  recommendation: Record<string, unknown>;
  trace: Record<string, unknown>;
  reasoning: string[];
  evidence: Array<Record<string, unknown>>;
  telemetry_references: string[];
  gis_evidence: Array<Record<string, unknown>>;
  incident_correlations: string[];
};

export type FieldTask = {
  id: string;
  incident_id: string;
  incident_code: string;
  status: "QUEUED" | "ACCEPTED" | "EN_ROUTE" | "IN_PROGRESS" | "BLOCKED" | "COMPLETED" | "REJECTED";
  priority: number;
  road_name: string | null;
  latitude: number;
  longitude: number;
  severity: string;
  sla_due_at: string;
  notes: string | null;
  before_media: Array<Record<string, unknown>>;
  after_media: Array<Record<string, unknown>>;
};

export type EnterpriseOperationsEvent =
  | { type: "connected"; channel: string }
  | { type: "incident_created"; incident: unknown }
  | { type: "incident_updated"; incident: unknown }
  | { type: "worker_assigned"; task: unknown }
  | { type: "repair_started"; task: unknown }
  | { type: "repair_completed"; task: unknown }
  | { type: "severity_changed"; incident: unknown }
  | { type: "AI_detection_received"; job: InferenceJob }
  | { type: "emergency_alert"; event: unknown }
  | { type: "model_registry_updated"; model: ModelRegistryEntry }
  | { type: "pong"; timestamp: string };
