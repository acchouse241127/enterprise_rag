"""
Application constants.

Centralized configuration values to avoid magic numbers in code.

Author: System
Date: 2026-03-07
"""

# ===========================================
# Citation Constants
# ===========================================
CITATION_SIMILARITY_THRESHOLD = 0.58
CITATION_SNIPPET_MAX_LENGTH = 150

# ===========================================
# Cache Constants
# ===========================================
CACHE_DEFAULT_TTL_SECONDS = 86400  # 24 hours
CACHE_SEMANTIC_THRESHOLD = 0.95
CACHE_MAX_ENTRIES_PER_KB = 1000

# ===========================================
# Retrieval Constants
# ===========================================
RETRIEVAL_TIMEOUT_MS = 500
RETRIEVAL_TOP_K_DEFAULT = 5
RETRIEVAL_CANDIDATE_K_DEFAULT = 12

# ===========================================
# Reranker Constants
# ===========================================
RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"
RERANKER_ENABLED = True

# ===========================================
# Dedup Constants
# ===========================================
DEDUP_SIMHASH_THRESHOLD = 3
DEDUP_ENABLED = True

# ===========================================
# Dynamic Threshold Constants
# ===========================================
DYNAMIC_THRESHOLD_MIN = 0.0
DYNAMIC_THRESHOLD_FALLBACK = 0.8
DYNAMIC_THRESHOLD_ENABLED = True

# ===========================================
# Upload Constants
# ===========================================
MAX_FILE_SIZE_MB = 200
SUPPORTED_FILE_EXTENSIONS = {
    "text": {".txt", ".md"},
    "document": {".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx"},
    "image": {".png", ".jpg", ".jpeg"},
}

# ===========================================
# QA Constants
# ===========================================
QA_HISTORY_MAX_TURNS = 6

# ===========================================
# Security Constants
# ===========================================
BCRYPT_MAX_PASSWORD_BYTES = 72
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# ===========================================
# Health Check Constants
# ===========================================
HEALTH_CHECK_INTERVAL_SECONDS = 30

# ===========================================
# Folder Sync Constants
# ===========================================
FOLDER_SYNC_INTERVAL_MINUTES = 30
FOLDER_SYNC_BATCH_SIZE = 50

# ===========================================
# Retrieval Log Constants
# ===========================================
RETRIEVAL_LOG_MAX_CHUNKS = 20

# ===========================================
# Verification Constants
# ===========================================
VERIFICATION_CONFIDENCE_THRESHOLD = 0.5
VERIFICATION_CITATION_THRESHOLD = 0.5
VERIFICATION_REFUSAL_THRESHOLD = 0.3

# ===========================================
# Degradation Strategy Constants
# ===========================================
DEGRADATION_LEVELS = {
    "L0_NORMAL": "L0_NORMAL",
    "L1_VECTOR_TIMEOUT": "L1_VECTOR_TIMEOUT",
    "L2_VECTOR_UNAVAILABLE": "L2_VECTOR_UNAVAILABLE",
    "L3_ALL_FAILED": "L3_ALL_FAILED",
}
