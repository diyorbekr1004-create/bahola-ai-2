# 🎓 AI O'qituvchi Hamkori (Bahola AI)

**Talaba ishlarini AI bilan tekshirish → o'qituvchi tasdiqlaydi → HEMIS/Excel eksport → kafedra uchun analitika.**
O'qituvchining haftalik 15–20 soatlik tekshirish va qog'oz to'ldirish vaqtini 1–2 soatga qisqartiradigan, bir kishi ishlab chiqishi va namoyish qilishi mumkin bo'lgan to'liq tizim.

[![CI](https://github.com/diyorbekr1004-create/bahola-ai-2/actions/workflows/ci.yml/badge.svg)](https://github.com/diyorbekr1004-create/bahola-ai-2/actions/workflows/ci.yml)

## Nimalar qila oladi

| Bo'lim | Imkoniyatlar |
|---|---|
| 🔎 **Tekshirish** | Matn / TXT / DOCX / PDF / **ZIP (batch)** yuklash · rubrika (mezonlar) bo'yicha ball va **asoslar** · aniqlangan **xatolar**, kuchli tomonlar, tavsiyalar · plagiat, AI-matn va **guruh ichidagi o'xshashlik** tekshiruvi · etalon javob bilan solishtirish · **Human-in-the-loop**: tasdiqlash / mezon bo'yicha tuzatish / izoh · talabaga DOCX fikr-mulohaza · audit jurnali |
| 📄 **Hujjatlar** | Fan nomi → **15 haftalik silabus** (soatlar, nazoratlar, adabiyotlar) · **dars rejasi** (80 daq. bosqichlar) · **imtihon biletlari** (N variant) · **test savollari** (4 variant, javoblar kaliti) · hammasi bitta **DOCX** faylda |
| 📊 **Hisobotlar** | Guruh bo'yicha **o'zlashtirish** va **sifat ko'rsatkichi** · 5 ballik taqsimot · **qiyin mavzular** va **qiyin mezonlar** reytingi · guruhlar taqqoslash · **xavf guruhi** · AI ↔ o'qituvchi mosligi · tejalgan vaqt · **kafedra mudiri / dekanat uchun tahliliy xulosa** · eksport: **HEMIS XLSX**, to'liq Excel (5 varaq), CSV, dekanat DOCX |
| 👥 **Talabalar** | HEMIS ro'yxatini XLSX/CSV import · guruhlar · rubrika shablonlari |

Barcha natijalar **yagona bazada** (SQLite default, PostgreSQL bir qatorda) saqlanadi. LLM ulanmagan bo'lsa ham tizim **to'liq oflayn** ishlaydi (deterministik evristik baholash); `OPENAI_API_KEY` berilsa OpenAI (yoki OpenAI-ga mos har qanday server: Groq, OpenRouter, Ollama) ishlatiladi va xato bo'lsa avtomatik oflayn rejimga qaytadi.

## Tez boshlash (3 buyruq)

```bash
python -m venv .venv && . .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
python scripts/seed.py --reset                        # 30 talaba, 110 baholangan ish, 1 hujjatlar to'plami
```

So'ng ikkita terminalda (yoki `make dev` / `scripts\run_dev.ps1`):

```bash
cd backend && uvicorn app.main:app --reload            # API:  http://localhost:8000/docs
streamlit run frontend/streamlit_app.py               # UI:   http://localhost:8501
```

Demo login: `teacher / teacher123` (admin/admin123, dekan/dekan123). `AUTH_REQUIRED=false` (default) rejimida login shart emas.

### Docker

```bash
cp .env.example .env            # OPENAI_API_KEY ni ixtiyoriy to'ldiring
docker compose up --build       # PostgreSQL + backend (8000) + frontend (8501)
```

## Loyiha tuzilmasi

```
backend/app/
  main.py               FastAPI ilova (lifespan: baza, demo userlar, standart rubrika)
  config.py             .env sozlamalari (shkala, chegaralar, provayder)
  db.py                 SQLModel modellari + yengil migratsiya (ADD COLUMN)
  schemas.py            Pydantic v2 sxemalar
  security.py           PBKDF2 parol, JWT, rollar, demo rejim
  llm.py / llm_adapter.py / openai_adapter.py   provayder fabrikasi, oflayn evristika, OpenAI (JSON mode)
  content_bank.py       fan mavzulari banki, silabus/bilet/test/dars rejasi quruvchilar
  plagiarism_detector.py plagiat, AI-matn, guruh ichidagi o'xshashlik
  file_parser.py        TXT/DOCX/PDF/ZIP/XLSX/CSV
  analytics.py          o'zlashtirish, sifat, 5 ballik, qiyin mavzular, xavf guruhi, xulosa matni
  exports.py            Excel (5 varaq), HEMIS XLSX/CSV, DOCX (hujjatlar, dekanat hisoboti, talaba fikr-mulohazasi)
  services/             grading, documents, reports
  routers/              system, auth, grading, documents, reports, students, rubrics
backend/tests/          39 ta test (pytest)
frontend/streamlit_app.py + frontend/ui/   4 tabli boshqaruv paneli (Plotly grafiklar)
config/hemis_template.json   HEMIS ustunlari (oliygohga moslab o'zgartiriladi)
prompts/templates.json       standart rubrika va promptlar
scripts/seed.py              demo ma'lumotlar
docs/                        PRESENTATION.md, HEMIS_EXPORT.md, API.md, DEPLOYMENT.md
```

## Asosiy API (to'liq ro'yxat: `docs/API.md` yoki `/docs`)

| Metod | Yo'l | Vazifa |
|---|---|---|
| POST | `/api/grade` | matn/fayl + metadata + rubrika → strukturalangan baho |
| POST | `/api/grade/batch` | bir nechta fayl yoki ZIP → barcha ishlar |
| GET | `/api/grades` · `/api/grade/{id}` | ro'yxat (filtrlar) va tafsilot |
| POST | `/api/grade/{id}/confirm` · `/edit` | o'qituvchi tasdiqlashi / mezon bo'yicha tuzatishi |
| GET | `/api/grade/{id}/feedback.docx` | talaba uchun fikr-mulohaza |
| POST | `/api/generate-docs` | silabus, dars rejasi, biletlar, testlar (+DOCX) |
| POST | `/api/reports` | analitika + xulosa + eksport havolalari |
| GET | `/api/reports/export?format=hemis\|excel\|csv\|dean` | faylni yuklab olish |
| POST | `/api/students/import` | HEMIS ro'yxati (XLSX/CSV) |
| GET/POST | `/api/rubrics`, `/api/assignments`, `/api/groups`, `/api/students` | ma'lumotnomalar |
| GET | `/api/stats`, `/api/audit`, `/api/health`, `/api/config` | tizim |

## Sozlamalar (`.env.example`)

- `DATABASE_URL` — `sqlite:///./data.db` yoki `postgresql://...`
- `LLM_PROVIDER` — `auto` / `mock` / `openai`; `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`
- `AUTH_REQUIRED` — `true` bo'lsa JWT majburiy; `SECRET_KEY` ni albatta almashtiring
- `GRADE_5_MIN / GRADE_4_MIN / GRADE_3_MIN` — 100→5 ballik shkala (default 86/71/56)
- `MINUTES_PER_MANUAL_CHECK` — "tejalgan vaqt" hisobi uchun (default 12 daqiqa/ish)
- `HEMIS_TEMPLATE_PATH` — HEMIS ustunlari shabloni

## Testlar

```bash
cd backend && pytest -q        # 39 passed
python -m pyflakes backend/app frontend scripts
```

## Hujjatlar

- [docs/PRESENTATION.md](docs/PRESENTATION.md) — xakaton taqdimoti va 3 ta jonli demo ssenariysi
- [docs/HEMIS_EXPORT.md](docs/HEMIS_EXPORT.md) — HEMIS jadvali formati va moslashtirish
- [docs/API.md](docs/API.md) — endpointlar va misollar
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Docker, Postgres, Azure/Streamlit Cloud
- [PRIVACY.md](PRIVACY.md) — shaxsiy ma'lumotlar siyosati

## Litsenziya

MIT (o'quv va xakaton maqsadlarida erkin foydalaning).
