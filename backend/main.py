"""
FastAPI application entrypoint.

Author: C2
Date: 2026-02-13
Updated: 2026-02-14 (Phase 3.3 Async Tasks, Prometheus, Conversations, KB Edit)
"""

import platform
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api import api_router
from app.config import settings
from app.core.limiter import limiter
from app.core import (
    get_operation_logger,
    register_exception_handlers,
    setup_logging,
    setup_operation_log_file,
)
from app.telemetry import (
    initialize_telemetry,
    instrument_fastapi,
)
from app.core.database import Base, engine, SessionLocal
from sqlalchemy import text
from app.models import Document, KnowledgeBase, User, UserKnowledgeBasePermission  # noqa: F401
from app.models import FolderSyncConfig, FolderSyncLog, RetrievalLog, RetrievalFeedback  # noqa: F401 Phase 3.2
from app.models import AsyncTask, Conversation, ConversationMessage  # noqa: F401 Phase 3.3
from app import metrics as prom_metrics  # Phase 3.3 Prometheus

# 应用启动时间（用于健康检查）
APP_START_TIME = datetime.now()


class OperationLogMiddleware(BaseHTTPMiddleware):
    """记录每条请求/响应的详细操作日志到 operation.log（与前端共用文件）。"""

    async def dispatch(self, request: Request, call_next):
        op_log = get_operation_logger()
        start = time.perf_counter()
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        client = request.client.host if request.client else ""
        # 请求体大小（仅对非流式读取）
        try:
            body_size = getattr(request.state, "_body_size", None)
        except Exception:
            body_size = None
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status = response.status_code
            # 响应体大小（streaming 时可能不可用）
            try:
                resp_body = getattr(response, "body", b"")
                resp_size = len(resp_body) if resp_body else None
            except Exception:
                resp_size = None
            op_log.info(
                "request_finished",
                extra={
                    "method": method,
                    "path": path,
                    "query": query or "(none)",
                    "client": client,
                    "status_code": status,
                    "duration_ms": duration_ms,
                    "request_body_size": body_size,
                    "response_body_size": resp_size,
                    "success": 200 <= status < 400,
                },
            )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            op_log.error(
                "request_failed",
                extra={
                    "method": method,
                    "path": path,
                    "query": query or "(none)",
                    "client": client,
                    "duration_ms": duration_ms,
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise


def _migrate_users_role_column() -> None:
    """Add users.role column if missing (Phase 2.3 RBAC schema upgrade)."""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'viewer'
        """))
        conn.execute(text("""
            UPDATE users SET role = 'admin' WHERE is_admin = true AND role <> 'admin'
        """))
        conn.commit()


def _migrate_knowledge_bases_chunk_columns() -> None:
    """Add knowledge_bases.chunk_size/chunk_overlap if missing (Phase 3.3)."""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE knowledge_bases
            ADD COLUMN IF NOT EXISTS chunk_size INTEGER NULL
        """))
        conn.execute(text("""
            ALTER TABLE knowledge_bases
            ADD COLUMN IF NOT EXISTS chunk_overlap INTEGER NULL
        """))
        conn.commit()


def _migrate_documents_source_url() -> None:
    """Add documents.source_url if missing (reshaping URL docs)."""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE documents
            ADD COLUMN IF NOT EXISTS source_url VARCHAR(2000) NULL
        """))
        conn.commit()


def _migrate_tenant_columns() -> None:
    """Add tenant_id to knowledge_bases and users for ToB plan three."""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE knowledge_bases
            ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64) NULL
        """))
        conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64) NULL
        """))
        conn.commit()


def _migrate_v2_chunks_and_kb() -> None:
    """V2.0 B1-2/B1-3: chunks 表、tsv 触发器、knowledge_bases 扩展。
       V2.0 B2-quality: retrieval_feedbacks 和 retrieval_logs 质量指标扩展。
    """
    migrations_dir = Path(__file__).resolve().parent / "migrations"
    order = [
        "V2.0_001_add_pg_jieba_extension.sql",
        "V2.0_002_create_chunks_table.sql",
        "V2.0_003_create_chunks_tsv_trigger.sql",
        "V2.0_005_alter_knowledge_bases.sql",
        "V2.0_004_alter_retrieval_feedbacks.sql",  # B2: feedback rating/reason
        "V2.0_006_alter_retrieval_logs.sql",     # B2: quality metrics + refusal
        "V2.0_009_add_kb_default_strategy.sql",  # V2.0: KB default retrieval strategy
    ]
    with engine.connect() as conn:
        for name in order:
            path = migrations_dir / name
            if not path.exists():
                continue
            sql = path.read_text(encoding="utf-8").strip()
            if not sql:
                continue
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception as e:
                conn.rollback()
                get_operation_logger().warning("V2.0 migrate %s: %s", name, e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    setup_logging(level=settings.log_level, json_format=settings.log_json_format)
    setup_operation_log_file()
    Base.metadata.create_all(bind=engine)

    # Initialize distributed tracing (OpenTelemetry)
    get_operation_logger().info("Initializing OpenTelemetry tracing...")
    initialize_telemetry()
    get_operation_logger().info("OpenTelemetry tracing initialized")

    # Instrument FastAPI for distributed tracing
    instrument_fastapi(app)
    for name, migrate in [
        ("users.role", _migrate_users_role_column),
        ("knowledge_bases.chunk_*", _migrate_knowledge_bases_chunk_columns),
        ("documents.source_url", _migrate_documents_source_url),
        ("tenant_id", _migrate_tenant_columns),
        ("V2.0 chunks+kb", _migrate_v2_chunks_and_kb),
    ]:
        try:
            migrate()
        except Exception as e:
            get_operation_logger().warning("migrate %s skipped: %s", name, e)

    # 预热嵌入模型：在后台线程中加载，避免阻塞启动
    import threading
    def _warmup_embedding_model():
        try:
            get_operation_logger().info("开始预热嵌入模型: %s", settings.embedding_model_name)
            from app.rag import BgeM3EmbeddingService
            service = BgeM3EmbeddingService(
                model_name=settings.embedding_model_name,
                fallback_dim=settings.embedding_fallback_dim,
            )
            # 用一个简单的文本触发模型加载
            service.embed(["预热模型"])
            get_operation_logger().info("嵌入模型预热完成")
        except Exception as e:
            get_operation_logger().warning("嵌入模型预热失败（将使用 fallback）: %s", e)

    warmup_thread = threading.Thread(target=_warmup_embedding_model, daemon=True)
    warmup_thread.start()

    yield
    # Shutdown (cleanup if needed)


def create_app() -> FastAPI:
    """Create and configure FastAPI app instance."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        # Content Security Policy
        csp = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';"
        response.headers["Content-Security-Policy"] = csp
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions-Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

    # CORS：SPA 跨域（allow_origins 可配置，默认含 http://localhost:3000）
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API 速率限制（防滥用）：默认 200 次/分钟/IP，登录接口在 auth 中单独限制
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # 操作日志中间件：记录所有请求/响应详情到 operation.log
    app.add_middleware(OperationLogMiddleware)

    # Register global exception handlers
    register_exception_handlers(app)

    # Include API routers
    app.include_router(api_router, prefix=settings.api_prefix)

    # ========== Phase 2.3: 健康检查与监控端点 ==========
    @app.get("/health", tags=["monitoring"])
    def health_check():
        """
        健康检查接口 - 用于负载均衡器/容器编排探针。
        返回应用状态、运行时间、数据库连接状态等。
        """
        uptime_seconds = (datetime.now() - APP_START_TIME).total_seconds()
        
        # 检查数据库连接
        db_status = "healthy"
        db_error = None
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
        except Exception as e:
            db_status = "unhealthy"
            db_error = str(e)
        
        status = "healthy" if db_status == "healthy" else "degraded"
        
        return JSONResponse(
            status_code=200 if status == "healthy" else 503,
            content={
                "status": status,
                "version": settings.app_version,
                "uptime_seconds": round(uptime_seconds, 2),
                "timestamp": datetime.now().isoformat(),
                "checks": {
                    "database": {
                        "status": db_status,
                        "error": db_error,
                    },
                },
            },
        )

    @app.get("/health/live", tags=["monitoring"])
    def liveness_probe():
        """
        存活探针 - Kubernetes liveness probe。
        仅检查应用进程是否存活。
        """
        return {"status": "alive", "timestamp": datetime.now().isoformat()}

    @app.get("/health/ready", tags=["monitoring"])
    def readiness_probe():
        """
        就绪探针 - Kubernetes readiness probe。
        检查应用是否准备好接收流量。
        """
        # 检查数据库
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            db_ready = True
        except Exception:
            db_ready = False
        
        ready = db_ready
        return JSONResponse(
            status_code=200 if ready else 503,
            content={
                "status": "ready" if ready else "not_ready",
                "timestamp": datetime.now().isoformat(),
                "checks": {
                    "database": db_ready,
                },
            },
        )

    @app.get("/metrics", tags=["monitoring"])
    def metrics():
        """
        Prometheus 格式指标接口。
        Phase 3.3: 支持 Prometheus 抓取。
        """
        # 更新 Gauge 指标
        try:
            db = SessionLocal()
            kb_count = db.query(KnowledgeBase).count()
            db.close()
            prom_metrics.KNOWLEDGE_BASES_TOTAL.set(kb_count)
        except Exception:
            pass
        
        return Response(
            content=prom_metrics.get_metrics(),
            media_type=prom_metrics.get_content_type(),
        )

    @app.get("/metrics/json", tags=["monitoring"])
    def metrics_json():
        """
        JSON 格式指标接口 - 便于调试和非 Prometheus 场景。
        """
        uptime_seconds = (datetime.now() - APP_START_TIME).total_seconds()
        
        # 获取基础统计
        try:
            db = SessionLocal()
            kb_count = db.query(KnowledgeBase).count()
            doc_count = db.query(Document).count()
            user_count = db.query(User).count()
            db.close()
        except Exception:
            kb_count = doc_count = user_count = -1
        
        return {
            "app_info": {
                "name": settings.app_name,
                "version": settings.app_version,
                "python_version": platform.python_version(),
                "platform": platform.system(),
            },
            "uptime_seconds": round(uptime_seconds, 2),
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "knowledge_bases": kb_count,
                "documents": doc_count,
                "users": user_count,
            },
            "config": {
                "retrieval_top_k": settings.retrieval_top_k,
                "reranker_enabled": settings.reranker_enabled,
                "dedup_enabled": settings.dedup_enabled,
                "dynamic_threshold_enabled": settings.dynamic_threshold_enabled,
            },
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=(settings.env == "development"),
    )
