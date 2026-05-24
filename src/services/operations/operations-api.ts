import { env } from "@/config/env";
import { apiClient } from "@/services/api/client";
import { tokenVault } from "@/services/security/token-vault";
import type { OperationsAnalytics, OperationsEvent, OperationsIncident } from "@/types/phase3";

const defaultMunicipalityId = process.env.NEXT_PUBLIC_MUNICIPALITY_ID ?? "MUNI-BLR";

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  return apiClient.get<T>(path, signal);
}

async function sendJson<T>(path: string, method: "POST" | "PATCH", body: unknown, signal?: AbortSignal): Promise<T> {
  return method === "POST" ? apiClient.post<T>(path, body, signal) : apiClient.patch<T>(path, body, signal);
}

function eventSocketUrl(channels: string[] = ["municipal-operations"]) {
  const wsBase = env.realtimeUrl || env.apiBaseUrl.replace(/^http/, "ws");
  const base = wsBase.endsWith("/operations/events") ? wsBase : `${wsBase}/operations/events`;
  const url = new URL(base);
  url.searchParams.set("municipality_id", defaultMunicipalityId);
  url.searchParams.set("channels", channels.join(","));
  const token = tokenVault.getAccessToken();
  if (token) {
    url.searchParams.set("token", token);
  }
  return url.toString();
}

export const operationsApi = {
  municipalityId: defaultMunicipalityId,

  listIncidents(signal?: AbortSignal) {
    return getJson<OperationsIncident[]>(`/operations/incidents?municipality_id=${encodeURIComponent(defaultMunicipalityId)}`, signal);
  },

  createIncident(payload: unknown, signal?: AbortSignal) {
    return sendJson<OperationsIncident>("/operations/incidents", "POST", payload, signal);
  },

  transitionIncident(incidentId: string, payload: unknown, signal?: AbortSignal) {
    return sendJson<OperationsIncident>(`/operations/incidents/${encodeURIComponent(incidentId)}/status`, "PATCH", payload, signal);
  },

  getAnalytics(signal?: AbortSignal) {
    return getJson<OperationsAnalytics>(`/operations/analytics?municipality_id=${encodeURIComponent(defaultMunicipalityId)}`, signal);
  },

  connectEvents(onEvent: (event: OperationsEvent) => void) {
    const socket = new WebSocket(eventSocketUrl());
    socket.addEventListener("message", (message) => {
      try {
        onEvent(JSON.parse(message.data) as OperationsEvent);
      } catch {
        return;
      }
    });
    const heartbeat = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "ping" }));
      }
    }, 25000);
    return {
      close() {
        window.clearInterval(heartbeat);
        socket.close();
      }
    };
  }
};

export function severityTone(severity: OperationsIncident["severity"]) {
  const map: Record<OperationsIncident["severity"], string> = {
    LOW: "text-emerald-300 bg-emerald-400/10 border-emerald-300/20",
    MEDIUM: "text-amber-300 bg-amber-400/10 border-amber-300/20",
    HIGH: "text-sky-300 bg-sky-400/10 border-sky-300/20",
    CRITICAL: "text-rose-300 bg-rose-400/10 border-rose-300/20"
  };
  return map[severity];
}
