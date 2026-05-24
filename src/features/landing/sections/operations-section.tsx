"use client";

import { motion } from "framer-motion";
import { Activity, BarChart3, Clock3, Map, RadioTower, ShieldAlert, UsersRound } from "lucide-react";
import { Reveal } from "@/components/animation/reveal";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { responseTimeline } from "@/features/landing/data";

const operations = [
  { title: "Live command map", description: "Mapbox-ready severity layers, ward boundaries, and active incident pins.", icon: Map, signal: "128 zones" },
  { title: "Authority routing", description: "JWT-ready workflows for municipal teams, contractors, and verified citizens.", icon: ShieldAlert, signal: "42s median" },
  { title: "Crew coordination", description: "Incident ownership, SLA timers, dispatch notes, and escalation chains.", icon: UsersRound, signal: "18 teams" }
];

export function OperationsSection() {
  return (
    <section id="operations" className="safe-x py-14 sm:py-20">
      <div className="mx-auto max-w-7xl">
        <Reveal>
          <div className="max-w-2xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-civic-blue/25 bg-civic-blue/10 px-3 py-2 text-xs font-semibold text-civic-blue shadow-[0_0_26px_rgba(79,140,255,0.12)]">
              <RadioTower className="size-4" />
              Operations foundation
            </div>
            <h2 className="text-balance text-3xl font-semibold tracking-normal text-white sm:text-5xl">
              A municipal intelligence system, not another inbox.
            </h2>
          </div>
        </Reveal>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {operations.map((item, index) => {
            const Icon = item.icon;
            return (
              <Reveal key={item.title} delay={index * 0.08}>
                <Card className="h-full overflow-hidden bg-white/[0.045]">
                  <CardHeader>
                    <div className="mb-4 flex items-center justify-between gap-3">
                      <div className="grid size-12 place-items-center rounded-2xl border border-civic-cyan/20 bg-civic-cyan/10 shadow-glow">
                        <Icon className="size-6 text-civic-cyan" />
                      </div>
                      <span className="rounded-full bg-white/8 px-3 py-1 text-xs font-semibold text-slate-300">{item.signal}</span>
                    </div>
                    <CardTitle>{item.title}</CardTitle>
                    <CardDescription>{item.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-3 rounded-2xl bg-civic-bg/60 p-3">
                      <Activity className="size-5 text-civic-success" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-white">System ready</p>
                        <p className="truncate text-xs text-slate-400">Phase 1 architecture online</p>
                      </div>
                      <Clock3 className="ml-auto size-4 shrink-0 text-slate-500" />
                    </div>
                  </CardContent>
                </Card>
              </Reveal>
            );
          })}
        </div>

        <Reveal delay={0.16}>
          <div className="mt-5 overflow-hidden rounded-3xl border border-white/10 bg-civic-surface/70 p-4 shadow-[0_26px_90px_rgba(0,0,0,0.3)] backdrop-blur-2xl">
            <div className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
              <div className="rounded-2xl border border-white/10 bg-white/[0.045] p-4">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Response timeline</p>
                    <p className="mt-1 text-lg font-semibold text-white">Ward 18 overflow escalation</p>
                  </div>
                  <BarChart3 className="size-5 text-civic-cyan" />
                </div>
                <div className="grid gap-3">
                  {responseTimeline.map((step, index) => (
                    <div key={step.label} className="relative flex items-center gap-3">
                      {index < responseTimeline.length - 1 ? (
                        <span className="absolute left-[0.58rem] top-7 h-7 w-px bg-white/10" />
                      ) : null}
                      <span className={`relative z-10 size-3 rounded-full ${step.active ? "bg-civic-cyan shadow-glow" : "bg-slate-600"}`} />
                      <div className="flex min-w-0 flex-1 items-center justify-between gap-3 rounded-2xl bg-civic-bg/54 p-3">
                        <span className="truncate text-sm font-semibold text-white">{step.label}</span>
                        <span className="text-xs font-semibold text-slate-400">{step.value}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                {["Detection", "Validation", "Dispatch"].map((label, index) => (
                  <motion.div
                    key={label}
                    initial={{ opacity: 0.4, y: 12 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.12 }}
                    className="rounded-2xl border border-white/10 bg-white/[0.045] p-4"
                  >
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Step 0{index + 1}</p>
                    <p className="mt-2 text-lg font-semibold text-white">{label}</p>
                    <div className="mt-4 h-2 rounded-full bg-white/10">
                      <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: `${78 + index * 8}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8, delay: index * 0.12 }}
                        className="h-full rounded-full bg-gradient-to-r from-civic-blue to-civic-cyan"
                      />
                    </div>
                    <p className="mt-3 text-xs leading-5 text-slate-400">
                      {index === 0 ? "Image class, location, and severity scored." : index === 1 ? "Verified for municipal queue integrity." : "Routed by department, zone, and SLA."}
                    </p>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
