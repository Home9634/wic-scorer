#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
  pip install -r requirements.txt
fi

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
