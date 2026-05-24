import { departmentForIssue, classifySeverity, repairUrgencyForSeverity } from "@/lib/severity";
import { createId, nowIso } from "@/lib/time";
import { yolov8Service } from "@/services/mlops/yolov8-service";
import type { CivicIssueType, GeoPoint } from "@/types/civic";
import type { AiDetectionMetadata, BoundingRegion } from "@/types/operations";

export type AiInferenceInput = {
  image: File;
  location?: GeoPoint;
  preferredIssueType?: CivicIssueType | null;
};

export type NormalizedDetectionResponse = {
  issueType: CivicIssueType;
  confidence: number;
  severity: ReturnType<typeof classifySeverity>;
  recommendedDepartment: ReturnType<typeof departmentForIssue>;
  infrastructureCategory: "roadway" | "sanitation" | "water" | "lighting";
  repairUrgency: string;
  boundingRegions: BoundingRegion[];
  metadata: AiDetectionMetadata;
};

function inferIssueType(input: AiInferenceInput): CivicIssueType {
  if (input.preferredIssueType) {
    return input.preferredIssueType;
  }

  if (input.image.name.toLowerCase().includes("water")) {
    return "water_leakage";
  }

  return "road_damage";
}

function categoryForIssue(issueType: CivicIssueType): NormalizedDetectionResponse["infrastructureCategory"] {
  if (issueType === "garbage") {
    return "sanitation";
  }

  if (issueType === "water_leakage" || issueType === "drainage_overflow") {
    return "water";
  }

  if (issueType === "broken_streetlight") {
    return "lighting";
  }

  return "roadway";
}

export const inferenceService = {
  async analyzeImage(input: AiInferenceInput): Promise<NormalizedDetectionResponse> {
    const started = performance.now();
    const yoloResult = await yolov8Service.infer({
      image: input.image,
      preferredIssueType: input.preferredIssueType ?? inferIssueType(input)
    });
    const topDetection = yoloResult.detections[0];
    if (!topDetection) {
      throw new Error("No infrastructure defect was detected by the active YOLO model.");
    }
    const issueType = topDetection.className;
    const confidence = topDetection.confidence;
    const severity = classifySeverity(issueType, confidence);
    const processedAt = nowIso();
    const boundingRegions: BoundingRegion[] = yoloResult.detections.map((detection) => detection.box);

    return {
      issueType,
      confidence,
      severity,
      recommendedDepartment: departmentForIssue(issueType),
      infrastructureCategory: categoryForIssue(issueType),
      repairUrgency: repairUrgencyForSeverity(severity),
      boundingRegions,
      metadata: {
        modelProvider: "yolov8",
        modelVersion: yoloResult.telemetry.modelId,
        inferenceId: yoloResult.inferenceId || createId("INF"),
        processedAt,
        processingMs: Math.round(performance.now() - started + yoloResult.telemetry.latencyMs),
        boundingRegions,
        geoContext: {
          wardId: "WARD-18",
          municipalityZone: "Bengaluru Zone 07",
          address: "Current civic capture radius",
          nearbyIncidentCount: 6,
          infrastructureDensity: 0.68,
          responseRadiusMeters: 380
        }
      }
    };
  }
};
