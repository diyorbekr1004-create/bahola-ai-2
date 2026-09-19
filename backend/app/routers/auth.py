"""Autentifikatsiya endpointlari."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..schemas import TokenResponse, UserOut
from ..security import create_access_token, create_user, get_current_user, get_user_by_username, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(u) -> UserOut:
    return UserOut(id=u.id, username=u.username, full_name=u.full_name, role=u.role, is_active=u.is_active)


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login yoki parol noto'g'ri")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Foydalanuvchi faol emas")
    token = create_access_token({"sub": user.username, "role": user.role})
    return TokenResponse(access_token=token, user=_user_out(user))


@router.post("/signup", response_model=UserOut)
async def signup(form_data: OAuth2PasswordRequestForm = Depends()):
    if get_user_by_username(form_data.username):
        raise HTTPException(status_code=400, detail="Bunday foydalanuvchi mavjud")
    if len(form_data.password) < 6:
        raise HTTPException(status_code=422, detail="Parol kamida 6 belgidan iborat bo'lsin")
    return _user_out(create_user(form_data.username, form_data.password))


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return _user_out(user)
