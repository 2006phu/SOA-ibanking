import json
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes import router as users_router

# Context variable to hold correlation_id per request context
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


class StructuredJSONFormatter(logging.Formatter):
    """Structured JSON formatter with correlation_id support."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": settings.SERVICE_NAME,
            "correlation_id": correlation_id_ctx.get(""),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJSONFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)


setup_logging()
logger = logging.getLogger("user-service.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database and creating tables if not present...")
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Application shutdown completed.")


app = FastAPI(
    title="User Service",
    description="User Profile & Balance Management Microservice for iBanking Tuition Payment",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next: Callable) -> Response:
    corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    token = correlation_id_ctx.set(corr_id)
    start_time = time.perf_counter()

    try:
        response: Response = await call_next(request)
        duration = time.perf_counter() - start_time
        response.headers["X-Correlation-ID"] = corr_id
        response.headers["X-Process-Time"] = f"{duration:.4f}s"
        logger.info(
            f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.4f}s"
        )
        return response
    except Exception as exc:
        duration = time.perf_counter() - start_time
        logger.error(
            f"{request.method} {request.url.path} failed after {duration:.4f}s: {str(exc)}",
            exc_info=True,
        )
        raise exc
    finally:
        correlation_id_ctx.reset(token)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
    }


app.include_router(users_router)
