import uuid
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, init_db
from app.logger import get_correlation_id, set_correlation_id, setup_logging
from app.rabbitmq import rabbitmq_client
from app.routes import router as payment_router
from app.schemas import HealthCheckResponse

setup_logging()
logger = logging.getLogger("payment-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown routines."""
    logger.info("Initializing Payment Service database schema...")
    await init_db()
    logger.info("Connecting to RabbitMQ...")
    await rabbitmq_client.connect(settings.RABBITMQ_URL)
    yield
    logger.info("Shutting down Payment Service resources...")
    await rabbitmq_client.close()
    await engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Payment Service",
    description="Microservice responsible for orchestrating tuition payment transactions using the Saga pattern.",
    version="1.0.0",
    lifespan=lifespan,
)

# Correlation ID Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    set_correlation_id(correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# CORS Middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Endpoint
@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for container health probes."""
    return HealthCheckResponse(status="healthy", service="payment-service")


# Include Service Routers
app.include_router(payment_router)
