import type { AuthenticatedUser, AuthSession } from "@/types";

const TOKEN_KEY = "log_analyzer_access_token";
const USER_KEY = "log_analyzer_user";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function getAuthToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(TOKEN_KEY);
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
}

export function clearAuthSession(): void {
  if (!isBrowser()) return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function hasAuthSession(): boolean {
  return Boolean(getAuthToken());
}

export function getAuthSession(): AuthSession | null {
  const token = getAuthToken();
  const user = getAuthUser();
  if (!token || !user) return null;
  return { token, user };
}
