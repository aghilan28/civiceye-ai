import type { RealtimeEvent } from "@/types/operations";

export type RealtimeSubscription = {
  unsubscribe: () => void;
};

export type RealtimeClientOptions = {
  pollIntervalMs?: number;
};

export class RealtimeClient {
  private listeners = new Set<(event: RealtimeEvent) => void>();
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private readonly pollIntervalMs: number;

  constructor(options: RealtimeClientOptions = {}) {
    this.pollIntervalMs = options.pollIntervalMs ?? 12000;
  }

  subscribe(listener: (event: RealtimeEvent) => void): RealtimeSubscription {
    this.listeners.add(listener);
    this.startPolling();

    return {
      unsubscribe: () => {
        this.listeners.delete(listener);
        if (this.listeners.size === 0) {
          this.stopPolling();
        }
      }
    };
  }

  publish(event: RealtimeEvent) {
    this.listeners.forEach((listener) => listener(event));
  }

  private startPolling() {
    if (this.intervalId) {
      return;
    }
    this.intervalId = setInterval(() => undefined, this.pollIntervalMs);
  }

  private stopPolling() {
    if (!this.intervalId) {
      return;
    }

    clearInterval(this.intervalId);
    this.intervalId = null;
  }
}

export const realtimeClient = new RealtimeClient();
