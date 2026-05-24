export type UserRole =
  | "citizen"
  | "municipality_admin"
  | "field_worker"
  | "contractor"
  | "emergency_operator"
  | "supervisor"
  | "platform_admin"
  | "system_admin"
  | "operator"
  | "admin";

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  municipalityId?: string;
};

export type AuthSession = {
  user: AuthUser;
  accessToken: string;
  refreshToken?: string;
  expiresAt: string;
};

export type LoginPayload = {
  email: string;
  password: string;
  municipality_id?: string;
  role?: UserRole;
  device_id?: string;
};
