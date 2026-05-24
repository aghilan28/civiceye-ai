"use client";

import { BrainCircuit, SendHorizontal } from "lucide-react";
import { getDemoScenario } from "@/services/demo/demo-engine";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/use-app-store";

export function OperationsCopilot() {
  const scenarioId = useAppStore((state) => state.activeDemoScenarioId);
  const stage = useAppStore((state) => state.demoStage);
  const scenario = getDemoScenario(scenarioId);

  const recommendation = stage
    ? `Prioritize ${stage.severity} response. ${stage.narration}`
    : "Run a scenario to generate live municipal recommendations.";

  return (
    <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <div className="flex items-center gap-3">
        <span className="grid size-11 place-items-center rounded-2xl bg-civic-purple/10">
          <BrainCircuit className="size-5 text-civic-purple" />
        </span>
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">AI operations copilot</p>
          <h2 className="text-xl font-semibold text-white">CivicEye Assistant</h2>
        </div>
      </div>
      <div className="mt-4 rounded-3xl border border-white/10 bg-civic-bg/58 p-4">
        <p className="text-sm leading-6 text-slate-200">{recommendation}</p>
        <div className="mt-4 grid gap-2">
          {[
            `Executive summary: ${scenario.civicImpact}`,
            `Recommended coordination: ${stage?.eventType.replaceAll("_", " ").toLowerCase() ?? "standby"}`,
            `Pilot proof point: response pressure is visible before SLA failure`
          ].map((item) => (
            <div key={item} className="rounded-2xl bg-white/[0.045] p-3 text-xs leading-5 text-slate-300">
              {item}
            </div>
          ))}
        </div>
      </div>
      <div className="mt-4 flex gap-2">
        <input className="h-12 min-w-0 flex-1 rounded-2xl border border-white/10 bg-white/[0.055] px-4 text-sm text-white outline-none placeholder:text-slate-600 focus:border-civic-cyan/30" placeholder="Ask for operational summary..." />
        <Button size="icon" variant="gradient" aria-label="Send copilot prompt">
          <SendHorizontal className="size-5" />
        </Button>
      </div>
    </div>
  );
}
