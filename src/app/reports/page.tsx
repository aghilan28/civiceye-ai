"use client";

import { Filter, Search } from "lucide-react";
import { IncidentCard } from "@/components/product/incident-card";
import { OperationalSkeleton } from "@/components/product/operational-skeleton";
import { PageHeader } from "@/components/product/page-header";
import { Button } from "@/components/ui/button";
import { useLiveOperations } from "@/hooks/use-live-operations";
import { useAppStore } from "@/store/use-app-store";

export default function ReportsPage() {
  useLiveOperations();
  const incidents = useAppStore((state) => state.incidents);
  const loading = useAppStore((state) => state.loading.dashboard);

  return (
    <section className="safe-x py-8 sm:py-12">
      <div className="mx-auto max-w-6xl">
        <PageHeader
          eyebrow="Incident registry"
          title="Reports"
          description="Review submitted, AI-verified, assigned, escalated, and resolved infrastructure incidents."
          action={<Button variant="secondary"><Filter className="size-4" />Filter</Button>}
        />
        <div className="mt-6 flex items-center gap-3 rounded-3xl border border-white/10 bg-white/[0.055] p-3 backdrop-blur-2xl">
          <Search className="size-5 text-slate-500" />
          <input className="h-11 flex-1 bg-transparent text-sm font-medium text-white outline-none placeholder:text-slate-600" placeholder="Search by ward, issue, report ID, or department" />
        </div>
        <div className="mt-5 grid gap-3">
          {loading ? <OperationalSkeleton rows={4} /> : incidents.map((incident) => <IncidentCard key={incident.id} incident={incident} />)}
        </div>
      </div>
    </section>
  );
}
