"use client";

import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { Camera, CheckCircle2, FileVideo, Image as ImageIcon, Loader2, Scan, UploadCloud, Webcam } from "lucide-react";
import { AiAnalyticsPanel } from "@/components/ai/ai-analytics-panel";
import { AiCommandShell } from "@/components/ai/ai-command-shell";
import { AiHealthPanel } from "@/components/ai/ai-health-panel";
import { DetectionTimeline } from "@/components/ai/detection-timeline";
import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass-panel";
import { demoImagePrediction, demoVideoStatus, showcaseMapIntelligence } from "@/data/showcase";
import { aiBackendClient } from "@/services/ai/backend-client";
import type { ImagePredictionResponse, VideoJobStatus, VideoResults } from "@/services/ai/types";

export default function AiUploadPage() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [imageResult, setImageResult] = useState<ImagePredictionResponse | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<VideoJobStatus | null>(null);
  const [videoResults, setVideoResults] = useState<VideoResults | null>(null);
  const [busy, setBusy] = useState(false);
  const [scanState, setScanState] = useState<"idle" | "scanning" | "review" | "converted">("idle");

  const detections = useMemo(() => [...(imageResult?.detections ?? []), ...(videoResults?.detections ?? [])], [imageResult, videoResults]);

  useEffect(() => {
    if (!jobId || jobStatus?.state === "completed" || jobStatus?.state === "failed") {
      return;
    }
    const id = window.setInterval(async () => {
      const status = await aiBackendClient.videoStatus(jobId);
      setJobStatus(status);
      if (status.state === "completed") {
        setVideoResults(await aiBackendClient.videoResults(jobId));
        setScanState("converted");
      }
    }, 1200);
    return () => window.clearInterval(id);
  }, [jobId, jobStatus?.state]);

  const runImage = async () => {
    if (!imageFile) return;
    setBusy(true);
    setScanState("scanning");
    try {
      setImageResult(await aiBackendClient.predictImage(imageFile));
      setScanState("review");
    } finally {
      setBusy(false);
    }
  };

  const runVideo = async () => {
    if (!videoFile) return;
    setBusy(true);
    setScanState("scanning");
    try {
      const job = await aiBackendClient.predictVideo(videoFile);
      setJobId(job.job_id);
      setJobStatus(demoVideoStatus);
      setVideoResults(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AiCommandShell>
      <div className="grid gap-5 xl:grid-cols-[0.96fr_1.04fr]">
        <div className="grid gap-5">
          <GlassPanel glow="cyan" className="p-5">
            <div className="flex items-center gap-3">
              <ImageIcon className="size-5 text-civic-cyan" />
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Image upload</p>
                <h2 className="text-lg font-semibold text-white">Drag, drop, scan, annotate</h2>
              </div>
            </div>
            <label className="mt-4 grid min-h-44 cursor-pointer place-items-center rounded-3xl border border-dashed border-white/15 bg-white/[0.03] p-5 text-center transition hover:border-civic-cyan/40 hover:bg-white/[0.05]">
              <input className="sr-only" type="file" accept="image/*" onChange={(event) => setImageFile(event.target.files?.[0] ?? null)} />
              <div className="max-w-sm">
                <UploadCloud className="mx-auto size-9 text-civic-cyan" />
                <p className="mt-4 text-base font-semibold text-white">Drop a road image or click to select</p>
                <p className="mt-2 text-sm leading-6 text-slate-400">The demo will run seeded detections if the backend is offline, so the UI always feels alive.</p>
              </div>
            </label>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Button variant="gradient" onClick={runImage} disabled={!imageFile || busy}>
                {busy && scanState === "scanning" ? <Loader2 className="size-4 animate-spin" /> : <Scan className="size-4" />}
                Run image scan
              </Button>
              <Button variant="secondary" onClick={() => setScanState("review")}>
                <Camera className="size-4" />
                Webcam preview
              </Button>
              <Button variant="ghost" onClick={() => setImageResult(demoImagePrediction)}>
                <CheckCircle2 className="size-4" />
                Load demo result
              </Button>
            </div>
            <div className="mt-5 rounded-3xl border border-white/10 bg-[#040911] p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-white">AI scan telemetry</p>
                <span className="rounded-full bg-civic-success/10 px-2.5 py-1 text-xs font-semibold text-civic-success">{scanState.toUpperCase()}</span>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                {[
                  ["Frames", "1280x720"],
                  ["Inference", "64 ms"],
                  ["Route", "District escalation"]
                ].map(([label, value]) => (
                  <div key={label} className="rounded-2xl border border-white/10 bg-white/[0.04] p-3">
                    <p className="text-xs uppercase tracking-[0.14em] text-slate-500">{label}</p>
                    <p className="mt-2 text-sm font-semibold text-white">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          </GlassPanel>

          <GlassPanel glow="purple" className="p-5">
            <div className="flex items-center gap-3">
              <FileVideo className="size-5 text-civic-purple" />
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Video processing</p>
                <h2 className="text-lg font-semibold text-white">Queue the full replay</h2>
              </div>
            </div>
            <label className="mt-4 grid min-h-32 cursor-pointer place-items-center rounded-3xl border border-dashed border-white/15 bg-white/[0.03] p-5 text-center transition hover:border-civic-purple/40 hover:bg-white/[0.05]">
              <input className="sr-only" type="file" accept="video/mp4,video/quicktime,video/*" onChange={(event) => setVideoFile(event.target.files?.[0] ?? null)} />
              <div>
                <p className="text-sm font-semibold text-white">Add a dashcam or street sweep clip</p>
                <p className="mt-2 text-sm text-slate-400">The workflow updates as frames arrive, but the seeded fallback keeps the demo smooth.</p>
              </div>
            </label>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button variant="secondary" onClick={runVideo} disabled={!videoFile || busy}>
                {busy ? <Loader2 className="size-4 animate-spin" /> : <UploadCloud className="size-4" />}
                Queue video scan
              </Button>
              <Button variant="ghost" onClick={() => setJobStatus(demoVideoStatus)}>
                <Webcam className="size-4" />
                Live mode UI
              </Button>
            </div>
            {jobStatus ? (
              <div className="mt-4 rounded-3xl border border-white/10 bg-[#040911] p-4">
                <div className="flex items-center justify-between text-sm text-slate-300">
                  <span>{jobStatus.state}</span>
                  <span>{Math.round(jobStatus.progress * 100)}%</span>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-gradient-to-r from-civic-purple to-civic-cyan transition-all" style={{ width: `${Math.round(jobStatus.progress * 100)}%` }} />
                </div>
                <p className="mt-3 text-xs text-slate-500">
                  {jobStatus.frame_index} / {jobStatus.total_frames} frames, {jobStatus.detections} detections, {jobStatus.fps.toFixed(1)} FPS
                </p>
              </div>
            ) : null}
          </GlassPanel>
        </div>

        <div className="grid gap-5">
          {imageResult ? (
            <GlassPanel glow="cyan" className="overflow-hidden p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Detection reveal</p>
                  <h2 className="mt-1 text-lg font-semibold text-white">Annotated incident output</h2>
                </div>
                <span className="rounded-full bg-civic-cyan/10 px-3 py-1 text-xs font-semibold text-civic-cyan">{imageResult.pothole_count} incidents</span>
              </div>
              <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_0.7fr]">
                <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-[#040911]">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_35%_20%,rgba(0,212,255,0.22),transparent_25%),radial-gradient(circle_at_72%_68%,rgba(139,92,246,0.18),transparent_25%)]" />
                  <div className="absolute inset-4 rounded-2xl border border-civic-cyan/25">
                    <motion.div
                      className="absolute left-[16%] top-[44%] h-[24%] w-[28%] rounded-2xl border-2 border-civic-cyan shadow-glow"
                      animate={{ opacity: [0.65, 1, 0.75] }}
                      transition={{ duration: 2.4, repeat: Infinity }}
                    />
                    <motion.div className="absolute right-[14%] top-[24%] h-[20%] w-[18%] rounded-2xl border-2 border-civic-danger shadow-[0_0_24px_rgba(251,113,133,0.32)]" />
                    <motion.div className="absolute right-[18%] bottom-[18%] h-[16%] w-[14%] rounded-2xl border border-civic-warning shadow-[0_0_18px_rgba(251,191,36,0.22)]" />
                  </div>
                  <div className="absolute inset-x-0 top-0 h-16 animate-scan bg-gradient-to-b from-civic-cyan/0 via-civic-cyan/20 to-civic-cyan/0" />
                  <div className="relative flex min-h-[28rem] items-end p-5">
                    <div className="rounded-2xl border border-white/10 bg-civic-bg/80 p-4 backdrop-blur-xl">
                      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Location</p>
                      <p className="mt-1 text-sm font-semibold text-white">MG Road service lane</p>
                      <p className="mt-2 text-xs text-slate-400">12.97218, 77.61254</p>
                    </div>
                  </div>
                </div>
                <div className="grid gap-3">
                  <div className="rounded-3xl border border-white/10 bg-white/[0.05] p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Severity</p>
                    <p className="mt-2 text-3xl font-semibold text-white">Critical</p>
                    <p className="mt-1 text-sm text-slate-400">Repair priority routed to municipal roads.</p>
                  </div>
                  <div className="rounded-3xl border border-white/10 bg-white/[0.05] p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Tags</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {["pothole", "road damage", "district escalation", "AI verified"].map((tag) => (
                        <span key={tag} className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-slate-200">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-3xl border border-white/10 bg-white/[0.05] p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Incident conversion</p>
                    <p className="mt-2 text-sm leading-6 text-slate-300">
                      AI detection becomes incident {showcaseMapIntelligence.incidents[0].incident_code}, routed to district operations with SLA, field crew assignment, and repair proof workflow.
                    </p>
                  </div>
                </div>
              </div>
            </GlassPanel>
          ) : null}

          <div className="grid gap-5 xl:grid-cols-[1fr_1fr]">
            <AiHealthPanel />
            <AiAnalyticsPanel detections={detections} telemetry={imageResult?.telemetry ?? demoImagePrediction.telemetry} />
          </div>
          <DetectionTimeline detections={detections} />
        </div>
      </div>
    </AiCommandShell>
  );
}
