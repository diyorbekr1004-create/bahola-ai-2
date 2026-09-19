"""LLM provayderini tanlash (fabrika).

LLM_PROVIDER: auto | mock | gemini | openai
  auto -> GEMINI_API_KEY bo'lsa Gemini, bo'lmasa OPENAI_API_KEY bo'lsa OpenAI, aks holda oflayn (mock).
"""
from __future__ import annotations

from . import config
from .gemini_adapter import GeminiAdapter
from .llm_adapter import MockLLMAdapter
from .openai_adapter import OpenAIAdapter

_llm = None


def resolve_provider() -> str:
    s = config.settings
    provider = (s.llm_provider or "auto").lower()
    if provider == "auto":
        if s.gemini_api_key:
            return "gemini"
        if s.openai_api_key:
            return "openai"
        return "mock"
    if provider == "gemini" and not s.gemini_api_key:
        return "mock"
    if provider == "openai" and not s.openai_api_key:
        return "mock"
    return provider if provider in {"mock", "gemini", "openai"} else "mock"


def get_llm():
    """Sozlamalarga qarab adapter qaytaradi (singleton)."""
    global _llm
    if _llm is not None:
        return _llm
    s = config.settings
    provider = resolve_provider()
    if provider == "gemini":
        _llm = GeminiAdapter(api_key=s.gemini_api_key, model=s.gemini_model, base_url=s.gemini_base_url, timeout=s.llm_timeout_seconds)
    elif provider == "openai":
        _llm = OpenAIAdapter(api_key=s.openai_api_key, model=s.openai_model, base_url=s.openai_base_url, timeout=s.llm_timeout_seconds)
    else:
        _llm = MockLLMAdapter()
    return _llm


def reset_llm(adapter=None) -> None:
    """Testlar / sozlama o'zgarganda adapterni almashtirish."""
    global _llm
    _llm = adapter


def provider_info() -> dict:
    llm = get_llm()
    return {"provider": getattr(llm, "name", "mock"), "model": getattr(llm, "model", None)}
