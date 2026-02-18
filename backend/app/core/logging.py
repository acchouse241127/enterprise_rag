"""
Structured logging configuration.

Author: C2
Date: 2026-02-13
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


def _operation_log_file_path() -> Path:
    """Shared operation log file (backend + frontend 共用)."""
    # backend/app/core/logging.py -> parents[3] = enterprise_rag
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "logs" / "operation.log"


class OperationLogFormatter(logging.Formatter):
    """Formatter for operation.log: 单行详细，便于查阅与 grep。"""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record.levelname
        msg = record.getMessage()
        # 把所有 extra 打成 key=value
        extra = []
        for k, v in record.__dict__.items():
            if k in ("name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "pathname", "process", "processName", "relativeCreated", "stack_info", "exc_info", "exc_text", "thread", "threadName", "message", "taskName"):
                continue
            if v is None or v == "":
                continue
            extra.append(f"{k}={_safe_repr(v)}")
        extra_str = " | ".join(extra) if extra else ""
        line = f"[{ts}] [BACKEND] [{level}] {msg}"
        if extra_str:
            line += " | " + extra_str
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def _safe_repr(v, max_len: int = 500) -> str:
    s = repr(v) if not isinstance(v, str) else v
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging output."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record.levelname
        name = record.name
        message = record.getMessage()

        # Add extra context if available
        extra_parts = []
        if hasattr(record, "request_id"):
            extra_parts.append(f"request_id={record.request_id}")
        if hasattr(record, "user"):
            extra_parts.append(f"user={record.user}")
        if hasattr(record, "duration_ms"):
            extra_parts.append(f"duration_ms={record.duration_ms}")

        extra_str = " ".join(extra_parts)
        if extra_str:
            return f"[{timestamp}] [{level}] [{name}] {message} | {extra_str}"
        return f"[{timestamp}] [{level}] [{name}] {message}"


def setup_logging(level: str = "INFO") -> None:
    """
    Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with structured format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # Application logger
    app_logger = logging.getLogger("enterprise_rag")
    app_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


def get_logger(name: str = "enterprise_rag") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


OPERATION_LOG_PATH = _operation_log_file_path()
OPERATION_LOGGER_NAME = "operation"


def setup_operation_log_file() -> None:
    """将操作日志写入与前端共用的 operation.log 文件。"""
    log_path = _operation_log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    op_logger = logging.getLogger(OPERATION_LOGGER_NAME)
    op_logger.setLevel(logging.DEBUG)
    # 避免重复添加 handler（例如测试或重载时）
    if not any(h for h in op_logger.handlers if getattr(h, "baseFilename", None) == str(log_path)):
        fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(OperationLogFormatter())
        op_logger.addHandler(fh)
    op_logger.propagate = False


def get_operation_logger() -> logging.Logger:
    """获取用于写入 operation.log 的 logger（请求/业务操作详情）。"""
    return logging.getLogger(OPERATION_LOGGER_NAME)
