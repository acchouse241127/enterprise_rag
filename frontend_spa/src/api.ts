import { getToken, logout } from "./auth";

const API_BASE = import.meta.env.VITE_API_BASE || "";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    logout();
    throw new Error("未登录或已过期");
  }
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function login(username: string, password: string): Promise<{ data: { access_token: string } }> {
  return request("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
}

export async function getMe(): Promise<{ data: { id: number; username: string } }> {
  return request("/api/auth/me");
}

export async function getKnowledgeBases(): Promise<{ data: Array<{ id: number; name: string }> }> {
  return request("/api/knowledge-bases");
}

export async function getDocuments(kbId: number): Promise<{ data: Array<{ id: number; filename: string; status: string }> }> {
  return request(`/api/knowledge-bases/${kbId}/documents`);
}

export { request };
