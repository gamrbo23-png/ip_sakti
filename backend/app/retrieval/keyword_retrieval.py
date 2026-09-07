"""
IP-SAKTI Sahayak — Keyword / Full-Text Retrieval
PostgreSQL full-text search with tsvector and optional exact-match lookup
for section/rule number queries.
"""
from __future__ import annotations

import re
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.logging_config import get_logger
from app.retrieval.vector_retrieval import VectorCandidate

logger = get_logger(__name__)
settings = get_settings()

# Detect explicit section/rule references in a query
SECTION_REF_RE = re.compile(r"\b[Ss]ection\s+(\d+[A-Za-z]?)\b")
RULE_REF_RE = re.compile(r"\b[Rr]ule\s+(\d+[A-Za-z]?)\b")
FORM_REF_RE = re.compile(r"\b[Ff]orm\s+(?:No\.?\s*)?([A-Z0-9][A-Z0-9\-]*)\b")


def _extract_legal_references(query: str) -> dict:
    """Extract any explicit Section/Rule/Form references from query."""
    refs = {}
    s = SECTION_REF_RE.search(query)
    if s:
        refs["section_no"] = s.group(1)
    r = RULE_REF_RE.search(query)
    if r:
        refs["rule_no"] = r.group(1)
    f = FORM_REF_RE.search(query)
    if f:
        refs["form_no"] = f.group(1)
    return refs


async def keyword_search(
    session: AsyncSession,
    query: str,
    top_k: Optional[int] = None,
    domain: Optional[str] = None,
    status_filter: Optional[List[str]] = None,
) -> List[VectorCandidate]:
    """
    Full-text keyword search with optional exact section/rule lookup.

    Uses:
    1. PostgreSQL tsvector GIN index for ranked FTS.
    2. Exact match on section_no/rule_no if detected in query.

    Returns VectorCandidate objects with keyword_score set in vector_score.
    """
    k = top_k or settings.keyword_top_k
    statuses = status_filter or ["CURRENT"]
    results: List[VectorCandidate] = []

    # ── 1. Exact legal reference lookup ──────────────────────────────────────
    legal_refs = _extract_legal_references(query)

    if legal_refs:
        conditions = ["c.status IN :statuses"]
        params: dict = {"statuses": tuple(statuses)}

        if "section_no" in legal_refs:
            conditions.append("c.section_no = :section_no")
            params["section_no"] = legal_refs["section_no"]
        if "rule_no" in legal_refs:
            conditions.append("c.rule_no = :rule_no")
            params["rule_no"] = legal_refs["rule_no"]
        if domain:
            conditions.append("c.domain = :domain")
            params["domain"] = domain

        params["limit"] = min(k, 10)  # Exact matches — take top 10
        where_clause = " AND ".join(conditions)

        try:
            exact_sql = text(f"""
                SELECT
                    c.id, c.content, c.document_title, c.domain,
                    c.section_no, c.rule_no, c.chapter, c.source_url,
                    c.authority, c.authority_tier, c.page_number, c.status, c.language,
                    1.0 AS keyword_score
                FROM chunks c
                WHERE {where_clause}
                LIMIT :limit
            """)
            exact_result = await session.execute(exact_sql, params)
            for row in exact_result.fetchall():
                results.append(VectorCandidate(
                    chunk_id=row.id,
                    content=row.content,
                    vector_score=float(row.keyword_score),
                    document_title=row.document_title,
                    domain=row.domain,
                    section_no=row.section_no,
                    rule_no=row.rule_no,
                    chapter=row.chapter,
                    source_url=row.source_url,
                    authority=row.authority,
                    authority_tier=str(row.authority_tier) if row.authority_tier else None,
                    page_number=row.page_number,
                    status=str(row.status) if row.status else None,
                    language=row.language,
                ))
        except Exception as exc:
            logger.warning("Exact legal reference lookup failed", error=str(exc))

    # ── 2. Full-text search ───────────────────────────────────────────────────
    # Clean query for tsvector: remove special chars, prepare for plainto_tsquery
    fts_query = re.sub(r"[^\w\s]", " ", query).strip()
    if not fts_query:
        return results

    conditions_fts = ["c.status IN :statuses_fts"]
    params_fts: dict = {"statuses_fts": tuple(statuses), "limit_fts": k}

    if domain:
        conditions_fts.append("c.domain = :domain_fts")
        params_fts["domain_fts"] = domain

    params_fts["fts_query"] = fts_query
    where_clause_fts = " AND ".join(conditions_fts)

    is_sqlite = "sqlite" in settings.database_url

    try:
        if is_sqlite:
            # SQLite fallback: search with LIKE and token frequency
            words = [w for w in fts_query.lower().split() if len(w) > 2]
            if words:
                from app.models.models import Chunk
                from sqlalchemy import select
                stmt = select(Chunk)
                if domain:
                    stmt = stmt.where(Chunk.domain == domain)
                res = await session.execute(stmt.limit(100))
                rows = res.scalars().all()
                existing_ids = {r.chunk_id for r in results}
                
                scored_candidates = []
                for r in rows:
                    if r.id in existing_ids:
                        continue
                    text_lower = r.content.lower()
                    hits = sum(1 for w in words if w in text_lower)
                    if hits > 0:
                        scored_candidates.append((
                            hits / len(words),
                            VectorCandidate(
                                chunk_id=r.id,
                                content=r.content,
                                vector_score=float(hits / len(words)),
                                document_title=r.document_title,
                                domain=r.domain,
                                section_no=r.section_no,
                                rule_no=r.rule_no,
                                chapter=r.chapter,
                                source_url=r.source_url,
                                authority=r.authority,
                                authority_tier=str(r.authority_tier.value) if r.authority_tier else None,
                                page_number=r.page_number,
                                status=str(r.status.value) if r.status else None,
                                language=r.language,
                            )
                        ))
                scored_candidates.sort(key=lambda x: x[0], reverse=True)
                for _, cand in scored_candidates[:k]:
                    results.append(cand)
            return results

        # PostgreSQL tsvector search
        fts_sql = text(f"""
            SELECT
                c.id, c.content, c.document_title, c.domain,
                c.section_no, c.rule_no, c.chapter, c.source_url,
                c.authority, c.authority_tier, c.page_number, c.status, c.language,
                ts_rank_cd(
                    to_tsvector('english', c.content),
                    plainto_tsquery('english', :fts_query)
                ) AS keyword_score
            FROM chunks c
            WHERE {where_clause_fts}
              AND to_tsvector('english', c.content) @@ plainto_tsquery('english', :fts_query)
            ORDER BY keyword_score DESC
            LIMIT :limit_fts
        """)
        fts_result = await session.execute(fts_sql, params_fts)
        existing_ids = {r.chunk_id for r in results}

        for row in fts_result.fetchall():
            if row.id not in existing_ids:
                results.append(VectorCandidate(
                    chunk_id=row.id,
                    content=row.content,
                    vector_score=float(row.keyword_score),
                    document_title=row.document_title,
                    domain=row.domain,
                    section_no=row.section_no,
                    rule_no=row.rule_no,
                    chapter=row.chapter,
                    source_url=row.source_url,
                    authority=row.authority,
                    authority_tier=str(row.authority_tier) if row.authority_tier else None,
                    page_number=row.page_number,
                    status=str(row.status) if row.status else None,
                    language=row.language,
                ))
    except Exception as exc:
        logger.error("Full-text search failed", error=str(exc))

    logger.debug("Keyword search complete", results=len(results), domain=domain)
    return results
