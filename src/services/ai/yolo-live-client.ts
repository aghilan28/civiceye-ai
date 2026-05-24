import { aiBackendClient } from "@/services/ai/backend-client";
import type { LiveInferenceEvent } from "@/services/ai/types";

export type LiveClientHandlers = {
  onInference: (event: LiveInferenceEvent) => void;
  onStatus?: (status: "connecting" | "open" | "closed" | "error") => void;
  onError?: (message: string) => void;
};

export class YoloLiveClient {
  private socket: WebSocket | null = null;
  private timer: number | null = null;
  private sending = false;

  constructor(
    private readonly video: HTMLVideoElement,
    private readonly canvas: HTMLCanvasElement,
    private readonly handlers: LiveClientHandlers,
    private readonly sourceId = "webcam"
  ) {}

  connect() {
    this.handlers.onStatus?.("connecting");
    this.socket = new WebSocket(aiBackendClient.liveWebSocketUrl(this.sourceId));
    this.socket.onopen = () => {
      this.handlers.onStatus?.("open");
      this.startLoop();
    };
    this.socket.onclose = () => {
      this.handlers.onStatus?.("closed");
      this.stopLoop();
    };
    this.socket.onerror = () => {
      this.handlers.onStatus?.("error");
      this.handlers.onError?.("Live inference WebSocket failed");
    };
    this.socket.onmessage = (message) => {
      const payload = JSON.parse(message.data as string) as LiveInferenceEvent | { type: string; error?: string };
      if (payload.type === "inference" && "detections" in payload) {
        this.handlers.onInference(payload);
      } else if (payload.type === "error") {
        this.handlers.onError?.(payload.error ?? "Backend live inference error");
      }
      this.sending = false;
    };
  }

  close() {
    this.stopLoop();
    this.socket?.close();
    this.socket = null;
  }

  private startLoop() {
    const send = () => {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN || this.sending) {
        this.timer = window.setTimeout(send, 16);
        return;
      }
      const width = this.video.videoWidth;
      const height = this.video.videoHeight;
      if (width > 0 && height > 0) {
        this.canvas.width = 640;
        this.canvas.height = Math.round((height / width) * 640);
        const context = this.canvas.getContext("2d", { alpha: false });
        if (context) {
          context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
          this.sending = true;
          this.socket.send(JSON.stringify({ type: "frame", frame: this.canvas.toDataURL("image/jpeg", 0.72) }));
        }
      }
      this.timer = window.setTimeout(send, 33);
    };
    send();
  }

  private stopLoop() {
    if (this.timer !== null) {
      window.clearTimeout(this.timer);
      this.timer = null;
    }
  }
}
