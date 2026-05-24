export type CivicIssueType =
  | "pothole"
  | "road_crack"
  | "flooding"
  | "garbage_overflow"
  | "drainage_blockage"
  | "fallen_tree"
  | "damaged_streetlight"
  | "traffic_signal_failure"
  | "road_erosion"
  | "infrastructure_collapse_indicator"
  | "illegal_dumping"
  | "lane_degradation"
  | "road_obstruction"
  | "manhole_damage"
  | "garbage"
  | "drainage_overflow"
  | "broken_streetlight"
  | "water_leakage"
  | "road_damage";

export type CivicSeverity = "low" | "medium" | "high" | "critical";

export type GeoPoint = {
  latitude: number;
  longitude: number;
  accuracy?: number;
};

export type DetectionResult = {
  issueType: CivicIssueType;
  confidence: number;
  severity: CivicSeverity;
  boundingBox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
};

export type CivicReport = {
  id: string;
  title: string;
  description?: string;
  issueType: CivicIssueType;
  severity: CivicSeverity;
  status: "submitted" | "verified" | "assigned" | "resolved" | "rejected";
  location: GeoPoint;
  imageUrl?: string;
  detection?: DetectionResult;
  createdAt: string;
  updatedAt: string;
};

export type CreateReportPayload = {
  description?: string;
  issueType?: CivicIssueType;
  location: GeoPoint;
  image: File;
};
