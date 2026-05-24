"use client";

import type { CivicDetection, InferenceTelemetry } from "@/services/ai/types";

export function AiAnalyticsPanel({ detections, telemetry }: { detections: CivicDetection[]; telemetry?: InferenceTelemetry | null }) {
  const confidence = detections.length ? detections.reduce((sum, item) => sum + item.confidence, 0) / detections.length : 0;
  const severe = detections.filter((item) => item.severity === "severe").length;
  const medium = detections.filter((item) => item.severity === "medium").length;
  const small = detections.filter((item) => item.severity === "small").length;
  const values = [
    ["Potholes", detections.length],
    ["Severe", severe],
    ["Medium", medium],
    ["Small", small],
    ["Mean conf", `${Math.round(confidence * 100)}%`],
    ["FPS", telemetry?.fps ? telemetry.fps.toFixed(1) : "0.0"]
  ];

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Detection analytics</p>
      <h2 className="mt-1 text-lg font-semibold text-white">Rolling inference</h2>
      <div className="mt-4 grid grid-cols-2 gap-3">
        {values.map(([label, value]) => (
          <div key={label} className="rounded-lg border border-white/10 bg-black/20 p-3">
            <p className="text-xs text-slate-500">{label}</p>
            <p className="mt-1 text-xl font-semibold text-white">{value}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 h-24 overflow-hidden rounded-xl border border-civic-cyan/15 bg-black/30 p-2">
        <div className="flex h-full items-end gap-1">
          {detections.slice(-36).map((detection) => (
            <div
              key={detection.id}
              className="min-w-2 flex-1 rounded-t bg-civic-cyan shadow-[0_0_18px_rgba(0,212,255,0.45)]"
              style={{ height: `${Math.max(14, detection.confidence * 100)}%` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

