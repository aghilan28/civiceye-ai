import Link from "next/link";
import { ArrowLeft, RadioTower } from "lucide-react";
import { AuthShell } from "@/components/auth/auth-shell";
import { CivicInput } from "@/components/auth/civic-input";
import { Button } from "@/components/ui/button";

export default function ForgotPasswordPage() {
  return (
    <AuthShell
      title="Restore secure access"
      subtitle="Request a protected access link for your CivicEye operational identity."
      footer={
        <Link href="/auth/login" className="inline-flex items-center gap-2 font-semibold text-civic-cyan">
          <ArrowLeft className="size-4" />
          Back to sign in
        </Link>
      }
    >
      <form className="grid gap-4">
        <CivicInput label="Account email" type="email" placeholder="you@city.gov" autoComplete="email" />
        <div className="rounded-2xl border border-white/10 bg-white/[0.055] p-4">
          <div className="flex items-center gap-3 text-sm font-semibold text-white">
            <RadioTower className="size-5 text-civic-cyan" />
            Secure reset telemetry
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-400">We verify device, session, and municipality context before restoring access.</p>
        </div>
        <Button type="button" size="lg" variant="gradient" className="w-full">
          Send access link
        </Button>
      </form>
    </AuthShell>
  );
}
