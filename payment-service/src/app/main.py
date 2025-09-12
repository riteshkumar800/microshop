from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import time
from starlette.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

SERVICE = "payment-service"
REQ_COUNT = Counter("http_requests_total", "HTTP requests", ["service","path","method","code"])
REQ_LAT = Histogram("http_request_duration_seconds", "Latency", ["service","path","method"])

app = FastAPI(title=SERVICE)
PROCESSED = {}

@app.middleware("http")
async def metrics_mw(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    dur = time.perf_counter() - start
    REQ_COUNT.labels(SERVICE, request.url.path, request.method, str(response.status_code)).inc()
    REQ_LAT.labels(SERVICE, request.url.path, request.method).observe(dur)
    return response

class PayIn(BaseModel):
    amount: float
    currency: str = "INR"
    source: str = "card_xxx"
    description: str | None = None

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/pay")
def pay(body: PayIn, x_idempotency_key: str | None = Header(None)):
    if not x_idempotency_key:
        raise HTTPException(400,"X-Idempotency-Key required")
    if x_idempotency_key in PROCESSED:
        return PROCESSED[x_idempotency_key]
    if body.amount <= 0:
        raise HTTPException(400,"Invalid amount")
    result = {"status":"succeeded","amount":body.amount,"currency":body.currency}
    PROCESSED[x_idempotency_key] = result
    return result
