"use client";

import { AiCommandShell } from "@/components/ai/ai-command-shell";
import { AiHealthPanel } from "@/components/ai/ai-health-panel";
import { aiBackendClient } from "@/services/ai/backend-client";

export default function AiSettingsPage() {
  return (
    <AiCommandShell>
      <div className="grid gap-5 lg:grid-cols-[0.7fr_0.3fr]">
        <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-5 backdrop-blur-2xl">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Runtime configuration</p>
          <h2 className="mt-1 text-xl font-semibold text-white">AI backend endpoint</h2>
          <div className="mt-5 rounded-xl border border-white/10 bg-black/25 p-4">
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">NEXT_PUBLIC_AI_BACKEND_URL</p>
            <p className="mt-2 break-all text-sm font-semibold text-white">{aiBackendClient.baseUrl}</p>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-400">
            Model weights, GPU device selection, confidence threshold, frame skip, batch size, CORS origins, and runtime storage are controlled by backend environment variables. The UI reads live health from `/health` and JSON runtime telemetry from `/runtime/metrics`.
          </p>
        </div>
        <AiHealthPanel />
      </div>
    </AiCommandShell>
  );
}
