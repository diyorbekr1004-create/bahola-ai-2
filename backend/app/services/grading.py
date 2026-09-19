"""Baholash xizmati: rubrika, LLM, halollik tekshiruvi, saqlash, HITL amallari."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import HTTPException
from sqlmodel import Session, select

from .. import config
from ..analytics import score_to_grade5
from ..db import Assignment, GradeRecord, RubricTemplate, Student, Submission, add_audit, dumps, loads, upsert_student, utcnow
from ..file_parser import word_count
from ..llm import get_llm
from ..schemas import EditGradeRequest, Feedback, GradeListItem, GradeResponse, IntegrityReport, RubricItem

FALLBACK_RUBRIC: List[Dict[str, Any]] = [
    {"name": "Dolzarblik va mavzuga moslik", "max_score": 20, "description": "Mavzu to'g'ri tushunilgan, maqsad aniq."},
    {"name": "Dalillar va tahlil", "max_score": 30, "description": "Fikrlar misol, raqam va manbalar bilan asoslangan."},
    {"name": "Tuzilma va mantiqiy izchillik", "max_score": 20, "description": "Kirish, asosiy qism, xulosa; fikrlar ketma-ket."},
    {"name": "Til va uslub", "max_score": 15, "description": "Savodxonlik, terminlar, jumla tuzilishi."},
    {"name": "Xulosa", "max_score": 15, "description": "Asosiy natijalar umumlashtirilgan."},
]


def default_rubric_items() -> List[RubricItem]:
    """`prompts/templates.json` dagi `rubric_default` yoki ichki fallback."""
    path = Path(config.settings.project_root) / "prompts" / "templates.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("rubric_default")
        if isinstance(items, list) and items:
            return [RubricItem(**it) for it in items]
    except (OSError, ValueError, TypeError):
        pass
    return [RubricItem(**it) for it in FALLBACK_RUBRIC]


def parse_rubric_json(raw: Optional[str]) -> Optional[List[RubricItem]]:
    if not raw or not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"rubric JSON noto'g'ri: {exc}") from exc
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if not isinstance(data, list) or not data:
        raise HTTPException(status_code=422, detail="rubric bo'sh ro'yxat bo'lishi mumkin emas")
    items = []
    for it in data:
        try:
            items.append(RubricItem(name=str(it["name"]), max_score=float(it.get("max_score", 10)), description=it.get("description")))
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"rubric elementi noto'g'ri: {it}") from exc
    return items


def resolve_rubric(session: Session, rubric_json: Optional[str] = None, rubric_template_id: Optional[int] = None, assignment: Optional[Assignment] = None) -> Tuple[List[RubricItem], Optional[str]]:
    """Ustuvorlik: so'rovdagi JSON > shablon ID > topshiriq shabloni > default shablon > fallback."""
    items = parse_rubric_json(rubric_json)
    if items:
        return items, "request"
    tid = rubric_template_id or (assignment.rubric_template_id if assignment else None)
    if tid:
        tpl = session.get(RubricTemplate, tid)
        if tpl:
            return [RubricItem(**it) for it in loads(tpl.items, [])], f"template:{tpl.id}"
    tpl = session.exec(select(RubricTemplate).where(RubricTemplate.is_default == True)).first()  # noqa: E712
    if tpl:
        return [RubricItem(**it) for it in loads(tpl.items, [])], f"template:{tpl.id}"
    return default_rubric_items(), "default"


def _comparison_set(session: Session, *, course: Optional[str], topic: Optional[str], group_name: Optional[str], student_id: str, limit: int = 150) -> List[Tuple[str, str]]:
    """Guruh ichidagi o'xshashlik uchun: shu fan/mavzudagi boshqa talabalar ishlari."""
    q = select(Submission).where(Submission.student_id != student_id)
    if topic:
        q = q.where(Submission.topic == topic)
    elif course:
        q = q.where(Submission.course == course)
    elif group_name:
        q = q.where(Submission.group_name == group_name)
    else:
        return []
    q = q.order_by(Submission.created_at.desc()).limit(limit)
    return [(s.student_id, s.content or "") for s in session.exec(q).all() if s.content]


def _grade_from_rubric(items: Sequence[RubricItem]) -> Tuple[float, float]:
    total = sum(float(i.score or 0) for i in items)
    max_total = sum(float(i.max_score) for i in items) or 100.0
    return round(total, 2), round(max_total, 2)


async def grade_content(
    session: Session,
    *,
    content: str,
    student_id: Optional[str] = None,
    student_name: Optional[str] = None,
    group_name: Optional[str] = None,
    course: Optional[str] = None,
    topic: Optional[str] = None,
    assignment_id: Optional[int] = None,
    rubric_json: Optional[str] = None,
    rubric_template_id: Optional[int] = None,
    reference_answer: Optional[str] = None,
    filename: Optional[str] = None,
    language: str = "uz",
    actor: Optional[str] = None,
) -> GradeResponse:
    content = (content or "").strip()
    if not content:
        raise HTTPException(status_code=422, detail="Baholash uchun matn bo'sh")
    started = time.perf_counter()

    assignment = session.get(Assignment, assignment_id) if assignment_id else None
    if assignment:
        course = course or assignment.course
        topic = topic or assignment.topic or assignment.title
        group_name = group_name or assignment.group_name
        reference_answer = reference_answer or assignment.reference_answer

    rubric, rubric_source = resolve_rubric(session, rubric_json, rubric_template_id, assignment)
    student_id = (student_id or "").strip() or "unknown"
    group_name = (group_name or "").strip() or None
    course = (course or "").strip() or None
    topic = (topic or "").strip() or None

    student = upsert_student(session, student_id, full_name=student_name, group_name=group_name)
    if student and not student_name:
        student_name = student.full_name
    if student and not group_name:
        group_name = student.group_name

    compare_with = _comparison_set(session, course=course, topic=topic, group_name=group_name, student_id=student_id)
    llm = get_llm()
    result = await llm.grade_submission(content, rubric, reference_answer=reference_answer, topic=topic, course=course, language=language, compare_with=compare_with)

    scored: List[RubricItem] = [r if isinstance(r, RubricItem) else RubricItem(**r) for r in result["rubric"]]
    total, max_total = _grade_from_rubric(scored)
    integrity = result.get("integrity") or {}
    feedback = Feedback(**(result.get("feedback") or {}))
    processing_ms = int((time.perf_counter() - started) * 1000)

    sub = Submission(student_id=student_id, group_name=group_name, course=course, topic=topic, assignment_id=assignment.id if assignment else None,
                     content=content, filename=filename, word_count=word_count(content))
    session.add(sub)
    session.commit()
    session.refresh(sub)

    details = {
        "rubric": [r.model_dump() for r in scored],
        "feedback": feedback.model_dump(),
        "integrity": integrity,
        "features": result.get("features"),
        "model": result.get("model"),
        "rubric_source": rubric_source,
        "reference_used": bool(reference_answer),
        "fallback_reason": result.get("fallback_reason"),
    }
    gr = GradeRecord(
        submission_id=sub.id, total_score=total, max_score=max_total, ai_total_score=total, details=dumps(details),
        feedback_summary=feedback.summary, plagiarism_score=integrity.get("plagiarism_score"), ai_likelihood=integrity.get("ai_likelihood"),
        similarity_score=integrity.get("similarity_score"), similar_to_student=integrity.get("similar_to"),
        status="pending", confirmed=False, processing_ms=processing_ms, provider=result.get("provider"),
    )
    session.add(gr)
    session.commit()
    session.refresh(gr)
    add_audit(session, "grade_autogenerated", actor, gr.id, f"student={student_id} score={total}/{max_total} provider={gr.provider} flags={','.join(integrity.get('flags', []))}")
    session.commit()
    return grade_to_response(session, gr, sub, student)


def grade_to_response(session: Session, gr: GradeRecord, sub: Optional[Submission] = None, student: Optional[Student] = None) -> GradeResponse:
    sub = sub or session.get(Submission, gr.submission_id)
    if student is None and sub is not None:
        student = session.exec(select(Student).where(Student.student_id == sub.student_id)).first()
    details = loads(gr.details, {})
    corrected = loads(gr.corrected_details, {}) if gr.corrected_details else {}
    rubric_raw = corrected.get("rubric") or details.get("rubric") or []
    rubric = []
    for r in rubric_raw:
        try:
            rubric.append(RubricItem(**r))
        except (TypeError, ValueError):
            continue
    integrity_raw = details.get("integrity") or {}
    integrity = IntegrityReport(
        plagiarism_score=gr.plagiarism_score, ai_likelihood=gr.ai_likelihood, similarity_score=gr.similarity_score,
        similar_to_student=gr.similar_to_student, reasons=integrity_raw.get("reasons") or [], flags=integrity_raw.get("flags") or [],
    )
    fb_raw = details.get("feedback") or {"summary": gr.feedback_summary or "", "suggestions": []}
    content = (sub.content if sub else "") or ""
    return GradeResponse(
        grade_id=gr.id, submission_id=gr.submission_id, student_id=sub.student_id if sub else None,
        student_name=student.full_name if student else None, group_name=(sub.group_name if sub else None) or (student.group_name if student else None),
        course=sub.course if sub else None, topic=sub.topic if sub else None,
        total_score=gr.total_score, max_score=gr.max_score or 100.0, ai_total_score=gr.ai_total_score,
        grade_5=score_to_grade5(gr.total_score, gr.max_score or 100.0), rubric=rubric, feedback=Feedback(**fb_raw), integrity=integrity,
        plagiarism_score=gr.plagiarism_score, ai_likelihood=gr.ai_likelihood, status=gr.status, confirmed=bool(gr.confirmed),
        teacher_id=gr.teacher_id, teacher_comment=gr.teacher_comment, provider=gr.provider, processing_ms=gr.processing_ms,
        word_count=sub.word_count if sub else None, filename=sub.filename if sub else None,
        content_preview=content[:400] + ("…" if len(content) > 400 else ""),
        created_at=gr.created_at.isoformat() if gr.created_at else None, updated_at=gr.updated_at.isoformat() if gr.updated_at else None,
    )


def get_grade_or_404(session: Session, grade_id: int) -> GradeRecord:
    gr = session.get(GradeRecord, grade_id)
    if not gr:
        raise HTTPException(status_code=404, detail="Baho topilmadi")
    return gr


def confirm_grade(session: Session, grade_id: int, teacher_id: Optional[str], comment: Optional[str], actor: Optional[str]) -> GradeResponse:
    gr = get_grade_or_404(session, grade_id)
    gr.confirmed = True
    gr.status = "confirmed" if gr.status != "edited" else "edited"
    gr.teacher_id = teacher_id or actor
    if comment:
        gr.teacher_comment = comment
    gr.updated_at = utcnow()
    session.add(gr)
    add_audit(session, "grade_confirmed", gr.teacher_id, gr.id, comment or "O'qituvchi bahoni tasdiqladi")
    session.commit()
    session.refresh(gr)
    return grade_to_response(session, gr)


def edit_grade(session: Session, grade_id: int, payload: EditGradeRequest, actor: Optional[str]) -> GradeResponse:
    gr = get_grade_or_404(session, grade_id)
    before = gr.total_score
    corrected: Dict[str, Any] = loads(gr.corrected_details, {}) if gr.corrected_details else {}
    if payload.corrected_rubric:
        items = [RubricItem(name=i.name, max_score=i.max_score, score=min(float(i.score or 0), float(i.max_score)), evidence=i.evidence, description=i.description) for i in payload.corrected_rubric]
        corrected["rubric"] = [i.model_dump() for i in items]
        total, max_total = _grade_from_rubric(items)
        gr.total_score, gr.max_score = total, max_total
    if payload.corrected_total is not None:
        gr.total_score = max(0.0, min(float(payload.corrected_total), float(gr.max_score or 100)))
    if payload.corrected_details:
        corrected["note"] = payload.corrected_details
    if payload.comment:
        gr.teacher_comment = payload.comment
    gr.corrected_details = dumps(corrected) if corrected else gr.corrected_details
    gr.teacher_id = payload.teacher_id or actor
    gr.status = "edited"
    gr.confirmed = bool(payload.confirm)
    gr.updated_at = utcnow()
    session.add(gr)
    add_audit(session, "grade_edited", gr.teacher_id, gr.id, f"{before} -> {gr.total_score}; {payload.comment or payload.corrected_details or ''}")
    session.commit()
    session.refresh(gr)
    return grade_to_response(session, gr)


def delete_grade(session: Session, grade_id: int, actor: Optional[str]) -> None:
    gr = get_grade_or_404(session, grade_id)
    sub = session.get(Submission, gr.submission_id)
    session.delete(gr)
    if sub:
        session.delete(sub)
    add_audit(session, "grade_deleted", actor, grade_id, None)
    session.commit()


def grade_rows(
    session: Session,
    *,
    course: Optional[str] = None,
    group_name: Optional[str] = None,
    topic: Optional[str] = None,
    student_id: Optional[str] = None,
    status: Optional[str] = None,
    only_confirmed: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Analitika/eksport/ro'yxat uchun tekis (flat) qatorlar."""
    q = select(GradeRecord, Submission).where(GradeRecord.submission_id == Submission.id)
    if course:
        q = q.where(Submission.course == course)
    if group_name:
        q = q.where(Submission.group_name == group_name)
    if topic:
        q = q.where(Submission.topic == topic)
    if student_id:
        q = q.where(Submission.student_id == student_id)
    if status:
        q = q.where(GradeRecord.status == status)
    if only_confirmed:
        q = q.where(GradeRecord.confirmed == True)  # noqa: E712
    q = q.order_by(GradeRecord.created_at.desc())
    if offset:
        q = q.offset(offset)
    if limit:
        q = q.limit(limit)
    pairs = session.exec(q).all()
    names = {s.student_id: s.full_name for s in session.exec(select(Student)).all()}
    rows: List[Dict[str, Any]] = []
    for gr, sub in pairs:
        details = loads(gr.details, {})
        corrected = loads(gr.corrected_details, {}) if gr.corrected_details else {}
        rows.append({
            "grade_id": gr.id, "submission_id": sub.id, "student_id": sub.student_id, "student_name": names.get(sub.student_id),
            "group_name": sub.group_name, "course": sub.course, "topic": sub.topic, "total_score": gr.total_score, "max_score": gr.max_score or 100.0,
            "ai_total_score": gr.ai_total_score, "grade_5": score_to_grade5(gr.total_score, gr.max_score or 100.0),
            "rubric": corrected.get("rubric") or details.get("rubric") or [], "feedback_summary": gr.feedback_summary,
            "status": gr.status, "confirmed": bool(gr.confirmed), "teacher_id": gr.teacher_id, "plagiarism_score": gr.plagiarism_score,
            "ai_likelihood": gr.ai_likelihood, "similarity_score": gr.similarity_score, "filename": sub.filename,
            "created_at": gr.created_at.isoformat() if gr.created_at else None, "updated_at": gr.updated_at.isoformat() if gr.updated_at else None,
        })
    return rows


def rows_to_list_items(rows: List[Dict[str, Any]]) -> List[GradeListItem]:
    return [GradeListItem(**{k: v for k, v in r.items() if k in GradeListItem.model_fields}) for r in rows]
