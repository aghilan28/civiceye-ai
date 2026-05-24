import type { ModelInferenceResult } from "@/types/mlops";

const cache = new Map<string, { result: ModelInferenceResult; expiresAt: number }>();
const ttlMs = 1000 * 60 * 15;

export function buildInferenceCacheKey(file: File, modelId: string) {
  return `${modelId}:${file.name}:${file.size}:${file.lastModified}`;
}

export const inferenceCache = {
  get(key: string) {
    const entry = cache.get(key);
    if (!entry || entry.expiresAt < Date.now()) {
      cache.delete(key);
      return null;
    }

    return entry.result;
  },

  set(key: string, result: ModelInferenceResult) {
    cache.set(key, { result, expiresAt: Date.now() + ttlMs });
  }
};
