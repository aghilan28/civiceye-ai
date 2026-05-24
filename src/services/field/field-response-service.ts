import { defaultDepartments } from "@/services/municipality/operations-engine";
import type { CivicIncident } from "@/types/operations";
import type { FieldTeam } from "@/types/realtime";

export function buildFieldTeams(incidents: CivicIncident[]): FieldTeam[] {
  return defaultDepartments.map((department, index) => {
    const assignedIncident = incidents.find((incident) => incident.assignedDepartment === department.type);

    return {
      id: `TEAM-${department.type.toUpperCase()}`,
      name: `${department.name} ${index + 1}`,
      department: department.type,
      status: assignedIncident ? "en_route" : "available",
      assignedIncidentId: assignedIncident?.id,
      etaMinutes: assignedIncident ? 8 + index * 7 : undefined,
      routeProgress: assignedIncident ? Math.min(92, 34 + index * 21) : 0,
      currentZone: assignedIncident?.municipalityZone ?? "Bengaluru Zone 07"
    };
  });
}

export function calculateFieldCoverage(teams: FieldTeam[]) {
  const active = teams.filter((team) => team.status !== "available").length;
  return Math.round((active / Math.max(teams.length, 1)) * 100);
}
