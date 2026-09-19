"""2-tab: Hujjatlar — silabus, dars rejasi, imtihon biletlari, testlar (DOCX bilan)."""
from __future__ import annotations

import streamlit as st

from . import api
from .theme import df

DOC_TYPES = {"syllabus": "Silabus (15 hafta)", "lesson_plan": "Dars rejasi", "exam_tickets": "Imtihon biletlari", "test_questions": "Test savollari"}


def _render_doc(d: dict, key: str) -> None:
    s = d.get("structured") or {}
    if d.get("download_url"):
        try:
            st.download_button("⬇️ DOCX yuklab olish (barcha hujjatlar)", data=api.download(d["download_url"]), file_name=d["download_url"].split("/")[-1], key=f"{key}_dl", type="primary")
        except api.APIError as exc:
            st.warning(f"Faylni olib bo'lmadi: {exc}")
    tabs = st.tabs(["📘 Silabus", "🧑‍🏫 Dars rejasi", "🎫 Biletlar", "✅ Testlar", "📝 Matn ko'rinishi"])
    with tabs[0]:
        syl = s.get("syllabus")
        if syl:
            hb = syl.get("hours_breakdown") or {}
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Haftalar", syl.get("weeks"))
            c2.metric("Ma'ruza (soat)", hb.get("lecture"))
            c3.metric("Amaliy (soat)", hb.get("practice"))
            c4.metric("Mustaqil (soat)", hb.get("independent"))
            st.dataframe(df(syl.get("weekly", []), ["week", "topic", "lecture_hours", "practice_hours", "independent_hours", "assessment"],
                            {"week": "Hafta", "topic": "Mavzu", "lecture_hours": "Ma'ruza", "practice_hours": "Amaliy", "independent_hours": "Mustaqil", "assessment": "Nazorat"}), width="stretch", hide_index=True)
            cols = st.columns(2)
            with cols[0]:
                st.markdown("**Maqsadlar**")
                for g in syl.get("goals", []):
                    st.markdown(f"- {g}")
                st.markdown("**Kutilayotgan natijalar**")
                for g in syl.get("learning_outcomes", []):
                    st.markdown(f"- {g}")
            with cols[1]:
                st.markdown("**Baholash tizimi**")
                st.dataframe(df(syl.get("assessment_policy", []), ["type", "max_score", "description"], {"type": "Nazorat", "max_score": "Ball", "description": "Izoh"}), width="stretch", hide_index=True)
                st.caption(syl.get("grade_scale", ""))
        else:
            st.info("Silabus tanlanmagan.")
    with tabs[1]:
        lp = s.get("lesson_plan")
        if lp:
            st.markdown(f"**Mavzu:** {lp.get('topic')} · {lp.get('week')}-hafta · {lp.get('duration_minutes')} daqiqa")
            st.dataframe(df(lp.get("stages", []), ["stage", "minutes", "activity"], {"stage": "Bosqich", "minutes": "Daqiqa", "activity": "Faoliyat"}), width="stretch", hide_index=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Maqsadlar**")
                for o in lp.get("objectives", []):
                    st.markdown(f"- {o}")
            with c2:
                st.markdown("**Metodlar:** " + ", ".join(lp.get("methods", [])))
                st.markdown("**Jihozlar:** " + ", ".join(lp.get("materials", [])))
                st.markdown(f"**Uyga vazifa:** {lp.get('homework')}")
        else:
            st.info("Dars rejasi tanlanmagan.")
    with tabs[2]:
        tickets = s.get("exam_tickets") or []
        if tickets:
            cols = st.columns(min(3, len(tickets)))
            for i, t in enumerate(tickets):
                with cols[i % len(cols)]:
                    st.markdown(f"**Bilet № {t['number']}**")
                    for j, q in enumerate(t["questions"], start=1):
                        st.markdown(f"{j}. *{q['type']}*: {q['text']}")
        else:
            st.info("Biletlar tanlanmagan.")
    with tabs[3]:
        qs = s.get("test_questions") or []
        if qs:
            for q in qs:
                st.markdown(f"**{q['number']}. {q['question']}**")
                for k, v in q["options"].items():
                    st.markdown(f"&nbsp;&nbsp;&nbsp;{k}) {v}")
            with st.expander("Javoblar kaliti"):
                st.write(", ".join(f"{q['number']}-{q['answer']}" for q in qs))
        else:
            st.info("Testlar tanlanmagan.")
    with tabs[4]:
        for title, k in (("Silabus", "syllabus"), ("Dars rejasi", "lesson_plan"), ("Biletlar", "exam_ticket"), ("Testlar", "test_questions")):
            if d.get(k):
                st.text_area(title, value=d[k], height=220, key=f"{key}_txt_{k}")


def render() -> None:
    st.subheader("📄 Hujjatlar — fan nomini yozing, 10 soniyada silabus va imtihon bileti tayyor")
    with st.form("doc_form"):
        c1, c2, c3 = st.columns([2, 1, 1])
        course = c1.text_input("Fan nomi", value="Matematika", placeholder="Masalan, Informatika")
        hours = c2.number_input("Jami soat", 2, 1000, 60)
        weeks = c3.number_input("Haftalar", 1, 40, 15)
        c4, c5, c6, c7 = st.columns(4)
        level = c4.selectbox("Daraja", ["Bakalavriat", "Magistratura", "Kollej", "Maktab (yuqori sinf)"])
        types = c5.multiselect("Hujjat turlari", list(DOC_TYPES.keys()), default=list(DOC_TYPES.keys()), format_func=lambda k: DOC_TYPES[k])
        n_tickets = c6.number_input("Biletlar soni", 1, 30, 5)
        n_questions = c7.number_input("Test savollari", 1, 50, 10)
        custom = st.text_area("Mavzular (ixtiyoriy, har qatorda bitta — bo'sh qoldirsangiz AI o'zi tuzadi)", height=80)
        submitted = st.form_submit_button("⚡ Generatsiya qilish", type="primary")
    if submitted:
        topics = [t.strip() for t in custom.splitlines() if t.strip()] or None
        try:
            with st.spinner("Hujjatlar shakllantirilmoqda…"):
                d = api.post("/api/generate-docs", json={"course_name": course, "hours": int(hours), "weeks": int(weeks), "level": level, "doc_types": types,
                                                          "n_tickets": int(n_tickets), "n_questions": int(n_questions), "topics": topics, "export_format": "docx"})
            st.session_state["last_doc"] = d
            st.success(f"Tayyor: {d.get('processing_ms')} ms, provayder: {d.get('provider')}")
        except api.APIError as exc:
            st.error(str(exc))
    d = st.session_state.get("last_doc")
    if d:
        _render_doc(d, key=f"doc_{d.get('document_id')}")

    st.markdown("---")
    with st.expander("🗂️ Avval yaratilgan hujjatlar"):
        try:
            docs = api.get("/api/documents", limit=30)
        except api.APIError as exc:
            st.error(str(exc))
            docs = []
        if docs:
            st.dataframe(df(docs, ["id", "course", "title", "doc_type", "created_by", "created_at"], {"id": "ID", "course": "Fan", "title": "Nomi", "doc_type": "Turi", "created_by": "Kim", "created_at": "Sana"}), width="stretch", hide_index=True)
            opts = {f"#{x['id']} · {x['title']}": x["id"] for x in docs}
            sel = st.selectbox("Hujjatni ochish", list(opts.keys()), key="doc_sel")
            if st.button("Ochish", key="doc_open"):
                try:
                    st.session_state["last_doc"] = api.get(f"/api/documents/{opts[sel]}")
                    st.rerun()
                except api.APIError as exc:
                    st.error(str(exc))
        else:
            st.caption("Hali hujjatlar yo'q.")
