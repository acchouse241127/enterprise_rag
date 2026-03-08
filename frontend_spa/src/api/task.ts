import { apiClient } from "./client";
import type { TasksResponse } from "./types";

/** 与后端 /api/tasks 一致（仅支持 list、get、cancel，无 retry/cleanup） */
const TASKS_PATH = "/api/tasks";

export async function getTasks(params?: {
  taskType?: string;
  status?: string;
  entityType?: string;
  entityId?: number;
  limit?: number;
  offset?: number;
}): Promise<TasksResponse> {
  const searchParams = new URLSearchParams();
  if (params?.taskType) searchParams.set("task_type", params.taskType);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.entityType) searchParams.set("entity_type", params.entityType);
  if (params?.entityId) searchParams.set("entity_id", String(params.entityId));
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  const query = searchParams.toString();
  const response = await apiClient.get<TasksResponse>(`${TASKS_PATH}${query ? `?${query}` : ""}`);
  return response.data;
}

export async function cancelTask(taskId: number): Promise<void> {
  await apiClient.post(`${TASKS_PATH}/${taskId}/cancel`);
}
