import type { CivicSeverity } from "@/types/civic";
import type { CivicRealtimeEvent } from "@/types/realtime";

export type DemoScenarioId =
  | "flood_emergency"
  | "pothole_escalation"
  | "infrastructure_cascade"
  | "smart_drainage_overload"
  | "district_risk_escalation"
  | "emergency_response"
  | "city_incident_spike"
  | "predictive_prevention";

export type ScenarioStage = {
  id: string;
  timestampMs: number;
  title: string;
  narration: string;
  telemetryDelta: {
    activeIncidents: number;
    riskScore: number;
    aiAnalyses: number;
    responsePressure: number;
  };
  severity: CivicSeverity;
  eventType: CivicRealtimeEvent["type"];
};

export type DemoScenario = {
  id: DemoScenarioId;
  title: string;
  subtitle: string;
  civicImpact: string;
  durationMs: number;
  stages: ScenarioStage[];
};

export type ReplayState = {
  scenarioId: DemoScenarioId;
  playing: boolean;
  cursorMs: number;
  speed: 1 | 1.5 | 2;
};

export type CopilotInsight = {
  id: string;
  title: string;
  body: string;
  priority: "advisory" | "important" | "urgent";
  recommendedAction: string;
};
