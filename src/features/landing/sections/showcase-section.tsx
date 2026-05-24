"use client";

import { motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  Cpu,
  Database,
  GitBranch,
  Map,
  RadioTower,
  Route,
  ServerCog,
  ShieldCheck,
  Workflow
} from "lucide-react";
import Link from "next/link";
import { Reveal } from "@/components/animation/reveal";
import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass-panel";
import {
  architectureNodes,
  executiveTrends,
  repairWorkflow,
  showcaseAnalytics,
  showcaseIncidents,
  showcaseMapIntelligence
} from "@/data/showcase";

const iconMap = [Route, ServerCog, Cpu, Database, RadioTower, BarChart3];

export function ShowcaseSection() {
  return (
    <>
      <LiveSystemPreview />
      <ArchitectureShowcase />
      <DetectionWorkflow />
      <AnalyticsShowcase />
      <EngineeringStory />
    </>
  );
}

function SectionHeading({
  eyebrow,
  title,
  body,
  icon: Icon
}: {
  eyebrow: string;
  title: string;
  body: string;
  icon: typeof Activity;
}) {
  return (
    <Reveal>
      <div className="max-w-3xl">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-civic-cyan/25 bg-civic-cyan/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-civic-cyan">
          <Icon className="size-4" />
          {eyebrow}
        </div>
        <h2 className="text-balance text-3xl font-semibold tracking-normal text-white sm:text-5xl">{title}</h2>
        <p className="mt-4 text-pretty text-base leading-7 text-slate-300 sm:text-lg">{body}</p>
      </div>
    </Reveal>
  );
}

function LiveSystemPreview() {
  return (
    <section id="live-preview" className="safe-x py-14 sm:py-20">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="Live system preview"
          title="A civic command surface that feels alive from the first click."
          body="The portfolio demo opens with seeded realtime operations: detections, district risk, repair queues, AI throughput, and field assignments move together even without a running backend."
          icon={Activity}
        />
        <div className="mt-8 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          <Reveal delay={0.1}>
            <GlassPanel glow="cyan" className="overflow-hidden p-4">
              <div className="relative min-h-[34rem] overflow-hidden rounded-[1.25rem] border border-white/10 bg-[#06101f] p-5">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_32%_20%,rgba(0,212,255,0.22),transparent_28%),radial-gradient(circle_at_76%_70%,rgba(79,140,255,0.18),transparent_30%)]" />
                <div className="city-grid absolute inset-x-[-18%] bottom-[-24%] h-[76%] opacity-70" />
                <div className="relative z-10 flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Bengaluru demo twin</p>
                    <h3 className="mt-1 text-2xl font-semibold text-white">Severity heat layer</h3>
                  </div>
                  <span className="rounded-full border border-civic-success/25 bg-civic-success/15 px-3 py-1 text-xs font-semibold text-civic-success">DEMO MODE ONLINE</span>
                </div>

                {showcaseMapIntelligence.districts.map((district, index) => (
                  <motion.div
                    key={district.district_id}
                    className="absolute rounded-full border border-civic-cyan/25 bg-civic-cyan/10"
                    style={{
                      left: `${14 + index * 18}%`,
                      top: `${24 + (index % 2) * 18}%`,
                      width: 96 + district.degradation_score * 0.7,
                      height: 96 + district.degradation_score * 0.7
                    }}
                    animate={{ scale: [0.94, 1.08, 0.94], opacity: [0.36, 0.7, 0.36] }}
                    transition={{ duration: 4 + index, repeat: Infinity, ease: "easeInOut" }}
                  />
                ))}

                {showcaseIncidents.map((incident, index) => (
                  <motion.div
                    key={incident.incident_id}
                    className="absolute z-10"
                    style={{ left: `${20 + index * 14}%`, top: `${38 + (index % 3) * 12}%` }}
                    animate={{ y: [0, -8, 0] }}
                    transition={{ duration: 3.4 + index * 0.35, repeat: Infinity, ease: "easeInOut" }}
                  >
                    <span className="absolute -inset-4 animate-ping rounded-full bg-civic-cyan/20" />
                    <span
                      className="relative block size-4 rounded-full border border-white/70 shadow-glow"
                      style={{ backgroundColor: incident.severity === "CRITICAL" ? "#FB7185" : incident.severity === "HIGH" ? "#4F8CFF" : "#00D4FF" }}
                    />
                    <span className="absolute left-5 top-[-9px] whitespace-nowrap rounded-full border border-white/10 bg-civic-bg/75 px-2 py-1 text-[10px] font-semibold text-slate-200 backdrop-blur-xl">
                      {incident.incident_code}
                    </span>
                  </motion.div>
                ))}

                <div className="absolute inset-x-5 bottom-5 grid gap-3 md:grid-cols-3">
                  {[
                    ["Queue pressure", "312 jobs", "vision.high"],
                    ["GPU throughput", "18.4 FPS", "2 workers"],
                    ["Repair queue", "47 active", "83% closure"]
                  ].map(([label, value, detail]) => (
                    <div key={label} className="rounded-2xl border border-white/10 bg-civic-bg/72 p-4 backdrop-blur-xl">
                      <p className="text-xs text-slate-400">{label}</p>
                      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
                      <p className="mt-1 text-xs text-civic-cyan">{detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            </GlassPanel>
          </Reveal>

          <Reveal delay={0.18}>
            <div className="grid gap-4">
              <GlassPanel glow="blue" className="p-4">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Incident feed</p>
                    <h3 className="mt-1 text-xl font-semibold text-white">AI validated reports</h3>
                  </div>
                  <RadioTower className="size-5 text-civic-cyan" />
                </div>
                <div className="grid gap-3">
                  {showcaseIncidents.slice(0, 4).map((incident) => (
                    <div key={incident.incident_id} className="rounded-2xl border border-white/10 bg-white/[0.05] p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm font-semibold text-white">{incident.road_name}</span>
                        <span className="rounded-full bg-white/10 px-2 py-1 text-[10px] font-semibold text-slate-300">{Math.round(incident.confidence * 100)}%</span>
                      </div>
                      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                        <span>{incident.severity}</span>
                        <span>{incident.status.replace("_", " ")}</span>
                        <span>{incident.assigned_department}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </GlassPanel>
              <GlassPanel glow="purple" className="p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">District activity</h3>
                  <Map className="size-5 text-civic-purple" />
                </div>
                <div className="grid gap-3">
                  {showcaseAnalytics.district_risk.map((district) => (
                    <div key={district.id}>
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium text-slate-200">{district.name}</span>
                        <span className="font-semibold text-civic-cyan">{district.risk_score}</span>
                      </div>
                      <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
                        <motion.div
                          className="h-full rounded-full bg-gradient-to-r from-civic-blue to-civic-cyan"
                          initial={{ width: 0 }}
                          whileInView={{ width: `${district.risk_score}%` }}
                          viewport={{ once: true }}
                          transition={{ duration: 0.8 }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </GlassPanel>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function ArchitectureShowcase() {
  return (
    <section id="architecture" className="safe-x py-14 sm:py-20">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="Architecture showcase"
          title="The system design story recruiters should remember."
          body="CivicEye presents the engineering beneath the interface: intake, queues, GPU workers, durable storage, websocket operations, analytics, and field repair orchestration."
          icon={Workflow}
        />
        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {architectureNodes.map((node, index) => {
            const Icon = iconMap[index] ?? GitBranch;
            return (
              <Reveal key={node.id} delay={index * 0.05}>
                <div className="relative h-full overflow-hidden rounded-3xl border border-white/10 bg-white/[0.045] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] backdrop-blur-2xl">
                  <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-civic-cyan/70 to-transparent" />
                  <div className="flex items-center justify-between gap-3">
                    <span className="grid size-12 place-items-center rounded-2xl border border-civic-cyan/20 bg-civic-cyan/10">
                      <Icon className="size-6 text-civic-cyan" />
                    </span>
                    <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-slate-300">{node.metric}</span>
                  </div>
                  <h3 className="mt-5 text-xl font-semibold text-white">{node.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-400">{node.detail}</p>
                  {index < architectureNodes.length - 1 ? (
                    <ArrowRight className="absolute right-4 top-1/2 hidden size-5 -translate-y-1/2 text-civic-cyan/50 lg:block" />
                  ) : null}
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function DetectionWorkflow() {
  return (
    <section id="demo-flow" className="safe-x py-14 sm:py-20">
      <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
        <SectionHeading
          eyebrow="AI detection demo"
          title="Upload evidence, reveal detections, generate a repair workflow."
          body="The demo flow shows the real product motion: media upload, scanning telemetry, annotated detections, incident creation, district assignment, and repair ticket lifecycle."
          icon={BrainCircuit}
        />
        <Reveal delay={0.12}>
          <GlassPanel glow="cyan" className="p-5">
            <div className="grid gap-4 sm:grid-cols-4">
              {repairWorkflow.map((step, index) => (
                <motion.div
                  key={step.label}
                  className="rounded-2xl border border-white/10 bg-white/[0.05] p-4"
                  whileHover={{ y: -4 }}
                >
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Step {index + 1}</p>
                  <p className="mt-3 text-2xl font-semibold text-white">{step.value}</p>
                  <h3 className="mt-2 text-sm font-semibold text-civic-cyan">{step.label}</h3>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{step.detail}</p>
                </motion.div>
              ))}
            </div>
            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <Button asChild variant="gradient">
                <Link href="/ai/upload">
                  Open AI upload demo
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button asChild variant="secondary">
                <Link href="/operations/live">
                  View command center
                  <RadioTower className="size-4" />
                </Link>
              </Button>
            </div>
          </GlassPanel>
        </Reveal>
      </div>
    </section>
  );
}

function AnalyticsShowcase() {
  return (
    <section id="analytics" className="safe-x py-14 sm:py-20">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          eyebrow="Executive analytics"
          title="Enterprise-grade metrics without the dashboard clutter."
          body="The analytics view is designed to help a recruiter understand the project quickly: model quality, district performance, response time, closure rate, and infrastructure health."
          icon={BarChart3}
        />
        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {executiveTrends.map((trend) => (
            <Reveal key={trend.label}>
              <div className="rounded-3xl border border-white/10 bg-white/[0.045] p-5 backdrop-blur-2xl">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-400">{trend.label}</p>
                  <span className="rounded-full bg-civic-success/10 px-2 py-1 text-xs font-semibold text-civic-success">{trend.trend}</span>
                </div>
                <p className="mt-4 text-4xl font-semibold text-white">{trend.value}</p>
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-civic-blue via-civic-purple to-civic-cyan"
                    initial={{ width: 0 }}
                    whileInView={{ width: `${trend.value}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.85 }}
                  />
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function EngineeringStory() {
  return (
    <section id="engineering" className="safe-x py-14 sm:py-20">
      <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <SectionHeading
          eyebrow="Engineering depth"
          title="Built to signal thinking beyond CRUD."
          body="The showcase explains the hard parts: computer vision inference, worker queues, real-time event delivery, model telemetry, observability, and a Kubernetes-ready deployment foundation without pretending this local demo is a live city-scale deployment."
          icon={ShieldCheck}
        />
        <Reveal delay={0.14}>
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              ["YOLO inference", "Image/video detection, bounding boxes, confidence, severity, annotated outputs."],
              ["Distributed workers", "Queue-based GPU worker concept with retry, telemetry, and batch throughput storytelling."],
              ["Realtime operations", "Websocket-style feeds, incident transitions, SLA clocks, field repair state."],
              ["Portfolio safety", "Seeded demo mode keeps the app polished when backend infrastructure is unavailable."]
            ].map(([title, body]) => (
              <div key={title} className="rounded-3xl border border-white/10 bg-white/[0.045] p-5 backdrop-blur-2xl">
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-400">{body}</p>
              </div>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
