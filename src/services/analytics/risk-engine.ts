import { nowIso } from "@/lib/time";
import type { CivicIncident } from "@/types/operations";
import type { DistrictRiskForecast, InfrastructureHealthSnapshot } from "@/types/realtime";

const severityWeight = {
  low: 0.18,
  medium: 0.38,
  high: 0.68,
  critical: 1
};

export function calculateInfrastructureHealth(incidents: CivicIncident[]): InfrastructureHealthSnapshot {
  const roadPressure = incidents.filter((incident) => incident.assignedDepartment === "roads").length;
  const drainagePressure = incidents.filter((incident) => incident.assignedDepartment === "stormwater").length;
  const sanitationPressure = incidents.filter((incident) => incident.assignedDepartment === "sanitation").length;
  const waterPressure = incidents.filter((incident) => incident.assignedDepartment === "water").length;

  return {
    roads: Math.max(40, 92 - roadPressure * 4),
    drainage: Math.max(35, 88 - drainagePressure * 7),
    sanitation: Math.max(45, 91 - sanitationPressure * 5),
    streetlighting: 91,
    water: Math.max(45, 88 - waterPressure * 6),
    updatedAt: nowIso()
  };
}

export function buildRiskForecasts(incidents: CivicIncident[]): DistrictRiskForecast[] {
  const grouped = incidents.reduce<Record<string, CivicIncident[]>>((acc, incident) => {
    const key = incident.ai.geoContext.wardId;
    acc[key] = [...(acc[key] ?? []), incident];
    return acc;
  }, {});

  return Object.entries(grouped).map(([districtId, districtIncidents]) => {
    const severityPressure = districtIncidents.reduce((sum, incident) => sum + severityWeight[incident.severity] * 100, 0);
    const avgConfidence =
      districtIncidents.reduce((sum, incident) => sum + incident.confidenceScore, 0) / Math.max(districtIncidents.length, 1);
    const responsePressure = Math.min(100, districtIncidents.length * 18 + severityPressure / 8);
    const riskScore = Math.min(100, Math.round(severityPressure / Math.max(districtIncidents.length, 1) + responsePressure * 0.35));

    return {
      districtId,
      districtName: districtIncidents[0]?.ai.geoContext.address ?? districtId,
      riskScore,
      instabilityIndex: Math.min(100, Math.round(riskScore * 0.82 + districtIncidents.length * 4)),
      recurrenceProbability: Math.min(100, Math.round(avgConfidence * 72 + districtIncidents.length * 6)),
      hazardImpact: Math.min(100, Math.round(severityPressure / Math.max(districtIncidents.length, 1))),
      citizenSafetyScore: Math.max(0, 100 - Math.round(riskScore * 0.72)),
      responsePressure,
      primaryDrivers: Array.from(new Set(districtIncidents.map((incident) => incident.issueType.replaceAll("_", " ")))).slice(0, 3),
      forecastWindowHours: 24,
      updatedAt: nowIso()
    };
  });
}

export function calculateCityRiskAverage(forecasts: DistrictRiskForecast[]) {
  if (forecasts.length === 0) {
    return 0;
  }

  return Math.round(forecasts.reduce((sum, forecast) => sum + forecast.riskScore, 0) / forecasts.length);
}
