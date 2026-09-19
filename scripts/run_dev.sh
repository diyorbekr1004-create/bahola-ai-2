#!/usr/bin/env bash
# Backend (uvicorn) va frontend (Streamlit) ni birga ishga tushiradi (Linux / macOS / Windows Git Bash). Ctrl+C ikkalasini to'xtatadi.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] && set -a && . ./.env && set +a
export BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

if [ -x "$ROOT/.venv/bin/python" ]; then PY="$ROOT/.venv/bin/python"
elif [ -x "$ROOT/.venv/Scripts/python.exe" ]; then PY="$ROOT/.venv/Scripts/python.exe"
else PY="python"; fi

echo "▶ Backend: http://localhost:8000/docs"
(cd backend && "$PY" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
BACK_PID=$!
trap 'kill $BACK_PID 2>/dev/null || true' EXIT
sleep 2
echo "▶ Frontend: http://localhost:8501"
"$PY" -m streamlit run frontend/streamlit_app.py --server.port 8501
