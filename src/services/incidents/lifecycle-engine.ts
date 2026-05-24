import { createId, nowIso } from "@/lib/time";
import type { IncidentLifecycleStatus, CivicIncident, IncidentAuditEvent } from "@/types/operations";

const allowedTransitions: Record<IncidentLifecycleStatus, IncidentLifecycleStatus[]> = {
  detected: ["submitted", "archived"],
  submitted: ["ai_verified", "municipality_reviewed", "archived"],
  ai_verified: ["municipality_reviewed", "assigned", "escalated", "archived"],
  municipality_reviewed: ["assigned", "escalated", "archived"],
  assigned: ["in_progress", "escalated", "resolved"],
  in_progress: ["escalated", "resolved"],
  escalated: ["assigned", "in_progress", "resolved"],
  resolved: ["archived"],
  archived: []
};

export type TransitionIncidentInput = {
  incident: CivicIncident;
  toStatus: IncidentLifecycleStatus;
  actorId: string;
  actorRole: IncidentAuditEvent["actorRole"];
  message: string;
};

export function canTransitionIncident(from: IncidentLifecycleStatus, to: IncidentLifecycleStatus) {
  return allowedTransitions[from].includes(to);
}

export function transitionIncident(input: TransitionIncidentInput): CivicIncident {
  const { incident, toStatus, actorId, actorRole, message } = input;

  if (!canTransitionIncident(incident.lifecycleStatus, toStatus)) {
    throw new Error(`Invalid incident transition from ${incident.lifecycleStatus} to ${toStatus}`);
  }

  const timestamp = nowIso();
  const auditEvent: IncidentAuditEvent = {
    id: createId("AUD"),
    actorId,
    actorRole,
    fromStatus: incident.lifecycleStatus,
    toStatus,
    message,
    createdAt: timestamp
  };

  return {
    ...incident,
    lifecycleStatus: toStatus,
    auditTrail: [auditEvent, ...incident.auditTrail],
    repairTimeline: {
      ...incident.repairTimeline,
      assignedAt: toStatus === "assigned" ? timestamp : incident.repairTimeline.assignedAt,
      startedAt: toStatus === "in_progress" ? timestamp : incident.repairTimeline.startedAt,
      escalatedAt: toStatus === "escalated" ? timestamp : incident.repairTimeline.escalatedAt,
      resolvedAt: toStatus === "resolved" ? timestamp : incident.repairTimeline.resolvedAt
    },
    updatedAt: timestamp
  };
}

export function buildIncidentTimeline(incident: CivicIncident) {
  return incident.auditTrail
    .slice()
    .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
    .map((event) => ({
      id: event.id,
      label: event.toStatus.replaceAll("_", " "),
      message: event.message,
      createdAt: event.createdAt,
      actorRole: event.actorRole
    }));
}
