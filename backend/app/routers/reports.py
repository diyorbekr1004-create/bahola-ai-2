"""Hisobotlar va eksportlar (Excel / HEMIS / CSV / dekanat DOCX)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session

from ..db import get_session
from ..schemas import ReportRequest, ReportResponse
from ..security import actor_name, get_current_user
from ..services import billing, reports as svc

router = APIRouter(prefix="/api", tags=["reports"])

MEDIA = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".csv": "text/csv",
}


@router.post("/reports", response_model=ReportResponse)
async def reports(req: ReportRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    """Guruh ko'rsatkichlari, qiyin mavzular, xavf guruhi, tahliliy xulosa va eksport havolalari."""
    return await svc.build_report(session, req, actor=actor_name(user), hemis_allowed=billing.has_feature(user, "hemis_export"))


@router.get("/reports/export")
def export_report(
    format: str = "excel", course: Optional[str] = None, group_name: Optional[str] = None, topic: Optional[str] = None,
    only_confirmed: bool = False, control_type: str = "JN", session: Session = Depends(get_session), user=Depends(get_current_user),
):
    """Faylni to'g'ridan-to'g'ri yuklab olish: format = excel | hemis | csv | dean."""
    if (format or "excel").lower() in ("hemis", "csv", "dean", "docx"):
        billing.require_feature(user, "hemis_export", "HEMIS / CSV / dekanat eksporti")
    path = svc.export_file(session, fmt=format, course=course, group=group_name, topic=topic, only_confirmed=only_confirmed, control_type=control_type, actor=actor_name(user))
    return FileResponse(str(path), filename=path.name, media_type=MEDIA.get(path.suffix.lower(), "application/octet-stream"))
