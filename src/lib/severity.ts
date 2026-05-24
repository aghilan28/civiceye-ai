import type { CivicIssueType, CivicSeverity } from "@/types/civic";
import type { DepartmentType } from "@/types/operations";

export function departmentForIssue(issueType: CivicIssueType): DepartmentType {
  const map: Record<CivicIssueType, DepartmentType> = {
    pothole: "roads",
    road_crack: "roads",
    flooding: "emergency_response",
    garbage_overflow: "sanitation",
    drainage_blockage: "stormwater",
    fallen_tree: "emergency_response",
    damaged_streetlight: "streetlighting",
    traffic_signal_failure: "streetlighting",
    road_erosion: "roads",
    infrastructure_collapse_indicator: "emergency_response",
    illegal_dumping: "sanitation",
    lane_degradation: "roads",
    road_obstruction: "roads",
    manhole_damage: "stormwater",
    garbage: "sanitation",
    drainage_overflow: "stormwater",
    broken_streetlight: "streetlighting",
    water_leakage: "water",
    road_damage: "roads"
  };

  return map[issueType];
}

export function classifySeverity(issueType: CivicIssueType, confidence: number): CivicSeverity {
  if (issueType === "drainage_overflow" && confidence >= 0.9) {
    return "critical";
  }

  if (["pothole", "water_leakage", "road_damage"].includes(issueType) && confidence >= 0.82) {
    return "high";
  }

  if (confidence >= 0.68) {
    return "medium";
  }

  return "low";
}

export function repairUrgencyForSeverity(severity: CivicSeverity) {
  const map: Record<CivicSeverity, string> = {
    low: "Monitor and schedule within 7 days",
    medium: "Assign field verification within 72 hours",
    high: "Repair or secure within 24 hours",
    critical: "Immediate response and escalation required"
  };

  return map[severity];
}

export function markerColorForSeverity(severity: CivicSeverity) {
  const map: Record<CivicSeverity, string> = {
    low: "#36D399",
    medium: "#FBBF24",
    high: "#4F8CFF",
    critical: "#FB7185"
  };

  return map[severity];
}
