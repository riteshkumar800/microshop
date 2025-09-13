#!/usr/bin/env bash
set -euo pipefail

# Ensure defaults for internal services
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///data.db}"
export PRODUCT_SERVICE_URL="${PRODUCT_SERVICE_URL:-http://127.0.0.1:8000}"

# Make nginx listen on Render's $PORT
PORT="${PORT:-10000}"
sed -i "s/__PORT__/${PORT}/g" /etc/nginx/conf.d/default.conf

# Start FastAPI apps via Supervisor
supervisord -c /etc/supervisor/supervisord.conf &

# Small wait and then run nginx in foreground
sleep 1
nginx -g 'daemon off;'
