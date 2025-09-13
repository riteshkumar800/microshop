FROM python:3.11-slim
WORKDIR /app

# System deps (optional but nice to have)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# IMPORTANT: bind to $PORT (Render provides it) – default to 10000 locally
CMD ["sh", "-c", "uvicorn src.app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
