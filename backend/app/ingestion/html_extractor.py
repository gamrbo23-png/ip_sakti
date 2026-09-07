"""
IP-SAKTI Sahayak — HTML/Webpage Text Extraction
Extracts clean, readable, structured text from official HTML/ASP government webpages
for RAG ingestion (TKDL, IP India, official portals).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

from bs4 import BeautifulSoup, Comment

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Tags that contain non-content or interactive code
UNWANTED_TAGS = [
    "script",
    "style",
    "noscript",
    "nav",
    "footer",
    "header",
    "iframe",
    "svg",
    "canvas",
    "object",
    "embed",
    "applet",
    "meta",
    "link",
    "form",
    "button",
    "select",
    "option",
]

# Common CSS classes/ids used for boilerplate navigation, banners, and modals
BOILERPLATE_PATTERNS = [
    "cookie-banner",
    "privacy-popup",
    "site-nav",
    "navbar",
    "top-nav",
    "main-nav",
    "sidebar-nav",
    "breadcrumb",
    "breadcrumbs",
    "site-footer",
    "modal",
    "popup",
    "social-share",
]


@dataclass
class PageContent:
    """Extracted content of an HTML document section or page."""
    page_number: int        # 1-indexed (1 for single HTML page)
    text: str
    is_ocr: bool = False
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.text.split())


@dataclass
class ExtractedDocument:
    """Full extracted content of an HTML/webpage document (compatible with pdf_extractor)."""
    file_path: str
    pages: List[PageContent] = field(default_factory=list)
    total_pages: int = 0
    ocr_pages: int = 0
    extraction_errors: List[str] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Concatenate all page texts."""
        return "\n\n".join(
            p.text
            for p in self.pages
            if p.text.strip()
        )

    @property
    def success(self) -> bool:
        return len(self.pages) > 0 and bool(self.full_text.strip())


def _clean_text(text: str) -> str:
    """
    Clean and normalize extracted HTML text:
    - Replace non-breaking spaces with standard space
    - Remove null bytes
    - Normalize line endings
    - Collapse excessive horizontal spaces and blank lines
    - Preserve Indian language characters
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # Replace non-breaking spaces
    text = text.replace("\xa0", " ").replace("&nbsp;", " ")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Clean line by line
    lines = text.split("\n")
    cleaned_lines = []
    prev_empty = False

    for line in lines:
        # Collapse multiple horizontal whitespace characters
        line_clean = re.sub(r"[ \t]+", " ", line).strip()
        if not line_clean:
            if not prev_empty:
                cleaned_lines.append("")
            prev_empty = True
        else:
            cleaned_lines.append(line_clean)
            prev_empty = False

    text = "\n".join(cleaned_lines).strip()

    # Collapse 3 or more consecutive newlines into double newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def _remove_boilerplate(soup: BeautifulSoup) -> None:
    """Remove comments, non-content tags, and common web boilerplate elements."""
    # 1. Remove HTML comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # 2. Decompose unwanted tags
    for tag_name in UNWANTED_TAGS:
        for element in soup.find_all(tag_name):
            element.decompose()

    # 3. Remove elements with boilerplate class or id attributes
    for element in soup.find_all(True):
        if not element.attrs:
            continue
        classes = element.get("class", [])
        if isinstance(classes, list):
            classes_str = " ".join(classes)
        else:
            classes_str = str(classes)
        el_id = str(element.get("id", ""))
        combined_meta = f"{classes_str} {el_id}".lower()

        if any(pat in combined_meta for pat in BOILERPLATE_PATTERNS):
            element.decompose()


def _format_html_structure(soup: BeautifulSoup) -> None:
    """
    Format semantic HTML elements to preserve logical line breaks,
    headings, lists, and tables before converting to raw text.
    """
    # Replace line breaks
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # Format table rows: tabulate cells with pipes
    for tr in soup.find_all("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in tr.find_all(["td", "th"])]
        if any(cells):
            tr.replace_with(f"\n| {' | '.join(cells)} |\n")

    # Format list items
    for li in soup.find_all("li"):
        li_text = li.get_text(" ", strip=True)
        if li_text:
            li.replace_with(f"\n• {li_text}\n")

    # Format headings
    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        h_text = h.get_text(" ", strip=True)
        if h_text:
            h.replace_with(f"\n\n{h_text}\n\n")

    # Format paragraphs and blockquotes
    for p in soup.find_all(["p", "blockquote"]):
        p_text = p.get_text(" ", strip=True)
        if p_text:
            p.replace_with(f"\n\n{p_text}\n\n")


def extract_html_content(raw_content: str, source_name: str = "raw_html") -> ExtractedDocument:
    """
    Extract clean, structured text directly from raw HTML string content.

    Args:
        raw_content: String containing raw HTML markup.
        source_name: Optional label for the source (for error/logging context).

    Returns:
        ExtractedDocument object compatible with the IP-SAKTI ingestion pipeline.
    """
    result = ExtractedDocument(file_path=source_name)

    if not raw_content or not raw_content.strip():
        error_msg = "HTML content is empty"
        result.extraction_errors.append(error_msg)
        logger.warning("[HTML_EXTRACTOR] Empty HTML content", source=source_name)
        return result

    # 1. Parse HTML content using BeautifulSoup with lxml
    logger.info("[HTML_EXTRACTOR] Parsing HTML content", file=source_name)
    try:
        soup = BeautifulSoup(raw_content, "lxml")
    except Exception as parse_exc:
        logger.warning("[HTML_EXTRACTOR] lxml parser failed, falling back to html.parser", error=str(parse_exc))
        try:
            soup = BeautifulSoup(raw_content, "html.parser")
        except Exception as fallback_exc:
            error_msg = f"HTML parsing failed: {fallback_exc}"
            result.extraction_errors.append(error_msg)
            logger.error("[HTML_EXTRACTOR] Parsing failed", source=source_name, error=str(fallback_exc))
            return result

    # 2. Remove boilerplate elements
    logger.info("[HTML_EXTRACTOR] Removing boilerplate elements", file=source_name)
    _remove_boilerplate(soup)

    # 3. Format semantic structure (headings, tables, lists, line breaks)
    _format_html_structure(soup)

    # 4. Extract raw text
    root_target = soup.body if soup.body else soup
    extracted_raw = root_target.get_text(separator="\n")

    # 5. Clean and normalize whitespace
    cleaned_text = _clean_text(extracted_raw)

    if not cleaned_text:
        error_msg = "No readable text extracted from HTML content"
        result.extraction_errors.append(error_msg)
        logger.warning("[HTML_EXTRACTOR] No readable text found", source=source_name)
        return result

    # 6. Assemble ExtractedDocument
    page_content = PageContent(
        page_number=1,
        text=cleaned_text,
        is_ocr=False,
    )
    result.pages.append(page_content)
    result.total_pages = 1
    result.ocr_pages = 0

    char_count = len(cleaned_text)
    word_count = page_content.word_count

    logger.info(
        "[HTML_EXTRACTOR] Text extraction completed",
        file=source_name,
        char_count=char_count,
        word_count=word_count,
    )
    logger.info(f"[HTML_EXTRACTOR] Extracted character count: {char_count}")

    return result


def extract_html(file_path_or_content: Union[str, Path]) -> ExtractedDocument:
    """
    Extract clean, structured text from an HTML or ASP webpage file (or raw HTML content).

    Args:
        file_path_or_content: Local path to the downloaded HTML/ASP file, or raw HTML string.

    Returns:
        ExtractedDocument object compatible with the IP-SAKTI ingestion pipeline.
    """
    # If a raw HTML markup string is passed directly
    if isinstance(file_path_or_content, str) and (
        file_path_or_content.strip().startswith("<")
        or ("<html" in file_path_or_content.lower())
    ):
        return extract_html_content(file_path_or_content, source_name="raw_html_string")

    path_obj = Path(file_path_or_content)
    result = ExtractedDocument(file_path=str(path_obj))

    # 1. Verify file exists
    if not path_obj.exists():
        error_msg = f"HTML file not found: {path_obj}"
        result.extraction_errors.append(error_msg)
        logger.error("[HTML_EXTRACTOR] File not found", path=str(path_obj))
        return result

    if not path_obj.is_file():
        error_msg = f"Path is not a regular file: {path_obj}"
        result.extraction_errors.append(error_msg)
        logger.error("[HTML_EXTRACTOR] Invalid file path", path=str(path_obj))
        return result

    # 2. Read HTML file safely with encoding fallbacks
    logger.info("[HTML_EXTRACTOR] Reading HTML file", file=path_obj.name, path=str(path_obj))
    raw_content = None
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]:
        try:
            with open(path_obj, "r", encoding=encoding, errors="strict") as f:
                raw_content = f.read()
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if raw_content is None:
        try:
            # Fallback with replacement for non-standard characters
            with open(path_obj, "r", encoding="utf-8", errors="replace") as f:
                raw_content = f.read()
        except Exception as exc:
            error_msg = f"Failed to read HTML file: {exc}"
            result.extraction_errors.append(error_msg)
            logger.error("[HTML_EXTRACTOR] Read error", path=str(path_obj), error=str(exc))
            return result

    # 3. Extract content from read HTML string
    extracted = extract_html_content(raw_content, source_name=path_obj.name)
    extracted.file_path = str(path_obj)
    return extracted

