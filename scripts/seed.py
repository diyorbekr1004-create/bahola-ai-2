"""Demo ma'lumotlar: guruhlar, talabalar, turli sifatdagi ishlar, tasdiqlangan/tuzatilgan baholar, bitta hujjatlar to'plami.

Ishga tushirish (loyiha ildizidan):
    python scripts/seed.py            # mavjud bazaga qo'shadi
    python scripts/seed.py --reset    # SQLite faylini o'chirib, qaytadan yaratadi
"""
from __future__ import annotations

import asyncio
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

if "--reset" in sys.argv:
    url = os.getenv("DATABASE_URL", "sqlite:///./data.db")
    if url.startswith("sqlite:///"):
        db_path = Path(url.replace("sqlite:///", ""))
        if db_path.exists():
            db_path.unlink()
            print(f"Baza o'chirildi: {db_path}")

from sqlmodel import Session, select  # noqa: E402

from app.db import GradeRecord, engine, init_db, upsert_group, upsert_student  # noqa: E402
from app.main import seed_default_rubric  # noqa: E402
from app.schemas import DocRequest, EditGradeRequest  # noqa: E402
from app.security import ensure_demo_users  # noqa: E402
from app.services.documents import generate_documents  # noqa: E402
from app.services.grading import confirm_grade, edit_grade, grade_content  # noqa: E402

rnd = random.Random(42)

FIRST = ["Aziz", "Dilnoza", "Bobur", "Malika", "Sardor", "Nilufar", "Jasur", "Gulnora", "Otabek", "Sevara", "Timur", "Zarina", "Umid", "Kamola", "Farrux", "Madina", "Shoxrux", "Laylo", "Rustam", "Nigora"]
LAST = ["Karimov", "Rahimova", "Toshmatov", "Yusupova", "Aliyev", "Nazarova", "Ergashev", "Saidova", "Xolmatov", "Qodirova", "Mirzayev", "Islomova", "Sobirov", "Abdullayeva", "Tursunov", "Hasanova"]

GROUPS = [
    {"name": "AT-21-01", "faculty": "Axborot texnologiyalari", "course_year": 3},
    {"name": "AT-21-02", "faculty": "Axborot texnologiyalari", "course_year": 3},
    {"name": "PD-22-01", "faculty": "Pedagogika", "course_year": 2},
]
COURSES = {
    "Pedagogika": ["Ta'lim va texnologiya", "Interfaol metodlar", "Baholash tizimi"],
    "Informatika": ["Algoritmlar va blok-sxemalar", "Ma'lumotlar bazalari asoslari"],
}


INTROS = [
    "{T} mavzusi bugungi kunda ta'lim tizimida dolzarb masalalardan biridir. Ushbu ishning maqsadi — {t} mohiyatini va amaliy ahamiyatini tahlil qilish.",
    "Hozirgi davrda {t} masalasi ko'plab tadqiqotchilar e'tiborini tortmoqda. Mazkur ishda men {t}ning asosiy jihatlarini ko'rib chiqaman.",
    "{T} — zamonaviy ta'limning ajralmas qismi. Ushbu inshoda uning afzalliklari va muammolari haqida fikr yuritiladi.",
    "Ta'lim sifatini oshirish haqida gap ketganda {t} birinchi o'rinda turadi. Ishning maqsadi shu masalani asoslashdir.",
    "Nima uchun {t} muhim? Ushbu savolga javob berish uchun avvalo uning mazmunini aniqlab olish lozim.",
]
CONCLUSIONS = [
    "Xulosa qilib aytganda, {t} tizimli yondashuv va malakali kadrlar bilan uyg'unlashgandagina kutilgan samarani beradi. Demak, {c} — bu birinchi navbatdagi vazifa.",
    "Shunday qilib, {t} bo'yicha olib borilgan tahlil shuni ko'rsatadiki, {c}. Yakunida ta'kidlash joizki, bu yo'nalishda izchil ish olib borish zarur.",
    "Umuman olganda, {t} ta'lim jarayonini sifat jihatidan yangi bosqichga olib chiqadi. Demak, {c}.",
    "Xulosa: {c}, va bu {t}ni rivojlantirishning asosiy sharti hisoblanadi.",
]
CONNECTORS = [("Birinchidan", "Ikkinchidan"), ("Avvalo", "Keyingi navbatda"), ("Eng avvalo", "Shuningdek"), ("Dastlab", "So'ngra")]
WEAK_LINES = [
    "{T} kerak. {T} yaxshi narsa. {c}. {T} yaxshi narsa.",
    "{T} haqida ko'p gapirishadi. Men ham shunday deb o'ylayman. {c}. Shu bilan tugatdim.",
    "{c}. Bu juda muhim. Bu juda muhim. Hammasi shu.",
    "{T} degani nima? Bilmayman, lekin {c}. Yana bir bor: {c}.",
]


def essay(topic: str, quality: str, salt: int) -> str:
    """Sifat darajasiga qarab turli tuzilmali matn tuzadi (strong / good / medium / weak)."""
    r = random.Random(salt)
    t, T = topic.lower(), topic
    facts = [f"{r.randint(2019, 2025)}-yilgi tadqiqotlarga ko'ra {r.randint(12, 48)}% o'sish kuzatilgan", f"UNESCO ({r.randint(2020, 2024)}) hisobotida bu masala alohida ta'kidlangan",
             f"so'rovnomada {r.randint(120, 900)} nafar talaba ishtirok etgan", f"natijalar {r.randint(3, 9)} ta oliy ta'lim muassasasida sinovdan o'tkazilgan",
             f"o'qituvchilarning {r.randint(55, 92)}% bu yondashuvni ma'qullagan", f"{r.randint(2, 6)} yillik kuzatuv natijalari buni tasdiqlaydi"]
    r.shuffle(facts)
    claims = [f"{t} ta'lim sifatini oshirishga xizmat qiladi", f"{t} o'qituvchi va talaba o'rtasidagi muloqotni faollashtiradi", f"{t} mustaqil fikrlashni rivojlantiradi",
              f"{t}ni joriy etishda moddiy-texnik baza muhim rol o'ynaydi", f"{t} bo'yicha o'qituvchilarni tayyorlash zarur", f"{t} talabalar motivatsiyasini oshiradi",
              f"{t} baholashda shaffoflikni ta'minlaydi", f"{t} vaqtni tejashga yordam beradi"]
    r.shuffle(claims)
    c1, c2 = r.choice(CONNECTORS)
    intro = r.choice(INTROS).format(T=T, t=t)
    concl = r.choice(CONCLUSIONS).format(T=T, t=t, c=claims[4])
    body1 = f"{c1}, {claims[0]}, chunki {facts[0]}. Masalan, {facts[1]}. {c2}, {claims[1]}; shuning uchun ko'plab oliygohlar bu yo'nalishga e'tibor qaratmoqda."
    body2 = f"Bundan tashqari, {claims[2]}. Shu bilan birga, {facts[2]}, natijada {claims[3]} degan xulosaga kelindi. Biroq ba'zi mutaxassislar fikricha, {claims[5]} degan fikr hali to'liq isbotlanmagan."
    if quality == "strong":
        return "\n\n".join([intro, body1, body2, concl])
    if quality == "good":
        return "\n\n".join([intro, body1 if r.random() < 0.5 else body2, concl])
    if quality == "medium":
        body = f"{claims[0]}. Masalan, {facts[0]}. {claims[1]}. Bu haqida ko'p gapiriladi va u muhim hisoblanadi. {claims[2]}."
        tail = f"Umuman olganda, {t} foydali." if r.random() < 0.6 else f"{claims[3]}."
        return "\n\n".join([intro, body, tail])
    return r.choice(WEAK_LINES).format(T=T, t=t, c=claims[0])


async def main() -> None:
    init_db()
    ensure_demo_users()
    seed_default_rubric()
    with Session(engine) as s:
        for g in GROUPS:
            upsert_group(s, **g)
        s.commit()

        students = []
        idx = 0
        for g in GROUPS:
            for _ in range(10):
                idx += 1
                sid = f"{300000 + idx}"
                name = f"{LAST[idx % len(LAST)]} {FIRST[idx % len(FIRST)]}"
                upsert_student(s, sid, full_name=name, group_name=g["name"])
                students.append({"student_id": sid, "name": name, "group": g["name"], "skill": rnd.choice(["strong", "good", "good", "medium", "medium", "weak"])})
        s.commit()

        created = []
        copied_from: dict = {}
        for course, topics in COURSES.items():
            for t_i, topic in enumerate(topics):
                for st in students:
                    if course == "Informatika" and not st["group"].startswith("AT"):
                        continue
                    if course == "Pedagogika" and st["group"].startswith("AT") and t_i == 2:
                        continue
                    quality = st["skill"]
                    if rnd.random() < 0.2:  # tasodifiy o'zgarish
                        quality = rnd.choice(["strong", "good", "medium", "weak"])
                    text = essay(topic, quality, salt=hash((st["student_id"], topic)) & 0xFFFF)
                    if st["student_id"].endswith("7") and t_i == 0 and copied_from.get(topic):
                        text = copied_from[topic] + " Qo'shimcha: men ham shunday fikrdaman."  # ataylab ko'chirilgan ish
                    elif st["student_id"].endswith("3") and t_i == 0:
                        copied_from[topic] = text
                    res = await grade_content(s, content=text, student_id=st["student_id"], student_name=st["name"], group_name=st["group"], course=course, topic=topic, actor="seed")
                    created.append(res)
        print(f"{len(created)} ta ish baholandi.")

        # Human-in-the-loop: 60% tasdiqlash, 15% tuzatish
        confirmed = edited = 0
        for res in created:
            roll = rnd.random()
            if roll < 0.6:
                confirm_grade(s, res.grade_id, teacher_id="teacher", comment=None, actor="teacher")
                confirmed += 1
            elif roll < 0.75:
                rubric = [dict(r.model_dump(), score=max(0.0, min(float(r.max_score), float(r.score or 0) + rnd.choice([-5, -3, 3, 5])))) for r in res.rubric]
                edit_grade(s, res.grade_id, EditGradeRequest(teacher_id="teacher", corrected_rubric=rubric, comment="O'qituvchi tuzatishi (demo)"), actor="teacher")
                edited += 1
        print(f"Tasdiqlangan: {confirmed}, tuzatilgan: {edited}, kutilmoqda: {len(created) - confirmed - edited}")

        doc = await generate_documents(s, DocRequest(course_name="Matematika", hours=60, weeks=15, n_tickets=5, n_questions=10, export_format="docx"), actor="seed")
        print(f"Hujjatlar to'plami yaratildi: id={doc.document_id}, docx={doc.export_path}")
        total = s.exec(select(GradeRecord)).all()
        print(f"Bazada jami baholar: {len(total)}")


if __name__ == "__main__":
    asyncio.run(main())
    print("Seed yakunlandi. Streamlit: streamlit run frontend/streamlit_app.py")
