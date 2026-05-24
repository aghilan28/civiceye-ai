"use client";

import { useEffect } from "react";
import { logger } from "@/services/observability/logger";

export function PwaProvider() {
  useEffect(() => {
    if (!("serviceWorker" in navigator) || process.env.NODE_ENV !== "production") {
      return;
    }

    navigator.serviceWorker
      .register("/sw.js")
      .then((registration) => {
        logger.info("pwa.service_worker.registered", { scope: registration.scope });
      })
      .catch((error) => {
        logger.warn("pwa.service_worker.failed", { error: error instanceof Error ? error.message : String(error) });
      });
  }, []);

  return null;
}
