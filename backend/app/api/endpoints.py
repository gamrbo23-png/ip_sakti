"""Search, Sources, Feedback, Documents, and Admin API endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.logging_config import get_logger
from app.models.models import (
    Chunk, Document, Feedback, IngestionJob, RetrievalLog, Source, ChatSession
)
from app.schemas.schemas import (
    AdminStatsResponse, FeedbackRequest, FeedbackResponse,
    IngestionJobResponse, IngestRequest, IngestResponse,
    SearchRequest, SearchResponse, SearchResult, SourceResponse,
)

logger = get_logger(__name__)
settings = get_settings()

# ─── Search Router ─────────────────────────────────────────────────────────────
search_router = APIRouter()


@search_router.post("/search", response_model=SearchResponse, summary="Search knowledge base")
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Search the legal knowledge base."""
    from app.retrieval.hybrid_retrieval import hybrid_retrieve
    from app.multilingual.language_detector import detect_language
    from app.services.embedding_service import get_embedding_service

    lang = detect_language(request.query).language

    retrieval = await hybrid_retrieve(
        session=db,
        query=request.query,
        query_language=lang,
        domain=request.domain,
        final_context_k=request.top_k,
    )

    results = [
        SearchResult(
            chunk_id=e.chunk_id,
            document_title=e.document_title,
            domain=e.domain,
            section_no=e.section_no,
            rule_no=e.rule_no,
            chapter=e.chapter,
            authority=e.authority,
            source_url=e.source_url,
            page_number=e.page_number,
            status=e.status,
            content_preview=e.content[:300] if e.content else "",
            relevance_score=round(e.reranker_score, 4),
        )
        for e in retrieval.evidence
    ]

    return SearchResponse(
        results=results,
        total=len(results),
        query=request.query,
        domain=request.domain,
    )


# ─── Sources Router ────────────────────────────────────────────────────────────
sources_router = APIRouter()


@sources_router.get("/sources", response_model=List[SourceResponse], summary="List knowledge sources")
async def list_sources(
    domain: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Return all registered knowledge sources."""
    stmt = select(Source).where(Source.is_active == True)
    if domain:
        stmt = stmt.where(Source.domain == domain)

    result = await db.execute(stmt.order_by(Source.domain, Source.name))
    sources = result.scalars().all()
    return sources


@sources_router.get("/sources/{source_id}", response_model=SourceResponse, summary="Get source detail")
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@sources_router.get("/domains", summary="List supported IP domains")
async def list_domains():
    """Return all supported IP domains with descriptions."""
    return {
        "domains": [
            {"domain": "patent", "display_name": "Patents", "description": "Inventions and technical innovations"},
            {"domain": "trademark", "display_name": "Trade Marks", "description": "Brand names, logos, slogans"},
            {"domain": "copyright", "display_name": "Copyright", "description": "Creative and literary works"},
            {"domain": "design", "display_name": "Industrial Designs", "description": "Aesthetic appearance of products"},
            {"domain": "gi", "display_name": "Geographical Indications", "description": "Products from specific regions"},
            {"domain": "sicld", "display_name": "Semiconductor IC Layout", "description": "Semiconductor layout-designs"},
            {"domain": "startup", "display_name": "Startup / DPIIT", "description": "Startup India IP facilitation"},
            {"domain": "data_protection", "display_name": "Data Protection", "description": "DPDP Act 2023"},
            {"domain": "regulatory_general", "display_name": "Regulatory", "description": "Other Indian regulatory topics"},
        ]
    }


@sources_router.get("/laws", summary="List indexed legal documents")
async def list_laws(
    domain: Optional[str] = None,
    document_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Return list of indexed legal documents."""
    stmt = select(Document)
    if domain:
        stmt = stmt.where(Document.domain == domain)
    if document_type:
        stmt = stmt.where(Document.document_type == document_type)

    result = await db.execute(stmt.order_by(Document.domain, Document.title))
    docs = result.scalars().all()

    return {
        "laws": [
            {
                "id": d.id,
                "title": d.title,
                "domain": d.domain,
                "document_type": d.document_type,
                "authority": d.authority,
                "status": str(d.status.value) if d.status else "UNKNOWN",
                "source_url": d.source_url,
                "page_count": d.page_count,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ],
        "total": len(docs),
    }


# ─── Feedback Router ───────────────────────────────────────────────────────────
feedback_router = APIRouter()


@feedback_router.post("/feedback", response_model=FeedbackResponse, summary="Submit answer feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Record user feedback on a generated answer."""
    fb = Feedback(
        session_id=request.session_id,
        message_id=request.message_id,
        retrieval_trace_id=request.retrieval_trace_id,
        rating=request.rating,
        comment=request.comment,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return FeedbackResponse(id=fb.id)


# ─── Documents Router ──────────────────────────────────────────────────────────
documents_router = APIRouter()


@documents_router.post("/documents/upload", summary="Upload and analyze a user document")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a user-uploaded document, extract its text, and cross-reference
    with the authoritative knowledge base. The uploaded document is NOT
    treated as authoritative legal source.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in settings.allowed_file_types_list:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Allowed: {settings.allowed_file_types}",
        )

    # Check file size
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb}MB",
        )

    # Extract text (simplified — in production use full pipeline)
    extracted_text = ""
    if ext == "pdf":
        try:
            import fitz
            import io
            doc = fitz.open(stream=content, filetype="pdf")
            pages = []
            for page in doc:
                pages.append(page.get_text("text"))
            extracted_text = "\n\n".join(pages)[:5000]  # Limit for safety
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Could not extract text from PDF: {exc}")
    elif ext == "txt":
        try:
            extracted_text = content.decode("utf-8", errors="replace")[:5000]
        except Exception:
            raise HTTPException(status_code=422, detail="Could not read text file")

    if not extracted_text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from the document")

    # Cross-reference with knowledge base
    from app.retrieval.hybrid_retrieval import hybrid_retrieve
    from app.services.embedding_service import get_embedding_service

    retrieval = await hybrid_retrieve(
        session=db,
        query=extracted_text[:500],  # Use beginning as query
        query_language="en",
        final_context_k=5,
    )

    related = [
        {
            "chunk_id": e.chunk_id,
            "document_title": e.document_title,
            "domain": e.domain,
            "section_no": e.section_no,
            "rule_no": e.rule_no,
            "authority": e.authority,
            "source_url": e.source_url,
            "relevance_score": round(e.reranker_score, 4),
            "content_preview": e.content[:200],
        }
        for e in retrieval.evidence
    ]

    return {
        "file_name": file.filename,
        "content_preview": extracted_text[:500],
        "related_official_sources": related,
        "disclaimer": (
            "⚠️ IMPORTANT: The uploaded document is a USER document and is NOT "
            "treated as an authoritative legal source. Related official sources "
            "are retrieved from the authoritative knowledge base for reference only. "
            "This document was processed temporarily and has NOT been stored."
        ),
        "privacy_note": "This document was not persisted to our systems.",
    }


# ─── Admin Router ──────────────────────────────────────────────────────────────
admin_router = APIRouter()


@admin_router.get("/stats", response_model=AdminStatsResponse, summary="Admin dashboard stats")
async def admin_stats(db: AsyncSession = Depends(get_db)):
    """Return statistics for the admin dashboard."""
    # Document counts
    total_docs = await db.scalar(select(func.count(Document.id))) or 0
    total_chunks = await db.scalar(select(func.count(Chunk.id))) or 0
    total_sources = await db.scalar(select(func.count(Source.id)).where(Source.is_active == True)) or 0
    total_sessions = await db.scalar(select(func.count(ChatSession.id))) or 0
    total_queries = await db.scalar(select(func.count(RetrievalLog.id))) or 0

    # Domain coverage
    domain_result = await db.execute(
        select(Chunk.domain, func.count(Chunk.id))
        .group_by(Chunk.domain)
    )
    domains_coverage = {row[0] or "unknown": row[1] for row in domain_result.fetchall()}

    # Recent jobs
    jobs_result = await db.execute(
        select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(10)
    )
    recent_jobs = jobs_result.scalars().all()

    # Latency averages
    latency_result = await db.execute(
        select(
            func.avg(RetrievalLog.retrieval_latency_ms),
            func.avg(RetrievalLog.total_latency_ms),
        )
    )
    lat_row = latency_result.fetchone()
    avg_retrieval = round(lat_row[0] or 0.0, 2)
    avg_total = round(lat_row[1] or 0.0, 2)

    # Low evidence rate
    low_evidence_count = await db.scalar(
        select(func.count(RetrievalLog.id)).where(
            RetrievalLog.evidence_level == "low"
        )
    ) or 0
    low_evidence_rate = round(low_evidence_count / max(total_queries, 1), 4)

    # Feedback rate
    helpful = await db.scalar(
        select(func.count(Feedback.id)).where(Feedback.rating == 1)
    ) or 0
    total_fb = await db.scalar(select(func.count(Feedback.id))) or 0
    helpful_rate = round(helpful / max(total_fb, 1), 4)

    return AdminStatsResponse(
        total_documents=total_docs,
        total_chunks=total_chunks,
        total_sources=total_sources,
        total_sessions=total_sessions,
        total_queries=total_queries,
        domains_coverage=domains_coverage,
        recent_jobs=[IngestionJobResponse.model_validate(j) for j in recent_jobs],
        avg_retrieval_latency_ms=avg_retrieval,
        avg_total_latency_ms=avg_total,
        low_evidence_rate=low_evidence_rate,
        helpful_feedback_rate=helpful_rate,
    )


@admin_router.post("/ingest", response_model=IngestResponse, summary="Trigger document ingestion")
async def trigger_ingestion(
    request: IngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Trigger ingestion of registered sources (async, returns immediately)."""
    import asyncio
    from app.ingestion.pipeline import run_full_ingestion

    # Run ingestion in background
    asyncio.create_task(
        run_full_ingestion(
            domains=request.domains,
            force_refresh=request.force_refresh,
        )
    )

    return IngestResponse(
        job_id=0,
        message="Ingestion started in background. Check /api/admin/stats for progress.",
        sources_queued=len(request.source_ids) if request.source_ids else -1,
    )


@admin_router.get("/ingestion/jobs", summary="List ingestion jobs")
async def list_ingestion_jobs(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IngestionJob)
        .order_by(IngestionJob.created_at.desc())
        .limit(limit)
    )
    jobs = result.scalars().all()
    return {"jobs": [IngestionJobResponse.model_validate(j) for j in jobs]}


# Export routers with their prefixes
search = search_router
sources = sources_router
feedback = feedback_router
documents = documents_router
admin = admin_router
