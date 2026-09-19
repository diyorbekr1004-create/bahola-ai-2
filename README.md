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
| 💬 **Yordamchi** | Sayt haqida AI chat: baholash, HEMIS eksport, tariflar, sozlamalar bo'yicha savol-javob (`config/assistant_knowledge.md` bilimlar bazasi); Gemini/OpenAI bo'lsa erkin suhbat, bo'lmasa oflayn FAQ |
| 💳 **Tariflar** | Free / Pro / Kafedra / Universitet rejalari (`config/pricing.json`) · oylik limitlar va funksiya cheklovlari (LLM, batch, HEMIS eksport) · obuna va to'lov so'rovi (hisob-faktura, Payme/Click/Uzum/bank) · ROI kalkulyator · raqobatchilar bilan taqqoslash va ustunliklar |

Barcha natijalar **yagona bazada** (SQLite default, PostgreSQL bir qatorda) saqlanadi. Tekshirish **Google Gemini** orqali ishlaydi (`GEMINI_API_KEY`); zaxira sifatida OpenAI yoki OpenAI-ga mos server (Groq, OpenRouter, Ollama) ulanadi. Kalit bo'lmasa yoki API xato bersa tizim **to'liq oflayn** ishlaydi (deterministik evristik baholash) — namoyish hech qachon to'xtamaydi.

## Tez boshlash

**Talab:** Python 3.11 – 3.14 (tavsiya: **3.12**). Boshqa hech narsa kerak emas — barcha paketlar tayyor wheel bilan o'rnatiladi.

Bitta buyruq bilan (venv + paketlar + demo ma'lumot + testlar):

```powershell
# Windows (PowerShell, loyiha ildizidan)
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

```bash
# Linux / macOS / Windows Git Bash
bash scripts/setup.sh
```

> Windows'da terminal **Git Bash** bo'lsa (`bash:` bilan boshlanadigan xabarlar), PowerShell buyruqlari (`Remove-Item`, `scripts\...`) ishlamaydi — `bash scripts/setup.sh` dan foydalaning va yo'llarda `/` yozing.

Yoki qo'lda:

```bash
py -3.12 -m venv .venv && .venv\Scripts\activate       # Linux/macOS: python3.12 -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements.txt
python scripts/seed.py --reset                        # 30 talaba, 110 baholangan ish, 1 hujjatlar to'plami
```

So'ng **bitta buyruq** (Streamlit backendni o'zi ishga tushiradi, log: `backend.log`):

```bash
streamlit run frontend/streamlit_app.py               # UI: http://localhost:8501 · API: http://localhost:8000/docs
```

Alohida boshqarish uchun: `cd backend && uvicorn app.main:app --reload` + `streamlit run ...` yoki `bash scripts/run_dev.sh`. Avto-ishga tushirishni o'chirish: `AUTO_START_BACKEND=false`.

**Gemini kaliti:** yon paneldagi «🔑 AI kaliti» bo'limiga kalitni qo'ying → «Saqlash» (`.env` ga yoziladi, darhol qo'llanadi) → «Ulanishni tekshirish».

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
  llm_base.py / gemini_adapter.py / openai_adapter.py   provayderlar (Gemini asosiy), JSON-rejim, oflaynga qaytish
  assistant_kb.py       yordamchi chat bilimlar bazasi (config/assistant_knowledge.md) va oflayn FAQ
  config.py             .env sozlamalari (shkala, chegaralar, provayder)
  db.py                 SQLModel modellari + yengil migratsiya (ADD COLUMN)
  schemas.py            Pydantic v2 sxemalar
  security.py           PBKDF2 parol, JWT, rollar, demo rejim
  llm.py / llm_adapter.py   provayder fabrikasi, oflayn deterministik evristika
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
| POST | `/api/chat`, `GET /api/chat/suggestions` | sayt haqida yordamchi chat |
| GET/POST | `/api/settings/llm`, `POST /api/settings/llm/test` | AI kalitini `.env` ga yozish, jonli qo'llash, ulanish testi |
| GET/POST | `/api/plans`, `/api/competitors`, `/api/subscription`, `/api/subscription/{id}/confirm`, `/api/subscription/cancel` | tariflar va obuna (402 — tarif cheklovi) |

## Sozlamalar (`.env.example`)

- `DATABASE_URL` — `sqlite:///./data.db` yoki `postgresql://...`
- `LLM_PROVIDER` — `auto` / `gemini` / `openai` / `mock`; `GEMINI_API_KEY`, `GEMINI_MODEL` (default `gemini-2.5-flash`); `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`
- `AUTH_REQUIRED` — `true` bo'lsa JWT majburiy; `SECRET_KEY` ni albatta almashtiring
- `GRADE_5_MIN / GRADE_4_MIN / GRADE_3_MIN` — 100→5 ballik shkala (default 86/71/56)
- `MINUTES_PER_MANUAL_CHECK` — "tejalgan vaqt" hisobi uchun (default 12 daqiqa/ish)
- `HEMIS_TEMPLATE_PATH` — HEMIS ustunlari shabloni
- `DEFAULT_PLAN` (demo foydalanuvchi tarifi), `PLAN_ENFORCEMENT`, `DEMO_PAYMENTS` — tariflar; narxlar `config/pricing.json` da

## Testlar

```bash
cd backend && pytest -q        # 39 passed
python -m pyflakes backend/app frontend scripts
```

## Muammolar va yechimlar (dev environment)

| Belgi | Sabab | Yechim |
|---|---|---|
| `Could not find vswhere.exe` / pandas build xatosi | Eski `requirements.txt` dagi qat'iy pin (`pandas==2.2.2`) yangi Python uchun wheel'siz edi, pip manbadan qurishga urindi | Joriy `backend/requirements.txt` dan o'rnating (diapazonlar), Python 3.12 tavsiya etiladi |
| `conflicting dependencies` (`sqlmodel 0.0.8`, `pydantic`, `fastapi 0.100`) | Eski pinlar Pydantic v1/v2 aralashgan | Joriy fayl Pydantic v2 + SQLModel 0.0.22+ ga mos, konflikt yo'q |
| `No matching distribution found for python-docx==0.8.12` / `passlib==1.8.2` | Mavjud bo'lmagan/eskirgan pinlar | Joriy faylda `python-docx>=1.1`, `passlib` umuman ishlatilmaydi (stdlib PBKDF2 + PyJWT) |
| `No module named pytest` | O'rnatish yarmida to'xtagan | `pip install -r backend/requirements.txt` ni qayta bajaring, keyin `cd backend && pytest -q` |
| Eski `.venv` ichida chalkash paketlar | Bir nechta o'rnatish urinishi | `.venv` papkasini o'chirib `scripts\setup.ps1` ni qayta ishga tushiring |
| `bash scripts/...sh` hech narsa chiqarmay tugaydi yoki `$'\r': command not found` / `set: pipefail\r: invalid option` | Git for Windows fayllarni CRLF bilan yuklab olgan | `git pull` qiling (`.gitattributes` qo'shilgan), so'ng `git rm -r --cached -q . && git reset -q --hard` — fayllar LF bilan qayta yoziladi; `.env` bo'lsa `sed -i 's/\r$//' .env` |
| `streamlit` ochilmayapti, «Backend ishlamayapti» | Backend alohida jarayonda ishga tushmagan | Avval `cd backend && uvicorn app.main:app --reload`, keyin Streamlit; yoki `scripts\run_dev.ps1` |

## Hujjatlar

- [docs/PRESENTATION.md](docs/PRESENTATION.md) — xakaton taqdimoti va 3 ta jonli demo ssenariysi
- [docs/HAKAMLAR_MEZONLARI.md](docs/HAKAMLAR_MEZONLARI.md) — texnik / biznes / soha mentorlari mezonlari bo'yicha javoblar
- [docs/BIZNES_MODEL.md](docs/BIZNES_MODEL.md) — bozor, tariflar, unit-ekonomika, raqobat, 3 yillik prognoz, risklar
- [docs/SLIDES_PROMPT.md](docs/SLIDES_PROMPT.md) — slayd generatori uchun tayyor prompt (skrinshotlar `docs/img/`)
- [docs/HEMIS_EXPORT.md](docs/HEMIS_EXPORT.md) — HEMIS jadvali formati va moslashtirish
- [docs/API.md](docs/API.md) — endpointlar va misollar
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Docker, Postgres, Azure/Streamlit Cloud
- [PRIVACY.md](PRIVACY.md) — shaxsiy ma'lumotlar siyosati

## Litsenziya

MIT (o'quv va xakaton maqsadlarida erkin foydalaning).
