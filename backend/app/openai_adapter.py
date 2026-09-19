"""OpenAI-ga mos (chat/completions) provayder adapteri.

`OPENAI_BASE_URL` orqali OpenAI, Azure OpenAI gateway, Groq, OpenRouter,
Ollama (`http://localhost:11434/v1`) kabi har qanday mos serverga ulanadi.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from .llm_base import ChatLLMAdapter

log = logging.getLogger("bahola.openai")


class OpenAIAdapter(ChatLLMAdapter):
    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None, timeout: float = 60.0):
        super().__init__()
        from .config import settings

        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.timeout = timeout or settings.llm_timeout_seconds

    async def _complete(self, messages: List[dict], *, temperature: float = 0.1, max_tokens: int = 2500, json_mode: bool = True) -> Optional[str]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload: Dict[str, Any] = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if r.status_code == 400 and json_mode:
                    payload.pop("response_format", None)  # ba'zi serverlar response_format'ni qo'llamaydi
                    r = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            self.last_error = str(exc)
            log.warning("OpenAI so'rovi muvaffaqiyatsiz: %s", exc)
            return None
