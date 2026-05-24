"use client";

import { Bell } from "lucide-react";
import { PageHeader } from "@/components/product/page-header";
import { ConnectionHealth } from "@/components/realtime/connection-health";
import { useLiveOperations } from "@/hooks/use-live-operations";
import { useRealtimeIntelligence } from "@/hooks/use-realtime-intelligence";
import { notifications } from "@/lib/product-data";
import { buildOperationalAlerts } from "@/services/alerts/alert-engine";
import { useAppStore } from "@/store/use-app-store";

export default function NotificationsPage() {
  useLiveOperations();
  useRealtimeIntelligence();
  const incidents = useAppStore((state) => state.incidents);
  const forecasts = useAppStore((state) => state.riskForecasts);
  const alerts = buildOperationalAlerts(incidents, forecasts);

  return (
    <section className="safe-x py-8 sm:py-12">
      <div className="mx-auto max-w-4xl">
        <PageHeader eyebrow="AI alerts" title="Notifications" description="Operational updates from AI verification, municipal routing, field response, and predictive alerting." action={<ConnectionHealth />} />
        <div className="mt-6 grid gap-3">
          {alerts.map((alert) => (
            <div key={alert.id} className="rounded-3xl border border-civic-danger/20 bg-civic-danger/10 p-4 backdrop-blur-2xl">
              <div className="flex items-center gap-3">
                <span className="grid size-12 place-items-center rounded-2xl bg-civic-danger/10">
                  <Bell className="size-5 text-civic-danger" />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-white">{alert.title}</p>
                  <p className="mt-1 text-sm text-slate-300">{alert.body}</p>
                </div>
              </div>
            </div>
          ))}
          {notifications.map((notification) => {
            const Icon = notification.icon;
            return (
              <div key={notification.title} className="rounded-3xl border border-white/10 bg-white/[0.055] p-4 backdrop-blur-2xl">
                <div className="flex items-center gap-3">
                  <span className="grid size-12 place-items-center rounded-2xl bg-civic-cyan/10">
                    <Icon className="size-5 text-civic-cyan" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-white">{notification.title}</p>
                    <p className="mt-1 text-sm text-slate-400">{notification.body}</p>
                  </div>
                  <span className="ml-auto text-xs text-slate-500">{notification.time}</span>
                </div>
              </div>
            );
          })}
          <div className="rounded-3xl border border-white/10 bg-civic-bg/58 p-5 text-center">
            <Bell className="mx-auto size-7 text-civic-cyan" />
            <p className="mt-3 text-sm font-semibold text-white">AI alert stream connected</p>
          </div>
        </div>
      </div>
    </section>
  );
}
