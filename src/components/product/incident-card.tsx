"use client";

import { motion } from "framer-motion";
import { AlertTriangle, ChevronRight, Clock3, MapPin } from "lucide-react";
import Link from "next/link";
import type { CivicIncident } from "@/types/operations";
import { cn } from "@/lib/utils";

const severityStyle = {
  low: "text-civic-success bg-civic-success/10 border-civic-success/20",
  medium: "text-civic-warning bg-civic-warning/10 border-civic-warning/20",
  high: "text-civic-blue bg-civic-blue/10 border-civic-blue/20",
  critical: "text-civic-danger bg-civic-danger/10 border-civic-danger/20"
};

function formatStatus(status: CivicIncident["lifecycleStatus"]) {
  return status.replaceAll("_", " ");
}

function formatIssue(issueType: CivicIncident["issueType"]) {
  return issueType.replaceAll("_", " ");
}

export function IncidentCard({ incident }: { incident: CivicIncident }) {
  return (
    <motion.div whileHover={{ y: -3 }} transition={{ type: "spring", stiffness: 260, damping: 24 }}>
      <Link
        href={`/reports/${incident.id}`}
        className="block rounded-3xl border border-white/10 bg-white/[0.055] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] backdrop-blur-2xl transition hover:border-civic-cyan/25"
      >
        <div className="flex items-start gap-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-2xl border border-civic-cyan/20 bg-civic-cyan/10">
            <AlertTriangle className="size-5 text-civic-cyan" />
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold capitalize text-white">{formatIssue(incident.issueType)}</p>
                <p className="mt-1 text-xs font-semibold text-slate-500">{incident.id}</p>
              </div>
              <span className={cn("rounded-full border px-2.5 py-1 text-[11px] font-semibold capitalize", severityStyle[incident.severity])}>
                {incident.severity}
              </span>
            </div>
            <div className="mt-4 grid gap-2 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <MapPin className="size-4 text-civic-cyan" />
                <span className="truncate">{incident.address}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock3 className="size-4 text-civic-purple" />
                <span className="capitalize">{formatStatus(incident.lifecycleStatus)} - SLA {new Date(incident.repairTimeline.slaDueAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
                <div className="h-full rounded-full bg-gradient-to-r from-civic-blue to-civic-cyan" style={{ width: `${Math.round(incident.confidenceScore * 100)}%` }} />
              </div>
              <span className="text-xs font-semibold text-slate-300">{Math.round(incident.confidenceScore * 100)}%</span>
              <ChevronRight className="size-4 text-slate-500" />
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
