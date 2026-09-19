"""Tariflar, obuna, to'lov so'rovlari va raqobat ma'lumotlari."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from .. import plans
from ..db import Subscription, get_session
from ..schemas import SubscriptionOut, SubscriptionRequest, SubscriptionStatus
from ..security import get_current_user, require_role
from ..services import billing

router = APIRouter(prefix="/api", tags=["billing"])


@router.get("/plans")
def list_plans():
    data = plans.load_pricing()
    return {"currency": data.get("currency", "so'm"), "plans": data["plans"], "addons": data.get("addons", []), "payment_methods": data.get("payment_methods", [])}


@router.get("/competitors")
def competitors():
    data = plans.load_pricing()
    return {"competitors": data.get("competitors", {"columns": [], "rows": []}), "advantages": data.get("advantages", [])}


@router.get("/subscription", response_model=SubscriptionStatus)
def my_subscription(session: Session = Depends(get_session), user=Depends(get_current_user)):
    return billing.status_for(session, user)


@router.post("/subscription", response_model=SubscriptionStatus)
def request_subscription(payload: SubscriptionRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    """Tarif tanlash: to'lov so'rovi (hisob-faktura) yaratiladi; to'lov tasdiqlangach tarif faollashadi."""
    billing.create_subscription(session, user, payload.plan, payload.seats, payload.months, payload.payment_method, payload.organization)
    return billing.status_for(session, user)


@router.post("/subscription/{sub_id}/confirm", response_model=SubscriptionStatus)
def confirm_subscription(sub_id: int, session: Session = Depends(get_session), user=Depends(get_current_user)):
    """To'lovni tasdiqlash (demo rejimda egasi, aks holda faqat admin)."""
    sub = billing.confirm_subscription(session, sub_id, user)
    owner = session.exec(select(Subscription).where(Subscription.id == sub.id)).first()
    from ..db import User

    target = session.exec(select(User).where(User.username == owner.username)).first() or user
    return billing.status_for(session, target)


@router.post("/subscription/cancel", response_model=SubscriptionStatus)
def cancel_subscription(session: Session = Depends(get_session), user=Depends(get_current_user)):
    billing.cancel_subscription(session, user)
    from ..db import User

    target = session.get(User, user.id) if user.id else user
    return billing.status_for(session, target)


@router.get("/subscriptions", response_model=List[SubscriptionOut])
def list_subscriptions(status: str | None = None, session: Session = Depends(get_session), user=Depends(require_role("admin"))):
    q = select(Subscription)
    if status:
        q = q.where(Subscription.status == status)
    return [billing.to_out(s) for s in session.exec(q.order_by(Subscription.created_at.desc())).all()]
