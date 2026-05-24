"use client";

import { Cpu, RadioTower, ServerCrash, Zap } from "lucide-react";
import { demoImagePrediction } from "@/data/showcase";
import { useAiBackendHealth } from "@/hooks/ai/use-ai-backend-health";

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-black/20 p-3">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

export function AiHealthPanel() {
  const { health, metrics, error } = useAiBackendHealth();
  const connected = !error && health?.status === "ok";
  const model = metrics?.model;
  const fallbackLatency = demoImagePrediction.telemetry.latency_ms;

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">AI health</p>
          <h2 className="mt-1 text-lg font-semibold text-white">Inference backend</h2>
        </div>
        <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${connected ? "bg-civic-success/10 text-civic-success" : "bg-civic-danger/10 text-civic-danger"}`}>
          {connected ? <RadioTower className="size-3.5" /> : <ServerCrash className="size-3.5" />}
          {connected ? "online" : "offline"}
        </span>
      </div>
      {error ? <p className="mt-4 rounded-xl border border-civic-danger/20 bg-civic-danger/10 p-3 text-sm text-civic-danger">{error}</p> : null}
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Metric label="Device" value={health?.device ?? "demo GPU worker"} />
        <Metric label="CUDA" value={health?.cuda_available ? "available" : "demo fallback"} />
        <Metric label="Latency avg" value={`${metrics?.inference.latency_avg_ms ?? fallbackLatency} ms`} />
        <Metric label="P95 latency" value={`${metrics?.inference.latency_p95_ms ?? 0} ms`} />
        <Metric label="GPU" value={String(model?.gpu_name ?? demoImagePrediction.telemetry.gpu_name)} />
        <Metric label="VRAM" value={`${model?.vram_used_mb ?? demoImagePrediction.telemetry.vram_used_mb} / ${model?.vram_total_mb ?? demoImagePrediction.telemetry.vram_total_mb} MB`} />
      </div>
      <div className="mt-4 flex items-center gap-2 rounded-xl border border-civic-cyan/15 bg-civic-cyan/8 px-3 py-2 text-xs text-slate-300">
        <Zap className="size-4 text-civic-cyan" />
        Model {health?.model_version ?? demoImagePrediction.telemetry.model_version} {health?.model_loaded ? "is warm" : "is running in seeded demo mode"}.
      </div>
      <div className="mt-3 flex items-center gap-2 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs text-slate-400">
        <Cpu className="size-4 text-slate-300" />
        {health?.weights_path ?? "Demo fallback keeps the portfolio experience stable"}
      </div>
    </div>
  );
}
