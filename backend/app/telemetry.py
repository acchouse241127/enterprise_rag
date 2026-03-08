"""
OpenTelemetry distributed tracing configuration for the RAG application.

This module sets up distributed tracing with OpenTelemetry for:
- HTTP request tracing (FastAPI)
- Database query tracing (SQL)
- Redis operation tracing
- Celery task tracing
"""

import asyncio
import logging
import os
from functools import wraps
from typing import Callable, Any, Optional
from contextlib import contextmanager

# Make OpenTelemetry imports optional to allow backend to start
# even if telemetry packages are not installed
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry import baggage
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logging.warning("OpenTelemetry packages not installed. Telemetry will be disabled.")

from app.config import settings


# Service configuration
SERVICE_NAME = "enterprise-rag"
SERVICE_VERSION = "2.0.0"


def setup_telemetry(
    service_name: str = SERVICE_NAME,
    service_version: str = SERVICE_VERSION,
    environment: str = "production",
    otlp_endpoint: Optional[str] = None,
    console_export: bool = False,
) -> Optional[TracerProvider]:
    """
    Initialize and configure OpenTelemetry for distributed tracing.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        environment: Environment (dev/staging/production)
        otlp_endpoint: Optional OTLP collector endpoint
        console_export: Whether to export spans to console (for debugging)

    Returns:
        Configured TracerProvider or None if OpenTelemetry is not available
    """
    if not OTEL_AVAILABLE:
        logging.warning("OpenTelemetry is not available. Telemetry is disabled.")
        return None

    # Create resource with service metadata
    resource = Resource.create(
        attributes={
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": environment,
            "host.name": os.uname().nodename if hasattr(os, "uname") else "unknown",
        }
    )

    # Choose exporter based on configuration
    if otlp_endpoint:
        # Production: export to OTLP collector (Jaeger/Tempo/Observability)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        logging.info(f"Using OTLP exporter: {otlp_endpoint}")
    elif console_export:
        # Development: export to console
        exporter = ConsoleSpanExporter()
        logging.info("Using Console exporter for telemetry")
    else:
        # No export - just use a dummy processor that discards spans
        exporter = None
        logging.warning("No exporter configured, spans will be discarded")

    # Configure tracer provider
    provider = TracerProvider(resource=resource)
    if exporter:
        processor = SimpleSpanProcessor(exporter)
        provider.add_span_processor(processor)
        logging.info(f"Added span processor: {type(processor).__name__}")
    else:
        logging.warning("No exporter, skipping span processor")

    # Set global tracer
    from opentelemetry.trace import set_tracer_provider
    set_tracer_provider(provider)

    logging.info(f"Telemetry initialized: service={service_name}, environment={environment}")

    return provider


def get_tracer(name: str = __name__) -> Any:
    """
    Get a tracer with the given name.

    Args:
        name: Name for the tracer (typically __name__)

    Returns:
        Tracer instance or None if OpenTelemetry is not available
    """
    if not OTEL_AVAILABLE:
        return None
    return trace.get_tracer(name)


def instrument_fastapi(app: Any) -> None:
    """
    Instrument FastAPI application with OpenTelemetry.

    Args:
        app: FastAPI application instance
    """
    if not OTEL_AVAILABLE:
        logging.warning("OpenTelemetry not available, skipping FastAPI instrumentation")
        return

    # Get the global tracer provider (must be set by initialize_telemetry first)
    from opentelemetry.trace import get_tracer_provider
    tracer_provider = get_tracer_provider()
    if not tracer_provider:
        logging.error("No tracer provider found. Call initialize_telemetry() before instrument_fastapi()")
        return

    instrumentor = FastAPIInstrumentor(tracer_provider=tracer_provider)
    instrumentor.instrument_app(app)
    logging.info("FastAPI instrumented with OpenTelemetry")


def instrument_httpx() -> None:
    """
    Instrument httpx client for HTTP request tracing.
    """
    if not OTEL_AVAILABLE:
        return
    instrumentor = HTTPXClientInstrumentor()
    instrumentor.instrument()


def instrument_sqlalchemy() -> None:
    """
    Instrument SQLAlchemy for database query tracing.
    """
    if not OTEL_AVAILABLE:
        return
    instrumentor = SQLAlchemyInstrumentor()
    instrumentor.instrument()


def instrument_celery() -> None:
    """
    Instrument Celery for background task tracing.
    """
    if not OTEL_AVAILABLE:
        return
    instrumentor = CeleryInstrumentor()
    instrumentor.instrument()


def instrument_redis() -> None:
    """
    Instrument Redis for cache operation tracing.
    """
    if not OTEL_AVAILABLE:
        return
    instrumentor = RedisInstrumentor()
    instrumentor.instrument()


def trace_with_baggage(baggage: dict[str, str]) -> contextmanager:
    """
    Create a span with baggage (correlation context).

    Baggage allows propagating context across distributed systems.
    Common baggage keys:
    - user_id: User identifier
    - session_id: Request session identifier
    - trace_id: Trace identifier
    - tenant_id: Multi-tenant identifier

    Args:
        baggage: Dictionary of baggage items

    Yields:
        Context with baggage set
    """
    if not OTEL_AVAILABLE:
        @contextmanager
        def _noop():
            yield
        return _noop()

    @contextmanager
    def _context():
        ctx = baggage.set_baggage(baggage)
        try:
            yield ctx
        finally:
            baggage.clear()
    return _context()


def with_tracer(name: str = __name__) -> Callable:
    """
    Decorator to automatically trace function execution.

    Args:
        name: Name for the span (defaults to function name)

    Example:
        @with_tracer("process_query")
        async def process_query(query: str):
            # Span is automatically created
            return await process(query)
    """
    if not OTEL_AVAILABLE:
        # If OTEL is not available, just return the function as-is
        def decorator(func: Callable) -> Callable:
            return func
        return decorator

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer(name)
            with tracer.start_as_current_span(func.__name__):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Error in {func.__name__}: {e}")
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer(name)
            with tracer.start_as_current_span(func.__name__):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Error in {func.__name__}: {e}")
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def setup_production_telemetry() -> Optional[TracerProvider]:
    """
    Set up telemetry for production environment.
    """
    # In production, export to OTLP collector
    otlp_endpoint = os.getenv("OTLP_ENDPOINT")
    if otlp_endpoint:
        return setup_telemetry(
            environment="production",
            otlp_endpoint=otlp_endpoint,
        )
    else:
        # Fallback to console export if no collector configured
        return setup_telemetry(
            environment="production",
            console_export=True,
        )

def setup_development_telemetry() -> Optional[TracerProvider]:
    """
    Set up telemetry for development environment.
    Uses console export by default.
    """
    return setup_telemetry(
        environment="development",
        console_export=True,
        otlp_endpoint=None,  # Always use console export in dev
    )


def initialize_telemetry() -> Optional[TracerProvider]:
    """
    Initialize telemetry based on environment.

    This function should be called at application startup.
    """
    env = settings.environment if hasattr(settings, "environment") else "development"
    otlp_endpoint = settings.otlp_endpoint if hasattr(settings, "otlp_endpoint") else None
    console_export = settings.otel_console_export if hasattr(settings, "otel_console_export") else False

    if env == "production" or (otlp_endpoint and not console_export):
        # Production: use OTLP if configured, otherwise console
        if otlp_endpoint:
            return setup_telemetry(
                environment=env,
                otlp_endpoint=otlp_endpoint,
                console_export=False,
            )
        else:
            return setup_telemetry(
                environment=env,
                console_export=True,
            )
    else:
        # Development: use console export by default
        return setup_telemetry(
            environment=env,
            console_export=True,
            otlp_endpoint=None,
        )
