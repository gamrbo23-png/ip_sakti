"""
IP-SAKTI Sahayak — PDF Text Extraction
Uses PyMuPDF for primary extraction with pytesseract OCR fallback for scanned pages.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Minimum text characters per page to consider it "text-based" (not scanned)
MIN_TEXT_CHARS_PER_PAGE = 50


@dataclass
class PageContent:
    """Extracted content of a single PDF page."""
    page_number: int        # 1-indexed
    text: str
    is_ocr: bool = False
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.text.split())


@dataclass
class ExtractedDocument:
    """Full extracted content of a PDF document."""
    file_path: str
    pages: List[PageContent] = field(default_factory=list)
    total_pages: int = 0
    ocr_pages: int = 0
    extraction_errors: List[str] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Concatenate all page texts."""
        return "\n\n".join(
            f"[Page {p.page_number}]\n{p.text}"
            for p in self.pages
            if p.text.strip()
        )

    @property
    def success(self) -> bool:
        return len(self.pages) > 0


def _clean_text(text: str) -> str:
    """
    Clean extracted PDF text:
    - Normalize whitespace
    - Remove excessive line breaks
    - Remove null bytes
    - Preserve Indian language characters
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive whitespace while preserving paragraph structure
    lines = text.split("\n")
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not prev_empty:
                cleaned_lines.append("")
            prev_empty = True
        else:
            cleaned_lines.append(stripped)
            prev_empty = False

    text = "\n".join(cleaned_lines).strip()

    # Collapse more than 2 consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def extract_pdf(file_path: Path) -> ExtractedDocument:
    """
    Extract text from a PDF using PyMuPDF.
    Falls back to OCR (pytesseract) for pages with insufficient text.

    Args:
        file_path: Path to the PDF file.

    Returns:
        ExtractedDocument with page-level content and metadata.
    """
    result = ExtractedDocument(file_path=str(file_path))

    try:
        import fitz  # PyMuPDF
    except ImportError:
        result.extraction_errors.append("PyMuPDF (fitz) not installed")
        logger.error("PyMuPDF not available")
        return result

    try:
        doc = fitz.open(str(file_path))
        result.total_pages = doc.page_count

        for page_idx in range(doc.page_count):
            page_num = page_idx + 1
            try:
                page = doc[page_idx]

                # Primary extraction: direct text
                text = page.get_text("text")
                is_ocr = False

                # If page has too little text, try OCR
                if len(text.strip()) < MIN_TEXT_CHARS_PER_PAGE:
                    text = _ocr_page(page, page_num)
                    if text:
                        is_ocr = True
                        result.ocr_pages += 1
                    else:
                        text = ""  # Empty page

                cleaned = _clean_text(text)
                if cleaned:
                    result.pages.append(PageContent(
                        page_number=page_num,
                        text=cleaned,
                        is_ocr=is_ocr,
                    ))

            except Exception as exc:
                error_msg = f"Error on page {page_num}: {exc}"
                result.extraction_errors.append(error_msg)
                logger.warning("Page extraction error", page=page_num, error=str(exc))

        doc.close()
        logger.info(
            "PDF extracted",
            file=file_path.name,
            total_pages=result.total_pages,
            extracted_pages=len(result.pages),
            ocr_pages=result.ocr_pages,
        )

    except Exception as exc:
        result.extraction_errors.append(f"Failed to open PDF: {exc}")
        logger.error("PDF extraction failed", file=str(file_path), error=str(exc))

    return result


def _ocr_page(page, page_num: int) -> str:
    """
    Perform OCR on a single PDF page using pytesseract.
    Renders the page at 300 DPI then runs Tesseract.
    """
    try:
        import fitz
        import pytesseract
        from PIL import Image
        import io

        # Render page at 300 DPI for good OCR quality
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))

        # OCR with Indian language support
        lang = settings.ocr_language
        text = pytesseract.image_to_string(img, lang=lang)
        logger.debug("OCR completed", page=page_num, chars=len(text))
        return text

    except ImportError:
        logger.warning("pytesseract or Pillow not available — OCR skipped")
        return ""
    except Exception as exc:
        logger.warning("OCR failed on page", page=page_num, error=str(exc))
        return ""
