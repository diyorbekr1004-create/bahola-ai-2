"""`.env` faylini xavfsiz yangilash va LLM sozlamalarini jonli qo'llash."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Optional

from . import config

ALLOWED_KEYS = {"LLM_PROVIDER", "GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_BASE_URL", "OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL"}
_KEY_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


def env_path() -> Path:
    return Path(config.settings.project_root) / ".env"


def update_env_file(path: Path, updates: Dict[str, Optional[str]]) -> Path:
    """KEY=VALUE qatorlarini almashtiradi yoki oxiriga qo'shadi; izohlar va boshqa qatorlar saqlanadi.

    `None` qiymat kalitni bo'sh qoldiradi (KEY=).
    """
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    if not lines:
        example = path.parent / ".env.example"
        if example.exists():
            lines = example.read_text(encoding="utf-8").splitlines()
    remaining = dict(updates)
    out = []
    for line in lines:
        m = _KEY_RE.match(line)
        if m and m.group(1) in remaining:
            key = m.group(1)
            out.append(f"{key}={remaining.pop(key) or ''}")
        else:
            out.append(line.rstrip("\r"))
    for key, value in remaining.items():
        out.append(f"{key}={value or ''}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def mask(secret: Optional[str]) -> Optional[str]:
    if not secret:
        return None
    if len(secret) <= 8:
        return "•" * len(secret)
    return f"{secret[:4]}…{secret[-4:]}"


def apply_llm_settings(*, provider: Optional[str] = None, gemini_key: Optional[str] = None, gemini_model: Optional[str] = None,
                       openai_key: Optional[str] = None, openai_model: Optional[str] = None, openai_base_url: Optional[str] = None, persist: bool = True) -> Dict[str, str]:
    """Sozlamalarni xotirada (config.settings + os.environ) va `.env` da yangilaydi, LLM adapterini qayta yaratadi."""
    from .llm import reset_llm

    s = config.settings
    updates: Dict[str, Optional[str]] = {}
    if provider is not None:
        s.llm_provider = provider.strip().lower() or "auto"
        updates["LLM_PROVIDER"] = s.llm_provider
    if gemini_key is not None:
        s.gemini_api_key = gemini_key.strip()
        updates["GEMINI_API_KEY"] = s.gemini_api_key
    if gemini_model:
        s.gemini_model = gemini_model.strip()
        updates["GEMINI_MODEL"] = s.gemini_model
    if openai_key is not None:
        s.openai_api_key = openai_key.strip()
        updates["OPENAI_API_KEY"] = s.openai_api_key
    if openai_model:
        s.openai_model = openai_model.strip()
        updates["OPENAI_MODEL"] = s.openai_model
    if openai_base_url:
        s.openai_base_url = openai_base_url.strip().rstrip("/")
        updates["OPENAI_BASE_URL"] = s.openai_base_url
    for k, v in updates.items():
        os.environ[k] = v or ""
    if persist and updates:
        update_env_file(env_path(), updates)
    reset_llm()
    return {k: (mask(v) if "KEY" in k else (v or "")) for k, v in updates.items()}
