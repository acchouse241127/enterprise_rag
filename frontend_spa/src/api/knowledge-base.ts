import { apiClient } from "./client";
import type {
  KnowledgeBase,
  KnowledgeBasesResponse,
  KnowledgeBaseResponse,
  CreateKnowledgeBaseRequest,
  DocumentsResponse,
  DocumentResponse,
  DocumentContentResponse,
  DocumentPreviewResponse,
  FolderSyncConfigResponse,
  FolderSyncLogsResponse,
  SyncNowResponse,
  DeleteSyncConfigResponse,
  DockerMountResponse,
  DockerStatusResponse,
  RestartContainerResponse,
} from "./types";
import { getToken, logout, API_BASE } from "./client";

// ========== Knowledge Bases ==========

export async function getKnowledgeBases(): Promise<KnowledgeBasesResponse> {
  const response = await apiClient.get<KnowledgeBasesResponse>("/api/knowledge-bases");
  return response.data;
}

export async function createKnowledgeBase(
  data: CreateKnowledgeBaseRequest
): Promise<KnowledgeBaseResponse> {
  const response = await apiClient.post<KnowledgeBaseResponse>("/api/knowledge-bases", data);
  return response.data;
}

export async function getKnowledgeBase(id: number): Promise<KnowledgeBaseResponse> {
  const response = await apiClient.get<KnowledgeBaseResponse>(`/api/knowledge-bases/${id}`);
  return response.data;
}

export async function updateKnowledgeBase(
  id: number,
  data: Partial<KnowledgeBase>
): Promise<KnowledgeBaseResponse> {
  const response = await apiClient.put<KnowledgeBaseResponse>(`/api/knowledge-bases/${id}`, data);
  return response.data;
}

export async function deleteKnowledgeBase(id: number): Promise<void> {
  await apiClient.delete(`/api/knowledge-bases/${id}`);
}

// ========== Documents ==========

export async function getDocuments(kbId: number): Promise<DocumentsResponse> {
  const response = await apiClient.get<DocumentsResponse>(
    `/api/knowledge-bases/${kbId}/documents`
  );
  return response.data;
}

export async function uploadDocument(
  kbId: number,
  file: File
): Promise<DocumentResponse> {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/knowledge-bases/${kbId}/documents`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  if (res.status === 401) {
    logout();
    throw new Error("未登录或已过期");
  }
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text);
  }
  return res.json();
}

export async function importUrl(kbId: number, url: string): Promise<DocumentResponse> {
  const response = await apiClient.post<DocumentResponse & { code?: number; detail?: string; message?: string }>(
    `/api/knowledge-bases/${kbId}/documents/from-url`,
    { url }
  );
  const data = response.data;
  if (data?.code !== 0 && data?.code !== undefined) {
    throw new Error(data.detail ?? data.message ?? "导入失败");
  }
  return data;
}

export async function getDocument(_kbId: number, docId: number): Promise<DocumentResponse> {
  const response = await apiClient.get<DocumentResponse>(`/api/documents/${docId}`);
  return response.data;
}

export async function getDocumentContent(
  _kbId: number,
  docId: number
): Promise<DocumentContentResponse> {
  const response = await apiClient.get<DocumentContentResponse>(
    `/api/knowledge-bases/documents/${docId}/content`
  );
  return response.data;
}

export async function updateDocumentContent(
  _kbId: number,
  docId: number,
  content: string
): Promise<DocumentResponse> {
  const response = await apiClient.put<DocumentResponse>(
    `/api/knowledge-bases/documents/${docId}/content`,
    { content }
  );
  return response.data;
}

export async function deleteDocument(_kbId: number, docId: number): Promise<void> {
  await apiClient.delete(`/api/documents/${docId}`);
}

export async function reparseDocument(_kbId: number, docId: number): Promise<DocumentResponse> {
  const response = await apiClient.post<DocumentResponse>(
    `/api/documents/${docId}/reparse`
  );
  return response.data;
}

export async function rechunkDocument(_kbId: number, docId: number): Promise<DocumentResponse> {
  const response = await apiClient.post<DocumentResponse>(
    `/api/knowledge-bases/documents/${docId}/rechunk`
  );
  return response.data;
}

export async function getDocumentPreview(
  docId: number
): Promise<DocumentPreviewResponse> {
  const response = await apiClient.get<DocumentPreviewResponse>(
    `/api/documents/${docId}/preview`
  );
  return response.data;
}

export async function downloadDocumentFile(
  docId: number
): Promise<{ blob: Blob; filename: string }> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/documents/${docId}/download`, {
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
  let filename = `document_${docId}`;
  const match = disposition.match(/filename\*?=(?:UTF-8''|")?([^";\n]+)/i);
  if (match && match[1]) {
    filename = decodeURIComponent(match[1]);
  }
  return { blob, filename };
}

export async function getDocumentVersions(docId: number): Promise<DocumentsResponse> {
  const response = await apiClient.get<DocumentsResponse>(`/api/documents/${docId}/versions`);
  return response.data;
}

export async function activateDocumentVersion(docId: number): Promise<DocumentResponse> {
  const response = await apiClient.post<DocumentResponse>(
    `/api/documents/${docId}/activate`
  );
  return response.data;
}

// ========== Folder Sync ==========

export async function getFolderSyncConfig(
  kbId: number
): Promise<FolderSyncConfigResponse> {
  const response = await apiClient.get<FolderSyncConfigResponse>(
    `/api/knowledge-bases/${kbId}/folder-sync`
  );
  return response.data;
}

export async function updateFolderSyncConfig(
  kbId: number,
  config: {
    directory_path: string;
    enabled?: boolean;
    sync_interval_minutes?: number;
    file_patterns?: string;
  }
): Promise<FolderSyncConfigResponse> {
  const response = await apiClient.post<FolderSyncConfigResponse>(
    `/api/knowledge-bases/${kbId}/folder-sync`,
    config
  );
  return response.data;
}

export async function deleteFolderSyncConfig(
  kbId: number
): Promise<DeleteSyncConfigResponse> {
  const response = await apiClient.delete<DeleteSyncConfigResponse>(
    `/api/knowledge-bases/${kbId}/folder-sync`
  );
  return response.data;
}

export async function syncFolderNow(kbId: number): Promise<SyncNowResponse> {
  const response = await apiClient.post<SyncNowResponse>(
    `/api/knowledge-bases/${kbId}/folder-sync/trigger`
  );
  return response.data;
}

export async function getFolderSyncLogs(
  kbId: number,
  limit: number = 20
): Promise<FolderSyncLogsResponse> {
  const response = await apiClient.get<FolderSyncLogsResponse>(
    `/api/knowledge-bases/${kbId}/folder-sync/logs?limit=${limit}`
  );
  return response.data;
}

// ========== Docker Mount ==========

export async function mountDockerVolume(
  kbId: number,
  hostPath: string,
  containerPath?: string
): Promise<DockerMountResponse> {
  const response = await apiClient.post<DockerMountResponse>(
    `/api/docker/mount/${kbId}`,
    {
      host_path: hostPath,
      container_path: containerPath,
    }
  );
  return response.data;
}

export async function getDockerStatus(): Promise<DockerStatusResponse> {
  const response = await apiClient.get<DockerStatusResponse>("/api/docker/status");
  return response.data;
}

export async function restartContainer(
  containerName: string
): Promise<RestartContainerResponse> {
  const response = await apiClient.post<RestartContainerResponse>(
    `/api/docker/restart/${containerName}`
  );
  return response.data;
}
