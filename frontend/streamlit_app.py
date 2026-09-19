"""AI O'qituvchi Hamkori — boshqaruv paneli (Streamlit).

Ishga tushirish:  streamlit run frontend/streamlit_app.py
Backend manzili:  BACKEND_URL muhit o'zgaruvchisi yoki yon paneldagi maydon.
"""
from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui import api, backend_launcher, settings_panel, tab_billing, tab_chat, tab_documents, tab_grading, tab_reports, tab_students  # noqa: E402

st.set_page_config(page_title="AI O'qituvchi Hamkori", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.2rem;}
      div[data-testid="stMetric"] {background: rgba(42,120,214,0.06); border: 1px solid rgba(42,120,214,0.15); border-radius: 10px; padding: 10px 14px;}
      div[data-testid="stMetricLabel"] {color: #52514e;}
    </style>
    """,
    unsafe_allow_html=True,
)

for k, v in {"token": None, "username": None, "backend_url": api.default_backend_url()}.items():
    st.session_state.setdefault(k, v)

# ---------------------------------------------------------------- Sidebar
with st.sidebar:
    st.markdown("## 🎓 AI O'qituvchi Hamkori")
    st.caption("Tekshirish · Hujjatlar · Hisobotlar — bir joyda")
    st.session_state["backend_url"] = st.text_input("Backend URL", value=st.session_state["backend_url"])
    with st.spinner("Backend tekshirilmoqda…"):
        ok, state, h = backend_launcher.ensure_backend()
    if ok:
        st.success(f"Backend: {h['status']} · v{h['version']} · LLM: **{h['provider']}**" + (f" · avtomatik ishga tushirildi ({st.session_state['backend_url']})" if state == "started" else ""))
    else:
        if state == "remote":
            st.error("Backend javob bermayapti. Manzilni tekshiring yoki serverni ishga tushiring.")
        else:
            st.error("Backend ishga tushmadi. Quyidagi logni ko'ring; qo'lda: `cd backend && uvicorn app.main:app`")
            log = backend_launcher.tail_log()
            if log:
                st.code(log, language="text")
            if st.button("🔄 Qayta urinish", key="backend_retry"):
                backend_launcher.restart()
                st.rerun()
    settings_panel.render()

    st.markdown("### 👤 O'qituvchi")
    if st.session_state["token"]:
        st.write(f"Kirgan: **{st.session_state['username']}**")
        if st.button("Chiqish", width="stretch"):
            st.session_state["token"] = None
            st.session_state["username"] = None
            api.invalidate()
            st.rerun()
    else:
        with st.form("login"):
            u = st.text_input("Login", value="teacher")
            p = st.text_input("Parol", type="password", value="teacher123")
            if st.form_submit_button("Kirish", width="stretch"):
                try:
                    res = api.post("/auth/token", data={"username": u, "password": p})
                    st.session_state["token"] = res["access_token"]
                    st.session_state["username"] = res["user"]["username"]
                    api.invalidate()
                    st.rerun()
                except api.APIError as exc:
                    st.error(str(exc))
        st.caption("Demo: teacher/teacher123 · admin/admin123 · dekan/dekan123")

    try:
        sub = api.get("/api/subscription")
        u = sub["usage"]
        limit_txt = f"{u['grades_used']} / {u['grades_limit']} ish (shu oy)" if u.get("grades_limit") else f"{u['grades_used']} ish (cheksiz)"
        st.info(f"Tarif: **{sub['plan_title']}** · {limit_txt}")
    except api.APIError:
        pass

    try:
        s = api.get("/api/stats")
        st.markdown("### 📌 Holat")
        st.metric("Baholangan ishlar", s["total_grades"], f"{s['pending']} tasdiqlanmagan")
        st.metric("Tejalgan vaqt", f"{s['time_saved_hours']} soat")
        st.caption(f"Talabalar: {s['students']} · Guruhlar: {s['groups']} · Hujjatlar: {s['documents']}")
    except api.APIError:
        pass

    st.markdown("---")
    st.caption("Demo ma'lumot uchun: `python scripts/seed.py`")

# ---------------------------------------------------------------- Tabs
st.title("AI O'qituvchi Hamkori")
st.caption("Talaba ishlarini AI bilan tekshiring, o'zingiz tasdiqlang, HEMIS uchun eksport qiling — haftalik 15–20 soat o'rniga 1–2 soat.")

tabs = st.tabs(["🔎 Tekshirish", "📄 Hujjatlar", "📊 Hisobotlar", "👥 Talabalar", "💳 Tariflar", "💬 Yordamchi"])
with tabs[0]:
    tab_grading.render()
with tabs[1]:
    tab_documents.render()
with tabs[2]:
    tab_reports.render()
with tabs[3]:
    tab_students.render()
with tabs[4]:
    tab_billing.render()
with tabs[5]:
    tab_chat.render()
