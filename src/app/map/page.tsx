"use client";

import { OperationalMap } from "@/components/maps/operational-map";
import { ConnectionHealth } from "@/components/realtime/connection-health";
import { RiskForecastPanel } from "@/components/realtime/risk-forecast-panel";
import { FieldResponsePanel } from "@/components/realtime/field-response-panel";
import { PageHeader } from "@/components/product/page-header";
import { SyncStatusPill } from "@/components/product/sync-status-pill";
import { useLiveOperations } from "@/hooks/use-live-operations";
import { useRealtimeIntelligence } from "@/hooks/use-realtime-intelligence";
import { useAppStore } from "@/store/use-app-store";

export default function MapPage() {
  useLiveOperations();
  useRealtimeIntelligence();
  const incidents = useAppStore((state) => state.incidents);
  const forecasts = useAppStore((state) => state.riskForecasts);
  const fieldTeams = useAppStore((state) => state.fieldTeams);

  return (
    <section className="safe-x py-8 sm:py-12">
      <div className="mx-auto max-w-7xl">
        <PageHeader
          eyebrow="Digital twin"
          title="Live smart-city map"
          description="Realtime issue markers, predictive risk zones, field response movement, and severity heat layers for municipal command."
          action={
            <div className="flex flex-wrap gap-3">
              <ConnectionHealth />
              <SyncStatusPill />
            </div>
          }
        />
        <div className="mt-8 grid gap-5 xl:grid-cols-[1fr_0.42fr]">
          <OperationalMap incidents={incidents} forecasts={forecasts} fieldTeams={fieldTeams} />
          <div className="grid gap-5">
            <RiskForecastPanel />
            <FieldResponsePanel />
          </div>
        </div>
      </div>
    </section>
  );
}
