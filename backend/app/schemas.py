"""API kirish/chiqish sxemalari (Pydantic v2)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Baholash
# ---------------------------------------------------------------------------
class RubricItem(BaseModel):
    name: str
    max_score: float = Field(gt=0)
    score: Optional[float] = None
    evidence: Optional[str] = None
    description: Optional[str] = None

    @field_validator("score")
    @classmethod
    def _clamp_score(cls, v, info):
        if v is None:
            return v
        return max(0.0, float(v))


class Feedback(BaseModel):
    summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class IntegrityReport(BaseModel):
    plagiarism_score: Optional[float] = None
    ai_likelihood: Optional[float] = None
    similarity_score: Optional[float] = None
    similar_to_student: Optional[str] = None
    reasons: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)


class GradeResponse(BaseModel):
    grade_id: Optional[int] = None
    submission_id: Optional[int] = None
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    group_name: Optional[str] = None
    course: Optional[str] = None
    topic: Optional[str] = None
    total_score: float
    max_score: float = 100.0
    ai_total_score: Optional[float] = None
    grade_5: Optional[int] = None
    rubric: List[RubricItem] = Field(default_factory=list)
    feedback: Feedback = Field(default_factory=Feedback)
    integrity: IntegrityReport = Field(default_factory=IntegrityReport)
    plagiarism_score: Optional[float] = None
    ai_likelihood: Optional[float] = None
    status: str = "pending"
    confirmed: bool = False
    teacher_id: Optional[str] = None
    teacher_comment: Optional[str] = None
    provider: Optional[str] = None
    processing_ms: Optional[int] = None
    word_count: Optional[int] = None
    filename: Optional[str] = None
    content_preview: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GradeListItem(BaseModel):
    grade_id: int
    submission_id: int
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    group_name: Optional[str] = None
    course: Optional[str] = None
    topic: Optional[str] = None
    total_score: float
    max_score: float = 100.0
    ai_total_score: Optional[float] = None
    grade_5: Optional[int] = None
    status: str = "pending"
    confirmed: bool = False
    plagiarism_score: Optional[float] = None
    ai_likelihood: Optional[float] = None
    similarity_score: Optional[float] = None
    teacher_id: Optional[str] = None
    filename: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BatchGradeError(BaseModel):
    filename: str
    error: str


class BatchGradeResponse(BaseModel):
    total: int
    graded: int
    failed: int
    results: List[GradeResponse]
    errors: List[BatchGradeError] = Field(default_factory=list)
    processing_ms: int = 0


class ConfirmRequest(BaseModel):
    teacher_id: Optional[str] = None
    comment: Optional[str] = None


class EditGradeRequest(BaseModel):
    teacher_id: Optional[str] = None
    corrected_total: Optional[float] = None
    corrected_rubric: Optional[List[RubricItem]] = None
    corrected_details: Optional[str] = None  # erkin izoh (eski API bilan moslik)
    comment: Optional[str] = None
    confirm: bool = True


class ConfirmResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    grade: Optional[GradeResponse] = None


class DetectRequest(BaseModel):
    text: str
    compare_with: Optional[List[str]] = None


class DetectResponse(BaseModel):
    plagiarism_score: float
    ai_likelihood: float
    similarity_score: Optional[float] = None
    reasons: List[str]
    flags: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Hujjatlar
# ---------------------------------------------------------------------------
class DocRequest(BaseModel):
    course_name: str
    hours: int = Field(default=60, ge=2, le=1000)
    weeks: int = Field(default=15, ge=1, le=40)
    language: str = "uz"
    level: Optional[str] = None  # bakalavr 1-kurs, magistratura ...
    doc_types: List[str] = Field(default_factory=lambda: ["syllabus", "lesson_plan", "exam_tickets", "test_questions"])
    n_tickets: int = Field(default=3, ge=1, le=30)
    n_questions: int = Field(default=10, ge=1, le=50)
    topics: Optional[List[str]] = None  # o'qituvchi o'zi mavzular ro'yxatini bersa
    export_format: Optional[str] = None  # 'docx' yoki None


class DocResponse(BaseModel):
    document_id: Optional[int] = None
    course_name: str
    syllabus: str = ""
    lesson_plan: str = ""
    exam_ticket: str = ""
    test_questions: str = ""
    structured: Dict[str, Any] = Field(default_factory=dict)
    export_path: Optional[str] = None
    download_url: Optional[str] = None
    provider: Optional[str] = None
    processing_ms: Optional[int] = None


class DocumentListItem(BaseModel):
    id: int
    doc_type: str
    course: Optional[str]
    title: Optional[str]
    export_path: Optional[str]
    download_url: Optional[str] = None
    created_by: Optional[str]
    created_at: Optional[str]


# ---------------------------------------------------------------------------
# Hisobotlar
# ---------------------------------------------------------------------------
class ReportRequest(BaseModel):
    course_name: Optional[str] = None
    group_id: Optional[str] = None  # eski nom (moslik uchun)
    group_name: Optional[str] = None
    topic: Optional[str] = None
    only_confirmed: bool = False
    export_format: Optional[str] = None  # excel | hemis | csv | None
    control_type: str = "JN"  # HEMIS nazorat turi: JN / ON / YN
    use_llm_summary: bool = False

    def resolved_group(self) -> Optional[str]:
        return self.group_name or self.group_id


class ReportResponse(BaseModel):
    summary: str
    narrative: Optional[str] = None
    analytics: Dict[str, Any]
    locked_features: List[str] = Field(default_factory=list)
    upgrade_hint: Optional[str] = None
    excel_path: Optional[str] = None
    download_url: Optional[str] = None
    hemis_download_url: Optional[str] = None
    csv_download_url: Optional[str] = None
    dean_report_url: Optional[str] = None


class StatsResponse(BaseModel):
    total_grades: int
    pending: int
    confirmed: int
    students: int
    groups: int
    documents: int
    average_score: float
    pass_rate: float
    quality_rate: float
    time_saved_hours: float
    provider: str


# ---------------------------------------------------------------------------
# Talabalar / guruhlar / mezonlar
# ---------------------------------------------------------------------------
class StudentIn(BaseModel):
    student_id: str
    full_name: Optional[str] = None
    group_name: Optional[str] = None


class StudentOut(StudentIn):
    id: int
    created_at: Optional[str] = None


class StudentImportResponse(BaseModel):
    imported: int
    updated: int
    groups: List[str]
    errors: List[str] = Field(default_factory=list)


class GroupIn(BaseModel):
    name: str
    faculty: Optional[str] = None
    course_year: Optional[int] = None


class GroupOut(GroupIn):
    id: int
    student_count: int = 0
    created_at: Optional[str] = None


class RubricTemplateIn(BaseModel):
    name: str
    course: Optional[str] = None
    description: Optional[str] = None
    items: List[RubricItem]
    is_default: bool = False


class RubricTemplateOut(RubricTemplateIn):
    id: int
    created_by: Optional[str] = None
    created_at: Optional[str] = None


class AssignmentIn(BaseModel):
    title: str
    course: Optional[str] = None
    topic: Optional[str] = None
    group_name: Optional[str] = None
    rubric_template_id: Optional[int] = None
    max_score: float = 100.0
    reference_answer: Optional[str] = None


class AssignmentOut(AssignmentIn):
    id: int
    created_by: Optional[str] = None
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Auth / audit / tizim
# ---------------------------------------------------------------------------
class UserOut(BaseModel):
    id: Optional[int] = None
    username: str
    full_name: Optional[str] = None
    role: str = "teacher"
    plan: str = "free"
    is_active: bool = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class AuditEntry(BaseModel):
    id: Optional[int] = None
    action: str
    actor: Optional[str]
    target_id: Optional[int]
    note: Optional[str]
    created_at: Optional[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    provider: str


class ConfigResponse(BaseModel):
    app_name: str
    version: str
    provider: str
    model: Optional[str] = None
    auth_required: bool
    grade_thresholds: Dict[str, float]
    minutes_per_manual_check: float
    max_upload_mb: int


# ---------------------------------------------------------------------------
# Tariflar / obuna
# ---------------------------------------------------------------------------
class UsageOut(BaseModel):
    grades_used: int = 0
    grades_limit: Optional[int] = None
    grades_remaining: Optional[int] = None
    documents_used: int = 0
    documents_limit: Optional[int] = None
    documents_remaining: Optional[int] = None
    period_start: Optional[str] = None


class SubscriptionOut(BaseModel):
    id: int
    username: str
    plan: str
    seats: int
    months: int
    amount: int
    currency: str = "so'm"
    payment_method: Optional[str] = None
    invoice_no: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    expires_at: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[str] = None


class SubscriptionStatus(BaseModel):
    username: str
    plan: str
    plan_title: str
    features: Dict[str, Any]
    limits: Dict[str, Any]
    usage: UsageOut
    subscription: Optional[SubscriptionOut] = None
    pending: Optional[SubscriptionOut] = None
    enforcement: bool = True
    demo_payments: bool = True
    is_demo_user: bool = False


class SubscriptionRequest(BaseModel):
    plan: str
    seats: int = Field(default=1, ge=1, le=100000)
    months: int = Field(default=1, ge=1, le=36)
    payment_method: Optional[str] = None
    organization: Optional[str] = None
