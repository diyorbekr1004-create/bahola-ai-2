def test_generate_docs_bundle_with_docx(client):
    r = client.post("/api/generate-docs", json={"course_name": "Matematika", "hours": 60, "weeks": 15, "n_tickets": 4, "n_questions": 12, "export_format": "docx"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["document_id"]
    s = j["structured"]["syllabus"]
    assert len(s["weekly"]) == 15
    assert s["weekly"][0]["topic"].startswith("To'plamlar")
    assert s["hours_breakdown"]["total"] >= 60
    assert len(j["structured"]["exam_tickets"]) == 4
    assert len(j["structured"]["test_questions"]) == 12
    assert all(q["answer"] in q["options"] for q in j["structured"]["test_questions"])
    assert "Hafta" not in j["syllabus"] or "hafta" in j["syllabus"]
    assert "BILET" in j["exam_ticket"]
    assert "Javoblar kaliti" in j["test_questions"]
    assert j["lesson_plan"].startswith("DARS REJASI")
    assert j["download_url"] and j["download_url"].startswith("/api/exports/")

    dl = client.get(j["download_url"])
    assert dl.status_code == 200 and dl.content[:2] == b"PK"
    dl2 = client.get(f"/api/documents/{j['document_id']}/download")
    assert dl2.status_code == 200

    lst = client.get("/api/documents")
    assert any(d["id"] == j["document_id"] for d in lst.json())
    one = client.get(f"/api/documents/{j['document_id']}")
    assert one.status_code == 200 and one.json()["structured"]["syllabus"]["weeks"] == 15


def test_generate_docs_unknown_course_uses_generic_topics(client):
    r = client.post("/api/generate-docs", json={"course_name": "Kvant kriptografiyasi", "weeks": 8, "doc_types": ["syllabus"], "export_format": None})
    assert r.status_code == 200
    j = r.json()
    assert len(j["structured"]["syllabus"]["weekly"]) == 8
    assert "Kvant kriptografiyasi" in j["structured"]["syllabus"]["weekly"][0]["topic"]
    assert "exam_tickets" not in j["structured"]
    assert j["export_path"] is not None  # docx default


def test_generate_docs_with_custom_topics(client):
    r = client.post("/api/generate-docs", json={"course_name": "Fizika", "weeks": 3, "topics": ["A", "B", "C"], "doc_types": ["syllabus", "exam_tickets"], "n_tickets": 2})
    j = r.json()
    assert [w["topic"] for w in j["structured"]["syllabus"]["weekly"]] == ["A", "B", "C"]
    assert len(j["structured"]["exam_tickets"]) == 2


def test_export_path_traversal_blocked(client):
    r = client.get("/api/exports/..%2F..%2Fetc%2Fpasswd")
    assert r.status_code == 404
