#!/usr/bin/env sh
set -eu

# Where the template *really* is (as per Dockerfile COPY)
TEMPLATE="/etc/nginx/conf.d/default.conf.template"
OUT="/etc/nginx/conf.d/default.conf"

# Back-compat fallback if someone copied to /etc/nginx/templates/
if [ ! -f "$TEMPLATE" ] && [ -f "/etc/nginx/templates/default.conf.template" ]; then
  TEMPLATE="/etc/nginx/templates/default.conf.template"
fi

# Safe defaults (inside the onebox all services are localhost)
: "${PRODUCT_HOST:=127.0.0.1}"
: "${USER_HOST:=127.0.0.1}"
: "${ORDER_HOST:=127.0.0.1}"
: "${PAYMENT_HOST:=127.0.0.1}"

export PRODUCT_HOST USER_HOST ORDER_HOST PAYMENT_HOST

# Render the Nginx conf from the template
envsubst '
${PRODUCT_HOST}
${USER_HOST}
${ORDER_HOST}
${PAYMENT_HOST}
' < "$TEMPLATE" > "$OUT"

# Just generate; supervisord will start nginx
echo "Rendered Nginx config to $OUT"
