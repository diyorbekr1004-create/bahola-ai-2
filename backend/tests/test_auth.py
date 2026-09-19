from app import config
from app.security import hash_password, verify_password


def test_password_hashing_roundtrip():
    h = hash_password("parol123")
    assert h.startswith("pbkdf2_sha256$")
    assert verify_password("parol123", h) and not verify_password("boshqa", h)
    assert not verify_password("x", "buzilgan")


def test_signup_login_me(client):
    r = client.post("/auth/signup", data={"username": "yangi_teacher", "password": "secret123"})
    assert r.status_code == 200 and r.json()["role"] == "teacher"
    assert client.post("/auth/signup", data={"username": "yangi_teacher", "password": "secret123"}).status_code == 400
    assert client.post("/auth/signup", data={"username": "qisqa", "password": "123"}).status_code == 422

    bad = client.post("/auth/token", data={"username": "yangi_teacher", "password": "wrong"})
    assert bad.status_code == 401
    ok = client.post("/auth/token", data={"username": "yangi_teacher", "password": "secret123"})
    assert ok.status_code == 200
    token = ok.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["username"] == "yangi_teacher"
    assert client.get("/auth/me", headers={"Authorization": "Bearer yaroqsiz"}).status_code == 401


def test_demo_users_exist(client):
    for u, p in (("teacher", "teacher123"), ("admin", "admin123"), ("dekan", "dekan123")):
        assert client.post("/auth/token", data={"username": u, "password": p}).status_code == 200


def test_auth_required_mode(client, monkeypatch):
    monkeypatch.setattr(config.settings, "auth_required", True)
    assert client.get("/api/grades").status_code == 401
    assert client.get("/auth/me").status_code == 401
    tok = client.post("/auth/token", data={"username": "admin", "password": "admin123"}).json()["access_token"]
    assert client.get("/api/grades", headers={"Authorization": f"Bearer {tok}"}).status_code == 200
    monkeypatch.setattr(config.settings, "auth_required", False)
    assert client.get("/auth/me").json()["username"] == "demo"
