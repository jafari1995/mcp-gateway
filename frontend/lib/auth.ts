const TOKEN_KEY = "mcpgw_session";
const USER_KEY = "mcpgw_user";

export type SessionUser = {
  id: number;
  name: string;
  username: string;
  email: string;
  role: "admin" | "user" | string;
  is_active: boolean;
};

export function getSessionToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getSessionUser(): SessionUser | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as SessionUser;
  } catch {
    return null;
  }
}

export function setSession(sessionToken: string, user: SessionUser): void {
  sessionStorage.setItem(TOKEN_KEY, sessionToken);
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getSessionToken());
}

export function isAdmin(): boolean {
  return getSessionUser()?.role === "admin";
}
