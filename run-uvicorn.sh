#!/usr/bin/env bash
set -euo pipefail
SERVICE_DIR="${1:-.}"
PORT="${2:-8000}"

cd "$SERVICE_DIR"

if [ -f "src/main.py" ]; then
  exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --app-dir src
elif [ -f "src/app.py" ]; then
  exec uvicorn app:app  --host 0.0.0.0 --port "$PORT" --app-dir src
elif [ -f "main.py" ]; then
  exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
elif [ -f "app.py" ]; then
  exec uvicorn app:app  --host 0.0.0.0 --port "$PORT"
else
  echo "❌ No FastAPI entrypoint found in $SERVICE_DIR (looked for src/main.py, src/app.py, main.py, app.py)" >&2
  find . -maxdepth 2 -name "*.py" -print
  exit 1
fi
