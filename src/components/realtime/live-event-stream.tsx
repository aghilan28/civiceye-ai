"use client";

import { motion } from "framer-motion";
import { AlertTriangle, BrainCircuit, CheckCircle2, CloudLightning, RadioTower, Route, UsersRound } from "lucide-react";
import type { CivicRealtimeEvent } from "@/types/realtime";
import { useAppStore } from "@/store/use-app-store";

const iconMap: Record<CivicRealtimeEvent["type"], typeof RadioTower> = {
  INCIDENT_CREATED: AlertTriangle,
  INCIDENT_ESCALATED: CloudLightning,
  INCIDENT_RESOLVED: CheckCircle2,
  AI_ANALYSIS_COMPLETED: BrainCircuit,
  MUNICIPALITY_RESPONSE: UsersRound,
  FIELD_TEAM_ASSIGNED: Route,
  SLA_WARNING: CloudLightning,
  RISK_FORECAST_UPDATED: BrainCircuit,
  HOTSPOT_DETECTED: AlertTriangle,
  TELEMETRY_REFRESH: RadioTower,
  SYSTEM_ALERT: AlertTriangle,
  WEATHER_RISK_EVENT: CloudLightning,
  emergency_alert: CloudLightning,
  tenant_provisioned: UsersRound
};

function eventTitle(event: CivicRealtimeEvent) {
  return event.type.replaceAll("_", " ").toLowerCase();
}

function eventBody(event: CivicRealtimeEvent) {
  if (event.type === "TELEMETRY_REFRESH") {
    return `${event.payload.telemetry.activeIncidents} active incidents, ${event.payload.telemetry.aiAnalysesRunning} AI analyses running`;
  }

  if (event.type === "RISK_FORECAST_UPDATED") {
    return `${event.payload.forecasts.length} district risk forecasts refreshed`;
  }

  if (event.type === "SYSTEM_ALERT") {
    return event.payload.body;
  }

  if (event.payload && "incidentId" in event.payload) {
    return `Incident ${event.payload.incidentId} updated by live operations`;
  }

  return "Realtime city intelligence event received";
}

export function LiveEventStream() {
  const events = useAppStore((state) => state.realtimeEvents);

  return (
    <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Realtime stream</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Operational event feed</h2>
        </div>
        <span className="rounded-full bg-civic-cyan/10 px-3 py-1 text-xs font-semibold text-civic-cyan">{events.length} events</span>
      </div>
      <div className="grid max-h-[28rem] gap-3 overflow-hidden">
        {events.slice(0, 8).map((event, index) => {
          const Icon = iconMap[event.type];
          const timestamp = event.timestamp ?? new Date().toISOString();
          return (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: 18, filter: "blur(8px)" }}
              animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              transition={{ duration: 0.35, delay: index * 0.02 }}
              className="flex items-center gap-3 rounded-2xl border border-white/10 bg-civic-bg/58 p-3"
            >
              <span className="grid size-10 shrink-0 place-items-center rounded-2xl bg-civic-cyan/10">
                <Icon className="size-5 text-civic-cyan" />
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold capitalize text-white">{eventTitle(event)}</p>
                <p className="truncate text-xs text-slate-400">{eventBody(event)}</p>
              </div>
              <span className="ml-auto shrink-0 text-[11px] text-slate-500">{new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
