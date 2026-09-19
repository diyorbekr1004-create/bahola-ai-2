"""1-tab: Tekshirish — yuklash, AI xulosasi, o'qituvchi tasdiqlashi/tuzatishi (human-in-the-loop)."""
from __future__ import annotations

import json
from typing import List

import pandas as pd
import streamlit as st

from . import api
from .theme import df, grade_badge, score_bar, status_for_ratio

RUBRIC_COLS = {"name": "Mezon", "max_score": "Maks. ball", "description": "Izoh"}


def _rubric_editor(key: str) -> List[dict]:
    templates = []
    try:
        templates = api.cached_get("/api/rubrics", api.backend_url(), st.session_state.get("token"))
    except api.APIError:
        pass
    options = {f"{t['name']}{' (standart)' if t.get('is_default') else ''}": t for t in templates}
    options["✏️ O'zim kiritaman"] = None
    choice = st.selectbox("Baholash mezonlari (rubrika)", list(options.keys()), key=f"{key}_tpl")
    tpl = options[choice]
    if tpl:
        base = [{"name": i["name"], "max_score": float(i["max_score"]), "description": i.get("description") or ""} for i in tpl["items"]]
    else:
        base = st.session_state.get(f"{key}_custom_rubric") or [{"name": "Mazmun", "max_score": 50.0, "description": ""}, {"name": "Shakl", "max_score": 50.0, "description": ""}]
    edited = st.data_editor(
        pd.DataFrame(base), num_rows="dynamic", width="stretch", key=f"{key}_editor", hide_index=True,
        column_config={
            "name": st.column_config.TextColumn("Mezon", required=True),
            "max_score": st.column_config.NumberColumn("Maks. ball", min_value=1, max_value=100, step=1),
            "description": st.column_config.TextColumn("Izoh"),
        },
    )
    items = [{"name": str(r["name"]).strip(), "max_score": float(r["max_score"] or 0), "description": str(r.get("description") or "")} for _, r in edited.iterrows() if str(r.get("name") or "").strip() and float(r.get("max_score") or 0) > 0]
    if tpl is None:
        st.session_state[f"{key}_custom_rubric"] = items
    total = sum(i["max_score"] for i in items)
    st.caption(f"Jami: **{total:g}** ball" + ("" if abs(total - 100) < 0.01 else " ⚠️ (100 ga tenglashtirish tavsiya etiladi)"))
    return items


def _students_and_groups():
    try:
        students = api.cached_get("/api/students", api.backend_url(), st.session_state.get("token"))
        groups = api.cached_get("/api/groups", api.backend_url(), st.session_state.get("token"))
    except api.APIError:
        students, groups = [], []
    return students, groups


def render_grade_result(g: dict, key: str, compact: bool = False) -> None:
    """Bitta baho natijasini ko'rsatadi va o'qituvchi amallarini taklif qiladi."""
    gid = g.get("grade_id")
    total, mx = g.get("total_score") or 0, g.get("max_score") or 100
    integ = g.get("integrity") or {}
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ball", f"{total:g} / {mx:g}")
    c2.metric("5 ballik", grade_badge(g.get("grade_5")))
    pi, pl = status_for_ratio(integ.get("plagiarism_score"), 0.25, 0.4)
    c3.metric("Plagiat", f"{pi} {int((integ.get('plagiarism_score') or 0) * 100)}%", pl)
    ai_i, ai_l = status_for_ratio(integ.get("ai_likelihood"), 0.4, 0.6)
    c4.metric("AI-matn", f"{ai_i} {int((integ.get('ai_likelihood') or 0) * 100)}%", ai_l)
    sim = integ.get("similarity_score")
    si, sl = status_for_ratio(sim, 0.4, 0.6)
    c5.metric("O'xshashlik", f"{si} {int((sim or 0) * 100)}%" if sim is not None else "—", (f"{integ.get('similar_to_student')}" if integ.get("similar_to_student") else sl))

    status_txt = {"pending": "⏳ Tasdiqlanmagan", "confirmed": "✅ Tasdiqlangan", "edited": "✏️ Tuzatilgan va tasdiqlangan"}.get(g.get("status"), g.get("status"))
    st.caption(
        f"{status_txt} · Talaba: **{g.get('student_name') or g.get('student_id') or '—'}** · Guruh: {g.get('group_name') or '—'} · "
        f"Fan: {g.get('course') or '—'} · Mavzu: {g.get('topic') or '—'} · {g.get('word_count') or 0} so'z · "
        f"{g.get('processing_ms') or 0} ms · provayder: {g.get('provider') or '—'}"
        + (f" · AI dastlabki balli: {g.get('ai_total_score'):g}" if g.get("ai_total_score") is not None and g.get("ai_total_score") != total else "")
    )

    left, right = st.columns([1.1, 1])
    with left:
        if g.get("rubric"):
            st.plotly_chart(score_bar(g["rubric"]), width="stretch", key=f"{key}_chart")
            with st.expander("Mezonlar bo'yicha asoslar (jadval)"):
                st.dataframe(df(g["rubric"], ["name", "score", "max_score", "evidence"], {"name": "Mezon", "score": "Ball", "max_score": "Maks.", "evidence": "Asos"}), width="stretch", hide_index=True)
    with right:
        fb = g.get("feedback") or {}
        st.markdown(f"**Xulosa:** {fb.get('summary') or '—'}")
        if fb.get("strengths"):
            st.markdown("**✅ Kuchli tomonlar**")
            for s in fb["strengths"]:
                st.markdown(f"- {s}")
        if fb.get("errors"):
            st.markdown("**❌ Aniqlangan xatolar**")
            for e in fb["errors"]:
                st.markdown(f"- {e}")
        if fb.get("suggestions"):
            st.markdown("**💡 Tavsiyalar**")
            for s in fb["suggestions"]:
                st.markdown(f"- {s}")
        if integ.get("reasons"):
            with st.expander("Halollik tekshiruvi sabablari"):
                for r in integ["reasons"]:
                    st.markdown(f"- {r}")
    if g.get("teacher_comment"):
        st.info(f"O'qituvchi izohi: {g['teacher_comment']}")

    if compact or not gid:
        return

    st.markdown("##### 👩‍🏫 O'qituvchi qarori")
    a1, a2, a3 = st.columns([1, 1.6, 1])
    with a1:
        comment = st.text_input("Izoh (ixtiyoriy)", key=f"{key}_confirm_comment")
        if st.button("✅ Tasdiqlash", key=f"{key}_confirm", type="primary", width="stretch", disabled=g.get("status") in ("confirmed", "edited")):
            try:
                res = api.post(f"/api/grade/{gid}/confirm", json={"teacher_id": st.session_state.get("username"), "comment": comment or None})
                _replace_result(res["grade"])
                api.invalidate()
                st.success("Baho tasdiqlandi va HEMIS eksportiga tayyor.")
                st.rerun()
            except api.APIError as exc:
                st.error(str(exc))
    with a2:
        with st.expander("✏️ Tuzatish (ballarni o'zgartirish)"):
            base = pd.DataFrame([{"name": r["name"], "score": float(r.get("score") or 0), "max_score": float(r["max_score"])} for r in g.get("rubric") or []])
            edited = st.data_editor(base, width="stretch", hide_index=True, key=f"{key}_edit_editor", disabled=["name", "max_score"],
                                    column_config={"name": "Mezon", "score": st.column_config.NumberColumn("Ball", min_value=0, step=1), "max_score": "Maks."})
            ecomment = st.text_area("Tuzatish sababi", key=f"{key}_edit_comment", height=70)
            if st.button("Saqlash va tasdiqlash", key=f"{key}_edit_btn", width="stretch"):
                rubric = [{"name": r["name"], "max_score": float(r["max_score"]), "score": min(float(r["score"] or 0), float(r["max_score"]))} for _, r in edited.iterrows()]
                try:
                    res = api.post(f"/api/grade/{gid}/edit", json={"teacher_id": st.session_state.get("username"), "corrected_rubric": rubric, "comment": ecomment or None, "confirm": True})
                    _replace_result(res["grade"])
                    api.invalidate()
                    st.success(f"Yangi ball: {res['grade']['total_score']:g}. Tuzatish jurnalga yozildi.")
                    st.rerun()
                except api.APIError as exc:
                    st.error(str(exc))
    with a3:
        try:
            st.download_button("📄 Talabaga fikr-mulohaza (DOCX)", data=api.download(f"/api/grade/{gid}/feedback.docx"), file_name=f"feedback_{g.get('student_id') or gid}.docx", key=f"{key}_fb_dl", width="stretch")
        except api.APIError:
            st.caption("Fikr-mulohaza faylini olib bo'lmadi")
        if st.button("🗑️ O'chirish", key=f"{key}_del", width="stretch"):
            try:
                api.delete(f"/api/grade/{gid}")
                st.session_state["last_results"] = [r for r in st.session_state.get("last_results", []) if r.get("grade_id") != gid]
                api.invalidate()
                st.rerun()
            except api.APIError as exc:
                st.error(str(exc))


def _replace_result(updated: dict) -> None:
    results = st.session_state.get("last_results", [])
    st.session_state["last_results"] = [updated if r.get("grade_id") == updated.get("grade_id") else r for r in results]
    if st.session_state.get("selected_grade", {}).get("grade_id") == updated.get("grade_id"):
        st.session_state["selected_grade"] = updated


def render() -> None:
    st.subheader("🔎 Tekshirish — talaba ishini yuklang, 5 soniyada ball va asoslar")
    students, groups = _students_and_groups()
    group_names = sorted({g["name"] for g in groups} | {s.get("group_name") for s in students if s.get("group_name")})

    left, right = st.columns([1, 1.2])
    with left:
        st.markdown("**Ish haqida ma'lumot**")
        g_choice = st.selectbox("Guruh", ["— tanlanmagan —"] + group_names + ["➕ Yangi guruh"], key="gr_group")
        group_name = st.text_input("Yangi guruh nomi", key="gr_group_new") if g_choice == "➕ Yangi guruh" else (None if g_choice.startswith("—") else g_choice)
        group_students = [s for s in students if not group_name or s.get("group_name") == group_name]
        s_options = {f"{s.get('full_name') or ''} ({s['student_id']})".strip(): s for s in group_students}
        s_choice = st.selectbox("Talaba", ["— qo'lda kiritish —"] + list(s_options.keys()), key="gr_student")
        if s_choice in s_options:
            student_id, student_name = s_options[s_choice]["student_id"], s_options[s_choice].get("full_name")
        else:
            student_id = st.text_input("Talaba ID (HEMIS)", key="gr_sid", placeholder="masalan, 123456 yoki fayl nomidan olinadi")
            student_name = st.text_input("F.I.Sh.", key="gr_sname")
        course = st.text_input("Fan", key="gr_course", placeholder="Masalan, Pedagogika")
        topic = st.text_input("Mavzu / topshiriq", key="gr_topic", placeholder="Masalan, Ta'lim va texnologiya")
        rubric_items = _rubric_editor("gr")
        with st.expander("Etalon javob (ixtiyoriy) — AI shu bilan solishtiradi"):
            reference = st.text_area("Kutilgan javob / kalit so'zlar", key="gr_ref", height=100)

    with right:
        st.markdown("**Talaba ishi**")
        mode = st.radio("Kiritish usuli", ["Matn", "Fayl(lar) / ZIP"], horizontal=True, key="gr_mode")
        text = uploaded = None
        if mode == "Matn":
            text = st.text_area("Matnni shu yerga joylang", height=320, key="gr_text", placeholder="Talaba inshosi, referati yoki javobi…")
        else:
            uploaded = st.file_uploader("TXT, DOCX, PDF yoki ZIP (bir nechta fayl = batch)", type=["txt", "md", "docx", "pdf", "zip"], accept_multiple_files=True, key="gr_files")
            st.caption("Batch rejimda talaba ID fayl nomidan olinadi: `123456_Aliyev.docx` → `123456_Aliyev`.")
        run = st.button("🚀 Baholash", type="primary", width="stretch", key="gr_run")

    if run:
        meta = {"student_id": student_id, "student_name": student_name, "group_name": group_name, "course": course, "topic": topic,
                "rubric": json.dumps(rubric_items, ensure_ascii=False) if rubric_items else None, "reference_answer": reference or None}
        try:
            with st.spinner("AI tekshirmoqda…"):
                if mode == "Matn":
                    if not (text or "").strip():
                        st.warning("Matn bo'sh.")
                        return
                    res = api.post("/api/grade", data={**meta, "text": text})
                    st.session_state["last_results"] = [res]
                    st.session_state["last_batch_errors"] = []
                else:
                    if not uploaded:
                        st.warning("Fayl tanlanmagan.")
                        return
                    if len(uploaded) == 1 and not uploaded[0].name.lower().endswith(".zip"):
                        res = api.post("/api/grade", data=meta, files={"file": (uploaded[0].name, uploaded[0].getvalue())})
                        st.session_state["last_results"] = [res]
                        st.session_state["last_batch_errors"] = []
                    else:
                        batch_meta = {k: v for k, v in meta.items() if k not in ("student_id", "student_name")}
                        res = api.post("/api/grade/batch", data=batch_meta, files=[("files", (f.name, f.getvalue())) for f in uploaded])
                        st.session_state["last_results"] = res["results"]
                        st.session_state["last_batch_errors"] = res.get("errors", [])
                        st.success(f"{res['graded']} ta ish baholandi, {res['failed']} ta xato, {res['processing_ms']} ms.")
            api.invalidate()
        except api.APIError as exc:
            st.error(str(exc))

    results = st.session_state.get("last_results") or []
    for err in st.session_state.get("last_batch_errors") or []:
        st.warning(f"{err['filename']}: {err['error']}")
    if results:
        st.markdown("---")
        st.markdown(f"### Natijalar ({len(results)})")
        if len(results) > 1:
            st.dataframe(df(results, ["student_id", "student_name", "total_score", "grade_5", "plagiarism_score", "ai_likelihood", "status"],
                            {"student_id": "Talaba", "student_name": "F.I.Sh.", "total_score": "Ball", "grade_5": "Baho", "plagiarism_score": "Plagiat", "ai_likelihood": "AI", "status": "Holat"}),
                         width="stretch", hide_index=True)
            for r in results:
                with st.expander(f"{r.get('student_name') or r.get('student_id')} — {r.get('total_score'):g} ball ({grade_badge(r.get('grade_5'))})"):
                    render_grade_result(r, key=f"res_{r.get('grade_id')}")
        else:
            render_grade_result(results[0], key=f"res_{results[0].get('grade_id')}")

    # --- Saqlangan baholar (HITL navbati) ---
    st.markdown("---")
    st.markdown("### 📋 Saqlangan baholar (tasdiqlash navbati)")
    f1, f2, f3, f4 = st.columns([1, 1, 1, 1])
    status = f1.selectbox("Holat", ["Barchasi", "pending", "confirmed", "edited"], key="lst_status")
    f_course = f2.text_input("Fan filtri", key="lst_course")
    f_group = f3.selectbox("Guruh filtri", ["Barchasi"] + group_names, key="lst_group")
    limit = f4.number_input("Limit", 10, 1000, 100, key="lst_limit")
    try:
        grades = api.get("/api/grades", status=None if status == "Barchasi" else status, course=f_course or None, group_name=None if f_group == "Barchasi" else f_group, limit=int(limit))
    except api.APIError as exc:
        st.error(str(exc))
        grades = []
    if not grades:
        st.info("Hali baholar yo'q. Yuqorida ish yuklang yoki `python scripts/seed.py` bilan demo ma'lumot kiriting.")
        return
    pending = sum(1 for g in grades if g["status"] == "pending")
    st.caption(f"Jami {len(grades)} ta, tasdiqlanmagan: {pending}")
    table = df(grades, ["grade_id", "student_id", "student_name", "group_name", "course", "topic", "total_score", "grade_5", "status", "plagiarism_score", "ai_likelihood", "similarity_score", "updated_at"],
               {"grade_id": "ID", "student_id": "Talaba", "student_name": "F.I.Sh.", "group_name": "Guruh", "course": "Fan", "topic": "Mavzu", "total_score": "Ball", "grade_5": "Baho", "status": "Holat", "plagiarism_score": "Plagiat", "ai_likelihood": "AI", "similarity_score": "O'xshash", "updated_at": "Yangilangan"})
    st.dataframe(table, width="stretch", hide_index=True, height=min(400, 40 + 35 * len(grades)))
    options = {f"#{g['grade_id']} · {g.get('student_name') or g['student_id']} · {g.get('course') or ''} · {g['total_score']:g} · {g['status']}": g["grade_id"] for g in grades}
    sel = st.selectbox("Ko'rish / tasdiqlash uchun bahoni tanlang", list(options.keys()), key="lst_sel")
    if st.button("Ochish", key="lst_open"):
        try:
            st.session_state["selected_grade"] = api.get(f"/api/grade/{options[sel]}")
        except api.APIError as exc:
            st.error(str(exc))
    selected = st.session_state.get("selected_grade")
    if selected:
        st.markdown(f"#### Baho #{selected['grade_id']}")
        with st.expander("Talaba matni (boshi)"):
            st.write(selected.get("content_preview") or "")
        render_grade_result(selected, key=f"sel_{selected['grade_id']}")
