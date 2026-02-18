"""
Custom exceptions and global exception handlers.

Author: C2
Date: 2026-02-13
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        code: int = 5000,
        message: str = "服务器内部错误",
        detail: str | None = None,
        status_code: int = 500,
    ):
        self.code = code
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found exception."""

    def __init__(self, detail: str = "资源不存在"):
        super().__init__(code=4040, message="资源不存在", detail=detail, status_code=404)


class ValidationError(AppException):
    """Validation error exception."""

    def __init__(self, detail: str = "参数错误"):
        super().__init__(code=1001, message="参数错误", detail=detail, status_code=400)


class AuthenticationError(AppException):
    """Authentication error exception."""

    def __init__(self, detail: str = "认证失败"):
        super().__init__(code=1002, message="认证失败", detail=detail, status_code=401)


class LlmError(AppException):
    """LLM service error exception."""

    def __init__(self, detail: str = "LLM 调用失败"):
        super().__init__(code=4001, message="LLM 调用失败", detail=detail, status_code=503)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        import logging

        logger = logging.getLogger("enterprise_rag")
        logger.exception(f"Unexpected error: {exc}")
        # 同时写入 operation.log 便于与前端日志一起查阅
        try:
            from app.core.logging import get_operation_logger
            op_log = get_operation_logger()
            op_log.error(
                "server_exception",
                extra={"path": request.url.path, "method": request.method, "error": str(exc)},
                exc_info=True,
            )
        except Exception:  # noqa: S110
            pass

        return JSONResponse(
            status_code=500,
            content={
                "code": 5000,
                "message": "服务器内部错误",
                "detail": str(exc) if str(exc) else None,
            },
        )
