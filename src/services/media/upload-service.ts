import { createId } from "@/lib/time";
import type { ReportImage } from "@/types/operations";

export type UploadProvider = "firebase_storage" | "cloudinary" | "s3";

export type UploadProgress = {
  progress: number;
  phase: "compressing" | "uploading" | "finalizing" | "complete";
};

export type UploadMediaInput = {
  file: File;
  incidentId?: string;
  provider?: UploadProvider;
  onProgress?: (progress: UploadProgress) => void;
};

async function compressImage(file: File, onProgress?: UploadMediaInput["onProgress"]) {
  onProgress?.({ progress: 12, phase: "compressing" });
  await new Promise((resolve) => setTimeout(resolve, 180));
  onProgress?.({ progress: 28, phase: "compressing" });
  return file;
}

export const uploadService = {
  async uploadIncidentImage(input: UploadMediaInput): Promise<ReportImage> {
    const provider = input.provider ?? "firebase_storage";
    const compressed = await compressImage(input.file, input.onProgress);
    input.onProgress?.({ progress: 52, phase: "uploading" });
    await new Promise((resolve) => setTimeout(resolve, 260));
    input.onProgress?.({ progress: 84, phase: "finalizing" });
    await new Promise((resolve) => setTimeout(resolve, 160));
    input.onProgress?.({ progress: 100, phase: "complete" });

    const imageId = createId("IMG");
    const incidentPath = input.incidentId ?? "pending";

    return {
      id: imageId,
      url: URL.createObjectURL(compressed),
      storagePath: `${provider}/incidents/${incidentPath}/${imageId}-${compressed.name}`,
      contentType: compressed.type || "image/jpeg",
      sizeBytes: compressed.size
    };
  }
};
