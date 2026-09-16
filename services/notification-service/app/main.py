import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.consumer import consumer
from app.logging_config import (
    CorrelationIdMiddleware,
    get_correlation_id,
    setup_logging,
)
from app.routes import router

# Initialize structured JSON logging
setup_logging()
logger = logging.getLogger("notification-service.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing RabbitMQ consumer worker."""
    logger.info("Starting Notification Service on port 8006...")

    # Start RabbitMQ consumer as a background task
    consumer_task = asyncio.create_task(consumer.start())
    logger.info("RabbitMQ consumer task initiated in background")

    try:
        yield
    finally:
        logger.info("Shutting down Notification Service...")
        await consumer.stop()
        if not consumer_task.done():
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
        logger.info("Notification Service shutdown complete")


app = FastAPI(
    title="Notification Service",
    description="iBanking Tuition Payment System - Notification Service (RabbitMQ Consumer)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID propagation middleware
app.add_middleware(CorrelationIdMiddleware)


# Exception handler for HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    correlation_id = get_correlation_id()
    logger.warning(
        f"HTTPException {exc.status_code}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "correlation_id": correlation_id
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "correlation_id": correlation_id
        }
    )


# Global unhandled exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = get_correlation_id()
    logger.error(
        f"Unhandled Server Error: {exc}",
        extra={
            "path": request.url.path,
            "correlation_id": correlation_id,
            "error": str(exc)
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "correlation_id": correlation_id
        }
    )


# Include API routes (includes GET /health and GET /)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=False
    )
