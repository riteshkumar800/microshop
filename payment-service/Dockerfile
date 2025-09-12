FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app
WORKDIR /app
COPY requirements.txt .
RUN pip install -q --no-cache-dir -r requirements.txt
COPY src ./src
EXPOSE 8003
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
