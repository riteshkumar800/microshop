# Onebox: Nginx + all FastAPI apps
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# OS deps: nginx, supervisor, envsubst, tini
RUN apt-get update && apt-get install -y --no-install-recommends \
      nginx supervisor ca-certificates curl gettext-base tini \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /run/nginx

WORKDIR /app

# Copy service code
COPY product-service /app/product-service
COPY user-service    /app/user-service
COPY order-service   /app/order-service
COPY payment-service /app/payment-service

# UI
COPY ui/index.html /app/ui/index.html

# Configs + entry
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY supervisord.conf    /etc/supervisor/conf.d/supervisord.conf
COPY start.sh            /app/start.sh
RUN chmod +x /app/start.sh

# Python deps (combine all service reqs)
RUN pip install --no-cache-dir \
      -r product-service/requirements.txt \
      -r user-service/requirements.txt \
      -r order-service/requirements.txt \
      -r payment-service/requirements.txt

# Reasonable defaults (order-service talks to product on localhost)
ENV PORT=10000 \
    DATABASE_URL=sqlite+aiosqlite:///data.db \
    PRODUCT_SERVICE_URL=http://127.0.0.1:8000 \
    USER_SERVICE_URL=http://127.0.0.1:8001

EXPOSE 10000
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["/app/start.sh"]
