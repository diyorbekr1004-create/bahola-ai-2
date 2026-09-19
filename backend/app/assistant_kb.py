"""Yordamchi chat uchun bilimlar bazasi (`config/assistant_knowledge.md`) va oflayn FAQ mosligi."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config

_STOP = set("va bilan uchun ham bu shu nima qanday qaysi mumkin kerak bo'ladi bo'lsa yoki lekin men siz biz sizga menga haqida qilinadi qiladi the and for with what how".split())
_APOS = str.maketrans({"’": "'", "‘": "'", "`": "'", "ʻ": "'", "ʼ": "'"})

_cache: Optional[Dict[str, Any]] = None


def kb_path() -> Path:
    return Path(config.settings.project_root) / "config" / "assistant_knowledge.md"


def _tokens(text: str) -> List[str]:
    text = (text or "").translate(_APOS).lower()
    return [t for t in re.findall(r"[\w']+", text) if len(t) > 2 and t not in _STOP]


def load(force: bool = False) -> Dict[str, Any]:
    """{'text': to'liq md, 'faq': [{question, keywords, answer, tokens}]}"""
    global _cache
    if _cache is not None and not force:
        return _cache
    try:
        text = kb_path().read_text(encoding="utf-8")
    except OSError:
        text = "# AI O'qituvchi Hamkori\nTalaba ishlarini AI bilan tekshirish, hujjatlar yaratish, HEMIS eksport va analitika tizimi."
    faq: List[Dict[str, Any]] = []
    for block in re.split(r"\n### ", text)[1:]:
        lines = block.strip().splitlines()
        if not lines:
            continue
        question = re.sub(r"^Savol:\s*", "", lines[0]).strip()
        keywords, answer_lines = "", []
        for ln in lines[1:]:
            if ln.lower().startswith("keywords:"):
                keywords = ln.split(":", 1)[1]
            elif ln.lower().startswith("javob:"):
                answer_lines.append(ln.split(":", 1)[1].strip())
            elif answer_lines:
                answer_lines.append(ln)
        answer = " ".join(a.strip() for a in answer_lines).strip()
        if question and answer:
            faq.append({"question": question, "keywords": [k.strip().translate(_APOS).lower() for k in keywords.split(",") if k.strip()],
                        "answer": answer, "tokens": set(_tokens(question) + _tokens(keywords))})
    _cache = {"text": text, "faq": faq}
    return _cache


def reload() -> Dict[str, Any]:
    return load(force=True)


def knowledge_text() -> str:
    return load()["text"]


def suggested_questions(limit: int = 4) -> List[str]:
    return [f["question"] for f in load()["faq"][:limit]]


def match_faq(question: str, threshold: float = 0.12) -> Optional[Dict[str, Any]]:
    """Kalit so'zlar mosligi bo'yicha eng yaqin FAQ (oflayn rejim)."""
    q_tokens = set(_tokens(question))
    q_text = (question or "").translate(_APOS).lower()
    if not q_tokens and not q_text.strip():
        return None
    best, best_score = None, 0.0
    for entry in load()["faq"]:
        overlap = len(q_tokens & entry["tokens"])
        phrase_hits = sum(1 for k in entry["keywords"] if k and k in q_text)
        score = (overlap + 1.5 * phrase_hits) / (len(q_tokens) + 2)
        if score > best_score:
            best, best_score = entry, score
    return best if best and best_score >= threshold else None


def offline_answer(question: str) -> str:
    entry = match_faq(question)
    if entry:
        return entry["answer"]
    topics = "; ".join(f["question"] for f in load()["faq"][:6])
    return ("Bu savolga aniq javobim yo'q. Men saytning bo'limlari, baholash, HEMIS eksport, tariflar va sozlamalar haqida javob bera olaman. "
            f"Masalan: {topics}")
