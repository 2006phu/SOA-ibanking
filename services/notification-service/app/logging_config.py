import contextvars
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Retrieve current correlation_id from context or generate an empty string."""
    return correlation_id_ctx.get() or ""


def set_correlation_id(correlation_id: str) -> contextvars.Token:
    """Set correlation_id in context."""
    return correlation_id_ctx.set(correlation_id)


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter with correlation_id and service metadata."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get() or getattr(record, "correlation_id", ""),
            "service": "notification-service",
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Append extra attributes passed to log calls
        standard_attrs = {
            "args", "asctime", "created", "exc_info", "exc_text", "filename",
            "funcName", "id", "levelname", "levelno", "lineno", "module",
            "msecs", "message", "msg", "name", "pathname", "process",
            "processName", "relativeCreated", "stack_info", "thread", "threadName"
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs and key not in log_data:
                try:
                    # Test JSON serializability
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, OverflowError):
                    log_data[key] = str(value)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging():
    """Configure root logger to use JSONFormatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if not any(isinstance(h.formatter, JSONFormatter) for h in root_logger.handlers):
        root_logger.handlers.clear()
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        root_logger.addHandler(handler)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to propagate or generate X-Correlation-ID for HTTP requests."""

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        token = set_correlation_id(correlation_id)
        try:
            response: Response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            correlation_id_ctx.reset(token)
