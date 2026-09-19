# AI O'qituvchi Hamkori — Minimal Demo

This workspace contains a runnable prototype for the AI Teacher Co-Pilot roadmap: a FastAPI backend and a Streamlit frontend with mock LLM behavior.

Quick start (requires Docker):

```bash
# From project root
docker-compose up --build
```

- Backend API: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501

Files of interest:
- `backend/app/main.py` — FastAPI app with `/api/grade`, `/api/generate-docs`, `/api/reports`
- `backend/app/llm_adapter.py` — mock LLM adapter (replace with real provider)
- `frontend/streamlit_app.py` — quick UI: Tekshirish, Hujjatlar, Hisobotlar
- `prompts/templates.json` — basic templates and rubric

Human-in-the-loop features:
- `/api/grades` — list saved grade records (for teacher review).
- `/api/grade/{grade_id}` — fetch stored grade details.
- `/api/grade/{grade_id}/confirm` — teacher confirms a grade.
- `/api/grade/{grade_id}/edit` — teacher edits and logs corrections.
- `/api/audit` — retrieve recent audit logs.

Streamlit UI notes:
- Tekshirish tab: upload/grade submissions and view saved grades via "Baholar ro'yxatini yuklash" button.
- Hisobotlar tab: use "Audit logni ko'rsatish" to inspect actions.

Next steps:
- Replace `llm_adapter` internals with OpenAI/Google API calls and proper prompt engineering.
- Improve rubric ingestion (teacher-specified rubrics) and file OCR for images.
- Add unit tests, authentication, and production DB (Postgres).
- Improve unit tests, CI and exports (automated cleanup of `exports/`).

Privacy & Data Handling:
- Talabalar shaxsiy ma'lumotlarini himoya qilish uchun faqat zarur minimal ma'lumotlar (student_id, ishlari) saqlanadi.
- Eksport qilingan fayllar `exports/` papkada saqlanadi; ishlab chiqishda ularni muntazam tozalash yoki avtomatik purj qilish mexanizmini qo'llang.
- Ishlab chiqarish uchun tavsiya: ma'lumotlar bazasida PII-ni maskalash, HTTPS, va diskdagi shifrlashni yoqing.
