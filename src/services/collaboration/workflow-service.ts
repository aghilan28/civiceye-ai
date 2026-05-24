import { createId, nowIso } from "@/lib/time";
import type { DepartmentType, IncidentLifecycleStatus } from "@/types/operations";

export type WorkflowComment = {
  id: string;
  incidentId: string;
  authorId: string;
  authorName: string;
  body: string;
  createdAt: string;
};

export type DepartmentTransfer = {
  id: string;
  incidentId: string;
  fromDepartment: DepartmentType;
  toDepartment: DepartmentType;
  reason: string;
  createdAt: string;
};

export type ApprovalRequest = {
  id: string;
  incidentId: string;
  requestedStatus: IncidentLifecycleStatus;
  requestedBy: string;
  approverRole: "municipality_admin" | "department_lead" | "emergency_coordinator";
  state: "pending" | "approved" | "rejected";
  createdAt: string;
};

export const workflowService = {
  createComment(incidentId: string, body: string): WorkflowComment {
    return {
      id: createId("COM"),
      incidentId,
      authorId: "USR-DEMO",
      authorName: "CivicEye Operator",
      body,
      createdAt: nowIso()
    };
  },

  requestTransfer(incidentId: string, fromDepartment: DepartmentType, toDepartment: DepartmentType, reason: string): DepartmentTransfer {
    return {
      id: createId("TRN"),
      incidentId,
      fromDepartment,
      toDepartment,
      reason,
      createdAt: nowIso()
    };
  },

  requestApproval(incidentId: string, requestedStatus: IncidentLifecycleStatus): ApprovalRequest {
    return {
      id: createId("APR"),
      incidentId,
      requestedStatus,
      requestedBy: "USR-DEMO",
      approverRole: requestedStatus === "resolved" ? "department_lead" : "municipality_admin",
      state: "pending",
      createdAt: nowIso()
    };
  }
};
