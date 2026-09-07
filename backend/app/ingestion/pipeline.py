"""
IP-SAKTI Sahayak — Document Ingestion Pipeline Orchestrator
Coordinates download → extract → parse → chunk → embed → store.
Idempotent: re-running on unchanged documents does nothing.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_context
from app.ingestion.chunker import LegalChunk, chunk_document
from app.ingestion.downloader import download_document
from app.ingestion.html_extractor import extract_html
from app.ingestion.legal_parser import parse_legal_structure
from app.ingestion.pdf_extractor import extract_pdf
from app.ingestion.source_registry import SourceEntry, get_source_registry
from app.logging_config import get_logger
from app.models.models import (
    AuthorityTier, Chunk, Document, DocumentStatus, DocumentVersion,
    IngestionJob, IngestionJobStatus, Source,
)
from app.services.embedding_service import get_embedding_service

logger = get_logger(__name__)
settings = get_settings()


class IngestionReport:
    """Summary of an ingestion run."""

    def __init__(self) -> None:
        self.documents_attempted = 0
        self.documents_successful = 0
        self.documents_failed = 0
        self.documents_skipped_duplicate = 0
        self.chunks_created = 0
        self.duplicates_skipped = 0
        self.embeddings_generated = 0
        self.errors: List[str] = []

    def to_dict(self) -> dict:
        return {
            "documents_attempted": self.documents_attempted,
            "documents_successful": self.documents_successful,
            "documents_failed": self.documents_failed,
            "documents_skipped_duplicate": self.documents_skipped_duplicate,
            "chunks_created": self.chunks_created,
            "duplicates_skipped": self.duplicates_skipped,
            "embeddings_generated": self.embeddings_generated,
            "errors": self.errors,
        }


async def _get_or_create_source(
    session: AsyncSession,
    entry: SourceEntry,
) -> Source:
    """Get existing DB source record or create a new one."""
    result = await session.execute(
        select(Source).where(Source.url == entry.url)
    )
    src = result.scalar_one_or_none()
    if src is None:
        src = Source(
            name=entry.name,
            authority=entry.authority,
            authority_tier=AuthorityTier(entry.authority_tier),
            domain=entry.domain,
            document_type=entry.document_type,
            url=entry.url,
            description=entry.description,
            is_active=True,
            last_checked=datetime.now(timezone.utc),
        )
        session.add(src)
        await session.flush()
    else:
        src.last_checked = datetime.now(timezone.utc)
    return src


async def _store_chunks(
    session: AsyncSession,
    chunks: List[LegalChunk],
    document_id: int,
    source_id: int,
    version_id: int,
) -> tuple[int, int]:
    """
    Store chunks in the database with embeddings.
    Returns (chunks_stored, duplicates_skipped).
    """
    emb_service = get_embedding_service()

    # Filter out chunks whose content_hash already exists
    existing_hashes = set()
    hashes = [c.content_hash for c in chunks]

    if hashes:
        result = await session.execute(
            select(Chunk.content_hash).where(Chunk.content_hash.in_(hashes))
        )
        existing_hashes = {row[0] for row in result.fetchall()}

    new_chunks = [c for c in chunks if c.content_hash not in existing_hashes]
    duplicates_skipped = len(chunks) - len(new_chunks)

    if not new_chunks:
        return 0, duplicates_skipped

    # Generate embeddings in batch
    texts = [c.content for c in new_chunks]
    embeddings = emb_service.encode(texts, show_progress=True)

    # Insert to database
    for i, (chunk, embedding) in enumerate(zip(new_chunks, embeddings)):
        db_chunk = Chunk(
            document_id=document_id,
            version_id=version_id,
            source_id=source_id,
            domain=chunk.domain,
            document_type=chunk.document_type,
            chapter=chunk.chapter,
            section_no=chunk.section_no,
            rule_no=chunk.rule_no,
            title=chunk.title,
            content=chunk.content,
            token_count=chunk.token_count,
            chunk_index=chunk.chunk_index,
            language=chunk.language,
            page_number=chunk.page_number,
            effective_from=None,
            effective_to=None,
            version_label=chunk.version_label,
            status=DocumentStatus(chunk.status) if chunk.status else DocumentStatus.CURRENT,
            authority=chunk.authority,
            authority_tier=AuthorityTier(chunk.authority_tier),
            source_url=chunk.source_url,
            document_title=chunk.document_title,
            content_hash=chunk.content_hash,
            embedding=embedding,
        )
        session.add(db_chunk)

    await session.flush()
    return len(new_chunks), duplicates_skipped


async def ingest_source_entry(
    entry: SourceEntry,
    force_refresh: bool = False,
) -> dict:
    """
    Ingest a single source entry through the full pipeline.

    Args:
        entry: Source registry entry with URL and metadata.
        force_refresh: If True, re-ingest even if hash unchanged.

    Returns:
        Dictionary with ingestion results.
    """
    async with get_db_context() as session:
        # Create/update the source record
        db_source = await _get_or_create_source(session, entry)

        # Create ingestion job record
        job = IngestionJob(
            source_id=db_source.id,
            source_url=entry.url,
            status=IngestionJobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        session.add(job)
        await session.flush()

        try:
            # ── Step 1: Download ──────────────────────────────────────────────
            logger.info("Downloading document", url=entry.url, source=entry.name)
            download = await download_document(
                url=entry.url,
                source_id=entry.id,
                domain=entry.domain,
                known_hash=None,  # Let downloader determine
            )

            if not download.success:
                job.status = IngestionJobStatus.FAILED
                job.error_message = download.error
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
                return {"status": "failed", "error": download.error, "url": entry.url}

            if download.is_duplicate:
                job.status = IngestionJobStatus.SKIPPED
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
                return {"status": "skipped", "reason": "unchanged", "url": entry.url}

            # ── Step 2: Check content hash in DB ──────────────────────────────
            if not force_refresh:
                existing_doc = await session.execute(
                    select(Document).where(
                        Document.content_hash == download.content_hash
                    )
                )
                if existing_doc.scalar_one_or_none():
                    logger.info("Document hash already in DB, skipping", hash=download.content_hash[:16])
                    job.status = IngestionJobStatus.SKIPPED
                    job.completed_at = datetime.now(timezone.utc)
                    await session.commit()
                    return {"status": "skipped", "reason": "hash_exists", "url": entry.url}

            # ── Step 3: Extract text (PDF or HTML) ────────────────────────────
            file_path = download.file_path
            suffix = file_path.suffix.lower() if file_path else ""
            doc_type = getattr(download, "content_type", "").lower()

            is_html = (
                doc_type == "html"
                or suffix in (".html", ".htm", ".asp", ".aspx")
            )
            is_pdf = (
                doc_type == "pdf"
                or suffix == ".pdf"
            )

            if is_html:
                logger.info("[INGEST] Source type detected: HTML", file=file_path.name if file_path else "")
                logger.info("[INGEST] Extracting HTML content", file=file_path.name if file_path else "")
                extracted = extract_html(file_path)
                if extracted.success:
                    char_count = len(extracted.full_text)
                    logger.info("[INGEST] HTML text extraction completed", char_count=char_count)
                    logger.info(f"[INGEST] Extracted character count: {char_count}")
            elif is_pdf:
                logger.info("[INGEST] Source type detected: PDF", file=file_path.name if file_path else "")
                logger.info("[INGEST] Extracting PDF content", file=file_path.name if file_path else "")
                extracted = extract_pdf(file_path)
            else:
                unsupported_error = f"Unsupported document format: {suffix or 'unknown format'}"
                logger.error("[INGEST] Unsupported format", file=str(file_path), error=unsupported_error)
                job.status = IngestionJobStatus.FAILED
                job.error_message = unsupported_error
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
                return {"status": "failed", "error": unsupported_error, "url": entry.url}

            if not extracted.success:
                job.status = IngestionJobStatus.FAILED
                job.error_message = "; ".join(extracted.extraction_errors[:3]) or "Extraction returned empty text"
                job.completed_at = datetime.now(timezone.utc)
                await session.commit()
                return {"status": "failed", "error": job.error_message, "url": entry.url}

            # ── Step 4: Parse legal structure ─────────────────────────────────
            parsed = parse_legal_structure(
                full_text=extracted.full_text,
                document_type=entry.document_type,
            )

            # ── Step 5: Create/supersede Document record ───────────────────────
            # Mark old versions as SUPERSEDED
            old_docs = await session.execute(
                select(Document).where(
                    Document.source_id == db_source.id,
                    Document.status == DocumentStatus.CURRENT,
                )
            )
            for old_doc in old_docs.scalars():
                old_doc.status = DocumentStatus.SUPERSEDED

            db_doc = Document(
                source_id=db_source.id,
                title=entry.name,
                domain=entry.domain,
                document_type=entry.document_type,
                authority=entry.authority,
                authority_tier=AuthorityTier(entry.authority_tier),
                language=entry.language,
                status=DocumentStatus.CURRENT,
                source_url=entry.url,
                content_hash=download.content_hash,
                file_path=str(download.file_path) if download.file_path else None,
                page_count=extracted.total_pages,
            )
            session.add(db_doc)
            await session.flush()

            # ── Step 6: Create DocumentVersion record ─────────────────────────
            db_version = DocumentVersion(
                document_id=db_doc.id,
                content_hash=download.content_hash,
                download_date=datetime.now(timezone.utc),
                status=DocumentStatus.CURRENT,
            )
            session.add(db_version)
            await session.flush()

            # ── Step 7: Chunk ─────────────────────────────────────────────────
            chunks = chunk_document(
                parsed_doc=parsed,
                document_title=entry.name,
                source_url=entry.url,
                authority=entry.authority,
                domain=entry.domain,
                document_type=entry.document_type,
                language=entry.language,
                status="CURRENT",
                authority_tier=entry.authority_tier,
            )

            # ── Step 8: Embed and store ───────────────────────────────────────
            stored, dupes = await _store_chunks(
                session=session,
                chunks=chunks,
                document_id=db_doc.id,
                source_id=db_source.id,
                version_id=db_version.id,
            )

            # ── Step 9: Update job record ─────────────────────────────────────
            job.status = IngestionJobStatus.COMPLETED
            job.document_id = db_doc.id
            job.documents_processed = 1
            job.chunks_created = stored
            job.duplicates_skipped = dupes
            job.embeddings_generated = stored
            job.completed_at = datetime.now(timezone.utc)

            await session.commit()

            logger.info(
                "Ingestion complete",
                source=entry.name,
                chunks=stored,
                dupes=dupes,
            )
            return {
                "status": "success",
                "url": entry.url,
                "chunks_created": stored,
                "duplicates_skipped": dupes,
                "document_id": db_doc.id,
            }

        except Exception as exc:
            logger.error("Ingestion pipeline error", url=entry.url, error=str(exc))
            job.status = IngestionJobStatus.FAILED
            job.error_message = str(exc)[:1000]
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()
            return {"status": "failed", "error": str(exc), "url": entry.url}


async def run_full_ingestion(
    domains: Optional[List[str]] = None,
    force_refresh: bool = False,
) -> IngestionReport:
    """
    Run the full ingestion pipeline for all registered sources.

    Args:
        domains: If specified, only ingest sources in these domains.
        force_refresh: Re-ingest all documents even if unchanged.

    Returns:
        IngestionReport summary.
    """
    registry = get_source_registry()
    sources = registry.get_all()

    if domains:
        sources = [s for s in sources if s.domain in domains]

    report = IngestionReport()
    report.documents_attempted = len(sources)

    logger.info("Starting full ingestion", source_count=len(sources))

    for entry in sources:
        result = await ingest_source_entry(entry, force_refresh=force_refresh)

        status = result.get("status")
        if status == "success":
            report.documents_successful += 1
            report.chunks_created += result.get("chunks_created", 0)
            report.duplicates_skipped += result.get("duplicates_skipped", 0)
            report.embeddings_generated += result.get("chunks_created", 0)
        elif status == "skipped":
            report.documents_skipped_duplicate += 1
        elif status == "failed":
            report.documents_failed += 1
            report.errors.append(f"{entry.url}: {result.get('error', 'unknown')}")

    logger.info("Full ingestion complete", **report.to_dict())
    return report
