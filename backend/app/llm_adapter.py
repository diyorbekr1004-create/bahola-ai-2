"""Oflayn (mock) LLM adapteri — deterministik, matn mazmuniga sezgir evristika.

Real LLM (OpenAI va h.k.) ulanmaganda ham tizim to'liq ishlashi uchun:
- baholash: matn xususiyatlari (hajm, tuzilma, argumentlar, dalillar, mavzuga
  aloqadorlik, til sifati) asosida har bir mezon bo'yicha ball;
- hujjatlar: mavzular bankidan silabus, dars rejasi, biletlar, testlar;
- hisobot: analitika asosida o'zbekcha tahliliy xulosa.

Bir xil matn uchun har doim bir xil natija qaytadi (hash asosidagi kichik
tebranish bilan), shuning uchun testlar va namoyish barqaror.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional, Sequence

from . import content_bank
from .plagiarism_detector import analyze_text, sentences, text_similarity, tokens
from .schemas import RubricItem

ARGUMENT_MARKERS = [
    "chunki", "masalan", "shuning uchun", "birinchidan", "ikkinchidan", "uchinchidan", "natijada",
    "bundan tashqari", "shu bilan birga", "ya'ni", "demak", "misol uchun", "sababi", "shunga ko'ra",
    "because", "for example", "for instance", "therefore", "however", "moreover", "thus",
    "например", "потому что", "таким образом", "во-первых", "во-вторых", "следовательно",
]
CONCLUSION_MARKERS = [
    "xulosa", "demak", "shunday qilib", "umuman olganda", "yakunida", "xulosa qilib", "yakuniy fikr",
    "in conclusion", "to conclude", "to sum up", "overall", "в заключение", "таким образом", "итак",
]
INTRO_MARKERS = [
    "mavzu", "ushbu", "mazkur", "maqsad", "dolzarb", "bugungi kunda", "hozirgi", "kirish",
    "this essay", "this paper", "introduction", "nowadays", "today", "данная", "актуальн", "в настоящее время",
]
EVIDENCE_PATTERNS = [
    r"\b(19|20)\d{2}\b",          # yillar
    r"\d+\s?%",                   # foizlar
    r"\b\d+[.,]\d+\b",            # kasr sonlar
    r"\(\s*[^)]*\d{4}[^)]*\)",    # (Muallif, 2020)
    r"\bmanba", r"\badabiyot", r"\bga ko'ra\b", r"\bfikricha\b", r"\baccording to\b", r"\bsource", r"\bисточник",
]
CODE_PATTERNS = [r"\bdef\s+\w+\(", r"\bfor\s+\w+\s+in\b", r"\bwhile\s*\(", r"\bif\s*\(", r"[{};]", r"\breturn\b", r"\bimport\b", r"\bSELECT\b", r"\bclass\s+\w+"]

STOPWORDS = set(
    "va bilan uchun ham bu shu ushbu mazkur bo'lgan bo'lib esa yoki lekin ammo biroq kabi orqali haqida the and for with this that from are was were is of to in on at by or an as be it its".split()
)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _stable_jitter(*parts: str, spread: int = 3) -> float:
    """Deterministik kichik tebranish (-spread..+spread)/100."""
    h = int(hashlib.md5("|".join(parts).encode("utf-8")).hexdigest(), 16)
    return ((h % (2 * spread + 1)) - spread) / 100.0


def _keyword_tokens(text: str) -> set:
    return {t for t in tokens(text) if len(t) > 3 and t not in STOPWORDS}


def text_features(text: str, reference_answer: Optional[str] = None, topic: Optional[str] = None) -> Dict[str, Any]:
    text = text or ""
    lowered = text.lower()
    toks = tokens(text)
    sents = sentences(text)
    paragraphs = [p for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    wc = len(toks)
    n_sent = max(1, len(sents))

    head = lowered[: max(200, len(lowered) // 5)]
    tail = lowered[-max(200, len(lowered) // 4):]

    arg_hits = sum(lowered.count(m) for m in ARGUMENT_MARKERS)
    has_conclusion = any(m in tail for m in CONCLUSION_MARKERS)
    has_intro = any(m in head for m in INTRO_MARKERS) or (topic is not None and any(t in head for t in _keyword_tokens(topic)))
    evidence_hits = sum(len(re.findall(p, text, flags=re.IGNORECASE)) for p in EVIDENCE_PATTERNS)
    code_hits = sum(len(re.findall(p, text)) for p in CODE_PATTERNS)

    lens = [len(s.split()) for s in sents] or [0]
    long_sentences = sum(1 for l in lens if l > 40)
    unique_ratio = len(set(toks)) / max(1, wc)
    repeated_sentences = len(sents) - len({s.lower() for s in sents})

    topic_overlap = None
    if topic:
        kt = _keyword_tokens(topic)
        if kt:
            topic_overlap = len(kt & set(toks)) / len(kt)

    ref_similarity = None
    ref_keyword_coverage = None
    if reference_answer and reference_answer.strip():
        ref_similarity = text_similarity(text, reference_answer)
        kref = _keyword_tokens(reference_answer)
        if kref:
            ref_keyword_coverage = len(kref & set(toks)) / len(kref)

    # --- Sub-ballar (0..1) ---
    if wc < 40:
        length_score = 0.15
    elif wc < 100:
        length_score = 0.35
    elif wc < 180:
        length_score = 0.55
    elif wc < 300:
        length_score = 0.75
    elif wc < 600:
        length_score = 0.9
    else:
        length_score = 1.0

    structure_score = 0.3 * has_intro + 0.4 * has_conclusion + 0.3 * (1.0 if len(paragraphs) >= 3 else 0.5 if len(paragraphs) == 2 else 0.0)
    argument_score = 0.6 * _clamp(arg_hits / 5.0) + 0.4 * _clamp(evidence_hits / 4.0)

    if ref_similarity is not None:
        cov = ref_keyword_coverage or 0.0
        relevance_score = _clamp(0.25 + 0.45 * cov + 0.3 * _clamp(ref_similarity / 0.5))
    elif topic_overlap is not None:
        relevance_score = _clamp(0.35 + 0.65 * topic_overlap)
    else:
        relevance_score = 0.7

    language_score = (
        0.5 * _clamp((unique_ratio - 0.35) / 0.35)
        + 0.3 * (1.0 - long_sentences / n_sent)
        + 0.2 * (1.0 - repeated_sentences / n_sent)
    )
    code_score = _clamp(code_hits / 6.0)

    overall = 0.25 * length_score + 0.2 * structure_score + 0.25 * argument_score + 0.15 * relevance_score + 0.15 * language_score

    return {
        "word_count": wc,
        "sentence_count": len(sents),
        "paragraph_count": len(paragraphs),
        "avg_sentence_len": round(sum(lens) / len(lens), 1),
        "long_sentences": long_sentences,
        "repeated_sentences": repeated_sentences,
        "unique_ratio": round(unique_ratio, 3),
        "argument_markers": arg_hits,
        "evidence_hits": evidence_hits,
        "code_hits": code_hits,
        "has_intro": bool(has_intro),
        "has_conclusion": bool(has_conclusion),
        "topic_overlap": None if topic_overlap is None else round(topic_overlap, 3),
        "reference_similarity": ref_similarity,
        "reference_keyword_coverage": None if ref_keyword_coverage is None else round(ref_keyword_coverage, 3),
        "scores": {
            "length": round(length_score, 3),
            "structure": round(structure_score, 3),
            "argument": round(argument_score, 3),
            "relevance": round(relevance_score, 3),
            "language": round(language_score, 3),
            "code": round(code_score, 3),
            "overall": round(overall, 3),
        },
    }


def _criterion_quality(name: str, f: Dict[str, Any]) -> float:
    s = f["scores"]
    n = (name or "").lower()
    if any(k in n for k in ("dolzarb", "mavzu", "kirish", "relevan", "maqsad", "muvofiq")):
        return 0.55 * s["relevance"] + 0.25 * (0.9 if f["has_intro"] else 0.35) + 0.2 * s["overall"]
    if any(k in n for k in ("dalil", "argument", "tahlil", "asos", "misol", "evidence", "analy", "isbot")):
        return 0.6 * s["argument"] + 0.2 * s["length"] + 0.2 * s["overall"]
    if any(k in n for k in ("xulosa", "yakun", "conclusion", "natija")):
        return 0.6 * (0.9 if f["has_conclusion"] else 0.25) + 0.4 * s["overall"]
    if any(k in n for k in ("til", "grammat", "uslub", "savod", "imlo", "language", "style", "orfograf")):
        return 0.7 * s["language"] + 0.3 * s["overall"]
    if any(k in n for k in ("tuzil", "struktur", "mantiq", "structure", "logic", "ketma", "izchil")):
        return 0.7 * s["structure"] + 0.3 * s["overall"]
    if any(k in n for k in ("ijod", "original", "creativ", "mustaqil")):
        return 0.5 * _clamp((f["unique_ratio"] - 0.35) / 0.35) + 0.5 * s["overall"]
    if any(k in n for k in ("hajm", "to'liq", "toliq", "complete", "qamrov", "yetarli")):
        return 0.7 * s["length"] + 0.3 * s["overall"]
    if any(k in n for k in ("kod", "code", "dastur", "algoritm", "amaliy")):
        return 0.5 * s["code"] + 0.2 * s["argument"] + 0.3 * s["overall"] if f["code_hits"] else 0.4 * s["argument"] + 0.6 * s["overall"]
    return s["overall"]


def _criterion_evidence(name: str, f: Dict[str, Any], score: float, max_score: float) -> str:
    n = (name or "").lower()
    pct = score / max_score if max_score else 0
    parts: List[str] = []
    if any(k in n for k in ("dolzarb", "mavzu", "kirish", "relevan", "maqsad")):
        if f["reference_keyword_coverage"] is not None:
            parts.append(f"etalon javobdagi kalit so'zlarning {int(f['reference_keyword_coverage'] * 100)}% qamrab olingan")
        if f["topic_overlap"] is not None:
            parts.append(f"mavzu kalit so'zlari bilan mosligi {int(f['topic_overlap'] * 100)}%")
        parts.append("kirish/mavzu bayoni mavjud" if f["has_intro"] else "kirish qismi aniq ajratilmagan")
    elif any(k in n for k in ("dalil", "argument", "tahlil", "asos", "misol")):
        parts.append(f"{f['argument_markers']} ta argument bog'lovchisi ('chunki', 'masalan' kabi)")
        parts.append(f"{f['evidence_hits']} ta raqamli dalil/manba belgisi" if f["evidence_hits"] else "raqamli dalil yoki manbaga havola yo'q")
    elif any(k in n for k in ("xulosa", "yakun", "conclusion")):
        parts.append("yakuniy xulosa qismi mavjud" if f["has_conclusion"] else "xulosa qismi topilmadi")
    elif any(k in n for k in ("til", "grammat", "uslub", "savod", "imlo")):
        parts.append(f"unikal so'zlar ulushi {int(f['unique_ratio'] * 100)}%")
        if f["long_sentences"]:
            parts.append(f"{f['long_sentences']} ta haddan tashqari uzun jumla")
    elif any(k in n for k in ("tuzil", "struktur", "mantiq")):
        parts.append(f"{f['paragraph_count']} ta abzats, kirish {'bor' if f['has_intro'] else 'yo`q'}, xulosa {'bor' if f['has_conclusion'] else 'yo`q'}")
    else:
        parts.append(f"{f['word_count']} so'z, {f['sentence_count']} jumla, umumiy sifat {int(f['scores']['overall'] * 100)}%")
    level = "yuqori" if pct >= 0.85 else "yaxshi" if pct >= 0.7 else "o'rtacha" if pct >= 0.55 else "past"
    return f"{'; '.join(parts)} — daraja: {level}."


def _build_feedback(f: Dict[str, Any], total: float, max_total: float, integrity: Dict[str, Any]) -> Dict[str, Any]:
    strengths: List[str] = []
    errors: List[str] = []
    suggestions: List[str] = []

    wc = f["word_count"]
    if wc >= 250:
        strengths.append(f"Ish hajmi yetarli ({wc} so'z).")
    elif wc < 120:
        errors.append(f"Ish juda qisqa ({wc} so'z) — mavzuni to'liq ochish uchun kamida 150–200 so'z tavsiya etiladi.")
        suggestions.append("Har bir fikrni kamida bitta misol yoki dalil bilan kengaytiring.")

    if f["has_intro"] and f["has_conclusion"]:
        strengths.append("Kirish va xulosa qismlari aniq ajratilgan.")
    if not f["has_intro"]:
        errors.append("Kirish qismida mavzu va maqsad aniq bayon qilinmagan.")
        suggestions.append("Ishni mavzuning dolzarbligi va maqsadini ko'rsatuvchi 2–3 jumlalik kirish bilan boshlang.")
    if not f["has_conclusion"]:
        errors.append("Xulosa qismi yo'q yoki aniq ifodalanmagan.")
        suggestions.append("Yakunda «Xulosa qilib aytganda…» ko'rinishida asosiy natijalarni umumlashtiring.")

    if f["argument_markers"] >= 4:
        strengths.append(f"Fikrlar mantiqiy bog'lovchilar orqali asoslangan ({f['argument_markers']} ta).")
    elif f["argument_markers"] <= 1:
        errors.append("Fikrlar asoslanmagan — 'chunki', 'masalan', 'shuning uchun' kabi bog'lovchilar deyarli yo'q.")
        suggestions.append("Har bir da'vodan keyin sabab va misol keltiring (da'vo → sabab → misol).")

    if f["evidence_hits"] >= 2:
        strengths.append("Raqamli dalillar, sanalar yoki manbalarga havolalar keltirilgan.")
    else:
        errors.append("Statistik ma'lumot, sana yoki manbaga havola keltirilmagan.")
        suggestions.append("Kamida 2 ta ishonchli manba yoki raqamli ma'lumot qo'shing.")

    if f["repeated_sentences"] > 0:
        errors.append(f"{f['repeated_sentences']} ta jumla aynan takrorlangan.")
        suggestions.append("Takrorlangan jumlalarni olib tashlang yoki yangi fikr bilan almashtiring.")
    if f["long_sentences"] > 0:
        errors.append(f"{f['long_sentences']} ta jumla 40 so'zdan uzun — o'qishni qiyinlashtiradi.")
        suggestions.append("Uzun jumlalarni 2–3 qisqa jumlaga bo'ling.")
    if f["paragraph_count"] < 2 and wc > 120:
        errors.append("Matn abzatslarga bo'linmagan.")
        suggestions.append("Har bir yangi fikrni alohida abzatsdan boshlang (kirish, asosiy qism, xulosa).")
    if f["unique_ratio"] >= 0.6 and wc > 80:
        strengths.append("Lug'at boyligi yaxshi — takrorlanuvchi so'zlar kam.")

    if f["topic_overlap"] is not None and f["topic_overlap"] < 0.34:
        errors.append("Mavzuga aloqadorlik past — mavzu kalit so'zlari matnda deyarli uchramaydi.")
        suggestions.append("Mavzuning asosiy terminlarini matnda bevosita ishlating va izohlang.")
    if f["reference_keyword_coverage"] is not None:
        cov = int(f["reference_keyword_coverage"] * 100)
        if cov >= 60:
            strengths.append(f"Etalon javobning asosiy tushunchalari qamrab olingan ({cov}%).")
        elif cov < 30:
            errors.append(f"Etalon javob bilan mosligi past ({cov}%) — muhim tushunchalar yoritilmagan.")
            suggestions.append("Topshiriq talab qilgan asosiy tushunchalarni birma-bir yoritib chiqing.")

    if "plagiarism" in integrity.get("flags", []):
        errors.append("Plagiat belgilari: takrorlanuvchi shablon iboralar ko'p.")
    if "ai_generated" in integrity.get("flags", []):
        errors.append("Matn sun'iy intellekt yordamida yozilgan bo'lishi ehtimoli yuqori — o'qituvchi tekshiruvi tavsiya etiladi.")
    if "similar_submission" in integrity.get("flags", []):
        errors.append(f"Boshqa talaba ishi bilan o'xshashlik yuqori ({int((integrity.get('similarity_score') or 0) * 100)}%).")

    if not strengths:
        strengths.append("Talaba mavzu bo'yicha dastlabki fikrlarini bayon qilgan.")
    if not suggestions:
        suggestions.append("Ishni shu darajada davom ettiring; misollar va manbalar sonini oshiring.")

    pct = total / max_total if max_total else 0
    level = "a'lo" if pct >= 0.86 else "yaxshi" if pct >= 0.71 else "qoniqarli" if pct >= 0.56 else "qoniqarsiz"
    main_issue = errors[0] if errors else "jiddiy kamchilik topilmadi"
    summary = (
        f"Ish {level} darajada bajarilgan ({round(total)}/{round(max_total)} ball). "
        f"Kuchli tomoni: {strengths[0].rstrip('.').lower()}. Asosiy kamchilik: {main_issue.rstrip('.').lower()}."
    )
    return {"summary": summary, "strengths": strengths[:5], "errors": errors[:6], "suggestions": suggestions[:5]}


class MockLLMAdapter:
    """Tashqi API'siz ishlaydigan baholash/hujjat/hisobot adapteri."""

    name = "mock"
    model = "heuristic-v2"

    async def grade_submission(
        self,
        text: str,
        rubric: Sequence[RubricItem],
        *,
        reference_answer: Optional[str] = None,
        topic: Optional[str] = None,
        course: Optional[str] = None,
        language: str = "uz",
        compare_with: Optional[Sequence] = None,
    ) -> Dict[str, Any]:
        f = text_features(text, reference_answer=reference_answer, topic=topic)
        integrity = analyze_text(text, compare_with=compare_with)

        scored: List[RubricItem] = []
        total = 0.0
        max_total = 0.0
        for item in rubric:
            q = _clamp(_criterion_quality(item.name, f) + _stable_jitter(text[:500], item.name), 0.05, 1.0)
            score = float(round(item.max_score * q))
            scored.append(RubricItem(name=item.name, max_score=item.max_score, score=score, evidence=_criterion_evidence(item.name, f, score, item.max_score), description=item.description))
            total += score
            max_total += item.max_score

        feedback = _build_feedback(f, total, max_total, integrity)
        return {
            "total_score": total,
            "max_score": max_total,
            "rubric": scored,
            "feedback": feedback,
            "plagiarism_score": integrity["plagiarism_score"],
            "ai_likelihood": integrity["ai_likelihood"],
            "integrity": integrity,
            "features": f,
            "provider": self.name,
            "model": self.model,
        }

    async def generate_docs(
        self,
        course_name: str,
        *,
        hours: int = 60,
        weeks: int = 15,
        language: str = "uz",
        level: Optional[str] = None,
        n_tickets: int = 3,
        n_questions: int = 10,
        topics: Optional[List[str]] = None,
        doc_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        doc_types = doc_types or ["syllabus", "lesson_plan", "exam_tickets", "test_questions"]
        topic_list = content_bank.topics_for_course(course_name, weeks, topics)
        out: Dict[str, Any] = {"course": course_name, "topics": topic_list, "provider": self.name}
        if "syllabus" in doc_types:
            out["syllabus"] = content_bank.build_syllabus(course_name, hours, weeks, topic_list, level)
        if "lesson_plan" in doc_types:
            out["lesson_plan"] = content_bank.build_lesson_plan(course_name, topic_list[0], week=1)
        if "exam_tickets" in doc_types:
            out["exam_tickets"] = content_bank.build_exam_tickets(course_name, topic_list, n_tickets)
        if "test_questions" in doc_types:
            out["test_questions"] = content_bank.build_mcq(course_name, topic_list, n_questions)
        return out

    async def generate_report_summary(self, analytics: Dict[str, Any], course: Optional[str], group: Optional[str]) -> str:
        from .analytics import build_narrative

        return build_narrative(analytics, course=course, group=group)

    async def chat(self, messages: Sequence[dict], *, system: Optional[str] = None, **_: Any) -> str:
        """Oflayn yordamchi: bilimlar bazasidagi FAQ bo'yicha javob."""
        from .assistant_kb import offline_answer

        last_user = next((m.get("content", "") for m in reversed(list(messages)) if m.get("role") == "user"), "")
        return offline_answer(str(last_user))
