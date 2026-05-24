"use client";

import { LockKeyhole } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { tokenVault } from "@/services/security/token-vault";
import { useAppStore } from "@/store/use-app-store";

type ProtectedRouteProps = {
  children: ReactNode;
  demoMode?: boolean;
};

export function ProtectedRoute({ children, demoMode = true }: ProtectedRouteProps) {
  const session = useAppStore((state) => state.session);
  const hasToken = Boolean(tokenVault.getAccessToken());

  if (session || hasToken || demoMode) {
    return <>{children}</>;
  }

  return (
    <section className="safe-x grid min-h-screen place-items-center py-10">
      <div className="max-w-md rounded-[2rem] border border-white/10 bg-white/[0.055] p-6 text-center backdrop-blur-2xl">
        <div className="mx-auto grid size-16 place-items-center rounded-full border border-civic-cyan/20 bg-civic-cyan/10 shadow-glow">
          <LockKeyhole className="size-7 text-civic-cyan" />
        </div>
        <h1 className="mt-5 text-2xl font-semibold text-white">Secure CivicEye access required</h1>
        <p className="mt-3 text-sm leading-6 text-slate-400">Sign in to access protected municipal intelligence surfaces.</p>
        <Button asChild className="mt-6" variant="gradient">
          <Link href="/auth/login">Sign in</Link>
        </Button>
      </div>
    </section>
  );
}
