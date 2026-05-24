"use client";

import { useEffect, useRef, useState } from "react";
import { Camera, Pause, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { YoloLiveClient } from "@/services/ai/yolo-live-client";
import type { CivicDetection, InferenceTelemetry, LiveInferenceEvent } from "@/services/ai/types";

export function LiveCameraPanel({ onInference }: { onInference: (detections: CivicDetection[], telemetry: InferenceTelemetry) => void }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const clientRef = useRef<YoloLiveClient | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [annotatedFrame, setAnnotatedFrame] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "connecting" | "open" | "closed" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [lastEvent, setLastEvent] = useState<LiveInferenceEvent | null>(null);

  useEffect(() => {
    return () => stop();
  }, []);

  const start = async () => {
    if (!videoRef.current || !canvasRef.current) {
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: 1280, height: 720 }, audio: false });
    streamRef.current = stream;
    videoRef.current.srcObject = stream;
    await videoRef.current.play();
    const client = new YoloLiveClient(
      videoRef.current,
      canvasRef.current,
      {
        onInference: (event) => {
          setAnnotatedFrame(event.annotatedFrame);
          setLastEvent(event);
          onInference(event.detections, {
            model_version: "live-yolov8",
            device: "backend",
            cuda_available: true,
            half_precision: true,
            latency_ms: event.latencyMs,
            fps: event.fps
          });
        },
        onStatus: setStatus,
        onError: setError
      },
      "webcam"
    );
    clientRef.current = client;
    client.connect();
  };

  const stop = () => {
    clientRef.current?.close();
    clientRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setStatus("closed");
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-black shadow-[0_28px_100px_rgba(0,0,0,0.42)]">
      <video ref={videoRef} className="aspect-video w-full object-cover opacity-40" playsInline muted />
      {annotatedFrame ? <img src={annotatedFrame} alt="YOLO annotated live inference frame" className="absolute inset-0 size-full object-cover" /> : null}
      <canvas ref={canvasRef} className="hidden" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(0,0,0,0.12),rgba(0,0,0,0.58))]" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 animate-scan bg-gradient-to-b from-civic-cyan/20 to-transparent" />
      <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full border border-civic-cyan/30 bg-black/60 px-3 py-1 text-xs font-semibold text-civic-cyan backdrop-blur">
        <Camera className="size-3.5" />
        {status}
      </div>
      <div className="absolute right-4 top-4 rounded-full border border-white/10 bg-black/60 px-3 py-1 text-xs font-semibold text-white backdrop-blur">
        {lastEvent?.fps.toFixed(1) ?? "0.0"} FPS / {lastEvent?.latencyMs.toFixed(0) ?? "0"} ms
      </div>
      <div className="absolute inset-x-4 bottom-4 flex flex-wrap items-center justify-between gap-3">
        <div className="rounded-xl border border-white/10 bg-black/60 px-4 py-3 backdrop-blur">
          <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Active detections</p>
          <p className="mt-1 text-2xl font-semibold text-white">{lastEvent?.potholeCount ?? 0}</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={start} size="sm" variant="gradient" disabled={status === "open" || status === "connecting"}>
            <Play className="size-4" />
            Start
          </Button>
          <Button onClick={stop} size="sm" variant="secondary">
            <Pause className="size-4" />
            Stop
          </Button>
        </div>
      </div>
      {error ? <div className="absolute bottom-24 left-4 right-4 rounded-xl border border-civic-danger/25 bg-civic-danger/15 p-3 text-sm text-civic-danger">{error}</div> : null}
    </div>
  );
}

