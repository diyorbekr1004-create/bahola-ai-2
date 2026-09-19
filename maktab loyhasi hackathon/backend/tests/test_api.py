import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_detect_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/detect", json={"text": "Bu test matni."})
        assert resp.status_code == 200
        j = resp.json()
        assert "plagiarism_score" in j


@pytest.mark.asyncio
async def test_grade_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/grade", data={"text": "Bu insho test uchun yozilgan."})
        assert resp.status_code == 200
        j = resp.json()
        assert "total_score" in j
        assert "grade_id" in j
