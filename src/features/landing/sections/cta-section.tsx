import { ArrowRight, Building2, Sparkles } from "lucide-react";
import { Reveal } from "@/components/animation/reveal";
import { Button } from "@/components/ui/button";

export function CtaSection() {
  return (
    <section className="safe-x py-14 sm:py-20">
      <Reveal>
        <div className="relative mx-auto max-w-7xl overflow-hidden rounded-[2rem] border border-civic-cyan/20 bg-gradient-to-br from-civic-blue/24 via-civic-purple/18 to-civic-cyan/14 p-6 shadow-[0_30px_120px_rgba(0,212,255,0.16)] backdrop-blur-2xl sm:p-10">
          <div aria-hidden="true" className="absolute -right-24 -top-28 size-72 rounded-full bg-civic-cyan/20 blur-3xl" />
          <div aria-hidden="true" className="absolute -bottom-28 left-10 size-72 rounded-full bg-civic-purple/18 blur-3xl" />
          <div className="relative grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-2 text-xs font-semibold text-white">
                <Building2 className="size-4" />
                Smart city deployment ready
              </div>
              <h2 className="text-balance text-3xl font-semibold tracking-normal text-white sm:text-5xl">
                Turn scattered civic complaints into an AI operating system.
              </h2>
              <p className="mt-4 max-w-2xl text-pretty text-base leading-7 text-slate-200">
                CivicEye gives cities a cinematic but practical command layer for AI reporting, live dashboards, response routing, and infrastructure intelligence.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row lg:flex-col">
              <Button size="lg">
                <Sparkles className="size-5" />
                Book pilot
                <ArrowRight className="size-5" />
              </Button>
              <Button size="lg" variant="secondary">
                View architecture
              </Button>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
