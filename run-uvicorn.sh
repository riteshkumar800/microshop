#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${1:?app dir missing}"
PORT="${2:-8000}"

cd "$APP_DIR"

# Try common layouts
if   [ -f "src/app/main.py" ]; then MODULE="app.main:app"; APPDIR="src"
elif [ -f "src/main.py"     ]; then MODULE="main:app";     APPDIR="src"
elif [ -f "app/main.py"     ]; then MODULE="app.main:app"; APPDIR="."
elif [ -f "main.py"         ]; then MODULE="main:app";     APPDIR="."
elif [ -f "app.py"          ]; then MODULE="app:app";      APPDIR="."
else
  echo "Could not find FastAPI entrypoint in $APP_DIR" >&2
  find . -maxdepth 3 -type f \( -name 'main.py' -o -name 'app.py' \) -print >&2 || true
  exit 1
fi

exec uvicorn "$MODULE" --host 0.0.0.0 --port "$PORT" --app-dir "$APPDIR" \
  --proxy-headers --forwarded-allow-ips='*' --log-level info
