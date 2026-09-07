"""
IP-SAKTI Sahayak — Hybrid Retrieval Pipeline
Merges vector + keyword results using Reciprocal Rank Fusion (RRF),
then applies BGE reranking and authority/version filtering.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.logging_config import get_logger
from app.retrieval.keyword_retrieval import keyword_search
from app.retrieval.vector_retrieval import VectorCandidate, vector_search
from app.services.embedding_service import get_embedding_service
from app.services.reranker_service import get_reranker_service

logger = get_logger(__name__)
settings = get_settings()

RRF_K = 60  # Standard RRF constant


@dataclass
class RetrievalResult:
    """Complete retrieval result with evidence chunks and trace data."""
    trace_id: str
    evidence: List[VectorCandidate]
    query: str
    language: str
    domain: Optional[str]
    intent: Optional[str]
    rewritten_queries: List[str]
    vector_count: int
    keyword_count: int
    merged_count: int
    final_count: int
    retrieval_latency_ms: float
    reranker_latency_ms: float
    total_latency_ms: float
    confidence: float
    evidence_level: str   # high | moderate | low
    trace_detail: Dict[str, Any] = field(default_factory=dict)


def _reciprocal_rank_fusion(
    vector_results: List[VectorCandidate],
    keyword_results: List[VectorCandidate],
    k: int = RRF_K,
) -> List[VectorCandidate]:
    """
    Merge vector and keyword results using Reciprocal Rank Fusion.

    RRF score = sum(1 / (k + rank_i)) for each list containing the item.
    Higher score = better combined rank.
    """
    scores: Dict[int, float] = {}
    chunk_map: Dict[int, VectorCandidate] = {}

    for rank, candidate in enumerate(vector_results):
        cid = candidate.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
        chunk_map[cid] = candidate

    for rank, candidate in enumerate(keyword_results):
        cid = candidate.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
        if cid not in chunk_map:
            chunk_map[cid] = candidate

    # Sort by RRF score descending
    sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

    merged = []
    for cid in sorted_ids:
        candidate = chunk_map[cid]
        candidate.vector_score = scores[cid]  # Use RRF score for merged ranking
        merged.append(candidate)

    return merged


def _compute_confidence(
    evidence: List[VectorCandidate],
    top_k: int,
) -> tuple[float, str]:
    """
    Compute a simple confidence score from top evidence scores.
    Returns (confidence_float, evidence_level_label).
    """
    if not evidence:
        return 0.0, "none"

    top_scores = [e.reranker_score for e in evidence[:top_k] if e.reranker_score > 0]
    if not top_scores:
        top_scores = [e.vector_score for e in evidence[:top_k]]

    avg_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
    max_score = max(top_scores) if top_scores else 0.0

    # Weight: 60% max score, 40% average
    confidence = 0.6 * max_score + 0.4 * avg_score

    if confidence >= settings.high_evidence_threshold:
        level = "high"
    elif confidence >= settings.moderate_evidence_threshold:
        level = "moderate"
    else:
        level = "low"

    return round(confidence, 4), level


async def hybrid_retrieve(
    session: AsyncSession,
    query: str,
    query_language: str = "en",
    domain: Optional[str] = None,
    intent: Optional[str] = None,
    rewritten_queries: Optional[List[str]] = None,
    prefer_current: bool = True,
    vector_top_k: Optional[int] = None,
    keyword_top_k: Optional[int] = None,
    rerank_top_k: Optional[int] = None,
    final_context_k: Optional[int] = None,
) -> RetrievalResult:
    """
    Full hybrid retrieval pipeline:
    1. Embed query (BGE-M3)
    2. Vector search (pgvector)
    3. Keyword search (PostgreSQL FTS)
    4. RRF fusion + deduplication
    5. BGE reranking
    6. Authority/version filtering
    7. Return top-K evidence

    Args:
        session: Database session.
        query: User's original query.
        query_language: Detected language code.
        domain: Optional domain filter.
        intent: Detected intent label.
        rewritten_queries: Additional query reformulations for broader retrieval.
        prefer_current: If True, prefer CURRENT status documents.
        vector_top_k: Override vector search top-k.
        keyword_top_k: Override keyword search top-k.
        rerank_top_k: Override reranker top-k.
        final_context_k: Override final evidence count.

    Returns:
        RetrievalResult with evidence chunks and full trace.
    """
    trace_id = str(uuid.uuid4())
    start_total = time.monotonic()

    v_k = vector_top_k or settings.vector_top_k
    kw_k = keyword_top_k or settings.keyword_top_k
    rr_k = rerank_top_k or settings.rerank_top_k
    f_k = final_context_k or settings.final_context_k

    status_filter = ["CURRENT"] if prefer_current else ["CURRENT", "AMENDED", "HISTORICAL"]
    rw_queries = rewritten_queries or []

    # ── Step 1: Embed query ───────────────────────────────────────────────────
    emb_service = get_embedding_service()
    start_retrieval = time.monotonic()

    query_embedding = emb_service.encode_query(query)

    # ── Step 2: Vector search (primary query + rewritten queries) ─────────────
    vector_results: List[VectorCandidate] = []
    all_queries = [query] + rw_queries[:2]   # Limit to 3 total queries

    for q in all_queries:
        q_emb = emb_service.encode_query(q) if q != query else query_embedding
        v_results = await vector_search(
            session=session,
            query_embedding=q_emb,
            top_k=v_k,
            domain=domain,
            status_filter=status_filter,
        )
        # Merge, dedup by chunk_id
        existing_ids = {r.chunk_id for r in vector_results}
        for r in v_results:
            if r.chunk_id not in existing_ids:
                vector_results.append(r)
                existing_ids.add(r.chunk_id)

    # ── Step 3: Keyword search ────────────────────────────────────────────────
    keyword_results = await keyword_search(
        session=session,
        query=query,
        top_k=kw_k,
        domain=domain,
        status_filter=status_filter,
    )

    retrieval_latency_ms = round((time.monotonic() - start_retrieval) * 1000, 2)

    # ── Step 4: RRF fusion + deduplication ────────────────────────────────────
    merged = _reciprocal_rank_fusion(
        vector_results=vector_results[:v_k],
        keyword_results=keyword_results[:kw_k],
    )

    # Take top candidates for reranking
    rerank_candidates = merged[:rr_k]

    # ── Step 5: Reranking ─────────────────────────────────────────────────────
    start_reranker = time.monotonic()

    if rerank_candidates:
        reranker = get_reranker_service()
        passages = [c.content for c in rerank_candidates]

        try:
            ranked = reranker.rerank(
                query=query,
                passages=passages,
                top_k=min(rr_k, len(passages)),
                normalize=True,
            )

            reranked_candidates = []
            for final_rank, (orig_idx, score) in enumerate(ranked):
                candidate = rerank_candidates[orig_idx]
                candidate.reranker_score = score
                candidate.final_rank = final_rank
                reranked_candidates.append(candidate)

        except Exception as exc:
            logger.warning("Reranker unavailable, using RRF order", error=str(exc))
            for i, c in enumerate(rerank_candidates):
                c.reranker_score = c.vector_score
                c.final_rank = i
            reranked_candidates = rerank_candidates

    else:
        reranked_candidates = []

    reranker_latency_ms = round((time.monotonic() - start_reranker) * 1000, 2)

    # ── Step 6: Authority/version preference ──────────────────────────────────
    # Sort Tier-1 above others at same reranker score
    def sort_key(c: VectorCandidate):
        tier_bonus = 0.1 if c.authority_tier == "TIER_1" else 0.0
        return c.reranker_score + tier_bonus

    final_evidence = sorted(reranked_candidates, key=sort_key, reverse=True)[:f_k]

    # ── Step 7: Compute confidence ─────────────────────────────────────────────
    confidence, evidence_level = _compute_confidence(final_evidence, f_k)

    total_latency_ms = round((time.monotonic() - start_total) * 1000, 2)

    logger.info(
        "Hybrid retrieval complete",
        trace_id=trace_id,
        vector_hits=len(vector_results),
        keyword_hits=len(keyword_results),
        merged=len(merged),
        final=len(final_evidence),
        confidence=confidence,
        evidence_level=evidence_level,
        total_ms=total_latency_ms,
    )

    return RetrievalResult(
        trace_id=trace_id,
        evidence=final_evidence,
        query=query,
        language=query_language,
        domain=domain,
        intent=intent,
        rewritten_queries=rw_queries,
        vector_count=len(vector_results),
        keyword_count=len(keyword_results),
        merged_count=len(merged),
        final_count=len(final_evidence),
        retrieval_latency_ms=retrieval_latency_ms,
        reranker_latency_ms=reranker_latency_ms,
        total_latency_ms=total_latency_ms,
        confidence=confidence,
        evidence_level=evidence_level,
        trace_detail={
            "vector_results": [
                {"id": r.chunk_id, "score": r.vector_score, "domain": r.domain}
                for r in vector_results[:10]
            ],
            "keyword_results": [
                {"id": r.chunk_id, "score": r.vector_score, "domain": r.domain}
                for r in keyword_results[:10]
            ],
            "reranked_results": [
                {
                    "id": r.chunk_id,
                    "reranker_score": r.reranker_score,
                    "final_rank": r.final_rank,
                }
                for r in reranked_candidates
            ],
        },
    )
