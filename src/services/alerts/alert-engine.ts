import { createId, nowIso } from "@/lib/time";
import type { CivicIncident } from "@/types/operations";
import type { CivicRealtimeEvent, DistrictRiskForecast } from "@/types/realtime";

export type OperationalAlert = {
  id: string;
  title: string;
  body: string;
  urgency: "info" | "warning" | "critical";
  incidentId?: string;
  districtId?: string;
  createdAt: string;
};

export function buildOperationalAlerts(incidents: CivicIncident[], forecasts: DistrictRiskForecast[]): OperationalAlert[] {
  const criticalIncidents = incidents
    .filter((incident) => incident.severity === "critical" || incident.escalationLevel === "critical")
    .map<OperationalAlert>((incident) => ({
      id: createId("ALT"),
      title: "Critical infrastructure failure",
      body: `${incident.issueType.replaceAll("_", " ")} requires immediate response in ${incident.address}.`,
      urgency: "critical",
      incidentId: incident.id,
      createdAt: nowIso()
    }));

  const riskAlerts = forecasts
    .filter((forecast) => forecast.riskScore >= 78)
    .map<OperationalAlert>((forecast) => ({
      id: createId("ALT"),
      title: "District overload prediction",
      body: `${forecast.districtName} has a ${forecast.riskScore} risk score driven by ${forecast.primaryDrivers.join(", ")}.`,
      urgency: "warning",
      districtId: forecast.districtId,
      createdAt: nowIso()
    }));

  return [...criticalIncidents, ...riskAlerts].slice(0, 8);
}

export function alertToRealtimeEvent(alert: OperationalAlert, municipalityId: string): CivicRealtimeEvent {
  return {
    id: createId("EVT"),
    type: "SYSTEM_ALERT",
    channel: "system.alerts",
    timestamp: alert.createdAt,
    municipalityId,
    payload: {
      title: alert.title,
      body: alert.body,
      urgency: alert.urgency
    }
  };
}
