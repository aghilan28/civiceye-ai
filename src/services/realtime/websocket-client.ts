import { env } from "@/config/env";
import { createId, nowIso } from "@/lib/time";
import { civicEventBus } from "@/services/realtime/event-bus";
import { tokenVault } from "@/services/security/token-vault";
import type { CivicRealtimeEvent, RealtimeChannel, RealtimeConnectionStatus } from "@/types/realtime";

type WebSocketClientOptions = {
  municipalityId: string;
  channels: RealtimeChannel[];
  url?: string;
  heartbeatMs?: number;
  maxReconnectDelayMs?: number;
};

export class CivicWebSocketClient {
  private socket: WebSocket | null = null;
  private reconnectAttempt = 0;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private fallbackTimer: ReturnType<typeof setInterval> | null = null;
  private queuedEvents: CivicRealtimeEvent[] = [];
  private statusListeners = new Set<(status: RealtimeConnectionStatus) => void>();
  private status: RealtimeConnectionStatus = "idle";
  private readonly options: Required<WebSocketClientOptions>;

  constructor(options: WebSocketClientOptions) {
    this.options = {
      url: options.url ?? env.realtimeUrl,
      municipalityId: options.municipalityId,
      channels: options.channels,
      heartbeatMs: options.heartbeatMs ?? 15000,
      maxReconnectDelayMs: options.maxReconnectDelayMs ?? 30000
    };
  }

  connect() {
    if (!this.options.url) {
      this.startDegradedMode();
      return;
    }

    this.setStatus(this.reconnectAttempt > 0 ? "reconnecting" : "connecting");

    try {
      this.socket = new WebSocket(this.socketUrl());
      this.socket.onopen = () => this.handleOpen();
      this.socket.onmessage = (message) => this.handleMessage(message);
      this.socket.onclose = () => this.scheduleReconnect();
      this.socket.onerror = () => this.scheduleReconnect();
    } catch {
      this.startDegradedMode();
    }
  }

  disconnect() {
    this.stopHeartbeat();
    this.stopDegradedMode();
    this.socket?.close();
    this.socket = null;
    this.setStatus("idle");
  }

  subscribeStatus(listener: (status: RealtimeConnectionStatus) => void) {
    this.statusListeners.add(listener);
    listener(this.status);

    return {
      unsubscribe: () => this.statusListeners.delete(listener)
    };
  }

  send(event: CivicRealtimeEvent) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(event));
      return;
    }

    this.queuedEvents.push(event);
  }

  private handleOpen() {
    this.reconnectAttempt = 0;
    this.setStatus("connected");
    this.socket?.send(
      JSON.stringify({
        type: "SUBSCRIBE",
        municipalityId: this.options.municipalityId,
        channels: this.options.channels
      })
    );
    this.flushQueue();
    this.startHeartbeat();
  }

  private socketUrl() {
    const url = new URL(this.options.url);
    url.searchParams.set("municipality_id", this.options.municipalityId);
    url.searchParams.set("channels", this.options.channels.join(","));
    const token = tokenVault.getAccessToken();
    if (token) {
      url.searchParams.set("token", token);
    }
    return url.toString();
  }

  private handleMessage(message: MessageEvent) {
    try {
      const parsed = JSON.parse(String(message.data)) as CivicRealtimeEvent | CivicRealtimeEvent[] | { type?: string; [key: string]: unknown };
      if (Array.isArray(parsed)) {
        civicEventBus.publishBatch(parsed);
      } else if (isCivicRealtimeEvent(parsed)) {
        civicEventBus.publish(parsed);
      } else if (parsed.type && parsed.type !== "pong" && parsed.type !== "connected") {
        civicEventBus.publish({
          id: createId("EVT"),
          type: "SYSTEM_ALERT",
          channel: "system.alerts",
          timestamp: nowIso(),
          municipalityId: this.options.municipalityId,
          payload: {
            title: `Operations event: ${String(parsed.type).replaceAll("_", " ")}`,
            body: "A persisted operations websocket event was received. Domain dashboards refresh from the authoritative API state.",
            urgency: parsed.type === "emergency_alert" ? "critical" : "info"
          }
        });
      }
    } catch {
      civicEventBus.publish({
        id: createId("EVT"),
        type: "SYSTEM_ALERT",
        channel: "system.alerts",
        timestamp: nowIso(),
        municipalityId: this.options.municipalityId,
        payload: {
          title: "Realtime payload ignored",
          body: "CivicEye received a malformed realtime event and preserved the live session.",
          urgency: "warning"
        }
      });
    }
  }

  private scheduleReconnect() {
    this.stopHeartbeat();
    this.socket = null;
    this.reconnectAttempt += 1;
    this.setStatus("reconnecting");
    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, this.options.maxReconnectDelayMs);
    setTimeout(() => this.connect(), delay);
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: "ping", timestamp: nowIso() }));
      }
    }, this.options.heartbeatMs);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private startDegradedMode() {
    this.setStatus("degraded");
    this.stopDegradedMode();
    this.fallbackTimer = setInterval(() => {
      civicEventBus.publish({
        id: createId("EVT"),
        type: "SYSTEM_ALERT",
        channel: "system.alerts",
        timestamp: nowIso(),
        municipalityId: this.options.municipalityId,
        payload: {
          title: "Realtime channel degraded",
          body: "CivicEye is not receiving websocket telemetry. Dashboards are using persisted API state until the channel reconnects.",
          urgency: "warning"
        }
      });
    }, 30000);
  }

  private stopDegradedMode() {
    if (this.fallbackTimer) {
      clearInterval(this.fallbackTimer);
      this.fallbackTimer = null;
    }
  }

  private flushQueue() {
    const events = this.queuedEvents.splice(0, this.queuedEvents.length);
    events.forEach((event) => this.send(event));
  }

  private setStatus(status: RealtimeConnectionStatus) {
    this.status = status;
    this.statusListeners.forEach((listener) => listener(status));
  }
}

function isCivicRealtimeEvent(value: CivicRealtimeEvent | { type?: string; [key: string]: unknown }): value is CivicRealtimeEvent {
  return typeof value === "object" && value !== null && "id" in value && "channel" in value && "timestamp" in value && "municipalityId" in value && "payload" in value;
}
