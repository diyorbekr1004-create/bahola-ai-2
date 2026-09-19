"""Hisobot xizmati: analitika + eksportlar + tahliliy xulosa."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlmodel import Session

from ..analytics import build_narrative, compute_analytics, short_summary
from ..db import add_audit
from ..exports import write_dean_report_docx, write_grades_excel, write_hemis_csv, write_hemis_excel
from ..llm import get_llm
from ..schemas import ReportRequest, ReportResponse
from .grading import grade_rows


def _url(path: Optional[Path | str]) -> Optional[str]:
    return f"/api/exports/{Path(path).name}" if path else None


async def build_report(session: Session, req: ReportRequest, actor: Optional[str] = None) -> ReportResponse:
    group = req.resolved_group()
    rows = grade_rows(session, course=req.course_name, group_name=group, topic=req.topic, only_confirmed=req.only_confirmed)
    analytics = compute_analytics(rows)
    analytics["filters"] = {"course": req.course_name, "group": group, "topic": req.topic, "only_confirmed": req.only_confirmed}

    if req.use_llm_summary:
        narrative = await get_llm().generate_report_summary(analytics, req.course_name, group)
    else:
        narrative = build_narrative(analytics, course=req.course_name, group=group)
    summary = short_summary(analytics, req.course_name, group)

    excel_path = hemis_path = csv_path = dean_path = None
    if rows:
        fmt = (req.export_format or "").lower()
        try:
            if fmt in ("", "excel", "all"):
                excel_path = write_grades_excel(rows, analytics, course_name=req.course_name, group_id=group)
            if fmt in ("hemis", "all"):
                hemis_path = write_hemis_excel(rows, course=req.course_name, group=group, control_type=req.control_type)
            if fmt in ("csv", "all"):
                csv_path = write_hemis_csv(rows, course=req.course_name, group=group, control_type=req.control_type)
            if fmt in ("dean", "all", "docx"):
                dean_path = write_dean_report_docx(analytics, narrative, req.course_name, group)
        except Exception:  # noqa: BLE001 - eksport xatosi hisobotni to'xtatmasin
            pass
        add_audit(session, "report_generated", actor, None, f"course={req.course_name} group={group} rows={len(rows)} format={fmt or 'excel'}")
        session.commit()

    return ReportResponse(
        summary=summary, narrative=narrative, analytics=analytics,
        excel_path=str(excel_path) if excel_path else None, download_url=_url(excel_path),
        hemis_download_url=_url(hemis_path), csv_download_url=_url(csv_path), dean_report_url=_url(dean_path),
    )


def export_file(session: Session, *, fmt: str, course: Optional[str], group: Optional[str], topic: Optional[str], only_confirmed: bool, control_type: str, actor: Optional[str]) -> Path:
    rows = grade_rows(session, course=course, group_name=group, topic=topic, only_confirmed=only_confirmed)
    if not rows:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Eksport uchun baholar topilmadi")
    fmt = (fmt or "excel").lower()
    if fmt == "hemis":
        path = write_hemis_excel(rows, course=course, group=group, control_type=control_type)
    elif fmt == "csv":
        path = write_hemis_csv(rows, course=course, group=group, control_type=control_type)
    elif fmt in ("dean", "docx"):
        analytics = compute_analytics(rows)
        path = write_dean_report_docx(analytics, build_narrative(analytics, course=course, group=group), course, group)
    else:
        path = write_grades_excel(rows, compute_analytics(rows), course_name=course, group_id=group)
    add_audit(session, "export_created", actor, None, f"format={fmt} course={course} group={group} rows={len(rows)}")
    session.commit()
    return Path(path)
