import { apiClient } from "@/services/api/client";
import type { DetectionResult, GeoPoint } from "@/types/civic";

export type DetectionRequest = {
  image: File;
  location?: GeoPoint;
  provider?: "yolov8" | "tensorflow" | "opencv";
};

export const detectionService = {
  analyzeImage(payload: DetectionRequest) {
    const formData = new FormData();
    formData.append("image", payload.image);

    if (payload.location) {
      formData.append("location", JSON.stringify(payload.location));
    }

    if (payload.provider) {
      formData.append("provider", payload.provider);
    }

    return apiClient.post<DetectionResult[], FormData>("/ai/detect", formData);
  }
};
