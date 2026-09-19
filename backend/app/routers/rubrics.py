"""Baholash mezonlari (rubrika) shablonlari va topshiriqlar."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import Assignment, RubricTemplate, dumps, get_session, loads
from ..schemas import AssignmentIn, AssignmentOut, RubricItem, RubricTemplateIn, RubricTemplateOut
from ..security import actor_name, get_current_user
from ..services.grading import default_rubric_items

router = APIRouter(prefix="/api", tags=["rubrics"])


def _tpl_out(t: RubricTemplate) -> RubricTemplateOut:
    return RubricTemplateOut(id=t.id, name=t.name, course=t.course, description=t.description, items=[RubricItem(**i) for i in loads(t.items, [])],
                             is_default=t.is_default, created_by=t.created_by, created_at=t.created_at.isoformat() if t.created_at else None)


@router.get("/rubrics/default", response_model=List[RubricItem])
def get_default_rubric():
    return default_rubric_items()


@router.get("/rubrics", response_model=List[RubricTemplateOut])
def list_rubrics(course: Optional[str] = None, session: Session = Depends(get_session), user=Depends(get_current_user)):
    q = select(RubricTemplate)
    if course:
        q = q.where((RubricTemplate.course == course) | (RubricTemplate.course == None))  # noqa: E711
    return [_tpl_out(t) for t in session.exec(q.order_by(RubricTemplate.is_default.desc(), RubricTemplate.name)).all()]


@router.post("/rubrics", response_model=RubricTemplateOut)
def create_rubric(payload: RubricTemplateIn, session: Session = Depends(get_session), user=Depends(get_current_user)):
    if not payload.items:
        raise HTTPException(status_code=422, detail="Kamida bitta mezon kerak")
    if payload.is_default:
        for t in session.exec(select(RubricTemplate).where(RubricTemplate.is_default == True)).all():  # noqa: E712
            t.is_default = False
            session.add(t)
    t = RubricTemplate(name=payload.name, course=payload.course, description=payload.description,
                       items=dumps([i.model_dump(exclude={"score", "evidence"}) for i in payload.items]), is_default=payload.is_default, created_by=actor_name(user))
    session.add(t)
    session.commit()
    session.refresh(t)
    return _tpl_out(t)


@router.delete("/rubrics/{template_id}")
def delete_rubric(template_id: int, session: Session = Depends(get_session), user=Depends(get_current_user)):
    t = session.get(RubricTemplate, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Shablon topilmadi")
    session.delete(t)
    session.commit()
    return {"success": True}


def _asg_out(a: Assignment) -> AssignmentOut:
    return AssignmentOut(id=a.id, title=a.title, course=a.course, topic=a.topic, group_name=a.group_name, rubric_template_id=a.rubric_template_id,
                         max_score=a.max_score, reference_answer=a.reference_answer, created_by=a.created_by, created_at=a.created_at.isoformat() if a.created_at else None)


@router.get("/assignments", response_model=List[AssignmentOut])
def list_assignments(course: Optional[str] = None, group_name: Optional[str] = None, session: Session = Depends(get_session), user=Depends(get_current_user)):
    q = select(Assignment)
    if course:
        q = q.where(Assignment.course == course)
    if group_name:
        q = q.where(Assignment.group_name == group_name)
    return [_asg_out(a) for a in session.exec(q.order_by(Assignment.created_at.desc())).all()]


@router.post("/assignments", response_model=AssignmentOut)
def create_assignment(payload: AssignmentIn, session: Session = Depends(get_session), user=Depends(get_current_user)):
    a = Assignment(**payload.model_dump(), created_by=actor_name(user))
    session.add(a)
    session.commit()
    session.refresh(a)
    return _asg_out(a)


@router.delete("/assignments/{assignment_id}")
def delete_assignment(assignment_id: int, session: Session = Depends(get_session), user=Depends(get_current_user)):
    a = session.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Topshiriq topilmadi")
    session.delete(a)
    session.commit()
    return {"success": True}
