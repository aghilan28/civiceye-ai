"use client";

import { BrainCircuit, Cpu, Gauge, RotateCcw } from "lucide-react";
import { modelHealthSummary } from "@/services/mlops/model-registry";

const qualityMetrics = [
  { label: "P95 inference latency", value: "842ms", icon: Gauge },
  { label: "Mean confidence", value: "92.4%", icon: BrainCircuit },
  { label: "GPU utilization hook", value: "62%", icon: Cpu },
  { label: "Fallback rate", value: "3.1%", icon: RotateCcw }
];

export function AiObservabilityPanel() {
  const models = modelHealthSummary();

  return (
    <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">MLOps registry</p>
        <h2 className="mt-1 text-xl font-semibold text-white">Model routing health</h2>
        <div className="mt-4 grid gap-3">
          {models.map((model) => (
            <div key={model.id} className="rounded-2xl border border-white/10 bg-civic-bg/58 p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-white">{model.id}</p>
                  <p className="mt-1 text-xs text-slate-400">v{model.version} - {model.runtime}</p>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${model.status === "healthy" ? "bg-civic-success/10 text-civic-success" : "bg-civic-warning/10 text-civic-warning"}`}>
                  {model.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {qualityMetrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <div key={metric.label} className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
              <span className="grid size-11 place-items-center rounded-2xl bg-civic-cyan/10">
                <Icon className="size-5 text-civic-cyan" />
              </span>
              <p className="mt-5 text-3xl font-semibold text-white">{metric.value}</p>
              <p className="mt-1 text-sm text-slate-400">{metric.label}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
