"use client";

import { motion } from "framer-motion";
import { BrainCircuit, TrendingUp } from "lucide-react";
import { useAppStore } from "@/store/use-app-store";

export function RiskForecastPanel() {
  const forecasts = useAppStore((state) => state.riskForecasts);

  return (
    <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Predictive AI</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Risk forecasting</h2>
        </div>
        <BrainCircuit className="size-5 text-civic-purple" />
      </div>
      <div className="grid gap-3">
        {forecasts.slice(0, 4).map((forecast) => (
          <div key={forecast.districtId} className="rounded-2xl border border-white/10 bg-civic-bg/58 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-white">{forecast.districtName}</p>
                <p className="mt-1 truncate text-xs text-slate-400">{forecast.primaryDrivers.join(" + ")}</p>
              </div>
              <span className="inline-flex items-center gap-1 rounded-full bg-civic-danger/10 px-2.5 py-1 text-xs font-semibold text-civic-danger">
                <TrendingUp className="size-3" />
                {forecast.riskScore}
              </span>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-center">
              {[
                ["Recurrence", forecast.recurrenceProbability],
                ["Hazard", forecast.hazardImpact],
                ["Pressure", forecast.responsePressure]
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl bg-white/[0.045] p-2">
                  <p className="text-sm font-semibold text-white">{Math.round(Number(value))}</p>
                  <p className="mt-1 text-[10px] uppercase tracking-[0.12em] text-slate-500">{label}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${forecast.riskScore}%` }}
                transition={{ duration: 0.7, ease: "easeOut" }}
                className="h-full rounded-full bg-gradient-to-r from-civic-purple via-civic-blue to-civic-danger"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
