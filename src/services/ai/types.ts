export type Severity = "small" | "medium" | "severe";
export type JobState = "queued" | "running" | "completed" | "failed" | "cancelled";

export type CivicBoundingBox = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  x_center: number;
  y_center: number;
  width: number;
  height: number;
  area_ratio: number;
};

export type CivicDetection = {
  id: string;
  timestamp: string;
  confidence: number;
  severity: Severity;
  frame_index: number | null;
  source_id: string;
  session_id: string;
  class_id: number;
  class_name: string;
  bbox: CivicBoundingBox;
  sharpness: number;
  gps?: Record<string, number> | null;
};

export type InferenceTelemetry = {
  model_version: string;
  device: string;
  cuda_available: boolean;
  half_precision: boolean;
  latency_ms: number;
  fps?: number | null;
  gpu_name?: string | null;
  vram_used_mb?: number | null;
  vram_total_mb?: number | null;
};

export type ImagePredictionResponse = {
  request_id: string;
  source_id: string;
  session_id: string;
  image_width: number;
  image_height: number;
  pothole_count: number;
  severity_summary: Record<Severity, number>;
  confidence_mean: number;
  annotated_image_url: string;
  detections: CivicDetection[];
  telemetry: InferenceTelemetry;
};

export type VideoJobResponse = {
  job_id: string;
  state: JobState;
  source_id: string;
  status_url: string;
  results_url: string;
};

export type VideoJobStatus = {
  job_id: string;
  state: JobState;
  progress: number;
  frame_index: number;
  total_frames: number;
  detections: number;
  fps: number;
  error?: string | null;
};

export type VideoResults = {
  job_id: string;
  state: JobState;
  processed_video_url?: string | null;
  detection_log_url?: string | null;
  analytics: {
    pothole_count?: number;
    processed_frames?: number;
    duration_seconds?: number;
    severity_distribution?: Record<Severity, number>;
    confidence_mean?: number;
    detections_per_minute?: number;
  };
  detections: CivicDetection[];
};

export type BackendHealth = {
  status: string;
  model_loaded: boolean;
  model_version: string;
  weights_path: string;
  device: string;
  cuda_available: boolean;
};

export type BackendMetrics = {
  inference: Record<string, number>;
  model: Record<string, string | number | boolean | null>;
};

export type LiveInferenceEvent = {
  type: "inference";
  sessionId: string;
  frameIndex: number;
  latencyMs: number;
  fps: number;
  detections: CivicDetection[];
  potholeCount: number;
  annotatedFrame: string;
};

