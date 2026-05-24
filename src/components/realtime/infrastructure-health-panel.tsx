"use client";

import { Activity } from "lucide-react";
import { useAppStore } from "@/store/use-app-store";

export function InfrastructureHealthPanel() {
  const health = useAppStore((state) => state.liveTelemetry?.infrastructureHealth);
  const metrics = [
    ["Roads", health?.roads ?? 0],
    ["Drainage", health?.drainage ?? 0],
    ["Sanitation", health?.sanitation ?? 0],
    ["Lighting", health?.streetlighting ?? 0],
    ["Water", health?.water ?? 0]
  ];

  return (
    <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Digital twin health</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Infrastructure systems</h2>
        </div>
        <Activity className="size-5 text-civic-success" />
      </div>
      <div className="grid gap-3">
        {metrics.map(([label, value]) => (
          <div key={label}>
            <div className="flex items-center justify-between text-sm">
              <span className="font-semibold text-white">{label}</span>
              <span className="text-slate-400">{value}%</span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full bg-gradient-to-r from-civic-success via-civic-cyan to-civic-blue" style={{ width: `${value}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
