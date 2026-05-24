import { addHoursIso } from "@/lib/time";
import { departmentForIssue } from "@/lib/severity";
import type { CivicSeverity } from "@/types/civic";
import type { CivicIncident, DepartmentType, MunicipalityDepartment } from "@/types/operations";

export const defaultDepartments: MunicipalityDepartment[] = [
  {
    id: "DEP-ROADS",
    municipalityId: "MUNI-BLR",
    type: "roads",
    name: "Road maintenance",
    activeCrewCount: 18,
    openIncidentCount: 42,
    serviceZones: ["Bengaluru Zone 07", "Bengaluru Zone 08"],
    slaHoursBySeverity: { low: 168, medium: 72, high: 24, critical: 4 }
  },
  {
    id: "DEP-SANITATION",
    municipalityId: "MUNI-BLR",
    type: "sanitation",
    name: "Solid waste",
    activeCrewCount: 14,
    openIncidentCount: 28,
    serviceZones: ["Bengaluru Zone 07"],
    slaHoursBySeverity: { low: 120, medium: 48, high: 18, critical: 6 }
  },
  {
    id: "DEP-STORMWATER",
    municipalityId: "MUNI-BLR",
    type: "stormwater",
    name: "Stormwater response",
    activeCrewCount: 9,
    openIncidentCount: 16,
    serviceZones: ["Bengaluru Zone 07"],
    slaHoursBySeverity: { low: 72, medium: 24, high: 8, critical: 3 }
  }
];

export function assignDepartment(issueType: CivicIncident["issueType"], departments = defaultDepartments): MunicipalityDepartment {
  const departmentType = departmentForIssue(issueType);
  return departments.find((department) => department.type === departmentType) ?? departments[0];
}

export function calculateSlaDueAt(createdAt: string, severity: CivicSeverity, department: MunicipalityDepartment) {
  return addHoursIso(createdAt, department.slaHoursBySeverity[severity]);
}

export function calculateWorkloadScore(department: MunicipalityDepartment) {
  return department.openIncidentCount / Math.max(department.activeCrewCount, 1);
}

export function rankDepartmentWorkload(departments = defaultDepartments) {
  return departments
    .map((department) => ({
      department: department.type as DepartmentType,
      open: department.openIncidentCount,
      capacity: department.activeCrewCount,
      workloadScore: calculateWorkloadScore(department)
    }))
    .sort((a, b) => b.workloadScore - a.workloadScore);
}
