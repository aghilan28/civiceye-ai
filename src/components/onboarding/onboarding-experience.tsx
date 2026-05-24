"use client";

import { motion } from "framer-motion";
import { ArrowRight, ChevronLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { onboardingSteps, roleOptions } from "@/lib/product-data";
import { useAppStore } from "@/store/use-app-store";

type OnboardingExperienceProps = {
  slug: string;
};

export function OnboardingExperience({ slug }: OnboardingExperienceProps) {
  const router = useRouter();
  const stepIndex = Math.max(0, onboardingSteps.findIndex((step) => step.slug === slug));
  const step = onboardingSteps[stepIndex] ?? onboardingSteps[0];
  const Icon = step.icon;
  const nextStep = onboardingSteps[stepIndex + 1];
  const previousStep = onboardingSteps[stepIndex - 1];
  const setOnboardingStep = useAppStore((state) => state.setOnboardingStep);

  function goNext() {
    setOnboardingStep(stepIndex + 1);
    if (nextStep) {
      router.push(`/onboarding/${nextStep.slug}`);
      return;
    }
    router.push("/dashboard");
  }

  return (
    <section className="safe-x relative min-h-screen overflow-hidden py-5">
      <div className="mx-auto flex min-h-[calc(100vh-2.5rem)] max-w-5xl flex-col">
        <div className="flex items-center justify-between">
          {previousStep ? (
            <Link href={`/onboarding/${previousStep.slug}`} className="grid size-11 place-items-center rounded-2xl border border-white/10 bg-white/[0.055] text-white backdrop-blur-xl">
              <ChevronLeft className="size-5" />
            </Link>
          ) : (
            <Link href="/" className="text-sm font-semibold text-slate-300">CivicEye</Link>
          )}
          <Link href="/dashboard" className="text-sm font-semibold text-slate-400">Skip</Link>
        </div>

        <div className="grid flex-1 content-center gap-8 py-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <motion.div
            key={step.slug}
            initial={{ opacity: 0, x: -18, filter: "blur(10px)" }}
            animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-civic-cyan/20 bg-civic-cyan/10 px-3 py-2 text-xs font-semibold text-civic-cyan">
              <Icon className="size-4" />
              {step.eyebrow}
            </div>
            <h1 className="text-balance text-4xl font-semibold leading-tight tracking-normal text-white sm:text-6xl">{step.title}</h1>
            <p className="mt-5 text-pretty text-base leading-7 text-slate-300 sm:text-lg">{step.body}</p>

            {step.slug === "role-selection" ? (
              <div className="mt-7 grid gap-3 sm:grid-cols-2">
                {roleOptions.map((role) => {
                  const RoleIcon = role.icon;
                  return (
                    <button key={role.title} className="rounded-3xl border border-white/10 bg-white/[0.055] p-4 text-left transition hover:border-civic-cyan/30 hover:bg-civic-cyan/8">
                      <RoleIcon className="size-5 text-civic-cyan" />
                      <p className="mt-3 text-sm font-semibold text-white">{role.title}</p>
                      <p className="mt-1 text-xs leading-5 text-slate-400">{role.description}</p>
                    </button>
                  );
                })}
              </div>
            ) : null}

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button size="lg" variant="gradient" onClick={goNext}>
                {step.primary}
                <ArrowRight className="size-5" />
              </Button>
              {step.secondary ? (
                <Button size="lg" variant="secondary" onClick={goNext}>
                  {step.secondary}
                </Button>
              ) : null}
            </div>
          </motion.div>

          <motion.div
            key={`${step.slug}-visual`}
            initial={{ opacity: 0, scale: 0.94, y: 18 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
            className="relative min-h-[30rem] overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 shadow-[0_28px_90px_rgba(0,0,0,0.34)] backdrop-blur-2xl"
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_42%_22%,rgba(0,212,255,0.24),transparent_28%),radial-gradient(circle_at_70%_72%,rgba(139,92,246,0.18),transparent_28%)]" />
            <div className="city-grid absolute inset-x-[-25%] bottom-[-18%] h-[70%] opacity-70" />
            <div className="relative grid h-full min-h-[28rem] place-items-center">
              <motion.div
                className="grid size-36 place-items-center rounded-full border border-civic-cyan/20 bg-civic-cyan/10 shadow-glow backdrop-blur-xl"
                animate={{ y: [0, -10, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              >
                <motion.span
                  className="absolute size-36 rounded-full border border-civic-cyan/20"
                  animate={{ scale: [1, 2.1], opacity: [0.5, 0] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeOut" }}
                />
                <Icon className="relative size-14 text-civic-cyan" />
              </motion.div>
            </div>
          </motion.div>
        </div>

        <div className="grid grid-cols-5 gap-2 pb-safe">
          {onboardingSteps.map((item, index) => (
            <div key={item.slug} className="h-1.5 overflow-hidden rounded-full bg-white/10">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-civic-blue to-civic-cyan"
                animate={{ width: index <= stepIndex ? "100%" : "0%" }}
                transition={{ duration: 0.35 }}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
