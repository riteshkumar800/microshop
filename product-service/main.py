from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os, sqlite3, requests, json
from contextlib import contextmanager
from uuid import uuid4

DB_PATH = "orders.db"
USER_URL = os.getenv("USER_URL", "http://user-service:8001")
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://product-service:8000")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://payment-service:8003")

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.commit(); conn.close()

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS orders(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          items TEXT NOT NULL, -- JSON
          total REAL NOT NULL,
          status TEXT NOT NULL
        )""")
init_db()

app = FastAPI(title="order-service")

class Item(BaseModel):
    product_id: int
    qty: int

class OrderIn(BaseModel):
    items: list[Item]

@app.get("/healthz")
def healthz():
    return {"ok": True}

def auth_user(authorization: str | None):
    if not authorization:
        raise HTTPException(401, "Missing Authorization")
    r = requests.get(f"{USER_URL}/auth/introspect", headers={"Authorization": authorization}, timeout=5)
    if r.status_code != 200:
        raise HTTPException(401, "Invalid token")
    return r.json()

@app.post("/orders")
def create_order(body: OrderIn, authorization: str | None = Header(None)):
    user = auth_user(authorization)
    uid = user["user_id"]

    # price cart
    total = 0.0
    for it in body.items:
        pr = requests.get(f"{PRODUCT_URL}/products/{it.product_id}", timeout=5)
        if pr.status_code != 200:
            raise HTTPException(404, f"Product {it.product_id} not found")
        pdata = pr.json()
        total += pdata["price"] * it.qty

    # charge (idempotent)
    idem = str(uuid4())
    pay = requests.post(f"{PAYMENT_URL}/pay",
                        json={"amount": round(total, 2), "currency": "INR", "source": "card_demo"},
                        headers={"X-Idempotency-Key": idem},
                        timeout=5)
    if pay.status_code != 200:
        raise HTTPException(402, "Payment failed")

    # reserve stock
    for it in body.items:
        rv = requests.post(f"{PRODUCT_URL}/reserve", json={"product_id": it.product_id, "qty": it.qty}, timeout=5)
        if rv.status_code != 200:
            raise HTTPException(409, f"Stock issue for product {it.product_id}")

    with db() as conn:
        conn.execute("INSERT INTO orders(user_id,items,total,status) VALUES(?,?,?,?)",
                     (uid, json.dumps([i.model_dump() for i in body.items]), round(total,2), "CONFIRMED"))
        rowid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    return {"order_id": rowid, "total": round(total,2), "status": "CONFIRMED"}
