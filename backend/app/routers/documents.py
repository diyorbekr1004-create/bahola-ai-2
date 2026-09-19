"""Hujjatlar generatori endpointlari."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session

from ..db import GeneratedDocument, get_session
from ..schemas import DocRequest, DocResponse, DocumentListItem
from ..security import actor_name, get_current_user
from ..services import documents as svc

router = APIRouter(prefix="/api", tags=["documents"])


@router.post("/generate-docs", response_model=DocResponse)
async def generate_docs(req: DocRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    """Fan nomi -> 15 haftalik silabus, dars rejasi, imtihon biletlari va testlar (DOCX bilan)."""
    return await svc.generate_documents(session, req, actor=actor_name(user))


@router.get("/documents", response_model=List[DocumentListItem])
def list_documents(course: Optional[str] = None, limit: int = 50, session: Session = Depends(get_session), user=Depends(get_current_user)):
    return svc.list_documents(session, course=course, limit=limit)


@router.get("/documents/{document_id}", response_model=DocResponse)
def get_document(document_id: int, session: Session = Depends(get_session)):
    d = session.get(GeneratedDocument, document_id)
    if not d:
        raise HTTPException(status_code=404, detail="Hujjat topilmadi")
    return svc.document_to_response(d)


@router.get("/documents/{document_id}/download")
def download_document(document_id: int, session: Session = Depends(get_session)):
    d = session.get(GeneratedDocument, document_id)
    if not d or not d.export_path or not Path(d.export_path).is_file():
        raise HTTPException(status_code=404, detail="Eksport fayli topilmadi")
    p = Path(d.export_path)
    return FileResponse(str(p), filename=p.name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
