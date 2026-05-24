"use client";

import { useMemo, useState } from "react";
import { AiAnalyticsPanel } from "@/components/ai/ai-analytics-panel";
import { AiCommandShell } from "@/components/ai/ai-command-shell";
import { AiHealthPanel } from "@/components/ai/ai-health-panel";
import { DetectionTimeline } from "@/components/ai/detection-timeline";
import { LiveCameraPanel } from "@/components/ai/live-camera-panel";
import type { CivicDetection, InferenceTelemetry } from "@/services/ai/types";

export default function AiLivePage() {
  const [detections, setDetections] = useState<CivicDetection[]>([]);
  const [telemetry, setTelemetry] = useState<InferenceTelemetry | null>(null);
  const rollingDetections = useMemo(() => detections.slice(0, 120), [detections]);

  return (
    <AiCommandShell>
      <div className="grid gap-5 xl:grid-cols-[1.35fr_0.65fr]">
        <div className="grid gap-5">
          <LiveCameraPanel
            onInference={(items, eventTelemetry) => {
              setTelemetry(eventTelemetry);
              if (items.length > 0) {
                setDetections((current) => [...items, ...current].slice(0, 240));
              }
            }}
          />
          <AiAnalyticsPanel detections={rollingDetections} telemetry={telemetry} />
        </div>
        <div className="grid gap-5">
          <AiHealthPanel />
          <DetectionTimeline detections={rollingDetections} />
        </div>
      </div>
    </AiCommandShell>
  );
}

