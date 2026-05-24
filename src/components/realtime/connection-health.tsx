"use client";

import { motion } from "framer-motion";
import { RadioTower, WifiOff } from "lucide-react";
import { useAppStore } from "@/store/use-app-store";

export function ConnectionHealth() {
  const status = useAppStore((state) => state.realtimeStatus);
  const connected = status === "connected";
  const degraded = status === "degraded" || status === "reconnecting";

  return (
    <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-semibold ${connected ? "border-civic-success/20 bg-civic-success/10 text-civic-success" : degraded ? "border-civic-warning/20 bg-civic-warning/10 text-civic-warning" : "border-white/10 bg-white/[0.055] text-slate-300"}`}>
      <span className="relative flex size-2">
        <motion.span
          className={`absolute inline-flex size-full rounded-full ${connected ? "bg-civic-success" : "bg-civic-warning"}`}
          animate={{ scale: [1, 2.4], opacity: [0.6, 0] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: "easeOut" }}
        />
        <span className={`relative inline-flex size-2 rounded-full ${connected ? "bg-civic-success" : "bg-civic-warning"}`} />
      </span>
      {connected ? <RadioTower className="size-4" /> : <WifiOff className="size-4" />}
      {connected ? "Realtime connected" : status === "degraded" ? "Degraded live mode" : status}
    </div>
  );
}
