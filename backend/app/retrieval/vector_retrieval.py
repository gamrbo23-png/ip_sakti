"""
IP-SAKTI Sahayak — Vector Retrieval
Semantic similarity search using pgvector (HNSW index, cosine similarity).
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.logging_config import get_logger
from app.models.models import Chunk, DocumentStatus

logger = get_logger(__name__)
settings = get_settings()


class VectorCandidate:
    """A retrieved chunk candidate from vector search."""

    def __init__(
        self,
        chunk_id: int,
        content: str,
        vector_score: float,
        document_title: Optional[str] = None,
        domain: Optional[str] = None,
        section_no: Optional[str] = None,
        rule_no: Optional[str] = None,
        chapter: Optional[str] = None,
        source_url: Optional[str] = None,
        authority: Optional[str] = None,
        authority_tier: Optional[str] = None,
        page_number: Optional[int] = None,
        status: Optional[str] = None,
        language: Optional[str] = None,
    ) -> None:
        self.chunk_id = chunk_id
        self.content = content
        self.vector_score = vector_score
        self.document_title = document_title
        self.domain = domain
        self.section_no = section_no
        self.rule_no = rule_no
        self.chapter = chapter
        self.source_url = source_url
        self.authority = authority
        self.authority_tier = authority_tier
        self.page_number = page_number
        self.status = status
        self.language = language
        # Will be filled by reranker
        self.reranker_score: float = 0.0
        self.final_rank: int = 0


async def vector_search(
    session: AsyncSession,
    query_embedding: List[float],
    top_k: Optional[int] = None,
    domain: Optional[str] = None,
    status_filter: Optional[List[str]] = None,
) -> List[VectorCandidate]:
    """
    Perform cosine similarity search using pgvector HNSW index.

    Args:
        session: Async database session.
        query_embedding: The query's dense embedding vector.
        top_k: Number of results to return.
        domain: Filter to a specific IP domain.
        status_filter: Filter by document status (e.g., ['CURRENT']).

    Returns:
        List of VectorCandidate objects sorted by similarity score.
    """
    k = top_k or settings.vector_top_k
    statuses = status_filter or ["CURRENT"]

    is_sqlite = "sqlite" in settings.database_url

    try:
        if is_sqlite:
            # SQLite fallback: load chunks and compute cosine similarity with numpy
            import numpy as np
            stmt = select(Chunk).where(Chunk.embedding != None)
            if domain:
                stmt = stmt.where(Chunk.domain == domain)
            
            res = await session.execute(stmt.limit(100))
            rows = res.scalars().all()
            
            q_vec = np.array(query_embedding, dtype=np.float32)
            candidates = []
            for r in rows:
                if not r.embedding:
                    continue
                emb = np.array(r.embedding, dtype=np.float32)
                sim = float(np.dot(q_vec, emb))
                candidates.append(VectorCandidate(
                    chunk_id=r.id,
                    content=r.content,
                    vector_score=sim,
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
                ))
            candidates.sort(key=lambda x: x.vector_score, reverse=True)
            return candidates[:k]

        # PostgreSQL pgvector query
        embedding_str = f"[{','.join(str(v) for v in query_embedding)}]"

        conditions = ["c.status IN :statuses", "c.embedding IS NOT NULL"]
        params: dict = {"statuses": tuple(statuses), "limit": k}

        if domain:
            conditions.append("c.domain = :domain")
            params["domain"] = domain

        where_clause = " AND ".join(conditions)

        sql = text(f"""
            SELECT
                c.id,
                c.content,
                c.document_title,
                c.domain,
                c.section_no,
                c.rule_no,
                c.chapter,
                c.source_url,
                c.authority,
                c.authority_tier,
                c.page_number,
                c.status,
                c.language,
                1 - (c.embedding <=> :query_vec::vector) AS similarity_score
            FROM chunks c
            WHERE {where_clause}
            ORDER BY c.embedding <=> :query_vec::vector
            LIMIT :limit
        """)

        params["query_vec"] = embedding_str
        result = await session.execute(sql, params)
        rows = result.fetchall()

        candidates = []
        for row in rows:
            candidate = VectorCandidate(
                chunk_id=row.id,
                content=row.content,
                vector_score=float(row.similarity_score),
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
            )
            candidates.append(candidate)

        logger.debug("Vector search complete", results=len(candidates), domain=domain)
        return candidates

    except Exception as exc:
        logger.error("Vector search failed", error=str(exc))
        return []

