import { apiClient } from "./client";
import type { FeedbackResponse, GetFeedbackResponse } from "./types";

/** 后端接口: POST /api/retrieval/feedback */
const FEEDBACK_PATH = "/api/retrieval/feedback";

/** 后端接口: GET /api/retrieval/logs/{log_id} 返回的 data.feedbacks 用于 getFeedback */
const RETRIEVAL_LOG_PATH = "/api/retrieval/logs";

// V2.0 新增：提交用户反馈（与后端 /api/retrieval/feedback 一致）
export async function submitFeedback(
  retrievalLogId: number,
  rating: "thumbs_up" | "thumbs_down",
  reason?: string
): Promise<FeedbackResponse> {
  const payload = {
    retrieval_log_id: retrievalLogId,
    feedback_type: rating === "thumbs_up" ? "helpful" : "not_helpful",
    rating: rating === "thumbs_up" ? 1 : -1,
    ...(reason ? { reason, comment: reason } : {}),
  };
  const response = await apiClient.post<FeedbackResponse>(FEEDBACK_PATH, payload);
  return response.data;
}

// V2.0 新增：通过检索日志接口获取某次问答的反馈（与后端 GET /api/retrieval/logs/{id} 一致）
export async function getFeedback(retrievalLogId: number): Promise<GetFeedbackResponse | null> {
  try {
    const response = await apiClient.get<{
      code: number;
      data?: { feedbacks: Array<{ feedback_type: string; comment?: string; created_at: string }> };
    }>(`${RETRIEVAL_LOG_PATH}/${retrievalLogId}`);
    const feedbacks = response.data?.data?.feedbacks;
    if (!feedbacks?.length) return null;
    const fb = feedbacks[0];
    return {
      data: {
        rating: fb.feedback_type === "helpful" ? "thumbs_up" : "thumbs_down",
        reason: fb.comment ?? "",
        created_at: fb.created_at,
      },
    };
  } catch {
    return null;
  }
}
