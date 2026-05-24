import type { CivicIssueType, CivicSeverity } from "@/types/civic";
import type { BoundingRegion } from "@/types/operations";

export type ModelProvider = "yolov8" | "tensorflow" | "opencv" | "fallback_heuristic";

export type ModelRuntime = "edge" | "cpu" | "gpu";

export type ModelHealthStatus = "healthy" | "degraded" | "offline";

export type RegisteredModel = {
  id: string;
  provider: ModelProvider;
  version: string;
  runtime: ModelRuntime;
  endpoint?: string;
  status: ModelHealthStatus;
  trafficWeight: number;
  rollbackVersion?: string;
};

export type YoloDetection = {
  className: CivicIssueType;
  confidence: number;
  box: BoundingRegion;
  maskPolygon?: Array<{ x: number; y: number }>;
};

export type InferenceTelemetry = {
  inferenceId: string;
  modelId: string;
  latencyMs: number;
  retryCount: number;
  cacheHit: boolean;
  gpuUtilization?: number;
  confidenceMean: number;
  failed: boolean;
};

export type AiExplanation = {
  title: string;
  summary: string;
  confidenceReasoning: string;
  severityReasoning: string;
  infrastructureImpact: string;
  trustIndicators: string[];
};

export type ModelInferenceResult = {
  inferenceId: string;
  detections: YoloDetection[];
  severity: CivicSeverity;
  explanation: AiExplanation;
  telemetry: InferenceTelemetry;
};
