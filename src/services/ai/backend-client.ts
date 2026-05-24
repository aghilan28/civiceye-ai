import type {
  BackendHealth,
  BackendMetrics,
  ImagePredictionResponse,
  VideoJobResponse,
  VideoJobStatus,
  VideoResults
} from "@/services/ai/types";
import { demoImagePrediction, demoVideoStatus } from "@/data/showcase";

const API_BASE = process.env.NEXT_PUBLIC_AI_BACKEND_URL ?? "http://localhost:8000";

function absoluteBackendUrl(path: string) {
  if (path.startsWith("http")) {
    return path;
  }
  return `${API_BASE}${path}`;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `CivicEye AI backend failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export const aiBackendClient = {
  baseUrl: API_BASE,

  fileUrl(path: string | null | undefined) {
    return path ? absoluteBackendUrl(path) : null;
  },

  async health(signal?: AbortSignal): Promise<BackendHealth> {
    try {
      return await parseJson<BackendHealth>(await fetch(`${API_BASE}/health`, { signal, cache: "no-store" }));
    } catch {
      return {
        status: "demo",
        model_loaded: true,
        model_version: demoImagePrediction.telemetry.model_version,
        weights_path: "seeded-demo",
        device: demoImagePrediction.telemetry.device,
        cuda_available: demoImagePrediction.telemetry.cuda_available
      };
    }
  },

  async metrics(signal?: AbortSignal): Promise<BackendMetrics> {
    try {
      return await parseJson<BackendMetrics>(await fetch(`${API_BASE}/runtime/metrics`, { signal, cache: "no-store" }));
    } catch {
      return {
        inference: {
          latency_avg_ms: demoImagePrediction.telemetry.latency_ms,
          latency_p95_ms: 91,
          fps: demoImagePrediction.telemetry.fps ?? 18.4
        },
        model: {
          model_version: demoImagePrediction.telemetry.model_version,
          gpu_name: demoImagePrediction.telemetry.gpu_name ?? "RTX A4000 demo worker",
          vram_used_mb: demoImagePrediction.telemetry.vram_used_mb ?? 2140,
          vram_total_mb: demoImagePrediction.telemetry.vram_total_mb ?? 16384
        }
      };
    }
  },

  async predictImage(image: File, signal?: AbortSignal): Promise<ImagePredictionResponse> {
    if (typeof window !== "undefined" && !image) {
      return demoImagePrediction;
    }
    const body = new FormData();
    body.append("image", image);
    body.append("source_id", "operator-upload");
    try {
      return await parseJson<ImagePredictionResponse>(await fetch(`${API_BASE}/predict/image`, { method: "POST", body, signal }));
    } catch {
      return demoImagePrediction;
    }
  },

  async predictVideo(video: File, signal?: AbortSignal): Promise<VideoJobResponse> {
    const body = new FormData();
    body.append("video", video);
    body.append("source_id", "operator-video-upload");
    try {
      return await parseJson<VideoJobResponse>(await fetch(`${API_BASE}/predict/video`, { method: "POST", body, signal }));
    } catch {
      return {
        job_id: demoVideoStatus.job_id,
        state: demoVideoStatus.state,
        source_id: "operator-video-upload",
        status_url: "/demo/video/status",
        results_url: "/demo/video/results"
      };
    }
  },

  async videoStatus(jobId: string, signal?: AbortSignal): Promise<VideoJobStatus> {
    try {
      return await parseJson<VideoJobStatus>(await fetch(`${API_BASE}/predict/status/${jobId}`, { signal, cache: "no-store" }));
    } catch {
      return demoVideoStatus;
    }
  },

  async videoResults(jobId: string, signal?: AbortSignal): Promise<VideoResults> {
    try {
      return await parseJson<VideoResults>(await fetch(`${API_BASE}/predict/results/${jobId}`, { signal, cache: "no-store" }));
    } catch {
      return {
        job_id: jobId,
        state: "completed",
        processed_video_url: null,
        detection_log_url: null,
        analytics: {
          pothole_count: demoImagePrediction.pothole_count,
          processed_frames: 1200,
          duration_seconds: 54,
          severity_distribution: demoImagePrediction.severity_summary,
          confidence_mean: demoImagePrediction.confidence_mean,
          detections_per_minute: 18
        },
        detections: demoImagePrediction.detections
      };
    }
  },

  liveWebSocketUrl(sourceId = "webcam") {
    const url = new URL(API_BASE);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = "/predict/live";
    url.searchParams.set("source_id", sourceId);
    return url.toString();
  }
};
