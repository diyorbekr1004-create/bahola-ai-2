import io
import zipfile

import pytest

from app import plans


@pytest.fixture()
def free_user(client):
    client.post("/auth/signup", data={"username": "free_teacher", "password": "secret123"})
    tok = client.post("/auth/token", data={"username": "free_teacher", "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_plans_and_competitors(client):
    p = client.get("/api/plans").json()
    names = [x["name"] for x in p["plans"]]
    assert names[:2] == ["free", "pro"] and "universitet" in names
    assert p["plans"][1]["price_per_seat"] == 59000
    c = client.get("/api/competitors").json()
    assert c["competitors"]["columns"][0] == "Bahola AI"
    assert len(c["competitors"]["rows"]) >= 5 and len(c["advantages"]) >= 3


def test_demo_user_has_default_plan(client):
    s = client.get("/api/subscription").json()
    assert s["plan"] == "universitet" and s["is_demo_user"] is True
    assert s["usage"]["grades_limit"] is None
    r = client.post("/api/subscription", json={"plan": "pro"})
    assert r.status_code == 400  # demo (tizimga kirmagan) foydalanuvchi obuna qila olmaydi


def test_free_plan_limits_and_upgrade_flow(client, free_user, good_text, weak_text, monkeypatch):
    s = client.get("/api/subscription", headers=free_user).json()
    assert s["plan"] == "free" and s["usage"]["grades_limit"] == 30 and s["features"]["llm"] is False

    monkeypatch.setitem(plans.get_plan("free")["limits"], "grades_per_month", 2)
    assert client.post("/api/grade", data={"text": good_text, "student_id": "F-1"}, headers=free_user).status_code == 200
    assert client.post("/api/grade", data={"text": weak_text, "student_id": "F-2"}, headers=free_user).status_code == 200
    third = client.post("/api/grade", data={"text": good_text, "student_id": "F-3"}, headers=free_user)
    assert third.status_code == 402 and "Pro" in third.json()["detail"]
    assert client.get("/api/subscription", headers=free_user).json()["usage"]["grades_remaining"] == 0

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("Z-1.txt", good_text)
    assert client.post("/api/grade/batch", files=[("files", ("z.zip", buf.getvalue(), "application/zip"))], headers=free_user).status_code == 402
    assert client.get("/api/reports/export", params={"format": "hemis"}, headers=free_user).status_code == 402
    rep = client.post("/api/reports", json={"export_format": "all"}, headers=free_user).json()
    assert "hemis_export" in rep["locked_features"] and rep["hemis_download_url"] is None and rep["download_url"]

    # Obuna: so'rov -> hisob-faktura -> tasdiqlash (demo) -> pro
    r = client.post("/api/subscription", json={"plan": "pro", "seats": 1, "months": 1, "payment_method": "Payme"}, headers=free_user)
    assert r.status_code == 200, r.text
    st = r.json()
    assert st["plan"] == "free" and st["pending"]["amount"] == 59000 and st["pending"]["invoice_no"].startswith("INV-")
    sid = st["pending"]["id"]
    st2 = client.post(f"/api/subscription/{sid}/confirm", headers=free_user).json()
    assert st2["plan"] == "pro" and st2["subscription"]["status"] == "active" and st2["usage"]["grades_limit"] is None
    assert client.post("/api/grade", data={"text": good_text, "student_id": "F-4"}, headers=free_user).status_code == 200
    assert client.get("/api/reports/export", params={"format": "hemis"}, headers=free_user).status_code == 200
    assert client.get("/auth/me", headers=free_user).json()["plan"] == "pro"

    # Bekor qilish -> free
    assert client.post("/api/subscription/cancel", headers=free_user).json()["plan"] == "free"
    bad = client.post("/api/subscription", json={"plan": "yoq"}, headers=free_user)
    assert bad.status_code == 422


def test_min_seats_and_admin_list(client, free_user):
    r = client.post("/api/subscription", json={"plan": "kafedra", "seats": 5, "months": 12, "payment_method": "Bank hisob-faktura"}, headers=free_user).json()
    assert r["pending"]["seats"] == 20 and r["pending"]["amount"] == 30000 * 20 * 12
    admin = client.post("/auth/token", data={"username": "admin", "password": "admin123"}).json()["access_token"]
    lst = client.get("/api/subscriptions", params={"status": "pending"}, headers={"Authorization": f"Bearer {admin}"})
    assert lst.status_code == 200 and any(x["username"] == "free_teacher" for x in lst.json())
    assert client.get("/api/subscriptions", headers=free_user).status_code == 403
