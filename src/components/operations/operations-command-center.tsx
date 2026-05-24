"use client";

import type { ComponentType } from "react";
import { useEffect, useMemo, useState } from "react";
import { BarChart3, Clock, Droplets, Gauge, MapPin, RadioTower, ShieldAlert, Wrench } from "lucide-react";
import { EmptyOperationsState } from "@/components/operations/operations-shell";
import { GlassPanel } from "@/components/ui/glass-panel";
import { showcaseAnalytics, showcaseIncidents, showcaseMapIntelligence } from "@/data/showcase";
import { operationsApi, severityTone } from "@/services/operations/operations-api";
import type { OperationsAnalytics, OperationsIncident } from "@/types/phase3";

type LoadState = "loading" | "ready" | "error";

export function OperationsCommandCenter({ mode }: { mode: "live" | "incidents" | "analytics" | "departments" | "field" }) {
  const [incidents, setIncidents] = useState<OperationsIncident[]>(showcaseIncidents);
  const [analytics, setAnalytics] = useState<OperationsAnalytics | null>(showcaseAnalytics);
  const [state, setState] = useState<LoadState>("loading");
  const [eventCount, setEventCount] = useState(12);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([operationsApi.listIncidents(controller.signal), operationsApi.getAnalytics(controller.signal)])
      .then(([incidentRows, analyticsSnapshot]) => {
        setIncidents(incidentRows.length ? incidentRows : showcaseIncidents);
        setAnalytics(analyticsSnapshot ?? showcaseAnalytics);
        setState("ready");
      })
      .catch(() => {
        setIncidents(showcaseIncidents);
        setAnalytics(showcaseAnalytics);
        setState("ready");
      });

    const connection = operationsApi.connectEvents((event) => {
      if (event.type === "incident_created") {
        setIncidents((current) => [event.incident, ...current.filter((item) => item.incident_id !== event.incident.incident_id)]);
        setEventCount((count) => count + 1);
      }
      if (event.type === "incident_updated") {
        setIncidents((current) => current.map((item) => (item.incident_id === event.incident.incident_id ? event.incident : item)));
        setEventCount((count) => count + 1);
      }
    });

    return () => {
      controller.abort();
      connection.close();
    };
  }, []);

  const activeRepairs = useMemo(() => incidents.filter((incident) => ["ASSIGNED", "IN_PROGRESS", "TEMPORARY_FIX"].includes(incident.status)), [incidents]);
  const riskDistricts = useMemo(() => analytics?.district_risk ?? showcaseAnalytics.district_risk, [analytics]);

  if (state === "loading") {
    return <EmptyOperationsState title="Connecting to civic operations" body="Loading incidents, district risk, and repair activity into the command center." />;
  }

  if (mode === "analytics") {
    return (
      <div className="grid gap-4 lg:grid-cols-[0.7fr_1fr]">
        <MetricGrid analytics={analytics} incidents={incidents} eventCount={eventCount} />
        <div className="grid gap-4">
          <GlassPanel glow="cyan" className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">District risk</p>
                <h2 className="mt-1 text-lg font-semibold text-white">Degradation scoring</h2>
              </div>
              <Gauge className="size-5 text-civic-cyan" />
            </div>
            <div className="mt-4 grid gap-3">
              {riskDistricts.map((district) => (
                <div key={district.id} className="rounded-2xl border border-white/10 bg-black/20 p-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold text-white">{district.name}</span>
                    <span className="text-civic-cyan">{Math.round(district.risk_score)} risk</span>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
                    <div className="h-full rounded-full bg-gradient-to-r from-civic-blue to-civic-cyan" style={{ width: `${Math.min(100, district.risk_score)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </GlassPanel>
          <GlassPanel glow="purple" className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Worker telemetry</p>
                <h2 className="mt-1 text-lg font-semibold text-white">GPU and queue health</h2>
              </div>
              <MapPin className="size-5 text-civic-purple" />
            </div>
            <div className="mt-4 grid gap-2">
              {showcaseMapIntelligence.worker_telemetry.map((worker) => (
                <div key={String(worker.id)} className="rounded-2xl border border-white/10 bg-white/[0.04] p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-white">{String(worker.id)}</span>
                    <span className="rounded-full bg-white/10 px-2 py-1 text-xs text-slate-300">{String(worker.status)}</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-400">
                    {String(worker.queue)} - {String(worker.fps)} FPS
                  </p>
                </div>
              ))}
            </div>
          </GlassPanel>
        </div>
      </div>
    );
  }

  if (mode === "departments") {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {["ROADS", "DRAINAGE", "UTILITIES", "SMART_INFRASTRUCTURE"].map((department) => {
          const owned = incidents.filter((incident) => incident.assigned_department === department);
          return (
            <div key={department} className="rounded-3xl border border-white/10 bg-white/[0.045] p-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">{department.replace("_", " ")}</h2>
                <Wrench className="size-5 text-civic-cyan" />
              </div>
              <p className="mt-4 text-4xl font-semibold text-white">{owned.length}</p>
              <p className="mt-1 text-sm text-slate-400">open assigned incidents</p>
              <p className="mt-4 text-sm leading-6 text-slate-400">Capacity, severity, geography, and SLA pressure are weighted into the queue view.</p>
            </div>
          );
        })}
      </div>
    );
  }

  if (mode === "field") {
    const tasks = activeRepairs.length > 0 ? activeRepairs : incidents.filter((incident) => incident.status === "VERIFIED");
    return (
      <div className="grid gap-3">
        {tasks.map((incident) => (
          <IncidentRow key={incident.incident_id} incident={incident} compact />
        ))}
        {tasks.length === 0 ? <EmptyOperationsState title="No field tasks assigned" body="Verified or assigned incidents will appear here after the assignment engine creates repair work." /> : null}
      </div>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[0.38fr_0.62fr]">
      <MetricGrid analytics={analytics} incidents={incidents} eventCount={eventCount} />
      <div className="grid gap-3">
        {incidents.slice(0, 5).map((incident) => (
          <IncidentRow key={incident.incident_id} incident={incident} />
        ))}
      </div>
    </div>
  );
}

function MetricGrid({ analytics, incidents, eventCount }: { analytics: OperationsAnalytics | null; incidents: OperationsIncident[]; eventCount: number }) {
  const severity = analytics?.severity_distribution ?? {};
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
      <Metric icon={ShieldAlert} label="Active incidents" value={String(analytics?.active_incidents ?? incidents.length)} />
      <Metric icon={Clock} label="Realtime events" value={String(eventCount)} />
      <Metric icon={RadioTower} label="Critical severity" value={String(severity.CRITICAL ?? 0)} />
      <Metric icon={Wrench} label="Completion rate" value={`${Math.round((analytics?.repair_completion_rate ?? 0) * 100)}%`} />
      <Metric icon={Droplets} label="Average SLA" value={`${analytics?.average_sla_hours ?? 0} h`} />
      <Metric icon={BarChart3} label="Recurrence" value={`${Math.round((analytics?.recurrence_rate ?? 0) * 100)}%`} />
    </div>
  );
}

function Metric({ icon: Icon, label, value }: { icon: ComponentType<{ className?: string }>; label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-slate-400">{label}</p>
        <Icon className="size-5 text-civic-cyan" />
      </div>
      <p className="mt-3 text-4xl font-semibold text-white">{value}</p>
    </div>
  );
}

function IncidentRow({ incident, compact = false }: { incident: OperationsIncident; compact?: boolean }) {
  const dueMs = new Date(incident.sla_due_at).getTime() - Date.now();
  const dueHours = Math.max(0, Math.round(dueMs / 3600000));
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${severityTone(incident.severity)}`}>{incident.severity}</span>
            <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-slate-300">{incident.status.replace("_", " ")}</span>
            <span className="text-xs text-slate-500">{incident.incident_code}</span>
          </div>
          <h2 className="mt-3 text-lg font-semibold text-white">{incident.road_name ?? "Unmapped road segment"}</h2>
          <p className="mt-1 flex items-center gap-2 text-sm text-slate-400">
            <MapPin className="size-4" />
            {incident.latitude.toFixed(5)}, {incident.longitude.toFixed(5)} - {incident.geohash}
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 text-right sm:min-w-60">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">SLA</p>
            <p className="mt-1 text-lg font-semibold text-white">{dueHours}h</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">AI</p>
            <p className="mt-1 text-lg font-semibold text-white">{Math.round(incident.confidence * 100)}%</p>
          </div>
        </div>
      </div>
      {!compact ? <div className="mt-4 h-px bg-white/10" /> : null}
    </div>
  );
}
