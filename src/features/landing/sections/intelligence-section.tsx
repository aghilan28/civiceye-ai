"use client";

import { motion } from "framer-motion";
import { BrainCircuit, CheckCircle2, LocateFixed, Route, UploadCloud } from "lucide-react";
import { Reveal } from "@/components/animation/reveal";
import { GlassPanel } from "@/components/ui/glass-panel";
import { detectionClasses, incidentFeed } from "@/features/landing/data";

const heatCells = Array.from({ length: 48 }, (_, index) => ({
  id: index,
  intensity: 18 + ((index * 17) % 72)
}));

export function IntelligenceSection() {
  return (
    <section id="intelligence" className="safe-x py-14 sm:py-20">
      <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.82fr_1.18fr] lg:items-center">
        <Reveal>
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-civic-purple/25 bg-civic-purple/10 px-3 py-2 text-xs font-semibold text-civic-purple shadow-[0_0_26px_rgba(139,92,246,0.12)]">
              <BrainCircuit className="size-4" />
              AI detection pipeline
            </div>
            <h2 className="text-balance text-3xl font-semibold tracking-normal text-white sm:text-5xl">
              Computer vision that understands the street.
            </h2>
            <p className="mt-5 text-pretty text-base leading-7 text-slate-300 sm:text-lg">
              CivicEye is structured for YOLOv8, TensorFlow, and OpenCV modules so image uploads, geolocation, confidence scoring, and authority routing can evolve without rewriting the product surface.
            </p>
            <div className="mt-7 grid gap-3">
              {[
                "Mobile image upload with GPS metadata",
                "AI class confidence and severity scoring",
                "REST API boundary ready for FastAPI services"
              ].map((item) => (
                <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.055] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] backdrop-blur-xl">
                  <CheckCircle2 className="size-5 shrink-0 text-civic-success" />
                  <span className="text-sm font-medium text-slate-200">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </Reveal>

        <Reveal delay={0.14}>
          <GlassPanel glow="purple" className="overflow-hidden p-3 sm:p-5">
            <div className="rounded-[1.5rem] border border-white/10 bg-[#07101f] p-4 sm:p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Detection review</p>
                  <h3 className="mt-1 text-xl font-semibold text-white">AI incident triage</h3>
                </div>
                <div className="grid size-12 place-items-center rounded-2xl border border-civic-cyan/20 bg-civic-cyan/10 shadow-glow">
                  <UploadCloud className="size-6 text-civic-cyan" />
                </div>
              </div>

              <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.92fr]">
                <div className="relative min-h-[27rem] overflow-hidden rounded-2xl border border-white/10 bg-slate-950">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_42%_28%,rgba(79,140,255,0.32),transparent_24%),radial-gradient(circle_at_66%_72%,rgba(0,212,255,0.18),transparent_24%)]" />
                  <div className="absolute inset-4 grid grid-cols-8 gap-1 opacity-75">
                    {heatCells.map((cell) => (
                      <motion.span
                        key={cell.id}
                        initial={{ opacity: 0.18 }}
                        whileInView={{ opacity: cell.intensity / 100 }}
                        viewport={{ once: true }}
                        transition={{ delay: cell.id * 0.01, duration: 0.45 }}
                        className="rounded-md border border-civic-cyan/10 bg-civic-cyan/20"
                      />
                    ))}
                  </div>
                  <div className="absolute inset-x-0 top-0 h-16 animate-scan bg-gradient-to-b from-civic-cyan/0 via-civic-cyan/30 to-civic-cyan/0" />
                  <div className="absolute left-[14%] top-[36%] h-24 w-36 rounded-xl border-2 border-civic-cyan shadow-glow">
                    <span className="absolute -top-8 left-0 rounded-full bg-civic-cyan px-2 py-1 text-xs font-semibold text-civic-bg">
                      Pothole 97%
                    </span>
                  </div>
                  <div className="absolute right-[12%] top-[22%] h-20 w-28 rounded-xl border border-civic-danger/80 shadow-[0_0_24px_rgba(251,113,133,0.28)]">
                    <span className="absolute -bottom-8 right-0 rounded-full bg-civic-danger px-2 py-1 text-xs font-semibold text-white">
                      Overflow 96%
                    </span>
                  </div>
                  <div className="absolute bottom-5 left-5 right-5 rounded-2xl border border-white/10 bg-civic-bg/78 p-4 backdrop-blur-xl">
                    <div className="flex items-center gap-3">
                      <LocateFixed className="size-5 text-civic-cyan" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-white">Auto-geotagged report</p>
                        <p className="truncate text-xs text-slate-400">12.9716 N, 77.5946 E - Ward escalation ready</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid gap-3">
                  {detectionClasses.map((item) => {
                    const Icon = item.icon;
                    return (
                      <motion.div
                        key={item.label}
                        whileHover={{ x: 4 }}
                        className="rounded-2xl border border-white/10 bg-white/[0.055] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <Icon className="size-5 text-civic-cyan" />
                            <span className="text-sm font-semibold text-white">{item.label}</span>
                          </div>
                          <span className="text-xs font-semibold text-slate-300">{item.confidence}%</span>
                        </div>
                        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
                          <motion.div
                            initial={{ width: 0 }}
                            whileInView={{ width: `${item.confidence}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.7 }}
                            className="h-full rounded-full bg-gradient-to-r from-civic-purple to-civic-cyan"
                          />
                        </div>
                      </motion.div>
                    );
                  })}

                  <div className="rounded-2xl border border-white/10 bg-civic-bg/65 p-4">
                    <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
                      <Route className="size-4 text-civic-blue" />
                      Live incident feed
                    </div>
                    <div className="grid gap-2">
                      {incidentFeed.map((item) => (
                        <div key={item.zone} className="flex items-center gap-3 rounded-xl bg-white/[0.05] p-2">
                          <span className="size-2 rounded-full bg-civic-cyan shadow-glow" />
                          <div className="min-w-0">
                            <p className="truncate text-xs font-semibold text-white">{item.issue}</p>
                            <p className="truncate text-[11px] text-slate-400">{item.zone} - {item.severity}</p>
                          </div>
                          <span className="ml-auto text-[11px] font-semibold text-slate-400">{item.eta}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </GlassPanel>
        </Reveal>
      </div>
    </section>
  );
}
