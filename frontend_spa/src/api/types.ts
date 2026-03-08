// ========== Auth ==========
export interface LoginResponse {
  code: number;
  message?: string;
  detail?: string;
  data?: {
    access_token: string;
    token_type?: string;
  };
}

export interface MeResponse {
  code: number;
  message?: string;
  data: {
    id: number;
    username: string;
    role: string;
    is_admin: boolean;
  };
}

// ========== Knowledge Base ==========
export interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  chunk_size?: number;
  chunk_overlap?: number;
  // V2.0 新增
  chunk_mode?: "char" | "sentence" | "token" | "chinese_recursive";
  parent_retrieval_mode?: "physical" | "dynamic" | "off";
  dynamic_expand_n?: number;
  default_retrieval_strategy?: "smart" | "precise" | "fast" | "deep";
  created_at?: string;
}

export interface CreateKnowledgeBaseRequest {
  name: string;
  description?: string;
  chunk_size?: number;
  chunk_overlap?: number;
  // V2.0 新增
  chunk_mode?: "char" | "sentence" | "token" | "chinese_recursive";
  parent_retrieval_mode?: "physical" | "dynamic" | "off";
  dynamic_expand_n?: number;
  default_retrieval_strategy?: "smart" | "precise" | "fast" | "deep";
}

export interface KnowledgeBasesResponse {
  data: KnowledgeBase[];
}

export interface KnowledgeBaseResponse {
  data: KnowledgeBase;
}

// ========== Document ==========
export interface Document {
  id: number;
  title?: string;
  filename: string;
  file_type?: string;
  file_size?: number;
  status: string;
  parser_message?: string;
  version?: number;
  created_at?: string;
}

export interface DocumentsResponse {
  data: Document[];
}

export interface DocumentResponse {
  data: Document;
}

export interface DocumentContentResponse {
  data: {
    content: string;
  };
}

export interface DocumentPreviewResponse {
  data: {
    id: number;
    filename: string;
    status: string;
    content: string;
  };
}

// ========== QA ==========
export interface Citation {
  id: number;
  chunk_id?: string;
  document_id?: number;
  filename?: string;
  chunk_index?: number;
  content_preview?: string;
  snippet?: string;
  reason?: string;
}

export interface Strategy {
  name: string;
  display_name: string;
  description: string;
  top_k: number;
  expansion_enabled: boolean;
  expansion_mode: "rule" | "llm" | "hybrid" | "none";
  keyword_enabled: boolean;
  retrieval_mode: "vector" | "bm25" | "hybrid";
  reranker_candidate_k: number;
}

export interface StrategiesResponse {
  data: Strategy[];
}

export interface QueryExpansionMeta {
  default_mode: "rule" | "llm" | "hybrid";
  default_cloud_model_name: string;
  local_available: boolean;
  supported_modes: Array<"rule" | "llm" | "hybrid">;
  supported_targets: Array<"cloud" | "local" | "default">;
  providers: string[];
}

export interface QueryExpansionMetaResponse {
  data: QueryExpansionMeta;
}

export interface QueryExpansionLlmConfig {
  provider?: "openai" | "deepseek";
  model_name?: string;
  base_url?: string;
  api_key?: string;
  temperature?: number;
  timeout_seconds?: number;
  max_retries?: number;
  retry_base_delay?: number;
}

// V2.0 新增：验证结果
export interface VerificationResult {
  confidence_score: number;
  confidence_level: "high" | "medium" | "low";
  faithfulness_score: number;
  has_hallucination: boolean;
  citation_accuracy: number;
}

// V2.0 新增：拒答信息
export interface RefusalInfo {
  reason: "empty_retrieval" | "low_relevance" | "low_faithfulness";
  message: string;
}

export interface StreamQaOptions {
  strategy?: string;
  conversationId?: string;
  topK?: number;
  systemPromptVersion?: "A" | "B" | "C";
  queryExpansionMode?: "rule" | "llm" | "hybrid";
  queryExpansionTarget?: "cloud" | "local" | "default";
  queryExpansionLlm?: QueryExpansionLlmConfig;
  // V2.0 新增
  retrievalMode?: "vector" | "bm25" | "hybrid";
}

// ========== Feedback (V2.0 新增) ==========
export interface SubmitFeedbackRequest {
  retrieval_log_id: number;
  rating: "thumbs_up" | "thumbs_down";
  reason?: string;
}

export interface FeedbackResponse {
  data: {
    id: string;
    created_at: string;
  };
}

export interface GetFeedbackResponse {
  data: {
    rating: string;
    reason: string;
    created_at: string;
  };
}

// ========== Conversations ==========
export interface Conversation {
  id: number;
  conversation_id: string;
  title?: string;
  knowledge_base_id: number;
  is_shared: boolean;
  share_token?: string;
  share_expires_at?: string;
  user_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface ConversationsResponse {
  // 后端直接返回数组，没有 data 包装
  [index: number]: Conversation;
  length: number;
}

export interface SharedConversation {
  id: string;
  title?: string;
  knowledge_base_name?: string;
  created_at: string;
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    created_at: string;
    citations?: Citation[];
  }>;
}

export interface SharedConversationResponse {
  code: number;
  message: string;
  data: SharedConversation;
}

export interface ConversationResponse {
  data: SharedConversation;
}

// ========== Tasks ==========
export interface Task {
  id: number;
  task_type: string;
  entity_type?: string;
  entity_id?: number;
  filename?: string;
  name?: string;
  status: string;
  progress: number;
  message?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface TasksResponse {
  tasks: Task[];
  total: number;
}

// ========== Folder Sync ==========
export interface FolderSyncConfig {
  id?: number;
  knowledge_base_id?: number;
  directory_path: string;
  enabled: boolean;
  sync_interval_minutes: number;
  file_patterns: string;
  last_sync_at?: string | null;
  last_sync_status?: string;
  last_sync_message?: string | null;
  last_sync_files_added?: number;
  last_sync_files_updated?: number;
  last_sync_files_deleted?: number;
}

export interface FolderSyncConfigResponse {
  code: number;
  message: string;
  data: FolderSyncConfig | null;
}

export interface FolderSyncLog {
  id: number;
  status: string;
  message?: string;
  files_scanned: number;
  files_added: number;
  files_updated: number;
  files_deleted: number;
  files_failed: number;
  duration_seconds: number;
  triggered_by: string;
  created_at: string;
}

export interface FolderSyncLogsResponse {
  code: number;
  message: string;
  data: FolderSyncLog[];
}

export interface SyncNowResponse {
  code: number;
  message: string;
  data: {
    id: number;
    status: string;
    message?: string;
    files_scanned: number;
    files_added: number;
    files_updated: number;
    files_deleted: number;
    files_failed: number;
    duration_seconds: number;
    triggered_by: string;
    created_at: string;
  };
}

export interface DeleteSyncConfigResponse {
  code: number;
  message: string;
  data: { deleted: boolean };
}

// ========== Dashboard / Retrieval Stats ==========
export interface RetrievalStats {
  total_queries: number;
  avg_top_score: number | null;
  avg_response_time_ms: number | null;
  not_helpful_ratio: number;
  helpful_count: number;
  not_helpful_count: number;
  sample_count: number;
  avg_chunks_returned: number | null;
  retrieval_log_enabled: boolean;
}

export interface RetrievalStatsResponse {
  code: number;
  message: string;
  data: RetrievalStats;
}

export interface DailyStats {
  date: string;
  query_count: number;
  avg_score: number | null;
}

export interface DailyStatsResponse {
  code: number;
  message: string;
  data: DailyStats[];
}

export interface KbStats {
  knowledge_base_id: number;
  knowledge_base_name: string;
  query_count: number;
  avg_score: number | null;
  avg_time_ms: number | null;
  helpful_count: number;
  not_helpful_count: number;
}

export interface KbStatsResponse {
  code: number;
  message: string;
  data: KbStats[];
}

export interface RetrievalLogFeedback {
  id: number;
  feedback_type: "helpful" | "not_helpful";
  is_sample_marked: boolean;
}

export interface RetrievalLog {
  id: number;
  knowledge_base_id: number;
  user_id: number;
  query: string;
  chunks_retrieved: number;
  chunks_after_rerank: number;
  top_chunk_score: number | null;
  avg_chunk_score: number | null;
  total_time_ms: number | null;
  answer_generated: boolean;
  created_at: string;
  feedbacks: RetrievalLogFeedback[];
}

export interface RetrievalLogsResponse {
  code: number;
  message: string;
  data: {
    total: number;
    items: RetrievalLog[];
  };
}

export interface RetrievalLogDetail extends RetrievalLog {
  query_embedding_time_ms: number | null;
  retrieval_time_ms: number | null;
  rerank_time_ms: number | null;
  llm_time_ms: number | null;
  chunks_after_filter: number | null;
  chunks_after_dedup: number | null;
  min_chunk_score: number | null;
  chunk_details: string | null;
  answer_length: number | null;
  error_message: string | null;
}

export interface RetrievalLogDetailResponse {
  code: number;
  message: string;
  data: RetrievalLogDetail;
}

export interface AddFeedbackRequest {
  retrieval_log_id: number;
  feedback_type: "helpful" | "not_helpful";
  rating: number;
  reason?: string;
  comment?: string;
}

export interface AddFeedbackResponse {
  code: number;
  message: string;
  data: {
    id: number;
    retrieval_log_id: number;
    feedback_type: string;
    comment?: string;
    created_at: string;
  };
}

export interface MarkSampleRequest {
  is_sample: boolean;
}

export interface MarkSampleResponse {
  code: number;
  message: string;
  data: {
    id: number;
    is_sample_marked: boolean;
  };
}

export interface ProblemSample {
  id: number;
  knowledge_base_id: number;
  query: string;
  top_chunk_score: number | null;
  created_at: string;
  feedbacks: RetrievalLogFeedback[];
}

export interface ProblemSamplesResponse {
  code: number;
  message: string;
  data: {
    total: number;
    items: ProblemSample[];
  };
}

export interface DashboardStatsResponse {
  code: number;
  message: string;
  data: RetrievalStats;
}

// ========== Docker Mount ==========
export interface DockerMountRequest {
  host_path: string;
  container_path?: string;
}

export interface DockerMountResponse {
  code: number;
  message: string;
  data: {
    success: boolean;
    message: string;
    container_name?: string;
    container_path?: string;
    host_path?: string;
  };
}

export interface ContainerStatus {
  name: string;
  status: string;
  running: boolean;
  image: string;
}

export interface DockerStatusResponse {
  code: number;
  message?: string;
  data: {
    success: boolean;
    docker_version?: string;
    api_version?: string;
    os?: string;
    backend?: ContainerStatus;
    worker?: ContainerStatus;
    enabled: boolean;
    message?: string;
  };
}

export interface RestartContainerResponse {
  code: number;
  message: string;
  data: {
    success: boolean;
    message: string;
    container_name?: string;
  };
}
