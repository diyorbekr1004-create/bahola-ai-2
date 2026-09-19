from app.assistant_kb import load, match_faq, offline_answer


def test_knowledge_base_loads_faq():
    kb = load(force=True)
    assert len(kb["faq"]) >= 10
    assert all(e["answer"] and e["tokens"] for e in kb["faq"])


def test_offline_matching_uz_variants():
    assert "Hisobotlar" in offline_answer("HEMIS eksport qanday qilinadi?")
    assert "59 000" in offline_answer("Narxlar qancha, tarif qanday?")
    assert "GEMINI_API_KEY" in offline_answer("Gemini kalitini qayerga yozaman?")
    assert "DOCX" in offline_answer("Qaysi fayl formatlarini yuklash mumkin")
    assert match_faq("asdkjh qwe") is None
    assert "aniq javobim yo'q" in offline_answer("asdkjh qwe")


def test_chat_endpoint_offline(client):
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "AI baholashi adolatlimi?"}]})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["provider"] == "mock" and j["offline"] is True
    assert "o'qituvchi" in j["answer"].lower()
    assert 1 <= len(j["suggestions"]) <= 4
    s = client.get("/api/chat/suggestions").json()
    assert len(s["suggestions"]) >= 4 and s["offline"] is True


def test_chat_endpoint_validation(client):
    assert client.post("/api/chat", json={"messages": []}).status_code == 422
    assert client.post("/api/chat", json={"messages": [{"role": "hacker", "content": "x"}]}).status_code == 422
    r = client.post("/api/chat", json={"messages": [{"role": "assistant", "content": "Salom"}]})
    assert r.status_code == 200 and r.json()["answer"]
