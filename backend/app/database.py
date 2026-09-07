"""
IP-SAKTI Sahayak — Database Engine & Session
Async SQLAlchemy with connection pooling and pgvector support.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


# ── Engine ────────────────────────────────────────────────────────────────────
is_sqlite = "sqlite" in settings.database_url

engine_kwargs = {
    "echo": settings.debug,
}
if not is_sqlite:
    engine_kwargs.update({
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_timeout": settings.database_pool_timeout,
        "pool_pre_ping": True,
    })

engine = create_async_engine(settings.database_url, **engine_kwargs)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for use outside FastAPI (e.g., scripts)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health() -> dict:
    """Run a quick health check against the database."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            pgvector_installed = False
            if not is_sqlite:
                try:
                    ext_result = await session.execute(
                        text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                    )
                    pgvector_installed = ext_result.scalar() is not None
                except Exception:
                    pgvector_installed = False
            return {
                "status": "healthy",
                "database_type": "sqlite" if is_sqlite else "postgresql",
                "pgvector": pgvector_installed,
            }
    except Exception as exc:
        logger.error("Database health check failed", error=str(exc))
        return {"status": "unhealthy", "error": str(exc)}


async def init_extensions() -> None:
    """Ensure database tables and extensions are initialized."""
    async with engine.begin() as conn:
        if not is_sqlite:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
                logger.info("PostgreSQL extensions initialized (vector, pg_trgm)")
            except Exception as exc:
                logger.warning("Could not initialize pgvector extension", error=str(exc))
        
        # Ensure tables exist
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified")

