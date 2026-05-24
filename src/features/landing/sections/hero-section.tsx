"use client";

import { motion } from "framer-motion";
import { ArrowRight, Camera, MapPin, Sparkles, Zap } from "lucide-react";
import Link from "next/link";
import { Reveal } from "@/components/animation/reveal";
import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass-panel";
import { showcaseStats } from "@/data/showcase";

const activityBands = [
  "Queue pressure: 312",
  "GPU workers: 4 hot",
  "District risk: elevated",
  "SLA route: 42s"
];

export function HeroSection() {
  return (
    <section id="platform" className="safe-x relative overflow-hidden pt-8 sm:pt-12">
      <div className="absolute inset-0">
        <div className="city-grid absolute inset-x-[-10%] top-28 h-[42rem] opacity-35" />
        <motion.div
          className="absolute left-1/2 top-28 h-[36rem] w-[36rem] -translate-x-1/2 rounded-full border border-civic-cyan/12"
          animate={{ scale: [0.9, 1.1, 0.92], opacity: [0.18, 0.45, 0.18] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>
      <div className="mx-auto grid max-w-7xl gap-8 pb-12 pt-4 lg:grid-cols-[0.92fr_1.08fr] lg:items-center lg:pt-10">
        <div className="relative z-10">
          <Reveal>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-civic-cyan/25 bg-white/5 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-civic-cyan backdrop-blur-xl">
              <span className="relative flex size-2">
                <span className="absolute inline-flex size-full animate-ping rounded-full bg-civic-cyan opacity-60" />
                <span className="relative inline-flex size-2 rounded-full bg-civic-cyan" />
              </span>
              CivicEye operations intelligence
            </div>
          </Reveal>
          <Reveal delay={0.08}>
            <h1 className="max-w-3xl text-balance text-[3.4rem] font-semibold leading-[0.92] tracking-normal text-white sm:text-7xl">
              AI civic infrastructure operations, presented like a serious startup.
            </h1>
          </Reveal>
          <Reveal delay={0.16}>
            <p className="mt-5 max-w-2xl text-pretty text-lg leading-8 text-slate-300 sm:text-xl">
              CivicEye turns road damage, drainage issues, and repair workflows into a polished command experience with seeded realtime activity, believable AI telemetry, and recruiter-ready engineering storytelling.
            </p>
          </Reveal>
          <Reveal delay={0.24}>
            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg" variant="gradient">
                <Link href="/ai/upload">
                  Open demo flow
                  <ArrowRight className="size-5" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="secondary">
                <Link href="#architecture">
                  View architecture
                  <Sparkles className="size-5" />
                </Link>
              </Button>
            </div>
          </Reveal>
          <Reveal delay={0.32}>
            <div className="mt-8 grid max-w-2xl grid-cols-2 gap-2 rounded-3xl border border-white/10 bg-white/[0.05] p-2 backdrop-blur-2xl sm:grid-cols-4">
              {showcaseStats.map((stat) => (
                <div key={stat.label} className="rounded-2xl bg-black/20 p-3">
                  <p className="text-xl font-semibold text-white">{stat.value}</p>
                  <p className="mt-1 truncate text-[11px] font-medium text-slate-400">{stat.label}</p>
                  <p className="mt-1 truncate text-[10px] text-civic-cyan">{stat.detail}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>

        <Reveal delay={0.12} className="relative min-h-[38rem]">
          <GlassPanel glow="cyan" className="relative overflow-hidden p-4 sm:p-5">
            <div className="relative min-h-[34rem] overflow-hidden rounded-[1.5rem] border border-white/10 bg-[#06101f]">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_20%,rgba(0,212,255,0.24),transparent_24%),radial-gradient(circle_at_78%_35%,rgba(139,92,246,0.16),transparent_26%),radial-gradient(circle_at_50%_82%,rgba(79,140,255,0.18),transparent_28%)]" />
              <div className="city-grid absolute inset-x-[-20%] bottom-[-18%] h-[76%] opacity-80" />
              <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(5,8,22,0.12),rgba(5,8,22,0.86))]" />
              <div className="absolute left-4 right-4 top-4 flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Live operations preview</p>
                  <p className="mt-1 text-lg font-semibold text-white">Bengaluru district mesh</p>
                </div>
                <span className="rounded-full border border-civic-success/20 bg-civic-success/15 px-3 py-1 text-xs font-semibold text-civic-success">ONLINE</span>
              </div>

              <motion.div
                className="absolute left-1/2 top-1/2 grid size-24 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-civic-cyan/20 bg-civic-cyan/10 backdrop-blur-xl"
                animate={{ scale: [1, 1.08, 1] }}
                transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              >
                <motion.span
                  className="absolute inset-0 rounded-full border border-civic-cyan/20"
                  animate={{ scale: [1, 2.3], opacity: [0.55, 0] }}
                  transition={{ duration: 2.8, repeat: Infinity, ease: "easeOut" }}
                />
                <Zap className="relative z-10 size-8 text-civic-cyan" />
              </motion.div>

              {[
                { left: "18%", top: "28%", label: "Road fracture" },
                { left: "56%", top: "22%", label: "Drain overflow" },
                { left: "72%", top: "58%", label: "Repair crew" },
                { left: "34%", top: "68%", label: "District risk" }
              ].map((node, index) => (
                <motion.div
                  key={node.label}
                  className="absolute"
                  style={{ left: node.left, top: node.top }}
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 3.6 + index * 0.4, repeat: Infinity, ease: "easeInOut" }}
                >
                  <span className="absolute -inset-4 animate-ping rounded-full bg-civic-cyan/20" />
                  <span className="relative block size-3 rounded-full bg-civic-cyan shadow-glow" />
                  <span className="absolute left-4 top-[-10px] whitespace-nowrap rounded-full border border-white/10 bg-civic-bg/75 px-2 py-1 text-[10px] font-semibold text-slate-200 backdrop-blur-xl">
                    {node.label}
                  </span>
                </motion.div>
              ))}

              <div className="absolute inset-x-4 bottom-4 grid gap-2 md:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-3 backdrop-blur-xl">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">AI scan</p>
                  <p className="mt-2 text-xl font-semibold text-white">94.8%</p>
                  <p className="mt-1 text-xs text-civic-cyan">confidence mean</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-3 backdrop-blur-xl">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Throughput</p>
                  <p className="mt-2 text-xl font-semibold text-white">18.4 FPS</p>
                  <p className="mt-1 text-xs text-civic-cyan">GPU worker chain</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-3 backdrop-blur-xl">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Repair route</p>
                  <p className="mt-2 text-xl font-semibold text-white">42s</p>
                  <p className="mt-1 text-xs text-civic-cyan">median dispatch</p>
                </div>
              </div>

              <div className="absolute right-4 top-20 w-[16rem] rounded-2xl border border-white/10 bg-civic-bg/75 p-3 backdrop-blur-xl">
                <div className="flex items-center gap-2 text-sm font-semibold text-white">
                  <Camera className="size-4 text-civic-cyan" />
                  Live incident feed
                </div>
                <div className="mt-3 grid gap-2">
                  {activityBands.map((item) => (
                    <div key={item} className="flex items-center gap-2 rounded-xl bg-white/[0.05] px-3 py-2 text-xs text-slate-300">
                      <MapPin className="size-3.5 text-civic-cyan" />
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </GlassPanel>
        </Reveal>
      </div>
    </section>
  );
}
