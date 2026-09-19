"""Tariflar, limitlar, obuna va to'lov so'rovlari."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from .. import config, plans
from ..db import GeneratedDocument, GradeRecord, Subscription, User, add_audit, utcnow
from ..llm import get_llm
from ..llm_adapter import MockLLMAdapter
from ..schemas import SubscriptionOut, SubscriptionStatus, UsageOut

PAYMENT_REQUIRED = 402


def month_start(now: Optional[datetime] = None) -> datetime:
    now = now or utcnow()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def plan_for(user: Optional[User]) -> Dict[str, Any]:
    """Tizimga kirmagan (demo) foydalanuvchi -> DEFAULT_PLAN; ro'yxatdan o'tgan foydalanuvchi -> o'z tarifi (bo'sh bo'lsa free)."""
    if user is None or getattr(user, "id", None) is None:
        return plans.get_plan(config.settings.default_plan)
    return plans.get_plan(getattr(user, "plan", None) or "free")


def usage_for(session: Session, username: str) -> UsageOut:
    start = month_start()
    grades = session.exec(select(func.count(GradeRecord.id)).where(GradeRecord.created_by == username, GradeRecord.created_at >= start)).one()
    docs = session.exec(select(func.count(GeneratedDocument.id)).where(GeneratedDocument.created_by == username, GeneratedDocument.created_at >= start)).one()
    return UsageOut(grades_used=int(grades), documents_used=int(docs), period_start=start.isoformat())


def status_for(session: Session, user: User) -> SubscriptionStatus:
    plan = plan_for(user)
    usage = usage_for(session, user.username)
    g_limit, d_limit = plans.limit(plan, "grades_per_month"), plans.limit(plan, "documents_per_month")
    usage.grades_limit = g_limit
    usage.documents_limit = d_limit
    usage.grades_remaining = None if g_limit is None else max(0, g_limit - usage.grades_used)
    usage.documents_remaining = None if d_limit is None else max(0, d_limit - usage.documents_used)
    active = session.exec(select(Subscription).where(Subscription.username == user.username, Subscription.status == "active").order_by(Subscription.created_at.desc())).first()
    pending = session.exec(select(Subscription).where(Subscription.username == user.username, Subscription.status == "pending").order_by(Subscription.created_at.desc())).first()
    return SubscriptionStatus(
        username=user.username, plan=plan["name"], plan_title=plan.get("title", plan["name"]), features=plan.get("features") or {}, limits=plan.get("limits") or {},
        usage=usage, subscription=to_out(active) if active else None, pending=to_out(pending) if pending else None,
        enforcement=config.settings.plan_enforcement, demo_payments=config.settings.demo_payments, is_demo_user=user.id is None,
    )


def _upgrade_msg(plan: Dict[str, Any], what: str) -> str:
    return f"{what} «{plan.get('title', plan['name'])}» tarifiga kirmaydi. «Tariflar» bo'limida Pro yoki Kafedra tarifiga o'ting."


def check_quota(session: Session, user: User, count: int = 1) -> None:
    """Oylik tekshirish limiti (402 Payment Required)."""
    if not config.settings.plan_enforcement:
        return
    plan = plan_for(user)
    limit = plans.limit(plan, "grades_per_month")
    if limit is None:
        return
    used = usage_for(session, user.username).grades_used
    if used + count > limit:
        raise HTTPException(status_code=PAYMENT_REQUIRED, detail=f"«{plan.get('title')}» tarifida oyiga {limit} ta ish tekshiriladi ({used} ta ishlatildi, so'ralgan: {count}). «Tariflar» bo'limida Pro tarifiga o'ting — cheksiz tekshirish.")


def check_document_quota(session: Session, user: User) -> None:
    if not config.settings.plan_enforcement:
        return
    plan = plan_for(user)
    limit = plans.limit(plan, "documents_per_month")
    if limit is None:
        return
    used = usage_for(session, user.username).documents_used
    if used + 1 > limit:
        raise HTTPException(status_code=PAYMENT_REQUIRED, detail=f"«{plan.get('title')}» tarifida oyiga {limit} ta hujjat to'plami yaratiladi ({used} ta ishlatildi). Pro tarifida cheksiz.")


def require_feature(user: User, key: str, what: str) -> None:
    if not config.settings.plan_enforcement:
        return
    plan = plan_for(user)
    if not plans.feature(plan, key):
        raise HTTPException(status_code=PAYMENT_REQUIRED, detail=_upgrade_msg(plan, what))


def has_feature(user: User, key: str) -> bool:
    if not config.settings.plan_enforcement:
        return True
    return bool(plans.feature(plan_for(user), key))


def llm_for(user: User):
    """Tarif LLM'ga ruxsat bermasa — oflayn evristika (xarajat nazorati)."""
    return get_llm() if has_feature(user, "llm") else MockLLMAdapter()


def to_out(sub: Subscription) -> SubscriptionOut:
    return SubscriptionOut(
        id=sub.id, username=sub.username, plan=sub.plan, seats=sub.seats, months=sub.months, amount=sub.amount, currency=sub.currency,
        payment_method=sub.payment_method, invoice_no=sub.invoice_no, status=sub.status,
        started_at=sub.started_at.isoformat() if sub.started_at else None, expires_at=sub.expires_at.isoformat() if sub.expires_at else None,
        note=sub.note, created_at=sub.created_at.isoformat() if sub.created_at else None,
    )


def create_subscription(session: Session, user: User, plan_name: str, seats: int, months: int, payment_method: Optional[str], organization: Optional[str]) -> Subscription:
    if user.id is None:
        raise HTTPException(status_code=400, detail="Tarifni o'zgartirish uchun tizimga kiring (masalan, teacher / teacher123).")
    if plan_name not in plans.plan_names():
        raise HTTPException(status_code=422, detail=f"Noma'lum tarif: {plan_name}")
    plan = plans.get_plan(plan_name)
    if plan_name == "free":
        return cancel_subscription(session, user)
    seats = max(int(plan.get("min_seats", 1)), seats)
    methods = plans.load_pricing().get("payment_methods") or []
    if payment_method and methods and payment_method not in methods:
        raise HTTPException(status_code=422, detail=f"To'lov usuli: {', '.join(methods)}")
    # eski kutilayotgan so'rovlarni bekor qilamiz
    for old in session.exec(select(Subscription).where(Subscription.username == user.username, Subscription.status == "pending")).all():
        old.status = "cancelled"
        old.updated_at = utcnow()
        session.add(old)
    sub = Subscription(
        username=user.username, plan=plan_name, seats=seats, months=months, amount=plans.price_total(plan, seats, months),
        currency=plans.load_pricing().get("currency", "so'm"), payment_method=payment_method or (methods[0] if methods else None),
        invoice_no=f"INV-{utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}", status="pending", note=organization,
    )
    session.add(sub)
    add_audit(session, "subscription_requested", user.username, None, f"plan={plan_name} seats={seats} months={months} amount={sub.amount}")
    session.commit()
    session.refresh(sub)
    return sub


def confirm_subscription(session: Session, sub_id: int, actor: User) -> Subscription:
    sub = session.get(Subscription, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Obuna so'rovi topilmadi")
    is_owner = sub.username == actor.username
    if actor.role != "admin" and not (is_owner and config.settings.demo_payments):
        raise HTTPException(status_code=403, detail="To'lovni faqat administrator tasdiqlaydi")
    if sub.status == "active":
        return sub
    now = utcnow()
    sub.status = "active"
    sub.started_at = now
    sub.expires_at = now + timedelta(days=30 * max(1, sub.months))
    sub.updated_at = now
    session.add(sub)
    user = session.exec(select(User).where(User.username == sub.username)).first()
    if user:
        user.plan = sub.plan
        session.add(user)
    for other in session.exec(select(Subscription).where(Subscription.username == sub.username, Subscription.status == "active", Subscription.id != sub.id)).all():
        other.status = "expired"
        session.add(other)
    add_audit(session, "subscription_activated", actor.username, sub.id, f"user={sub.username} plan={sub.plan} amount={sub.amount} via={sub.payment_method}")
    session.commit()
    session.refresh(sub)
    return sub


def cancel_subscription(session: Session, user: User) -> Optional[Subscription]:
    if user.id is None:
        raise HTTPException(status_code=400, detail="Tizimga kiring")
    last = None
    for sub in session.exec(select(Subscription).where(Subscription.username == user.username, Subscription.status.in_(["active", "pending"]))).all():  # type: ignore[attr-defined]
        sub.status = "cancelled"
        sub.updated_at = utcnow()
        session.add(sub)
        last = sub
    db_user = session.get(User, user.id)
    if db_user:
        db_user.plan = "free"
        session.add(db_user)
    add_audit(session, "subscription_cancelled", user.username, None, None)
    session.commit()
    return last
