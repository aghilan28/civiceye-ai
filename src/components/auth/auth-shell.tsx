import type { ReactNode } from "react";
import Link from "next/link";
import { CivicLogo } from "@/components/product/civic-logo";

type AuthShellProps = {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
};

export function AuthShell({ title, subtitle, children, footer }: AuthShellProps) {
  return (
    <section className="safe-x relative min-h-screen overflow-hidden py-6">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-6xl flex-col justify-between gap-8">
        <Link href="/" aria-label="CivicEye home" className="w-fit">
          <CivicLogo />
        </Link>
        <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div className="hidden lg:block">
            <div className="relative min-h-[34rem] overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.045] p-6 backdrop-blur-2xl">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_35%_25%,rgba(0,212,255,0.24),transparent_28%),radial-gradient(circle_at_72%_72%,rgba(139,92,246,0.18),transparent_28%)]" />
              <div className="city-grid absolute inset-x-[-25%] bottom-[-20%] h-[72%] opacity-70" />
              <div className="relative rounded-3xl border border-white/10 bg-civic-bg/60 p-5 backdrop-blur-xl">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Secure access</p>
                <h2 className="mt-3 text-3xl font-semibold text-white">Enter the city intelligence network.</h2>
                <p className="mt-3 text-sm leading-6 text-slate-300">AI telemetry, incident routing, and response coordination are protected behind operational identity.</p>
              </div>
              <div className="absolute bottom-6 left-6 right-6 grid gap-3">
                {["Biometric-ready session", "JWT service boundary", "Municipality-grade audit trail"].map((item) => (
                  <div key={item} className="rounded-2xl border border-white/10 bg-civic-bg/70 p-4 text-sm font-semibold text-slate-200 backdrop-blur-xl">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="rounded-[2rem] border border-white/10 bg-civic-bg/72 p-5 shadow-[0_28px_100px_rgba(0,0,0,0.36)] backdrop-blur-2xl sm:p-8">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-civic-cyan">CivicEye access</p>
              <h1 className="mt-3 text-3xl font-semibold tracking-normal text-white sm:text-5xl">{title}</h1>
              <p className="mt-3 text-sm leading-6 text-slate-300 sm:text-base">{subtitle}</p>
            </div>
            <div className="mt-7">{children}</div>
            <div className="mt-6 text-center text-sm text-slate-400">{footer}</div>
          </div>
        </div>
      </div>
    </section>
  );
}
