import contextvars
import json
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routes import router as otp_router
from app.schemas import HealthResponse
from app.service import rabbitmq_client

correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)


class JSONLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get()
            or getattr(record, "correlation_id", ""),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONLogFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        l = logging.getLogger(logger_name)
        l.handlers = [handler]
        l.propagate = False


configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing OTP Service...")
    await init_db()
    logger.info("Database initialized successfully.")
    try:
        await rabbitmq_client.connect()
    except Exception as e:
        logger.warning(f"RabbitMQ connection on startup failed: {e}")
    yield
    logger.info("Shutting down OTP Service...")
    await rabbitmq_client.close()
    logger.info("OTP Service shutdown completed.")


app = FastAPI(
    title="OTP Service",
    description="Microservice for generating and verifying OTP codes for iBanking Tuition Payment system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation ID Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    token = correlation_id_ctx.set(correlation_id)
    start_time = time.time()
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Correlation-ID"] = correlation_id
        logger.info(
            f"{request.method} {request.url.path} responded {response.status_code} in {duration_ms:.2f}ms"
        )
        return response
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"{request.method} {request.url.path} failed after {duration_ms:.2f}ms: {exc}",
            exc_info=True,
        )
        raise
    finally:
        correlation_id_ctx.reset(token)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
@app.get("/api/otp/health", response_model=HealthResponse, tags=["Health"], include_in_schema=False)
async def health_check():
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        database="connected",
        rabbitmq="connected" if rabbitmq_client.is_connected() else "disconnected",
    )


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "docs": "/docs",
    }


# Include routes
app.include_router(otp_router)
