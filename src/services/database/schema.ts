import type { AuthUser } from "@/types/auth";
import type { CivicIncident, CivicNotification, MunicipalityDepartment } from "@/types/operations";

export type CivicEyeCollectionMap = {
  users: AuthUser;
  incidents: CivicIncident;
  municipalities: {
    id: string;
    name: string;
    region: string;
    timezone: string;
    createdAt: string;
  };
  departments: MunicipalityDepartment;
  notifications: CivicNotification;
  aiDetections: CivicIncident["ai"];
  infrastructureAssets: {
    id: string;
    municipalityId: string;
    type: "road" | "drain" | "streetlight" | "waterline" | "waste_zone";
    geoHash: string;
    healthScore: number;
    updatedAt: string;
  };
  responseWorkflows: {
    id: string;
    incidentId: string;
    departmentId: string;
    assignedCrewId?: string;
    status: CivicIncident["lifecycleStatus"];
    createdAt: string;
    updatedAt: string;
  };
};

export const civicEyeCollections = {
  users: "users",
  incidents: "incidents",
  municipalities: "municipalities",
  departments: "departments",
  notifications: "notifications",
  aiDetections: "aiDetections",
  infrastructureAssets: "infrastructureAssets",
  responseWorkflows: "responseWorkflows"
} as const satisfies Record<keyof CivicEyeCollectionMap, string>;
