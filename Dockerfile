# Multi-app (FastAPI) + Nginx + Supervisor in one container
FROM python:3.11-slim

# OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx supervisor build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source
COPY product-service /app/product-service
COPY user-service    /app/user-service
COPY order-service   /app/order-service
COPY payment-service /app/payment-service
COPY ui/index.html   /usr/share/nginx/html/index.html

# Python deps (each service has its own requirements)
RUN pip install --no-cache-dir \
    -r /app/product-service/requirements.txt \
    -r /app/user-service/requirements.txt \
    -r /app/order-service/requirements.txt \
    -r /app/payment-service/requirements.txt

# Nginx + Supervisor configs and startup script
COPY nginx.conf.template      /etc/nginx/conf.d/default.conf
COPY supervisord.conf         /etc/supervisor/supervisord.conf
COPY start.sh                 /start.sh
RUN chmod +x /start.sh

# Make sure nginx logs go to stdout/stderr
RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

# Render provides $PORT; we’ll rewrite Nginx listen to it at runtime
ENV PORT=10000
EXPOSE 10000

CMD ["/start.sh"]
