"""OpenAI-ga mos (chat/completions) provayder adapteri.

`OPENAI_BASE_URL` orqali OpenAI, Azure OpenAI gateway, Groq, OpenRouter,
Ollama (`http://localhost:11434/v1`) kabi har qanday mos serverga ulanadi.
JSON-rejimda ishlaydi; javob buzilgan yoki server xato bersa, mock
adapterga tushib qoladi (tizim hech qachon to'xtab qolmaydi).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Sequence

import httpx

from . import content_bank
from .llm_adapter import MockLLMAdapter, text_features
from .plagiarism_detector import analyze_text
from .schemas import RubricItem

log = logging.getLogger("bahola.openai")

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def extract_json(content: str) -> Optional[dict]:
    """Model javobidan JSON ob'ektni ajratib oladi (```json ... ``` bo'lsa ham)."""
    if not content:
        return None
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE | re.DOTALL).strip()
    try:
        return json.loads(content)
    except ValueError:
        m = _JSON_BLOCK.search(content)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                return None
    return None


class OpenAIAdapter:
    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None, timeout: float = 60.0):
        from .config import settings

        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.timeout = timeout or settings.llm_timeout_seconds
        self.fallback = MockLLMAdapter()
        self.last_error: Optional[str] = None

    async def _chat(self, messages: List[dict], *, temperature: float = 0.1, max_tokens: int = 2500, json_mode: bool = True) -> Optional[dict]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload: Dict[str, Any] = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if r.status_code == 400 and json_mode:
                    # Ba'zi serverlar response_format'ni qo'llamaydi — qayta urinamiz
                    payload.pop("response_format", None)
                    r = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                parsed = extract_json(content)
                if parsed is None:
                    self.last_error = "JSON parse error"
                return parsed
        except Exception as exc:  # noqa: BLE001 - har qanday tarmoq/format xatosi
            self.last_error = str(exc)
            log.warning("LLM so'rovi muvaffaqiyatsiz: %s", exc)
            return None

    # ------------------------------------------------------------------
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
        rubric_desc = [{"name": r.name, "max_score": r.max_score, "description": r.description or ""} for r in rubric]
        lang_name = {"uz": "o'zbek (lotin)", "ru": "rus", "en": "ingliz"}.get(language, "o'zbek (lotin)")
        system = (
            "Siz oliy ta'lim o'qituvchisining yordamchisisiz. Talaba ishini berilgan mezonlar (rubrika) bo'yicha "
            "adolatli va asosli baholaysiz. Faqat quyidagi JSON sxemasida javob bering, boshqa matn yozmang:\n"
            '{"rubric":[{"name":str,"max_score":number,"score":number,"evidence":str}],'
            '"feedback":{"summary":str,"strengths":[str],"errors":[str],"suggestions":[str]}}\n'
            f"Barcha matnlar {lang_name} tilida bo'lsin. 'evidence' — ballni asoslovchi aniq iqtibos yoki kuzatuv. "
            "'errors' — ishdagi aniq xatolar (mazmuniy, mantiqiy, til). 'score' hech qachon max_score dan oshmasin."
        )
        user_parts = [f"Fan: {course or '-'}", f"Mavzu/topshiriq: {topic or '-'}", f"Mezonlar: {json.dumps(rubric_desc, ensure_ascii=False)}"]
        if reference_answer:
            user_parts.append(f"Etalon (kutilgan) javob:\n{reference_answer[:4000]}")
        user_parts.append(f"Talaba ishi:\n{text[:12000]}")
        parsed = await self._chat([{"role": "system", "content": system}, {"role": "user", "content": "\n\n".join(user_parts)}])

        if not parsed or not isinstance(parsed.get("rubric"), list):
            result = await self.fallback.grade_submission(text, rubric, reference_answer=reference_answer, topic=topic, course=course, language=language, compare_with=compare_with)
            result["provider"] = "mock-fallback"
            result["fallback_reason"] = self.last_error
            return result

        # LLM javobini rubrika bilan moslashtiramiz (nomlar bo'yicha), yetishmaganini evristika bilan to'ldiramiz
        by_name = {str(r.get("name", "")).strip().lower(): r for r in parsed["rubric"] if isinstance(r, dict)}
        heuristic = await self.fallback.grade_submission(text, rubric, reference_answer=reference_answer, topic=topic, course=course, language=language, compare_with=compare_with)
        h_by_name = {r.name.lower(): r for r in heuristic["rubric"]}
        scored: List[RubricItem] = []
        total = 0.0
        max_total = 0.0
        for item in rubric:
            src = by_name.get(item.name.lower())
            if src and src.get("score") is not None:
                try:
                    score = float(src["score"])
                except (TypeError, ValueError):
                    score = float(h_by_name[item.name.lower()].score or 0)
                score = max(0.0, min(float(item.max_score), round(score, 1)))
                evidence = str(src.get("evidence") or "")[:1000]
            else:
                h = h_by_name[item.name.lower()]
                score, evidence = float(h.score or 0), h.evidence
            scored.append(RubricItem(name=item.name, max_score=item.max_score, score=score, evidence=evidence, description=item.description))
            total += score
            max_total += item.max_score

        fb = parsed.get("feedback") or {}
        feedback = {
            "summary": str(fb.get("summary") or heuristic["feedback"]["summary"]),
            "strengths": [str(x) for x in (fb.get("strengths") or heuristic["feedback"]["strengths"])][:6],
            "errors": [str(x) for x in (fb.get("errors") or heuristic["feedback"]["errors"])][:8],
            "suggestions": [str(x) for x in (fb.get("suggestions") or heuristic["feedback"]["suggestions"])][:6],
        }
        integrity = analyze_text(text, compare_with=compare_with)
        return {
            "total_score": total,
            "max_score": max_total,
            "rubric": scored,
            "feedback": feedback,
            "plagiarism_score": integrity["plagiarism_score"],
            "ai_likelihood": integrity["ai_likelihood"],
            "integrity": integrity,
            "features": text_features(text, reference_answer=reference_answer, topic=topic),
            "provider": self.name,
            "model": self.model,
        }

    # ------------------------------------------------------------------
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
        # 1) Mavzular ro'yxatini LLM'dan olamiz (o'qituvchi bermagan bo'lsa)
        topic_list = topics
        if not topic_list:
            system = "Siz oliy ta'lim metodistisiz. Faqat JSON qaytaring: {\"topics\":[str]}"
            user = (
                f"«{course_name}» fani uchun {weeks} haftalik o'quv rejasi mavzularini ({weeks} ta, mantiqiy ketma-ketlikda, "
                f"{level or 'bakalavriat'} darajasi, o'zbek tilida) tuzing. Har bir mavzu qisqa va aniq bo'lsin."
            )
            parsed = await self._chat([{"role": "system", "content": system}, {"role": "user", "content": user}], max_tokens=1500)
            if parsed and isinstance(parsed.get("topics"), list) and parsed["topics"]:
                topic_list = [str(t).strip() for t in parsed["topics"] if str(t).strip()]
        topic_list = content_bank.topics_for_course(course_name, weeks, topic_list)

        out: Dict[str, Any] = {"course": course_name, "topics": topic_list, "provider": self.name}
        if "syllabus" in doc_types:
            out["syllabus"] = content_bank.build_syllabus(course_name, hours, weeks, topic_list, level)
        if "lesson_plan" in doc_types:
            out["lesson_plan"] = content_bank.build_lesson_plan(course_name, topic_list[0], week=1)
        if "exam_tickets" in doc_types:
            out["exam_tickets"] = content_bank.build_exam_tickets(course_name, topic_list, n_tickets)
        if "test_questions" in doc_types:
            # 2) Test savollarini LLM bilan sifatliroq qilamiz
            system = (
                "Siz test tuzuvchi metodistsiz. Faqat JSON qaytaring: "
                '{"questions":[{"topic":str,"question":str,"options":{"A":str,"B":str,"C":str,"D":str},"answer":"A|B|C|D"}]}'
            )
            user = f"«{course_name}» fani, mavzular: {json.dumps(topic_list[:weeks], ensure_ascii=False)}. {n_questions} ta 4 variantli test savoli tuzing (o'zbek tilida, har xil mavzulardan, bitta to'g'ri javob)."
            parsed = await self._chat([{"role": "system", "content": system}, {"role": "user", "content": user}], max_tokens=3500)
            questions = []
            if parsed and isinstance(parsed.get("questions"), list):
                for i, q in enumerate(parsed["questions"][:n_questions], start=1):
                    if not isinstance(q, dict) or not isinstance(q.get("options"), dict):
                        continue
                    ans = str(q.get("answer", "A")).strip().upper()[:1]
                    if ans not in {"A", "B", "C", "D"}:
                        ans = "A"
                    questions.append({"number": i, "topic": str(q.get("topic") or ""), "question": str(q.get("question") or ""), "options": {k: str(v) for k, v in q["options"].items()}, "answer": ans})
            out["test_questions"] = questions or content_bank.build_mcq(course_name, topic_list, n_questions)
        return out

    # ------------------------------------------------------------------
    async def generate_report_summary(self, analytics: Dict[str, Any], course: Optional[str], group: Optional[str]) -> str:
        from .analytics import build_narrative

        base = build_narrative(analytics, course=course, group=group)
        system = "Siz kafedra mudiri uchun tahliliy xulosa yozuvchi metodistsiz. Faqat JSON qaytaring: {\"summary\": str}"
        user = (
            f"Fan: {course or 'barcha'}; guruh: {group or 'barcha'}. Statistik ma'lumotlar: "
            f"{json.dumps({k: analytics.get(k) for k in ('total_students', 'total_grades', 'average_score', 'pass_rate', 'quality_rate', 'distribution', 'weak_topics', 'criteria_stats', 'at_risk_students')}, ensure_ascii=False)[:6000]}\n\n"
            "Shu ma'lumotlar asosida 3–4 abzatsli rasmiy tahliliy xulosa (o'zbek tilida) yozing: umumiy holat, "
            "qiyin mavzular va sabablari, xavf guruhidagi talabalar, aniq tavsiyalar."
        )
        parsed = await self._chat([{"role": "system", "content": system}, {"role": "user", "content": user}], max_tokens=1200)
        if parsed and parsed.get("summary"):
            return str(parsed["summary"])
        return base
