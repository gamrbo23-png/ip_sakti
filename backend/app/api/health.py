"""Health and readiness check endpoints."""
from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import get_settings
from app.database import check_database_health

router = APIRouter()
settings = get_settings()
_START_TIME = time.time()


@router.get("/health", summary="Liveness check")
async def health() -> dict:
    """Returns 200 if the server is running."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - _START_TIME, 2),
    }


@router.get("/ready", summary="Readiness check")
async def ready() -> dict:
    """Returns 200 only when all dependencies are healthy."""
    db_health = await check_database_health()

    # Check embedding service availability
    embedding_status = "unknown"
    try:
        from app.services.embedding_service import get_embedding_service
        svc = get_embedding_service()
        embedding_status = "ready" if svc.is_ready() else "loading"
    except Exception:
        embedding_status = "unavailable"

    all_healthy = db_health["status"] == "healthy"

    return {
        "status": "ready" if all_healthy else "not_ready",
        "components": {
            "database": db_health,
            "embedding_service": embedding_status,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
