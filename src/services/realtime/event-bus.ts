import type { CivicRealtimeEvent, RealtimeChannel } from "@/types/realtime";

export type EventHandler<TEvent extends CivicRealtimeEvent = CivicRealtimeEvent> = (event: TEvent) => void;

export type EventSubscription = {
  unsubscribe: () => void;
};

export class CivicEventBus {
  private handlers = new Map<RealtimeChannel | "all", Set<EventHandler>>();
  private buffer: CivicRealtimeEvent[] = [];
  private scheduled = false;

  subscribe(channel: RealtimeChannel | "all", handler: EventHandler): EventSubscription {
    const handlers = this.handlers.get(channel) ?? new Set<EventHandler>();
    handlers.add(handler);
    this.handlers.set(channel, handlers);

    return {
      unsubscribe: () => {
        handlers.delete(handler);
      }
    };
  }

  publish(event: CivicRealtimeEvent) {
    this.buffer.push(event);
    this.scheduleFlush();
  }

  publishBatch(events: CivicRealtimeEvent[]) {
    this.buffer.push(...events);
    this.scheduleFlush();
  }

  private scheduleFlush() {
    if (this.scheduled) {
      return;
    }

    this.scheduled = true;
    queueMicrotask(() => {
      const events = this.buffer.splice(0, this.buffer.length);
      this.scheduled = false;
      events.forEach((event) => this.deliver(event));
    });
  }

  private deliver(event: CivicRealtimeEvent) {
    this.handlers.get("all")?.forEach((handler) => handler(event));
    if (event.channel) {
      this.handlers.get(event.channel)?.forEach((handler) => handler(event));
    }
  }
}

export const civicEventBus = new CivicEventBus();
