import { operationsApi } from "@/services/operations/operations-api";
import type { CivicIssueType, GeoPoint } from "@/types/civic";
import type { AiDetectionMetadata, CivicIncident, DepartmentType, IncidentLifecycleStatus, ReportImage } from "@/types/operations";
import type { DetectionSource, IncidentSeverity, IncidentStatus, OperationsIncident } from "@/types/phase3";

export type CreateIncidentInput = {
  issueType: CivicIssueType;
  confidenceScore: number;
  severity: CivicIncident["severity"];
  location: GeoPoint;
  address: string;
  images: ReportImage[];
  ai: AiDetectionMetadata;
};

const severityToApi: Record<CivicIncident["severity"], IncidentSeverity> = {
  low: "LOW",
  medium: "MEDIUM",
  high: "HIGH",
  critical: "CRITICAL"
};

const severityFromApi: Record<IncidentSeverity, CivicIncident["severity"]> = {
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  CRITICAL: "critical"
};

const statusFromApi: Record<IncidentStatus, IncidentLifecycleStatus> = {
  DETECTED: "detected",
  VERIFIED: "ai_verified",
  ASSIGNED: "assigned",
  IN_PROGRESS: "in_progress",
  TEMPORARY_FIX: "in_progress",
  COMPLETED: "resolved",
  REOPENED: "escalated"
};

function departmentFromApi(value: string | null): DepartmentType {
  if (value === "DRAINAGE") {
    return "stormwater";
  }
  if (value === "UTILITIES") {
    return "water";
  }
  if (value === "SMART_INFRASTRUCTURE") {
    return "streetlighting";
  }
  return "roads";
}

function firstBoundingRegion(input: CreateIncidentInput) {
  return input.ai.boundingRegions[0] ?? {
    x: 0,
    y: 0,
    width: 1,
    height: 1,
    label: input.issueType,
    confidence: input.confidenceScore
  };
}

function apiIncidentToCivicIncident(incident: OperationsIncident): CivicIncident {
  const severity = severityFromApi[incident.severity];
  return {
    id: incident.incident_id,
    issueType: "pothole",
    severity,
    confidenceScore: incident.confidence,
    geoCoordinates: { latitude: incident.latitude, longitude: incident.longitude },
    address: [incident.road_name, incident.district, incident.city, incident.state].filter(Boolean).join(", "),
    municipalityZone: incident.district ?? incident.city,
    images: [],
    ai: {
      modelProvider: "yolov8",
      modelVersion: "persisted-operations",
      inferenceId: incident.incident_code,
      processedAt: incident.detected_at,
      processingMs: 0,
      boundingRegions: [],
      geoContext: {
        wardId: incident.geohash,
        municipalityZone: incident.district ?? incident.city,
        address: incident.road_name ?? "Persisted civic incident",
        nearbyIncidentCount: 0,
        infrastructureDensity: 0,
        responseRadiusMeters: 0
      }
    },
    createdBy: { id: "system", name: "CivicEye Operations", role: "operator" },
    assignedDepartment: departmentFromApi(incident.assigned_department),
    lifecycleStatus: statusFromApi[incident.status],
    escalationLevel: severity === "critical" ? "critical" : severity === "high" ? "sla_risk" : "watch",
    repairTimeline: {
      submittedAt: incident.detected_at,
      verifiedAt: incident.detected_at,
      assignedAt: incident.status === "ASSIGNED" || incident.status === "IN_PROGRESS" || incident.status === "COMPLETED" ? incident.updated_at : undefined,
      startedAt: incident.status === "IN_PROGRESS" || incident.status === "COMPLETED" ? incident.updated_at : undefined,
      resolvedAt: incident.status === "COMPLETED" ? incident.updated_at : undefined,
      slaDueAt: incident.sla_due_at
    },
    verificationState: incident.status === "DETECTED" ? "pending" : "ai_verified",
    auditTrail: [],
    createdAt: incident.detected_at,
    updatedAt: incident.updated_at
  };
}

export const incidentService = {
  async listIncidents() {
    const incidents = await operationsApi.listIncidents();
    return incidents.map(apiIncidentToCivicIncident);
  },

  async getIncident(id: string) {
    const incidents = await operationsApi.listIncidents();
    const incident = incidents.find((item) => item.incident_id === id);
    return incident ? apiIncidentToCivicIncident(incident) : null;
  },

  async createIncident(input: CreateIncidentInput) {
    const box = firstBoundingRegion(input);
    const width = Math.max(0.0001, Math.min(1, box.width));
    const height = Math.max(0.0001, Math.min(1, box.height));
    const capturedAt = input.ai.processedAt;
    const payload = {
      geo: {
        latitude: input.location.latitude,
        longitude: input.location.longitude,
        timestamp: capturedAt,
        road_name: input.address,
        district: input.ai.geoContext.wardId,
        city: "Bengaluru",
        state: "Karnataka",
        postal_code: null,
        municipality_id: operationsApi.municipalityId,
        route_segment_id: null,
        source: "BROWSER_GEOLOCATION" satisfies DetectionSource
      },
      detection: {
        detection_id: input.ai.inferenceId,
        session_id: input.ai.inferenceId,
        source_id: "citizen-report",
        model_version: input.ai.modelVersion,
        confidence: input.confidenceScore,
        class_id: 0,
        class_name: input.issueType,
        frame_index: null,
        bbox_x1: box.x,
        bbox_y1: box.y,
        bbox_x2: box.x + width,
        bbox_y2: box.y + height,
        bbox_width_ratio: width,
        bbox_height_ratio: height,
        bbox_area_ratio: Math.min(1, width * height),
        edge_variance: Math.max(0, input.ai.processingMs),
        frame_persistence: 1
      },
      media_assets: input.images.map((image) => ({
        type: "DETECTION_IMAGE",
        storage_provider: "browser_capture",
        object_key: image.storagePath,
        public_url: image.url,
        content_type: image.contentType,
        size_bytes: image.sizeBytes,
        checksum_sha256: null,
        width: image.width ?? null,
        height: image.height ?? null,
        captured_at: capturedAt,
        metadata: { source: "citizen_report_upload" }
      })),
      image_scale: 1,
      created_by_id: null,
      metadata: {
        issue_type: input.issueType,
        frontend_severity: severityToApi[input.severity],
        geo_context: input.ai.geoContext
      }
    };
    const incident = await operationsApi.createIncident(payload);
    return apiIncidentToCivicIncident(incident);
  }
};
