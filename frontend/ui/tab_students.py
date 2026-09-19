"""4-tab: Talabalar, guruhlar va baholash mezonlari shablonlari."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from . import api
from .theme import df


def render() -> None:
    st.subheader("👥 Talabalar, guruhlar va mezonlar")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("**📥 Ro'yxatni import qilish (HEMIS eksporti: XLSX/CSV)**")
        st.caption("Ustunlar: `Talaba ID`/`HEMIS ID`/`student_id`, `F.I.Sh.`/`full_name`, `Guruh`/`group`.")
        up = st.file_uploader("Fayl", type=["xlsx", "xls", "csv"], key="st_import")
        default_group = st.text_input("Guruh (faylda ustun bo'lmasa)", key="st_import_group")
        if up and st.button("Import qilish", key="st_import_btn", type="primary"):
            try:
                res = api.post("/api/students/import", files={"file": (up.name, up.getvalue())}, params={"group_name": default_group or None})
                api.invalidate()
                st.success(f"Yangi: {res['imported']}, yangilangan: {res['updated']}, guruhlar: {', '.join(res['groups']) or '—'}")
                for e in res.get("errors", []):
                    st.warning(e)
            except api.APIError as exc:
                st.error(str(exc))
    with c2:
        st.markdown("**➕ Talaba qo'shish**")
        with st.form("st_add"):
            sid = st.text_input("Talaba ID (HEMIS)")
            name = st.text_input("F.I.Sh.")
            grp = st.text_input("Guruh")
            if st.form_submit_button("Qo'shish"):
                try:
                    api.post("/api/students", json={"student_id": sid, "full_name": name or None, "group_name": grp or None})
                    api.invalidate()
                    st.success("Qo'shildi")
                except api.APIError as exc:
                    st.error(str(exc))

    try:
        groups = api.get("/api/groups")
        students = api.get("/api/students")
    except api.APIError as exc:
        st.error(str(exc))
        return
    g1, g2 = st.columns([1, 2])
    with g1:
        st.markdown("**Guruhlar**")
        if groups:
            st.dataframe(df(groups, ["name", "faculty", "course_year", "student_count"], {"name": "Guruh", "faculty": "Fakultet", "course_year": "Kurs", "student_count": "Talabalar"}), width="stretch", hide_index=True)
        else:
            st.caption("Guruhlar yo'q.")
    with g2:
        st.markdown("**Talabalar**")
        sel = st.selectbox("Guruh bo'yicha", ["Barchasi"] + [g["name"] for g in groups], key="st_group_filter")
        rows = [s for s in students if sel == "Barchasi" or s.get("group_name") == sel]
        if rows:
            st.dataframe(df(rows, ["student_id", "full_name", "group_name"], {"student_id": "ID", "full_name": "F.I.Sh.", "group_name": "Guruh"}), width="stretch", hide_index=True, height=min(400, 40 + 35 * len(rows)))
        else:
            st.caption("Talabalar yo'q.")

    st.markdown("---")
    st.markdown("### 🧩 Baholash mezonlari shablonlari")
    try:
        rubrics = api.get("/api/rubrics")
    except api.APIError:
        rubrics = []
    r1, r2 = st.columns([1, 1])
    with r1:
        for t in rubrics:
            with st.expander(f"{'⭐ ' if t.get('is_default') else ''}{t['name']}" + (f" — {t['course']}" if t.get("course") else "")):
                st.dataframe(df(t["items"], ["name", "max_score", "description"], {"name": "Mezon", "max_score": "Maks.", "description": "Izoh"}), width="stretch", hide_index=True)
                if t.get("created_by") != "system" and st.button("O'chirish", key=f"rb_del_{t['id']}"):
                    try:
                        api.delete(f"/api/rubrics/{t['id']}")
                        api.invalidate()
                        st.rerun()
                    except api.APIError as exc:
                        st.error(str(exc))
    with r2:
        st.markdown("**Yangi shablon**")
        name = st.text_input("Nomi", key="rb_name")
        course = st.text_input("Fan (ixtiyoriy)", key="rb_course")
        items = st.data_editor(pd.DataFrame([{"name": "Mazmun", "max_score": 40.0, "description": ""}, {"name": "Tahlil", "max_score": 30.0, "description": ""}, {"name": "Xulosa", "max_score": 30.0, "description": ""}]),
                               num_rows="dynamic", width="stretch", hide_index=True, key="rb_editor",
                               column_config={"name": "Mezon", "max_score": st.column_config.NumberColumn("Maks.", min_value=1, step=1), "description": "Izoh"})
        make_default = st.checkbox("Standart shablon qilib belgilash", key="rb_default")
        if st.button("Saqlash", key="rb_save", type="primary"):
            payload = [{"name": str(r["name"]).strip(), "max_score": float(r["max_score"] or 0), "description": str(r.get("description") or "")} for _, r in items.iterrows() if str(r.get("name") or "").strip()]
            try:
                api.post("/api/rubrics", json={"name": name, "course": course or None, "items": payload, "is_default": make_default})
                api.invalidate()
                st.success("Shablon saqlandi")
                st.rerun()
            except api.APIError as exc:
                st.error(str(exc))
