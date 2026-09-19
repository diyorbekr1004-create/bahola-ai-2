import streamlit as st
import httpx
import pandas as pd

BACKEND = st.secrets.get("backend_url", "http://localhost:8000")

st.set_page_config(page_title="AI O'qituvchi Hamkori", layout="wide")

st.title("AI O'qituvchi Hamkori — Demo")

# Simple auth: teacher login to obtain bearer token
if "token" not in st.session_state:
    st.session_state.token = None

with st.sidebar.expander("O'qituvchi login"):
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", key="login_btn"):
        try:
            resp = httpx.post(f"{BACKEND}/auth/token", data={"username": username, "password": password}, timeout=10.0)
            resp.raise_for_status()
            token = resp.json().get("access_token")
            st.session_state.token = token
            st.success("Login muvaffaqiyatli")
        except Exception as e:
            st.error(f"Login xatolik: {e}")
    if st.session_state.token:
        st.write("Token: (saqlangan)")
        if st.button("Logout", key="logout_btn"):
            st.session_state.token = None


def auth_headers():
    h = {}
    if st.session_state.get("token"):
        h["Authorization"] = f"Bearer {st.session_state.token}"
    return h

tab = st.tabs(["Tekshirish", "Hujjatlar", "Hisobotlar"])

with tab[0]:
    st.header("Tekshirish: Talaba ishini yuklang yoki yozing")
    uploaded = st.file_uploader("Matn yoki fayl yuklang", type=["txt", "docx"])
    text = st.text_area("Yoki bu yerga matnni joylang")
    st.markdown("---")
    st.subheader("Saqlangan baholar")
    if st.button("Baholar ro'yxatini yuklash"):
        try:
            resp = httpx.get(f"{BACKEND}/api/grades", timeout=10.0, headers=auth_headers())
            resp.raise_for_status()
            grades = resp.json()
            if grades:
                options = {f"ID {g['grade_id']} — {g['course'] or ''} — {g['total_score']}": g['grade_id'] for g in grades}
                sel = st.selectbox("Bahoni tanlang", options=list(options.keys()))
                gid = options[sel]
                # load selected grade
                resp2 = httpx.get(f"{BACKEND}/api/grade/{gid}", timeout=10.0, headers=auth_headers())
                resp2.raise_for_status()
                gdet = resp2.json()
                st.write("Grade details:")
                st.json(gdet)
                st.info(f"Tasdiqlangan: {gdet.get('confirmed')} | Yangilangan: {gdet.get('updated_at')}")
            else:
                st.info("Hech qanday saqlangan baho topilmadi.")
        except Exception as e:
            st.error(f"Baholarni yuklashda xatolik: {e}")
    if st.button("Baholash"):
        with st.spinner("Yaratilmoqda..."):
            files = {}
            form = {"text": text}
            if uploaded:
                files["file"] = (uploaded.name, uploaded.getvalue())
            try:
                resp = httpx.post(f"{BACKEND}/api/grade", data=form, files=files, timeout=30.0)
                resp.raise_for_status()
                data = resp.json()
                st.success(f"Total score: {data['total_score']}")
                st.json(data)

                # Run detection on the text as well
                try:
                    det = httpx.post(f"{BACKEND}/api/detect", json={"text": text}, timeout=10.0, headers=auth_headers())
                    det.raise_for_status()
                    ddata = det.json()
                    st.info(f"Plagiarism: {ddata['plagiarism_score']} | AI-likelihood: {ddata['ai_likelihood']}")
                    st.write("Reasons:")
                    for r in ddata.get('reasons', []):
                        st.write(f"- {r}")
                except Exception:
                    pass

                # Teacher actions: confirm or edit (use real grade_id if returned)
                grade_id = data.get('grade_id')
                if not grade_id:
                    st.warning("No grade_id returned by backend — confirm/edit will use record 1 (dev).")
                    grade_id = 1

                cols = st.columns(2)
                with cols[0]:
                    teacher = st.text_input("Teacher ID for confirm", value="teacher_1", key=f"confirm_teacher_{grade_id}")
                    if st.button("Tasdiqlash", key=f"confirm_{grade_id}"):
                        try:
                            resp2 = httpx.post(f"{BACKEND}/api/grade/{grade_id}/confirm", data={"teacher_id": teacher}, timeout=10.0, headers=auth_headers())
                            resp2.raise_for_status()
                            st.success("Confirmed")
                        except Exception as e:
                            st.error(f"Confirm failed: {e}")

                with cols[1]:
                    corrected = st.text_area("To'g'irlangan tafsilotlar", key=f"corrected_{grade_id}")
                    corrected_total = st.number_input("To'g'irlangan jami ball", value=data.get('total_score', 0), key=f"corrected_total_{grade_id}")
                    teacher2 = st.text_input("Teacher ID for edit", value="teacher_1_edit", key=f"edit_teacher_{grade_id}")
                    if st.button("Yuborish (Edit)", key=f"edit_{grade_id}"):
                        try:
                            payload = {"teacher_id": teacher2, "corrected_details": corrected, "corrected_total": int(corrected_total)}
                            resp3 = httpx.post(f"{BACKEND}/api/grade/{grade_id}/edit", json=payload, timeout=10.0, headers=auth_headers())
                            resp3.raise_for_status()
                            st.success("Edit logged")
                        except Exception as e:
                            st.error(f"Edit failed: {e}")
            except Exception as e:
                st.error(f"Xatolik: {e}")

with tab[1]:
    st.header("Hujjatlar generatori")
    course = st.text_input("Fan nomi", "Matematika")
    hours = st.number_input("Soatlar (jami)", value=60)
    weeks = st.number_input("Haftalar", value=15)
    if st.button("Generatsiya"):
        try:
            resp = httpx.post(f"{BACKEND}/api/generate-docs", json={"course_name": course, "hours": int(hours), "weeks": int(weeks)}, headers=auth_headers())
            resp.raise_for_status()
            d = resp.json()
            st.subheader("Silabus")
            st.text_area("", value=d["syllabus"], height=300)
            st.subheader("Imtihon bileti")
            st.text_area("", value=d["exam_ticket"], height=200)
        except Exception as e:
            st.error(f"Xatolik: {e}")

with tab[2]:
    st.header("Hisobotlar")
    course = st.text_input("Report uchun fan nomi", "Matematika - Guruh A")
    gid = st.text_input("Guruh ID (ixtiyoriy)")
    if st.button("Yaratish"):
        try:
            resp = httpx.post(f"{BACKEND}/api/reports", json={"course_name": course, "group_id": gid}, headers=auth_headers())
            resp.raise_for_status()
            d = resp.json()
            st.success(d.get("summary"))
        except Exception as e:
            st.error(f"Xatolik: {e}")

    st.markdown("---")
    if st.button("Audit logni ko'rsatish"):
        try:
            resp = httpx.get(f"{BACKEND}/api/audit", timeout=10.0, headers=auth_headers())
            resp.raise_for_status()
            logs = resp.json()
            if logs:
                df = pd.DataFrame(logs)
                st.table(df)
            else:
                st.info("Hech qanday audit topilmadi.")
        except Exception as e:
            st.error(f"Audit olishda xatolik: {e}")
