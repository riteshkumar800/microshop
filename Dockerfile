FROM python:3.11-slim

# OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx supervisor ca-certificates curl bash tini && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on

WORKDIR /app

# App sources
COPY product-service  /app/product-service
COPY user-service     /app/user-service
COPY order-service    /app/order-service
COPY payment-service  /app/payment-service
COPY ui/index.html    /usr/share/nginx/html/index.html

# Python deps (aggregate service requirements; add safe defaults)
RUN bash -lc 'set -e; \
  for f in /app/*-service/requirements.txt; do \
    [ -f "$f" ] && cat "$f"; \
  done > /tmp/requirements.txt; \
  pip install --no-cache-dir -r /tmp/requirements.txt || true; \
  pip install --no-cache-dir "fastapi>=0.110" "uvicorn[standard]>=0.27" \
    aiosqlite sqlalchemy passlib[bcrypt] python-multipart itsdangerous'

# Nginx & Supervisor configs
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template
COPY supervisord.conf   /etc/supervisord.conf
COPY start.sh           /start.sh
COPY run-uvicorn.sh     /app/run-uvicorn.sh

RUN chmod +x /start.sh /app/run-uvicorn.sh && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

# Local upstreams (Nginx template uses these)
ENV PRODUCT_HOST=127.0.0.1 \
    USER_HOST=127.0.0.1 \
    ORDER_HOST=127.0.0.1

# Start nginx (via start.sh) and the apps (via supervisord)
CMD ["/bin/sh","-lc","/start.sh && exec /usr/bin/supervisord -c /etc/supervisord.conf"]
