"use client";

import { motion } from "framer-motion";
import { Activity, ArrowRight, Gauge, LocateFixed, Network, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { Reveal } from "@/components/animation/reveal";
import { Button } from "@/components/ui/button";

const metrics = [
  { value: "42s", label: "median routing" },
  { value: "94.8%", label: "AI confidence" },
  { value: "18.4", label: "frames / sec" }
];

const nodes = [
  { id: "North grid", x: "24%", y: "28%", tone: "cyan" },
  { id: "Stormwater", x: "62%", y: "23%", tone: "blue" },
  { id: "Corridor 8", x: "76%", y: "58%", tone: "cyan" },
  { id: "Field crew", x: "35%", y: "69%", tone: "white" },
  { id: "Priority route", x: "51%", y: "47%", tone: "cyan" }
];

const telemetry = [
  { label: "Incident queue", value: "312", delta: "+18" },
  { label: "Routing SLA", value: "00:42", delta: "stable" },
  { label: "GPU workers", value: "4 hot", delta: "18.4 FPS" }
];

const alerts = [
  { title: "Road surface anomaly", area: "Ward 12 / arterial lane", level: "high" },
  { title: "Drainage overflow risk", area: "South basin sensor mesh", level: "watch" }
];

function OperationsPanel() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="relative mx-auto w-full max-w-[38rem]"
    >
      <div className="absolute -inset-6 rounded-[2rem] bg-civic-cyan/[0.06] blur-3xl" />
      <div className="relative overflow-hidden rounded-[1.75rem] border border-white/[0.09] bg-[#07101c] shadow-[0_34px_120px_rgba(0,0,0,0.48)]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_24%_18%,rgba(0,212,255,0.16),transparent_31%),radial-gradient(circle_at_82%_22%,rgba(79,140,255,0.12),transparent_29%),linear-gradient(180deg,rgba(255,255,255,0.045),transparent_38%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.045)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.045)_1px,transparent_1px)] bg-[size:36px_36px] opacity-45" />

        <div className="relative z-10 border-b border-white/[0.08] px-5 py-4 sm:px-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-[0.66rem] font-semibold uppercase tracking-[0.24em] text-slate-500">AI operations mesh</p>
              <h2 className="mt-1 text-base font-semibold text-white">Bengaluru district command</h2>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full border border-civic-success/20 bg-civic-success/10 px-3 py-1.5 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-civic-success">
              <span className="size-1.5 rounded-full bg-civic-success shadow-[0_0_16px_rgba(54,211,153,0.7)]" />
              Live
            </div>
          </div>
        </div>

        <div className="relative z-10 p-4 sm:p-6">
          <div className="relative h-[22rem] overflow-hidden rounded-[1.25rem] border border-white/[0.07] bg-[#050b14] sm:h-[26rem]">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_48%,rgba(0,212,255,0.09),transparent_28%),linear-gradient(145deg,rgba(79,140,255,0.07),transparent_38%)]" />
            <svg className="absolute inset-0 size-full opacity-70" viewBox="0 0 600 430" aria-hidden="true">
              <path d="M74 96H240L328 164H516" fill="none" stroke="rgba(148,163,184,0.16)" strokeWidth="1" />
              <path d="M84 318H222L304 246H514" fill="none" stroke="rgba(148,163,184,0.16)" strokeWidth="1" />
              <path d="M134 88V330" fill="none" stroke="rgba(148,163,184,0.12)" strokeWidth="1" />
              <path d="M424 70V350" fill="none" stroke="rgba(148,163,184,0.12)" strokeWidth="1" />
              <motion.path
                d="M144 120C212 138 244 184 294 212C351 245 394 239 458 285"
                fill="none"
                stroke="rgba(0,212,255,0.58)"
                strokeLinecap="round"
                strokeWidth="2"
                strokeDasharray="9 14"
                animate={{ strokeDashoffset: [0, -92] }}
                transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
              />
              <motion.path
                d="M202 304C246 264 286 254 330 224C376 193 394 155 462 126"
                fill="none"
                stroke="rgba(79,140,255,0.45)"
                strokeLinecap="round"
                strokeWidth="2"
                strokeDasharray="8 16"
                animate={{ strokeDashoffset: [0, -96] }}
                transition={{ duration: 7.2, repeat: Infinity, ease: "linear" }}
              />
            </svg>

            <motion.div
              className="absolute left-1/2 top-1/2 size-44 -translate-x-1/2 -translate-y-1/2 rounded-full border border-civic-cyan/10"
              animate={{ scale: [0.88, 1.28], opacity: [0.42, 0] }}
              transition={{ duration: 4.8, repeat: Infinity, ease: "easeOut" }}
            />
            <motion.div
              className="absolute left-1/2 top-1/2 size-28 -translate-x-1/2 -translate-y-1/2 rounded-full border border-civic-cyan/18 bg-civic-cyan/[0.035]"
              animate={{ rotate: 360 }}
              transition={{ duration: 14, repeat: Infinity, ease: "linear" }}
            >
              <span className="absolute left-1/2 top-0 h-1/2 w-px origin-bottom bg-gradient-to-b from-civic-cyan/70 to-transparent" />
            </motion.div>

            <div className="absolute left-1/2 top-1/2 grid size-16 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-civic-cyan/20 bg-[#071523]/90 shadow-[0_0_32px_rgba(0,212,255,0.13)]">
              <Network className="size-6 text-civic-cyan" />
            </div>

            {nodes.map((node, index) => (
              <motion.div
                key={node.id}
                className="absolute"
                style={{ left: node.x, top: node.y }}
                animate={{ opacity: [0.72, 1, 0.72] }}
                transition={{ duration: 3.8 + index * 0.35, repeat: Infinity, ease: "easeInOut" }}
              >
                <span
                  className={
                    node.tone === "white"
                      ? "block size-2.5 rounded-full bg-white shadow-[0_0_16px_rgba(255,255,255,0.45)]"
                      : node.tone === "blue"
                        ? "block size-2.5 rounded-full bg-civic-blue shadow-[0_0_16px_rgba(79,140,255,0.45)]"
                        : "block size-2.5 rounded-full bg-civic-cyan shadow-[0_0_18px_rgba(0,212,255,0.5)]"
                  }
                />
                <span className="absolute left-4 top-[-0.55rem] hidden whitespace-nowrap text-[0.65rem] font-medium text-slate-400 sm:block">
                  {node.id}
                </span>
              </motion.div>
            ))}

            <div className="absolute left-4 top-4 w-[12.5rem] rounded-2xl border border-white/[0.08] bg-[#07111e]/88 p-3 shadow-[0_20px_50px_rgba(0,0,0,0.24)]">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                <LocateFixed className="size-3.5 text-civic-cyan" />
                Active scan
              </div>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.07]">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-civic-blue to-civic-cyan"
                  animate={{ width: ["38%", "78%", "52%"] }}
                  transition={{ duration: 5.5, repeat: Infinity, ease: "easeInOut" }}
                />
              </div>
              <p className="mt-2 text-xs text-slate-400">Vision model validating corridor anomalies</p>
            </div>

            <div className="absolute bottom-4 right-4 grid w-[13rem] gap-2">
              {alerts.map((alert) => (
                <div key={alert.title} className="rounded-2xl border border-white/[0.08] bg-[#07111e]/88 p-3 shadow-[0_20px_50px_rgba(0,0,0,0.24)]">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-white">{alert.title}</p>
                    <span className="rounded-full border border-civic-cyan/15 bg-civic-cyan/[0.07] px-2 py-0.5 text-[0.62rem] font-semibold uppercase tracking-[0.12em] text-civic-cyan">
                      {alert.level}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">{alert.area}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {telemetry.map((item) => (
              <div key={item.label} className="rounded-2xl border border-white/[0.07] bg-white/[0.035] p-3">
                <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
                <div className="mt-2 flex items-end justify-between gap-3">
                  <p className="text-lg font-semibold text-white">{item.value}</p>
                  <p className="text-xs font-medium text-civic-cyan">{item.delta}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export function HeroSection() {
  return (
    <section id="platform" className="safe-x relative isolate overflow-hidden bg-[#030711]">
      <div aria-hidden="true" className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_22%,rgba(0,212,255,0.12),transparent_31%),radial-gradient(circle_at_77%_14%,rgba(79,140,255,0.1),transparent_29%),linear-gradient(180deg,#030711_0%,#050816_72%,#050816_100%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.035)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.035)_1px,transparent_1px)] bg-[size:48px_48px] opacity-35 [mask-image:linear-gradient(to_bottom,rgba(0,0,0,0.82),transparent_88%)]" />
        <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-civic-bg to-transparent" />
      </div>

      <div className="mx-auto grid max-w-7xl gap-12 pb-16 pt-14 sm:pt-20 lg:min-h-[calc(100vh-5rem)] lg:grid-cols-[0.92fr_1.08fr] lg:items-center lg:gap-14 lg:pb-24 lg:pt-16">
        <div className="relative z-10 max-w-2xl">
          <Reveal>
            <div className="inline-flex items-center gap-2 rounded-full border border-civic-cyan/20 bg-[#07111e]/80 px-3.5 py-2 text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-civic-cyan shadow-[0_0_28px_rgba(0,212,255,0.08)]">
              <span className="size-1.5 rounded-full bg-civic-cyan shadow-[0_0_14px_rgba(0,212,255,0.65)]" />
              Civic infrastructure AI
            </div>
          </Reveal>

          <Reveal delay={0.08}>
            <h1 className="mt-6 max-w-[12ch] text-balance text-5xl font-semibold leading-[0.96] tracking-[-0.04em] text-white sm:text-6xl lg:text-[4.9rem]">
              Operational AI for urban infrastructure.
            </h1>
          </Reveal>

          <Reveal delay={0.16}>
            <p className="mt-6 max-w-[31rem] text-base leading-7 text-slate-300 sm:text-lg sm:leading-8">
              CivicEye coordinates visual detection, incident routing, and field response telemetry into one calm command layer for modern city operations.
            </p>
          </Reveal>

          <Reveal delay={0.24}>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button
                asChild
                size="lg"
                className="rounded-xl bg-gradient-to-r from-civic-blue to-civic-cyan shadow-[0_18px_45px_rgba(0,212,255,0.18)] hover:brightness-110"
              >
                <Link href="/ai/upload">
                  Open demo flow
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="secondary"
                className="rounded-xl border-white/10 bg-white/[0.035] text-slate-100 shadow-none hover:border-civic-cyan/25 hover:bg-white/[0.06] hover:shadow-[0_0_32px_rgba(0,212,255,0.08)]"
              >
                <Link href="#architecture">
                  View architecture
                  <ShieldCheck className="size-4" />
                </Link>
              </Button>
            </div>
          </Reveal>

          <Reveal delay={0.32}>
            <div className="mt-10 grid max-w-[32rem] grid-cols-3 divide-x divide-white/[0.08] border-y border-white/[0.08] py-4">
              {metrics.map((metric) => (
                <div key={metric.label} className="px-4 first:pl-0 last:pr-0">
                  <p className="text-xl font-semibold tracking-[-0.02em] text-white sm:text-2xl">{metric.value}</p>
                  <p className="mt-1 text-[0.72rem] font-medium uppercase tracking-[0.14em] text-slate-500">{metric.label}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>

        <div className="relative z-10">
          <div className="mb-4 hidden items-center justify-end gap-3 text-xs text-slate-500 lg:flex">
            <Activity className="size-4 text-civic-cyan" />
            <span>Live coordination center</span>
            <Gauge className="size-4 text-civic-blue" />
          </div>
          <OperationsPanel />
        </div>
      </div>
    </section>
  );
}
