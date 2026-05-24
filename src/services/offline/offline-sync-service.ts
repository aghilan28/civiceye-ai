import { createId, nowIso } from "@/lib/time";
import { offlineQueueRepository } from "@/services/repositories/offline-queue-repository";
import type { OfflineQueueItem } from "@/types/operations";

export const offlineSyncService = {
  async enqueue(type: OfflineQueueItem["type"], payload: unknown) {
    return offlineQueueRepository.enqueue({
      id: createId("SYNC"),
      type,
      payload,
      attempts: 0,
      createdAt: nowIso(),
      status: "queued"
    });
  },

  async flush(processor: (item: OfflineQueueItem) => Promise<void>) {
    const queue = await offlineQueueRepository.list();

    for (const item of queue) {
      const syncingItem: OfflineQueueItem = {
        ...item,
        status: "syncing",
        attempts: item.attempts + 1,
        lastAttemptAt: nowIso()
      };
      await offlineQueueRepository.update(syncingItem);

      try {
        await processor(syncingItem);
        await offlineQueueRepository.remove(syncingItem.id);
      } catch {
        await offlineQueueRepository.update({ ...syncingItem, status: "failed" });
      }
    }
  }
};
