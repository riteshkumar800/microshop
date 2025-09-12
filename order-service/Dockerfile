FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app \
    USER_URL=http://user-service:8001 \
    PRODUCT_URL=http://product-service:8000 \
    PAYMENT_URL=http://payment-service:8003
WORKDIR /app
COPY requirements.txt .
RUN pip install -q --no-cache-dir -r requirements.txt
COPY src ./src
EXPOSE 8002
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
