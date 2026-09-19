"""Baholash endpointlari: yakka/batch baholash, ro'yxat, tasdiqlash, tuzatish, halollik tekshiruvi."""
from __future__ import annotations

import time
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from .. import config
from ..db import get_session
from ..exports import write_student_feedback_docx
from ..file_parser import UnsupportedFileError, extract_text, is_zip, iter_zip_files, student_id_from_filename
from ..plagiarism_detector import analyze_text
from ..schemas import BatchGradeError, BatchGradeResponse, ConfirmRequest, ConfirmResponse, DetectRequest, DetectResponse, EditGradeRequest, GradeListItem, GradeResponse
from ..security import actor_name, get_current_user
from ..services import grading as svc

router = APIRouter(prefix="/api", tags=["grading"])


async def _read_upload(file: UploadFile) -> bytes:
    raw = await file.read()
    limit = config.settings.max_upload_mb * 1024 * 1024
    if len(raw) > limit:
        raise HTTPException(status_code=413, detail=f"Fayl juda katta (maks. {config.settings.max_upload_mb} MB)")
    return raw


@router.post("/grade", response_model=GradeResponse)
async def grade_endpoint(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    student_id: Optional[str] = Form(None),
    student_name: Optional[str] = Form(None),
    group_name: Optional[str] = Form(None),
    course: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    assignment_id: Optional[int] = Form(None),
    rubric: Optional[str] = Form(None),
    rubric_template_id: Optional[int] = Form(None),
    reference_answer: Optional[str] = Form(None),
    language: str = Form("uz"),
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """Matn yoki fayl (txt/docx/pdf) yuklang — 5 soniyada ball, asoslar va xatolar."""
    content = text or ""
    filename = None
    if file is not None and file.filename:
        raw = await _read_upload(file)
        try:
            content = extract_text(file.filename, raw) or content
        except UnsupportedFileError as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        filename = file.filename
        if not student_id:
            student_id = student_id_from_filename(file.filename)
    return await svc.grade_content(
        session, content=content, student_id=student_id, student_name=student_name, group_name=group_name, course=course, topic=topic,
        assignment_id=assignment_id, rubric_json=rubric, rubric_template_id=rubric_template_id, reference_answer=reference_answer,
        filename=filename, language=language, actor=actor_name(user),
    )


@router.post("/grade/batch", response_model=BatchGradeResponse)
async def grade_batch(
    files: List[UploadFile] = File(...),
    group_name: Optional[str] = Form(None),
    course: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    assignment_id: Optional[int] = Form(None),
    rubric: Optional[str] = Form(None),
    rubric_template_id: Optional[int] = Form(None),
    reference_answer: Optional[str] = Form(None),
    language: str = Form("uz"),
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """Bir nechta fayl yoki ZIP arxiv — har bir fayl alohida talaba ishi (student_id fayl nomidan olinadi)."""
    started = time.perf_counter()
    items: List[tuple[str, bytes]] = []
    for f in files:
        raw = await _read_upload(f)
        if is_zip(f.filename, raw):
            items.extend(iter_zip_files(raw))
        else:
            items.append((f.filename or "file.txt", raw))
    if len(items) > config.settings.max_batch_files:
        raise HTTPException(status_code=413, detail=f"Bir vaqtda maks. {config.settings.max_batch_files} ta fayl")

    results: List[GradeResponse] = []
    errors: List[BatchGradeError] = []
    for name, raw in items:
        try:
            content = extract_text(name, raw)
            res = await svc.grade_content(
                session, content=content, student_id=student_id_from_filename(name), group_name=group_name, course=course, topic=topic,
                assignment_id=assignment_id, rubric_json=rubric, rubric_template_id=rubric_template_id, reference_answer=reference_answer,
                filename=name, language=language, actor=actor_name(user),
            )
            results.append(res)
        except HTTPException as exc:
            errors.append(BatchGradeError(filename=name, error=str(exc.detail)))
        except Exception as exc:  # noqa: BLE001
            errors.append(BatchGradeError(filename=name, error=f"{exc.__class__.__name__}: {exc}"))
    return BatchGradeResponse(total=len(items), graded=len(results), failed=len(errors), results=results, errors=errors, processing_ms=int((time.perf_counter() - started) * 1000))


@router.get("/grades", response_model=List[GradeListItem])
def list_grades(
    course: Optional[str] = None, group_name: Optional[str] = None, topic: Optional[str] = None, student_id: Optional[str] = None,
    status: Optional[str] = None, only_confirmed: bool = False, limit: int = 100, offset: int = 0,
    session: Session = Depends(get_session), user=Depends(get_current_user),
):
    rows = svc.grade_rows(session, course=course, group_name=group_name, topic=topic, student_id=student_id, status=status, only_confirmed=only_confirmed, limit=min(limit, 1000), offset=offset)
    return svc.rows_to_list_items(rows)


@router.get("/grade/{grade_id}", response_model=GradeResponse)
def get_grade(grade_id: int, session: Session = Depends(get_session)):
    return svc.grade_to_response(session, svc.get_grade_or_404(session, grade_id))


@router.post("/grade/{grade_id}/confirm", response_model=ConfirmResponse)
async def confirm_grade(grade_id: int, payload: Optional[ConfirmRequest] = None, teacher_id: Optional[str] = Form(None), session: Session = Depends(get_session), user=Depends(get_current_user)):
    payload = payload or ConfirmRequest()
    grade = svc.confirm_grade(session, grade_id, payload.teacher_id or teacher_id, payload.comment, actor_name(user))
    return ConfirmResponse(success=True, message="Baho tasdiqlandi", grade=grade)


@router.post("/grade/{grade_id}/edit", response_model=ConfirmResponse)
async def edit_grade(grade_id: int, payload: EditGradeRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    grade = svc.edit_grade(session, grade_id, payload, actor_name(user))
    return ConfirmResponse(success=True, message="Baho tuzatildi va jurnalga yozildi", grade=grade)


@router.delete("/grade/{grade_id}", response_model=ConfirmResponse)
def delete_grade(grade_id: int, session: Session = Depends(get_session), user=Depends(get_current_user)):
    svc.delete_grade(session, grade_id, actor_name(user))
    return ConfirmResponse(success=True, message="Baho o'chirildi")


@router.get("/grade/{grade_id}/feedback.docx")
def grade_feedback_docx(grade_id: int, session: Session = Depends(get_session)):
    grade = svc.grade_to_response(session, svc.get_grade_or_404(session, grade_id))
    path = write_student_feedback_docx(grade.model_dump())
    return FileResponse(str(path), filename=path.name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.post("/detect", response_model=DetectResponse)
async def detect_endpoint(req: DetectRequest):
    compare = [(f"matn-{i + 1}", t) for i, t in enumerate(req.compare_with or [])] or None
    out = analyze_text(req.text, compare_with=compare)
    return DetectResponse(plagiarism_score=out["plagiarism_score"], ai_likelihood=out["ai_likelihood"], similarity_score=out.get("similarity_score"), reasons=out["reasons"], flags=out.get("flags", []))
