import pytest
from httpx import AsyncClient
from sqlmodel import Session

from app.main import app
from app.db import engine, Submission, GradeRecord, init_db


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


@pytest.mark.asyncio
async def test_reports_include_analytics_and_excel_export():
    init_db()
    with Session(engine) as s:
        sub = Submission(student_id="ST-101", course="Matematika", content="Test content")
        s.add(sub)
        s.commit()
        s.refresh(sub)
        s.add(GradeRecord(submission_id=sub.id, total_score=88, details='{"rubric": []}', confirmed=True))
        s.commit()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/reports", json={"course_name": "Matematika", "group_id": "G-1"})
        assert resp.status_code == 200
        payload = resp.json()
        assert "summary" in payload
        assert "analytics" in payload
        assert payload["analytics"]["average_score"] >= 0
        assert payload["excel_path"] is not None or "excel_path" in payload


@pytest.mark.asyncio
async def test_generate_docs_export_docx():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/generate-docs", json={
            "course_name": "Fizika",
            "hours": 60,
            "weeks": 15,
            "export_format": "docx",
        })
        assert resp.status_code == 200
        payload = resp.json()
        assert "export_path" in payload
        assert payload["export_path"]
