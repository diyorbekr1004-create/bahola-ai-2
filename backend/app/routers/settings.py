"""LLM sozlamalari: kalitni to'g'ri joyga (.env) yozish, jonli qo'llash va ulanishni tekshirish."""
from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .. import config, env_store, llm
from ..security import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


def settings_access(user=Depends(get_current_user)):
    """Ishlab chiqarishda (AUTH_REQUIRED=true) faqat admin; demo rejimda hamma."""
    if config.settings.auth_required and user.role != "admin":
        raise HTTPException(status_code=403, detail="Sozlamalarni faqat administrator o'zgartiradi")
    return user


class LLMSettingsIn(BaseModel):
    provider: Optional[str] = Field(default=None, pattern="^(auto|gemini|openai|mock)$")
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    openai_base_url: Optional[str] = None
    persist: bool = True


class LLMSettingsOut(BaseModel):
    configured_provider: str
    active_provider: str
    active_model: Optional[str] = None
    gemini_key_set: bool
    gemini_key_masked: Optional[str] = None
    gemini_model: str
    openai_key_set: bool
    openai_key_masked: Optional[str] = None
    openai_model: str
    openai_base_url: str
    env_path: str
    env_exists: bool


class LLMTestOut(BaseModel):
    ok: bool
    provider: str
    model: Optional[str] = None
    sample: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None


def _status() -> LLMSettingsOut:
    s = config.settings
    info = llm.provider_info()
    return LLMSettingsOut(
        configured_provider=s.llm_provider, active_provider=info["provider"], active_model=info.get("model"),
        gemini_key_set=bool(s.gemini_api_key), gemini_key_masked=env_store.mask(s.gemini_api_key), gemini_model=s.gemini_model,
        openai_key_set=bool(s.openai_api_key), openai_key_masked=env_store.mask(s.openai_api_key), openai_model=s.openai_model, openai_base_url=s.openai_base_url,
        env_path=str(env_store.env_path()), env_exists=env_store.env_path().exists(),
    )


@router.get("/llm", response_model=LLMSettingsOut)
def get_llm_settings(user=Depends(settings_access)):
    return _status()


@router.post("/llm", response_model=LLMSettingsOut)
def set_llm_settings(payload: LLMSettingsIn, user=Depends(settings_access)):
    """Kalitni `.env` ga yozadi va darhol qo'llaydi (qayta ishga tushirish shart emas)."""
    if payload.gemini_api_key is not None and payload.gemini_api_key.strip() and len(payload.gemini_api_key.strip()) < 20:
        raise HTTPException(status_code=422, detail="Gemini kaliti juda qisqa — AIza... bilan boshlanadigan to'liq kalitni kiriting")
    env_store.apply_llm_settings(
        provider=payload.provider, gemini_key=payload.gemini_api_key, gemini_model=payload.gemini_model,
        openai_key=payload.openai_api_key, openai_model=payload.openai_model, openai_base_url=payload.openai_base_url, persist=payload.persist,
    )
    return _status()


@router.post("/llm/test", response_model=LLMTestOut)
async def test_llm_connection(user=Depends(settings_access)):
    """Joriy provayderga kichik so'rov yuboradi va natijani qaytaradi."""
    adapter = llm.get_llm()
    info = llm.provider_info()
    if info["provider"] == "mock":
        return LLMTestOut(ok=False, provider="mock", error="API kaliti kiritilmagan — hozir oflayn (evristik) rejim ishlayapti. Gemini kalitini kiriting.")
    started = time.perf_counter()
    text = await adapter._complete([{"role": "user", "content": "Bir jumlada o'zbek tilida salomlashing."}], temperature=0.2, max_tokens=60, json_mode=False)
    latency = int((time.perf_counter() - started) * 1000)
    if text:
        return LLMTestOut(ok=True, provider=info["provider"], model=info.get("model"), sample=text.strip()[:200], latency_ms=latency)
    return LLMTestOut(ok=False, provider=info["provider"], model=info.get("model"), error=(adapter.last_error or "Javob yo'q")[:400], latency_ms=latency)
