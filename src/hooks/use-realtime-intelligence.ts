"use client";

import { useEffect, useMemo, useRef } from "react";
import { buildRiskForecasts, calculateCityRiskAverage, calculateInfrastructureHealth } from "@/services/analytics/risk-engine";
import { buildFieldTeams } from "@/services/field/field-response-service";
import { civicEventBus } from "@/services/realtime/event-bus";
import { CivicWebSocketClient } from "@/services/realtime/websocket-client";
import { createId, nowIso } from "@/lib/time";
import { useAppStore } from "@/store/use-app-store";

export function useRealtimeIntelligence() {
  const incidents = useAppStore((state) => state.incidents);
  const setRealtimeStatus = useAppStore((state) => state.setRealtimeStatus);
  const pushRealtimeEvent = useAppStore((state) => state.pushRealtimeEvent);
  const setRiskForecasts = useAppStore((state) => state.setRiskForecasts);
  const setFieldTeams = useAppStore((state) => state.setFieldTeams);
  const setLiveTelemetry = useAppStore((state) => state.setLiveTelemetry);
  const clientRef = useRef<CivicWebSocketClient | null>(null);

  const forecasts = useMemo(() => buildRiskForecasts(incidents), [incidents]);
  const fieldTeams = useMemo(() => buildFieldTeams(incidents), [incidents]);

  useEffect(() => {
    setRiskForecasts(forecasts);
    setFieldTeams(fieldTeams);
    setLiveTelemetry({
      activeIncidents: incidents.length,
      aiAnalysesRunning: Math.max(3, Math.ceil(incidents.length * 0.34)),
      fieldTeamsActive: fieldTeams.filter((team) => team.status !== "available").length,
      slaWarnings: incidents.filter((incident) => incident.escalationLevel === "sla_risk" || incident.escalationLevel === "critical").length,
      districtRiskAverage: calculateCityRiskAverage(forecasts),
      eventVelocityPerMinute: 18 + incidents.length,
      infrastructureHealth: calculateInfrastructureHealth(incidents),
      updatedAt: nowIso()
    });
  }, [fieldTeams, forecasts, incidents, setFieldTeams, setLiveTelemetry, setRiskForecasts]);

  useEffect(() => {
    const client = new CivicWebSocketClient({
      municipalityId: "MUNI-BLR",
      channels: ["city.telemetry", "incidents.live", "ai.operations", "municipality.workflow", "field.response", "risk.forecast", "system.alerts"]
    });

    clientRef.current = client;
    const statusSubscription = client.subscribeStatus(setRealtimeStatus);
    const eventSubscription = civicEventBus.subscribe("all", (event) => {
      pushRealtimeEvent(event);

      if (event.type === "TELEMETRY_REFRESH") {
        setLiveTelemetry(event.payload.telemetry);
      }

      if (event.type === "RISK_FORECAST_UPDATED") {
        setRiskForecasts(event.payload.forecasts);
      }
    });

    client.connect();

    return () => {
      statusSubscription.unsubscribe();
      eventSubscription.unsubscribe();
      client.disconnect();
      clientRef.current = null;
    };
  }, [pushRealtimeEvent, setLiveTelemetry, setRealtimeStatus, setRiskForecasts]);

  useEffect(() => {
    if (forecasts.length === 0) {
      return;
    }

    civicEventBus.publish({
      id: createId("EVT"),
      type: "RISK_FORECAST_UPDATED",
      channel: "risk.forecast",
      timestamp: nowIso(),
      municipalityId: "MUNI-BLR",
      payload: { forecasts }
    });
  }, [forecasts]);
}
