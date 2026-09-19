import pytest
from app.plagiarism_detector import analyze_text


def test_analyze_text_simple():
    text = "Bu oddiy matn. Bu oddiy matn. Bu oddiy matn."
    out = analyze_text(text)
    assert "plagiarism_score" in out
    assert "ai_likelihood" in out
    assert isinstance(out["reasons"], list)


def test_analyze_text_unique():
    text = "Bu matn har bir jumlasi noyob va turlicha yozilgan namunadir. Har bir jumla boshqa mavzuni ochib beradi."
    out = analyze_text(text)
    assert out["plagiarism_score"] <= 0.5
