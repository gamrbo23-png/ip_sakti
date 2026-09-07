"""
IP-SAKTI Sahayak — Intent & Domain Classifier
Classifies user queries into IP domains and action intents using an LLM call.
Fast, lightweight classification before full RAG pipeline.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

SUPPORTED_INTENTS = [
    "definition", "eligibility", "registration", "procedure",
    "documents", "fees", "timeline", "renewal", "opposition",
    "infringement", "ownership", "licensing", "assignment",
    "compliance", "comparison", "source_lookup", "amendment_lookup",
    "regulatory_guidance", "general_ip_guidance",
]

SUPPORTED_DOMAINS = [
    "patent", "trademark", "copyright", "design", "gi",
    "sicld", "startup", "data_protection", "regulatory_general", "unknown",
]

CLASSIFICATION_PROMPT = """You are a classification engine for an Indian IP law assistant.

Analyze the following user query and return a JSON object with these exact fields:
- "intent": one of {intents}
- "domain": one or more of {domains} (return as array, up to 3)
- "primary_domain": the single most likely domain
- "requires_current_rules": true if the query asks about current procedures/fees/deadlines
- "has_section_reference": true if the query mentions a specific section/rule/form number
- "confidence": your confidence from 0.0 to 1.0

Query: {query}

Respond with ONLY valid JSON, nothing else."""


@dataclass
class ClassificationResult:
    """Result of intent and domain classification."""
    intent: str
    domain: str               # Primary domain
    all_domains: List[str]    # All relevant domains
    requires_current_rules: bool
    has_section_reference: bool
    confidence: float


async def classify_intent_and_domain(
    query: str,
    language: str = "en",
) -> ClassificationResult:
    """
    Classify the user's query into intent and IP domain.

    Uses a fast LLM call with structured output.
    Falls back to heuristics if LLM is unavailable.

    Args:
        query: User's original query.
        language: Detected language code.

    Returns:
        ClassificationResult with intent and domain.
    """
    # First try heuristic classification (fast, no API call)
    heuristic = _heuristic_classify(query)
    if heuristic.confidence >= 0.8:
        logger.debug("Heuristic classification", **vars(heuristic))
        return heuristic

    # Try LLM classification
    try:
        import openai

        client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
        )

        prompt = CLASSIFICATION_PROMPT.format(
            intents=", ".join(SUPPORTED_INTENTS),
            domains=", ".join(SUPPORTED_DOMAINS),
            query=query[:500],  # Truncate long queries
        )

        response = await client.chat.completions.create(
            model=settings.llm_model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        intent = data.get("intent", "general_ip_guidance")
        if intent not in SUPPORTED_INTENTS:
            intent = "general_ip_guidance"

        domains = data.get("domain", ["unknown"])
        if isinstance(domains, str):
            domains = [domains]
        valid_domains = [d for d in domains if d in SUPPORTED_DOMAINS]
        if not valid_domains:
            valid_domains = ["unknown"]

        primary = data.get("primary_domain", valid_domains[0])
        if primary not in SUPPORTED_DOMAINS:
            primary = valid_domains[0]

        return ClassificationResult(
            intent=intent,
            domain=primary,
            all_domains=valid_domains,
            requires_current_rules=data.get("requires_current_rules", True),
            has_section_reference=data.get("has_section_reference", False),
            confidence=min(float(data.get("confidence", 0.7)), 1.0),
        )

    except Exception as exc:
        logger.warning("LLM classification failed, using heuristic", error=str(exc))
        return heuristic


def _heuristic_classify(query: str) -> ClassificationResult:
    """
    Fast heuristic classification based on keyword matching.
    Used as fallback when LLM is unavailable.
    """
    q = query.lower()

    # Domain keywords
    domain_keywords = {
        "patent": ["patent", "invention", "invent", "technical", "process", "product", "पेटेंट"],
        "trademark": ["trademark", "trade mark", "brand", "logo", "mark", "ट्रेडमार्क", "ব্র্যান্ড"],
        "copyright": ["copyright", "creative", "author", "book", "software", "music", "कॉपीराइट"],
        "design": ["design", "appearance", "shape", "pattern", "डिजाइन"],
        "gi": ["geographical indication", "gi", "origin", "region", "darjeeling"],
        "startup": ["startup", "dpiit", "company", "incorporation", "स्टार्टअप"],
        "data_protection": ["data protection", "privacy", "personal data", "dpdp", "डेटा"],
    }

    intent_keywords = {
        "registration": ["register", "registration", "apply", "application", "file", "filing", "रजिस्टर"],
        "fees": ["fee", "cost", "charge", "price", "pay", "शुल्क"],
        "timeline": ["time", "duration", "how long", "days", "months", "years", "deadline"],
        "procedure": ["procedure", "process", "step", "how to", "कैसे", "process"],
        "eligibility": ["eligible", "qualify", "who can", "eligibility", "criteria"],
        "definition": ["what is", "define", "definition", "meaning", "क्या है"],
        "comparison": ["difference", "vs", "versus", "compare", "better", "which"],
        "source_lookup": ["section", "rule", "form", "act", "schedule"],
        "renewal": ["renew", "renewal", "extend", "expiry", "nवीनीकरण"],
        "infringement": ["infringement", "violation", "copy", "piracy", "infringe"],
    }

    # Score domains
    domain_scores = {d: 0 for d in SUPPORTED_DOMAINS}
    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if kw in q:
                domain_scores[domain] += 1

    best_domain = max(domain_scores, key=domain_scores.get)
    domain_confidence = min(domain_scores[best_domain] / 2.0, 1.0)

    if domain_scores[best_domain] == 0:
        best_domain = "unknown"

    # Score intents
    intent_scores = {i: 0 for i in SUPPORTED_INTENTS}
    for intent, keywords in intent_keywords.items():
        for kw in keywords:
            if kw in q:
                intent_scores[intent] += 1

    best_intent = max(intent_scores, key=intent_scores.get)
    if intent_scores[best_intent] == 0:
        best_intent = "general_ip_guidance"

    # Determine all relevant domains
    all_domains = [d for d, s in domain_scores.items() if s > 0] or ["unknown"]

    has_section_ref = any(ref in q for ref in ["section", "rule", "form", "schedule"])
    requires_current = any(kw in q for kw in ["current", "now", "today", "2024", "2025", "fee", "cost"])

    confidence = domain_confidence if best_domain != "unknown" else 0.3

    return ClassificationResult(
        intent=best_intent,
        domain=best_domain,
        all_domains=all_domains,
        requires_current_rules=requires_current,
        has_section_reference=has_section_ref,
        confidence=confidence,
    )
