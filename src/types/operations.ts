import type { AuthUser, UserRole } from "@/types/auth";
import type { CivicIssueType, CivicSeverity, GeoPoint } from "@/types/civic";

export type IncidentLifecycleStatus =
  | "detected"
  | "submitted"
  | "ai_verified"
  | "municipality_reviewed"
  | "assigned"
  | "in_progress"
  | "escalated"
  | "resolved"
  | "archived";

export type VerificationState = "pending" | "ai_verified" | "human_verified" | "rejected";

export type EscalationLevel = "none" | "watch" | "sla_risk" | "critical";

export type DepartmentType =
  | "roads"
  | "sanitation"
  | "stormwater"
  | "streetlighting"
  | "water"
  | "emergency_response";

export type BoundingRegion = {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence: number;
};

export type GeoContextMetadata = {
  wardId: string;
  municipalityZone: string;
  address: string;
  nearbyIncidentCount: number;
  infrastructureDensity: number;
  responseRadiusMeters: number;
};

export type AiDetectionMetadata = {
  modelProvider: "yolov8" | "tensorflow" | "opencv" | "manual_review";
  modelVersion: string;
  inferenceId: string;
  processedAt: string;
  processingMs: number;
  boundingRegions: BoundingRegion[];
  segmentationMaskUrl?: string;
  geoContext: GeoContextMetadata;
};

export type RepairTimeline = {
  submittedAt: string;
  verifiedAt?: string;
  assignedAt?: string;
  startedAt?: string;
  escalatedAt?: string;
  resolvedAt?: string;
  slaDueAt: string;
};

export type ReportImage = {
  id: string;
  url: string;
  storagePath: string;
  width?: number;
  height?: number;
  contentType: string;
  sizeBytes: number;
};

export type IncidentAuditEvent = {
  id: string;
  actorId: string;
  actorRole: UserRole | "system" | "ai";
  fromStatus?: IncidentLifecycleStatus;
  toStatus: IncidentLifecycleStatus;
  message: string;
  createdAt: string;
};

export type CivicIncident = {
  id: string;
  issueType: CivicIssueType;
  severity: CivicSeverity;
  confidenceScore: number;
  geoCoordinates: GeoPoint;
  address: string;
  municipalityZone: string;
  images: ReportImage[];
  ai: AiDetectionMetadata;
  createdBy: Pick<AuthUser, "id" | "name" | "role">;
  assignedDepartment: DepartmentType;
  lifecycleStatus: IncidentLifecycleStatus;
  escalationLevel: EscalationLevel;
  repairTimeline: RepairTimeline;
  verificationState: VerificationState;
  auditTrail: IncidentAuditEvent[];
  createdAt: string;
  updatedAt: string;
};

export type MunicipalityDepartment = {
  id: string;
  municipalityId: string;
  type: DepartmentType;
  name: string;
  activeCrewCount: number;
  openIncidentCount: number;
  serviceZones: string[];
  slaHoursBySeverity: Record<CivicSeverity, number>;
};

export type DashboardMetrics = {
  activeIncidents: number;
  aiVerifiedIncidents: number;
  slaRiskCount: number;
  resolvedToday: number;
  averageConfidence: number;
  workloadByDepartment: Array<{
    department: DepartmentType;
    open: number;
    capacity: number;
  }>;
  severityDistribution: Record<CivicSeverity, number>;
};

export type NotificationCategory = "report_update" | "escalation" | "municipality_response" | "ai_verified" | "nearby_alert" | "emergency";

export type CivicNotification = {
  id: string;
  category: NotificationCategory;
  title: string;
  body: string;
  incidentId?: string;
  unread: boolean;
  createdAt: string;
};

export type OfflineQueueItem = {
  id: string;
  type: "create_report" | "upload_media" | "transition_incident";
  payload: unknown;
  attempts: number;
  createdAt: string;
  lastAttemptAt?: string;
  status: "queued" | "syncing" | "failed";
};

export type RealtimeEvent =
  | { type: "incident.created"; incident: CivicIncident }
  | { type: "incident.updated"; incident: CivicIncident }
  | { type: "notification.created"; notification: CivicNotification }
  | { type: "telemetry.updated"; metrics: DashboardMetrics };
