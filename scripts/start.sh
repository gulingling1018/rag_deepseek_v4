#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
fi

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
