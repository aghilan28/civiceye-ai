import type { UserRole } from "@/types/auth";

export type EnterpriseRole = UserRole | "field_engineer" | "regional_admin" | "super_admin";

export type Permission =
  | "incident:create"
  | "incident:read"
  | "incident:assign"
  | "incident:resolve"
  | "incident:escalate"
  | "ai:review"
  | "analytics:read"
  | "municipality:admin"
  | "users:manage"
  | "deployment:read";

export const permissionMatrix: Record<EnterpriseRole, Permission[]> = {
  citizen: ["incident:create", "incident:read"],
  municipality_admin: ["incident:create", "incident:read", "incident:assign", "incident:resolve", "incident:escalate", "ai:review", "analytics:read", "municipality:admin", "users:manage"],
  field_worker: ["incident:read", "incident:resolve"],
  emergency_operator: ["incident:read", "incident:assign", "incident:escalate", "analytics:read"],
  supervisor: ["incident:read", "incident:assign", "incident:resolve", "incident:escalate", "analytics:read", "deployment:read"],
  system_admin: ["incident:create", "incident:read", "incident:assign", "incident:resolve", "incident:escalate", "ai:review", "analytics:read", "municipality:admin", "users:manage", "deployment:read"],
  platform_admin: ["incident:create", "incident:read", "incident:assign", "incident:resolve", "incident:escalate", "ai:review", "analytics:read", "municipality:admin", "users:manage", "deployment:read"],
  operator: ["incident:create", "incident:read", "incident:assign", "incident:escalate", "ai:review", "analytics:read"],
  admin: ["incident:create", "incident:read", "incident:assign", "incident:resolve", "incident:escalate", "ai:review", "analytics:read", "municipality:admin", "users:manage"],
  contractor: ["incident:read", "incident:resolve"],
  field_engineer: ["incident:read", "incident:resolve"],
  regional_admin: ["incident:read", "incident:assign", "incident:escalate", "analytics:read", "municipality:admin", "users:manage", "deployment:read"],
  super_admin: ["incident:create", "incident:read", "incident:assign", "incident:resolve", "incident:escalate", "ai:review", "analytics:read", "municipality:admin", "users:manage", "deployment:read"]
};

export function hasPermission(role: EnterpriseRole, permission: Permission) {
  return permissionMatrix[role]?.includes(permission) ?? false;
}

export function assertPermission(role: EnterpriseRole, permission: Permission) {
  if (!hasPermission(role, permission)) {
    throw new Error(`RBAC denied ${permission} for role ${role}`);
  }
}
