import io

from openpyxl import Workbook


def test_import_students_csv_and_groups(client, auth_headers):
    csv_data = "HEMIS ID;F.I.Sh.;Guruh\n123456;Karimov Aziz;IMP-01\n123457;Rahimova Dilnoza;IMP-01\n;Bo'sh ID;IMP-01\n".encode("utf-8")
    r = client.post("/api/students/import", files={"file": ("talabalar.csv", csv_data, "text/csv")}, headers=auth_headers)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["imported"] == 2 and j["groups"] == ["IMP-01"]
    assert len(j["errors"]) == 1

    lst = client.get("/api/students", params={"group_name": "IMP-01"})
    assert {s["student_id"] for s in lst.json()} == {"123456", "123457"}
    assert any(g["name"] == "IMP-01" and g["student_count"] == 2 for g in client.get("/api/groups").json())

    # qayta import -> updated
    r2 = client.post("/api/students/import", files={"file": ("talabalar.csv", csv_data, "text/csv")})
    assert r2.json()["updated"] == 2


def test_import_students_xlsx(client):
    wb = Workbook()
    ws = wb.active
    ws.append(["student_id", "full_name", "group"])
    ws.append([555001, "Toshmatov Bobur", "XL-01"])
    buf = io.BytesIO()
    wb.save(buf)
    r = client.post("/api/students/import", files={"file": ("list.xlsx", buf.getvalue(), "application/octet-stream")})
    assert r.status_code == 200, r.text
    assert r.json()["imported"] == 1
    st = client.get("/api/students", params={"q": "Toshmatov"}).json()
    assert st and st[0]["student_id"] == "555001"


def test_create_student_and_group(client):
    r = client.post("/api/students", json={"student_id": "NEW-1", "full_name": "Yangi Talaba", "group_name": "NEW-G"})
    assert r.status_code == 200 and r.json()["group_name"] == "NEW-G"
    g = client.post("/api/groups", json={"name": "NEW-G", "faculty": "AT", "course_year": 2})
    assert g.status_code == 200 and g.json()["faculty"] == "AT"
    assert client.post("/api/students", json={"student_id": "  "}).status_code == 422


def test_rubric_templates_and_assignments(client):
    d = client.get("/api/rubrics/default").json()
    assert sum(i["max_score"] for i in d) == 100
    lst = client.get("/api/rubrics").json()
    assert any(t["is_default"] for t in lst)

    r = client.post("/api/rubrics", json={"name": "Test rubrika", "items": [{"name": "A", "max_score": 60}, {"name": "B", "max_score": 40}]})
    assert r.status_code == 200
    tid = r.json()["id"]

    a = client.post("/api/assignments", json={"title": "1-topshiriq", "course": "Fizika", "topic": "Kinematika", "group_name": "AS-1", "rubric_template_id": tid, "reference_answer": "Tezlik, tezlanish, yo'l."})
    assert a.status_code == 200
    aid = a.json()["id"]

    g = client.post("/api/grade", data={"text": "Tezlik va tezlanish tushunchalari. Yo'l formulasi s = v t. Masalan, 2 soatda 100 km. Xulosa: kinematika harakatni o'rganadi.", "student_id": "AS-ST-1", "assignment_id": aid})
    assert g.status_code == 200, g.text
    j = g.json()
    assert [i["name"] for i in j["rubric"]] == ["A", "B"]
    assert j["course"] == "Fizika" and j["topic"] == "Kinematika" and j["group_name"] == "AS-1"

    assert client.delete(f"/api/assignments/{aid}").status_code == 200
    assert client.delete(f"/api/rubrics/{tid}").status_code == 200
    assert client.delete(f"/api/rubrics/{tid}").status_code == 404
