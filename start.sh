#!/usr/bin/env bash
set -euo pipefail

# Render provides $PORT; fall back if missing
export PORT="${PORT:-10000}"

# Render's nginx (Debian) doesn't auto-template; do it ourselves
envsubst '\$PORT' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Start everything
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
