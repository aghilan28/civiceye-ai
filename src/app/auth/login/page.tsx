"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Fingerprint, LockKeyhole, Mail } from "lucide-react";
import { AuthShell } from "@/components/auth/auth-shell";
import { CivicInput } from "@/components/auth/civic-input";
import { Button } from "@/components/ui/button";
import { authService } from "@/services/auth/auth-service";
import { useAppStore } from "@/store/use-app-store";

export default function LoginPage() {
  const router = useRouter();
  const setSession = useAppStore((state) => state.setSession);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    try {
      const session = await authService.login({
        email: String(form.get("email") || ""),
        password: String(form.get("password") || ""),
        municipality_id: String(form.get("municipality_id") || "MUNI-BLR"),
        role: "municipality_admin"
      });
      setSession(session);
      router.push("/dashboard");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to sign in");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title="Access command network"
      subtitle="Sign in to review AI-verified incidents, dispatch civic response, and track infrastructure telemetry."
      footer={
        <>
          New to CivicEye?{" "}
          <Link href="/auth/signup" className="font-semibold text-civic-cyan">
            Create an account
          </Link>
        </>
      }
    >
      <form className="grid gap-4" onSubmit={handleSubmit}>
        <CivicInput label="Municipality ID" name="municipality_id" defaultValue="MUNI-BLR" autoComplete="organization" />
        <CivicInput label="Operational email" name="email" type="email" placeholder="you@city.gov" autoComplete="email" />
        <CivicInput label="Secure password" name="password" type="password" placeholder="••••••••" autoComplete="current-password" />
        <div className="flex items-center justify-between gap-3 text-sm">
          <label className="flex items-center gap-2 text-slate-400">
            <input type="checkbox" className="size-4 rounded border-white/20 bg-white/10 accent-civic-cyan" />
            Keep session active
          </label>
          <Link href="/auth/forgot-password" className="font-semibold text-civic-cyan">
            Reset access
          </Link>
        </div>
        {error ? <p className="rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">{error}</p> : null}
        <Button type="submit" size="lg" variant="gradient" className="mt-2 w-full" disabled={loading}>
          <Fingerprint className="size-5" />
          {loading ? "Signing in" : "Enter CivicEye"}
        </Button>
        <div className="grid grid-cols-2 gap-3">
          <Button type="button" variant="secondary">
            <Mail className="size-4" />
            SSO
          </Button>
          <Button type="button" variant="secondary">
            <LockKeyhole className="size-4" />
            Passkey
          </Button>
        </div>
      </form>
    </AuthShell>
  );
}
