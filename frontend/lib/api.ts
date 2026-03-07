import { getAuthToken } from "@/lib/auth";
import type {
  ApiErrorPayload,
  AuthenticatedUser,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  UploadResponse
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export class ApiRequestError extends Error {
  status: number;
  payload: ApiErrorPayload | null;

  constructor(message: string, status: number, payload: ApiErrorPayload | null = null) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.payload = payload;
  }
}

type ApiRequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string | null;
  headers?: HeadersInit;
};

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

async function parseJsonSafely(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function apiRequest<T>(
  path: string,
  { method = "GET", body, token, headers }: ApiRequestOptions = {}
): Promise<T> {
  const resolvedToken = token === undefined ? getAuthToken() : token;
  const finalHeaders = new Headers(headers || {});

  if (!(body instanceof FormData)) {
    finalHeaders.set("Content-Type", "application/json");
  }

  if (resolvedToken) {
    finalHeaders.set("Authorization", `Bearer ${resolvedToken}`);
  }

  const response = await fetch(buildApiUrl(path), {
    method,
    headers: finalHeaders,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined
  });

  const payload = (await parseJsonSafely(response)) as ApiErrorPayload | null;
  if (!response.ok) {
    const message =
      (payload && typeof payload.error === "string" && payload.error) ||
      `Request failed with status ${response.status}`;
    throw new ApiRequestError(message, response.status, payload);
  }

  return payload as T;
}

export function loginUser(payload: LoginRequest): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: payload,
    token: null
  });
}

export function registerUser(payload: RegisterRequest): Promise<RegisterResponse> {
  return apiRequest<RegisterResponse>("/api/auth/register", {
    method: "POST",
    body: payload,
    token: null
  });
}

export function fetchCurrentUser(token?: string): Promise<AuthenticatedUser> {
  return apiRequest<AuthenticatedUser>("/api/auth/me", { method: "GET", token });
}

export function uploadLogFile(file: File, source = "zscaler"): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("source", source);

  return apiRequest<UploadResponse>("/uploads", {
    method: "POST",
    body: formData
  });
}
