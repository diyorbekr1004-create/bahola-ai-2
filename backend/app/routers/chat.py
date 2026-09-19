"""Sayt haqida yordamchi chat."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from .. import assistant_kb
from ..db import get_session
from ..llm import provider_info
from ..schemas import ChatRequest, ChatResponse
from ..security import get_current_user
from ..services import assistant

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, session: Session = Depends(get_session), user=Depends(get_current_user)):
    """Sayt, baholash, HEMIS eksport, tariflar haqida savollarga javob (LLM yoki oflayn FAQ)."""
    return await assistant.answer(session, user, req.messages)


@router.get("/chat/suggestions")
def chat_suggestions():
    info = provider_info()
    return {"suggestions": assistant_kb.suggested_questions(6), "provider": info["provider"], "model": info.get("model"), "offline": info["provider"] == "mock"}
