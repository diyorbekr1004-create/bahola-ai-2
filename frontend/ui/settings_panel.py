"""Yon panel: «🔑 AI kaliti» — Gemini/OpenAI kalitini to'g'ri joyga (.env) yozish va ulanishni tekshirish."""
from __future__ import annotations

import streamlit as st

from . import api


def render() -> None:
    with st.expander("🔑 AI kaliti (Gemini / OpenAI)", expanded=False):
        try:
            st_ = api.get("/api/settings/llm")
        except api.APIError as exc:
            st.caption(f"Sozlamalarni o'qib bo'lmadi: {exc}")
            return
        active = st_["active_provider"]
        if active == "gemini":
            st.success(f"Gemini ulangan: {st_['gemini_key_masked']} · {st_['active_model']}")
        elif active == "openai":
            st.success(f"OpenAI ulangan: {st_['openai_key_masked']} · {st_['active_model']}")
        else:
            st.warning("Kalit yo'q — oflayn (evristik) rejim. Gemini kalitini kiriting.")
        provider = st.selectbox("Provayder", ["gemini", "openai"], key="key_provider", help="Kalit `.env` fayliga yoziladi va darhol qo'llanadi")
        if provider == "gemini":
            key = st.text_input("GEMINI_API_KEY", type="password", key="key_gemini", placeholder="AIza… (aistudio.google.com/apikey)")
            model = st.text_input("Model", value=st_["gemini_model"], key="key_gemini_model")
        else:
            key = st.text_input("OPENAI_API_KEY", type="password", key="key_openai", placeholder="sk-…")
            model = st.text_input("Model", value=st_["openai_model"], key="key_openai_model")
        c1, c2 = st.columns(2)
        if c1.button("💾 Saqlash", key="key_save", width="stretch", type="primary"):
            payload = {"provider": "auto"}
            if provider == "gemini":
                payload.update({"gemini_api_key": key, "gemini_model": model})
            else:
                payload.update({"openai_api_key": key, "openai_model": model})
            try:
                res = api.post("/api/settings/llm", json=payload)
                api.invalidate()
                st.success(f"Saqlandi → {res['env_path']} · faol: {res['active_provider']}")
                st.rerun()
            except api.APIError as exc:
                st.error(str(exc))
        if c2.button("🔌 Ulanishni tekshirish", key="key_test", width="stretch"):
            try:
                with st.spinner("So'rov yuborilmoqda…"):
                    t = api.post("/api/settings/llm/test")
                if t["ok"]:
                    st.success(f"{t['provider']} · {t['model']} · {t['latency_ms']} ms\n\n«{t['sample']}»")
                else:
                    st.error(t.get("error") or "Ulanmadi")
            except api.APIError as exc:
                st.error(str(exc))
        if st.button("Oflayn rejimga qaytish", key="key_mock"):
            try:
                api.post("/api/settings/llm", json={"provider": "mock"})
                api.invalidate()
                st.rerun()
            except api.APIError as exc:
                st.error(str(exc))
        st.caption(f"`.env`: {st_['env_path']}")
