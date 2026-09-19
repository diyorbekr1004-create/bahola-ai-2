from difflib import SequenceMatcher
from typing import Dict, Any
import re


def _unique_ngrams_score(text: str, n: int = 3) -> float:
    tokens = re.findall(r"\w+", text.lower())
    if len(tokens) < n:
        return 1.0
    ngrams = [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    unique = len(set(ngrams))
    total = len(ngrams)
    if total == 0:
        return 1.0
    return unique / total


def analyze_text(text: str) -> Dict[str, Any]:
    """Return a lightweight analysis: plagiarism_score (0..1), ai_likelihood (0..1), reasons list."""
    # Heuristic 1: ngram uniqueness (lower uniqueness -> higher plagiarism/boilerplate)
    uniq_score = _unique_ngrams_score(text, n=3)
    # Heuristic 2: repeated sentences
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    repeats = len(sentences) - len(set(sentences))
    repeat_ratio = repeats / max(1, len(sentences))

    # Plagiarism score: inverse of uniqueness weighted with repeats
    plagiarism_score = max(0.0, min(1.0, (1.0 - uniq_score) * 0.8 + repeat_ratio * 0.6))

    # AI-likelihood heuristic: very uniform sentence length, high lexical simplicity
    lens = [len(s.split()) for s in sentences] or [0]
    avg = sum(lens) / len(lens)
    variance = sum((l - avg) ** 2 for l in lens) / max(1, len(lens))
    # low variance -> more likely templated; short average length -> possibly AI
    ai_indicator = 0.0
    if avg < 12:
        ai_indicator += 0.3
    if variance < 20:
        ai_indicator += 0.4
    if plagiarism_score > 0.5:
        ai_indicator += 0.2

    ai_likelihood = max(0.0, min(1.0, ai_indicator))

    reasons = []
    if plagiarism_score > 0.4:
        reasons.append("Matnda takrorlanuvchi frazalar va kam unikal 3-gram mavjud.")
    if ai_likelihood > 0.4:
        reasons.append("Matn taxminan sun'iy intellekt shabloniga o'xshaydi — jumla uzunliklari bir tekis.")
    if not reasons:
        reasons.append("Oddiy tahlil: hech qanday sezilarli muammo topilmadi.")

    # Simple similarity to small set of boilerplate phrases (mock)
    boilerplate_examples = [
        "In conclusion", "To summarize", "This essay explores", "The purpose of this paper"
    ]
    sim_hits = 0
    for b in boilerplate_examples:
        if b.lower() in text.lower():
            sim_hits += 1
    if sim_hits >= 2:
        plagiarism_score = min(1.0, plagiarism_score + 0.15)
        reasons.append("Matnda keng tarqalgan boilerplate iboralar ko'p ishlatilgan.")

    return {"plagiarism_score": round(plagiarism_score, 3), "ai_likelihood": round(ai_likelihood, 3), "reasons": reasons}
