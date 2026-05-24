"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BarChart3, Camera, History, Settings, UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { href: "/ai/live", label: "Live", icon: Camera },
  { href: "/ai/upload", label: "Upload", icon: UploadCloud },
  { href: "/ai/history", label: "History", icon: History },
  { href: "/ai/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/ai/settings", label: "Settings", icon: Settings }
];

export function AiCommandShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <section className="safe-x min-h-screen py-6 sm:py-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-5 flex flex-col gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-civic-cyan/25 bg-civic-cyan/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-civic-cyan">
              <Activity className="size-3.5" />
              YOLOv8 production inference
            </div>
            <h1 className="mt-3 text-3xl font-semibold tracking-normal text-white sm:text-5xl">CivicEye AI Command</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400 sm:text-base">
              Realtime pothole detection, live camera operations, video processing, and model health for municipal road intelligence.
            </p>
          </div>
          <nav className="flex gap-2 overflow-x-auto rounded-2xl border border-white/10 bg-white/[0.04] p-1 backdrop-blur-xl">
            {items.map((item) => {
              const active = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "inline-flex min-h-10 shrink-0 items-center gap-2 rounded-xl px-3 text-sm font-semibold text-slate-400 transition",
                    active && "bg-white text-civic-bg shadow-[0_12px_35px_rgba(255,255,255,0.12)]",
                    !active && "hover:bg-white/10 hover:text-white"
                  )}
                >
                  <Icon className="size-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        {children}
      </div>
    </section>
  );
}

