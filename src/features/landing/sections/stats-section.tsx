"use client";

import { motion, useInView, useMotionValue, useSpring, useTransform } from "framer-motion";
import { Activity, TrendingUp } from "lucide-react";
import { useEffect, useRef } from "react";
import { Reveal } from "@/components/animation/reveal";
import { platformStats } from "@/features/landing/data";

function AnimatedValue({ value, suffix }: { value: number; suffix: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, { stiffness: 90, damping: 24 });
  const displayValue = useTransform(springValue, (latest) => {
    const rounded = value % 1 === 0 ? Math.round(latest).toString() : latest.toFixed(1);
    return `${rounded}${suffix}`;
  });

  useEffect(() => {
    if (inView) {
      motionValue.set(value);
    }
  }, [inView, motionValue, value]);

  return <motion.span ref={ref}>{displayValue}</motion.span>;
}

export function StatsSection() {
  return (
    <section id="analytics" className="safe-x py-10 sm:py-14">
      <div className="mx-auto max-w-7xl">
        <Reveal>
          <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-2 shadow-[0_28px_90px_rgba(0,0,0,0.28)] backdrop-blur-2xl">
            <div className="mb-2 flex items-center justify-between px-3 pt-3">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                <Activity className="size-4 text-civic-cyan" />
                Live telemetry
              </div>
              <span className="rounded-full bg-civic-success/12 px-3 py-1 text-xs font-semibold text-civic-success">streaming</span>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {platformStats.map((stat, index) => (
                <motion.div
                  key={stat.label}
                  whileHover={{ y: -5, scale: 1.01 }}
                  transition={{ type: "spring", stiffness: 260, damping: 22 }}
                  className="group relative overflow-hidden rounded-[1.45rem] border border-white/10 bg-civic-surface/76 p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.10)]"
                >
                  <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-civic-cyan/70 to-transparent opacity-0 transition group-hover:opacity-100" />
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-3xl font-semibold tracking-normal text-white">
                      <AnimatedValue value={stat.numeric} suffix={stat.suffix} />
                    </p>
                    <span className="inline-flex items-center gap-1 rounded-full border border-civic-cyan/15 bg-civic-cyan/10 px-2 py-1 text-[11px] font-semibold text-civic-cyan">
                      <TrendingUp className="size-3" />
                      {stat.trend}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{stat.label}</p>
                  <div className="mt-4 grid grid-cols-12 gap-1">
                    {Array.from({ length: 12 }).map((_, barIndex) => (
                      <motion.span
                        key={barIndex}
                        initial={{ height: 8, opacity: 0.3 }}
                        whileInView={{ height: 8 + ((barIndex * 13 + index * 9) % 28), opacity: 0.8 }}
                        viewport={{ once: true }}
                        transition={{ delay: barIndex * 0.025, duration: 0.45 }}
                        className="self-end rounded-full bg-gradient-to-t from-civic-blue/40 to-civic-cyan"
                      />
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
