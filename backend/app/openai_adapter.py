import os
import httpx
from typing import List
from .schemas import RubricItem, Feedback
import json


class OpenAIAdapter:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.url = "https://api.openai.com/v1/chat/completions"

    async def _call(self, messages, temperature=0.0, max_tokens=800):
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(self.url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()

    async def grade_submission(self, text: str, rubric: List[RubricItem]):
        # Build prompt that requests strict JSON output
        rubric_desc = [{"name": r.name, "max_score": r.max_score} for r in rubric]
        system = (
            "You are an education-assistant that grades student submissions. "
            "Return ONLY valid JSON following this schema: {total_score:int, rubric:[{name:str, max_score:int, score:int, evidence:str}], plagiarism_score:float, ai_likelihood:float, feedback:{summary:str, suggestions:[str]}}."
        )
        user = (
            f"Rubric: {json.dumps(rubric_desc)}\n\n" +
            f"Student submission:\n{text}\n\n" +
            "Give scores for each rubric item and brief evidence lines."
        )

        resp = await self._call([{"role": "system", "content": system}, {"role": "user", "content": user}])
        try:
            content = resp["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            # Map to objects similar to mock
            return parsed
        except Exception as e:
            # If parsing fails, fallback to a simple mock
            from .llm_adapter import LLMAdapter

            mock = LLMAdapter()
            return await mock.grade_submission(text, rubric)

    async def generate_docs(self, course_name: str, hours: int = 60, weeks: int = 15):
        system = "You produce a syllabus and an exam ticket. Respond as JSON: {syllabus:str, exam_ticket:str}."
        user = f"Create a {weeks}-week syllabus for {course_name} totaling {hours} hours. Output JSON only."
        resp = await self._call([{"role": "system", "content": system}, {"role": "user", "content": user}])
        try:
            content = resp["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception:
            # fallback
            weeks_list = "\n".join([f"Hafta {i}: Mavzu {i}" for i in range(1, weeks + 1)])
            return {"syllabus": f"{course_name} — {weeks}-haftalik o'quv rejasi.\n\n{weeks_list}", "exam_ticket": f"Bilet — {course_name}\n1) Nazariya\n2) Tushuntirish\n3) Amaliy"}

    async def generate_report(self, course_name: str, group_id: str = None):
        system = "Produce a short analytical summary for administration. Respond JSON: {summary:str, excel_path:null, analytics:{average_score:float, pass_rate:float, quality_rate:float, weak_topics:[{topic:str, average_score:float, difficulty:float}]}}."
        user = f"Create an admin summary for {course_name} (group {group_id})."
        resp = await self._call([{"role": "system", "content": system}, {"role": "user", "content": user}])
        try:
            content = resp["choices"][0]["message"]["content"]
            result = json.loads(content)
            if "analytics" not in result:
                result["analytics"] = {
                    "average_score": 78.0,
                    "pass_rate": 82.0,
                    "quality_rate": 64.0,
                    "weak_topics": [{"topic": "Mavzu 3", "average_score": 68.0, "difficulty": 32.0}],
                }
            return result
        except Exception:
            return {
                "summary": f"Guruh: {group_id or 'Barcha'} — {course_name}: O'rtacha 78%.",
                "excel_path": None,
                "analytics": {
                    "average_score": 78.0,
                    "pass_rate": 82.0,
                    "quality_rate": 64.0,
                    "weak_topics": [{"topic": "Mavzu 3", "average_score": 68.0, "difficulty": 32.0}],
                },
            }
