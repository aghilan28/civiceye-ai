"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, BrainCircuit, Gauge, RadioTower } from "lucide-react";
import { enterpriseApi } from "@/services/enterprise/enterprise-api";
import type { IntelligenceSnapshot, ModelRegistryEntry } from "@/types/enterprise";

type EnterpriseIntelligencePanelProps = {
  mode: "executive" | "infrastructure" | "districts" | "predictions" | "emergency";
};

export function EnterpriseIntelligencePanel({ mode }: EnterpriseIntelligencePanelProps) {
  const [snapshot, setSnapshot] = useState<IntelligenceSnapshot | null>(null);
  const [models, setModels] = useState<ModelRegistryEntry[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([enterpriseApi.intelligenceSnapshot(controller.signal), enterpriseApi.modelRegistry(controller.signal)])
      .then(([intelligence, registry]) => {
        setSnapshot(intelligence);
        setModels(registry);
        setState("ready");
      })
      .catch(() => setState("error"));
    const connection = enterpriseApi.connectEvents((event) => {
      if (event.type === "AI_detection_received" || event.type === "emergency_alert" || event.type === "model_registry_updated" || event.type === "incident_updated") {
        enterpriseApi.intelligenceSnapshot().then(setSnapshot).catch(() => undefined);
        enterpriseApi.modelRegistry().then(setModels).catch(() => undefined);
      }
    });
    return () => {
      controller.abort();
      connection.close();
    };
  }, []);

  if (state === "loading") {
    return <div className="rounded-lg border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-300">Loading autonomous civic intelligence from persisted telemetry.</div>;
  }

  if (state === "error" || !snapshot) {
    return <div className="rounded-lg border border-rose-300/20 bg-rose-500/10 p-5 text-sm text-rose-100">Enterprise intelligence APIs are unavailable. Start FastAPI with PostgreSQL/PostGIS to activate this surface.</div>;
  }

  if (mode === "emergency") {
    return (
      <div className="grid gap-4 lg:grid-cols-[0.38fr_0.62fr]">
        <Metric icon={AlertTriangle} label="Open emergencies" value={snapshot.emergency_events.length} />
        <Records title="Emergency coordination" rows={snapshot.emergency_events} empty="No active disaster response events." />
      </div>
    );
  }

  if (mode === "predictions") {
    return (
      <div className="grid gap-4 lg:grid-cols-[0.38fr_0.62fr]">
        <Metric icon={BrainCircuit} label="Prediction horizon" value={`${snapshot.predictions.length}`} />
        <Records title="Predictive risk engine" rows={snapshot.predictions} empty="No prediction snapshots have been persisted yet." />
      </div>
    );
  }

  if (mode === "infrastructure") {
    return (
      <div className="grid gap-4 xl:grid-cols-3">
        {models.map((model) => (
          <div key={model.id} className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white">{model.model_type.replaceAll("_", " ")}</h2>
              <span className={model.active ? "text-xs font-semibold text-emerald-300" : "text-xs text-slate-500"}>{model.active ? "active" : "standby"}</span>
            </div>
            <p className="mt-2 text-sm text-slate-400">{model.version} · {model.deployment_target.replaceAll("_", " ")}</p>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <span className="text-slate-500">P95</span>
              <span className="text-right text-white">{model.latency_p95_ms}ms</span>
              <span className="text-slate-500">Edge</span>
              <span className="text-right text-white">{model.edge_compatible ? "compatible" : "cloud only"}</span>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[0.34fr_0.66fr]">
      <div className="grid gap-3">
        <Metric icon={Gauge} label="City health" value={`${snapshot.city_health_score}%`} />
        <Metric icon={RadioTower} label="Websocket clients" value={String(snapshot.websocket_health.connected_clients ?? 0)} />
        <Metric icon={BrainCircuit} label="Registered models" value={String(models.length)} />
      </div>
      <div className="grid gap-4">
        <Records title="Operational agents" rows={snapshot.agent_recommendations} empty="No agent recommendations yet." />
        <Records title="Queue pressure" rows={[snapshot.queue_pressure]} empty="No queued inference jobs." />
      </div>
    </div>
  );
}

function Metric({ icon: Icon, label, value }: { icon: typeof Gauge; label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">{label}</span>
        <Icon className="size-5 text-cyan-300" />
      </div>
      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
    </div>
  );
}

function Records({ title, rows, empty }: { title: string; rows: Array<Record<string, unknown>>; empty: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
      <h2 className="text-lg font-semibold text-white">{title}</h2>
      <div className="mt-4 grid gap-3">
        {rows.length === 0 ? <p className="text-sm text-slate-400">{empty}</p> : null}
        {rows.slice(0, 8).map((row, index) => (
          <pre key={index} className="max-h-40 overflow-auto rounded-md border border-white/10 bg-black/30 p-3 text-xs leading-5 text-slate-300">
            {JSON.stringify(row, null, 2)}
          </pre>
        ))}
      </div>
    </div>
  );
}
