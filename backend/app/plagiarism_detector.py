"""Plagiat / AI-matn / guruh ichidagi o'xshashlik uchun yengil evristik tahlil.

Tashqi xizmatlarga bog'liq emas — 100% oflayn ishlaydi. Natijalar 0..1 oralig'ida.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Optional, Tuple

_WORD_RE = re.compile(r"\w+", re.UNICODE)

# Keng tarqalgan shablon iboralar (o'zbek, rus, ingliz)
BOILERPLATE = [
    "in conclusion", "to summarize", "this essay explores", "the purpose of this paper",
    "xulosa qilib aytganda", "umuman olganda", "ushbu ishda", "mazkur ishda",
    "в заключение", "таким образом", "в данной работе",
]

# AI-yozuvga xos "silliq" bog'lovchilar
AI_MARKERS = [
    "shuni ta'kidlash joizki", "muhim jihati shundaki", "umumiy holda", "shubhasiz",
    "delve", "furthermore", "moreover", "it is important to note", "in today's world",
    "в современном мире", "следует отметить", "важно отметить",
]


def tokens(text: str) -> List[str]:
    return _WORD_RE.findall((text or "").lower())


def sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text or "") if s.strip()]


def ngrams(tok: List[str], n: int = 3) -> List[str]:
    if len(tok) < n:
        return [" ".join(tok)] if tok else []
    return [" ".join(tok[i : i + n]) for i in range(len(tok) - n + 1)]


def _unique_ngrams_score(text: str, n: int = 3) -> float:
    grams = ngrams(tokens(text), n)
    if not grams:
        return 1.0
    return len(set(grams)) / len(grams)


def jaccard_similarity(a: str, b: str, n: int = 3) -> float:
    ga, gb = set(ngrams(tokens(a), n)), set(ngrams(tokens(b), n))
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def text_similarity(a: str, b: str) -> float:
    """Ikki matn o'rtasidagi o'xshashlik (0..1): n-gram Jaccard va SequenceMatcher aralashmasi."""
    if not a or not b:
        return 0.0
    jac = jaccard_similarity(a, b, 3)
    # SequenceMatcher katta matnlarda sekin — 6000 belgigacha cheklaymiz
    seq = SequenceMatcher(None, a[:6000].lower(), b[:6000].lower()).ratio()
    return round(max(jac, 0.6 * seq + 0.4 * jac), 3)


def find_most_similar(text: str, others: Iterable[Tuple[str, str]], top_k: int = 5) -> Tuple[float, Optional[str]]:
    """`others` = [(label, text)]. Eng yuqori o'xshashlik va uning yorlig'ini qaytaradi.

    Avval tez Jaccard bilan barcha nomzodlar saralanadi, so'ng faqat eng yaqin
    `top_k` tasi uchun qimmatroq SequenceMatcher hisoblanadi.
    """
    candidates: List[Tuple[float, str, str]] = []
    for other_label, other_text in others:
        if not other_text:
            continue
        candidates.append((jaccard_similarity(text, other_text, 3), other_label, other_text))
    if not candidates:
        return 0.0, None
    candidates.sort(key=lambda c: c[0], reverse=True)
    best, label = 0.0, None
    for _, other_label, other_text in candidates[:top_k]:
        sim = text_similarity(text, other_text)
        if sim > best:
            best, label = sim, other_label
    return round(best, 3), label


def analyze_text(text: str, compare_with: Optional[Iterable[Tuple[str, str]]] = None) -> Dict[str, Any]:
    """Plagiat ehtimoli, AI-matn ehtimoli, (ixtiyoriy) boshqa ishlarga o'xshashlik va sabablar."""
    text = text or ""
    lowered = text.lower()
    toks = tokens(text)
    sents = sentences(text)

    # 1) Takrorlanuvchi n-gramlar va jumlalar
    uniq_score = _unique_ngrams_score(text, 3)
    repeats = len(sents) - len(set(s.lower() for s in sents))
    repeat_ratio = repeats / max(1, len(sents))
    plagiarism = (1.0 - uniq_score) * 0.8 + repeat_ratio * 0.6

    # 2) Shablon iboralar
    boiler_hits = sum(1 for b in BOILERPLATE if b in lowered)
    if boiler_hits >= 2:
        plagiarism += 0.15

    # 3) AI-uslub: bir tekis jumla uzunligi, AI bog'lovchilar, juda "toza" leksika
    lens = [len(s.split()) for s in sents] or [0]
    avg_len = sum(lens) / len(lens)
    variance = sum((l - avg_len) ** 2 for l in lens) / max(1, len(lens))
    ai_marker_hits = sum(lowered.count(m) for m in AI_MARKERS)
    unique_ratio = len(set(toks)) / max(1, len(toks))

    ai = 0.0
    if len(sents) >= 4 and variance < 15:
        ai += 0.35
    elif len(sents) >= 4 and variance < 30:
        ai += 0.15
    if 14 <= avg_len <= 26 and len(sents) >= 4:
        ai += 0.15
    ai += min(0.3, ai_marker_hits * 0.1)
    if unique_ratio > 0.75 and len(toks) > 150:
        ai += 0.1
    if plagiarism > 0.5:
        ai += 0.1

    plagiarism = round(max(0.0, min(1.0, plagiarism)), 3)
    ai = round(max(0.0, min(1.0, ai)), 3)

    reasons: List[str] = []
    flags: List[str] = []
    if repeat_ratio > 0.15:
        reasons.append(f"Matnda {repeats} ta jumla aynan takrorlangan.")
    if uniq_score < 0.7 and len(toks) > 30:
        reasons.append("Takrorlanuvchi iboralar ko'p — unikal 3-gram ulushi past.")
    if boiler_hits >= 2:
        reasons.append("Keng tarqalgan shablon iboralar ko'p ishlatilgan.")
    if ai_marker_hits >= 2:
        reasons.append("Sun'iy intellekt uslubiga xos bog'lovchi iboralar uchraydi.")
    if len(sents) >= 4 and variance < 15:
        reasons.append("Jumla uzunliklari g'ayritabiiy darajada bir tekis.")

    similarity, similar_label = None, None
    if compare_with:
        similarity, similar_label = find_most_similar(text, compare_with)
        if similarity is not None and similarity >= 0.6:
            reasons.append(f"Boshqa ish bilan o'xshashlik {int(similarity * 100)}% ({similar_label}).")
            flags.append("similar_submission")

    if plagiarism >= 0.4:
        flags.append("plagiarism")
    if ai >= 0.6:
        flags.append("ai_generated")
    if not reasons:
        reasons.append("Sezilarli muammo topilmadi.")

    return {
        "plagiarism_score": plagiarism,
        "ai_likelihood": ai,
        "similarity_score": similarity,
        "similar_to": similar_label,
        "reasons": reasons,
        "flags": flags,
    }
