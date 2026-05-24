import Link from "next/link";
import { ArrowRight, Building2, Camera, ShieldCheck } from "lucide-react";
import { AuthShell } from "@/components/auth/auth-shell";
import { CivicInput } from "@/components/auth/civic-input";
import { Button } from "@/components/ui/button";

export default function SignupPage() {
  return (
    <AuthShell
      title="Join the civic AI network"
      subtitle="Create an operational identity for reporting, response coordination, and smart-city analytics."
      footer={
        <>
          Already onboarded?{" "}
          <Link href="/auth/login" className="font-semibold text-civic-cyan">
            Sign in
          </Link>
        </>
      }
    >
      <form className="grid gap-4">
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            { label: "Citizen network", icon: Camera },
            { label: "Municipality team", icon: Building2 }
          ].map((option) => {
            const Icon = option.icon;
            return (
              <button key={option.label} type="button" className="rounded-2xl border border-white/10 bg-white/[0.055] p-4 text-left transition hover:border-civic-cyan/30 hover:bg-civic-cyan/8">
                <Icon className="size-5 text-civic-cyan" />
                <p className="mt-3 text-sm font-semibold text-white">{option.label}</p>
              </button>
            );
          })}
        </div>
        <CivicInput label="Full name" placeholder="Aarav Mehta" autoComplete="name" />
        <CivicInput label="Email" type="email" placeholder="you@example.com" autoComplete="email" />
        <CivicInput label="Password" type="password" placeholder="Create secure access" autoComplete="new-password" />
        <div className="rounded-2xl border border-civic-success/20 bg-civic-success/10 p-4">
          <div className="flex items-center gap-3 text-sm font-semibold text-civic-success">
            <ShieldCheck className="size-5" />
            AI-assisted onboarding included
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-400">CivicEye will personalize reporting, permissions, and operational views after signup.</p>
        </div>
        <Button asChild size="lg" variant="gradient" className="w-full">
          <Link href="/onboarding/welcome">
            Continue onboarding
            <ArrowRight className="size-5" />
          </Link>
        </Button>
      </form>
    </AuthShell>
  );
}
