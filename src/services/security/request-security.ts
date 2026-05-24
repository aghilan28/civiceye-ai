export type UploadValidationResult = {
  ok: boolean;
  reason?: string;
};

const allowedImageTypes = new Set(["image/jpeg", "image/png", "image/webp"]);
const maxUploadBytes = 8 * 1024 * 1024;

export function sanitizeText(input: string) {
  return input.replace(/[<>]/g, "").trim().slice(0, 2000);
}

export function validateUpload(file: File): UploadValidationResult {
  if (!allowedImageTypes.has(file.type)) {
    return { ok: false, reason: "Unsupported file type" };
  }

  if (file.size > maxUploadBytes) {
    return { ok: false, reason: "Image exceeds 8MB upload policy" };
  }

  return { ok: true };
}

export function buildTenantHeaders(municipalityId: string, role: string) {
  return {
    "X-CivicEye-Municipality": municipalityId,
    "X-CivicEye-Role": role
  };
}
