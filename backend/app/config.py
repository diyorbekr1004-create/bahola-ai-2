"""Markaziy sozlamalar (environment orqali boshqariladi).

Barcha qiymatlar .env yoki muhit o'zgaruvchilaridan o'qiladi. Testlar va
skriptlar `reload_settings()` orqali qayta yuklashi mumkin.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# .env faylini (agar mavjud bo'lsa) loyiha ildizidan yuklaymiz
_ROOT = Path(os.getenv("PROJECT_ROOT") or Path(__file__).resolve().parents[2]).resolve()
load_dotenv(_ROOT / ".env", override=False)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    # --- Umumiy ---
    app_name: str = "AI O'qituvchi Hamkori"
    app_version: str = "2.0.0"
    project_root: Path = _ROOT

    # --- Ma'lumotlar bazasi ---
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data.db"))

    # --- Xavfsizlik ---
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret-change-me"))
    access_token_expire_minutes: int = field(default_factory=lambda: _env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))
    # AUTH_REQUIRED=false bo'lsa token bo'lmagan so'rovlar "demo" o'qituvchi sifatida ishlaydi
    auth_required: bool = field(default_factory=lambda: _env_bool("AUTH_REQUIRED", False))
    # Demo foydalanuvchilarni (teacher/admin/dekan) avtomatik yaratish
    demo_users: bool = field(default_factory=lambda: _env_bool("DEMO_USERS", True))

    # --- LLM provayder ---
    # LLM_PROVIDER: auto | mock | gemini | openai  (auto: Gemini kaliti bo'lsa Gemini, keyin OpenAI, aks holda oflayn)
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "auto").strip().lower())
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", "").strip())
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip())
    gemini_base_url: str = field(default_factory=lambda: os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/"))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", "").strip())
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip())
    # OpenAI-ga mos har qanday server (Groq, OpenRouter, Ollama, Azure OpenAI gateway ...)
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"))
    llm_timeout_seconds: float = field(default_factory=lambda: _env_float("LLM_TIMEOUT_SECONDS", 60.0))

    # --- Eksport ---
    export_dir: Path = field(default_factory=lambda: Path(os.getenv("EXPORT_DIR", str(_ROOT / "exports"))).resolve())
    hemis_template_path: Path = field(
        default_factory=lambda: Path(os.getenv("HEMIS_TEMPLATE_PATH", str(_ROOT / "config" / "hemis_template.json"))).resolve()
    )

    # --- Baholash shkalasi (100 ballik -> 5 ballik) ---
    # O'zbekiston OTMlarida keng tarqalgan shkala: 86-100 -> 5, 71-85 -> 4, 56-70 -> 3, 0-55 -> 2
    grade5_min: float = field(default_factory=lambda: _env_float("GRADE_5_MIN", 86))
    grade4_min: float = field(default_factory=lambda: _env_float("GRADE_4_MIN", 71))
    grade3_min: float = field(default_factory=lambda: _env_float("GRADE_3_MIN", 56))

    # --- Analitika ---
    # O'qituvchi bitta ishni qo'lda tekshirishga sarflaydigan o'rtacha vaqt (daqiqa)
    minutes_per_manual_check: float = field(default_factory=lambda: _env_float("MINUTES_PER_MANUAL_CHECK", 12))
    plagiarism_flag_threshold: float = field(default_factory=lambda: _env_float("PLAGIARISM_FLAG_THRESHOLD", 0.4))
    ai_flag_threshold: float = field(default_factory=lambda: _env_float("AI_FLAG_THRESHOLD", 0.6))
    similarity_flag_threshold: float = field(default_factory=lambda: _env_float("SIMILARITY_FLAG_THRESHOLD", 0.6))

    # --- Tariflar / to'lov ---
    # Tizimga kirmagan (demo) foydalanuvchining tarifi
    default_plan: str = field(default_factory=lambda: os.getenv("DEFAULT_PLAN", "universitet").strip().lower())
    # Limitlar va funksiya cheklovlarini qo'llash
    plan_enforcement: bool = field(default_factory=lambda: _env_bool("PLAN_ENFORCEMENT", True))
    # true: obuna so'rovini egasining o'zi "to'lov qildim" deb tasdiqlashi mumkin (demo); false: faqat admin
    demo_payments: bool = field(default_factory=lambda: _env_bool("DEMO_PAYMENTS", True))

    # --- Fayl cheklovlari ---
    max_upload_mb: int = field(default_factory=lambda: _env_int("MAX_UPLOAD_MB", 10))
    max_batch_files: int = field(default_factory=lambda: _env_int("MAX_BATCH_FILES", 100))

    @property
    def pass_threshold(self) -> float:
        """O'zlashtirish chegarasi (3 baho)."""
        return self.grade3_min

    @property
    def quality_threshold(self) -> float:
        """Sifat ko'rsatkichi chegarasi (4 va 5 baho)."""
        return self.grade4_min

    @property
    def grade_thresholds(self) -> dict:
        return {5: self.grade5_min, 4: self.grade4_min, 3: self.grade3_min}


settings = Settings()


def reload_settings() -> Settings:
    """Muhit o'zgaruvchilari o'zgargandan keyin sozlamalarni qayta o'qiydi (testlar uchun)."""
    global settings
    settings = Settings()
    return settings
