"""
前端操作日志：与后端共用 enterprise_rag/logs/operation.log，记录所有请求/响应细节。
"""

import logging
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# 与 backend 一致的日志文件路径：frontend/operation_log.py -> parents[1] = enterprise_rag
_OPERATION_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "operation.log"
_OPERATION_LOGGER_NAME = "frontend_operation"
_setup_done = False
_session: requests.Session | None = None


def _operation_log_formatter(record: logging.LogRecord) -> str:
    ts = record.created
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    level = record.levelname
    msg = record.getMessage()
    extra = []
    for k, v in record.__dict__.items():
        if k in (
            "name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno",
            "lineno", "module", "msecs", "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName", "message", "taskName",
        ):
            continue
        if v is None or v == "":
            continue
        s = repr(v) if not isinstance(v, str) else v
        if len(s) > 500:
            s = s[:500] + "..."
        extra.append(f"{k}={s}")
    extra_str = " | ".join(extra) if extra else ""
    line = f"[{dt}] [FRONTEND] [{level}] {msg}"
    if extra_str:
        line += " | " + extra_str
    if record.exc_info:
        line += "\n" + logging.Formatter().formatException(record.exc_info)
    return line


def setup_operation_log() -> None:
    """将前端操作日志写入与后端共用的 operation.log。"""
    global _setup_done
    if _setup_done:
        return
    _setup_done = True
    _OPERATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(_OPERATION_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    if not any(
        getattr(h, "baseFilename", None) == str(_OPERATION_LOG_PATH)
        for h in logger.handlers
    ):
        class _OpFormatter(logging.Formatter):
            def format(self, record):
                return _operation_log_formatter(record)

        handler = logging.FileHandler(_OPERATION_LOG_PATH, mode="a", encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(_OpFormatter())
        logger.addHandler(handler)
    logger.propagate = False


def _get_op_logger() -> logging.Logger:
    setup_operation_log()
    return logging.getLogger(_OPERATION_LOGGER_NAME)


def _get_http_session() -> requests.Session:
    """Shared HTTP session with connection pooling and retry."""
    global _session
    if _session is not None:
        return _session
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]),
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    _session = session
    return session


def _infer_operation(url: str, method: str) -> str:
    """从 URL 和 method 推断操作名，便于查阅。"""
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        path = (p.path or "").strip("/")
        if p.path and "/api/" in (url or ""):
            # 去掉 /api 前缀
            path = path.replace("api/", "", 1) if path.startswith("api/") else path
        if not path:
            return f"{method.lower()}_unknown"
        op = path.replace("/", ".")
        return f"{method.lower()}.{op}"
    except Exception:
        return f"{method.lower()}_request"


def logged_request(method: str, url: str, operation_name: str | None = None, **kwargs) -> requests.Response:
    """发请求并记录到 operation.log（方法、URL、状态码、耗时、成功/失败、错误信息）。"""
    op_log = _get_op_logger()
    op = operation_name or _infer_operation(url, method)
    start = time.perf_counter()
    try:
        session = _get_http_session()
        resp = session.request(method, url, **kwargs)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        # 流式响应不读 content，避免拉取整个 body
        size = None
        if not kwargs.get("stream") and resp.content is not None:
            size = len(resp.content)
        success = 200 <= resp.status_code < 400
        op_log.info(
            "request_finished",
            extra={
                "operation": op,
                "method": method,
                "url": url,
                "status_code": resp.status_code,
                "duration_ms": duration_ms,
                "response_size": size,
                "success": success,
            },
        )
        return resp
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        op_log.error(
            "request_failed",
            extra={
                "operation": op,
                "method": method,
                "url": url,
                "duration_ms": duration_ms,
                "error": str(exc),
            },
            exc_info=True,
        )
        raise


def logged_get(url: str, operation_name: str | None = None, **kwargs) -> requests.Response:
    return logged_request("GET", url, operation_name=operation_name, **kwargs)


def logged_post(url: str, operation_name: str | None = None, **kwargs) -> requests.Response:
    return logged_request("POST", url, operation_name=operation_name, **kwargs)


def logged_put(url: str, operation_name: str | None = None, **kwargs) -> requests.Response:
    return logged_request("PUT", url, operation_name=operation_name, **kwargs)


def logged_delete(url: str, operation_name: str | None = None, **kwargs) -> requests.Response:
    return logged_request("DELETE", url, operation_name=operation_name, **kwargs)
