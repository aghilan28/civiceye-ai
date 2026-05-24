"use client";

import { useEffect } from "react";
import { incidentService } from "@/services/incidents/incident-service";
import { realtimeClient } from "@/services/realtime/realtime-client";
import { useAppStore } from "@/store/use-app-store";

export function useLiveOperations() {
  const setIncidents = useAppStore((state) => state.setIncidents);
  const upsertIncident = useAppStore((state) => state.upsertIncident);
  const pushNotification = useAppStore((state) => state.pushNotification);
  const setDashboardMetrics = useAppStore((state) => state.setDashboardMetrics);
  const setLoading = useAppStore((state) => state.setLoading);

  useEffect(() => {
    let active = true;
    setLoading({ dashboard: true });

    incidentService
      .listIncidents()
      .then((incidents) => {
        if (active) {
          setIncidents(incidents);
        }
      })
      .finally(() => {
        if (active) {
          setLoading({ dashboard: false });
        }
      });

    const subscription = realtimeClient.subscribe((event) => {
      if (event.type === "incident.created" || event.type === "incident.updated") {
        upsertIncident(event.incident);
      }

      if (event.type === "notification.created") {
        pushNotification(event.notification);
      }

      if (event.type === "telemetry.updated") {
        setDashboardMetrics(event.metrics);
      }
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, [pushNotification, setDashboardMetrics, setIncidents, setLoading, upsertIncident]);
}
