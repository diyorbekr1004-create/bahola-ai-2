"""Sayt haqida yordamchi chat: bilimlar bazasi + joriy holat + LLM (yoki oflayn FAQ)."""
from __future__ import annotations

from typing import List

from sqlmodel import Session

from .. import assistant_kb, config, plans
from ..db import User
from ..llm import get_llm, provider_info
from ..schemas import ChatMessage, ChatResponse
from . import billing

MAX_HISTORY = 12


def _plans_summary() -> str:
    parts = []
    for p in plans.plans():
        price = "bepul" if not p.get("price_per_seat") else f"{int(p['price_per_seat']):,} so'm/{p.get('billing', 'oy')}".replace(",", " ")
        lim = p.get("limits", {}).get("grades_per_month")
        parts.append(f"- {p.get('title')}: {price}; tekshirish limiti: {lim if lim is not None else 'cheksiz'}; LLM: {'ha' if p.get('features', {}).get('llm') else 'yo`q'}; HEMIS eksport: {'ha' if p.get('features', {}).get('hemis_export') else 'yo`q'}")
    return "\n".join(parts)


def build_system_prompt(session: Session, user: User) -> str:
    info = provider_info()
    status = billing.status_for(session, user)
    u = status.usage
    limit_txt = f"{u.grades_used}/{u.grades_limit}" if u.grades_limit is not None else f"{u.grades_used} (cheksiz)"
    return (
        "Siz «AI O'qituvchi Hamkori» (Bahola AI) sayti bo'yicha do'stona yordamchisiz. Faqat quyidagi bilimlar bazasi va joriy holat asosida, "
        "o'zbek tilida (lotin), qisqa va aniq (3–6 jumla, kerak bo'lsa punktlar bilan) javob bering. Bilmagan narsangizni to'qib chiqarmang — "
        "«bu haqda ma'lumotim yo'q» deb ayting va qaysi bo'limga qarashni maslahat bering. Foydalanuvchini kerakli tabga yo'naltiring.\n\n"
        f"=== JORIY HOLAT ===\nAI provayder: {info['provider']} ({info.get('model') or 'oflayn'}). "
        f"Foydalanuvchi: {user.username} (rol: {user.role}), tarif: {status.plan_title}, shu oyda tekshirilgan ishlar: {limit_txt}. "
        f"Auth talab qilinadi: {'ha' if config.settings.auth_required else 'yo`q (demo)'}.\n\n"
        f"=== TARIFLAR ===\n{_plans_summary()}\n\n"
        f"=== BILIMLAR BAZASI ===\n{assistant_kb.knowledge_text()}"
    )


async def answer(session: Session, user: User, messages: List[ChatMessage]) -> ChatResponse:
    history = [{"role": m.role, "content": m.content} for m in messages if m.role in ("user", "assistant")][-MAX_HISTORY:]
    if not history or history[-1]["role"] != "user":
        history.append({"role": "user", "content": "Sayt haqida qisqacha ma'lumot bering."})
    llm = get_llm()
    info = provider_info()
    offline = info["provider"] == "mock"
    system = build_system_prompt(session, user)
    text = await llm.chat(history, system=system)
    last_q = history[-1]["content"]
    suggestions = [q for q in assistant_kb.suggested_questions(6) if q.lower() != last_q.lower()][:4]
    return ChatResponse(answer=text, provider=info["provider"], model=info.get("model"), suggestions=suggestions, offline=offline)
