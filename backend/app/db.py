"""Ma'lumotlar bazasi modellari (SQLModel) va yengil migratsiya.

SQLite (default) yoki PostgreSQL (`DATABASE_URL`) bilan ishlaydi. Jadval
yaratilgandan keyin qo'shilgan yangi ustunlar `ensure_columns()` orqali
avtomatik `ALTER TABLE ... ADD COLUMN` bilan qo'shiladi, shuning uchun eski
`data.db` fayllar ham buzilmasdan ishlayveradi.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import inspect, text
from sqlmodel import Field, Session, SQLModel, create_engine, select

from .config import settings


def utcnow() -> datetime:
    """Naive UTC vaqt (SQLite va Postgres uchun bir xil saqlanadi)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _make_engine(url: str):
    kwargs: dict[str, Any] = {"echo": False}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _make_engine(settings.database_url)


# ---------------------------------------------------------------------------
# Modellar
# ---------------------------------------------------------------------------
class User(SQLModel, table=True):
    """Tizim foydalanuvchisi: o'qituvchi, kafedra mudiri (admin) yoki dekanat."""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: str = Field(default="teacher")  # teacher | admin | dean
    plan: str = Field(default="free")     # free | pro | kafedra | universitet
    organization: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class StudentGroup(SQLModel, table=True):
    """Akademik guruh (masalan, AT-21-01)."""

    __tablename__ = "student_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    faculty: Optional[str] = None
    course_year: Optional[int] = None
    created_at: datetime = Field(default_factory=utcnow)


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True, unique=True)  # HEMIS ID yoki talaba raqami
    full_name: Optional[str] = None
    group_name: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utcnow)


class RubricTemplate(SQLModel, table=True):
    """O'qituvchi tomonidan saqlangan baholash mezonlari to'plami."""

    __tablename__ = "rubric_template"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    course: Optional[str] = None
    description: Optional[str] = None
    items: str = Field(default="[]")  # JSON: [{name, max_score, description}]
    is_default: bool = False
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class Assignment(SQLModel, table=True):
    """Topshiriq (mavzu) — ishlar shu topshiriqqa bog'lanadi."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    course: Optional[str] = Field(default=None, index=True)
    topic: Optional[str] = None
    group_name: Optional[str] = Field(default=None, index=True)
    rubric_template_id: Optional[int] = None
    max_score: float = 100.0
    reference_answer: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class Submission(SQLModel, table=True):
    """Talaba topshirgan ish (matn)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(index=True)
    group_name: Optional[str] = Field(default=None, index=True)
    course: Optional[str] = Field(default=None, index=True)
    topic: Optional[str] = None
    assignment_id: Optional[int] = None
    content: Optional[str] = None
    filename: Optional[str] = None
    word_count: int = 0
    created_at: datetime = Field(default_factory=utcnow)


class GradeRecord(SQLModel, table=True):
    """AI bahosi + o'qituvchi tasdiqlashi/tuzatishi."""

    __tablename__ = "graderecord"

    id: Optional[int] = Field(default=None, primary_key=True)
    submission_id: int = Field(index=True)
    total_score: float = 0.0            # joriy (yakuniy) ball
    max_score: float = 100.0
    ai_total_score: Optional[float] = None  # AI bergan dastlabki ball (kalibratsiya uchun)
    details: Optional[str] = None       # JSON: {rubric, feedback, errors, provider, ...}
    feedback_summary: Optional[str] = None
    plagiarism_score: Optional[float] = None
    ai_likelihood: Optional[float] = None
    similarity_score: Optional[float] = None       # guruh ichidagi eng yuqori o'xshashlik
    similar_to_student: Optional[str] = None
    status: str = Field(default="pending")  # pending | confirmed | edited
    confirmed: bool = False
    teacher_id: Optional[str] = None
    teacher_comment: Optional[str] = None
    corrected_details: Optional[str] = None  # JSON: o'qituvchi tuzatgan mezonlar
    processing_ms: Optional[int] = None
    provider: Optional[str] = None
    created_by: Optional[str] = Field(default=None, index=True)  # tarif limitlari uchun
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class AuditLog(SQLModel, table=True):
    __tablename__ = "auditlog"

    id: Optional[int] = Field(default=None, primary_key=True)
    action: str = Field(index=True)
    actor: Optional[str] = None
    target_id: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class GeneratedDocument(SQLModel, table=True):
    """Yaratilgan silabus / dars rejasi / bilet / test hujjatlari."""

    __tablename__ = "generated_document"

    id: Optional[int] = Field(default=None, primary_key=True)
    doc_type: str = Field(index=True)  # syllabus | lesson_plan | exam_tickets | test_questions | bundle
    course: Optional[str] = Field(default=None, index=True)
    title: Optional[str] = None
    content: Optional[str] = None  # JSON (strukturalangan hujjat)
    export_path: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class Subscription(SQLModel, table=True):
    """Tarif obunasi va to'lov so'rovi."""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    plan: str
    seats: int = 1
    months: int = 1
    amount: int = 0                      # so'm
    currency: str = "so'm"
    payment_method: Optional[str] = None
    invoice_no: Optional[str] = None
    status: str = Field(default="pending")  # pending | active | cancelled | expired
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


# ---------------------------------------------------------------------------
# Yordamchi funksiyalar
# ---------------------------------------------------------------------------
def ensure_columns(target_engine=None) -> list[str]:
    """Modelda bor, lekin jadvalda yo'q ustunlarni qo'shadi (yengil migratsiya).

    Faqat `ADD COLUMN` bajariladi (NULL ruxsat etilgan holda), shuning uchun
    SQLite va PostgreSQL uchun xavfsiz. Qo'shilgan ustunlar ro'yxatini qaytaradi.
    """
    eng = target_engine or engine
    added: list[str] = []
    inspector = inspect(eng)
    for table in SQLModel.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        existing = {c["name"] for c in inspector.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing:
                continue
            col_type = col.type.compile(dialect=eng.dialect)
            ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col_type}'
            with eng.begin() as conn:
                conn.execute(text(ddl))
            added.append(f"{table.name}.{col.name}")
    return added


def init_db(target_engine=None) -> None:
    eng = target_engine or engine
    SQLModel.metadata.create_all(eng)
    ensure_columns(eng)


def get_session():
    """FastAPI dependency."""
    with Session(engine) as session:
        yield session


def add_audit(session: Session, action: str, actor: Optional[str], target_id: Optional[int], note: Optional[str] = None) -> AuditLog:
    entry = AuditLog(action=action, actor=actor, target_id=target_id, note=(note or "")[:2000] or None)
    session.add(entry)
    return entry


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def loads(raw: Optional[str], default: Any = None) -> Any:
    if raw is None or raw == "":
        return {} if default is None else default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return {} if default is None else default


def upsert_student(session: Session, student_id: str, full_name: Optional[str] = None, group_name: Optional[str] = None) -> Optional[Student]:
    """Talaba (va guruh) yozuvini mavjud bo'lmasa yaratadi, bo'lsa yangilaydi."""
    student_id = (student_id or "").strip()
    if not student_id or student_id.lower() in {"unknown", "noma'lum"}:
        return None
    st = session.exec(select(Student).where(Student.student_id == student_id)).first()
    if st is None:
        st = Student(student_id=student_id, full_name=full_name, group_name=group_name)
        session.add(st)
    else:
        if full_name:
            st.full_name = full_name
        if group_name:
            st.group_name = group_name
        session.add(st)
    if group_name:
        upsert_group(session, group_name)
    return st


def upsert_group(session: Session, name: str, faculty: Optional[str] = None, course_year: Optional[int] = None) -> Optional[StudentGroup]:
    name = (name or "").strip()
    if not name:
        return None
    grp = session.exec(select(StudentGroup).where(StudentGroup.name == name)).first()
    if grp is None:
        grp = StudentGroup(name=name, faculty=faculty, course_year=course_year)
        session.add(grp)
    else:
        if faculty:
            grp.faculty = faculty
        if course_year:
            grp.course_year = course_year
        session.add(grp)
    return grp
