"""AI O'qituvchi Hamkori — FastAPI backend.

Uchta asosiy oqim:
  1. Tekshirish  — /api/grade, /api/grade/batch, tasdiqlash/tuzatish (human-in-the-loop)
  2. Hujjatlar   — /api/generate-docs (silabus, dars rejasi, biletlar, testlar, DOCX)
  3. Hisobotlar  — /api/reports, /api/reports/export (Excel, HEMIS, CSV, dekanat DOCX)
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from . import config
from .db import RubricTemplate, dumps, engine, init_db
from .routers import auth, billing, chat, documents, grading, reports, rubrics, students, system
from .security import ensure_demo_users
from .services.grading import default_rubric_items

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bahola")


def seed_default_rubric() -> None:
    with Session(engine) as s:
        if s.exec(select(RubricTemplate).limit(1)).first():
            return
        items = [i.model_dump(exclude={"score", "evidence"}) for i in default_rubric_items()]
        s.add(RubricTemplate(name="Standart insho/referat rubrikasi", description="Dolzarblik, dalillar, tuzilma, til, xulosa (jami 100 ball)", items=dumps(items), is_default=True, created_by="system"))
        s.add(RubricTemplate(name="Amaliy/dasturlash topshirig'i", course=None, description="Kod va amaliy yechimlar uchun", items=dumps([
            {"name": "Topshiriqqa moslik", "max_score": 25, "description": "Talab qilingan funksionallik bajarilgan"},
            {"name": "Algoritm va mantiq", "max_score": 30, "description": "Yechim to'g'ri va samarali"},
            {"name": "Kod sifati va uslub", "max_score": 20, "description": "O'qilishi oson, nomlash, tuzilma"},
            {"name": "Tushuntirish va izohlar", "max_score": 15, "description": "Yechim izohlangan"},
            {"name": "Xulosa va natija", "max_score": 10, "description": "Natija tekshirilgan va umumlashtirilgan"},
        ]), is_default=False, created_by="system"))
        s.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_demo_users()
    seed_default_rubric()
    log.info("Baza tayyor: %s | LLM: %s", config.settings.database_url.split("@")[-1], config.settings.llm_provider)
    yield


app = FastAPI(
    title="AI O'qituvchi Hamkori — Backend",
    version=config.settings.app_version,
    description="Talaba ishlarini baholash, o'quv hujjatlarini yaratish, HEMIS/Excel eksport va analitika.",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for r in (system.router, auth.router, grading.router, documents.router, reports.router, students.router, rubrics.router, billing.router, chat.router):
    app.include_router(r)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("Kutilmagan xato: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": f"Ichki xato: {exc.__class__.__name__}"})


@app.get("/", include_in_schema=False)
def root():
    return {"app": config.settings.app_name, "version": config.settings.app_version, "docs": "/docs", "health": "/api/health"}
