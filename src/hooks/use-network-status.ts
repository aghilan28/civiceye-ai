"use client";

import { useEffect } from "react";
import { useAppStore } from "@/store/use-app-store";

export function useNetworkStatus() {
  const isOnline = useAppStore((state) => state.isOnline);
  const setOnline = useAppStore((state) => state.setOnline);

  useEffect(() => {
    const syncStatus = () => setOnline(navigator.onLine);
    syncStatus();
    window.addEventListener("online", syncStatus);
    window.addEventListener("offline", syncStatus);

    return () => {
      window.removeEventListener("online", syncStatus);
      window.removeEventListener("offline", syncStatus);
    };
  }, [setOnline]);

  return isOnline;
}
