import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.auth import AuthMiddleware
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.tuition import router as tuition_router
from app.routes.payments import router as payments_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("iBanking API Gateway is starting up on port 8000...")
    yield
    logger.info("iBanking API Gateway has shut down.")


app = FastAPI(
    title="iBanking API Gateway",
    description="Central API Gateway with JWT Authentication and Distributed Tracing for iBanking Tuition Payment System",
    version="1.0.0",
    lifespan=lifespan,
)

# 1. CORS Middleware (outermost, handles preflight and sets headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Correlation ID Middleware (generates/attaches X-Correlation-ID)
app.add_middleware(CorrelationIdMiddleware)

# 3. Structured JSON Logging Middleware
app.add_middleware(LoggingMiddleware)

# 4. JWT Authentication Middleware
app.add_middleware(AuthMiddleware)

# Include Route Modules
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(tuition_router, prefix="/api/tuition", tags=["Tuition"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container health probes and monitoring."""
    return {"status": "healthy", "service": "gateway"}


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint providing service status and documentation link."""
    return {
        "service": "iBanking API Gateway",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }
