import { env } from "@/config/env";
import { tokenVault } from "@/services/security/token-vault";

export type ApiRequestContext = {
  requestId: string;
  attempt: number;
  startedAt: number;
};

export type ApiClientOptions = {
  baseUrl?: string;
  getAccessToken?: () => string | null;
  refreshAccessToken?: () => Promise<string | null>;
  maxRetries?: number;
  retryDelayMs?: number;
};

export type ApiResult<T> = {
  data: T;
  status: number;
  requestId: string;
};

export type NormalizedApiError = {
  message: string;
  status: number;
  code: string;
  requestId: string;
  payload: unknown;
  retryable: boolean;
};

export class ApiError extends Error {
  status: number;
  code: string;
  requestId: string;
  payload: unknown;
  retryable: boolean;

  constructor(error: NormalizedApiError) {
    super(error.message);
    this.name = "ApiError";
    this.status = error.status;
    this.code = error.code;
    this.requestId = error.requestId;
    this.payload = error.payload;
    this.retryable = error.retryable;
  }
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetryableStatus(status: number) {
  return status === 408 || status === 429 || status >= 500;
}

function createRequestId() {
  return `REQ-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`.toUpperCase();
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly getAccessToken?: () => string | null;
  private readonly refreshAccessToken?: () => Promise<string | null>;
  private readonly maxRetries: number;
  private readonly retryDelayMs: number;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? env.apiBaseUrl;
    this.getAccessToken = options.getAccessToken;
    this.refreshAccessToken = options.refreshAccessToken;
    this.maxRetries = options.maxRetries ?? 2;
    this.retryDelayMs = options.retryDelayMs ?? 450;
  }

  async get<TResponse>(path: string, signal?: AbortSignal): Promise<TResponse> {
    return this.request<TResponse>(path, { method: "GET", signal }).then((result) => result.data);
  }

  async post<TResponse, TBody = unknown>(path: string, body?: TBody, signal?: AbortSignal): Promise<TResponse> {
    return this.request<TResponse>(path, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
      signal
    }).then((result) => result.data);
  }

  async patch<TResponse, TBody = unknown>(path: string, body?: TBody, signal?: AbortSignal): Promise<TResponse> {
    return this.request<TResponse>(path, {
      method: "PATCH",
      body: JSON.stringify(body),
      signal
    }).then((result) => result.data);
  }

  async delete<TResponse>(path: string, signal?: AbortSignal): Promise<TResponse> {
    return this.request<TResponse>(path, { method: "DELETE", signal }).then((result) => result.data);
  }

  async request<TResponse>(path: string, init: RequestInit): Promise<ApiResult<TResponse>> {
    const requestId = createRequestId();
    let accessToken = this.getAccessToken?.() ?? null;

    for (let attempt = 0; attempt <= this.maxRetries; attempt += 1) {
      const context: ApiRequestContext = { requestId, attempt, startedAt: Date.now() };
      try {
        const response = await this.execute<TResponse>(path, init, accessToken, context);
        return response;
      } catch (error) {
        if (error instanceof ApiError && error.status === 401 && this.refreshAccessToken && attempt === 0) {
          accessToken = await this.refreshAccessToken();
          if (accessToken) {
            continue;
          }
        }

        const retryable = error instanceof ApiError ? error.retryable : true;
        if (!retryable || attempt >= this.maxRetries) {
          throw error;
        }

        await delay(this.retryDelayMs * (attempt + 1));
      }
    }

    throw new ApiError({
      message: "Request failed after retries",
      status: 0,
      code: "REQUEST_RETRY_EXHAUSTED",
      requestId,
      payload: null,
      retryable: false
    });
  }

  private async execute<TResponse>(
    path: string,
    init: RequestInit,
    accessToken: string | null,
    context: ApiRequestContext
  ): Promise<ApiResult<TResponse>> {
    const headers = new Headers(init.headers);
    headers.set("X-CivicEye-Request-Id", context.requestId);
    headers.set("X-CivicEye-Api-Version", "2026-05-15");

    if (!(init.body instanceof FormData) && init.body !== undefined) {
      headers.set("Content-Type", "application/json");
    }

    if (accessToken) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }

    let response: Response;

    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        ...init,
        headers,
        cache: "no-store"
      });
    } catch (error) {
      throw new ApiError({
        message: error instanceof Error ? error.message : "Network request failed",
        status: 0,
        code: "NETWORK_ERROR",
        requestId: context.requestId,
        payload: null,
        retryable: true
      });
    }

    const contentType = response.headers.get("content-type");
    const payload = contentType?.includes("application/json") ? await response.json() : await response.text();

    if (!response.ok) {
      throw new ApiError({
        message: typeof payload === "object" && payload && "message" in payload ? String(payload.message) : response.statusText || "API request failed",
        status: response.status,
        code: typeof payload === "object" && payload && "code" in payload ? String(payload.code) : `HTTP_${response.status}`,
        requestId: context.requestId,
        payload,
        retryable: isRetryableStatus(response.status)
      });
    }

    return {
      data: payload as TResponse,
      status: response.status,
      requestId: context.requestId
    };
  }
}

async function rotateAccessToken() {
  const refreshToken = tokenVault.getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(`${env.apiBaseUrl}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CivicEye-Request-Id": createRequestId() },
      body: JSON.stringify({ refreshToken }),
      cache: "no-store"
    });
    if (!response.ok) {
      tokenVault.clear();
      return null;
    }
    const session = (await response.json()) as { accessToken: string; refreshToken?: string };
    tokenVault.setAccessToken(session.accessToken);
    if (session.refreshToken) {
      tokenVault.rotateRefreshToken(session.refreshToken);
    }
    return session.accessToken;
  } catch {
    return null;
  }
}

export const apiClient = new ApiClient({
  getAccessToken: () => tokenVault.getAccessToken(),
  refreshAccessToken: rotateAccessToken
});
