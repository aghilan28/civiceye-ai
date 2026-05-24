import type { DemoScenario } from "@/types/demo";

export const demoScenarios: DemoScenario[] = [
  {
    id: "flood_emergency",
    title: "Flood Emergency Simulation",
    subtitle: "Stormwater overflow, road closures, and field-team routing in a high-risk district.",
    civicImpact: "Shows how CivicEye compresses emergency detection, routing, and public response into minutes.",
    durationMs: 42000,
    stages: [
      {
        id: "flood-1",
        timestampMs: 0,
        title: "Rainfall anomaly detected",
        narration: "Weather risk enters the civic graph and raises drainage sensitivity across Ward 18.",
        telemetryDelta: { activeIncidents: 8, riskScore: 72, aiAnalyses: 4, responsePressure: 61 },
        severity: "medium",
        eventType: "WEATHER_RISK_EVENT"
      },
      {
        id: "flood-2",
        timestampMs: 9000,
        title: "Drainage overflow verified",
        narration: "YOLOv8 analysis confirms surface water accumulation with critical severity.",
        telemetryDelta: { activeIncidents: 19, riskScore: 86, aiAnalyses: 9, responsePressure: 78 },
        severity: "critical",
        eventType: "AI_ANALYSIS_COMPLETED"
      },
      {
        id: "flood-3",
        timestampMs: 22000,
        title: "Stormwater team dispatched",
        narration: "CivicEye assigns the nearest stormwater response team and starts SLA tracking.",
        telemetryDelta: { activeIncidents: 21, riskScore: 82, aiAnalyses: 6, responsePressure: 74 },
        severity: "critical",
        eventType: "FIELD_TEAM_ASSIGNED"
      },
      {
        id: "flood-4",
        timestampMs: 35000,
        title: "Escalation contained",
        narration: "Predictive spread slows as field response reaches the affected radius.",
        telemetryDelta: { activeIncidents: 15, riskScore: 64, aiAnalyses: 3, responsePressure: 46 },
        severity: "high",
        eventType: "MUNICIPALITY_RESPONSE"
      }
    ]
  },
  {
    id: "pothole_escalation",
    title: "Pothole Escalation Scenario",
    subtitle: "A citizen report becomes an AI-verified hazard and is routed by urgency.",
    civicImpact: "Demonstrates citizen-to-municipality trust and fast repair prioritization.",
    durationMs: 36000,
    stages: [
      {
        id: "pot-1",
        timestampMs: 0,
        title: "Citizen report submitted",
        narration: "A mobile report arrives with image evidence and device geolocation.",
        telemetryDelta: { activeIncidents: 5, riskScore: 48, aiAnalyses: 2, responsePressure: 34 },
        severity: "medium",
        eventType: "INCIDENT_CREATED"
      },
      {
        id: "pot-2",
        timestampMs: 10000,
        title: "Surface fracture classified",
        narration: "The AI identifies a high-confidence road hazard and recommends road maintenance.",
        telemetryDelta: { activeIncidents: 7, riskScore: 58, aiAnalyses: 5, responsePressure: 42 },
        severity: "high",
        eventType: "AI_ANALYSIS_COMPLETED"
      },
      {
        id: "pot-3",
        timestampMs: 24000,
        title: "SLA warning prevented",
        narration: "CivicEye assigns a field engineer before the corridor reaches escalation risk.",
        telemetryDelta: { activeIncidents: 6, riskScore: 41, aiAnalyses: 2, responsePressure: 28 },
        severity: "high",
        eventType: "FIELD_TEAM_ASSIGNED"
      }
    ]
  },
  {
    id: "infrastructure_cascade",
    title: "Infrastructure Failure Cascade",
    subtitle: "Road damage, water leakage, and sanitation pressure combine into district risk.",
    civicImpact: "Shows how the platform reasons across departments instead of treating reports as isolated tickets.",
    durationMs: 45000,
    stages: [
      {
        id: "cas-1",
        timestampMs: 0,
        title: "Cross-system instability begins",
        narration: "Multiple asset classes degrade inside the same service radius.",
        telemetryDelta: { activeIncidents: 24, riskScore: 76, aiAnalyses: 11, responsePressure: 72 },
        severity: "high",
        eventType: "HOTSPOT_DETECTED"
      },
      {
        id: "cas-2",
        timestampMs: 18000,
        title: "Department overload forecast",
        narration: "The predictive model flags roads and water teams as nearing capacity.",
        telemetryDelta: { activeIncidents: 31, riskScore: 88, aiAnalyses: 13, responsePressure: 89 },
        severity: "critical",
        eventType: "RISK_FORECAST_UPDATED"
      },
      {
        id: "cas-3",
        timestampMs: 34000,
        title: "Regional coordination activated",
        narration: "CivicEye recommends cross-department routing and executive visibility.",
        telemetryDelta: { activeIncidents: 22, riskScore: 66, aiAnalyses: 6, responsePressure: 55 },
        severity: "high",
        eventType: "MUNICIPALITY_RESPONSE"
      }
    ]
  },
  {
    id: "predictive_prevention",
    title: "Predictive Maintenance Prevention",
    subtitle: "AI identifies a recurring drainage risk before citizen reports spike.",
    civicImpact: "Communicates the shift from reactive complaint handling to preventive city operations.",
    durationMs: 39000,
    stages: [
      {
        id: "pre-1",
        timestampMs: 0,
        title: "Recurring hotspot detected",
        narration: "CivicEye sees a pattern from historical incidents and rainfall sensitivity.",
        telemetryDelta: { activeIncidents: 11, riskScore: 69, aiAnalyses: 4, responsePressure: 39 },
        severity: "medium",
        eventType: "HOTSPOT_DETECTED"
      },
      {
        id: "pre-2",
        timestampMs: 16000,
        title: "Preventive dispatch recommended",
        narration: "The copilot recommends clearing drainage before the next high-rainfall window.",
        telemetryDelta: { activeIncidents: 9, riskScore: 52, aiAnalyses: 2, responsePressure: 31 },
        severity: "medium",
        eventType: "RISK_FORECAST_UPDATED"
      },
      {
        id: "pre-3",
        timestampMs: 30000,
        title: "Incident spike avoided",
        narration: "The district risk curve drops as maintenance begins before citizen impact.",
        telemetryDelta: { activeIncidents: 5, riskScore: 28, aiAnalyses: 1, responsePressure: 18 },
        severity: "low",
        eventType: "MUNICIPALITY_RESPONSE"
      }
    ]
  }
];
