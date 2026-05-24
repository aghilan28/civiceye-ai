"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { OperationsShell } from "@/components/operations/operations-shell";
import { OperationalSkeleton } from "@/components/product/operational-skeleton";
import { showcaseMapIntelligence } from "@/data/showcase";
import { enterpriseApi } from "@/services/enterprise/enterprise-api";
import type { MapIntelligence } from "@/types/enterprise";

const EnterpriseCommandMap = dynamic(() => import("@/components/maps/enterprise-command-map").then((module) => module.EnterpriseCommandMap), {
  ssr: false,
  loading: () => (
    <div className="min-h-[42rem] rounded-lg border border-white/10 bg-white/[0.045] p-5 backdrop-blur-2xl">
      <OperationalSkeleton rows={4} />
    </div>
  )
});

export default function OperationsMapPage() {
  const [intelligence, setIntelligence] = useState<MapIntelligence | null>(null);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    function refresh() {
      enterpriseApi
        .mapIntelligence(controller.signal)
        .then((snapshot) => {
          setIntelligence(snapshot);
          setLoadState("ready");
        })
        .catch(() => {
          setIntelligence(showcaseMapIntelligence);
          setLoadState("ready");
        });
    }
    refresh();
    const connection = enterpriseApi.connectEvents((event) => {
      if (
        event.type === "incident_created" ||
        event.type === "incident_updated" ||
        event.type === "worker_assigned" ||
        event.type === "repair_started" ||
        event.type === "repair_completed" ||
        event.type === "severity_changed" ||
        event.type === "emergency_alert"
      ) {
        refresh();
      }
    });
    const interval = window.setInterval(refresh, 30000);
    return () => {
      controller.abort();
      connection.close();
      window.clearInterval(interval);
    };
  }, []);

  return (
    <OperationsShell eyebrow="GIS digital twin" title="Infrastructure map">
      {loadState === "loading" ? (
        <div className="min-h-[42rem] rounded-lg border border-white/10 bg-white/[0.045] p-5 backdrop-blur-2xl">
          <OperationalSkeleton rows={5} />
        </div>
      ) : null}
      {loadState === "error" ? null : null}
      {intelligence ? <EnterpriseCommandMap intelligence={intelligence} /> : null}
    </OperationsShell>
  );
}
