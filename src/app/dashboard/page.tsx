"use client";

import dynamic from "next/dynamic";
import { Activity, AlertTriangle, BarChart3, BrainCircuit, RadioTower } from "lucide-react";
import { ExecutiveImpact } from "@/components/demo/executive-impact";
import { OperationsCopilot } from "@/components/demo/operations-copilot";
import { ConnectionHealth } from "@/components/realtime/connection-health";
import { FieldResponsePanel } from "@/components/realtime/field-response-panel";
import { InfrastructureHealthPanel } from "@/components/realtime/infrastructure-health-panel";
import { LiveEventStream } from "@/components/realtime/live-event-stream";
import { RiskForecastPanel } from "@/components/realtime/risk-forecast-panel";
import { IncidentCard } from "@/components/product/incident-card";
import { OperationalSkeleton } from "@/components/product/operational-skeleton";
import { PageHeader } from "@/components/product/page-header";
import { SyncStatusPill } from "@/components/product/sync-status-pill";
import { TelemetryCard } from "@/components/product/telemetry-card";
import { Button } from "@/components/ui/button";
import { useLiveOperations } from "@/hooks/use-live-operations";
import { useRealtimeIntelligence } from "@/hooks/use-realtime-intelligence";
import { useAppStore } from "@/store/use-app-store";

const OperationalMap = dynamic(() => import("@/components/maps/operational-map").then((module) => module.OperationalMap), {
  ssr: false,
  loading: () => (
    <div className="min-h-[34rem] rounded-[2rem] border border-white/10 bg-white/[0.045] p-5 backdrop-blur-2xl">
      <OperationalSkeleton rows={4} />
    </div>
  )
});

export default function DashboardPage() {
  useLiveOperations();
  useRealtimeIntelligence();
  const incidents = useAppStore((state) => state.incidents);
  const liveTelemetry = useAppStore((state) => state.liveTelemetry);
  const loading = useAppStore((state) => state.loading.dashboard);
  const activeIncidents = liveTelemetry?.activeIncidents ?? incidents.length;
  const averageRisk = liveTelemetry?.districtRiskAverage ?? 0;
  const slaWarnings = liveTelemetry?.slaWarnings ?? incidents.filter((incident) => incident.escalationLevel !== "none").length;
  const aiAnalyses = liveTelemetry?.aiAnalysesRunning ?? 0;

  return (
    <section className="safe-x py-8 sm:py-12">
      <div className="mx-auto max-w-7xl">
        <PageHeader
          eyebrow="AI operations center"
          title="Live city intelligence"
          description="Realtime incidents, predictive risk, infrastructure health, and field response coordination for municipal operations."
          action={
            <div className="flex flex-wrap gap-3">
              <ConnectionHealth />
              <SyncStatusPill />
              <Button variant="gradient">Open live map</Button>
            </div>
          }
        />

        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <TelemetryCard label="Active incidents" value={String(activeIncidents)} trend="live" icon={AlertTriangle} tone="danger" />
          <TelemetryCard label="AI analyses" value={String(aiAnalyses)} trend="running" icon={BrainCircuit} tone="cyan" />
          <TelemetryCard label="SLA warnings" value={String(slaWarnings)} trend="watch" icon={Activity} tone="purple" />
          <TelemetryCard label="District risk" value={`${averageRisk}`} trend="forecast" icon={BarChart3} tone="blue" />
        </div>

        <div className="mt-6 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="grid gap-5">
            <OperationalMap incidents={incidents} />
            <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Priority queue</p>
                  <h2 className="mt-1 text-xl font-semibold text-white">Live incident command</h2>
                </div>
                <span className="inline-flex items-center gap-2 rounded-full bg-civic-cyan/10 px-3 py-1 text-xs font-semibold text-civic-cyan">
                  <RadioTower className="size-3" />
                  streaming
                </span>
              </div>
              {loading ? (
                <OperationalSkeleton rows={3} />
              ) : (
                <div className="grid gap-3">
                  {incidents.map((incident) => (
                    <IncidentCard key={incident.id} incident={incident} />
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="grid gap-5">
            <LiveEventStream />
            <OperationsCopilot />
            <RiskForecastPanel />
            <FieldResponsePanel />
            <InfrastructureHealthPanel />
            <ExecutiveImpact />
          </div>
        </div>
      </div>
    </section>
  );
}
