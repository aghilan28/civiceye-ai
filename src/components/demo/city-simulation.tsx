"use client";

import { motion } from "framer-motion";
import { useAppStore } from "@/store/use-app-store";

export function CitySimulation() {
  const stage = useAppStore((state) => state.demoStage);
  const intensity = stage?.telemetryDelta.riskScore ?? 52;
  const nodes = Array.from({ length: 18 }, (_, index) => ({
    id: index,
    left: `${12 + ((index * 23) % 76)}%`,
    top: `${18 + ((index * 31) % 62)}%`,
    delay: index * 0.08
  }));

  return (
    <div className="relative min-h-[34rem] overflow-hidden rounded-[2rem] border border-white/10 bg-[#06101f] p-5 backdrop-blur-2xl">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_40%_24%,rgba(0,212,255,0.22),transparent_28%),radial-gradient(circle_at_72%_70%,rgba(139,92,246,0.20),transparent_28%)]" />
      <div className="city-grid absolute inset-x-[-25%] bottom-[-20%] h-[80%] opacity-75" />
      <div className="relative z-10">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Living city simulation</p>
        <h2 className="mt-1 text-2xl font-semibold text-white">{stage?.title ?? "City intelligence ready"}</h2>
        <p className="mt-2 max-w-xl text-sm leading-6 text-slate-300">{stage?.narration ?? "Select and run a guided scenario to watch CivicEye reconstruct operational city intelligence."}</p>
      </div>
      {nodes.map((node) => (
        <motion.span
          key={node.id}
          className="absolute rounded-full bg-civic-cyan shadow-glow"
          style={{ left: node.left, top: node.top, width: 7, height: 7 }}
          animate={{ scale: [1, 1.8, 1], opacity: [0.35, 1, 0.45] }}
          transition={{ duration: 2.4, repeat: Infinity, delay: node.delay }}
        />
      ))}
      <motion.div
        className="absolute left-1/2 top-1/2 rounded-full border border-civic-purple/30 bg-civic-purple/10"
        animate={{
          width: 120 + intensity * 2,
          height: 120 + intensity * 2,
          x: "-50%",
          y: "-50%",
          opacity: [0.22, 0.46, 0.24]
        }}
        transition={{ duration: 1.8 }}
      />
    </div>
  );
}
