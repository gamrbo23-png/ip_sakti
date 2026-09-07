"""
IP-SAKTI Sahayak — Legal Structure Parser
Detects chapters, sections, rules, subsections, schedules, and forms in Indian legal text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from app.logging_config import get_logger

logger = get_logger(__name__)


# ── Regex patterns for Indian legal structure ─────────────────────────────────

# Chapter patterns: "CHAPTER I", "CHAPTER 1 —", "Chapter I.", etc.
CHAPTER_RE = re.compile(
    r"^(?:CHAPTER|Chapter)\s+([IVXLCDM]+|\d+)\b[.\s—:-]*(.*)$",
    re.MULTILINE,
)

# Section patterns: "Section 18", "Section 18.", "SECTION 18 —", "18."  at line start
SECTION_RE = re.compile(
    r"^(?:Section|SECTION|Sec\.?)\s+(\d+[A-Za-z]?)\b[.\s—:-]*(.*)$",
    re.MULTILINE,
)

# Rule patterns: "Rule 23", "RULE 23 —", "23. Conditions for ..."
RULE_RE = re.compile(
    r"^(?:Rule|RULE|r\.)\s+(\d+[A-Za-z]?)\b[.\s—:-]*(.*)$",
    re.MULTILINE,
)

# Sub-rule patterns: "(1)", "(1)(a)", "(2)" at start of line
SUBRULE_RE = re.compile(
    r"^\((\d+[a-zA-Z]?)\)\s+",
    re.MULTILINE,
)

# Clause / sub-clause: "(a)", "(b)" at line start
CLAUSE_RE = re.compile(
    r"^\s*\(([a-z])\)\s+",
    re.MULTILINE,
)

# Schedule patterns
SCHEDULE_RE = re.compile(
    r"^(?:THE\s+)?(?:SCHEDULE|Schedule|FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)\s+SCHEDULE\b",
    re.MULTILINE,
)

# Form patterns: "FORM TM-1", "Form No. 1", "FORM A", etc.
FORM_RE = re.compile(
    r"^(?:FORM|Form)\s+(?:No\.?\s*)?([A-Z0-9][A-Z0-9\-]*)\b",
    re.MULTILINE,
)

# Article patterns (for Constitutions / regulations)
ARTICLE_RE = re.compile(
    r"^(?:Article|ARTICLE)\s+(\d+[A-Za-z]?)\b[.\s—:-]*(.*)$",
    re.MULTILINE,
)


@dataclass
class LegalProvision:
    """
    Represents a single identified legal provision within a document.
    """
    provision_type: str         # chapter | section | rule | subrule | clause | schedule | form | article
    number: Optional[str]       # "18", "23", "I", "(1)", "(a)", etc.
    title: Optional[str]        # Heading text, if present
    text: str                   # The full text of this provision
    page_number: Optional[int]
    start_char: int             # Character offset in the document
    end_char: int
    chapter: Optional[str] = None
    section_no: Optional[str] = None
    rule_no: Optional[str] = None
    subsection_no: Optional[str] = None
    clause_no: Optional[str] = None
    schedule_no: Optional[str] = None
    form_no: Optional[str] = None


@dataclass
class ParsedDocument:
    """Result of parsing legal structure from extracted document text."""
    provisions: List[LegalProvision] = field(default_factory=list)
    chapter_map: dict = field(default_factory=dict)   # chapter_number -> title
    full_text: str = ""
    parse_warnings: List[str] = field(default_factory=list)


def parse_legal_structure(
    full_text: str,
    document_type: str = "act",
    page_map: Optional[dict] = None,  # char_offset -> page_number
) -> ParsedDocument:
    """
    Parse the legal structure of a document.

    Args:
        full_text: Full text of the document.
        document_type: Type hint (act, rules, etc.) to guide parsing.
        page_map: Optional mapping of character offsets to page numbers.

    Returns:
        ParsedDocument with identified provisions and their metadata.
    """
    result = ParsedDocument(full_text=full_text)
    lines = full_text.split("\n")

    # Build a simple char-offset-to-page-number lookup
    def get_page(offset: int) -> Optional[int]:
        if not page_map:
            return None
        # Find the page that contains this offset
        for char_offset, page in sorted(page_map.items()):
            if offset <= char_offset:
                return page
        return max(page_map.values()) if page_map else None

    # ── Pass 1: Identify chapter headings ────────────────────────────────────
    current_chapter: Optional[str] = None
    current_chapter_title: Optional[str] = None
    current_section: Optional[str] = None
    current_rule: Optional[str] = None

    # Parse as a single block — find all structural markers with their positions
    provisions: List[LegalProvision] = []
    current_offset = 0
    prev_provision_end = 0

    # Find all structural boundaries
    boundaries: List[Tuple[int, str, str, str]] = []  # (start, type, number, title)

    for match in CHAPTER_RE.finditer(full_text):
        boundaries.append((match.start(), "chapter", match.group(1), match.group(2).strip()))

    for match in SECTION_RE.finditer(full_text):
        boundaries.append((match.start(), "section", match.group(1), match.group(2).strip()))

    for match in RULE_RE.finditer(full_text):
        boundaries.append((match.start(), "rule", match.group(1), match.group(2).strip()))

    for match in SCHEDULE_RE.finditer(full_text):
        boundaries.append((match.start(), "schedule", match.group(0).strip(), ""))

    for match in FORM_RE.finditer(full_text):
        boundaries.append((match.start(), "form", match.group(1), ""))

    for match in ARTICLE_RE.finditer(full_text):
        boundaries.append((match.start(), "article", match.group(1), match.group(2).strip()))

    # Sort boundaries by position
    boundaries.sort(key=lambda x: x[0])

    if not boundaries:
        # No structure detected — treat entire text as one block
        result.parse_warnings.append("No legal structure detected; treating as plain text")
        provisions.append(LegalProvision(
            provision_type="text",
            number=None,
            title=None,
            text=full_text.strip(),
            page_number=1,
            start_char=0,
            end_char=len(full_text),
        ))
        result.provisions = provisions
        return result

    # ── Pass 2: Extract text between boundaries ───────────────────────────────
    _chapter = None
    _section = None
    _rule = None

    for i, (start, ptype, number, title) in enumerate(boundaries):
        # End of this provision = start of next boundary (or end of text)
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(full_text)
        text = full_text[start:end].strip()

        if not text:
            continue

        # Track context
        if ptype == "chapter":
            _chapter = number
            result.chapter_map[number] = title
            _section = None
            _rule = None
        elif ptype == "section":
            _section = number
        elif ptype == "rule":
            _rule = number

        provision = LegalProvision(
            provision_type=ptype,
            number=number,
            title=title or None,
            text=text,
            page_number=get_page(start),
            start_char=start,
            end_char=end,
            chapter=_chapter,
            section_no=_section if ptype == "section" else None,
            rule_no=_rule if ptype == "rule" else None,
        )

        # Detect subsections within the provision text
        if ptype in ("section", "rule"):
            provision.section_no = number if ptype == "section" else None
            provision.rule_no = number if ptype == "rule" else None

        provisions.append(provision)

    result.provisions = provisions
    logger.info(
        "Legal structure parsed",
        total_provisions=len(provisions),
        chapters=len(result.chapter_map),
        document_type=document_type,
    )
    return result
