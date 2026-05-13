#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! python3 -m pip --version >/dev/null 2>&1; then
  curl -fsSLo /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
  python3 /tmp/get-pip.py --user --break-system-packages
fi

if python3 -m venv .venv >/dev/null 2>&1; then
  . .venv/bin/activate
  python3 -m pip install --upgrade pip
  python3 -m pip install -r requirements.txt
  echo "Using virtual environment: .venv"
else
  python3 -m pip install --user --break-system-packages -r requirements.txt
  echo "python3-venv is unavailable, fell back to user-site installation."
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env created from .env.example"
fi

echo "Bootstrap completed."
