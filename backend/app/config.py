"""
IP-SAKTI Sahayak — Application Configuration
Reads from environment variables with sensible defaults.
All secrets MUST be set via environment or .env file.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Literal

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "IP-SAKTI Sahayak"
    app_env: Literal["development", "staging", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION"

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://ipsakti_user:password@localhost:5432/ipsakti"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30

    # ── LLM ───────────────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"
    llm_model_name: str = "gemini-3.1-flash-lite"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048
    llm_timeout_seconds: int = 60

    # ── Embeddings ────────────────────────────────────────────────────────────
    embedding_model_name: str = "BAAI/BGE-M3"
    embedding_dimension: int = 1024
    embedding_batch_size: int = 16
    embedding_device: str = "cpu"

    # ── Reranker ──────────────────────────────────────────────────────────────
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    reranker_device: str = "cpu"

    # ── Retrieval ─────────────────────────────────────────────────────────────
    vector_top_k: int = 20
    keyword_top_k: int = 20
    rerank_top_k: int = 8
    final_context_k: int = 5

    # ── Confidence thresholds ─────────────────────────────────────────────────
    high_evidence_threshold: float = 0.75
    moderate_evidence_threshold: float = 0.45

    # ── JWT Authentication ────────────────────────────────────────────────────
    jwt_secret_key: str = "CHANGE_THIS_JWT_SECRET"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"
    cors_allow_credentials: bool = True

    # ── Storage ───────────────────────────────────────────────────────────────
    storage_backend: Literal["local", "minio"] = "local"
    local_storage_path: str = "./data/raw"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "ipsakti-documents"
    minio_secure: bool = False

    # ── Document Processing ───────────────────────────────────────────────────
    max_upload_size_mb: int = 50
    allowed_file_types: str = "pdf,txt"
    ocr_language: str = "eng+hin+ben+tam+tel"
    ocr_dpi: int = 300

    # ── Ingestion ─────────────────────────────────────────────────────────────
    ingestion_concurrency: int = 4
    ingestion_retry_attempts: int = 3
    ingestion_retry_delay_seconds: int = 5

    # ── Admin ─────────────────────────────────────────────────────────────────
    admin_email: str = "admin@ipsakti.local"
    admin_password: str = "CHANGE_THIS_ADMIN_PASSWORD"

    # ── Evaluation ────────────────────────────────────────────────────────────
    evaluation_benchmark_path: str = "./data/benchmark/questions.json"
    evaluation_output_path: str = "./data/evaluation_results.json"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_file_types_list(self) -> List[str]:
        return [t.strip().lower() for t in self.allowed_file_types.split(",") if t.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
