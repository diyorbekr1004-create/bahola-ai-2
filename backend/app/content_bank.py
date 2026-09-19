"""Oflayn (mock) rejim uchun fan mavzulari banki va hujjat shablonlari.

Real LLM ulanmaganda silabus/bilet/test shu bankdan tuziladi. Fan nomi
bank kalitlaridan biriga mos kelmasa, umumiy shablon ishlatiladi.
"""
from __future__ import annotations

import random
import re
from typing import Dict, List, Optional

TOPIC_BANK: Dict[str, List[str]] = {
    "matematika": [
        "To'plamlar nazariyasi va mantiq elementlari", "Haqiqiy sonlar va ketma-ketliklar", "Funksiya tushunchasi va uning xossalari",
        "Limitlar nazariyasi", "Uzluksiz funksiyalar", "Hosila va differensial", "Hosilaning tatbiqlari",
        "Aniqmas integral", "Aniq integral va uning tatbiqlari", "Matritsalar va determinantlar",
        "Chiziqli tenglamalar sistemasi", "Vektorlar algebrasi", "Analitik geometriya elementlari",
        "Differensial tenglamalar asoslari", "Qatorlar nazariyasi",
    ],
    "fizika": [
        "Kinematika asoslari", "Dinamika. Nyuton qonunlari", "Saqlanish qonunlari", "Aylanma harakat va tebranishlar",
        "Molekulyar-kinetik nazariya", "Termodinamika qonunlari", "Elektrostatika", "O'zgarmas tok qonunlari",
        "Magnit maydon", "Elektromagnit induksiya", "O'zgaruvchan tok", "Geometrik optika",
        "To'lqin optikasi", "Kvant fizikasi elementlari", "Atom va yadro fizikasi",
    ],
    "informatika": [
        "Axborot va axborot texnologiyalari", "Sanoq sistemalari va kodlash", "Kompyuter arxitekturasi",
        "Operatsion tizimlar", "Algoritmlar va blok-sxemalar", "Dasturlash asoslari", "Shartli va takrorlanuvchi konstruksiyalar",
        "Massivlar va satrlar", "Funksiyalar va modullar", "Ma'lumotlar tuzilmalari", "Fayllar bilan ishlash",
        "Ma'lumotlar bazalari asoslari", "Kompyuter tarmoqlari", "Axborot xavfsizligi", "Sun'iy intellektga kirish",
    ],
    "dasturlash": [
        "Dasturlash tillari va muhitlar", "O'zgaruvchilar, turlar va operatorlar", "Shart operatorlari",
        "Sikllar", "Funksiyalar va rekursiya", "Ro'yxatlar va lug'atlar", "Satrlar bilan ishlash",
        "Ob'ektga yo'naltirilgan dasturlash: sinflar", "Meros va polimorfizm", "Istisnolar bilan ishlash",
        "Fayllar va JSON", "Modullar va paketlar", "Testlash asoslari", "Git va versiya nazorati", "Yakuniy loyiha",
    ],
    "python": [
        "Python muhiti va sintaksis", "Ma'lumot turlari va o'zgaruvchilar", "Shart operatorlari va mantiq",
        "Sikllar va iteratorlar", "Funksiyalar, lambda, rekursiya", "Ro'yxat, kortej, to'plam, lug'at",
        "Satrlar va formatlash", "Fayllar va istisnolar", "Sinflar va OOP", "Modullar, paketlar, pip",
        "Standart kutubxona: datetime, collections, itertools", "Regular expressions", "NumPy va Pandas asoslari",
        "Ma'lumotlarni vizualizatsiya qilish", "Yakuniy loyiha himoyasi",
    ],
    "ma'lumotlar bazasi": [
        "Ma'lumotlar bazalari tushunchasi va turlari", "Relyatsion model", "ER-diagrammalar", "Normalizatsiya (1NF-3NF)",
        "SQL: DDL buyruqlari", "SQL: DML buyruqlari", "SELECT va filtrlash", "JOIN operatsiyalari",
        "Agregat funksiyalar va guruhlash", "Ichki so'rovlar", "Indekslar va optimallashtirish", "Tranzaksiyalar va ACID",
        "Saqlanadigan protseduralar", "NoSQL bazalar", "Xavfsizlik va zaxira nusxalash",
    ],
    "sun'iy intellekt": [
        "Sun'iy intellekt tarixi va yo'nalishlari", "Qidiruv algoritmlari", "Bilimlarni tasvirlash", "Mantiqiy xulosa chiqarish",
        "Mashinali o'qitishga kirish", "Nazoratli o'qitish: regressiya", "Nazoratli o'qitish: klassifikatsiya",
        "Nazoratsiz o'qitish: klasterlash", "Neyron tarmoqlar asoslari", "Chuqur o'qitish", "Kompyuter ko'rish",
        "Tabiiy tilni qayta ishlash", "Katta til modellari", "AI etikasi va xavfsizlik", "Yakuniy loyiha",
    ],
    "ingliz tili": [
        "Introductions and Personal Information", "Daily Routines and Present Simple", "Past Simple and Life Events",
        "Future Forms and Plans", "Present Perfect", "Modal Verbs", "Comparatives and Superlatives",
        "Reading Strategies: Skimming and Scanning", "Academic Vocabulary", "Writing a Paragraph",
        "Writing an Essay", "Listening for Main Ideas", "Speaking: Presentations", "Conditionals", "Revision and Exam Practice",
    ],
    "tarix": [
        "Tarix fanining predmeti va manbalari", "Qadimgi davlatlar", "O'rta asrlar sivilizatsiyasi", "Amir Temur va temuriylar davri",
        "Xonliklar davri", "Chor Rossiyasi istilosi", "Jadidchilik harakati", "Sovet davri va uning oqibatlari",
        "Mustaqillik uchun kurash", "O'zbekiston mustaqilligi", "Konstitutsiya va davlat qurilishi", "Iqtisodiy islohotlar",
        "Ta'lim va madaniyat", "Xalqaro munosabatlar", "Yangi O'zbekiston strategiyasi",
    ],
    "iqtisodiyot": [
        "Iqtisodiyot nazariyasining predmeti", "Talab va taklif", "Bozor muvozanati va elastiklik", "Iste'molchi xatti-harakati",
        "Ishlab chiqarish va xarajatlar", "Bozor tuzilmalari", "Mehnat bozori", "Makroiqtisodiy ko'rsatkichlar",
        "Inflyatsiya va ishsizlik", "Pul-kredit siyosati", "Fiskal siyosat", "Iqtisodiy o'sish",
        "Xalqaro savdo", "Moliya bozorlari", "Raqamli iqtisodiyot",
    ],
    "kimyo": [
        "Atom tuzilishi", "Davriy qonun va davriy sistema", "Kimyoviy bog'lanish", "Moddaning agregat holatlari",
        "Eritmalar", "Kimyoviy reaksiyalar tezligi", "Kimyoviy muvozanat", "Oksidlanish-qaytarilish reaksiyalari",
        "Metallar", "Metallmaslar", "Organik kimyoga kirish", "Uglevodorodlar", "Kislorodli organik birikmalar",
        "Polimerlar", "Kimyo va ekologiya",
    ],
    "biologiya": [
        "Hujayra tuzilishi", "Moddalar almashinuvi", "Hujayra bo'linishi", "Genetika asoslari", "Irsiyat qonunlari",
        "O'zgaruvchanlik", "Evolyutsiya nazariyasi", "Organizmlar sistematikasi", "O'simliklar fiziologiyasi",
        "Hayvonlar fiziologiyasi", "Odam anatomiyasi", "Ekologiya asoslari", "Biotexnologiya", "Biosfera", "Bioxilma-xillikni saqlash",
    ],
    "pedagogika": [
        "Pedagogika fanining predmeti", "Ta'lim tizimi va qonunchilik", "Didaktika asoslari", "Ta'lim metodlari",
        "Zamonaviy pedagogik texnologiyalar", "Interfaol metodlar", "Baholash va nazorat", "Tarbiya nazariyasi",
        "Sinf rahbari faoliyati", "Inklyuziv ta'lim", "Raqamli ta'lim vositalari", "Pedagogik mahorat",
        "O'quv dasturlarini loyihalash", "Ta'limda sun'iy intellekt", "Pedagogik tadqiqot metodlari",
    ],
}

GENERIC_TOPICS = [
    "{course} faniga kirish: predmet, maqsad va vazifalar", "{course} fanining asosiy tushunchalari va terminlari",
    "{course} fanining nazariy asoslari", "{course} rivojlanish tarixi va zamonaviy yo'nalishlari",
    "{course} fanida tadqiqot metodlari", "{course}: asosiy qonuniyatlar va tamoyillar",
    "{course}: amaliy masalalarni yechish usullari", "{course}: tahlil va modellashtirish",
    "{course} fanining boshqa fanlar bilan aloqasi", "{course}: zamonaviy texnologiyalar va vositalar",
    "{course}: amaliyotda qo'llash misollari", "{course}: loyiha ishini rejalashtirish",
    "{course}: sifat va samaradorlikni baholash", "{course}: muammolar va istiqbollar", "Yakuniy takrorlash va umumlashtirish",
]

DEFAULT_LITERATURE = [
    "O'zbekiston Respublikasi Oliy ta'lim, fan va innovatsiyalar vazirligi tomonidan tasdiqlangan namunaviy dastur.",
    "Fan bo'yicha asosiy darslik (so'nggi nashr).",
    "Fan bo'yicha o'quv-uslubiy majmua (kafedra tomonidan tayyorlangan).",
    "Elektron ta'lim resurslari: ziyonet.uz, hemis tizimi, ochiq onlayn kurslar.",
]


def _norm(s: str) -> str:
    return re.sub(r"[^\w\s']", " ", (s or "").lower()).strip()


def topics_for_course(course: str, weeks: int, custom: Optional[List[str]] = None) -> List[str]:
    """Fan nomiga mos mavzular ro'yxati (uzunligi = weeks)."""
    if custom:
        base = [t.strip() for t in custom if t and t.strip()]
    else:
        key = _norm(course)
        base: List[str] = []
        for bank_key, topics in TOPIC_BANK.items():
            if bank_key in key or key in bank_key:
                base = list(topics)
                break
        if not base:
            base = [t.format(course=course.strip()) for t in GENERIC_TOPICS]
    if not base:
        base = [t.format(course=course.strip()) for t in GENERIC_TOPICS]
    out: List[str] = []
    i = 0
    while len(out) < weeks:
        t = base[i % len(base)]
        if i >= len(base):
            t = f"{t} (chuqurlashtirilgan)"
        out.append(t)
        i += 1
    return out[:weeks]


THEORY_QUESTION_TEMPLATES = [
    "«{topic}» mavzusining mohiyatini va asosiy tushunchalarini yoritib bering.",
    "«{topic}» bo'yicha asosiy ta'riflar, qonuniyatlar va ularning ahamiyatini tushuntiring.",
    "«{topic}» mavzusida qanday muammolar o'rganiladi? Ularning yechim yo'llarini bayon qiling.",
]
EXPLAIN_QUESTION_TEMPLATES = [
    "«{topic}» va «{other}» mavzularini taqqoslang: umumiy va farqli jihatlarini ko'rsating.",
    "«{topic}» mavzusining amaliyotdagi ahamiyatini misollar bilan tushuntiring.",
    "«{topic}» bo'yicha bilimlar kasbiy faoliyatda qanday qo'llaniladi? Asoslab bering.",
]
PRACTICAL_TASK_TEMPLATES = [
    "«{topic}» mavzusiga oid amaliy masalani yeching va yechim bosqichlarini izohlang.",
    "«{topic}» bo'yicha kichik loyiha/tahlil rejasini tuzing va kutilgan natijani asoslang.",
    "«{topic}» mavzusi bo'yicha real vaziyatga oid keys (case study) tahlilini bajaring.",
]

MCQ_TEMPLATES = [
    {
        "q": "«{topic}» mavzusining asosiy maqsadi nimadan iborat?",
        "correct": "{topic} bo'yicha nazariy bilim va amaliy ko'nikmalarni shakllantirish",
        "distractors": ["Faqat tarixiy sanalarni yodlash", "Boshqa fan mavzularini takrorlash", "Baholashsiz mustaqil ish bajarish"],
    },
    {
        "q": "Quyidagilardan qaysi biri «{course}» fanida «{topic}» mavzusidan keyin o'rganiladi?",
        "correct": "{next_topic}",
        "distractors": ["{other1}", "{other2}", "Yuqoridagilarning hech biri"],
    },
    {
        "q": "«{topic}» mavzusini o'zlashtirish uchun qaysi faoliyat eng samarali?",
        "correct": "Nazariyani amaliy mashqlar va misollar bilan mustahkamlash",
        "distractors": ["Faqat ma'ruza matnini o'qish", "Mavzuni o'tkazib yuborish", "Faqat test savollarini yodlash"],
    },
    {
        "q": "«{topic}» mavzusi qaysi fanga tegishli?",
        "correct": "{course}",
        "distractors": ["Jismoniy tarbiya", "Chet tili", "Falsafa"],
    },
]


def build_exam_tickets(course: str, topics: List[str], n_tickets: int, seed: Optional[str] = None) -> List[dict]:
    rnd = random.Random(seed or course)
    tickets: List[dict] = []
    for i in range(n_tickets):
        t1 = topics[(i * 3) % len(topics)]
        t2 = topics[(i * 3 + 1) % len(topics)]
        t3 = topics[(i * 3 + 2) % len(topics)]
        other = topics[(i * 3 + 5) % len(topics)]
        tickets.append(
            {
                "number": i + 1,
                "questions": [
                    {"type": "Nazariy savol", "text": rnd.choice(THEORY_QUESTION_TEMPLATES).format(topic=t1)},
                    {"type": "Tushuntirish savoli", "text": rnd.choice(EXPLAIN_QUESTION_TEMPLATES).format(topic=t2, other=other)},
                    {"type": "Amaliy vazifa", "text": rnd.choice(PRACTICAL_TASK_TEMPLATES).format(topic=t3)},
                ],
            }
        )
    return tickets


def build_mcq(course: str, topics: List[str], n_questions: int, seed: Optional[str] = None) -> List[dict]:
    rnd = random.Random((seed or course) + "mcq")
    letters = ["A", "B", "C", "D"]
    out: List[dict] = []
    for i in range(n_questions):
        topic = topics[i % len(topics)]
        tpl = MCQ_TEMPLATES[i % len(MCQ_TEMPLATES)]
        nxt = topics[(i + 1) % len(topics)]
        others = [t for t in topics if t not in {topic, nxt}] or ["Boshqa mavzu"]
        rnd.shuffle(others)
        fmt = dict(topic=topic, course=course, next_topic=nxt, other1=others[0], other2=others[1 % len(others)])
        correct = tpl["correct"].format(**fmt)
        options = [correct] + [d.format(**fmt) for d in tpl["distractors"]]
        rnd.shuffle(options)
        answer = letters[options.index(correct)]
        out.append(
            {
                "number": i + 1,
                "topic": topic,
                "question": tpl["q"].format(**fmt),
                "options": {letters[k]: opt for k, opt in enumerate(options)},
                "answer": answer,
            }
        )
    return out


def build_lesson_plan(course: str, topic: str, week: int = 1, duration: int = 80) -> dict:
    """80 daqiqalik (2 akademik soat) dars rejasi."""
    return {
        "course": course,
        "week": week,
        "topic": topic,
        "duration_minutes": duration,
        "objectives": [
            f"Talabalarga «{topic}» mavzusining asosiy tushunchalarini tushuntirish.",
            "Nazariy bilimlarni amaliy misollar orqali mustahkamlash.",
            "Tanqidiy fikrlash va mustaqil ishlash ko'nikmalarini rivojlantirish.",
        ],
        "competencies": ["Fanga oid bilim va tushunish", "Tahlil qilish", "Amaliyotda qo'llash", "Muloqot va hamkorlik"],
        "methods": ["Ma'ruza-suhbat", "Aqliy hujum", "Kichik guruhlarda ishlash", "Keys-stadi", "Muammoli ta'lim"],
        "materials": ["Taqdimot (slaydlar)", "Tarqatma materiallar", "Darslik va o'quv qo'llanma", "Onlayn test platformasi"],
        "stages": [
            {"stage": "Tashkiliy qism", "minutes": 5, "activity": "Davomat, dars maqsadini e'lon qilish, motivatsiya."},
            {"stage": "O'tilgan mavzuni takrorlash", "minutes": 10, "activity": "Blits-savollar, qisqa test."},
            {"stage": "Yangi mavzu bayoni", "minutes": 30, "activity": f"«{topic}» mavzusining asosiy tushunchalari, misollar, sxema/jadvallar bilan izohlash."},
            {"stage": "Mustahkamlash (amaliy qism)", "minutes": 25, "activity": "Kichik guruhlarda topshiriq yechish, natijalarni taqdim etish, muhokama."},
            {"stage": "Baholash va uyga vazifa", "minutes": 10, "activity": "Reflektsiya, faol talabalarni rag'batlantirish, mustaqil ish topshirig'ini berish."},
        ],
        "homework": f"«{topic}» mavzusi bo'yicha 5 ta savolga yozma javob tayyorlash va bitta amaliy misol keltirish.",
        "assessment": "Faollik (JN) — 5 ballgacha; uy vazifasi keyingi darsda tekshiriladi.",
    }


def build_syllabus(course: str, hours: int, weeks: int, topics: List[str], level: Optional[str] = None) -> dict:
    lecture_w = max(1, round(hours / (4 * weeks)))
    practice_w = max(1, round(hours / (4 * weeks)))
    independent_w = max(1, round(hours / (2 * weeks)))
    mid1 = max(1, weeks // 2)
    mid2 = max(mid1 + 1, weeks - 1)
    weekly = []
    for i, topic in enumerate(topics, start=1):
        assessment = "JN"
        if i == mid1:
            assessment = "1-ON"
        elif i == mid2:
            assessment = "2-ON"
        if i == weeks:
            assessment = "YN (yakuniy nazorat)"
        weekly.append(
            {
                "week": i,
                "topic": topic,
                "lecture_hours": lecture_w,
                "practice_hours": practice_w,
                "independent_hours": independent_w,
                "assessment": assessment,
            }
        )
    total_lecture = lecture_w * weeks
    total_practice = practice_w * weeks
    total_independent = independent_w * weeks
    return {
        "course": course,
        "level": level or "Bakalavriat",
        "weeks": weeks,
        "hours": hours,
        "hours_breakdown": {
            "lecture": total_lecture,
            "practice": total_practice,
            "independent": total_independent,
            "total": total_lecture + total_practice + total_independent,
        },
        "goals": [
            f"«{course}» fanining nazariy asoslari va amaliy ko'nikmalarini shakllantirish.",
            "Olingan bilimlarni kasbiy faoliyatda mustaqil qo'llash qobiliyatini rivojlantirish.",
            "Tanqidiy fikrlash, tahlil va muammolarni yechish kompetensiyalarini rivojlantirish.",
        ],
        "learning_outcomes": [
            f"«{course}» fanining asosiy tushunchalari va qonuniyatlarini biladi.",
            "Fanga oid masalalarni tahlil qiladi va yechim taklif qiladi.",
            "Zamonaviy vositalar va metodlardan amaliyotda foydalana oladi.",
            "Natijalarni yozma va og'zaki shaklda asosli taqdim eta oladi.",
        ],
        "assessment_policy": [
            {"type": "Joriy nazorat (JN)", "max_score": 30, "description": "Amaliy mashg'ulotlardagi faollik, uy vazifalari, mustaqil ishlar."},
            {"type": "Oraliq nazorat (ON)", "max_score": 20, "description": f"{mid1}- va {mid2}-haftalarda yozma ish/test."},
            {"type": "Yakuniy nazorat (YN)", "max_score": 50, "description": "Semestr yakunida yozma ish yoki og'zaki imtihon."},
        ],
        "grade_scale": "86–100 — a'lo (5); 71–85 — yaxshi (4); 56–70 — qoniqarli (3); 0–55 — qoniqarsiz (2).",
        "literature": DEFAULT_LITERATURE,
        "weekly": weekly,
    }
