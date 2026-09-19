"""3-tab: Hisobotlar — guruh ko'rsatkichlari, grafiklar, HEMIS/Excel eksport, tahliliy xulosa."""
from __future__ import annotations

import streamlit as st

from . import api
from .theme import ORDINAL_BLUE, bar, df


def _filters():
    try:
        grades = api.cached_get("/api/grades", api.backend_url(), st.session_state.get("token"), limit=1000)
    except api.APIError:
        grades = []
    courses = sorted({g["course"] for g in grades if g.get("course")})
    groups = sorted({g["group_name"] for g in grades if g.get("group_name")})
    topics = sorted({g["topic"] for g in grades if g.get("topic")})
    c1, c2, c3, c4, c5 = st.columns([1.4, 1.2, 1.4, 1, 1])
    course = c1.selectbox("Fan", ["Barchasi"] + courses, key="rp_course")
    group = c2.selectbox("Guruh", ["Barchasi"] + groups, key="rp_group")
    topic = c3.selectbox("Mavzu", ["Barchasi"] + topics, key="rp_topic")
    only_confirmed = c4.checkbox("Faqat tasdiqlangan", key="rp_conf")
    control = c5.selectbox("HEMIS nazorat turi", ["JN", "ON", "YN"], key="rp_ctrl")
    return (None if course == "Barchasi" else course, None if group == "Barchasi" else group, None if topic == "Barchasi" else topic, only_confirmed, control)


def render() -> None:
    st.subheader("📊 Hisobotlar — o'zlashtirish, sifat, qiyin mavzular, HEMIS eksport")
    course, group, topic, only_confirmed, control = _filters()
    use_llm = st.toggle("Tahliliy xulosani LLM bilan boyitish (agar provayder ulangan bo'lsa)", value=False, key="rp_llm")
    if st.button("📈 Hisobot yaratish", type="primary", key="rp_run"):
        try:
            with st.spinner("Tahlil qilinmoqda…"):
                st.session_state["last_report"] = api.post("/api/reports", json={"course_name": course, "group_name": group, "topic": topic, "only_confirmed": only_confirmed, "export_format": "all", "control_type": control, "use_llm_summary": use_llm})
        except api.APIError as exc:
            st.error(str(exc))
    rep = st.session_state.get("last_report")
    if not rep:
        st.info("Filtrlarni tanlab «Hisobot yaratish» tugmasini bosing.")
        return
    a = rep["analytics"]
    if not a.get("total_grades"):
        st.warning(rep["summary"])
        return

    k1, k2, k3 = st.columns(3)
    k1.metric("Baholangan ishlar", a["total_grades"], f"{a['total_students']} talaba")
    k2.metric("O'rtacha ball", f"{a['average_score']}%", f"mediana {a['median_score']}%")
    k3.metric("O'zlashtirish", f"{a['pass_rate']}%", f"≥{int(a['thresholds']['pass'])} ball")
    k4, k5, k6 = st.columns(3)
    k4.metric("Sifat ko'rsatkichi", f"{a['quality_rate']}%", f"≥{int(a['thresholds']['quality'])} ball")
    k5.metric("Tasdiqlangan", f"{a['confirmed_count']} / {a['total_grades']}", f"{a['pending_count']} kutmoqda")
    k6.metric("Tejalgan vaqt", f"{a['time_saved_hours']} soat", f"{int(a['time_saved_minutes'])} daqiqa, qo'lda tekshiruvga nisbatan")

    st.markdown("#### 📥 Eksport (o'qituvchi qayta qo'lda kiritmaydi)")
    if rep.get("locked_features"):
        st.warning(rep.get("upgrade_hint") or "Ba'zi eksportlar joriy tarifda mavjud emas.")
    d1, d2, d3, d4 = st.columns(4)
    for col, label, url_key in ((d1, "🏛️ HEMIS jadvali (XLSX)", "hemis_download_url"), (d2, "📊 To'liq Excel hisobot", "download_url"), (d3, "🧾 CSV (HEMIS ustunlari)", "csv_download_url"), (d4, "📝 Dekanat uchun DOCX", "dean_report_url")):
        url = rep.get(url_key)
        if url:
            try:
                col.download_button(label, data=api.download(url), file_name=url.split("/")[-1], key=f"rp_dl_{url_key}", width="stretch")
            except api.APIError as exc:
                col.caption(f"Yuklab bo'lmadi: {exc}")

    c1, c2 = st.columns(2)
    with c1:
        hist = a.get("histogram") or []
        st.plotly_chart(bar([h["label"] for h in hist], [h["count"] for h in hist], "Baholar taqsimoti (5 ballik)", colors=ORDINAL_BLUE, hover_label="Talabalar"), width="stretch", key="rp_hist")
    with c2:
        weak = a.get("weak_topics") or []
        st.plotly_chart(bar([w["topic"] for w in weak][:8], [w["difficulty"] for w in weak][:8], "Qiyin mavzular (100 − o'rtacha ball)", horizontal=True, value_suffix="%", hover_label="Qiyinchilik"), width="stretch", key="rp_weak")
    c3, c4 = st.columns(2)
    with c3:
        crit = a.get("criteria_stats") or []
        st.plotly_chart(bar([c["criterion"] for c in crit], [c["average_percent"] for c in crit], "Mezonlar bo'yicha o'rtacha (%)", horizontal=True, value_suffix="%", hover_label="O'rtacha"), width="stretch", key="rp_crit")
    with c4:
        gs = a.get("group_stats") or []
        if len(gs) > 1:
            st.plotly_chart(bar([g["group"] for g in gs], [g["average_score"] for g in gs], "Guruhlar taqqoslash — o'rtacha ball (%)", value_suffix="%", hover_label="O'rtacha"), width="stretch", key="rp_groups")
        else:
            st.plotly_chart(bar([w["topic"] for w in weak][:8], [w["pass_rate"] for w in weak][:8], "Mavzular bo'yicha o'zlashtirish (%)", value_suffix="%", hover_label="O'zlashtirish"), width="stretch", key="rp_topics_pass")

    t1, t2, t3 = st.tabs(["⚠️ Xavf guruhi", "🏆 Eng yaxshi natijalar", "📋 Jadval ko'rinishi"])
    with t1:
        risk = a.get("at_risk_students") or []
        if risk:
            st.dataframe(df(risk, ["student_id", "student_name", "group", "count", "average_score", "last_score", "trend"], {"student_id": "Talaba", "student_name": "F.I.Sh.", "group": "Guruh", "count": "Ishlar", "average_score": "O'rtacha %", "last_score": "Oxirgi %", "trend": "Dinamika"}), width="stretch", hide_index=True)
        else:
            st.success("Xavf guruhidagi talabalar yo'q.")
    with t2:
        st.dataframe(df(a.get("top_students") or [], ["student_id", "student_name", "group", "average_score", "grade_5"], {"student_id": "Talaba", "student_name": "F.I.Sh.", "group": "Guruh", "average_score": "O'rtacha %", "grade_5": "Baho"}), width="stretch", hide_index=True)
    with t3:
        st.markdown("**Mavzular**")
        st.dataframe(df(weak, ["topic", "average_score", "pass_rate", "count", "difficulty"], {"topic": "Mavzu", "average_score": "O'rtacha %", "pass_rate": "O'zlashtirish %", "count": "Ishlar", "difficulty": "Qiyinchilik %"}), width="stretch", hide_index=True)
        st.markdown("**Mezonlar**")
        st.dataframe(df(crit, ["criterion", "average_percent", "below_pass_pct", "count"], {"criterion": "Mezon", "average_percent": "O'rtacha %", "below_pass_pct": "Chegaradan past %", "count": "Baholar"}), width="stretch", hide_index=True)
        st.markdown("**Guruhlar**")
        st.dataframe(df(gs, ["group", "count", "average_score", "pass_rate", "quality_rate"], {"group": "Guruh", "count": "Ishlar", "average_score": "O'rtacha %", "pass_rate": "O'zlashtirish %", "quality_rate": "Sifat %"}), width="stretch", hide_index=True)

    integ = a.get("integrity") or {}
    agr = a.get("ai_teacher_agreement") or {}
    i1, i2, i3, i4 = st.columns(4)
    i1.metric("Plagiat belgisi", integ.get("plagiarism_flags", 0))
    i2.metric("AI-matn belgisi", integ.get("ai_flags", 0))
    i3.metric("O'xshash ishlar", integ.get("similarity_flags", 0))
    i4.metric("AI ↔ o'qituvchi farqi", f"{agr.get('mean_abs_diff', 0)} ball", f"{agr.get('within_5_points_pct', 0)}% ≤5 ball")

    st.markdown("#### 🧠 Kafedra mudiri / dekanat uchun tahliliy xulosa")
    st.markdown(rep.get("narrative") or rep.get("summary"))

    with st.expander("🧾 Audit jurnali (kim, qachon, nima qildi)"):
        try:
            logs = api.get("/api/audit", limit=100)
            if logs:
                st.dataframe(df(logs, ["created_at", "action", "actor", "target_id", "note"], {"created_at": "Vaqt", "action": "Amal", "actor": "Kim", "target_id": "ID", "note": "Izoh"}), width="stretch", hide_index=True)
            else:
                st.caption("Audit yozuvlari yo'q.")
        except api.APIError as exc:
            st.error(str(exc))
