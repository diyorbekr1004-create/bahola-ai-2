"""5-tab: Tariflar — pullik rejalar, obuna/to'lov, ROI kalkulyator, raqobatchilar bilan taqqoslash."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from . import api

FEATURE_LABELS = {"llm": "AI (LLM) bilan chuqur baholash", "batch": "ZIP / batch yuklash", "hemis_export": "HEMIS / CSV / dekanat eksporti",
                  "shared_rubrics": "Umumiy rubrika shablonlari", "dean_dashboard": "Dekanat dashboardi", "on_premise": "On-premise (OTM serverida)"}


def _fmt(n) -> str:
    try:
        return f"{int(n):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(n)


def _usage_block(sub: dict) -> None:
    u = sub["usage"]
    c1, c2, c3 = st.columns([1, 1.5, 1.5])
    c1.metric("Joriy tarif", sub["plan_title"], "demo foydalanuvchi" if sub.get("is_demo_user") else sub["username"])
    with c2:
        st.caption("Tekshirilgan ishlar (shu oy)")
        if u["grades_limit"]:
            st.progress(min(1.0, u["grades_used"] / max(1, u["grades_limit"])), text=f"{u['grades_used']} / {u['grades_limit']}")
        else:
            st.progress(0.0, text=f"{u['grades_used']} / cheksiz")
    with c3:
        st.caption("Hujjat to'plamlari (shu oy)")
        if u["documents_limit"]:
            st.progress(min(1.0, u["documents_used"] / max(1, u["documents_limit"])), text=f"{u['documents_used']} / {u['documents_limit']}")
        else:
            st.progress(0.0, text=f"{u['documents_used']} / cheksiz")
    if sub.get("subscription"):
        s = sub["subscription"]
        st.success(f"Faol obuna: {s['plan']} · {s['seats']} o'rin · {s['months']} oy · {_fmt(s['amount'])} so'm · {s['payment_method']} · tugaydi: {(s.get('expires_at') or '')[:10]}")
    if sub.get("pending"):
        p = sub["pending"]
        st.warning(f"To'lov kutilmoqda: {p['plan']} · {p['seats']} o'rin · {p['months']} oy · **{_fmt(p['amount'])} so'm** · hisob-faktura **{p['invoice_no']}** ({p['payment_method']})")
        b1, b2 = st.columns(2)
        if sub.get("demo_payments") and b1.button("✅ To'lovni tasdiqlash (demo)", key="bill_confirm", type="primary"):
            try:
                api.post(f"/api/subscription/{p['id']}/confirm")
                api.invalidate()
                st.rerun()
            except api.APIError as exc:
                st.error(str(exc))
        if b2.button("Bekor qilish", key="bill_cancel_pending"):
            try:
                api.post("/api/subscription/cancel")
                st.rerun()
            except api.APIError as exc:
                st.error(str(exc))


def _plan_cards(plans_data: dict, sub: dict) -> None:
    plans_list = plans_data["plans"]
    cols = st.columns(len(plans_list))
    for col, plan in zip(cols, plans_list):
        with col:
            current = plan["name"] == sub["plan"]
            price = "Bepul" if not plan["price_per_seat"] else f"{_fmt(plan['price_per_seat'])} so'm"
            st.markdown(f"### {'⭐ ' if current else ''}{plan['title']}")
            st.markdown(f"**{price}** <span style='color:#898781'>/ o'qituvchi / {plan['billing']}</span>", unsafe_allow_html=True)
            st.caption(plan.get("tagline") or "")
            if plan.get("min_seats", 1) > 1:
                st.caption(f"kamida {plan['min_seats']} o'qituvchi")
            for h in plan.get("highlights", []):
                st.markdown(f"✅ {h}")
            for key, label in FEATURE_LABELS.items():
                if not plan["features"].get(key):
                    st.markdown(f"<span style='color:#898781'>— {label}</span>", unsafe_allow_html=True)
            st.caption(f"Qo'llab-quvvatlash: {plan['features'].get('support', '')}")
            if current:
                st.button("Joriy tarif", key=f"plan_{plan['name']}", disabled=True, width="stretch")
            elif not plan["price_per_seat"]:
                if st.button("Bepulga o'tish", key=f"plan_{plan['name']}", width="stretch"):
                    try:
                        api.post("/api/subscription/cancel")
                        api.invalidate()
                        st.session_state.pop("billing_choice", None)
                        st.rerun()
                    except api.APIError as exc:
                        st.error(str(exc))
            elif st.button("Tanlash", key=f"plan_{plan['name']}", width="stretch", type="primary" if plan["name"] == "pro" else "secondary"):
                st.session_state["billing_choice"] = plan["name"]


def _checkout(plans_data: dict, sub: dict) -> None:
    choice = st.session_state.get("billing_choice")
    if not choice:
        return
    plan = next((p for p in plans_data["plans"] if p["name"] == choice), None)
    if not plan:
        return
    st.markdown(f"#### 🧾 Buyurtma: {plan['title']}")
    if sub.get("is_demo_user"):
        st.info("Tarifni o'zgartirish uchun yon paneldan tizimga kiring (masalan, **teacher / teacher123** — Free tarif).")
        return
    with st.form("checkout"):
        c1, c2, c3 = st.columns(3)
        seats = c1.number_input("O'qituvchilar soni", min_value=int(plan.get("min_seats", 1)), value=int(plan.get("min_seats", 1)), step=1)
        months = c2.selectbox("Muddat", [1, 3, 6, 12], index=3 if plan["name"] == "universitet" else 0, format_func=lambda m: f"{m} oy")
        method = c3.selectbox("To'lov usuli", plans_data.get("payment_methods") or ["Bank hisob-faktura"])
        org = st.text_input("Tashkilot (OTM / kafedra) — hisob-faktura uchun", placeholder="Masalan, TATU, Dasturiy injiniring kafedrasi")
        total = int(plan["price_per_seat"]) * int(seats) * int(months)
        st.markdown(f"**Jami: {_fmt(total)} so'm** ({_fmt(plan['price_per_seat'])} × {int(seats)} × {int(months)} oy)")
        if st.form_submit_button("So'rov yuborish va hisob-faktura olish", type="primary"):
            try:
                api.post("/api/subscription", json={"plan": plan["name"], "seats": int(seats), "months": int(months), "payment_method": method, "organization": org or None})
                api.invalidate()
                st.session_state.pop("billing_choice", None)
                st.success("So'rov yaratildi. Yuqorida hisob-faktura raqami ko'rsatiladi; to'lov tasdiqlangach tarif faollashadi.")
                st.rerun()
            except api.APIError as exc:
                st.error(str(exc))


def _roi_calculator(plans_data: dict) -> None:
    st.markdown("#### 🧮 ROI kalkulyator — o'qituvchi uchun qancha tejaladi?")
    c1, c2, c3, c4 = st.columns(4)
    students = c1.number_input("Talabalar (barcha guruhlar)", 10, 2000, 90, step=10)
    tasks = c2.number_input("Topshiriqlar / oy", 1, 30, 4)
    minutes = c3.number_input("Daqiqa / ish (qo'lda)", 3, 60, 12)
    hour_value = c4.number_input("O'qituvchi soati qiymati (so'm)", 10000, 500000, 50000, step=5000)
    works = students * tasks
    hours_saved = works * minutes / 60 * 0.85  # tasdiqlashga ~15% vaqt qoladi
    value = hours_saved * hour_value
    pro = next((p for p in plans_data["plans"] if p["name"] == "pro"), {"price_per_seat": 59000})
    price = int(pro["price_per_seat"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ishlar / oy", _fmt(works))
    m2.metric("Tejalgan vaqt / oy", f"{hours_saved:.0f} soat")
    m3.metric("Tejalgan qiymat / oy", f"{_fmt(value)} so'm")
    m4.metric("Pro tarif ROI", f"{value / price:.0f}×" if price else "∞", f"narx {_fmt(price)} so'm/oy")
    st.caption("Hisob: ishlar × daqiqa × 85% (o'qituvchi faqat tasdiqlaydi) ÷ 60 × soat qiymati. Universitet tarifida (25 000 so'm) ROI yanada yuqori.")


def _competitors(comp: dict) -> None:
    st.markdown("#### 🥇 Raqobatchilardan ustunlik")
    adv = comp.get("advantages") or []
    if adv:
        rows = [adv[i:i + 3] for i in range(0, len(adv), 3)]
        for row in rows:
            cols = st.columns(3)
            for col, a in zip(cols, row):
                with col:
                    st.markdown(f"**{a['title']}**")
                    st.caption(a["text"])
    table = comp.get("competitors") or {}
    if table.get("rows"):
        df = pd.DataFrame([[r["criterion"]] + r["values"] for r in table["rows"]], columns=["Mezon"] + table["columns"])
        st.dataframe(df, width="stretch", hide_index=True, height=40 + 36 * len(df))


def render() -> None:
    st.subheader("💳 Tariflar va biznes model")
    try:
        sub = api.get("/api/subscription")
        plans_data = api.cached_get("/api/plans", api.backend_url(), None)
        comp = api.cached_get("/api/competitors", api.backend_url(), None)
    except api.APIError as exc:
        st.error(str(exc))
        return
    _usage_block(sub)
    if not sub.get("enforcement"):
        st.caption("Limitlar o'chirilgan (PLAN_ENFORCEMENT=false).")
    st.markdown("---")
    _plan_cards(plans_data, sub)
    _checkout(plans_data, sub)
    addons = plans_data.get("addons") or []
    if addons:
        with st.expander("➕ Qo'shimcha xizmatlar (bir martalik)"):
            st.dataframe(pd.DataFrame([{"Xizmat": a["title"], "Narx": (_fmt(a["price"]) + " so'm") if a.get("price") else "kelishuv asosida", "Birlik": a.get("unit", ""), "Tavsif": a.get("description", "")} for a in addons]), width="stretch", hide_index=True)
    st.markdown("---")
    _roi_calculator(plans_data)
    st.markdown("---")
    _competitors(comp)
    st.caption("Narxlar va jadval `config/pricing.json` faylida — kod o'zgartirmasdan tahrirlanadi.")
