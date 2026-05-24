"use client";

import { useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Play, Presentation, Sparkles } from "lucide-react";
import { demoScenarios } from "@/data/demo-scenarios";
import { getDemoScenario, publishScenarioStage } from "@/services/demo/demo-engine";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/use-app-store";

export function GuidedDemoPanel() {
  const scenarioId = useAppStore((state) => state.activeDemoScenarioId);
  const replay = useAppStore((state) => state.replay);
  const presentationMode = useAppStore((state) => state.presentationMode);
  const setActiveDemoScenario = useAppStore((state) => state.setActiveDemoScenario);
  const setDemoStage = useAppStore((state) => state.setDemoStage);
  const setPresentationMode = useAppStore((state) => state.setPresentationMode);
  const setReplay = useAppStore((state) => state.setReplay);
  const scenario = useMemo(() => getDemoScenario(scenarioId), [scenarioId]);

  useEffect(() => {
    if (!replay.playing) {
      return;
    }

    const interval = window.setInterval(() => {
      setReplay({ cursorMs: Math.min(replay.cursorMs + 1000 * replay.speed, scenario.durationMs) });
    }, 1000);

    if (replay.cursorMs >= scenario.durationMs) {
      window.clearInterval(interval);
      setReplay({ playing: false, cursorMs: scenario.durationMs });
    }

    return () => window.clearInterval(interval);
  }, [replay.cursorMs, replay.playing, replay.speed, scenario.durationMs, setReplay]);

  useEffect(() => {
    const activeStage = [...scenario.stages].reverse().find((stage) => stage.timestampMs <= replay.cursorMs) ?? scenario.stages[0];
    if (activeStage) {
      setDemoStage(activeStage);
      publishScenarioStage(activeStage);
    }
  }, [replay.cursorMs, scenario.stages, setDemoStage]);

  return (
    <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Guided demo mode</p>
          <h2 className="mt-1 text-xl font-semibold text-white">{scenario.title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">{scenario.subtitle}</p>
        </div>
        <Sparkles className="size-5 shrink-0 text-civic-cyan" />
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {demoScenarios.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveDemoScenario(item.id)}
            className={`rounded-2xl border p-3 text-left transition ${item.id === scenarioId ? "border-civic-cyan/30 bg-civic-cyan/10" : "border-white/10 bg-civic-bg/58 hover:border-civic-cyan/20"}`}
          >
            <p className="text-sm font-semibold text-white">{item.title}</p>
            <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">{item.civicImpact}</p>
          </button>
        ))}
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <Button variant="gradient" onClick={() => setReplay({ playing: !replay.playing })}>
          <Play className="size-4" />
          {replay.playing ? "Pause scenario" : "Run scenario"}
        </Button>
        <Button variant="secondary" onClick={() => setPresentationMode(!presentationMode)}>
          <Presentation className="size-4" />
          {presentationMode ? "Exit presentation" : "Presentation mode"}
        </Button>
      </div>

      <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
        <motion.div
          animate={{ width: `${Math.min(100, (replay.cursorMs / scenario.durationMs) * 100)}%` }}
          transition={{ duration: 0.35 }}
          className="h-full rounded-full bg-gradient-to-r from-civic-blue via-civic-purple to-civic-cyan"
        />
      </div>
    </div>
  );
}
