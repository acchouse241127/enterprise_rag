import { apiClient } from "./client";
import type {
  RetrievalStatsResponse,
  DailyStatsResponse,
  KbStatsResponse,
  RetrievalLogsResponse,
  RetrievalLogDetailResponse,
  AddFeedbackRequest,
  AddFeedbackResponse,
  MarkSampleResponse,
  ProblemSamplesResponse,
} from "./types";

// ========== Stats ==========

export async function getRetrievalStats(params?: {
  knowledgeBaseId?: number;
  startDate?: string;
  endDate?: string;
}): Promise<RetrievalStatsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.knowledgeBaseId)
    searchParams.set("knowledge_base_id", String(params.knowledgeBaseId));
  if (params?.startDate) searchParams.set("start_date", params.startDate);
  if (params?.endDate) searchParams.set("end_date", params.endDate);
  const query = searchParams.toString();
  const response = await apiClient.get<RetrievalStatsResponse>(
    `/api/retrieval/stats${query ? `?${query}` : ""}`
  );
  return response.data;
}

export async function getStatsByDate(params?: {
  knowledgeBaseId?: number;
  days?: number;
}): Promise<DailyStatsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.knowledgeBaseId)
    searchParams.set("knowledge_base_id", String(params.knowledgeBaseId));
  if (params?.days) searchParams.set("days", String(params.days));
  const query = searchParams.toString();
  const response = await apiClient.get<DailyStatsResponse>(
    `/api/retrieval/stats/by-date${query ? `?${query}` : ""}`
  );
  return response.data;
}

export async function getStatsByKnowledgeBase(params?: {
  startDate?: string;
  endDate?: string;
}): Promise<KbStatsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.startDate) searchParams.set("start_date", params.startDate);
  if (params?.endDate) searchParams.set("end_date", params.endDate);
  const query = searchParams.toString();
  const response = await apiClient.get<KbStatsResponse>(
    `/api/retrieval/stats/by-knowledge-base${query ? `?${query}` : ""}`
  );
  return response.data;
}

// ========== Logs ==========

export async function getRetrievalLogs(params?: {
  knowledgeBaseId?: number;
  hasFeedback?: boolean;
  feedbackType?: "helpful" | "not_helpful";
  limit?: number;
  offset?: number;
}): Promise<RetrievalLogsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.knowledgeBaseId)
    searchParams.set("knowledge_base_id", String(params.knowledgeBaseId));
  if (params?.hasFeedback !== undefined)
    searchParams.set("has_feedback", String(params.hasFeedback));
  if (params?.feedbackType)
    searchParams.set("feedback_type", params.feedbackType);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  const query = searchParams.toString();
  const response = await apiClient.get<RetrievalLogsResponse>(
    `/api/retrieval/logs${query ? `?${query}` : ""}`
  );
  return response.data;
}

export async function getRetrievalLogDetail(
  logId: number
): Promise<RetrievalLogDetailResponse> {
  const response = await apiClient.get<RetrievalLogDetailResponse>(
    `/api/retrieval/logs/${logId}`
  );
  return response.data;
}

// ========== Feedback ==========

export async function addFeedback(
  data: AddFeedbackRequest
): Promise<AddFeedbackResponse> {
  const response = await apiClient.post<AddFeedbackResponse>(
    "/api/retrieval/feedback",
    data
  );
  return response.data;
}

export async function markFeedbackAsSample(
  feedbackId: number,
  isSample: boolean
): Promise<MarkSampleResponse> {
  const response = await apiClient.post<MarkSampleResponse>(
    `/api/retrieval/feedback/${feedbackId}/mark-sample`,
    { is_sample: isSample }
  );
  return response.data;
}

// ========== Problem Samples ==========

export async function getProblemSamples(params?: {
  knowledgeBaseId?: number;
  limit?: number;
  offset?: number;
}): Promise<ProblemSamplesResponse> {
  const searchParams = new URLSearchParams();
  if (params?.knowledgeBaseId)
    searchParams.set("knowledge_base_id", String(params.knowledgeBaseId));
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  const query = searchParams.toString();
  const response = await apiClient.get<ProblemSamplesResponse>(
    `/api/retrieval/samples${query ? `?${query}` : ""}`
  );
  return response.data;
}

// ========== Dashboard (alias for stats) ==========

export async function getDashboardStats(params?: {
  kbId?: number;
  startDate?: string;
  endDate?: string;
}): Promise<RetrievalStatsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.kbId) searchParams.set("knowledge_base_id", String(params.kbId));
  if (params?.startDate) searchParams.set("start_date", params.startDate);
  if (params?.endDate) searchParams.set("end_date", params.endDate);
  const query = searchParams.toString();
  const response = await apiClient.get<RetrievalStatsResponse>(
    `/api/retrieval/dashboard${query ? `?${query}` : ""}`
  );
  return response.data;
}
