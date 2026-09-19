"""6-tab: Yordamchi — sayt haqida savol-javob (LLM yoki oflayn FAQ)."""
from __future__ import annotations

import streamlit as st

from . import api

WELCOME = ("Salom! Men AI O'qituvchi Hamkori bo'yicha yordamchiman. Baholash, HEMIS eksport, hujjatlar, tariflar yoki "
           "sozlamalar haqida so'rang — kerakli bo'limga yo'naltiraman.")


def _ask(question: str) -> None:
    history = st.session_state.setdefault("chat_history", [])
    history.append({"role": "user", "content": question})
    try:
        res = api.post("/api/chat", json={"messages": [{"role": m["role"], "content": m["content"]} for m in history[-12:]]})
        history.append({"role": "assistant", "content": res["answer"]})
        st.session_state["chat_suggestions"] = res.get("suggestions") or []
        st.session_state["chat_provider"] = f"{res.get('provider')}{' (oflayn FAQ)' if res.get('offline') else ' · ' + str(res.get('model') or '')}"
    except api.APIError as exc:
        history.append({"role": "assistant", "content": f"Xatolik: {exc}"})


def render() -> None:
    st.subheader("💬 Yordamchi — sayt haqida savol bering")
    if "chat_suggestions" not in st.session_state:
        try:
            s = api.get("/api/chat/suggestions")
            st.session_state["chat_suggestions"] = s.get("suggestions") or []
            st.session_state["chat_provider"] = f"{s.get('provider')}{' (oflayn FAQ)' if s.get('offline') else ' · ' + str(s.get('model') or '')}"
        except api.APIError:
            st.session_state["chat_suggestions"] = []
            st.session_state["chat_provider"] = "—"
    c1, c2 = st.columns([3, 1])
    c1.caption(f"Javob beruvchi: **{st.session_state.get('chat_provider', '—')}**. Gemini kaliti qo'shilsa javoblar erkin suhbat rejimida bo'ladi.")
    if c2.button("🧹 Suhbatni tozalash", key="chat_clear", width="stretch"):
        st.session_state["chat_history"] = []
        st.rerun()

    suggestions = st.session_state.get("chat_suggestions") or []
    if suggestions:
        cols = st.columns(min(4, len(suggestions)))
        for i, (col, q) in enumerate(zip(cols, suggestions[:4])):
            if col.button(q, key=f"chat_sug_{i}", width="stretch"):
                _ask(q)
                st.rerun()

    box = st.container(height=460)
    with box:
        with st.chat_message("assistant"):
            st.write(WELCOME)
        for m in st.session_state.get("chat_history", []):
            with st.chat_message(m["role"]):
                st.write(m["content"])

    prompt = st.chat_input("Savolingizni yozing… (masalan: HEMIS eksport qanday qilinadi?)", key="chat_input")
    if prompt:
        _ask(prompt)
        st.rerun()
