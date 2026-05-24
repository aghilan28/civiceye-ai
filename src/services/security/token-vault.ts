import { browserStorage } from "@/services/storage/browser-storage";

const ACCESS_TOKEN_KEY = "civiceye.secure.access";
const REFRESH_TOKEN_KEY = "civiceye.secure.refresh";

export const tokenVault = {
  getAccessToken() {
    return browserStorage.getItem(ACCESS_TOKEN_KEY);
  },

  setAccessToken(token: string) {
    browserStorage.setItem(ACCESS_TOKEN_KEY, token);
  },

  getRefreshToken() {
    return browserStorage.getItem(REFRESH_TOKEN_KEY);
  },

  rotateRefreshToken(token: string) {
    browserStorage.setItem(REFRESH_TOKEN_KEY, token);
  },

  clear() {
    browserStorage.removeItem(ACCESS_TOKEN_KEY);
    browserStorage.removeItem(REFRESH_TOKEN_KEY);
  }
};
