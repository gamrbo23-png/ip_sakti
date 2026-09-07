"""
IP-SAKTI Sahayak — Language Detection
Detects user query language with confidence score.
Handles English, Hindi, Bengali, Tamil, Telugu, and Hinglish.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from app.logging_config import get_logger

logger = get_logger(__name__)

# Unicode ranges for Indian scripts
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")   # Hindi, Marathi, Sanskrit
BENGALI_RE = re.compile(r"[\u0980-\u09FF]")
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
TELUGU_RE = re.compile(r"[\u0C00-\u0C7F]")
LATIN_RE = re.compile(r"[a-zA-Z]")

# Common Hinglish/transliterated Hindi words
HINGLISH_KEYWORDS = {
    "aur", "hai", "hain", "mera", "meri", "apna", "apni", "ka", "ki", "ke",
    "kaise", "kya", "ko", "se", "par", "mein", "nahi", "nahin", "krein",
    "karo", "karein", "startup", "brand", "patent", "trademark", "register",
    "kaise", "hoga", "rahega", "chahiye",
}

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिंदी",
    "bn": "বাংলা",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "mixed": "Hinglish / Mixed",
}


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""
    language: str               # ISO 639-1 code or "mixed"
    confidence: float           # 0.0 to 1.0
    detected_scripts: list      # Which scripts were found
    display_name: str           # Human-readable language name
    is_mixed: bool              # True for Hinglish/code-switching


def detect_language(text: str) -> LanguageDetectionResult:
    """
    Detect the language of an input text.

    Strategy:
    1. Check for Indian script characters (reliable Unicode detection).
    2. If no Indian scripts, check for Hinglish patterns.
    3. Fall back to langdetect for English detection.
    4. For mixed Latin + Hinglish patterns, label as "mixed".

    Args:
        text: User's input text.

    Returns:
        LanguageDetectionResult with language code and confidence.
    """
    if not text or not text.strip():
        return LanguageDetectionResult("en", 0.5, [], "English", False)

    cleaned = text.strip()
    detected_scripts = []

    # ── Script-based detection ────────────────────────────────────────────────
    has_devanagari = bool(DEVANAGARI_RE.search(cleaned))
    has_bengali = bool(BENGALI_RE.search(cleaned))
    has_tamil = bool(TAMIL_RE.search(cleaned))
    has_telugu = bool(TELUGU_RE.search(cleaned))
    has_latin = bool(LATIN_RE.search(cleaned))

    if has_devanagari:
        detected_scripts.append("Devanagari")
    if has_bengali:
        detected_scripts.append("Bengali")
    if has_tamil:
        detected_scripts.append("Tamil")
    if has_telugu:
        detected_scripts.append("Telugu")
    if has_latin:
        detected_scripts.append("Latin")

    # Pure script detection (highest confidence)
    if has_devanagari and not has_latin:
        return LanguageDetectionResult("hi", 0.97, detected_scripts, "हिंदी", False)

    if has_bengali and not has_latin:
        return LanguageDetectionResult("bn", 0.97, detected_scripts, "বাংলা", False)

    if has_tamil and not has_latin:
        return LanguageDetectionResult("ta", 0.97, detected_scripts, "தமிழ்", False)

    if has_telugu and not has_latin:
        return LanguageDetectionResult("te", 0.97, detected_scripts, "తెలుగు", False)

    # Mixed Devanagari + Latin = Hinglish
    if has_devanagari and has_latin:
        return LanguageDetectionResult("mixed", 0.90, detected_scripts, "Hinglish / Mixed", True)

    # ── Hinglish detection (pure Latin transliteration) ───────────────────────
    if has_latin and not any([has_devanagari, has_bengali, has_tamil, has_telugu]):
        words = set(cleaned.lower().split())
        hinglish_hits = words & HINGLISH_KEYWORDS

        if len(hinglish_hits) >= 2:
            return LanguageDetectionResult(
                "mixed", 0.80, detected_scripts, "Hinglish / Mixed", True
            )

    # ── langdetect fallback for English/other ─────────────────────────────────
    try:
        from langdetect import detect, detect_langs
        from langdetect.lang_detect_exception import LangDetectException

        lang_probs = detect_langs(cleaned)
        if lang_probs:
            best = lang_probs[0]
            lang_code = best.lang
            confidence = best.prob

            # Map to supported codes
            if lang_code in ("hi", "mr"):
                return LanguageDetectionResult("hi", confidence, detected_scripts, "हिंदी", False)
            elif lang_code == "bn":
                return LanguageDetectionResult("bn", confidence, detected_scripts, "বাংলা", False)
            elif lang_code == "ta":
                return LanguageDetectionResult("ta", confidence, detected_scripts, "தமிழ்", False)
            elif lang_code == "te":
                return LanguageDetectionResult("te", confidence, detected_scripts, "తెలుగు", False)
            elif lang_code == "en":
                return LanguageDetectionResult("en", confidence, detected_scripts, "English", False)
            else:
                # Unknown language — default to English
                return LanguageDetectionResult("en", 0.6, detected_scripts, "English", False)

    except Exception:
        pass

    # Default to English
    return LanguageDetectionResult("en", 0.7, detected_scripts, "English", False)


def get_response_language_instruction(lang_code: str) -> str:
    """Get the instruction for the LLM to respond in the user's language."""
    instructions = {
        "en": "Respond in clear English.",
        "hi": "हिंदी में उत्तर दें। महत्वपूर्ण कानूनी शब्दों को अंग्रेजी में कोष्ठकों में दिखाएं।",
        "bn": "বাংলায় উত্তর দিন। গুরুত্বপূর্ণ আইনি পরিভাষা ইংরেজিতে বন্ধনীতে দেখান।",
        "ta": "தமிழில் பதில் அளிக்கவும். முக்கியமான சட்ட சொற்களை ஆங்கிலத்தில் அடைப்புக்குறிக்குள் காட்டவும்।",
        "te": "తెలుగులో సమాధానం ఇవ్వండి. ముఖ్యమైన చట్టపరమైన పదాలను ఆంగ్లంలో బ్రాకెట్లలో చూపండి।",
        "mixed": "The user wrote in Hinglish (mixed Hindi-English). Respond in a friendly mix of Hindi and English, keeping legal terms in English with Hindi explanation.",
    }
    return instructions.get(lang_code, "Respond in clear English.")
