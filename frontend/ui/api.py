"""Backend bilan ishlash uchun yengil HTTP mijoz (httpx)."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
import streamlit as st


class APIError(Exception):
    pass


def default_backend_url() -> str:
    url = os.getenv("BACKEND_URL")
    if url:
        return url
    try:
        return st.secrets.get("backend_url", "http://localhost:8000")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 - secrets fayli yo'q
        return "http://localhost:8000"


def backend_url() -> str:
    return st.session_state.get("backend_url") or default_backend_url()


def auth_headers() -> Dict[str, str]:
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _detail(resp: httpx.Response) -> str:
    try:
        data = resp.json()
        detail = data.get("detail") if isinstance(data, dict) else data
        if isinstance(detail, list):
            return "; ".join(f"{'.'.join(str(x) for x in d.get('loc', []))}: {d.get('msg')}" for d in detail)
        return str(detail)
    except ValueError:
        return resp.text[:300]


def _request(method: str, path: str, *, timeout: float = 120.0, **kwargs) -> httpx.Response:
    url = f"{backend_url().rstrip('/')}{path}"
    headers = {**auth_headers(), **kwargs.pop("headers", {})}
    try:
        resp = httpx.request(method, url, headers=headers, timeout=timeout, **kwargs)
    except httpx.HTTPError as exc:
        raise APIError(f"Backend bilan bog'lanib bo'lmadi ({url}): {exc}") from exc
    if resp.status_code == 402:
        raise APIError(f"💳 Tarif cheklovi: {_detail(resp)}")
    if resp.status_code >= 400:
        raise APIError(f"{resp.status_code}: {_detail(resp)}")
    return resp


def get(path: str, **params) -> Any:
    return _request("GET", path, params={k: v for k, v in params.items() if v not in (None, "", [])}).json()


def post(path: str, *, json: Optional[dict] = None, data: Optional[dict] = None, files: Any = None, params: Optional[dict] = None) -> Any:
    if data is not None:
        data = {k: v for k, v in data.items() if v not in (None, "")}
    return _request("POST", path, json=json, data=data, files=files, params=params).json()


def delete(path: str) -> Any:
    return _request("DELETE", path).json()


def download(path: str, **params) -> bytes:
    return _request("GET", path, params={k: v for k, v in params.items() if v not in (None, "")}).content


def health() -> Optional[dict]:
    try:
        return _request("GET", "/api/health", timeout=5.0).json()
    except APIError:
        return None


@st.cache_data(ttl=30, show_spinner=False)
def cached_get(path: str, backend: str, token: Optional[str], **params) -> Any:
    """30 soniya keshlanadigan GET (ro'yxatlar uchun)."""
    return get(path, **params)


def invalidate() -> None:
    cached_get.clear()
