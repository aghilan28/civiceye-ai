"use client";

import { motion } from "framer-motion";
import { Clock3, RadioTower } from "lucide-react";
import { getDemoScenario } from "@/services/demo/demo-engine";
import { useAppStore } from "@/store/use-app-store";

export function IncidentReplay() {
  const scenarioId = useAppStore((state) => state.activeDemoScenarioId);
  const replay = useAppStore((state) => state.replay);
  const setReplay = useAppStore((state) => state.setReplay);
  const scenario = getDemoScenario(scenarioId);

  return (
    <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Incident replay</p>
          <h2 className="mt-1 text-xl font-semibold text-white">AI decision timeline</h2>
        </div>
        <Clock3 className="size-5 text-civic-purple" />
      </div>
      <input
        aria-label="Replay timeline"
        type="range"
        min={0}
        max={scenario.durationMs}
        value={replay.cursorMs}
        onChange={(event) => setReplay({ cursorMs: Number(event.target.value), playing: false })}
        className="w-full accent-civic-cyan"
      />
      <div className="mt-4 grid gap-3">
        {scenario.stages.map((stage) => {
          const active = replay.cursorMs >= stage.timestampMs;
          return (
            <motion.div
              key={stage.id}
              animate={{ opacity: active ? 1 : 0.42, x: active ? 0 : 8 }}
              className={`rounded-2xl border p-3 ${active ? "border-civic-cyan/25 bg-civic-cyan/10" : "border-white/10 bg-civic-bg/58"}`}
            >
              <div className="flex items-center gap-3">
                <span className="grid size-9 place-items-center rounded-xl bg-civic-cyan/10">
                  <RadioTower className="size-4 text-civic-cyan" />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-white">{stage.title}</p>
                  <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">{stage.narration}</p>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
