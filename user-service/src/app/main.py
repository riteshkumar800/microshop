from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import sqlite3, os, time, hashlib
from contextlib import contextmanager
from starlette.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import jwt

SERVICE = "user-service"
REQ_COUNT = Counter("http_requests_total", "HTTP requests", ["service","path","method","code"])
REQ_LAT = Histogram("http_request_duration_seconds", "Latency", ["service","path","method"])

DB_PATH = "users.db"
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGO = "HS256"
TOKEN_TTL = 3600

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    try: yield conn
    finally:
        conn.commit(); conn.close()

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL
        )""")
init_db()

def hash_pw(pw: str): return hashlib.sha256(pw.encode()).hexdigest()

app = FastAPI(title=SERVICE)

@app.middleware("http")
async def metrics_mw(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    dur = time.perf_counter() - start
    REQ_COUNT.labels(SERVICE, request.url.path, request.method, str(response.status_code)).inc()
    REQ_LAT.labels(SERVICE, request.url.path, request.method).observe(dur)
    return response

class RegisterIn(BaseModel):
    email: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/auth/register")
def register(body: RegisterIn):
    with db() as conn:
        try:
            conn.execute("INSERT INTO users(email,password_hash) VALUES(?,?)",(body.email,hash_pw(body.password)))
        except sqlite3.IntegrityError:
            raise HTTPException(409,"Email already exists")
    return {"registered": True}

@app.post("/auth/login")
def login(body: LoginIn):
    with db() as conn:
        row = conn.execute("SELECT id,password_hash FROM users WHERE email=?", (body.email,)).fetchone()
    if not row or row[1] != hash_pw(body.password):
        raise HTTPException(401,"Invalid credentials")
    uid = row[0]
    now = int(time.time())
    token = jwt.encode({"sub": uid,"email": body.email,"iat": now,"exp": now+TOKEN_TTL}, JWT_SECRET, algorithm=JWT_ALGO)
    return {"token": token}

@app.get("/auth/introspect")
def introspect(authorization: str | None = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401,"Missing token")
    token = authorization.split(" ",1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception:
        raise HTTPException(401,"Invalid token")
    return {"active": True, "user_id": payload["sub"], "email": payload["email"], "exp": payload["exp"]}
