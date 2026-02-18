"""
Application configuration management.

Author: C2
Date: 2026-02-13
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 固定 .env 路径：始终从 enterprise_rag 目录加载，避免因启动目录不同读到错误配置（如 Google API）
_ENV_DIR = Path(__file__).resolve().parent.parent.parent  # backend/app -> backend -> enterprise_rag
_DOTENV_PATH = _ENV_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Enterprise RAG System"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"
    log_level: str = "INFO"
    env: str = "development"  # development | production；生产环境不向响应泄露异常详情
    cors_origins: str = "http://localhost:3000"  # 逗号分隔，SPA 跨域白名单

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "enterprise_rag"
    postgres_user: str = "enterprise_rag"
    postgres_password: str = "enterprise_rag"

    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_prefix: str = "kb"

    upload_root_dir: str = "../data/uploads"
    max_file_size_mb: int = 200  # 单文件上传大小上限（MB）
    chunk_size: int = 800
    chunk_overlap: int = 100
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_fallback_dim: int = 64
    retrieval_top_k: int = 5
    reranker_enabled: bool = True
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    reranker_candidate_k: int = 12  # 候选数越小越快，20 易导致首字等待 3~8 秒
    qa_history_max_turns: int = 6

    # 检索去重与动态阈值配置（Phase 2.3）
    dedup_enabled: bool = True
    dedup_simhash_threshold: int = 3  # SimHash 汉明距离阈值，小于等于此值视为重复
    dynamic_threshold_enabled: bool = True
    # Reranker 分数最低阈值：BGE 等模型得分范围不固定，0.3 易把相关结果滤光，改为 0 仅过滤负分
    dynamic_threshold_min: float = 0.0
    # Chroma 余弦距离阈值：越大越宽松。0.65 偏严易导致「未检索到足够知识」，0.8 更宽松
    dynamic_threshold_fallback: float = 0.8

    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model_name: str = "deepseek-chat"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 3
    llm_retry_base_delay: float = 1.0
    llm_temperature: float = 0.2  # Kimi K2.5 仅支持 1.0，其他模型可用 0.2

    jwt_secret_key: str = "please-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 文件夹同步配置（Phase 3.2）
    folder_sync_enabled: bool = True
    folder_sync_interval_minutes: int = 30  # 轮询间隔（分钟）
    folder_sync_batch_size: int = 50  # 单次同步最大文件数

    # 检索质量看板配置（Phase 3.2）
    retrieval_log_enabled: bool = True
    retrieval_log_max_chunks: int = 20  # 日志中记录的最大 chunk 数

    model_config = SettingsConfigDict(
        env_file=str(_DOTENV_PATH) if _DOTENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

