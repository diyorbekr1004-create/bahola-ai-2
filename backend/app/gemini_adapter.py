"""Google Gemini (Generative Language API) provayder adapteri.

REST `models/{model}:generateContent` orqali ishlaydi (SDK talab qilinmaydi).
JSON-rejim: `generationConfig.responseMimeType = application/json`.
Sozlamalar: GEMINI_API_KEY, GEMINI_MODEL (default gemini-2.5-flash), GEMINI_BASE_URL.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from .llm_base import ChatLLMAdapter

log = logging.getLogger("bahola.gemini")


class GeminiAdapter(ChatLLMAdapter):
    name = "gemini"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None, timeout: float = 60.0):
        super().__init__()
        from .config import settings

        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.base_url = (base_url or settings.gemini_base_url).rstrip("/")
        self.timeout = timeout or settings.llm_timeout_seconds

    @staticmethod
    def build_payload(messages: List[dict], *, temperature: float, max_tokens: int, json_mode: bool) -> Dict[str, Any]:
        """OpenAI uslubidagi xabarlarni Gemini formatiga o'tkazadi."""
        system_parts = [m["content"] for m in messages if m.get("role") == "system" and m.get("content")]
        contents = []
        for m in messages:
            role = m.get("role")
            if role == "system" or not m.get("content"):
                continue
            contents.append({"role": "model" if role == "assistant" else "user", "parts": [{"text": str(m["content"])}]})
        if not contents:
            contents = [{"role": "user", "parts": [{"text": " "}]}]
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        return payload

    @staticmethod
    def extract_text(data: Dict[str, Any]) -> Optional[str]:
        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts if isinstance(p, dict)) or None
        except (KeyError, IndexError, TypeError):
            return None

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()

    async def _complete(self, messages: List[dict], *, temperature: float = 0.1, max_tokens: int = 2500, json_mode: bool = True) -> Optional[str]:
        payload = self.build_payload(messages, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode)
        try:
            data = await self._post(payload)
            text = self.extract_text(data)
            if text is None:
                self.last_error = f"Bo'sh javob: {str(data)[:200]}"
            return text
        except Exception as exc:  # noqa: BLE001
            self.last_error = str(exc)
            log.warning("Gemini so'rovi muvaffaqiyatsiz: %s", exc)
            return None
