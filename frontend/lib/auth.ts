import type { AuthenticatedUser, AuthSession } from "@/types";

const TOKEN_KEY = "log_analyzer_access_token";
const USER_KEY = "log_analyzer_user";
export const AUTH_TOKEN_COOKIE = "log_analyzer_access_token";
const AUTH_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function readCookieValue(name: string): string | null {
  if (!isBrowser()) return null;
  const prefix = `${name}=`;
  const match = document.cookie.split("; ").find((chunk) => chunk.startsWith(prefix));
  if (!match) return null;
  return decodeURIComponent(match.slice(prefix.length));
}

export function getAuthToken(): string | null {
  if (!isBrowser()) return null;
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    const cookieToken = readCookieValue(AUTH_TOKEN_COOKIE);
    if (!cookieToken) return null;
    localStorage.setItem(TOKEN_KEY, cookieToken);
    return cookieToken;
  }

  const cookiePrefix = `${AUTH_TOKEN_COOKIE}=`;
  const hasCookie = document.cookie.split("; ").some((chunk) => chunk.startsWith(cookiePrefix));
  if (!hasCookie) {
    document.cookie = `${AUTH_TOKEN_COOKIE}=${encodeURIComponent(token)}; Path=/; Max-Age=${AUTH_COOKIE_MAX_AGE_SECONDS}; SameSite=Lax`;
  }

  return token;
}

export function getAuthUser(): AuthenticatedUser | null {
  if (!isBrowser()) return null;

  const stored = localStorage.getItem(USER_KEY);
  if (!stored) return null;

  try {
    return JSON.parse(stored) as AuthenticatedUser;
  } catch {
    return null;
  }
}

export function setAuthSession(token: string, user: AuthenticatedUser): void {
  if (!isBrowser()) return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  document.cookie = `${AUTH_TOKEN_COOKIE}=${encodeURIComponent(token)}; Path=/; Max-Age=${AUTH_COOKIE_MAX_AGE_SECONDS}; SameSite=Lax`;
}

export function clearAuthSession(): void {
  if (!isBrowser()) return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  document.cookie = `${AUTH_TOKEN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function getAuthSession(): AuthSession | null {
  const token = getAuthToken();
  const user = getAuthUser();
  if (!token || !user) return null;
  return { token, user };
}
