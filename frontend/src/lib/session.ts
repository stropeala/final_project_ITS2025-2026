import type { User } from "./types.ts";

// ---------------------------------------------------------------------------
// Session state. The JWT lives in localStorage so a page reload keeps you
// logged in; the resolved User is cached in memory for the current page life.
// ---------------------------------------------------------------------------

const TOKEN_KEY = "its.token";

let cachedUser: User | null = null;

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  cachedUser = null;
}

export function getCachedUser(): User | null {
  return cachedUser;
}

export function setCachedUser(user: User | null): void {
  cachedUser = user;
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}
