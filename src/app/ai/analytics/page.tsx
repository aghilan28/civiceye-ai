"use client";

import { AiCommandShell } from "@/components/ai/ai-command-shell";
import { AiHealthPanel } from "@/components/ai/ai-health-panel";
import { useAiBackendHealth } from "@/hooks/ai/use-ai-backend-health";

export default function AiAnalyticsPage() {
  const { metrics } = useAiBackendHealth();

  return (
    <AiCommandShell>
      <div className="grid gap-5 lg:grid-cols-[1fr_0.42fr]">
        <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-5 backdrop-blur-2xl">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">MLOps telemetry</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Inference performance</h2>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(metrics?.inference ?? {}).map(([key, value]) => (
              <div key={key} className="rounded-xl border border-white/10 bg-black/25 p-4">
                <p className="text-xs uppercase tracking-[0.12em] text-slate-500">{key.replaceAll("_", " ")}</p>
                <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
              </div>
            ))}
          </div>
        </div>
        <AiHealthPanel />
      </div>
    </AiCommandShell>
  );
}

