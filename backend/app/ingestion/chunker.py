"""
IP-SAKTI Sahayak — Section-Aware Legal Document Chunker
Splits legal text into chunks that respect legal boundaries.

Chunking strategy:
  1. Use legal provisions (sections/rules) as natural boundaries.
  2. Target 500–1200 tokens per chunk, legal boundaries have priority.
  3. Apply 100-token overlap only at section boundaries.
  4. Preserve full legal metadata on every chunk.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.ingestion.legal_parser import LegalProvision, ParsedDocument
from app.logging_config import get_logger

logger = get_logger(__name__)

# Token estimator: rough approximation (1 token ≈ 4 chars for English, 3 for Indic)
CHARS_PER_TOKEN = 4
TARGET_MIN_TOKENS = 500
TARGET_MAX_TOKENS = 1200
OVERLAP_TOKENS = 100

TARGET_MIN_CHARS = TARGET_MIN_TOKENS * CHARS_PER_TOKEN    # 2000
TARGET_MAX_CHARS = TARGET_MAX_TOKENS * CHARS_PER_TOKEN    # 4800
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN          # 400


@dataclass
class LegalChunk:
    """
    A single chunk ready for embedding and storage.
    Contains full legal provenance metadata.
    """
    content: str
    content_hash: str
    chunk_index: int

    # Document identity
    document_title: str
    source_url: str
    authority: str
    domain: str
    document_type: str
    language: str = "en"

    # Legal structure
    chapter: Optional[str] = None
    section_no: Optional[str] = None
    subsection_no: Optional[str] = None
    rule_no: Optional[str] = None
    clause_no: Optional[str] = None
    form_no: Optional[str] = None
    schedule_no: Optional[str] = None
    title: Optional[str] = None

    # Pagination / version
    page_number: Optional[int] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    version_label: Optional[str] = None
    status: str = "CURRENT"
    authority_tier: str = "TIER_1"

    @property
    def token_count(self) -> int:
        return len(self.content) // CHARS_PER_TOKEN

    def to_citation_string(self) -> str:
        """Return a human-readable citation for this chunk."""
        parts = [self.document_title]
        if self.chapter:
            parts.append(f"Chapter {self.chapter}")
        if self.section_no:
            parts.append(f"Section {self.section_no}")
        if self.rule_no:
            parts.append(f"Rule {self.rule_no}")
        if self.page_number:
            parts.append(f"p. {self.page_number}")
        return " — ".join(parts)


def _compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _split_long_provision(text: str, max_chars: int, overlap_chars: int) -> List[str]:
    """
    Split a long provision into sub-chunks at paragraph/sentence boundaries.
    Used when a single provision exceeds TARGET_MAX_CHARS.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars

        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        # Try to break at paragraph boundary
        split_pos = text.rfind("\n\n", start + max_chars // 2, end)
        if split_pos == -1:
            # Try sentence boundary
            split_pos = text.rfind(". ", start + max_chars // 2, end)
            if split_pos == -1:
                # Hard split
                split_pos = end

        chunks.append(text[start:split_pos + 1].strip())
        start = max(split_pos - overlap_chars, start + 1)

    return [c for c in chunks if c.strip()]


def chunk_document(
    parsed_doc: ParsedDocument,
    document_title: str,
    source_url: str,
    authority: str,
    domain: str,
    document_type: str,
    language: str = "en",
    status: str = "CURRENT",
    version_label: Optional[str] = None,
    effective_from: Optional[str] = None,
    effective_to: Optional[str] = None,
    authority_tier: str = "TIER_1",
) -> List[LegalChunk]:
    """
    Convert parsed legal provisions into retrieval-ready chunks.

    Strategy:
    1. Small provisions (< TARGET_MIN_CHARS) are merged with neighbors
       of the same chapter to create meaningful chunks.
    2. Large provisions (> TARGET_MAX_CHARS) are split at paragraph/sentence
       boundaries with OVERLAP_CHARS overlap.
    3. Every chunk retains its legal hierarchy metadata.
    """
    all_chunks: List[LegalChunk] = []
    chunk_index = 0

    def make_chunk(
        content: str,
        provision: LegalProvision,
        sub_index: int = 0,
    ) -> Optional[LegalChunk]:
        nonlocal chunk_index
        cleaned = content.strip()
        if not cleaned or len(cleaned) < 20:
            return None

        c = LegalChunk(
            content=cleaned,
            content_hash=_compute_hash(cleaned),
            chunk_index=chunk_index,
            document_title=document_title,
            source_url=source_url,
            authority=authority,
            domain=domain,
            document_type=document_type,
            language=language,
            chapter=provision.chapter,
            section_no=provision.section_no,
            rule_no=provision.rule_no,
            title=provision.title,
            page_number=provision.page_number,
            effective_from=effective_from,
            effective_to=effective_to,
            version_label=version_label,
            status=status,
            authority_tier=authority_tier,
        )
        chunk_index += 1
        return c

    # ── Group and chunk provisions ────────────────────────────────────────────
    buffer_text = ""
    buffer_provision: Optional[LegalProvision] = None

    for provision in parsed_doc.provisions:
        text = provision.text

        # If the provision is itself too long, flush buffer and split this provision
        if len(text) > TARGET_MAX_CHARS:
            # Flush buffer
            if buffer_text and buffer_provision:
                c = make_chunk(buffer_text, buffer_provision)
                if c:
                    all_chunks.append(c)
                buffer_text = ""
                buffer_provision = None

            # Split the long provision
            sub_texts = _split_long_provision(text, TARGET_MAX_CHARS, OVERLAP_CHARS)
            for sub_text in sub_texts:
                c = make_chunk(sub_text, provision)
                if c:
                    all_chunks.append(c)
            continue

        # If provision fits in buffer, accumulate
        candidate = (buffer_text + "\n\n" + text).strip() if buffer_text else text

        if len(candidate) <= TARGET_MAX_CHARS:
            buffer_text = candidate
            if buffer_provision is None:
                buffer_provision = provision
        else:
            # Flush current buffer
            if buffer_text and buffer_provision:
                c = make_chunk(buffer_text, buffer_provision)
                if c:
                    all_chunks.append(c)

            # Start new buffer with overlap from end of previous buffer
            overlap = buffer_text[-OVERLAP_CHARS:] if buffer_text else ""
            buffer_text = (overlap + "\n\n" + text).strip() if overlap else text
            buffer_provision = provision

    # Flush remaining buffer
    if buffer_text and buffer_provision:
        c = make_chunk(buffer_text, buffer_provision)
        if c:
            all_chunks.append(c)

    # Remove duplicate chunks (same content hash)
    seen_hashes = set()
    unique_chunks = []
    for chunk in all_chunks:
        if chunk.content_hash not in seen_hashes:
            seen_hashes.add(chunk.content_hash)
            unique_chunks.append(chunk)

    logger.info(
        "Chunking complete",
        document=document_title[:60],
        total_chunks=len(unique_chunks),
        avg_tokens=sum(c.token_count for c in unique_chunks) // max(len(unique_chunks), 1),
    )
    return unique_chunks
