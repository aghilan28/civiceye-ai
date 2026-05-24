"use client";

import { useEffect } from "react";
import { tokenVault } from "@/services/security/token-vault";
import { useAppStore } from "@/store/use-app-store";

function decodeJwtPayload(token: string) {
  try {
    const payload = token.split(".")[1];
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(window.atob(normalized)) as {
      sub?: string;
      role?: string;
      municipality_id?: string;
      exp?: number;
    };
  } catch {
    return null;
  }
}

export function SessionHydrator() {
  const setSession = useAppStore((state) => state.setSession);

  useEffect(() => {
    const token = tokenVault.getAccessToken();
    const refreshToken = tokenVault.getRefreshToken();
    if (!token) {
      return;
    }
    const payload = decodeJwtPayload(token);
    if (!payload?.sub || !payload.exp || payload.exp * 1000 < Date.now()) {
      tokenVault.clear();
      return;
    }
    const email = payload.sub.replace(/^user-/, "");
    setSession({
      accessToken: token,
      refreshToken: refreshToken ?? undefined,
      expiresAt: new Date(payload.exp * 1000).toISOString(),
      user: {
        id: payload.sub,
        name: email.split("@", 1)[0].replaceAll(".", " "),
        email,
        role: (payload.role ?? "citizen") as never,
        municipalityId: payload.municipality_id
      }
    });
  }, [setSession]);

  return null;
}
