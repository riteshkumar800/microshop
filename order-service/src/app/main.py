from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os, sqlite3, requests, json, time
from contextlib import contextmanager
from uuid import uuid4
from starlette.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SERVICE = "order-service"
REQ_COUNT = Counter("http_requests_total", "HTTP requests", ["service","path","method","code"])
REQ_LAT = Histogram("http_request_duration_seconds", "Latency", ["service","path","method"])

# retrying session for resilience
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.2, status_forcelist=[502,503,504], allowed_methods=["GET","POST"])
session.mount("http://", HTTPAdapter(max_retries=retries))

DB_PATH = "orders.db"
USER_URL = os.getenv("USER_URL","http://user-service:8001")
PRODUCT_URL = os.getenv("PRODUCT_URL","http://product-service:8000")
PAYMENT_URL = os.getenv("PAYMENT_URL","http://payment-service:8003")

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    try: yield conn
    finally:
        conn.commit(); conn.close()

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS orders(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          items TEXT NOT NULL,
          total REAL NOT NULL,
          status TEXT NOT NULL
        )""")
init_db()

app = FastAPI(title=SERVICE)

@app.middleware("http")
async def metrics_mw(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    dur = time.perf_counter() - start
    REQ_COUNT.labels(SERVICE, request.url.path, request.method, str(response.status_code)).inc()
    REQ_LAT.labels(SERVICE, request.url.path, request.method).observe(dur)
    return response

class Item(BaseModel):
    product_id: int
    qty: int

class OrderIn(BaseModel):
    items: list[Item]

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def auth_user(authorization: str | None):
    if not authorization: raise HTTPException(401,"Missing Authorization")
    r = session.get(f"{USER_URL}/auth/introspect", headers={"Authorization": authorization}, timeout=5)
    if r.status_code != 200: raise HTTPException(401,"Invalid token")
    return r.json()

@app.post("/orders")
def create_order(body: OrderIn, authorization: str | None = Header(None)):
    user = auth_user(authorization)
    uid = user["user_id"]

    total = 0.0
    for it in body.items:
        pr = session.get(f"{PRODUCT_URL}/products/{it.product_id}", timeout=5)
        if pr.status_code != 200:
            raise HTTPException(404, f"Product {it.product_id} not found")
        pdata = pr.json()
        total += pdata["price"] * it.qty

    idem = str(uuid4())
    pay = session.post(f"{PAYMENT_URL}/pay",
                       json={"amount": round(total,2), "currency": "INR", "source": "card_demo"},
                       headers={"X-Idempotency-Key": idem},
                       timeout=5)
    if pay.status_code != 200:
        raise HTTPException(402, "Payment failed")

    for it in body.items:
        rv = session.post(f"{PRODUCT_URL}/reserve", json={"product_id": it.product_id, "qty": it.qty}, timeout=5)
        if rv.status_code != 200:
            raise HTTPException(409, f"Stock issue for product {it.product_id}")

    with db() as conn:
        conn.execute("INSERT INTO orders(user_id,items,total,status) VALUES(?,?,?,?)",
                     (uid, json.dumps([i.model_dump() for i in body.items]), round(total,2), "CONFIRMED"))
        rowid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return {"order_id": rowid, "total": round(total,2), "status":"CONFIRMED"}
