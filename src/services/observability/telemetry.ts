import { logger } from "@/services/observability/logger";

export type TelemetryMetric = {
  name: string;
  value: number;
  unit: "ms" | "count" | "percent" | "bytes";
  tags?: Record<string, string>;
};

export type TraceSpan = {
  name: string;
  correlationId: string;
  startedAt: number;
  end: (metadata?: Record<string, unknown>) => void;
  fail: (error: unknown, metadata?: Record<string, unknown>) => void;
};

export const telemetry = {
  metric(metric: TelemetryMetric) {
    logger.info("metric.recorded", { metric });
  },

  span(name: string, correlationId: string): TraceSpan {
    const startedAt = performance.now();
    return {
      name,
      correlationId,
      startedAt,
      end(metadata) {
        logger.info("trace.completed", {
          name,
          correlationId,
          durationMs: Math.round(performance.now() - startedAt),
          ...metadata
        });
      },
      fail(error, metadata) {
        logger.error("trace.failed", {
          name,
          correlationId,
          durationMs: Math.round(performance.now() - startedAt),
          error: error instanceof Error ? error.message : String(error),
          ...metadata
        });
      }
    };
  }
};
