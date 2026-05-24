import type { ImagePredictionResponse, VideoJobStatus } from "@/services/ai/types";
import type { MapIntelligence } from "@/types/enterprise";
import type { OperationsAnalytics, OperationsIncident } from "@/types/phase3";

const now = Date.now();

function hoursFromNow(hours: number) {
  return new Date(now + hours * 60 * 60 * 1000).toISOString();
}

function hoursAgo(hours: number) {
  return new Date(now - hours * 60 * 60 * 1000).toISOString();
}

export const showcaseStats = [
  { label: "Verified detections", value: "12.6k", detail: "monthly civic reports scored" },
  { label: "Median routing", value: "42s", detail: "AI to department queue" },
  { label: "Demo confidence", value: "94.8%", detail: "YOLOv8 pothole benchmark" },
  { label: "Active districts", value: "18", detail: "seeded operations model" }
];

export const showcaseIncidents: OperationsIncident[] = [
  {
    incident_id: "INC-BLR-1048",
    incident_code: "CE-1048",
    municipality_id: "MUNI-BLR",
    latitude: 12.97218,
    longitude: 77.61254,
    road_name: "MG Road service lane",
    district: "Central Business District",
    city: "Bengaluru",
    state: "Karnataka",
    postal_code: "560001",
    geohash: "tdr1w8",
    route_segment_id: "SEG-MG-18",
    severity: "CRITICAL",
    confidence: 0.972,
    status: "ASSIGNED",
    assigned_department: "ROADS",
    repair_priority: 96,
    sla_due_at: hoursFromNow(3.2),
    detected_at: hoursAgo(0.8),
    updated_at: hoursAgo(0.1)
  },
  {
    incident_id: "INC-BLR-1039",
    incident_code: "CE-1039",
    municipality_id: "MUNI-BLR",
    latitude: 12.98534,
    longitude: 77.64121,
    road_name: "Indiranagar 100 Feet Road",
    district: "East Mobility Corridor",
    city: "Bengaluru",
    state: "Karnataka",
    postal_code: "560038",
    geohash: "tdr1yy",
    route_segment_id: "SEG-IND-07",
    severity: "HIGH",
    confidence: 0.941,
    status: "IN_PROGRESS",
    assigned_department: "ROADS",
    repair_priority: 84,
    sla_due_at: hoursFromNow(7.5),
    detected_at: hoursAgo(2.4),
    updated_at: hoursAgo(0.4)
  },
  {
    incident_id: "INC-BLR-1027",
    incident_code: "CE-1027",
    municipality_id: "MUNI-BLR",
    latitude: 12.93494,
    longitude: 77.61013,
    road_name: "Koramangala 5th Block",
    district: "South Tech District",
    city: "Bengaluru",
    state: "Karnataka",
    postal_code: "560095",
    geohash: "tdr1kz",
    route_segment_id: "SEG-KOR-31",
    severity: "MEDIUM",
    confidence: 0.903,
    status: "VERIFIED",
    assigned_department: "ROADS",
    repair_priority: 62,
    sla_due_at: hoursFromNow(18),
    detected_at: hoursAgo(3.7),
    updated_at: hoursAgo(1.1)
  },
  {
    incident_id: "INC-BLR-1018",
    incident_code: "CE-1018",
    municipality_id: "MUNI-BLR",
    latitude: 12.99742,
    longitude: 77.56792,
    road_name: "Malleshwaram arterial",
    district: "North Residential Ring",
    city: "Bengaluru",
    state: "Karnataka",
    postal_code: "560003",
    geohash: "tdr4c2",
    route_segment_id: "SEG-MAL-11",
    severity: "HIGH",
    confidence: 0.918,
    status: "TEMPORARY_FIX",
    assigned_department: "UTILITIES",
    repair_priority: 78,
    sla_due_at: hoursFromNow(10),
    detected_at: hoursAgo(6.5),
    updated_at: hoursAgo(1.8)
  },
  {
    incident_id: "INC-BLR-1006",
    incident_code: "CE-1006",
    municipality_id: "MUNI-BLR",
    latitude: 12.91577,
    longitude: 77.63452,
    road_name: "HSR Layout 27th Main",
    district: "Outer Ring Tech Belt",
    city: "Bengaluru",
    state: "Karnataka",
    postal_code: "560102",
    geohash: "tdr1re",
    route_segment_id: "SEG-HSR-27",
    severity: "LOW",
    confidence: 0.862,
    status: "COMPLETED",
    assigned_department: "ROADS",
    repair_priority: 41,
    sla_due_at: hoursFromNow(30),
    detected_at: hoursAgo(12),
    updated_at: hoursAgo(0.6)
  }
];

export const showcaseAnalytics: OperationsAnalytics = {
  municipality_id: "MUNI-BLR",
  active_incidents: 128,
  severity_distribution: { LOW: 23, MEDIUM: 51, HIGH: 39, CRITICAL: 15 },
  repair_completion_rate: 0.83,
  average_sla_hours: 7.4,
  recurrence_rate: 0.18,
  district_risk: [
    { id: "DIST-CBD", name: "Central Business District", incident_count: 31, risk_score: 88 },
    { id: "DIST-EAST", name: "East Mobility Corridor", incident_count: 24, risk_score: 74 },
    { id: "DIST-SOUTH", name: "South Tech District", incident_count: 19, risk_score: 62 },
    { id: "DIST-NORTH", name: "North Residential Ring", incident_count: 17, risk_score: 51 }
  ],
  updated_at: new Date(now).toISOString()
};

export const showcaseMapIntelligence: MapIntelligence = {
  municipality_id: "MUNI-BLR",
  incidents: showcaseIncidents.map((incident) => ({
    incident_id: incident.incident_id,
    incident_code: incident.incident_code,
    latitude: incident.latitude,
    longitude: incident.longitude,
    severity: incident.severity,
    confidence: incident.confidence,
    status: incident.status,
    municipality: incident.municipality_id,
    district: incident.district,
    assigned_department: incident.assigned_department,
    sla_due_at: incident.sla_due_at,
    detected_at: incident.detected_at,
    updated_at: incident.updated_at,
    media: []
  })),
  districts: showcaseAnalytics.district_risk.map((district) => ({
    district_id: district.id,
    name: district.name,
    incident_count: district.incident_count,
    critical_count: district.name.includes("Central") ? 7 : district.name.includes("East") ? 4 : 2,
    sla_risk_count: Math.max(2, Math.round(district.incident_count * 0.18)),
    degradation_score: district.risk_score,
    boundary_geojson: null
  })),
  heatmap_points: showcaseIncidents.map((incident) => ({
    incident_id: incident.incident_id,
    coordinates: [incident.longitude, incident.latitude],
    weight: incident.confidence
  })),
  risk_assets: [],
  active_repairs: [
    { id: "TASK-221", team: "Road Crew Alpha", eta_minutes: 9, status: "en_route" },
    { id: "TASK-218", team: "Utility Patch Beta", eta_minutes: 17, status: "stabilizing" }
  ],
  worker_telemetry: [
    { id: "gpu-worker-blr-01", queue: "vision.high", fps: 18.4, status: "running" },
    { id: "gpu-worker-blr-02", queue: "vision.batch", fps: 22.1, status: "running" },
    { id: "edge-worker-ward-18", queue: "edge.live", fps: 12.7, status: "degraded" }
  ],
  updated_at: new Date(now).toISOString()
};

export const architectureNodes = [
  { id: "capture", title: "Citizen and fleet capture", detail: "Image, video, GPS, EXIF, and dashcam evidence enters the intake boundary.", metric: "8.4k/day" },
  { id: "queue", title: "Redis inference queue", detail: "Priority jobs are batched by severity, district, source quality, and SLA pressure.", metric: "312 queued" },
  { id: "gpu", title: "YOLOv8 GPU workers", detail: "Workers run pothole inference, severity scoring, and artifact annotation.", metric: "18.4 FPS" },
  { id: "postgres", title: "Postgres operations graph", detail: "Durable incidents, repairs, teams, SLAs, and district risk are persisted.", metric: "99.9 demo uptime" },
  { id: "realtime", title: "Websocket command layer", detail: "Operators see new detections, status transitions, and field progress in seconds.", metric: "42s route" },
  { id: "analytics", title: "Executive analytics", detail: "District trends, model telemetry, repair efficiency, and quality scores tell the story.", metric: "83% closure" }
];

export const repairWorkflow = [
  { label: "AI detected", value: "97.2%", detail: "Pothole class confidence" },
  { label: "Incident created", value: "CE-1048", detail: "Metadata, GPS, severity, evidence" },
  { label: "District assigned", value: "CBD", detail: "Risk and ownership matched" },
  { label: "Repair queued", value: "P1", detail: "Crew, SLA, materials, proof flow" }
];

export const executiveTrends = [
  { label: "Infrastructure quality", value: 84, trend: "+7" },
  { label: "Response efficiency", value: 78, trend: "+14" },
  { label: "AI precision", value: 95, trend: "+4" },
  { label: "SLA protection", value: 88, trend: "+11" }
];

export const demoImagePrediction: ImagePredictionResponse = {
  request_id: "REQ-DEMO-IMAGE",
  source_id: "portfolio-upload",
  session_id: "SESSION-RECRUITER-DEMO",
  image_width: 1280,
  image_height: 720,
  pothole_count: 3,
  severity_summary: { small: 1, medium: 1, severe: 1 },
  confidence_mean: 0.943,
  annotated_image_url: "",
  detections: [
    {
      id: "DET-1048-A",
      timestamp: new Date(now).toISOString(),
      confidence: 0.972,
      severity: "severe",
      frame_index: 0,
      source_id: "portfolio-upload",
      session_id: "SESSION-RECRUITER-DEMO",
      class_id: 0,
      class_name: "pothole",
      bbox: { x1: 0.17, y1: 0.48, x2: 0.46, y2: 0.72, x_center: 0.315, y_center: 0.6, width: 0.29, height: 0.24, area_ratio: 0.069 },
      sharpness: 84,
      gps: { latitude: 12.97218, longitude: 77.61254 }
    },
    {
      id: "DET-1048-B",
      timestamp: new Date(now + 300).toISOString(),
      confidence: 0.931,
      severity: "medium",
      frame_index: 0,
      source_id: "portfolio-upload",
      session_id: "SESSION-RECRUITER-DEMO",
      class_id: 0,
      class_name: "road-surface-fracture",
      bbox: { x1: 0.56, y1: 0.39, x2: 0.76, y2: 0.58, x_center: 0.66, y_center: 0.485, width: 0.2, height: 0.19, area_ratio: 0.038 },
      sharpness: 79,
      gps: { latitude: 12.97218, longitude: 77.61254 }
    },
    {
      id: "DET-1048-C",
      timestamp: new Date(now + 600).toISOString(),
      confidence: 0.926,
      severity: "small",
      frame_index: 0,
      source_id: "portfolio-upload",
      session_id: "SESSION-RECRUITER-DEMO",
      class_id: 0,
      class_name: "surface-crack",
      bbox: { x1: 0.72, y1: 0.62, x2: 0.87, y2: 0.76, x_center: 0.795, y_center: 0.69, width: 0.15, height: 0.14, area_ratio: 0.021 },
      sharpness: 75,
      gps: { latitude: 12.97218, longitude: 77.61254 }
    }
  ],
  telemetry: {
    model_version: "civiceye-yolov8n-road-v0.3",
    device: "cuda:0 demo profile",
    cuda_available: true,
    half_precision: true,
    latency_ms: 64,
    fps: 18.4,
    gpu_name: "RTX A4000 demo worker",
    vram_used_mb: 2140,
    vram_total_mb: 16384
  }
};

export const demoVideoStatus: VideoJobStatus = {
  job_id: "VID-DEMO-4481",
  state: "running",
  progress: 0.72,
  frame_index: 864,
  total_frames: 1200,
  detections: 18,
  fps: 21.6
};
