"""Tariflar va raqobat ma'lumotlari (`config/pricing.json`)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config

FALLBACK_PRICING: Dict[str, Any] = {
    "currency": "so'm",
    "plans": [
        {"name": "free", "title": "Bepul", "price_per_seat": 0, "billing": "oy", "min_seats": 1, "tagline": "", "limits": {"grades_per_month": 30, "documents_per_month": 3},
         "features": {"llm": False, "batch": False, "hemis_export": False, "analytics": "asosiy", "shared_rubrics": False, "dean_dashboard": False, "on_premise": False, "support": "hamjamiyat"}, "highlights": []},
        {"name": "pro", "title": "Pro", "price_per_seat": 59000, "billing": "oy", "min_seats": 1, "tagline": "", "limits": {"grades_per_month": None, "documents_per_month": None},
         "features": {"llm": True, "batch": True, "hemis_export": True, "analytics": "to'liq", "shared_rubrics": False, "dean_dashboard": False, "on_premise": False, "support": "email"}, "highlights": []},
        {"name": "universitet", "title": "Universitet", "price_per_seat": 25000, "billing": "oy (yillik)", "min_seats": 100, "tagline": "", "limits": {"grades_per_month": None, "documents_per_month": None},
         "features": {"llm": True, "batch": True, "hemis_export": True, "analytics": "dekanat", "shared_rubrics": True, "dean_dashboard": True, "on_premise": True, "support": "SLA"}, "highlights": []},
    ],
    "addons": [],
    "payment_methods": ["Payme", "Click", "Bank hisob-faktura"],
    "competitors": {"columns": [], "rows": []},
    "advantages": [],
}

_cache: Optional[Dict[str, Any]] = None


def pricing_path() -> Path:
    return Path(config.settings.project_root) / "config" / "pricing.json"


def load_pricing(force: bool = False) -> Dict[str, Any]:
    global _cache
    if _cache is not None and not force:
        return _cache
    data: Dict[str, Any] = dict(FALLBACK_PRICING)
    try:
        raw = json.loads(pricing_path().read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("plans"), list) and raw["plans"]:
            data.update({k: v for k, v in raw.items() if not k.startswith("_")})
    except (OSError, ValueError):
        pass
    _cache = data
    return data


def reload_pricing() -> Dict[str, Any]:
    return load_pricing(force=True)


def plans() -> List[Dict[str, Any]]:
    return load_pricing()["plans"]


def plan_names() -> List[str]:
    return [p["name"] for p in plans()]


def get_plan(name: Optional[str]) -> Dict[str, Any]:
    for p in plans():
        if p["name"] == (name or "free"):
            return p
    return plans()[0]


def plan_rank(name: Optional[str]) -> int:
    names = plan_names()
    return names.index(name) if name in names else 0


def feature(plan: Dict[str, Any], key: str) -> Any:
    return (plan.get("features") or {}).get(key)


def limit(plan: Dict[str, Any], key: str) -> Optional[int]:
    return (plan.get("limits") or {}).get(key)


def price_total(plan: Dict[str, Any], seats: int, months: int) -> int:
    return int(plan.get("price_per_seat", 0)) * max(int(plan.get("min_seats", 1)), seats) * max(1, months)
