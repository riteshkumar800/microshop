from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, time
import psycopg2
from contextlib import contextmanager
from starlette.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

SERVICE = "product-service"
REQ_COUNT = Counter("http_requests_total","HTTP requests",["service","path","method","code"])
REQ_LAT   = Histogram("http_request_duration_seconds","Latency",["service","path","method"])

DB_URL = os.getenv("DATABASE_URL","postgresql://product:product@product-db:5432/productdb")

@contextmanager
def db():
    conn = psycopg2.connect(DB_URL)
    try: yield conn
    finally: conn.commit(); conn.close()

def init_db():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
          CREATE TABLE IF NOT EXISTS products(
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            stock INTEGER NOT NULL
          )""")
init_db()

app = FastAPI(title=SERVICE)

@app.middleware("http")
async def metrics_mw(request, call_next):
    t = time.perf_counter()
    resp = await call_next(request)
    REQ_COUNT.labels(SERVICE, request.url.path, request.method, str(resp.status_code)).inc()
    REQ_LAT.labels(SERVICE, request.url.path, request.method).observe(time.perf_counter()-t)
    return resp

class ProductIn(BaseModel):
    name: str
    price: float
    stock: int

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/products")
def list_products():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id,name,price,stock FROM products ORDER BY id")
        rows = cur.fetchall()
    return [{"id":r[0],"name":r[1],"price":r[2],"stock":r[3]} for r in rows]

@app.get("/products/{pid}")
def get_product(pid: int):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id,name,price,stock FROM products WHERE id=%s",(pid,))
        row = cur.fetchone()
    if not row: raise HTTPException(404, "Product not found")
    return {"id":row[0],"name":row[1],"price":row[2],"stock":row[3]}

@app.post("/products")
def create_product(p: ProductIn):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO products(name,price,stock) VALUES(%s,%s,%s)", (p.name,p.price,p.stock))
    return {"created": True}

class ReserveIn(BaseModel):
    product_id: int
    qty: int

@app.post("/reserve")
def reserve(r: ReserveIn):
    with db() as conn:
        cur = conn.cursor()
        # atomic decrement if enough stock
        cur.execute("""
          UPDATE products
             SET stock = stock - %s
           WHERE id = %s AND stock >= %s
        RETURNING id
        """, (r.qty, r.product_id, r.qty))
        ok = cur.fetchone()
        if ok: return {"reserved": True}
        cur.execute("SELECT 1 FROM products WHERE id=%s",(r.product_id,))
        if not cur.fetchone(): raise HTTPException(404,"Product not found")
        raise HTTPException(409,"Insufficient stock")
