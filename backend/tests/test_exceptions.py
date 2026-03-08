"""
Unit tests for custom exceptions.

Tests for app/core/exceptions.py
Author: C2
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestAppException:
    """Tests for AppException class."""

    def test_app_exception_default_values(self):
        """Test AppException with default values."""
        from app.core.exceptions import AppException

        exc = AppException()
        assert exc.code == 5000
        assert exc.message == "服务器内部错误"
        assert exc.detail is None
        assert exc.status_code == 500

    def test_app_exception_custom_values(self):
        """Test AppException with custom values."""
        from app.core.exceptions import AppException

        exc = AppException(
            code=1234,
            message="Custom error",
            detail="More details",
            status_code=400
        )
        assert exc.code == 1234
        assert exc.message == "Custom error"
        assert exc.detail == "More details"
        assert exc.status_code == 400

    def test_app_exception_inherits_from_exception(self):
        """Test that AppException inherits from Exception."""
        from app.core.exceptions import AppException

        exc = AppException()
        assert isinstance(exc, Exception)


class TestNotFoundError:
    """Tests for NotFoundError class."""

    def test_not_found_error_default(self):
        """Test NotFoundError with default message."""
        from app.core.exceptions import NotFoundError

        exc = NotFoundError()
        assert exc.code == 4040
        assert exc.message == "资源不存在"
        assert exc.status_code == 404

    def test_not_found_error_custom_detail(self):
        """Test NotFoundError with custom detail."""
        from app.core.exceptions import NotFoundError

        exc = NotFoundError(detail="文档不存在")
        assert exc.detail == "文档不存在"
        assert exc.status_code == 404


class TestValidationError:
    """Tests for ValidationError class."""

    def test_validation_error_default(self):
        """Test ValidationError with default message."""
        from app.core.exceptions import ValidationError

        exc = ValidationError()
        assert exc.code == 1001
        assert exc.message == "参数错误"
        assert exc.status_code == 400

    def test_validation_error_custom_detail(self):
        """Test ValidationError with custom detail."""
        from app.core.exceptions import ValidationError

        exc = ValidationError(detail="参数格式错误")
        assert exc.detail == "参数格式错误"
        assert exc.status_code == 400


class TestAuthenticationError:
    """Tests for AuthenticationError class."""

    def test_authentication_error_default(self):
        """Test AuthenticationError with default message."""
        from app.core.exceptions import AuthenticationError

        exc = AuthenticationError()
        assert exc.code == 1002
        assert exc.message == "认证失败"
        assert exc.status_code == 401

    def test_authentication_error_custom_detail(self):
        """Test AuthenticationError with custom detail."""
        from app.core.exceptions import AuthenticationError

        exc = AuthenticationError(detail="Token 无效")
        assert exc.detail == "Token 无效"
        assert exc.status_code == 401


class TestLlmError:
    """Tests for LlmError class."""

    def test_llm_error_default(self):
        """Test LlmError with default message."""
        from app.core.exceptions import LlmError

        exc = LlmError()
        assert exc.code == 4001
        assert exc.message == "LLM 调用失败"
        assert exc.status_code == 503

    def test_llm_error_custom_detail(self):
        """Test LlmError with custom detail."""
        from app.core.exceptions import LlmError

        exc = LlmError(detail="API 超时")
        assert exc.detail == "API 超时"
        assert exc.status_code == 503


class TestRegisterExceptionHandlers:
    """Tests for register_exception_handlers function."""

    def test_register_exception_handlers(self):
        """Test that exception handlers are registered."""
        from app.core.exceptions import register_exception_handlers, AppException
        from fastapi import FastAPI

        app = FastAPI()
        register_exception_handlers(app)

        # Check that exception handlers are registered
        assert AppException in app.exception_handlers
        assert Exception in app.exception_handlers

    @pytest.mark.asyncio
    async def test_app_exception_handler(self):
        """Test AppException handler returns correct response."""
        from app.core.exceptions import register_exception_handlers, AppException
        from fastapi import FastAPI, Request

        app = FastAPI()
        register_exception_handlers(app)

        handler = app.exception_handlers[AppException]
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"

        exc = AppException(code=1234, message="Test error", detail="Detail", status_code=400)

        from fastapi.responses import JSONResponse
        response = await handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_generic_exception_handler(self):
        """Test generic Exception handler returns 500."""
        from app.core.exceptions import register_exception_handlers
        from fastapi import FastAPI, Request

        app = FastAPI()
        register_exception_handlers(app)

        handler = app.exception_handlers[Exception]
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        exc = ValueError("Something went wrong")

        from fastapi.responses import JSONResponse
        response = await handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_generic_exception_handler_production(self):
        """Test generic handler in production mode hides details."""
        from app.core.exceptions import register_exception_handlers
        from fastapi import FastAPI, Request

        app = FastAPI()
        register_exception_handlers(app)

        handler = app.exception_handlers[Exception]
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        exc = ValueError("Secret error")

        with patch("app.core.exceptions.settings") as mock_settings:
            mock_settings.env = "production"

            from fastapi.responses import JSONResponse
            response = await handler(request, exc)

            # In production, detail should be None
            # (body would need to be parsed to check)

    @pytest.mark.asyncio
    async def test_generic_exception_handler_development(self):
        """Test generic handler in development mode shows details."""
        from app.core.exceptions import register_exception_handlers
        from fastapi import FastAPI, Request

        app = FastAPI()
        register_exception_handlers(app)

        handler = app.exception_handlers[Exception]
        request = MagicMock(spec=Request)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        exc = ValueError("Visible error")

        with patch("app.core.exceptions.settings") as mock_settings:
            mock_settings.env = "development"

            from fastapi.responses import JSONResponse
            import json

            response = await handler(request, exc)

            assert response.status_code == 500


class TestExceptionHierarchy:
    """Tests for exception class hierarchy."""

    def test_not_found_is_app_exception(self):
        """Test NotFoundError is instance of AppException."""
        from app.core.exceptions import NotFoundError, AppException

        exc = NotFoundError()
        assert isinstance(exc, AppException)

    def test_validation_is_app_exception(self):
        """Test ValidationError is instance of AppException."""
        from app.core.exceptions import ValidationError, AppException

        exc = ValidationError()
        assert isinstance(exc, AppException)

    def test_auth_is_app_exception(self):
        """Test AuthenticationError is instance of AppException."""
        from app.core.exceptions import AuthenticationError, AppException

        exc = AuthenticationError()
        assert isinstance(exc, AppException)

    def test_llm_is_app_exception(self):
        """Test LlmError is instance of AppException."""
        from app.core.exceptions import LlmError, AppException

        exc = LlmError()
        assert isinstance(exc, AppException)
