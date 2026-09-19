from typing import List
from .schemas import RubricItem, Feedback
import random


class LLMAdapter:
    """Mockable LLM adapter. Replace internals with real API calls (OpenAI/Google).

    Methods:
    - grade_submission(text, rubric): returns structured rubric scores and feedback
    - generate_docs(request): returns syllabus and exam ticket
    - generate_report(request): returns summary and path to export
    """

    async def grade_submission(self, text: str, rubric: List[RubricItem]):
        # Simple heuristic/mock: distribute points randomly but reproducibly
        total = 0
        evidences = []
        for r in rubric:
            score = random.randint(max(0, r.max_score - 3), r.max_score)
            r.score = score
            r.evidence = f"Detected key points for '{r.name}'."
            total += score
            evidences.append(r.evidence)

        feedback = Feedback(
            summary="Umumiy baho va xulosalar avtomatik tahlil asosida.",
            suggestions=[
                "Argumentlaringizni kuchaytirish uchun manbalarni keltiring.",
                "Xulosa qismini aniqroq yozing va asoslang.",
            ],
        )

        # Mock plagiarism / AI likelihood
        plagiarism = round(random.uniform(0, 0.3), 3)
        ai_likelihood = round(random.uniform(0, 0.5), 3)

        return {
            "total_score": total,
            "rubric": rubric,
            "plagiarism_score": plagiarism,
            "ai_likelihood": ai_likelihood,
            "feedback": feedback,
        }

    async def generate_docs(self, course_name: str, hours: int = 60, weeks: int = 15):
        syllabus = f"{course_name} — {weeks}-haftalik o'quv rejasi (umumiy {hours} soat).\n\n"
        for w in range(1, weeks + 1):
            syllabus += f"Hafta {w}: Mavzu {w} — Maqsadlar va kompetensiyalar.\n"

        exam = f"Imtihon bileti — {course_name}\n1) Nazariy savol\n2) Tushuntirish savoli\n3) Amaliy vazifa"

        return {"syllabus": syllabus, "exam_ticket": exam}

    async def generate_report(self, course_name: str, group_id: str = None):
        # Simple mock summary
        summary = f"Guruh: {group_id or 'Barcha'} — {course_name}: O'rtacha o'zlashtirish 78%, sifat ko'rsatkichi 64%."
        return {
            "summary": summary,
            "excel_path": None,
            "analytics": {
                "average_score": 78.0,
                "pass_rate": 82.0,
                "quality_rate": 64.0,
                "weak_topics": [{"topic": "Mavzu 3", "average_score": 68.0, "difficulty": 32.0}],
            },
        }
