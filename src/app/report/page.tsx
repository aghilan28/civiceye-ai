"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowRight, Camera, CheckCircle2, ImagePlus, MapPin, UploadCloud } from "lucide-react";
import { AiScanVisual } from "@/components/product/ai-scan-visual";
import { BottomSheet } from "@/components/product/bottom-sheet";
import { PageHeader } from "@/components/product/page-header";
import { SyncStatusPill } from "@/components/product/sync-status-pill";
import { Button } from "@/components/ui/button";
import { issueTypes, scanStages } from "@/lib/product-data";
import { inferenceService } from "@/services/ai/inference-service";
import { incidentService } from "@/services/incidents/incident-service";
import { uploadService } from "@/services/media/upload-service";
import { notificationService } from "@/services/notifications/notification-service";
import { offlineSyncService } from "@/services/offline/offline-sync-service";
import { useAppStore } from "@/store/use-app-store";

export default function ReportPage() {
  const reportFlow = useAppStore((state) => state.reportFlow);
  const setReportFlow = useAppStore((state) => state.setReportFlow);
  const upsertIncident = useAppStore((state) => state.upsertIncident);
  const isOnline = useAppStore((state) => state.isOnline);
  const setLoading = useAppStore((state) => state.setLoading);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (reportFlow.step !== "scanning") {
      return;
    }

    const interval = window.setInterval(() => {
      setReportFlow({
        scanStage: Math.min(reportFlow.scanStage + 1, scanStages.length - 1)
      });
    }, 800);

    if (reportFlow.scanStage >= scanStages.length - 1) {
      window.clearInterval(interval);
      window.setTimeout(() => setReportFlow({ step: "result" }), 550);
    }

    return () => window.clearInterval(interval);
  }, [reportFlow.scanStage, reportFlow.step, setReportFlow]);

  async function runAiReportPipeline() {
    if (!selectedImage) {
      setReportFlow({ scanError: "Select a real road image before running AI analysis." });
      fileInputRef.current?.click();
      return;
    }

    setReportFlow({ step: "scanning", scanStage: 0, scanError: null, uploadProgress: 0 });
    setLoading({ upload: true });

    try {
      const location = await resolveDeviceLocation();
      const uploadedImage = await uploadService.uploadIncidentImage({
        file: selectedImage,
        onProgress: (progress) => setReportFlow({ uploadProgress: progress.progress })
      });
      const detection = await inferenceService.analyzeImage({
        image: selectedImage,
        location,
        preferredIssueType: reportFlow.selectedIssueType
      });
      const incident = await incidentService.createIncident({
        issueType: detection.issueType,
        confidenceScore: detection.confidence,
        severity: detection.severity,
        location,
        address: detection.metadata.geoContext.address,
        images: [uploadedImage],
        ai: detection.metadata
      });

      if (!isOnline) {
        await offlineSyncService.enqueue("create_report", incident);
      }

      upsertIncident(incident);
      notificationService.create("ai_verified", "AI verification complete", `${incident.id} is ready for municipal review.`, incident.id);
      setReportFlow({ createdIncidentId: incident.id });
    } catch (error) {
      setReportFlow({ scanError: error instanceof Error ? error.message : "AI report pipeline failed" });
    } finally {
      setLoading({ upload: false });
    }
  }

  function handleImageSelected(file: File | null) {
    if (!file) {
      return;
    }
    if (!file.type.startsWith("image/")) {
      setReportFlow({ scanError: "CivicEye accepts image files for this report flow." });
      return;
    }
    setSelectedImage(file);
    setReportFlow({ step: "preview", scanError: null, uploadPreviewUrl: URL.createObjectURL(file) });
  }

  return (
    <section className="safe-x py-8 sm:py-12">
      <div className="mx-auto max-w-6xl">
        <PageHeader
          eyebrow="AI report flow"
          title="Report infrastructure issue"
          description="Capture or upload civic evidence, let CivicEye scan it, then submit a geotagged operational incident."
          action={
            <div className="flex flex-wrap gap-3">
              <SyncStatusPill />
              <Button variant="secondary" onClick={() => setSheetOpen(true)}>Upload options</Button>
            </div>
          }
        />

        <div className="mt-8 grid gap-5 lg:grid-cols-[0.92fr_1.08fr]">
          <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
            <div className="grid gap-3">
              {[
                { step: "capture", label: "Capture or upload", icon: Camera },
                { step: "preview", label: "Smart preview", icon: ImagePlus },
                { step: "scanning", label: "AI scanning", icon: UploadCloud },
                { step: "result", label: "Detection result", icon: CheckCircle2 }
              ].map((item, index) => {
                const Icon = item.icon;
                const active = reportFlow.step === item.step;
                return (
                  <button
                    key={item.step}
                    onClick={() => setReportFlow({ step: item.step as typeof reportFlow.step })}
                    className={`flex items-center gap-3 rounded-2xl border p-4 text-left transition ${active ? "border-civic-cyan/30 bg-civic-cyan/10 text-white shadow-glow" : "border-white/10 bg-white/[0.045] text-slate-400"}`}
                  >
                    <Icon className={active ? "size-5 text-civic-cyan" : "size-5"} />
                    <div>
                      <p className="text-sm font-semibold">{item.label}</p>
                      <p className="text-xs text-slate-500">Step 0{index + 1}</p>
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="mt-5 rounded-3xl border border-white/10 bg-civic-bg/58 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Issue category</p>
              <div className="mt-3 grid grid-cols-2 gap-2">
                {issueTypes.map((issue) => {
                  const Icon = issue.icon;
                  const selected = reportFlow.selectedIssueType === issue.value;
                  return (
                    <button
                      key={issue.value}
                      onClick={() => setReportFlow({ selectedIssueType: issue.value })}
                      className={`rounded-2xl border p-3 text-left transition ${selected ? "border-civic-cyan/30 bg-civic-cyan/10" : "border-white/10 bg-white/[0.045]"}`}
                    >
                      <Icon className="size-5 text-civic-cyan" />
                      <p className="mt-2 text-xs font-semibold text-white">{issue.label}</p>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="grid gap-5">
            {reportFlow.step === "capture" || reportFlow.step === "preview" ? (
              <div className="grid min-h-[28rem] place-items-center rounded-[2rem] border border-dashed border-civic-cyan/25 bg-civic-cyan/8 p-6 text-center backdrop-blur-2xl">
                <div>
                  <div className="mx-auto grid size-20 place-items-center rounded-full border border-civic-cyan/25 bg-civic-cyan/10 shadow-glow">
                    <Camera className="size-9 text-civic-cyan" />
                  </div>
                  <h2 className="mt-5 text-2xl font-semibold text-white">Capture civic evidence</h2>
                  <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-400">{selectedImage ? selectedImage.name : "Choose a real road image from camera or gallery. CivicEye will send it to the active YOLO backend for analysis."}</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    capture="environment"
                    className="hidden"
                    onChange={(event) => handleImageSelected(event.target.files?.[0] ?? null)}
                  />
                  <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
                    <Button variant="gradient" onClick={runAiReportPipeline}>
                      Run AI scan
                      <ArrowRight className="size-5" />
                    </Button>
                    <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
                      Upload source
                    </Button>
                  </div>
                </div>
              </div>
            ) : null}

            {reportFlow.step === "scanning" ? (
              <div className="grid gap-3">
                <AiScanVisual activeStage={reportFlow.scanStage} />
                <div className="rounded-2xl border border-white/10 bg-white/[0.055] p-4 backdrop-blur-2xl">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                    <span>Progressive upload</span>
                    <span>{reportFlow.uploadProgress}%</span>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
                    <div className="h-full rounded-full bg-gradient-to-r from-civic-blue to-civic-cyan" style={{ width: `${reportFlow.uploadProgress}%` }} />
                  </div>
                  {reportFlow.scanError ? <p className="mt-3 text-sm font-semibold text-civic-danger">{reportFlow.scanError}</p> : null}
                </div>
              </div>
            ) : null}

            {reportFlow.step === "result" ? (
              <div className="rounded-[2rem] border border-white/10 bg-white/[0.055] p-5 backdrop-blur-2xl">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-civic-cyan">AI detection complete</p>
                    <h2 className="mt-2 text-3xl font-semibold text-white">Road damage detected</h2>
                    <p className="mt-2 text-sm leading-6 text-slate-400">High-priority surface fracture with pedestrian and vehicle risk impact.</p>
                  </div>
                  <span className="rounded-full border border-civic-danger/20 bg-civic-danger/10 px-3 py-1 text-xs font-semibold text-civic-danger">High</span>
                </div>
                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  {[
                    ["Confidence", "93%"],
                    ["Department", "Road maintenance"],
                    ["Urgency", "Repair within 24h"],
                    ["Priority", "P1 operational"]
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-2xl border border-white/10 bg-civic-bg/58 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{label}</p>
                      <p className="mt-2 text-sm font-semibold text-white">{value}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-5 flex items-center gap-3 rounded-2xl border border-white/10 bg-civic-bg/58 p-4">
                  <MapPin className="size-5 text-civic-cyan" />
                  <div>
                    <p className="text-sm font-semibold text-white">Geotag ready</p>
                    <p className="text-xs text-slate-400">Ward detected from current device location.</p>
                  </div>
                </div>
                <Button className="mt-5 w-full" size="lg" variant="gradient">
                  {reportFlow.createdIncidentId ? `Submitted ${reportFlow.createdIncidentId}` : "Submit verified report"}
                </Button>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <BottomSheet open={sheetOpen} title="Choose upload source" onClose={() => setSheetOpen(false)}>
        <div className="grid gap-3">
          {["Camera", "Gallery", "Drag and drop", "Live capture"].map((item) => (
            <button key={item} onClick={() => fileInputRef.current?.click()} className="rounded-2xl border border-white/10 bg-white/[0.055] p-4 text-left text-sm font-semibold text-white">
              {item}
            </button>
          ))}
        </div>
      </BottomSheet>
    </section>
  );
}

async function resolveDeviceLocation() {
  if (!navigator.geolocation) {
    throw new Error("Device geolocation is required to create a municipal incident.");
  }
  const position = await new Promise<GeolocationPosition>((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 12000, maximumAge: 30000 });
  });
  return {
    latitude: position.coords.latitude,
    longitude: position.coords.longitude,
    accuracy: position.coords.accuracy
  };
}
