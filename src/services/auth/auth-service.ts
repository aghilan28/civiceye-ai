import { apiClient } from "@/services/api/client";
import { tokenVault } from "@/services/security/token-vault";
import type { AuthSession, LoginPayload } from "@/types/auth";

export const authService = {
  async login(payload: LoginPayload) {
    const session = await apiClient.post<AuthSession, LoginPayload>("/auth/login", payload);
    tokenVault.setAccessToken(session.accessToken);
    if (session.refreshToken) {
      tokenVault.rotateRefreshToken(session.refreshToken);
    }
    return session;
  },

  async refresh(refreshToken: string) {
    const session = await apiClient.post<AuthSession, { refreshToken: string }>("/auth/refresh", { refreshToken });
    tokenVault.setAccessToken(session.accessToken);
    if (session.refreshToken) {
      tokenVault.rotateRefreshToken(session.refreshToken);
    }
    return session;
  },

  async logout() {
    try {
      return await apiClient.post<{ ok: boolean }>("/auth/logout");
    } finally {
      tokenVault.clear();
    }
  }
};
