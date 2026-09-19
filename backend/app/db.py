from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
import os
from datetime import datetime
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")
engine = create_engine(DATABASE_URL, echo=False)


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str
    name: Optional[str]


class Submission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str
    course: Optional[str]
    content: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GradeRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    submission_id: int
    total_score: int
    details: Optional[str]
    confirmed: bool = Field(default=False)
    corrected_details: Optional[str] = None
    teacher_id: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    action: str
    actor: Optional[str]
    target_id: Optional[int]
    note: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False


def create_user(username: str, password: str, is_super: bool = False):
    init_db()
    with Session(engine) as s:
        u = User(username=username, hashed_password=get_password_hash(password), is_superuser=is_super)
        s.add(u)
        s.commit()
        s.refresh(u)
        return u
