import { apiClient, getToken, logout, API_BASE } from "./client";
import type {
  Conversation,
  ConversationResponse,
  SharedConversationResponse,
} from "./types";

export async function getConversations(params?: {
  knowledge_base_id?: number | string;
  limit?: number;
  offset?: number;
}): Promise<Conversation[]> {
  const searchParams = new URLSearchParams();
  if (params?.knowledge_base_id) searchParams.set("knowledge_base_id", String(params.knowledge_base_id));
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  const query = searchParams.toString();
  const response = await apiClient.get<Conversation[]>(
    `/api/conversations${query ? `?${query}` : ""}`
  );
  return response.data;
}

export async function getConversation(id: number): Promise<ConversationResponse> {
  const response = await apiClient.get<ConversationResponse>(`/api/conversations/${id}`);
  return response.data;
}

export async function deleteConversation(id: number): Promise<void> {
  await apiClient.delete(`/api/conversations/${id}`);
}

export async function shareConversation(id: number, expiresInDays?: number): Promise<{ data: { share_token: string; share_url?: string; expires_at?: string } }> {
  const response = await apiClient.post<{ data: { share_token: string; share_url?: string; expires_at?: string } }>(
    `/api/conversations/${id}/share`,
    expiresInDays ? { expires_in_days: expiresInDays } : {}
  );
  return response.data;
}

export async function getSharedConversation(shareId: string): Promise<SharedConversationResponse> {
  const response = await apiClient.get<SharedConversationResponse>(
    `/api/conversations/share/${shareId}`
  );
  return response.data;
}

export async function exportConversationFile(
  id: number,
  format: "markdown" | "pdf" | "docx"
): Promise<{ blob: Blob; filename: string }> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/conversations/${id}/export/${format}`, {
    method: "GET",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 401) {
    logout();
    throw new Error("未登录或已过期");
  }
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text);
  }
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  let filename = `conversation_${id}.${format === "markdown" ? "md" : format}`;
  const match = disposition.match(/filename\*?=(?:UTF-8''|")?([^";\n]+)/i);
  if (match && match[1]) {
    filename = decodeURIComponent(match[1]);
  }
  return { blob, filename };
}
