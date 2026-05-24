"use client";

import type { CivicDetection } from "@/services/ai/types";

export function DetectionTimeline({ detections }: { detections: CivicDetection[] }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Incident timeline</p>
          <h2 className="mt-1 text-lg font-semibold text-white">Detection events</h2>
        </div>
        <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-slate-300">{detections.length} events</span>
      </div>
      <div className="max-h-[28rem] space-y-3 overflow-y-auto pr-1">
        {detections.length === 0 ? (
          <p className="rounded-xl border border-white/10 bg-black/20 p-4 text-sm text-slate-400">No YOLO detections have been received in this session.</p>
        ) : (
          detections.slice(0, 80).map((detection) => (
            <div key={detection.id} className="rounded-xl border border-white/10 bg-black/25 p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-semibold text-white">{detection.severity.toUpperCase()}</span>
                <span className="text-xs text-slate-500">{new Date(detection.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-slate-400">
                <span>{Math.round(detection.confidence * 100)}% confidence</span>
                <span>frame {detection.frame_index ?? 0}</span>
                <span>edge {Math.round(detection.sharpness)}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

