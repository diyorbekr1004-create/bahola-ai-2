"""Talabalar va guruhlar: ro'yxat, qo'shish, Excel/CSV import."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlmodel import Session, select

from ..db import Student, StudentGroup, add_audit, get_session, upsert_group, upsert_student
from ..file_parser import parse_student_list
from ..schemas import GroupIn, GroupOut, StudentImportResponse, StudentIn, StudentOut
from ..security import actor_name, get_current_user

router = APIRouter(prefix="/api", tags=["students"])


def _student_out(s: Student) -> StudentOut:
    return StudentOut(id=s.id, student_id=s.student_id, full_name=s.full_name, group_name=s.group_name, created_at=s.created_at.isoformat() if s.created_at else None)


@router.get("/students", response_model=List[StudentOut])
def list_students(group_name: Optional[str] = None, q: Optional[str] = None, limit: int = 500, session: Session = Depends(get_session), user=Depends(get_current_user)):
    query = select(Student)
    if group_name:
        query = query.where(Student.group_name == group_name)
    if q:
        like = f"%{q}%"
        query = query.where((Student.full_name.ilike(like)) | (Student.student_id.ilike(like)))  # type: ignore[union-attr]
    query = query.order_by(Student.group_name, Student.full_name).limit(min(limit, 5000))
    return [_student_out(s) for s in session.exec(query).all()]


@router.post("/students", response_model=StudentOut)
def create_student(payload: StudentIn, session: Session = Depends(get_session), user=Depends(get_current_user)):
    st = upsert_student(session, payload.student_id, full_name=payload.full_name, group_name=payload.group_name)
    if st is None:
        raise HTTPException(status_code=422, detail="student_id bo'sh bo'lishi mumkin emas")
    session.commit()
    session.refresh(st)
    return _student_out(st)


@router.delete("/students/{student_pk}")
def delete_student(student_pk: int, session: Session = Depends(get_session), user=Depends(get_current_user)):
    st = session.get(Student, student_pk)
    if not st:
        raise HTTPException(status_code=404, detail="Talaba topilmadi")
    session.delete(st)
    session.commit()
    return {"success": True}


@router.post("/students/import", response_model=StudentImportResponse)
async def import_students(file: UploadFile = File(...), group_name: Optional[str] = None, session: Session = Depends(get_session), user=Depends(get_current_user)):
    """XLSX/CSV: ustunlar `student_id`/`HEMIS ID`, `F.I.Sh.`/`full_name`, `Guruh`/`group`."""
    raw = await file.read()
    try:
        rows = parse_student_list(file.filename, raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Faylni o'qib bo'lmadi: {exc}") from exc
    imported = updated = 0
    groups: set[str] = set()
    errors: List[str] = []
    existing_ids = {s.student_id for s in session.exec(select(Student)).all()}
    for r in rows:
        sid = r.get("student_id")
        if not sid:
            errors.append(f"ID yo'q: {r}")
            continue
        g = r.get("group_name") or group_name
        upsert_student(session, sid, full_name=r.get("full_name"), group_name=g)
        if g:
            groups.add(g)
        if sid in existing_ids:
            updated += 1
        else:
            imported += 1
            existing_ids.add(sid)
    add_audit(session, "students_imported", actor_name(user), None, f"file={file.filename} imported={imported} updated={updated}")
    session.commit()
    return StudentImportResponse(imported=imported, updated=updated, groups=sorted(groups), errors=errors[:20])


@router.get("/groups", response_model=List[GroupOut])
def list_groups(session: Session = Depends(get_session), user=Depends(get_current_user)):
    counts = dict(session.exec(select(Student.group_name, func.count(Student.id)).group_by(Student.group_name)).all())
    groups = session.exec(select(StudentGroup).order_by(StudentGroup.name)).all()
    known = {g.name for g in groups}
    out = [GroupOut(id=g.id, name=g.name, faculty=g.faculty, course_year=g.course_year, student_count=counts.get(g.name, 0), created_at=g.created_at.isoformat() if g.created_at else None) for g in groups]
    # Guruh jadvalida yo'q, lekin talabalarda uchraydigan guruhlar
    for name, cnt in counts.items():
        if name and name not in known:
            out.append(GroupOut(id=0, name=name, student_count=cnt))
    return out


@router.post("/groups", response_model=GroupOut)
def create_group(payload: GroupIn, session: Session = Depends(get_session), user=Depends(get_current_user)):
    g = upsert_group(session, payload.name, faculty=payload.faculty, course_year=payload.course_year)
    if g is None:
        raise HTTPException(status_code=422, detail="Guruh nomi bo'sh")
    session.commit()
    session.refresh(g)
    return GroupOut(id=g.id, name=g.name, faculty=g.faculty, course_year=g.course_year, created_at=g.created_at.isoformat() if g.created_at else None)
