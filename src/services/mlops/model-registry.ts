import { env } from "@/config/env";
import type { RegisteredModel } from "@/types/mlops";

export const registeredModels: RegisteredModel[] = [
  {
    id: "civiceye-yolov8-primary",
    provider: "yolov8",
    version: "1.0.0",
    runtime: "gpu",
    endpoint: env.aiInferenceUrl,
    status: env.aiInferenceUrl ? "healthy" : "degraded",
    trafficWeight: 90,
    rollbackVersion: "0.9.4"
  },
  {
    id: "civiceye-fallback-heuristic",
    provider: "fallback_heuristic",
    version: "1.0.0",
    runtime: "edge",
    status: "healthy",
    trafficWeight: 10
  }
];

export function selectInferenceModel() {
  return registeredModels.find((model) => model.status === "healthy" && model.provider === "yolov8") ?? registeredModels[1];
}

export function modelHealthSummary() {
  return registeredModels.map((model) => ({
    id: model.id,
    status: model.status,
    version: model.version,
    runtime: model.runtime
  }));
}
