export const env = {
  appUrl: process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  mapboxToken: process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "",
  realtimeUrl: process.env.NEXT_PUBLIC_REALTIME_URL ?? "",
  aiInferenceUrl: process.env.NEXT_PUBLIC_AI_INFERENCE_URL ?? "",
  firebase: {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY ?? "",
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? "",
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID ?? ""
  },
  jwtStorageKey: process.env.JWT_STORAGE_KEY ?? "civiceye.auth.token",
  aiDetectionProvider: process.env.AI_DETECTION_PROVIDER ?? "yolov8"
} as const;
