"""Backend (uvicorn) ni Streamlit ichidan avtomatik ishga tushirish.

`BACKEND_URL` localhost bo'lsa va backend javob bermasa, shu venv'dagi Python bilan
`uvicorn app.main:app` fon jarayoni sifatida ishga tushiriladi (log: backend.log).
O'chirish: AUTO_START_BACKEND=false.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import streamlit as st

from . import api

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
LOG_PATH = ROOT / "backend.log"


def is_local(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def auto_start_enabled() -> bool:
    return os.getenv("AUTO_START_BACKEND", "true").strip().lower() not in {"0", "false", "no", "off"}


def port_free(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) != 0


def pick_port(preferred: int) -> int:
    """Afzal port band bo'lsa (masalan, eski jarayon osilib qolgan), keyingi bo'sh portni tanlaydi."""
    for port in [preferred] + list(range(preferred + 1, preferred + 20)):
        if port_free(port):
            return port
    return preferred


@st.cache_resource(show_spinner=False)
def _spawn(port: int) -> dict:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    # Windows'da "OpenBLAS: Memory allocation failed" xatosining oldini olish
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("OMP_NUM_THREADS", "1")
    log = open(LOG_PATH, "ab")
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(BACKEND_DIR), env=env, stdout=log, stderr=subprocess.STDOUT, **kwargs,
    )
    return {"proc": proc, "port": port, "started": time.time()}


def tail_log(lines: int = 40) -> str:
    try:
        data = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(data[-lines:])


def restart() -> None:
    """Jarayonni to'xtatib, keyingi urinishda qayta ishga tushirish."""
    for proc in st.session_state.get("_backend_procs", []):
        try:
            proc.terminate()
        except Exception:  # noqa: BLE001
            pass
    st.session_state["_backend_procs"] = []
    _spawn.clear()


def ensure_backend(wait_seconds: int = 30) -> Tuple[bool, str, Optional[dict]]:
    """(ishlayaptimi, holat, health) — kerak bo'lsa backendni ishga tushiradi va kutadi."""
    h = api.health()
    if h:
        return True, "ok", h
    url = api.backend_url()
    if not is_local(url) or not auto_start_enabled():
        return False, "remote", None
    if not (BACKEND_DIR / "app" / "main.py").exists():
        return False, "no-backend-dir", None
    preferred = urlparse(url).port or 8000
    port = pick_port(preferred)
    if port != preferred:
        # 8000-port boshqa (javob bermayotgan) jarayon tomonidan band — yangi portga o'tamiz
        parsed = urlparse(url)
        st.session_state["backend_url"] = f"{parsed.scheme}://{parsed.hostname}:{port}"
    info = _spawn(port)
    st.session_state.setdefault("_backend_procs", []).append(info["proc"])
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        h = api.health(timeout=2.0)
        if h:
            return True, "started", h
        if info["proc"].poll() is not None:
            return False, "exited", None
        time.sleep(1.0)
    return False, "timeout", None
