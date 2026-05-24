import { env } from "@/config/env";
import { apiClient } from "@/services/api/client";
import { tokenVault } from "@/services/security/token-vault";
import type {
  CopilotRecommendation,
  EnterpriseOperationsEvent,
  FieldTask,
  IntelligenceSnapshot,
  MapIntelligence,
  ModelRegistryEntry,
  TenantProvisionRequest,
  TenantProvisionResponse
} from "@/types/enterprise";

const defaultMunicipalityId = process.env.NEXT_PUBLIC_MUNICIPALITY_ID ?? "MUNI-BLR";

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  return apiClient.get<T>(path, signal);
}

function eventSocketUrl() {
  const wsBase = env.realtimeUrl || env.apiBaseUrl.replace(/^http/, "ws");
  const base = wsBase.endsWith("/operations/events") ? wsBase : `${wsBase}/operations/events`;
  const url = new URL(base);
  url.searchParams.set("municipality_id", defaultMunicipalityId);
  url.searchParams.set("channels", "municipal-operations,tenant.operations,tenant.ai,emergency");
  const token = tokenVault.getAccessToken();
  if (token) {
    url.searchParams.set("token", token);
  }
  return url.toString();
}

export const enterpriseApi = {
  municipalityId: defaultMunicipalityId,

  mapIntelligence(signal?: AbortSignal) {
    return getJson<MapIntelligence>(`/operations/map/intelligence?municipality_id=${encodeURIComponent(defaultMunicipalityId)}`, signal);
  },

  intelligenceSnapshot(signal?: AbortSignal) {
    return getJson<IntelligenceSnapshot>(`/intelligence/snapshot?municipality_id=${encodeURIComponent(defaultMunicipalityId)}`, signal);
  },

  modelRegistry(signal?: AbortSignal) {
    return getJson<ModelRegistryEntry[]>(`/ai/models?municipality_id=${encodeURIComponent(defaultMunicipalityId)}`, signal);
  },

  modelBenchmarks(signal?: AbortSignal) {
    return getJson<Array<Record<string, unknown>>>(`/ai/models/benchmarks`, signal);
  },

  orchestrationTelemetry(signal?: AbortSignal) {
    return getJson<Record<string, unknown>>(`/ai/orchestration/telemetry`, signal);
  },

  fieldTasks(fieldWorkerId?: string, signal?: AbortSignal) {
    const worker = fieldWorkerId ? `&field_worker_id=${encodeURIComponent(fieldWorkerId)}` : "";
    return getJson<FieldTask[]>(`/field/tasks?municipality_id=${encodeURIComponent(defaultMunicipalityId)}${worker}`, signal);
  },

  provisionTenant(payload: TenantProvisionRequest) {
    return apiClient.post<TenantProvisionResponse, TenantProvisionRequest>("/tenants/provision", payload);
  },

  copilot(payload: { municipality_id: string; incident_id?: string | null; agent_names?: string[] }) {
    return apiClient.post<{ municipality_id: string; recommendations: CopilotRecommendation[]; autonomous_actions: Array<Record<string, unknown>>; updated_at: string }, typeof payload>(
      "/copilot/recommendations",
      payload
    );
  },

  invoice(municipalityId = defaultMunicipalityId) {
    return getJson(`/billing/invoice?municipality_id=${encodeURIComponent(municipalityId)}`);
  },

  connectEvents(onEvent: (event: EnterpriseOperationsEvent) => void) {
    const socket = new WebSocket(eventSocketUrl());
    socket.addEventListener("message", (message) => {
      try {
        onEvent(JSON.parse(message.data) as EnterpriseOperationsEvent);
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
