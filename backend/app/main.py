"""
IP-SAKTI Sahayak — FastAPI Application Entry Point
Initializes the app, middleware, lifespan, and routes.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import check_database_health, init_extensions
from app.logging_config import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    logger.info("Starting IP-SAKTI Sahayak backend", env=settings.app_env)

    # Initialize pgvector and pg_trgm extensions
    await init_extensions()
    logger.info("Database extensions ready")

    # Warm up embedding model lazily (imported here to avoid circular deps)
    try:
        from app.services.embedding_service import get_embedding_service
        emb = get_embedding_service()
        logger.info("Embedding service ready", model=settings.embedding_model_name)
    except Exception as exc:
        logger.warning("Embedding service not available at startup", error=str(exc))

    yield  # Application runs here

    logger.info("Shutting down IP-SAKTI Sahayak")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="IP-SAKTI Sahayak API",
    description=(
        "Multilingual RAG-based IP & Regulatory Guidance Assistant for India. "
        "Provides citation-first answers grounded in authoritative government sources."
    ),
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Add X-Process-Time header to every response."""
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000, 2)
    response.headers["X-Process-Time"] = f"{duration_ms}ms"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Structured request logging."""
    logger.info(
        "Request",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )
    response = await call_next(request)
    logger.info(
        "Response",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
    )
    return response


# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": request.url.path},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error("Internal server error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error. Please try again later."},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
from app.api import health, chat, search, sources, feedback, admin, documents

app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(sources.router, prefix="/api", tags=["Sources"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
