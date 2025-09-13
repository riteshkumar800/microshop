#!/usr/bin/env bash
set -euo pipefail

# Ensure PORT default (Render will set it automatically)
export PORT="${PORT:-10000}"

# Render’s nginx in Debian doesn’t auto-template; do it ourselves
envsubst '${PORT}' </etc/nginx/templates/default.conf.template >/etc/nginx/conf.d/default.conf

# Start everything under supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
