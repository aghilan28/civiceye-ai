"use client";

import { motion } from "framer-motion";
import { Camera, Plus } from "lucide-react";
import Link from "next/link";

export function FloatingReportFab() {
  return (
    <motion.div
      className="fixed bottom-28 right-4 z-40 md:bottom-8 md:right-8"
      initial={{ scale: 0.86, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 260, damping: 22 }}
    >
      <Link
        href="/report"
        className="group relative flex h-16 items-center gap-3 overflow-hidden rounded-full border border-civic-cyan/30 bg-gradient-to-r from-civic-blue via-civic-purple to-civic-cyan px-5 font-semibold text-white shadow-[0_22px_70px_rgba(0,212,255,0.28)]"
      >
        <span className="absolute inset-0 animate-pulse bg-white/10 opacity-0 transition group-hover:opacity-100" />
        <span className="relative grid size-10 place-items-center rounded-full bg-white/16">
          <span className="absolute inset-0 rounded-full border border-white/20" />
          <Camera className="size-5" />
        </span>
        <span className="relative hidden sm:inline">Report issue</span>
        <Plus className="relative size-5 sm:hidden" />
      </Link>
    </motion.div>
  );
}
