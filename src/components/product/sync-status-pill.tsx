"use client";

import { Cloud, CloudOff } from "lucide-react";
import { useNetworkStatus } from "@/hooks/use-network-status";

export function SyncStatusPill() {
  const isOnline = useNetworkStatus();

  return (
    <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-semibold ${isOnline ? "border-civic-success/20 bg-civic-success/10 text-civic-success" : "border-civic-warning/20 bg-civic-warning/10 text-civic-warning"}`}>
      {isOnline ? <Cloud className="size-4" /> : <CloudOff className="size-4" />}
      {isOnline ? "Live sync" : "Offline queue"}
    </div>
  );
}
