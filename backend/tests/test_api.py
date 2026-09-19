import io
import json
import zipfile

from docx import Document


def test_health_and_config(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["provider"] == "mock"
    c = client.get("/api/config")
    assert c.status_code == 200
    assert c.json()["grade_thresholds"]["5"] == 86


def test_grade_text_returns_structured_result(client, good_text):
    r = client.post("/api/grade", data={"text": good_text, "student_id": "ST-001", "student_name": "Aliyev Vali", "group_name": "AT-21-01", "course": "Pedagogika", "topic": "Ta'lim va texnologiya"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["grade_id"] and j["submission_id"]
    assert 0 <= j["total_score"] <= j["max_score"] == 100
    assert j["grade_5"] in (2, 3, 4, 5)
    assert len(j["rubric"]) == 5
    assert all(item["score"] is not None and item["score"] <= item["max_score"] for item in j["rubric"])
    assert j["feedback"]["summary"]
    assert isinstance(j["feedback"]["errors"], list)
    assert j["status"] == "pending" and j["confirmed"] is False
    assert j["student_name"] == "Aliyev Vali"
    assert j["provider"] == "mock"


def test_good_text_scores_higher_than_weak(client, good_text, weak_text):
    good = client.post("/api/grade", data={"text": good_text, "student_id": "ST-002", "course": "Pedagogika"}).json()
    weak = client.post("/api/grade", data={"text": weak_text, "student_id": "ST-003", "course": "Pedagogika"}).json()
    assert good["total_score"] > weak["total_score"]
    assert any("qisqa" in e for e in weak["feedback"]["errors"])


def test_grading_is_deterministic(client, good_text):
    a = client.post("/api/grade", data={"text": good_text, "student_id": "ST-004"}).json()
    b = client.post("/api/grade", data={"text": good_text, "student_id": "ST-004"}).json()
    assert a["total_score"] == b["total_score"]


def test_custom_rubric_and_reference_answer(client, good_text):
    rubric = json.dumps([{"name": "Mavzuga moslik", "max_score": 50}, {"name": "Xulosa", "max_score": 50}])
    r = client.post("/api/grade", data={"text": good_text, "student_id": "ST-005", "rubric": rubric, "reference_answer": "Texnologiya ta'lim sifatini oshiradi, HEMIS shaffoflik beradi, sun'iy intellekt vaqtni tejaydi."})
    assert r.status_code == 200, r.text
    j = r.json()
    assert [i["name"] for i in j["rubric"]] == ["Mavzuga moslik", "Xulosa"]
    assert j["max_score"] == 100


def test_invalid_rubric_rejected(client, good_text):
    r = client.post("/api/grade", data={"text": good_text, "rubric": "not json"})
    assert r.status_code == 422


def test_empty_text_rejected(client):
    r = client.post("/api/grade", data={"text": "   "})
    assert r.status_code == 422


def test_grade_docx_upload(client, good_text):
    doc = Document()
    for para in good_text.split("\n\n"):
        doc.add_paragraph(para)
    buf = io.BytesIO()
    doc.save(buf)
    r = client.post("/api/grade", data={"course": "Pedagogika"}, files={"file": ("AT2101_Karimova_Nilufar.docx", buf.getvalue(), "application/octet-stream")})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["student_id"] == "AT2101_Karimova_Nilufar"
    assert j["filename"].endswith(".docx")
    assert j["word_count"] > 100


def test_batch_grading_with_zip(client, good_text, weak_text):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ST-101.txt", good_text)
        zf.writestr("ST-102.txt", weak_text)
        zf.writestr("readme.exe", b"\x00\x01binary")
    r = client.post("/api/grade/batch", data={"course": "Pedagogika", "group_name": "AT-21-02", "topic": "Batch mavzu"}, files=[("files", ("ishlar.zip", buf.getvalue(), "application/zip"))])
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["total"] == 2 and j["graded"] == 2 and j["failed"] == 0
    assert {x["student_id"] for x in j["results"]} == {"ST-101", "ST-102"}


def test_similarity_between_students_is_flagged(client, good_text):
    client.post("/api/grade", data={"text": good_text, "student_id": "SIM-1", "course": "Fizika", "topic": "Kinematika"})
    r = client.post("/api/grade", data={"text": good_text + " Qo'shimcha jumla.", "student_id": "SIM-2", "course": "Fizika", "topic": "Kinematika"})
    j = r.json()
    assert j["integrity"]["similarity_score"] >= 0.6
    assert j["integrity"]["similar_to_student"] == "SIM-1"
    assert "similar_submission" in j["integrity"]["flags"]


def test_list_get_confirm_edit_delete_flow(client, good_text, auth_headers):
    g = client.post("/api/grade", data={"text": good_text, "student_id": "ST-777", "course": "Matematika"}).json()
    gid = g["grade_id"]

    lst = client.get("/api/grades", params={"course": "Matematika"}, headers=auth_headers)
    assert lst.status_code == 200 and any(x["grade_id"] == gid for x in lst.json())

    got = client.get(f"/api/grade/{gid}")
    assert got.status_code == 200 and got.json()["rubric"]

    conf = client.post(f"/api/grade/{gid}/confirm", json={"teacher_id": "t1", "comment": "Yaxshi ish"}, headers=auth_headers)
    assert conf.status_code == 200 and conf.json()["grade"]["confirmed"] is True
    assert conf.json()["grade"]["status"] == "confirmed"

    edit_payload = {"teacher_id": "t1", "corrected_rubric": [{**item, "score": item["max_score"]} for item in g["rubric"]], "comment": "Ballarni oshirdim"}
    ed = client.post(f"/api/grade/{gid}/edit", json=edit_payload, headers=auth_headers)
    assert ed.status_code == 200, ed.text
    eg = ed.json()["grade"]
    assert eg["total_score"] == 100 and eg["status"] == "edited" and eg["ai_total_score"] == g["total_score"]

    ed2 = client.post(f"/api/grade/{gid}/edit", json={"teacher_id": "t1", "corrected_total": 250}, headers=auth_headers)
    assert ed2.json()["grade"]["total_score"] == 100  # max_score dan oshmaydi

    fb = client.get(f"/api/grade/{gid}/feedback.docx")
    assert fb.status_code == 200 and fb.content[:2] == b"PK"

    audit = client.get("/api/audit", headers=auth_headers)
    actions = {a["action"] for a in audit.json()}
    assert {"grade_autogenerated", "grade_confirmed", "grade_edited"} <= actions

    d = client.delete(f"/api/grade/{gid}", headers=auth_headers)
    assert d.status_code == 200
    assert client.get(f"/api/grade/{gid}").status_code == 404


def test_detect_endpoint(client, weak_text):
    r = client.post("/api/detect", json={"text": weak_text, "compare_with": [weak_text]})
    assert r.status_code == 200
    j = r.json()
    assert 0 <= j["plagiarism_score"] <= 1 and 0 <= j["ai_likelihood"] <= 1
    assert j["similarity_score"] >= 0.9


def test_stats_endpoint(client):
    r = client.get("/api/stats")
    assert r.status_code == 200
    assert r.json()["total_grades"] >= 1
    assert r.json()["time_saved_hours"] > 0
