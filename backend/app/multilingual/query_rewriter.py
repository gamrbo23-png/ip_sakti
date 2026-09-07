"""
IP-SAKTI Sahayak — Query Rewriter
Generates retrieval-optimized query representations from user input.
Produces English retrieval queries even when user writes in Hindi/Bengali.
"""
from __future__ import annotations

import json
from typing import List, Optional

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

REWRITE_SYSTEM_PROMPT = """You are a legal query rewriter for an Indian IP law retrieval system.

Your task: Given a user's query (possibly in Hindi, Bengali, or other Indian languages),
generate 3-5 short English search queries that will retrieve the most relevant legal text
from Indian IP law documents.

Rules:
- Always generate queries in ENGLISH for retrieval (the legal database is in English)
- Keep each query short (3-10 words)
- Include relevant legal terminology
- If the query mentions a specific section/rule number, always include it
- Include alternate legal terms for the same concept
- Do NOT change the user's intent
- Return as a JSON array of strings

Example:
User query: "मैं अपने ब्रांड नाम को ट्रेडमार्क कैसे करूं?"
Output: ["trademark registration procedure", "trade mark application India", "brand name protection registration", "Trade Marks Act registration", "TM application process"]
"""


async def rewrite_query(
    query: str,
    language: str,
    domain: Optional[str] = None,
    intent: Optional[str] = None,
) -> List[str]:
    """
    Generate retrieval-optimized query reformulations.

    Args:
        query: User's original query.
        language: Detected language code.
        domain: Classified domain (for context).
        intent: Classified intent (for context).

    Returns:
        List of English retrieval queries (3-5 items).
    """
    # If already in English, still generate variations
    context = ""
    if domain and domain != "unknown":
        context += f" The query is about {domain}."
    if intent and intent != "general_ip_guidance":
        context += f" The user wants information about: {intent}."

    try:
        import openai

        client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
        )

        user_msg = f"Query: {query}\nContext:{context}\n\nGenerate retrieval queries:"

        response = await client.chat.completions.create(
            model=settings.llm_model_name,
            messages=[
                {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=200,
        )

        content = response.choices[0].message.content.strip()

        # Try to parse JSON array
        if content.startswith("["):
            queries = json.loads(content)
        else:
            # Extract array from response if wrapped in text
            import re
            match = re.search(r"\[.*?\]", content, re.DOTALL)
            if match:
                queries = json.loads(match.group(0))
            else:
                queries = [content]

        # Validate and clean
        queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
        queries = queries[:5]  # Max 5 queries

        logger.debug("Query rewritten", original=query[:50], rewrites=queries)
        return queries

    except Exception as exc:
        logger.warning("Query rewriting failed, using heuristic", error=str(exc))
        return _heuristic_rewrite(query, domain, intent)


def _heuristic_rewrite(
    query: str,
    domain: Optional[str],
    intent: Optional[str],
) -> List[str]:
    """
    Fast heuristic query reformulation without LLM.
    """
    rewrites = [query]

    domain_terms = {
        "patent": ["patent India", "Patents Act 1970", "patent registration"],
        "trademark": ["trademark India", "Trade Marks Act 1999", "trademark registration"],
        "copyright": ["copyright India", "Copyright Act 1957", "copyright registration"],
        "design": ["design India", "Designs Act 2000", "design registration"],
        "gi": ["geographical indication India", "GI Act 1999", "GI registration"],
        "startup": ["startup India DPIIT", "startup recognition", "startup IP"],
        "data_protection": ["DPDP Act 2023", "data protection India", "personal data India"],
    }

    intent_terms = {
        "registration": ["registration procedure", "how to register", "application process"],
        "fees": ["fee schedule", "filing fees", "government fees"],
        "timeline": ["processing time", "duration", "how long"],
        "eligibility": ["eligibility criteria", "who can apply", "requirements"],
        "renewal": ["renewal procedure", "how to renew"],
    }

    if domain and domain in domain_terms:
        rewrites.extend(domain_terms[domain][:2])

    if intent and intent in intent_terms:
        rewrites.extend(intent_terms[intent][:1])

    return list(dict.fromkeys(rewrites))[:5]  # Deduplicate and limit
