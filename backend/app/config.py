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
    cors_origins: str = "http://localhost:3000,http://localhost:3003,http://localhost:5173"  # 逗号分隔，SPA 3000 + Vite dev 3003/5173
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "enterprise_rag"
    postgres_user: str = "enterprise_rag"
    postgres_password: str = "enterprise_rag"
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_prefix: str = "kb"
    upload_root_dir: str = "../data/uploads"
    max_file_size_mb: int = 200  # 单文件上传大小上限（MB），不区分文件格式，可由 MAX_FILE_SIZE_MB 覆盖
    chunk_size: int = 800
    chunk_overlap: int = 100
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_fallback_dim: int = 64
    retrieval_top_k: int = 5
    retrieval_use_keyword: bool = True  # 是否启用关键词一路召回（与向量合并）
    retrieval_query_expansion_enabled: bool = True  # 是否启用查询扩展
    retrieval_query_expansion_mode: str = "rule"  # rule | llm | hybrid（查询扩展模式）
    retrieval_strategy: str = "smart"  # smart | precise | fast | deep（与 retrieval_strategy.py 保持一致）
    reranker_enabled: bool = True
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    reranker_candidate_k: int = 12  # 候选数越小越快，20 易导致首字等待 3~8 秒
    qa_history_max_turns: int = 6

    # 检索去重与动态阈值配置（Phase 2.3）
    dedup_enabled: bool = True
    dedup_simhash_threshold: int = 3  # SimHash 相似距离阈值，小于等于此值视为重复
    dynamic_threshold_enabled: bool = True
    # Reranker 分数最低阈值：BGE 模型得分范围不固定，0.3 易把相关结果滤光，改为 0 仅过滤负分
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
    # 略略 B 覆盖：按任务类型覆盖 model/base_url/api_key，空则全部用默认
    llm_task_overrides: dict[str, dict] | None = None  # Strategy B: e.g. {"qa": {"model_name": "strong-model"}}
    jwt_secret_key: str = "CHANGE_THIS_IN_PRODUCTION_USE_RANDOM_32_CHARS_OR_MORE"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 文件夹同步配置（Phase 2.3）
    folder_sync_enabled: bool = True
    folder_sync_interval_minutes: int = 30  # 潜询间隔（分钟）
    folder_sync_batch_size: int = 50  # 单次同步最大文件数

    # 检索质量看板配置（Phase 2.3）
    retrieval_log_enabled: bool = True
    retrieval_log_max_chunks: int = 20  # 日志中记录的最大 chunk 数

    # V2.0 质量保障配置
    verification_enabled: bool = False  # 是否启用答案验证（NLI 模型加载较慢，默认关闭）
    verification_confidence_threshold: float = 0.5
    verification_citation_threshold: float = 0.5
    verification_refusal_threshold: float = 0.3

    # Redis & Celery（队列与 Worker）
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = ""  # 空则使用 redis_url

    # ============ 搜索优化配置 (2026-03-03) ============
    cache_enabled: bool = True
    cache_default_ttl_seconds: int = 86400  # 24小时
    cache_semantic_threshold: float = 0.95
    cache_max_entries_per_kb: int = 1000
    retrieval_timeout_ms: int = 500
    retrieval_fallback_enabled: bool = True
    health_check_interval_seconds: int = 30

    # 降级策略
    retrieval_timeout_ms: int = 500
    retrieval_fallback_enabled: bool = True

    # 日志格式：JSON 结构化日志（便于日志采集系统）或文本格式（便于开发调试）
    log_json_format: bool = False

    # PII 匿名化
    pii_anonymization_enabled: bool = True
    pii_types: list[str] = ["phone", "id_card", "bank_card", "email", "address", "name"]
    pii_custom_rules: list[dict] = []

    # 禁用词库
    forbidden_words_enabled: bool = True
    forbidden_words_cache_ttl_seconds: int = 300
    forbidden_words_default_action: str = "replace"  # replace | block

    # 自查询检索器
    self_query_enabled: bool = True
    self_query_llm_temperature: float = 0.1
    self_query_max_filter_fields: int = 5

    # SPLADE 疏疏嵌入
    splade_enabled: bool = False
    splade_model_name: str = "naver/splade_v3_distil"
    splade_max_vocab_size: int = 30522
    splade_threshold: float = 0.1

    # V2.0 Phase 4: Docling PDF 解析器配置
    pdf_parser_backend: str = "docling"  # "legacy" | "docling"
    docling_ocr_enabled: bool = True  # Docling OCR 开关（扫描 PDF）
    docling_images_subdir: str = "images"  # 提取图片的存储子目录

    # V2.0 Phase 5: VLM 图片描述配置
    vlm_enabled: bool = False  # 是否启用 VLM 图片描述（默认关闭，需配置 API Key）
    vlm_provider: str = "openai"  # VLM 提供者: "openai" | "deepseek"
    vlm_api_key: str = ""  # VLM API Key（如与 LLM 相同可留空复用）
    vlm_base_url: str = ""  # VLM API 地址（留空则使用 LLM 配置）
    vlm_model_name: str = "gpt-4o-mini"  # VLM 模型名称
    vlm_max_tokens: int = 500  # VLM 最大生成 token 数
    vlm_timeout_seconds: int = 60  # VLM 请求超时时间
    vlm_max_retries: int = 3  # VLM 最大重试次数
    vlm_async_processing: bool = True  # 是否异步处理图片描述（不阻塞主流程）

    # ============ V2.0 Phase 6: 检索增强配置 ============
    # 查询分析器配置
    query_analyzer_enabled: bool = True  # 是否启用查询分析
    query_analysis_min_confidence: float = 0.3  # 最低置信度才应用增强
    # 模态感知排序配置
    modality_aware_ranking_enabled: bool = True  # 是否启用模态感知排序
    modality_boost_factor: float = 2.0  # 模态匹配结果的权重提升系数

    # ============ V2.0 Phase 7: OpenTelemetry 分布式追踪配置 ============
    # 环境类型
    environment: str = "development"
    # OTLP Collector 端点（生产环境配置）
    # Jaeger: http://jaeger:14268/api/v2/spans
    # Tempo: http://tempo:3200/api/traces
    # Grafana Tempo: https://<grafana-domain>/tempo/api/traces
    otlp_endpoint: str = ""
    # 是否导出到控制台（仅开发调试用）
    otel_console_export: bool = False

    # ============ Docker 动态挂载配置 ============
    # 是否启用 Docker 动态挂载功能
    docker_dynamic_mount_enabled: bool = True
    # Docker 重启超时时间（秒）
    docker_restart_timeout: int = 30
    # 安全限制：允许的路径前缀（逗号分隔），空则允许所有路径
    # 例如: "C:/Users/,/data/" 仅允许挂载这些前缀下的目录
    docker_allowed_path_prefixes: str = ""
    # 默认容器名称
    docker_backend_container_name: str = "enterprise_rag_backend"
    docker_worker_container_name: str = "enterprise_rag_worker"

    model_config = SettingsConfigDict(
        env_file=str(_DOTENV_PATH) if _DOTENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()
