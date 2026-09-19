#!/usr/bin/env bash
# Linux/macOS uchun bir martalik o'rnatish: Python tekshiruvi -> venv -> paketlar -> demo ma'lumot -> testlar
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY=""
for cand in python3.12 python3.13 python3.11 python3.14 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then PY="$cand"; break; fi
  fi
done
[ -n "$PY" ] || { echo "Python 3.11+ topilmadi."; exit 1; }
echo "Python: $PY ($($PY --version))"

[ -d .venv ] || "$PY" -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
[ -f .env ] || cp .env.example .env
python scripts/seed.py --reset
(cd backend && python -m pytest -q)

echo
echo "Tayyor. Ishga tushirish:  make dev   (yoki scripts/run_dev.sh)"
