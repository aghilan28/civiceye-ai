import { demoScenarios } from "@/data/demo-scenarios";
import { createId, nowIso } from "@/lib/time";
import { civicEventBus } from "@/services/realtime/event-bus";
import type { DemoScenario, DemoScenarioId, ScenarioStage } from "@/types/demo";
import type { CivicRealtimeEvent } from "@/types/realtime";

export function getDemoScenario(id: DemoScenarioId): DemoScenario {
  return demoScenarios.find((scenario) => scenario.id === id) ?? demoScenarios[0];
}

export function stageToRealtimeEvent(stage: ScenarioStage): CivicRealtimeEvent {
  if (stage.eventType === "WEATHER_RISK_EVENT") {
    return {
      id: createId("EVT"),
      type: "WEATHER_RISK_EVENT",
      channel: "risk.forecast",
      timestamp: nowIso(),
      municipalityId: "MUNI-BLR",
      payload: { districtId: "WARD-18", rainfallMm: 68, floodRisk: stage.telemetryDelta.riskScore }
    };
  }

  if (stage.eventType === "FIELD_TEAM_ASSIGNED") {
    return {
      id: createId("EVT"),
      type: "FIELD_TEAM_ASSIGNED",
      channel: "field.response",
      timestamp: nowIso(),
      municipalityId: "MUNI-BLR",
      payload: {
        team: {
          id: "TEAM-STORMWATER-DEMO",
          name: "Stormwater Response Alpha",
          department: "stormwater",
          status: "en_route",
          assignedIncidentId: "CE-DEMO",
          etaMinutes: 9,
          routeProgress: 58,
          currentZone: "Bengaluru Zone 07"
        }
      }
    };
  }

  if (stage.eventType === "AI_ANALYSIS_COMPLETED") {
    return {
      id: createId("EVT"),
      type: "AI_ANALYSIS_COMPLETED",
      channel: "ai.operations",
      timestamp: nowIso(),
      municipalityId: "MUNI-BLR",
      payload: { incidentId: "CE-DEMO", confidence: 0.96, modelVersion: "civiceye-yolov8-primary" }
    };
  }

  if (stage.eventType === "RISK_FORECAST_UPDATED") {
    return {
      id: createId("EVT"),
      type: "RISK_FORECAST_UPDATED",
      channel: "risk.forecast",
      timestamp: nowIso(),
      municipalityId: "MUNI-BLR",
      payload: {
        forecasts: [
          {
            districtId: "WARD-18",
            districtName: "Ward 18, Bengaluru",
            riskScore: stage.telemetryDelta.riskScore,
            instabilityIndex: stage.telemetryDelta.riskScore + 4,
            recurrenceProbability: 78,
            hazardImpact: stage.telemetryDelta.responsePressure,
            citizenSafetyScore: Math.max(0, 100 - stage.telemetryDelta.riskScore),
            responsePressure: stage.telemetryDelta.responsePressure,
            primaryDrivers: ["drainage overflow", "road damage", "rainfall risk"],
            forecastWindowHours: 24,
            updatedAt: nowIso()
          }
        ]
      }
    };
  }

  if (stage.eventType === "HOTSPOT_DETECTED") {
    return {
      id: createId("EVT"),
      type: "HOTSPOT_DETECTED",
      channel: "risk.forecast",
      timestamp: nowIso(),
      municipalityId: "MUNI-BLR",
      payload: { districtId: "WARD-18", issueCount: stage.telemetryDelta.activeIncidents, severity: stage.severity }
    };
  }

  if (stage.eventType === "MUNICIPALITY_RESPONSE") {
    return {
      id: createId("EVT"),
      type: "MUNICIPALITY_RESPONSE",
      channel: "municipality.workflow",
      timestamp: nowIso(),
      municipalityId: "MUNI-BLR",
      payload: { incidentId: "CE-DEMO", department: "stormwater", action: stage.title }
    };
  }

  return {
    id: createId("EVT"),
    type: "INCIDENT_CREATED",
    channel: "incidents.live",
    timestamp: nowIso(),
    municipalityId: "MUNI-BLR",
    payload: {
      incident: {
        id: "CE-DEMO",
        issueType: "road_damage",
        severity: stage.severity,
        confidenceScore: 0.92,
        geoCoordinates: { latitude: 12.9716, longitude: 77.5946, accuracy: 8 },
        address: "Demo corridor",
        municipalityZone: "Bengaluru Zone 07",
        images: [],
        ai: {
          modelProvider: "yolov8",
          modelVersion: "demo",
          inferenceId: "INF-DEMO",
          processedAt: nowIso(),
          processingMs: 840,
          boundingRegions: [],
          geoContext: {
            wardId: "WARD-18",
            municipalityZone: "Bengaluru Zone 07",
            address: "Demo corridor",
            nearbyIncidentCount: 4,
            infrastructureDensity: 0.7,
            responseRadiusMeters: 320
          }
        },
        createdBy: { id: "DEMO", name: "Demo System", role: "operator" },
        assignedDepartment: "roads",
        lifecycleStatus: "submitted",
        escalationLevel: "watch",
        repairTimeline: { submittedAt: nowIso(), slaDueAt: nowIso() },
        verificationState: "pending",
        auditTrail: [],
        createdAt: nowIso(),
        updatedAt: nowIso()
      }
    }
  };
}

export function publishScenarioStage(stage: ScenarioStage) {
  civicEventBus.publish(stageToRealtimeEvent(stage));
}
