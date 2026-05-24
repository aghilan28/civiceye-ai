import { browserStorage } from "@/services/storage/browser-storage";
import type { OfflineQueueItem } from "@/types/operations";

const OFFLINE_QUEUE_KEY = "civiceye.offline.queue.v1";

export type OfflineQueueRepository = {
  list: () => Promise<OfflineQueueItem[]>;
  enqueue: (item: OfflineQueueItem) => Promise<OfflineQueueItem>;
  update: (item: OfflineQueueItem) => Promise<OfflineQueueItem>;
  remove: (id: string) => Promise<void>;
};

function readQueue() {
  const raw = browserStorage.getItem(OFFLINE_QUEUE_KEY);
  if (!raw) {
    return [];
  }

  try {
    return JSON.parse(raw) as OfflineQueueItem[];
  } catch {
    return [];
  }
}

function writeQueue(queue: OfflineQueueItem[]) {
  browserStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
}

export const offlineQueueRepository: OfflineQueueRepository = {
  async list() {
    return readQueue();
  },

  async enqueue(item) {
    const queue = readQueue();
    writeQueue([item, ...queue]);
    return item;
  },

  async update(item) {
    const queue = readQueue().map((entry) => (entry.id === item.id ? item : entry));
    writeQueue(queue);
    return item;
  },

  async remove(id) {
    writeQueue(readQueue().filter((item) => item.id !== id));
  }
};
