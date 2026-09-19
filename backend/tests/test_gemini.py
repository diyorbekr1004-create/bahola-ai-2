import json

import pytest

from app import config, llm
from app.gemini_adapter import GeminiAdapter
from app.llm_base import extract_json
from app.schemas import RubricItem


def _gemini_response(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}], "role": "model"}, "finishReason": "STOP"}]}


def test_build_payload_maps_roles_and_json_mode():
    msgs = [{"role": "system", "content": "Siz yordamchisiz"}, {"role": "user", "content": "Salom"}, {"role": "assistant", "content": "Salom!"}, {"role": "user", "content": "Narx?"}]
    p = GeminiAdapter.build_payload(msgs, temperature=0.2, max_tokens=100, json_mode=True)
    assert p["systemInstruction"]["parts"][0]["text"] == "Siz yordamchisiz"
    assert [c["role"] for c in p["contents"]] == ["user", "model", "user"]
    assert p["generationConfig"]["responseMimeType"] == "application/json"
    p2 = GeminiAdapter.build_payload(msgs, temperature=0.2, max_tokens=100, json_mode=False)
    assert "responseMimeType" not in p2["generationConfig"]


def test_extract_json_variants():
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Mana javob: {"a": 1} rahmat') == {"a": 1}
    assert extract_json("[1,2]") is None and extract_json("") is None


@pytest.mark.asyncio
async def test_gemini_grading_maps_scores(monkeypatch, good_text):
    adapter = GeminiAdapter(api_key="test-key", model="gemini-test")
    calls = []

    async def fake_post(payload):
        calls.append(payload)
        return _gemini_response(json.dumps({
            "rubric": [{"name": "Mavzuga moslik", "max_score": 50, "score": 44, "evidence": "Mavzu ochilgan"}, {"name": "Xulosa", "max_score": 50, "score": 80, "evidence": "..."}],
            "feedback": {"summary": "Yaxshi ish", "strengths": ["Aniq"], "errors": ["Manba kam"], "suggestions": ["Manba qo'shing"]},
        }))

    monkeypatch.setattr(adapter, "_post", fake_post)
    rubric = [RubricItem(name="Mavzuga moslik", max_score=50), RubricItem(name="Xulosa", max_score=50)]
    res = await adapter.grade_submission(good_text, rubric, topic="Ta'lim")
    assert res["provider"] == "gemini" and res["model"] == "gemini-test"
    assert res["rubric"][0].score == 44 and res["rubric"][1].score == 50  # max_score dan oshmaydi
    assert res["total_score"] == 94 and res["feedback"]["errors"] == ["Manba kam"]
    assert calls and "x-goog" not in json.dumps(calls[0])  # kalit payloadga tushmaydi
    assert calls[0]["generationConfig"]["responseMimeType"] == "application/json"


@pytest.mark.asyncio
async def test_gemini_failure_falls_back_to_offline(monkeypatch, good_text):
    adapter = GeminiAdapter(api_key="test-key")

    async def boom(payload):
        raise RuntimeError("503 Service Unavailable")

    monkeypatch.setattr(adapter, "_post", boom)
    res = await adapter.grade_submission(good_text, [RubricItem(name="Xulosa", max_score=100)])
    assert res["provider"] == "mock-fallback" and "503" in res["fallback_reason"]
    assert 0 < res["total_score"] <= 100

    async def bad_json(payload):
        return _gemini_response("bu json emas")

    monkeypatch.setattr(adapter, "_post", bad_json)
    res2 = await adapter.grade_submission(good_text, [RubricItem(name="Xulosa", max_score=100)])
    assert res2["provider"] == "mock-fallback"
    # erkin chat ham oflayn FAQ ga qaytadi
    monkeypatch.setattr(adapter, "_post", boom)
    text = await adapter.chat([{"role": "user", "content": "HEMIS eksport qanday qilinadi?"}], system="x")
    assert "HEMIS" in text


@pytest.mark.asyncio
async def test_gemini_chat_returns_text(monkeypatch):
    adapter = GeminiAdapter(api_key="k")

    async def fake_post(payload):
        assert "responseMimeType" not in payload["generationConfig"]
        return _gemini_response("Salom! Men yordamchiman.")

    monkeypatch.setattr(adapter, "_post", fake_post)
    assert await adapter.chat([{"role": "user", "content": "Salom"}]) == "Salom! Men yordamchiman."


def test_provider_resolution(monkeypatch):
    monkeypatch.setattr(config.settings, "llm_provider", "auto")
    monkeypatch.setattr(config.settings, "gemini_api_key", "g")
    monkeypatch.setattr(config.settings, "openai_api_key", "o")
    assert llm.resolve_provider() == "gemini"
    monkeypatch.setattr(config.settings, "gemini_api_key", "")
    assert llm.resolve_provider() == "openai"
    monkeypatch.setattr(config.settings, "openai_api_key", "")
    assert llm.resolve_provider() == "mock"
    monkeypatch.setattr(config.settings, "llm_provider", "gemini")
    assert llm.resolve_provider() == "mock"  # kalit yo'q -> oflayn
    monkeypatch.setattr(config.settings, "gemini_api_key", "g")
    llm.reset_llm()
    try:
        assert llm.get_llm().name == "gemini" and llm.provider_info()["model"] == config.settings.gemini_model
    finally:
        llm.reset_llm()
