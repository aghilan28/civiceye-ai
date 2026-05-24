"use client";

import { motion } from "framer-motion";
import { Activity, Bell, ChevronRight, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";
import { navigationItems } from "@/lib/navigation";
import { Button } from "@/components/ui/button";

export function Navbar() {
  return (
    <motion.header
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.55, ease: "easeOut" }}
      className="safe-x sticky top-0 z-40 border-b border-white/10 bg-civic-bg/62 backdrop-blur-2xl"
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-3">
        <Link href="/" className="flex min-w-0 items-center gap-2" aria-label="CivicEye home">
          <span className="relative grid size-9 shrink-0 place-items-center rounded-xl border border-civic-cyan/30 bg-civic-cyan/10 shadow-glow">
            <span className="absolute inset-1 rounded-lg bg-civic-cyan/10 blur-sm" />
            <ShieldCheck className="size-5 text-civic-cyan" />
          </span>
          <span className="truncate text-lg font-semibold tracking-normal text-white">CivicEye</span>
        </Link>

        <nav aria-label="Primary navigation" className="hidden items-center gap-1 md:flex">
          {navigationItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-full px-4 py-2 text-sm font-medium text-slate-300 transition hover:bg-white/8 hover:text-white hover:shadow-[0_0_24px_rgba(0,212,255,0.10)]"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="hidden sm:inline-flex" aria-label="View alerts">
            <Bell className="size-5" />
          </Button>
          <Button className="hidden md:inline-flex">
            <Sparkles className="size-4" />
            Request demo
            <ChevronRight className="size-4" />
          </Button>
          <Button variant="secondary" size="icon" className="md:hidden" aria-label="Live system status">
            <Activity className="size-5 text-civic-cyan" />
          </Button>
        </div>
      </div>
    </motion.header>
  );
}
