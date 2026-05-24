"use client";

import { motion } from "framer-motion";
import { BrainCircuit, ScanLine } from "lucide-react";
import { scanStages } from "@/lib/product-data";

type AiScanVisualProps = {
  activeStage: number;
};

export function AiScanVisual({ activeStage }: AiScanVisualProps) {
  return (
    <div className="relative min-h-[28rem] overflow-hidden rounded-[2rem] border border-white/10 bg-[#06101f] shadow-[0_28px_90px_rgba(0,0,0,0.32)]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_44%_24%,rgba(79,140,255,0.28),transparent_28%),radial-gradient(circle_at_72%_76%,rgba(0,212,255,0.18),transparent_26%)]" />
      <div className="absolute inset-4 grid grid-cols-7 gap-1 opacity-60">
        {Array.from({ length: 56 }).map((_, index) => (
          <motion.span
            key={index}
            animate={{ opacity: [0.12, 0.55, 0.2] }}
            transition={{ duration: 2.6 + (index % 4), repeat: Infinity, delay: index * 0.025 }}
            className="rounded-md border border-civic-cyan/10 bg-civic-cyan/10"
          />
        ))}
      </div>
      <motion.div
        className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-transparent via-civic-cyan/35 to-transparent"
        animate={{ y: ["-20%", "420%"] }}
        transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
      />
      <div className="absolute left-[18%] top-[34%] h-28 w-44 rounded-2xl border-2 border-civic-cyan shadow-glow">
        <span className="absolute -top-9 left-0 rounded-full bg-civic-cyan px-3 py-1 text-xs font-semibold text-civic-bg">Road damage 93%</span>
      </div>
      <div className="absolute right-[14%] top-[22%] h-20 w-32 rounded-2xl border border-civic-danger/80 shadow-[0_0_28px_rgba(251,113,133,0.28)]">
        <span className="absolute -bottom-9 right-0 rounded-full bg-civic-danger px-3 py-1 text-xs font-semibold text-white">Hazard zone</span>
      </div>
      <div className="absolute bottom-4 left-4 right-4 rounded-3xl border border-white/10 bg-civic-bg/78 p-4 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <span className="grid size-11 place-items-center rounded-2xl bg-civic-cyan/10">
            <BrainCircuit className="size-5 text-civic-cyan" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">{scanStages[activeStage]}</p>
            <p className="truncate text-xs text-slate-400">Neural infrastructure analysis running</p>
          </div>
          <ScanLine className="ml-auto size-5 text-civic-purple" />
        </div>
      </div>
    </div>
  );
}
