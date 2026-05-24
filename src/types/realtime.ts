import type { CivicSeverity } from "@/types/civic";
import type { CivicIncident, DepartmentType } from "@/types/operations";

export type RealtimeConnectionStatus = "idle" | "connecting" | "connected" | "reconnecting" | "degraded" | "offline";

export type RealtimeChannel =
  | "city.telemetry"
  | "incidents.live"
  | "ai.operations"
  | "municipality.workflow"
  | "field.response"
  | "risk.forecast"
  | "system.alerts"
  | "emergency"
  | "tenant.operations"
  | "tenant.emergency"
  | "tenant.ai";

export type FieldTeamStatus = "available" | "assigned" | "en_route" | "on_site" | "repairing" | "returning";

export type FieldTeam = {
  id: string;
  name: string;
  department: DepartmentType;
  status: FieldTeamStatus;
  assignedIncidentId?: string;
  etaMinutes?: number;
  routeProgress: number;
  currentZone: string;
};

export type DistrictRiskForecast = {
  districtId: string;
  districtName: string;
  riskScore: number;
  instabilityIndex: number;
  recurrenceProbability: number;
  hazardImpact: number;
  citizenSafetyScore: number;
  responsePressure: number;
  primaryDrivers: string[];
  forecastWindowHours: number;
  updatedAt: string;
};

export type InfrastructureHealthSnapshot = {
  roads: number;
  drainage: number;
  sanitation: number;
  streetlighting: number;
  water: number;
  updatedAt: string;
};

export type LiveTelemetrySnapshot = {
  activeIncidents: number;
  aiAnalysesRunning: number;
  fieldTeamsActive: number;
  slaWarnings: number;
  districtRiskAverage: number;
  eventVelocityPerMinute: number;
  infrastructureHealth: InfrastructureHealthSnapshot;
  updatedAt: string;
};

export type CivicRealtimeEvent =
  | { id: string; type: "INCIDENT_CREATED"; channel: "incidents.live"; timestamp: string; municipalityId: string; payload: { incident: CivicIncident } }
  | { id: string; type: "INCIDENT_ESCALATED"; channel: "incidents.live"; timestamp: string; municipalityId: string; payload: { incidentId: string; severity: CivicSeverity; reason: string } }
  | { id: string; type: "INCIDENT_RESOLVED"; channel: "incidents.live"; timestamp: string; municipalityId: string; payload: { incidentId: string; resolvedBy: string; repairMinutes: number } }
  | { id: string; type: "AI_ANALYSIS_COMPLETED"; channel: "ai.operations"; timestamp: string; municipalityId: string; payload: { incidentId: string; confidence: number; modelVersion: string } }
  | { id: string; type: "MUNICIPALITY_RESPONSE"; channel: "municipality.workflow"; timestamp: string; municipalityId: string; payload: { incidentId: string; department: DepartmentType; action: string } }
  | { id: string; type: "FIELD_TEAM_ASSIGNED"; channel: "field.response"; timestamp: string; municipalityId: string; payload: { team: FieldTeam } }
  | { id: string; type: "SLA_WARNING"; channel: "system.alerts"; timestamp: string; municipalityId: string; payload: { incidentId: string; minutesRemaining: number; severity: CivicSeverity } }
  | { id: string; type: "RISK_FORECAST_UPDATED"; channel: "risk.forecast"; timestamp: string; municipalityId: string; payload: { forecasts: DistrictRiskForecast[] } }
  | { id: string; type: "HOTSPOT_DETECTED"; channel: "risk.forecast"; timestamp: string; municipalityId: string; payload: { districtId: string; issueCount: number; severity: CivicSeverity } }
  | { id: string; type: "TELEMETRY_REFRESH"; channel: "city.telemetry"; timestamp: string; municipalityId: string; payload: { telemetry: LiveTelemetrySnapshot } }
  | { id: string; type: "SYSTEM_ALERT"; channel: "system.alerts"; timestamp: string; municipalityId: string; payload: { title: string; body: string; urgency: "info" | "warning" | "critical" } }
  | { id: string; type: "WEATHER_RISK_EVENT"; channel: "risk.forecast"; timestamp: string; municipalityId: string; payload: { districtId: string; rainfallMm: number; floodRisk: number } }
  | { id: string; type: "emergency_alert"; channel?: "emergency"; timestamp?: string; municipalityId: string; payload?: Record<string, unknown>; event?: Record<string, unknown> }
  | { id: string; type: "tenant_provisioned"; channel?: "system.alerts"; timestamp?: string; municipalityId: string; payload?: Record<string, unknown>; tenant?: Record<string, unknown> };

export type EventBatch = {
  batchId: string;
  municipalityId: string;
  events: CivicRealtimeEvent[];
  receivedAt: string;
};
