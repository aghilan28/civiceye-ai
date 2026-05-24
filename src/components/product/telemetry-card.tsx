"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type TelemetryCardProps = {
  label: string;
  value: string;
  trend: string;
  icon: LucideIcon;
  tone?: "cyan" | "blue" | "purple" | "success" | "danger";
};

const toneMap = {
  cyan: "text-civic-cyan bg-civic-cyan/10 border-civic-cyan/20",
  blue: "text-civic-blue bg-civic-blue/10 border-civic-blue/20",
  purple: "text-civic-purple bg-civic-purple/10 border-civic-purple/20",
  success: "text-civic-success bg-civic-success/10 border-civic-success/20",
  danger: "text-civic-danger bg-civic-danger/10 border-civic-danger/20"
};

export function TelemetryCard({ label, value, trend, icon: Icon, tone = "cyan" }: TelemetryCardProps) {
  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ type: "spring", stiffness: 260, damping: 22 }}
      className="neon-edge rounded-3xl border border-white/10 bg-white/[0.055] p-4 shadow-[0_22px_70px_rgba(0,0,0,0.28)] backdrop-blur-2xl"
    >
      <div className="flex items-center justify-between gap-3">
        <span className={cn("grid size-11 place-items-center rounded-2xl border", toneMap[tone])}>
          <Icon className="size-5" />
        </span>
        <span className="rounded-full bg-white/8 px-2.5 py-1 text-xs font-semibold text-slate-300">{trend}</span>
      </div>
      <p className="mt-5 text-3xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-sm text-slate-400">{label}</p>
    </motion.div>
  );
}
