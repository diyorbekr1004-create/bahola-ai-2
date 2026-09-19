#!/usr/bin/env bash
# Bir martalik o'rnatish (Linux / macOS / Windows Git Bash):
#   Python tekshiruvi -> venv -> paketlar -> demo ma'lumot -> testlar
# Ishga tushirish (loyiha ildizidan):  bash scripts/setup.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY=""
# Windows: `py` launcher orqali aniq versiyani tanlaymiz (Microsoft Store "python" stubidan qochish uchun)
if command -v py >/dev/null 2>&1; then
  for v in 3.12 3.13 3.11 3.14; do
    if py "-$v" -c 'import sys' >/dev/null 2>&1; then PY="py -$v"; break; fi
  done
fi
if [ -z "$PY" ]; then
  for cand in python3.12 python3.13 python3.11 python3.14 python3 python; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
      PY="$cand"; break
    fi
  done
fi
[ -n "$PY" ] || { echo "Python 3.11+ topilmadi. https://www.python.org/downloads/ dan 3.12 ni o'rnating."; exit 1; }
echo "Python: $PY ($($PY --version 2>&1))"

[ -d .venv ] || $PY -m venv .venv
if [ -x "$ROOT/.venv/bin/python" ]; then
  VENV_PY="$ROOT/.venv/bin/python"; ACTIVATE=". .venv/bin/activate"
else
  VENV_PY="$ROOT/.venv/Scripts/python.exe"; ACTIVATE="source .venv/Scripts/activate"
fi

"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r backend/requirements.txt
[ -f .env ] || cp .env.example .env
"$VENV_PY" scripts/seed.py --reset
(cd backend && "$VENV_PY" -m pytest -q)

echo
echo "Tayyor. Ishga tushirish:"
echo "  $ACTIVATE"
echo "  bash scripts/run_dev.sh        # backend (8000) + frontend (8501)"
