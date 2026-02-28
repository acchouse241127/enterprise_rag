"""
Prometheus metrics for Enterprise RAG system.

Phase 3.3: Prometheus + Grafana 监控
Author: C2
Date: 2026-02-14
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST

# ============== Application Info ==============
APP_INFO = Info("enterprise_rag", "Enterprise RAG System Information")
APP_INFO.info({
    "version": "1.0.0",
    "phase": "3.3",
})

# ============== HTTP Request Metrics ==============
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# ============== Document Processing Metrics ==============
DOCUMENTS_UPLOADED_TOTAL = Counter(
    "documents_uploaded_total",
    "Total documents uploaded",
    ["knowledge_base_id", "file_type"]
)

DOCUMENTS_PARSED_TOTAL = Counter(
    "documents_parsed_total",
    "Total documents parsed",
    ["knowledge_base_id", "status"]  # status: success, failed
)

DOCUMENT_PARSE_DURATION_SECONDS = Histogram(
    "document_parse_duration_seconds",
    "Document parsing duration in seconds",
    ["file_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

DOCUMENT_SIZE_BYTES = Histogram(
    "document_size_bytes",
    "Document size in bytes",
    ["file_type"],
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600]  # 1KB to 100MB
)

# ============== RAG Pipeline Metrics ==============
RAG_QUERIES_TOTAL = Counter(
    "rag_queries_total",
    "Total RAG queries",
    ["knowledge_base_id"]
)

RAG_QUERY_DURATION_SECONDS = Histogram(
    "rag_query_duration_seconds",
    "RAG query duration in seconds",
    ["stage"],  # retrieval, rerank, llm, total
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

RAG_CHUNKS_RETRIEVED = Histogram(
    "rag_chunks_retrieved",
    "Number of chunks retrieved per query",
    [],
    buckets=[1, 2, 5, 10, 20, 50, 100]
)

RAG_TOP_CHUNK_SCORE = Histogram(
    "rag_top_chunk_score",
    "Top chunk similarity score",
    [],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# ============== User Feedback Metrics ==============
USER_FEEDBACK_TOTAL = Counter(
    "user_feedback_total",
    "Total user feedback submissions",
    ["feedback_type"]  # helpful, not_helpful
)

# ============== Async Task Metrics ==============
ASYNC_TASKS_TOTAL = Counter(
    "async_tasks_total",
    "Total async tasks created",
    ["task_type"]
)

ASYNC_TASKS_COMPLETED = Counter(
    "async_tasks_completed",
    "Total async tasks completed",
    ["task_type", "status"]  # success, failed, cancelled
)

ASYNC_TASKS_DURATION_SECONDS = Histogram(
    "async_tasks_duration_seconds",
    "Async task duration in seconds",
    ["task_type"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

ASYNC_TASKS_PENDING = Gauge(
    "async_tasks_pending",
    "Number of pending async tasks",
    ["task_type"]
)

# ============== Knowledge Base Metrics ==============
KNOWLEDGE_BASES_TOTAL = Gauge(
    "knowledge_bases_total",
    "Total number of knowledge bases"
)

DOCUMENTS_TOTAL = Gauge(
    "documents_total",
    "Total number of documents",
    ["knowledge_base_id"]
)

CHUNKS_TOTAL = Gauge(
    "chunks_total",
    "Total number of chunks in vector store",
    ["knowledge_base_id"]
)

# ============== System Metrics ==============
ACTIVE_USERS = Gauge(
    "active_users",
    "Number of active users in the last hour"
)

# ============== Helper Functions ==============
def get_metrics() -> bytes:
    """Generate Prometheus metrics output."""
    return generate_latest()


def get_content_type() -> str:
    """Get Prometheus content type."""
    return CONTENT_TYPE_LATEST

# ============== V2.0 Quality Assurance Metrics ==============
QA_CONFIDENCE_SCORE = Histogram(
    "qa_confidence_score",
    "Answer confidence score distribution",
    ["knowledge_base_id"],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

QA_FAITHFULNESS_SCORE = Histogram(
    "qa_faithfulness_score",
    "Answer faithfulness score distribution",
    ["knowledge_base_id"],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

QA_REFUSAL_TOTAL = Counter(
    "qa_refusal_total",
    "Total QA refusals",
    ["knowledge_base_id", "refusal_reason"]
)

QA_VERIFICATION_ACTION_TOTAL = Counter(
    "qa_verification_action_total",
    "Total QA verification actions",
    ["knowledge_base_id", "action"]  # pass, filter, retry, refuse
)
