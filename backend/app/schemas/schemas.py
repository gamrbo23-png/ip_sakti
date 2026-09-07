"""
IP-SAKTI Sahayak — Pydantic Schemas for API
Request/response models for all endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


# ── Chat Schemas ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """User chat request."""
    query: str = Field(..., min_length=1, max_length=2000, description="User's question")
    session_id: Optional[str] = Field(None, description="Existing session ID to continue conversation")
    language: Optional[str] = Field(None, description="Force response language (auto-detected if not provided)")
    domain: Optional[str] = Field(None, description="Force a specific IP domain")
    include_trace: bool = Field(False, description="Include retrieval trace in response (debug)")


class CitationResponse(BaseModel):
    """A single citation in the response."""
    citation_number: int
    document_title: str
    section_no: Optional[str] = None
    rule_no: Optional[str] = None
    chapter: Optional[str] = None
    page_number: Optional[int] = None
    authority: str
    source_url: str
    status: str
    is_current: bool


class EvidenceTrace(BaseModel):
    """Evidence item for the 'Why this answer?' panel."""
    chunk_id: int
    document_title: Optional[str] = None
    section_no: Optional[str] = None
    rule_no: Optional[str] = None
    chapter: Optional[str] = None
    domain: Optional[str] = None
    authority: Optional[str] = None
    authority_tier: Optional[str] = None
    source_url: Optional[str] = None
    page_number: Optional[int] = None
    status: Optional[str] = None
    reranker_score: float
    content_preview: str   # First 300 chars of content


class ChatResponse(BaseModel):
    """Complete chat response."""
    session_id: str
    message_id: Optional[int] = None
    answer: str
    language: str
    domain: Optional[str] = None
    intent: Optional[str] = None
    confidence: float
    evidence_level: str   # high | moderate | low | none
    citations: List[CitationResponse]
    evidence: List[EvidenceTrace]   # For 'Why this answer?' panel
    warnings: List[str]
    retrieval_trace_id: str
    has_sufficient_evidence: bool
    retrieval_latency_ms: float
    total_latency_ms: float
    trace_detail: Optional[Dict[str, Any]] = None   # Only if include_trace=True


# ── Search Schemas ────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    domain: Optional[str] = None
    document_type: Optional[str] = None
    status: Optional[str] = None
    top_k: int = Field(10, ge=1, le=50)


class SearchResult(BaseModel):
    chunk_id: int
    document_title: Optional[str] = None
    domain: Optional[str] = None
    section_no: Optional[str] = None
    rule_no: Optional[str] = None
    chapter: Optional[str] = None
    authority: Optional[str] = None
    source_url: Optional[str] = None
    page_number: Optional[int] = None
    status: Optional[str] = None
    content_preview: str
    relevance_score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str
    domain: Optional[str] = None


# ── Source Schemas ─────────────────────────────────────────────────────────────

class SourceResponse(BaseModel):
    id: int
    name: str
    authority: str
    authority_tier: str
    domain: str
    document_type: Optional[str] = None
    url: str
    description: Optional[str] = None
    is_active: bool
    last_checked: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Feedback Schemas ──────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    session_id: Optional[str] = None
    message_id: Optional[int] = None
    retrieval_trace_id: Optional[str] = None
    rating: int = Field(..., ge=-1, le=1, description="1=helpful, -1=not helpful")
    comment: Optional[str] = Field(None, max_length=1000)


class FeedbackResponse(BaseModel):
    id: int
    message: str = "Thank you for your feedback"


# ── Document Upload Schemas ───────────────────────────────────────────────────

class DocumentAnalysisResponse(BaseModel):
    """Response after analyzing an uploaded user document."""
    file_name: str
    content_preview: str
    related_sources: List[SearchResult]
    analysis: str
    warnings: List[str]
    disclaimer: str


# ── Admin Schemas ─────────────────────────────────────────────────────────────

class IngestionJobResponse(BaseModel):
    id: int
    source_url: str
    status: str
    chunks_created: int
    duplicates_skipped: int
    embeddings_generated: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminStatsResponse(BaseModel):
    """Dashboard statistics for admin panel."""
    total_documents: int
    total_chunks: int
    total_sources: int
    total_sessions: int
    total_queries: int
    domains_coverage: Dict[str, int]
    recent_jobs: List[IngestionJobResponse]
    avg_retrieval_latency_ms: float
    avg_total_latency_ms: float
    low_evidence_rate: float
    helpful_feedback_rate: float


class IngestRequest(BaseModel):
    """Admin: trigger ingestion of a source."""
    source_ids: Optional[List[str]] = Field(None, description="Specific source IDs to ingest (all if not specified)")
    domains: Optional[List[str]] = None
    force_refresh: bool = False


class IngestResponse(BaseModel):
    job_id: int
    message: str
    sources_queued: int


# ── Domain / Law Schemas ──────────────────────────────────────────────────────

class DomainInfo(BaseModel):
    domain: str
    display_name: str
    description: str
    acts: List[str]
    rules: List[str]


class IPComparisonRow(BaseModel):
    """One row in the IP comparison table."""
    field: str
    patent: Optional[str]
    trademark: Optional[str]
    copyright: Optional[str]
    design: Optional[str]
