"use client";

import { useEffect, useState } from "react";
import { aiBackendClient } from "@/services/ai/backend-client";
import type { BackendHealth, BackendMetrics } from "@/services/ai/types";

export function useAiBackendHealth() {
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [metrics, setMetrics] = useState<BackendMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      try {
        const [healthPayload, metricsPayload] = await Promise.all([
          aiBackendClient.health(controller.signal),
          aiBackendClient.metrics(controller.signal)
        ]);
        setHealth(healthPayload);
        setMetrics(metricsPayload);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "AI backend unavailable");
      }
    };
    void load();
    const id = window.setInterval(load, 4000);
    return () => {
      controller.abort();
      window.clearInterval(id);
    };
  }, []);

  return { health, metrics, error };
}

