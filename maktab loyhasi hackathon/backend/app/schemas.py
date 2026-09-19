from typing import List, Optional
from pydantic import BaseModel


class RubricItem(BaseModel):
    name: str
    max_score: int
    score: Optional[int] = None
    evidence: Optional[str] = None


class Feedback(BaseModel):
    summary: str
    suggestions: List[str]


class GradeResponse(BaseModel):
    total_score: int
    rubric: List[RubricItem]
    plagiarism_score: Optional[float] = None
    ai_likelihood: Optional[float] = None
    feedback: Feedback
    grade_id: Optional[int] = None
    submission_id: Optional[int] = None
    confirmed: Optional[bool] = False
    updated_at: Optional[str] = None


class GradeSummary(BaseModel):
    grade_id: int
    submission_id: int
    student_id: Optional[str]
    course: Optional[str]
    total_score: int
    confirmed: bool
    updated_at: Optional[str]


class DocRequest(BaseModel):
    course_name: str
    hours: int = 60
    weeks: int = 15
    language: Optional[str] = "uz"
    export_format: Optional[str] = None  # 'docx' or None


class DocResponse(BaseModel):
    syllabus: str
    exam_ticket: str
    export_path: Optional[str] = None


class DetectRequest(BaseModel):
    text: str


class DetectResponse(BaseModel):
    plagiarism_score: float
    ai_likelihood: float
    reasons: List[str]


class EditGradeRequest(BaseModel):
    teacher_id: str
    corrected_details: Optional[str]
    corrected_total: Optional[int]


class ConfirmResponse(BaseModel):
    success: bool
    message: Optional[str]


class AuditEntry(BaseModel):
    action: str
    actor: Optional[str]
    target_id: Optional[int]
    note: Optional[str]
    created_at: Optional[str]


class ReportRequest(BaseModel):
    course_name: str
    group_id: Optional[str] = None


class ReportResponse(BaseModel):
    summary: str
    excel_path: Optional[str] = None
