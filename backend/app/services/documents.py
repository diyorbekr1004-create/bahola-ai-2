"""Hujjatlar xizmati: silabus, dars rejasi, biletlar, testlar — generatsiya va saqlash."""
from __future__ import annotations

import time
from typing import Optional

from sqlmodel import Session, select

from ..db import GeneratedDocument, add_audit, dumps, loads
from ..exports import render_lesson_plan_text, render_syllabus_text, render_tests_text, render_tickets_text, write_documents_docx
from ..llm import get_llm
from ..schemas import DocRequest, DocResponse, DocumentListItem


def download_url_for(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    from pathlib import Path

    return f"/api/exports/{Path(path).name}"


async def generate_documents(session: Session, req: DocRequest, actor: Optional[str] = None) -> DocResponse:
    started = time.perf_counter()
    llm = get_llm()
    docs = await llm.generate_docs(
        req.course_name, hours=req.hours, weeks=req.weeks, language=req.language, level=req.level,
        n_tickets=req.n_tickets, n_questions=req.n_questions, topics=req.topics, doc_types=req.doc_types,
    )
    syllabus_text = render_syllabus_text(docs.get("syllabus") or {})
    lesson_text = render_lesson_plan_text(docs.get("lesson_plan") or {})
    tickets_text = render_tickets_text(docs.get("exam_tickets") or [], req.course_name)
    tests_text = render_tests_text(docs.get("test_questions") or [])

    export_path = None
    if (req.export_format or "docx").lower() == "docx":
        try:
            export_path = str(write_documents_docx(req.course_name, docs))
        except Exception:  # noqa: BLE001 - eksport xatosi generatsiyani to'xtatmasin
            export_path = None

    record = GeneratedDocument(doc_type="bundle" if len(req.doc_types) > 1 else (req.doc_types[0] if req.doc_types else "bundle"),
                               course=req.course_name, title=f"{req.course_name} — {req.weeks} hafta / {req.hours} soat",
                               content=dumps(docs), export_path=export_path, created_by=actor)
    session.add(record)
    session.commit()
    session.refresh(record)
    add_audit(session, "documents_generated", actor, record.id, f"course={req.course_name} types={','.join(req.doc_types)}")
    session.commit()

    return DocResponse(
        document_id=record.id, course_name=req.course_name, syllabus=syllabus_text, lesson_plan=lesson_text,
        exam_ticket=tickets_text, test_questions=tests_text, structured=docs, export_path=export_path,
        download_url=download_url_for(export_path), provider=docs.get("provider"), processing_ms=int((time.perf_counter() - started) * 1000),
    )


def list_documents(session: Session, course: Optional[str] = None, limit: int = 50) -> list[DocumentListItem]:
    q = select(GeneratedDocument)
    if course:
        q = q.where(GeneratedDocument.course == course)
    q = q.order_by(GeneratedDocument.created_at.desc()).limit(limit)
    return [
        DocumentListItem(id=d.id, doc_type=d.doc_type, course=d.course, title=d.title, export_path=d.export_path,
                         download_url=download_url_for(d.export_path), created_by=d.created_by,
                         created_at=d.created_at.isoformat() if d.created_at else None)
        for d in session.exec(q).all()
    ]


def document_to_response(d: GeneratedDocument) -> DocResponse:
    docs = loads(d.content, {})
    return DocResponse(
        document_id=d.id, course_name=d.course or "", syllabus=render_syllabus_text(docs.get("syllabus") or {}),
        lesson_plan=render_lesson_plan_text(docs.get("lesson_plan") or {}), exam_ticket=render_tickets_text(docs.get("exam_tickets") or [], d.course or ""),
        test_questions=render_tests_text(docs.get("test_questions") or []), structured=docs, export_path=d.export_path,
        download_url=download_url_for(d.export_path), provider=docs.get("provider"),
    )
