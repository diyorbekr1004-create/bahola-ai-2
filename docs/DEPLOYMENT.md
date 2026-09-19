# Joylashtirish (deployment)

## 1. Lokal (Docker Compose)

```bash
cp .env.example .env         # kerak bo'lsa OPENAI_API_KEY, SECRET_KEY
docker compose up --build
```

- PostgreSQL 16 (`db`), backend `http://localhost:8000/docs`, frontend `http://localhost:8501`.
- Eksport fayllari `exports` nomli volume'da; HEMIS shabloni `./config` dan o'qiladi.
- Demo ma'lumot: `docker compose exec backend python -c "..."` o'rniga lokal `python scripts/seed.py` ni `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_teacher_db` bilan ishga tushiring.

## 2. Lokal (Docker'siz)

```bash
pip install -r backend/requirements.txt
python scripts/seed.py --reset
make dev         # yoki: scripts/run_dev.sh, Windows: scripts\run_dev.ps1
```

## 3. Ishlab chiqarish uchun tekshiruv ro'yxati

- [ ] `DATABASE_URL` — boshqariladigan PostgreSQL (Azure Database for PostgreSQL, Cloud SQL, RDS).
- [ ] `SECRET_KEY` — kamida 32 belgili tasodifiy satr; `AUTH_REQUIRED=true`; `DEMO_USERS=false`.
- [ ] `GEMINI_API_KEY` (yoki `OPENAI_API_KEY`) maxfiy saqlanadi (Key Vault / Secrets Manager), `LLM_PROVIDER=auto`.
- [ ] HTTPS (reverse proxy: nginx / Caddy / App Service TLS).
- [ ] `EXPORT_DIR` uchun doimiy disk va tozalash siyosati (masalan, 30 kundan eski fayllarni o'chirish).
- [ ] Bazani zaxiralash (kunlik) va audit jurnalini saqlash muddati.
- [ ] `MAX_UPLOAD_MB`, `MAX_BATCH_FILES` cheklovlarini oliygoh yuklamasiga moslang.

## 4. Azure (variant)

- **Backend:** Azure App Service (Linux, konteyner) yoki Azure Container Apps — `Dockerfile` ildizda. Muhit o'zgaruvchilari App Settings orqali.
- **Frontend:** alohida App Service / Container App (`frontend/Dockerfile`), `BACKEND_URL` = backend manzili.
- **Baza:** Azure Database for PostgreSQL Flexible Server; `DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require`.
- **LLM:** Azure OpenAI bo'lsa `OPENAI_BASE_URL` ni OpenAI-ga mos gateway manziliga yo'naltiring yoki `OPENAI_API_KEY` bilan OpenAI'dan foydalaning.

## 5. Streamlit Community Cloud (faqat frontend)

Repozitoriyni ulang, entry: `frontend/streamlit_app.py`, requirements: `frontend/requirements.txt`, secrets: `backend_url = "https://<backend-manzili>"`.

## 6. Yangilanish va migratsiya

`init_db()` jadvallarni yaratadi va modelga qo'shilgan yangi ustunlarni `ALTER TABLE ... ADD COLUMN` bilan avtomatik qo'shadi — eski `data.db` ishlayveradi. Ustun turini o'zgartirish yoki o'chirish kerak bo'lsa Alembic'dan foydalaning.
