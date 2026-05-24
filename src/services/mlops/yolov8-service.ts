import { createId } from "@/lib/time";
import { classifySeverity } from "@/lib/severity";
import { telemetry } from "@/services/observability/telemetry";
import { inferenceCache, buildInferenceCacheKey } from "@/services/mlops/inference-cache";
import { selectInferenceModel } from "@/services/mlops/model-registry";
import { explainDetection } from "@/services/mlops/explainability-service";
import { aiBackendClient } from "@/services/ai/backend-client";
import type { CivicIssueType } from "@/types/civic";
import type { ModelInferenceResult, YoloDetection } from "@/types/mlops";

export type YoloInferenceInput = {
  image: File;
  preferredIssueType?: CivicIssueType | null;
  signal?: AbortSignal;
};

function normalizeIssueType(className: string): CivicIssueType {
  return className === "pothole" ? "pothole" : "road_damage";
}

function toYoloDetection(className: string, confidence: number, bbox: { x_center: number; y_center: number; width: number; height: number }): YoloDetection {
  const issueType = normalizeIssueType(className);
  return {
    className: issueType,
    confidence,
    box: {
      x: bbox.x_center - bbox.width / 2,
      y: bbox.y_center - bbox.height / 2,
      width: bbox.width,
      height: bbox.height,
      label: issueType,
      confidence
    }
  };
}

export const yolov8Service = {
  async infer(input: YoloInferenceInput): Promise<ModelInferenceResult> {
    const model = selectInferenceModel();
    const cacheKey = buildInferenceCacheKey(input.image, model.id);
    const cached = inferenceCache.get(cacheKey);

    if (cached) {
      telemetry.metric({ name: "ai.inference.cache_hit", value: 1, unit: "count", tags: { model: model.id } });
      return {
        ...cached,
        telemetry: {
          ...cached.telemetry,
          cacheHit: true
        }
      };
    }

    const inferenceId = createId("INF");
    const span = telemetry.span("ai.yolov8.inference", inferenceId);
    const startedAt = performance.now();

    try {
      const payload = await aiBackendClient.predictImage(input.image, input.signal);
      const detections = payload.detections.map((detection) =>
        toYoloDetection(detection.class_name, detection.confidence, detection.bbox)
      );
      const topDetection = detections[0];
      const explanationIssueType = topDetection?.className ?? "pothole";
      const severity = topDetection ? classifySeverity(topDetection.className, topDetection.confidence) : "low";
      const latencyMs = Math.round(performance.now() - startedAt);
      const result: ModelInferenceResult = {
        inferenceId,
        detections,
        severity,
        explanation: explainDetection(explanationIssueType, severity, detections),
        telemetry: {
          inferenceId,
          modelId: payload.telemetry.model_version,
          latencyMs,
          retryCount: 0,
          cacheHit: false,
          gpuUtilization: payload.telemetry.cuda_available ? 1 : undefined,
          confidenceMean: payload.confidence_mean,
          failed: false
        }
      };

      inferenceCache.set(cacheKey, result);
      telemetry.metric({ name: "ai.inference.latency", value: latencyMs, unit: "ms", tags: { model: model.id } });
      span.end({ modelId: payload.telemetry.model_version, detectionCount: detections.length });
      return result;
    } catch (error) {
      span.fail(error, { modelId: model.id });
      throw error;
    }
  }
};
