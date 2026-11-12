import { getSessionToken, type SessionUser } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_BASE || "/gw";

export type Overview = {
  users: number;
  tokens_active: number;
  servers: number;
  tools: number;
  needs_setup: boolean;
  me?: SessionUser | null;
};

export type User = SessionUser & { created_at?: string };

export type Token = {
  id: number;
  user_id: number;
  label: string;
  token_prefix: string;
  created_at: string;
  revoked_at: string | null;
  raw_token?: string | null;
};

export type Server = {
  id: number;
  name: string;
  base_url: string;
  transport: string;
  status: string;
  last_error: string | null;
  is_public?: boolean;
  created_at: string;
  tool_count: number;
};

export type Tool = {
  id: number;
  server_id: number;
  server_name?: string | null;
  name: string;
  description: string | null;
  enabled_globally: boolean;
  granted?: boolean | null;
};

export type ConnectInfo = {
  mcp_url: string;
  example_cursor_snippet: string;
  hint: string;
};

function parseError(text: string, fallback: string): string {
  try {
    const data = JSON.parse(text) as { detail?: string | Array<{ msg?: string }> };
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d) => d.msg || JSON.stringify(d)).join(" | ");
    }
  } catch {
    /* ignore */
  }
  return text || fallback;
}

async function api<T>(path: string, init?: RequestInit, auth = true): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (auth) {
    const token = getSessionToken();
    if (!token) throw new Error("نشست ادمین/کاربر یافت نشد. دوباره وارد شوید.");
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(parseError(text, res.statusText));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const client = {
  login: (username: string, password: string) =>
    api<{ ok: boolean; session_token: string; user: SessionUser }>(
      "/api/auth/login",
      { method: "POST", body: JSON.stringify({ username, password }) },
      false
    ),
  me: () => api<SessionUser>("/api/auth/me"),
  logout: () => api<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
  overview: () => api<Overview>("/api/overview"),
  connect: () => api<ConnectInfo>("/api/connect"),
  users: () => api<User[]>("/api/users"),
  createUser: (body: {
    name: string;
    username: string;
    email: string;
    password: string;
    role?: string;
  }) => api<User>("/api/users", { method: "POST", body: JSON.stringify(body) }),
  myTokens: () => api<Token[]>("/api/me/tokens"),
  createMyToken: (body: { label?: string; tool_ids: number[] }) =>
    api<Token>("/api/me/tokens", { method: "POST", body: JSON.stringify(body) }),
  buildGateway: (body: { label?: string; tool_ids: number[] }) =>
    api<Token>("/api/me/gateway", { method: "POST", body: JSON.stringify(body) }),
  revokeMyToken: (tokenId: number) =>
    api<Token>(`/api/me/tokens/${tokenId}/revoke`, { method: "POST" }),
  myGrants: (tokenId: number) => api<Tool[]>(`/api/me/tokens/${tokenId}/grants`),
  setMyGrants: (tokenId: number, tool_ids: number[]) =>
    api<Tool[]>(`/api/me/tokens/${tokenId}/grants`, {
      method: "PUT",
      body: JSON.stringify({ tool_ids }),
    }),
  catalogTools: () => api<Tool[]>("/api/catalog/tools"),
  servers: () => api<Server[]>("/api/servers"),
  createServer: (body: { name: string; base_url: string; auth_header?: string | null }) =>
    api<Server>("/api/servers", { method: "POST", body: JSON.stringify(body) }),
  createDemoServer: () =>
    api<Server>("/api/servers/demo", { method: "POST", body: "{}" }),
  deleteServer: (id: number) =>
    api<void>(`/api/servers/${id}`, { method: "DELETE" }),
  syncServer: (id: number) =>
    api<Server>(`/api/servers/${id}/sync`, { method: "POST", body: "{}" }),
  serverTools: (id: number) => api<Tool[]>(`/api/servers/${id}/tools`),
};
