"""Test muhiti: vaqtinchalik SQLite baza, eksport papkasi, mock LLM, ochiq auth."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="bahola_test_"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP / 'test.db'}"
os.environ["EXPORT_DIR"] = str(_TMP / "exports")
os.environ["LLM_PROVIDER"] = "mock"
os.environ["AUTH_REQUIRED"] = "false"
os.environ["DEMO_USERS"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes!!"
os.environ.pop("OPENAI_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

SAMPLE_GOOD = (
    "Ta'lim va texnologiya mavzusi bugungi kunda juda dolzarb. Ushbu ishning maqsadi raqamli texnologiyalarning "
    "ta'lim sifatiga ta'sirini tahlil qilishdir.\n\n"
    "Birinchidan, 2023-yilgi tadqiqotlarga ko'ra, onlayn platformalardan foydalanish talabalar o'zlashtirishini 18% oshirgan. "
    "Masalan, HEMIS tizimi orqali davomat va baholarni kuzatish shaffoflikni ta'minlaydi, chunki barcha ma'lumotlar bir joyda jamlanadi. "
    "Ikkinchidan, sun'iy intellekt vositalari o'qituvchining tekshirish vaqtini qisqartiradi, shuning uchun u metodik ishga ko'proq vaqt ajrata oladi.\n\n"
    "Bundan tashqari, YuNESKO ma'lumotlariga ko'ra (UNESCO, 2022) raqamli savodxonlik XXI asrning asosiy kompetensiyalaridan biridir. "
    "Shu bilan birga, texnologiyalarga haddan tashqari bog'lanish tanqidiy fikrlashni susaytirishi mumkin, masalan, tayyor javoblardan nusxa ko'chirish holatlari ko'paymoqda.\n\n"
    "Xulosa qilib aytganda, texnologiya ta'limda kuchli vosita, ammo u pedagogik yondashuv bilan uyg'unlashgandagina samara beradi. "
    "Demak, o'qituvchilarni raqamli kompetensiyalar bo'yicha muntazam o'qitish tavsiya etiladi."
)
SAMPLE_WEAK = "Texnologiya yaxshi. Texnologiya yaxshi. Kompyuter kerak."


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    resp = client.post("/auth/token", data={"username": "teacher", "password": "teacher123"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def good_text():
    return SAMPLE_GOOD


@pytest.fixture()
def weak_text():
    return SAMPLE_WEAK
