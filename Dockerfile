FROM python:3.11-slim

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx supervisor gettext-base && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy source
COPY product-service/ ./product-service/
COPY user-service/    ./user-service/
COPY order-service/   ./order-service/
COPY payment-service/ ./payment-service/
COPY ui/index.html    /usr/share/nginx/html/index.html

# python deps (from each service)
RUN pip install --no-cache-dir \
    -r product-service/requirements.txt \
    -r user-service/requirements.txt \
    -r order-service/requirements.txt \
    -r payment-service/requirements.txt

# nginx + supervisord + start script
COPY onebox/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY onebox/supervisord.conf   /etc/supervisor/conf.d/supervisord.conf
COPY onebox/start.sh           /start.sh
RUN chmod +x /start.sh

# Render routes traffic to $PORT for Docker services; we template it at runtime
ENV PORT=10000
EXPOSE 10000

CMD ["/start.sh"]
