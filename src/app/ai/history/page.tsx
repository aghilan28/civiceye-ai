"use client";

import { AiCommandShell } from "@/components/ai/ai-command-shell";
import { AiHealthPanel } from "@/components/ai/ai-health-panel";

export default function AiHistoryPage() {
  return (
    <AiCommandShell>
      <div className="grid gap-5 lg:grid-cols-[0.7fr_0.3fr]">
        <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-5 backdrop-blur-2xl">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Detection archive</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Backend job history</h2>
          <p className="mt-4 text-sm leading-6 text-slate-400">
            Video job records are persisted by the FastAPI service under the configured runtime storage directory as processed videos and JSON detection logs. Upload a video in the operations tab to generate a real job record backed by YOLO detections.
          </p>
        </div>
        <AiHealthPanel />
      </div>
    </AiCommandShell>
  );
}

