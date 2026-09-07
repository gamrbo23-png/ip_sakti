"""
IP-SAKTI Sahayak — Chat API Endpoint
Core RAG pipeline endpoint: handles multilingual queries end-to-end.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.llm.generator import generate_answer
from app.logging_config import get_logger
from app.models.models import ChatMessage, ChatSession, RetrievalLog
from app.multilingual.intent_classifier import classify_intent_and_domain
from app.multilingual.language_detector import detect_language
from app.multilingual.query_rewriter import rewrite_query
from app.retrieval.hybrid_retrieval import hybrid_retrieve
from app.schemas.schemas import (
    ChatRequest, ChatResponse, CitationResponse, EvidenceTrace,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse, summary="Ask IP-SAKTI Sahayak")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Main RAG endpoint. Processes a user query through:
    1. Language detection
    2. Intent + domain classification
    3. Query rewriting
    4. Hybrid retrieval (vector + keyword)
    5. BGE reranking
    6. Grounded LLM generation
    7. Citation verification
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info("Chat request", query=query[:100], session_id=request.session_id)

    # ── Step 1: Language detection ────────────────────────────────────────────
    lang_result = detect_language(query)
    language = request.language or lang_result.language

    # ── Step 2: Get or create session ─────────────────────────────────────────
    session_id = request.session_id or str(uuid.uuid4())
    db_session = await db.get(ChatSession, session_id)

    if db_session is None:
        db_session = ChatSession(
            id=session_id,
            language=language,
            is_active=True,
        )
        db.add(db_session)
        await db.flush()

    # ── Step 3: Intent + domain classification ────────────────────────────────
    classification = await classify_intent_and_domain(query, language)
    domain = request.domain or (
        classification.domain if classification.domain != "unknown" else None
    )

    # ── Step 4: Query rewriting ───────────────────────────────────────────────
    rewritten = await rewrite_query(
        query=query,
        language=language,
        domain=domain,
        intent=classification.intent,
    )

    # ── Step 5: Hybrid retrieval ──────────────────────────────────────────────
    retrieval_result = await hybrid_retrieve(
        session=db,
        query=query,
        query_language=language,
        domain=domain,
        intent=classification.intent,
        rewritten_queries=rewritten,
        prefer_current=classification.requires_current_rules,
    )

    # ── Step 6: LLM generation ────────────────────────────────────────────────
    generated = await generate_answer(
        query=query,
        retrieval_result=retrieval_result,
        language=language,
        domain=domain,
        intent=classification.intent,
    )

    # ── Step 7: Persist chat messages ─────────────────────────────────────────
    # User message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=query,
        language=language,
        domain=domain,
        intent=classification.intent,
    )
    db.add(user_msg)
    await db.flush()

    # Assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=generated.answer,
        language=language,
        domain=domain,
        intent=classification.intent,
        citations=[
            {
                "citation_number": c.citation_number,
                "document_title": c.document_title,
                "section_no": c.section_no,
                "rule_no": c.rule_no,
                "source_url": c.source_url,
            }
            for c in generated.citations
        ],
        confidence=generated.confidence,
        evidence_level=generated.evidence_level,
        retrieval_trace_id=retrieval_result.trace_id,
    )
    db.add(assistant_msg)
    await db.flush()

    # Update session metadata
    if not db_session.domain and domain:
        db_session.domain = domain
    db_session.updated_at = datetime.now(timezone.utc)

    # ── Step 8: Persist retrieval log ─────────────────────────────────────────
    retrieval_log = RetrievalLog(
        id=retrieval_result.trace_id,
        session_id=session_id,
        query=query,
        query_language=language,
        query_domain=domain,
        query_intent=classification.intent,
        rewritten_queries=rewritten,
        vector_candidates={"count": retrieval_result.vector_count},
        keyword_candidates={"count": retrieval_result.keyword_count},
        merged_candidates={"count": retrieval_result.merged_count},
        final_evidence={
            "count": retrieval_result.final_count,
            "chunk_ids": [e.chunk_id for e in retrieval_result.evidence],
        },
        llm_response=generated.answer[:2000],
        retrieval_latency_ms=retrieval_result.retrieval_latency_ms,
        reranker_latency_ms=retrieval_result.reranker_latency_ms,
        llm_latency_ms=generated.llm_latency_ms,
        total_latency_ms=generated.total_latency_ms,
        confidence=generated.confidence,
        evidence_level=generated.evidence_level,
    )
    db.add(retrieval_log)
    await db.commit()

    # ── Build response ────────────────────────────────────────────────────────
    citation_responses = [
        CitationResponse(
            citation_number=c.citation_number,
            document_title=c.document_title,
            section_no=c.section_no,
            rule_no=c.rule_no,
            chapter=c.chapter,
            page_number=c.page_number,
            authority=c.authority,
            source_url=c.source_url,
            status=c.status,
            is_current=c.is_current,
        )
        for c in generated.citations
    ]

    evidence_traces = [
        EvidenceTrace(
            chunk_id=e.chunk_id,
            document_title=e.document_title,
            section_no=e.section_no,
            rule_no=e.rule_no,
            chapter=e.chapter,
            domain=e.domain,
            authority=e.authority,
            authority_tier=e.authority_tier,
            source_url=e.source_url,
            page_number=e.page_number,
            status=e.status,
            reranker_score=round(e.reranker_score, 4),
            content_preview=e.content[:300] if e.content else "",
        )
        for e in retrieval_result.evidence
    ]

    return ChatResponse(
        session_id=session_id,
        message_id=assistant_msg.id,
        answer=generated.answer,
        language=language,
        domain=domain,
        intent=classification.intent,
        confidence=generated.confidence,
        evidence_level=generated.evidence_level,
        citations=citation_responses,
        evidence=evidence_traces,
        warnings=generated.warnings,
        retrieval_trace_id=retrieval_result.trace_id,
        has_sufficient_evidence=generated.has_sufficient_evidence,
        retrieval_latency_ms=retrieval_result.retrieval_latency_ms,
        total_latency_ms=generated.total_latency_ms,
        trace_detail=retrieval_result.trace_detail if request.include_trace else None,
    )


@router.get("/chat/{session_id}", summary="Get chat history")
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all messages for a chat session."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()

    return {
        "session_id": session_id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "language": m.language,
                "domain": m.domain,
                "citations": m.citations,
                "confidence": m.confidence,
                "evidence_level": m.evidence_level,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "total": len(messages),
    }
