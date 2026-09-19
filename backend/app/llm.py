"""LLM provayderini tanlash (fabrika)."""
from __future__ import annotations


from . import config
from .llm_adapter import MockLLMAdapter
from .openai_adapter import OpenAIAdapter

_llm = None


def get_llm():
    """Sozlamalarga qarab adapter qaytaradi (singleton)."""
    global _llm
    if _llm is not None:
        return _llm
    s = config.settings
    provider = s.llm_provider
    if provider == "auto":
        provider = "openai" if s.openai_api_key else "mock"
    if provider == "openai" and s.openai_api_key:
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
