import pytest

from app import config, env_store, llm
from app.config import _normalize_sqlite_url
from app.gemini_adapter import GeminiAdapter


def test_normalize_sqlite_url():
    root = config.settings.project_root.as_posix()
    assert _normalize_sqlite_url("sqlite:///./data.db") == f"sqlite:///{root}/data.db"
    assert _normalize_sqlite_url("sqlite:///data.db") == f"sqlite:///{root}/data.db"
    assert _normalize_sqlite_url("sqlite:////tmp/x.db") == "sqlite:////tmp/x.db"
    assert _normalize_sqlite_url("sqlite:///C:/x/y.db") == "sqlite:///C:/x/y.db"
    assert _normalize_sqlite_url("postgresql://u:p@h/db") == "postgresql://u:p@h/db"


def test_update_env_file_replaces_and_appends(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# izoh\nLLM_PROVIDER=auto\nGEMINI_API_KEY=\nOTHER=1\n", encoding="utf-8")
    env_store.update_env_file(env, {"GEMINI_API_KEY": "AIzaTEST", "GEMINI_MODEL": "gemini-2.5-flash"})
    text = env.read_text(encoding="utf-8")
    assert "# izoh" in text and "OTHER=1" in text
    assert "GEMINI_API_KEY=AIzaTEST" in text and text.count("GEMINI_API_KEY=") == 1
    assert text.rstrip().endswith("GEMINI_MODEL=gemini-2.5-flash")
    assert env_store.mask("AIzaSy1234567890abcd") == "AIza…abcd" and env_store.mask("short") == "•••••" and env_store.mask("") is None


@pytest.fixture()
def restore_llm(tmp_path, monkeypatch):
    s = config.settings
    saved = (s.llm_provider, s.gemini_api_key, s.gemini_model, s.openai_api_key, s.project_root)
    monkeypatch.setattr(s, "project_root", tmp_path)
    (tmp_path / ".env.example").write_text("LLM_PROVIDER=auto\nGEMINI_API_KEY=\n", encoding="utf-8")
    yield tmp_path
    s.llm_provider, s.gemini_api_key, s.gemini_model, s.openai_api_key, s.project_root = saved
    llm.reset_llm()


def test_settings_endpoints_set_key_and_test_connection(client, restore_llm, monkeypatch):
    st = client.get("/api/settings/llm").json()
    assert st["active_provider"] == "mock" and st["gemini_key_set"] is False

    assert client.post("/api/settings/llm", json={"gemini_api_key": "short"}).status_code == 422

    r = client.post("/api/settings/llm", json={"provider": "auto", "gemini_api_key": "AIzaSyFAKEKEY1234567890abcdef", "gemini_model": "gemini-2.5-flash"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["active_provider"] == "gemini" and j["gemini_key_masked"] == "AIza…cdef" and j["env_exists"] is True
    env_text = (restore_llm / ".env").read_text(encoding="utf-8")
    assert "GEMINI_API_KEY=AIzaSyFAKEKEY1234567890abcdef" in env_text and "LLM_PROVIDER=auto" in env_text
    assert client.get("/api/health").json()["provider"] == "gemini"

    async def fake_post(payload):
        return {"candidates": [{"content": {"parts": [{"text": "Assalomu alaykum!"}]}}]}

    monkeypatch.setattr(GeminiAdapter, "_post", lambda self, payload: fake_post(payload))
    t = client.post("/api/settings/llm/test").json()
    assert t["ok"] is True and t["provider"] == "gemini" and "alaykum" in t["sample"]

    async def boom(payload):
        raise RuntimeError("401 API key not valid")

    monkeypatch.setattr(GeminiAdapter, "_post", lambda self, payload: boom(payload))
    llm.reset_llm()
    t2 = client.post("/api/settings/llm/test").json()
    assert t2["ok"] is False and "401" in t2["error"]

    back = client.post("/api/settings/llm", json={"provider": "mock"}).json()
    assert back["active_provider"] == "mock"
    assert client.post("/api/settings/llm/test").json()["ok"] is False


def test_settings_require_admin_when_auth_required(client, monkeypatch):
    monkeypatch.setattr(config.settings, "auth_required", True)
    tok = client.post("/auth/token", data={"username": "teacher", "password": "teacher123"}).json()["access_token"]
    assert client.get("/api/settings/llm", headers={"Authorization": f"Bearer {tok}"}).status_code == 403
    adm = client.post("/auth/token", data={"username": "admin", "password": "admin123"}).json()["access_token"]
    assert client.get("/api/settings/llm", headers={"Authorization": f"Bearer {adm}"}).status_code == 200
