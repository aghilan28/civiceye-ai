"use client";

import { CitySimulation } from "@/components/demo/city-simulation";
import { ExecutiveImpact } from "@/components/demo/executive-impact";
import { GuidedDemoPanel } from "@/components/demo/guided-demo-panel";
import { IncidentReplay } from "@/components/demo/incident-replay";
import { OperationsCopilot } from "@/components/demo/operations-copilot";
import { PageHeader } from "@/components/product/page-header";
import { ConnectionHealth } from "@/components/realtime/connection-health";
import { useLiveOperations } from "@/hooks/use-live-operations";
import { useRealtimeIntelligence } from "@/hooks/use-realtime-intelligence";
import { useAppStore } from "@/store/use-app-store";

export default function DemoPage() {
  useLiveOperations();
  useRealtimeIntelligence();
  const presentationMode = useAppStore((state) => state.presentationMode);

  return (
    <section className={`safe-x py-8 sm:py-12 ${presentationMode ? "min-h-screen bg-civic-bg" : ""}`}>
      <div className="mx-auto max-w-7xl">
        <PageHeader
          eyebrow="Executive demo"
          title="CivicEye live city simulation"
          description="Run guided municipal scenarios with realtime events, AI narration, incident replay, and executive impact storytelling."
          action={<ConnectionHealth />}
        />
        <div className="mt-8 grid gap-5 xl:grid-cols-[1fr_0.44fr]">
          <div className="grid gap-5">
            <CitySimulation />
            <IncidentReplay />
          </div>
          <div className="grid gap-5">
            <GuidedDemoPanel />
            <OperationsCopilot />
            <ExecutiveImpact />
          </div>
        </div>
      </div>
    </section>
  );
}
