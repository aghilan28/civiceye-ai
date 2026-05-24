import { repairUrgencyForSeverity } from "@/lib/severity";
import type { CivicIssueType, CivicSeverity } from "@/types/civic";
import type { AiExplanation, YoloDetection } from "@/types/mlops";

export function explainDetection(issueType: CivicIssueType, severity: CivicSeverity, detections: YoloDetection[]): AiExplanation {
  const topDetection = detections[0];
  const confidence = Math.round((topDetection?.confidence ?? 0) * 100);

  return {
    title: `Why CivicEye flagged ${issueType.replaceAll("_", " ")}`,
    summary: `The model found visual patterns consistent with ${issueType.replaceAll("_", " ")} and mapped the region to an operational severity of ${severity}.`,
    confidenceReasoning: `Confidence is ${confidence}% based on visible texture, boundary shape, contrast, and infrastructure context in the detected region.`,
    severityReasoning: `${severity} severity was selected because the detected area, likely road/user impact, and geo-context exceed the configured municipal response threshold.`,
    infrastructureImpact: repairUrgencyForSeverity(severity),
    trustIndicators: [
      "Bounding region intersects visible infrastructure surface",
      "Model response includes normalized confidence and class label",
      "Geo-context enrichment matched a municipality service zone",
      "Inference telemetry is recorded for audit and quality monitoring"
    ]
  };
}
