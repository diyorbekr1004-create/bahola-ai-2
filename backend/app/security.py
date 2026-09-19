"""Autentifikatsiya: parol xeshlash (PBKDF2), JWT (PyJWT), rollar.

`AUTH_REQUIRED=false` (default) rejimida token yuborilmagan so'rovlar demo
o'qituvchi sifatida qabul qilinadi — xakaton namoyishi uchun qulay. Ishlab
chiqarishda `AUTH_REQUIRED=true` va kuchli `SECRET_KEY` o'rnating.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from . import config
from .db import User, engine, init_db

ALGORITHM = "HS256"
PBKDF2_ITERATIONS = 200_000

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

DEMO_USERS = [
    ("teacher", "teacher123", "Demo O'qituvchi", "teacher"),
    ("admin", "admin123", "Kafedra mudiri", "admin"),
    ("dekan", "dekan123", "Dekanat", "dean"),
]


# ---------------------------------------------------------------------------
# Parol
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, hashed: str) -> bool:
    try:
        scheme, iterations, salt_b64, digest_b64 = hashed.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    s = config.settings
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=s.access_token_expire_minutes))
    payload.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(payload, s.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.settings.secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


# ---------------------------------------------------------------------------
# Foydalanuvchilar
# ---------------------------------------------------------------------------
def get_user_by_username(username: str) -> Optional[User]:
    with Session(engine) as s:
        return s.exec(select(User).where(User.username == username)).first()


def create_user(username: str, password: str, full_name: Optional[str] = None, role: str = "teacher") -> User:
    init_db()
    with Session(engine) as s:
        existing = s.exec(select(User).where(User.username == username)).first()
        if existing:
            return existing
        u = User(username=username, hashed_password=hash_password(password), full_name=full_name, role=role)
        s.add(u)
        s.commit()
        s.refresh(u)
        return u


def ensure_demo_users() -> None:
    if not config.settings.demo_users:
        return
    for username, password, full_name, role in DEMO_USERS:
        create_user(username, password, full_name=full_name, role=role)


def demo_user() -> User:
    return User(id=None, username="demo", hashed_password="", full_name="Demo O'qituvchi", role="teacher", is_active=True)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> User:
    if not token:
        if config.settings.auth_required:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token talab qilinadi", headers={"WWW-Authenticate": "Bearer"})
        return demo_user()
    payload = decode_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token yaroqsiz yoki muddati o'tgan")
    user = get_user_by_username(payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Foydalanuvchi topilmadi")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Foydalanuvchi faol emas")
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    return user


def require_role(*roles: str):
    def _dep(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles and user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat yo'q")
        return user

    return _dep


def actor_name(user: Optional[User], fallback: Optional[str] = None) -> Optional[str]:
    if fallback:
        return fallback
    if user is None:
        return None
    return user.username
