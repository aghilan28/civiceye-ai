import { apiClient } from "@/services/api/client";
import type { CivicReport, CreateReportPayload } from "@/types/civic";

export const reportService = {
  listReports() {
    return apiClient.get<CivicReport[]>("/reports");
  },

  getReport(id: string) {
    return apiClient.get<CivicReport>(`/reports/${id}`);
  },

  createReport(payload: CreateReportPayload) {
    const formData = new FormData();
    formData.append("image", payload.image);
    formData.append("location", JSON.stringify(payload.location));

    if (payload.description) {
      formData.append("description", payload.description);
    }

    if (payload.issueType) {
      formData.append("issueType", payload.issueType);
    }

    return apiClient.post<CivicReport, FormData>("/reports", formData);
  }
};
