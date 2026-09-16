import json
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, Dict

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import async_session, init_db
from app.routes import router as tuition_router
from app.service import seed_initial_data

# Correlation ID context variable
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


class StructuredJSONFormatter(logging.Formatter):
    """Custom logging formatter outputting structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": settings.SERVICE_NAME,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get()
            or getattr(record, "correlation_id", None)
            or "",
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_structured_logging():
    """Configure root logger to use structured JSON output."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.handlers = [handler]

    # Reduce noisy loggers if needed
    logging.getLogger("uvicorn.access").handlers = [handler]


setup_structured_logging()
logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to propagate or generate X-Correlation-ID for each request."""

    async def dispatch(self, request: Request, call_next):
        corr_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )
        token = correlation_id_ctx.set(corr_id)
        start_time = time.perf_counter()

        try:
            response: Response = await call_next(request)
            process_time = time.perf_counter() - start_time
            response.headers["X-Correlation-ID"] = corr_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}s"

            logger.info(
                f"{request.method} {request.url.path} responded with {response.status_code} in {process_time:.4f}s"
            )
            return response
        except Exception as exc:
            process_time = time.perf_counter() - start_time
            logger.error(
                f"Unhandled error processing {request.method} {request.url.path}: {exc}",
                exc_info=True,
            )
            raise
        finally:
            correlation_id_ctx.reset(token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager: initialize DB tables and seed sample data."""
    logger.info("Initializing database tables for Tuition Service...")
    await init_db()
    logger.info("Database tables initialized successfully.")

    # Seed initial data if tables are empty
    try:
        async with async_session() as session:
            try:
                await seed_initial_data(session)
                await session.commit()
            except Exception as e:
                logger.warning(f"Failed to seed initial data: {e}")
                await session.rollback()
    except Exception as e:
        logger.warning(f"Could not connect to database for initial seed: {e}")

    yield

    logger.info("Tuition Service is shutting down...")


app = FastAPI(
    title="Tuition Service",
    description="Tuition lookup and payment management service for iBanking system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# Include routes
app.include_router(tuition_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler returning standard JSON response for unexpected errors."""
    if isinstance(exc, (StarletteHTTPException, RequestValidationError)):
        raise exc

    corr_id = correlation_id_ctx.get() or ""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "correlation_id": corr_id,
        },
        headers={"X-Correlation-ID": corr_id},
    )

