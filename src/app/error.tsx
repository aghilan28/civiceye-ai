"use client";

import { AlertTriangle, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <section className="safe-x grid min-h-screen place-items-center py-10">
      <div className="max-w-md rounded-[2rem] border border-white/10 bg-white/[0.055] p-6 text-center shadow-[0_28px_100px_rgba(0,0,0,0.36)] backdrop-blur-2xl">
        <div className="mx-auto grid size-16 place-items-center rounded-full border border-civic-danger/20 bg-civic-danger/10">
          <AlertTriangle className="size-7 text-civic-danger" />
        </div>
        <h1 className="mt-5 text-2xl font-semibold text-white">Operational surface recovered</h1>
        <p className="mt-3 text-sm leading-6 text-slate-400">{error.message || "CivicEye caught an unexpected client error and preserved the current route shell."}</p>
        <Button className="mt-6" variant="gradient" onClick={reset}>
          <RefreshCcw className="size-4" />
          Retry surface
        </Button>
      </div>
    </section>
  );
}
