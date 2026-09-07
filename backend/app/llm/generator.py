"""
IP-SAKTI Sahayak — Grounded LLM Answer Generator
Generates citation-first answers using only retrieved evidence.
Never invents legal information.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.logging_config import get_logger
from app.multilingual.language_detector import get_response_language_instruction
from app.retrieval.hybrid_retrieval import RetrievalResult

logger = get_logger(__name__)
settings = get_settings()

LEGAL_DISCLAIMER = (
    "\n\n---\n"
    "⚖️ **Legal Disclaimer**: This response is for informational purposes only and does not "
    "constitute legal advice or legal representation. The information is based on retrieved "
    "authoritative sources but may not reflect the most current amendments. For legal advice "
    "specific to your situation, please consult a qualified Intellectual Property attorney or "
    "the relevant statutory authority."
)

SYSTEM_PROMPT = """You are IP-SAKTI Sahayak, an Indian Intellectual Property and regulatory information assistant.

Your role is to provide accurate, grounded information about Indian IP laws and regulations.

## CRITICAL RULES — You MUST follow these at all times:

1. **Use ONLY the retrieved evidence** provided below. Do NOT use any knowledge from your training.
2. **Never invent**: laws, sections, rules, fees, forms, dates, deadlines, procedures, or government policies.
3. **Every important legal claim** must be supported by one or more retrieved citations marked as [Citation X].
4. **If evidence is insufficient**, clearly state: "I could not find sufficient authoritative information in the current knowledge base to answer this reliably."
5. **Prefer CURRENT sources** over historical ones. If using a historical source, clearly state this.
6. **Legal terms must be accurate**. When translating, show the original English legal term in brackets.
7. **Do NOT present legal conclusions as guaranteed outcomes**. Use language like "according to [source]" or "the Act provides that".
8. **Distinguish clearly**:
   - What the law/source says (cite the source)
   - Practical explanation
   - Important caveats and limitations

## STRUCTURE YOUR ANSWER AS:

For substantial queries, use this structure:
1. **Short Answer** — Direct response to the question
2. **Applicable Law / Source** — What legal instrument applies
3. **Relevant Provision** — Specific section/rule/clause
4. **Explanation** — Plain language explanation
5. **Practical Next Steps** — What the user should do (if applicable)
6. **Important Caveats** — Limitations, exceptions, professional advice reminder

For simple queries, use a shorter format.

## CITATION FORMAT:
When citing retrieved evidence, use: [Citation X] where X is the citation number.
At the end, list all citations used in this format:
[Citation 1]: Document Title, Section/Rule X, Page Y, Authority: Z

{language_instruction}

## RETRIEVED EVIDENCE:
{evidence_block}

Remember: You MUST have retrieved evidence to support any legal claim you make."""

LOW_EVIDENCE_RESPONSE = """I could not find sufficient authoritative information in the current knowledge base to reliably answer this question.

**What this means:**
- The knowledge base may not yet contain documents covering this specific topic
- The question may fall outside the currently indexed IP domains (patents, trademarks, copyright, designs, GI, SICLD)

**What you can do:**
- Visit [IP India](https://ipindia.gov.in) directly for official information
- Contact the relevant statutory authority
- Consult a qualified Intellectual Property attorney for advice specific to your situation

⚖️ **Disclaimer**: This system provides informational guidance, not legal advice."""


@dataclass
class Citation:
    """A verified citation from retrieved evidence."""
    citation_number: int
    document_title: str
    section_no: Optional[str]
    rule_no: Optional[str]
    chapter: Optional[str]
    page_number: Optional[int]
    authority: str
    source_url: str
    chunk_id: int
    status: str = "CURRENT"
    is_current: bool = True


@dataclass
class GeneratedAnswer:
    """Complete generated answer with citations and metadata."""
    answer: str
    citations: List[Citation]
    language: str
    domain: Optional[str]
    intent: Optional[str]
    confidence: float
    evidence_level: str       # high | moderate | low | none
    retrieval_trace_id: str
    llm_latency_ms: float
    total_latency_ms: float
    warnings: List[str] = field(default_factory=list)
    has_sufficient_evidence: bool = True


def _build_evidence_block(retrieval_result: RetrievalResult) -> str:
    """Format evidence chunks for inclusion in the LLM prompt."""
    if not retrieval_result.evidence:
        return "No relevant evidence was retrieved from the knowledge base."

    blocks = []
    for i, chunk in enumerate(retrieval_result.evidence, 1):
        citation_header = f"[Evidence {i}]"
        meta_parts = []

        if chunk.document_title:
            meta_parts.append(f"Document: {chunk.document_title}")
        if chunk.chapter:
            meta_parts.append(f"Chapter: {chunk.chapter}")
        if chunk.section_no:
            meta_parts.append(f"Section: {chunk.section_no}")
        if chunk.rule_no:
            meta_parts.append(f"Rule: {chunk.rule_no}")
        if chunk.page_number:
            meta_parts.append(f"Page: {chunk.page_number}")
        if chunk.authority:
            meta_parts.append(f"Authority: {chunk.authority}")
        if chunk.status:
            meta_parts.append(f"Status: {chunk.status}")
        if chunk.source_url:
            meta_parts.append(f"Source: {chunk.source_url}")

        meta = " | ".join(meta_parts)
        content = chunk.content[:1500]  # Limit per chunk to avoid token overflow

        blocks.append(f"{citation_header}\n{meta}\n\n{content}")

    return "\n\n---\n\n".join(blocks)


def _extract_citations_from_evidence(
    retrieval_result: RetrievalResult,
) -> List[Citation]:
    """Build citation objects directly from retrieved evidence chunks."""
    citations = []
    for i, chunk in enumerate(retrieval_result.evidence, 1):
        citation = Citation(
            citation_number=i,
            document_title=chunk.document_title or "Unknown Document",
            section_no=chunk.section_no,
            rule_no=chunk.rule_no,
            chapter=chunk.chapter,
            page_number=chunk.page_number,
            authority=chunk.authority or "Unknown",
            source_url=chunk.source_url or "",
            chunk_id=chunk.chunk_id,
            status=chunk.status or "CURRENT",
            is_current=(chunk.status in ("CURRENT", None)),
        )
        citations.append(citation)
    return citations


async def generate_answer(
    query: str,
    retrieval_result: RetrievalResult,
    language: str = "en",
    domain: Optional[str] = None,
    intent: Optional[str] = None,
) -> GeneratedAnswer:
    """
    Generate a grounded, citation-first answer from retrieved evidence.

    Args:
        query: The user's original query.
        retrieval_result: Full retrieval result with evidence chunks.
        language: User's language code.
        domain: Classified IP domain.
        intent: Classified intent.

    Returns:
        GeneratedAnswer with answer text, citations, and metadata.
    """
    start = time.monotonic()
    warnings = []

    # ── Low evidence fallback ─────────────────────────────────────────────────
    if not retrieval_result.evidence or retrieval_result.evidence_level == "low":
        low_evidence_threshold = settings.moderate_evidence_threshold

        if retrieval_result.confidence < low_evidence_threshold or not retrieval_result.evidence:
            lang_instruction = get_response_language_instruction(language)
            fallback_answer = LOW_EVIDENCE_RESPONSE

            total_ms = round((time.monotonic() - start) * 1000, 2)
            return GeneratedAnswer(
                answer=fallback_answer + LEGAL_DISCLAIMER,
                citations=[],
                language=language,
                domain=domain,
                intent=intent,
                confidence=retrieval_result.confidence,
                evidence_level="low",
                retrieval_trace_id=retrieval_result.trace_id,
                llm_latency_ms=0.0,
                total_latency_ms=total_ms,
                warnings=["Insufficient evidence — fallback response returned"],
                has_sufficient_evidence=False,
            )

    # ── Warn about non-current sources ───────────────────────────────────────
    for chunk in retrieval_result.evidence:
        if chunk.status and chunk.status not in ("CURRENT",):
            warnings.append(
                f"Note: Evidence from '{chunk.document_title}' has status: {chunk.status}. "
                "Verify against the current official source."
            )

    # ── Build evidence block and citations ────────────────────────────────────
    evidence_block = _build_evidence_block(retrieval_result)
    citations = _extract_citations_from_evidence(retrieval_result)
    lang_instruction = get_response_language_instruction(language)

    system_prompt = SYSTEM_PROMPT.format(
        language_instruction=lang_instruction,
        evidence_block=evidence_block,
    )

    user_message = (
        f"User Query: {query}\n\n"
        f"Domain: {domain or 'general'}\n"
        f"Intent: {intent or 'general_ip_guidance'}\n\n"
        "Please provide a grounded answer using only the retrieved evidence above."
    )

    # ── LLM call ──────────────────────────────────────────────────────────────
    llm_start = time.monotonic()

    try:
        import openai

        client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
        )

        response = await client.chat.completions.create(
            model=settings.llm_model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

        answer_text = response.choices[0].message.content
        llm_latency_ms = round((time.monotonic() - llm_start) * 1000, 2)

        # Append legal disclaimer
        answer_text = answer_text + LEGAL_DISCLAIMER

    except Exception as exc:
        logger.error("LLM generation failed", error=str(exc))
        warnings.append(f"LLM generation error: {str(exc)[:100]}")
        # Graceful degradation: return evidence summary without LLM
        answer_text = _fallback_evidence_summary(
            query, retrieval_result, language
        ) + LEGAL_DISCLAIMER
        llm_latency_ms = 0.0

    total_latency_ms = round((time.monotonic() - start) * 1000, 2)

    return GeneratedAnswer(
        answer=answer_text,
        citations=citations,
        language=language,
        domain=domain,
        intent=intent,
        confidence=retrieval_result.confidence,
        evidence_level=retrieval_result.evidence_level,
        retrieval_trace_id=retrieval_result.trace_id,
        llm_latency_ms=llm_latency_ms,
        total_latency_ms=total_latency_ms,
        warnings=warnings,
        has_sufficient_evidence=True,
    )


def _fallback_evidence_summary(
    query: str,
    retrieval_result: RetrievalResult,
    language: str,
) -> str:
    """
    Create a plain evidence summary when LLM is unavailable.
    Shows retrieved passages without LLM explanation.
    """
    lines = [
        f"**Retrieved Evidence for your query** (LLM generation temporarily unavailable)\n",
        f"Query: {query}\n",
    ]

    for i, chunk in enumerate(retrieval_result.evidence[:3], 1):
        title = chunk.document_title or "Unknown Document"
        section = f"Section {chunk.section_no}" if chunk.section_no else (
            f"Rule {chunk.rule_no}" if chunk.rule_no else "")
        lines.append(f"\n---\n**{title}** {section}")
        lines.append(chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content)
        if chunk.source_url:
            lines.append(f"Source: {chunk.source_url}")

    return "\n".join(lines)
