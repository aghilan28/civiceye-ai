export type IncidentStatus = "DETECTED" | "VERIFIED" | "ASSIGNED" | "IN_PROGRESS" | "TEMPORARY_FIX" | "COMPLETED" | "REOPENED";
export type IncidentSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type DetectionSource = "BROWSER_GEOLOCATION" | "MOBILE_GPS" | "UPLOADED_METADATA" | "EXIF" | "DASHCAM_GPS" | "MANUAL";

export type OperationsIncident = {
  incident_id: string;
  incident_code: string;
  municipality_id: string;
  latitude: number;
  longitude: number;
  road_name: string | null;
  district: string | null;
  city: string;
  state: string;
  postal_code: string | null;
  geohash: string;
  route_segment_id: string | null;
  severity: IncidentSeverity;
  confidence: number;
  status: IncidentStatus;
  assigned_department: string | null;
  repair_priority: number;
  sla_due_at: string;
  detected_at: string;
  updated_at: string;
};

export type OperationsAnalytics = {
  municipality_id: string;
  active_incidents: number;
  severity_distribution: Record<string, number>;
  repair_completion_rate: number;
  average_sla_hours: number;
  recurrence_rate: number;
  district_risk: Array<{
    id: string;
    name: string;
    incident_count: number;
    risk_score: number;
  }>;
  updated_at: string;
};

export type OperationsEvent =
  | { type: "connected"; channel: string }
  | { type: "incident_created"; incident: OperationsIncident }
  | { type: "incident_updated"; incident: OperationsIncident }
  | { type: "pong"; timestamp: string };

export type FieldRepairTask = {
  id: string;
  incident: OperationsIncident;
  status: "QUEUED" | "ACCEPTED" | "EN_ROUTE" | "IN_PROGRESS" | "BLOCKED" | "COMPLETED" | "REJECTED";
  priority: number;
  notes?: string | null;
};
