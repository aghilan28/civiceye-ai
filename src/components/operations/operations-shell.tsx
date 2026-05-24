"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { Activity, BarChart3, Building2, Map, RadioTower, Route, ShieldCheck, Sparkles, Wrench } from "lucide-react";

const links = [
  { href: "/operations/live", label: "Live", icon: RadioTower },
  { href: "/operations/incidents", label: "Incidents", icon: ShieldCheck },
  { href: "/operations/map", label: "Map", icon: Map },
  { href: "/operations/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/operations/departments", label: "Departments", icon: Building2 },
  { href: "/field/tasks", label: "Field", icon: Wrench }
];

export function OperationsShell({ children, title, eyebrow }: { children: ReactNode; title: string; eyebrow: string }) {
  return (
    <section className="safe-x min-h-screen py-6 sm:py-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-civic-cyan/20 bg-civic-cyan/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-civic-cyan">
              <Sparkles className="size-3.5" />
              {eyebrow}
            </div>
            <h1 className="text-balance text-3xl font-semibold text-white sm:text-5xl">{title}</h1>
          </div>
          <nav className="flex gap-2 overflow-x-auto rounded-2xl border border-white/10 bg-white/[0.045] p-2 backdrop-blur-2xl">
            {links.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="inline-flex h-10 shrink-0 items-center gap-2 rounded-xl px-3 text-sm font-semibold text-slate-300 transition hover:bg-white/10 hover:text-white"
              >
                <item.icon className="size-4" />
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="relative overflow-hidden rounded-[1.5rem] border border-white/10 bg-[#060b16]/80 p-4 shadow-[0_24px_100px_rgba(0,0,0,0.35)] backdrop-blur-2xl sm:p-6">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-civic-cyan to-transparent" />
          <div className="pointer-events-none absolute right-6 top-6 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-500">
            <Activity className="size-3 text-civic-cyan" />
            production ops
          </div>
          {children}
        </div>
      </div>
    </section>
  );
}

export function EmptyOperationsState({ title, body }: { title: string; body: string }) {
  return (
    <div className="flex min-h-[22rem] items-center justify-center rounded-2xl border border-dashed border-white/10 bg-white/[0.025] p-6 text-center">
      <div className="max-w-md">
        <Route className="mx-auto size-8 text-civic-cyan" />
        <h2 className="mt-4 text-xl font-semibold text-white">{title}</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">{body}</p>
      </div>
    </div>
  );
}
