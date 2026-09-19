"""Tizim: health, config, statistika, eksport fayllarini yuklab olish, audit."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlmodel import Session, select

from .. import config
from ..analytics import compute_analytics
from ..db import AuditLog, GeneratedDocument, GradeRecord, Student, StudentGroup, engine, get_session
from ..exports import export_dir
from ..llm import provider_info
from ..schemas import AuditEntry, ConfigResponse, HealthResponse, StatsResponse
from ..security import get_current_user
from ..services.grading import grade_rows

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health():
    db_status = "ok"
    try:
        with Session(engine) as s:
            s.exec(select(GradeRecord.id).limit(1)).first()
    except Exception as exc:  # noqa: BLE001
        db_status = f"error: {exc.__class__.__name__}"
    return HealthResponse(status="ok" if db_status == "ok" else "degraded", version=config.settings.app_version, database=db_status, provider=provider_info()["provider"])


@router.get("/config", response_model=ConfigResponse)
def get_config():
    s = config.settings
    info = provider_info()
    return ConfigResponse(
        app_name=s.app_name, version=s.app_version, provider=info["provider"], model=info["model"], auth_required=s.auth_required,
        grade_thresholds={str(k): v for k, v in s.grade_thresholds.items()}, minutes_per_manual_check=s.minutes_per_manual_check, max_upload_mb=s.max_upload_mb,
    )


@router.get("/stats", response_model=StatsResponse)
def stats(session: Session = Depends(get_session), user=Depends(get_current_user)):
    rows = grade_rows(session)
    a = compute_analytics(rows)
    return StatsResponse(
        total_grades=a["total_grades"], pending=a["pending_count"], confirmed=a["confirmed_count"],
        students=session.exec(select(func.count(Student.id))).one(), groups=session.exec(select(func.count(StudentGroup.id))).one(),
        documents=session.exec(select(func.count(GeneratedDocument.id))).one(), average_score=a["average_score"], pass_rate=a["pass_rate"],
        quality_rate=a["quality_rate"], time_saved_hours=a["time_saved_hours"], provider=provider_info()["provider"],
    )


@router.get("/audit", response_model=List[AuditEntry])
def get_audit_logs(limit: int = 50, action: Optional[str] = None, session: Session = Depends(get_session), user=Depends(get_current_user)):
    q = select(AuditLog)
    if action:
        q = q.where(AuditLog.action == action)
    q = q.order_by(AuditLog.created_at.desc()).limit(min(limit, 500))
    return [AuditEntry(id=a.id, action=a.action, actor=a.actor, target_id=a.target_id, note=a.note, created_at=a.created_at.isoformat() if a.created_at else None) for a in session.exec(q).all()]


@router.get("/exports/{filename}")
def download_export(filename: str):
    """`exports/` papkasidagi faylni yuklab olish (path traversal himoyasi bilan)."""
    base = export_dir().resolve()
    target = (base / Path(filename).name).resolve()
    if target.parent != base or not target.is_file():
        raise HTTPException(status_code=404, detail="Fayl topilmadi")
    media = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".csv": "text/csv",
    }.get(target.suffix.lower(), "application/octet-stream")
    return FileResponse(str(target), media_type=media, filename=target.name)


@router.get("/exports", response_model=List[dict])
def list_exports(limit: int = 50, user=Depends(get_current_user)):
    files = sorted(export_dir().glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    return [{"filename": p.name, "size": p.stat().st_size, "download_url": f"/api/exports/{p.name}"} for p in files]
