"""
Tests for Language Detection and Intent / Domain Classification
"""
import pytest
from app.multilingual.language_detector import detect_language
from app.multilingual.intent_classifier import _heuristic_classify


def test_language_detection_hindi():
    res = detect_language("मैं अपने ब्रांड नाम को कैसे सुरक्षित कर सकता हूँ?")
    assert res.language == "hi"
    assert res.confidence >= 0.9


def test_language_detection_bengali():
    res = detect_language("ট্রেডমার্ক রেজিস্ট্রেশন কীভাবে করতে হয়?")
    assert res.language == "bn"
    assert res.confidence >= 0.9


def test_language_detection_english():
    res = detect_language("What is the difference between a patent and a trademark?")
    assert res.language == "en"


def test_language_detection_hinglish():
    res = detect_language("Mere startup ke brand name ko trademark kaise register karein?")
    assert res.is_mixed or res.language in ("mixed", "hi", "en")


def test_heuristic_classification_trademark():
    res = _heuristic_classify("How do I register a trademark for my brand logo?")
    assert res.domain == "trademark"
    assert res.intent == "registration"


def test_heuristic_classification_patent_section():
    res = _heuristic_classify("What does Section 3 of Patents Act say?")
    assert res.domain == "patent"
    assert res.has_section_reference is True
