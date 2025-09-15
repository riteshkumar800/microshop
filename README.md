Microshop — tiny microservices demo (FastAPI + Nginx + Postgres)


Microshop is a minimal e-commerce backend made of 4 FastAPI services behind an Nginx gateway, with a lightweight static web UI. It’s intentionally small, easy to read, and trivial to run locally in Docker (single image).

TL;DR (run in ~60s)
# 0) (first time) create a docker network
docker network create microshop-net 2>/dev/null || true

# 1) Postgres
docker rm -f product-db 2>/dev/null || true
docker run -d --name product-db --network microshop-net \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=productdb \
  -p 5433:5432 postgres:15

# 2) App
docker rm -f microshop-onebox 2>/dev/null || true
docker build -t microshop-onebox .
docker run -d --name microshop-onebox --network microshop-net \
  -p 8081:80 \
  -e DATABASE_URL=postgresql://postgres:postgres@product-db:5432/productdb \
  -e DB_URL=postgresql://postgres:postgres@product-db:5432/productdb \
  -e PRODUCT_DB_URL=postgresql://postgres:postgres@product-db:5432/productdb \
  -e PRODUCT_URL=http://127.0.0.1:8000 \
  -e USER_URL=http://127.0.0.1:8001 \
  -e PAYMENT_URL=http://127.0.0.1:8003 \
  microshop-onebox

# 3) Open UI
open http://localhost:8081   # (mac)  or xdg-open / start on linux/windows


Prefer a free cloud DB? Use Neon and set DATABASE_URL etc. to …?sslmode=require.

What’s inside

product-service — products CRUD + reserve

user-service — register/login/JWT introspect

order-service — creates orders (requires JWT), talks to product & payment

payment-service — fake, idempotent /pay

gateway — Nginx reverse proxy at /api/* + static UI at /

Stack: Python 3.11 · FastAPI · Uvicorn · SQLAlchemy · Nginx · PostgreSQL

Browser → Nginx (/ and /api/*) → product-service
                            ├→ user-service
                            ├→ order-service
                            └→ payment-service
                      ↳ PostgreSQL (single DB for demo)

One-minute smoke test (cURL)
BASE=http://localhost:8081

# Products
curl -s $BASE/api/products/products | jq .
curl -s -X POST $BASE/api/products/products -H 'Content-Type: application/json' \
  -d '{"name":"Keyboard","price":999,"stock":5}' | jq .

# Auth
curl -s -X POST $BASE/api/users/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"secret"}' | jq .
TOKEN=$(curl -s -X POST $BASE/api/users/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"secret"}' | jq -r .token)

# Order (product_id 1 if it’s your first product)
curl -s -X POST $BASE/api/orders/orders \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"user_id":1,"items":[{"product_id":1,"qty":1}]}' | jq .

# Pay (fake, idempotent)
curl -s -X POST $BASE/api/payments/pay -H 'Content-Type: application/json' \
  -H "X-Idempotency-Key: pay-$(date +%s)" \
  -d '{"order_id":"1","amount":999,"method":"card"}' | jq .


The web UI is at http://localhost:8081
 (register, login, add products, cart, place order).

API (via gateway)

Products

GET /api/products/products — list

POST /api/products/products — { name, price, stock }

POST /api/products/reserve — { product_id, qty }

Users

POST /api/users/auth/register — { email, password }

POST /api/users/auth/login — { email, password } → { token }

GET /api/users/auth/introspect — Authorization: Bearer <token>

Orders

POST /api/orders/orders — Authorization: Bearer <token>, body { user_id, items:[{product_id, qty}] }

Payments

POST /api/payments/pay — idempotent with X-Idempotency-Key

Health: GET /api/{products|users|orders|payments}/healthz → { "ok": true }.

Env vars
var	purpose	example
DATABASE_URL	Postgres DSN (used by services)	postgresql://postgres:postgres@product-db:5432/productdb
DB_URL	same as above	same
PRODUCT_DB_URL	same as above (product service)	same
PRODUCT_URL	internal product-service URL	http://127.0.0.1:8000
USER_URL	internal user-service URL	http://127.0.0.1:8001
PAYMENT_URL	internal payment-service URL	http://127.0.0.1:8003

Cloud DBs like Neon must end with ?sslmode=require.

Repo layout
.
├─ product-service/
├─ user-service/
├─ order-service/
├─ payment-service/
├─ ui/
│  └─ index.html
├─ nginx.conf.template
├─ supervisord.conf
├─ run-uvicorn.sh
├─ start.sh
├─ Dockerfile
└─ scripts/
   └─ smoke.sh

Screenshots

Add your screenshots to docs/ and link them here.

UI landing: docs/ui.png
![UI](docs/ui.png)

cURL smoke test: docs/smoke.png
![Smoke](docs/smoke.png)

Troubleshooting

Only /api/users/healthz is 200 → Use a real Postgres DSN. Check docker logs microshop-onebox.

Order 500 → order-service couldn’t introspect token. Ensure USER_URL=http://127.0.0.1:8001 is set on the container.

Neon → Don’t forget ?sslmode=require.

Port busy → Change host port: -p 9090:80.

Highlights (for reviewers)

End-to-end microservices demo: auth, inventory, orders, payments.

Real concerns baked in: JWT auth + idempotent payments + reverse proxy.

Zero-friction local run: single Docker image spins up Nginx + all services.

Small, readable code with FastAPI.

License

MIT

scripts/smoke.sh
#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://localhost:8081}"

echo "== health =="
for s in products users orders payments; do
  printf "%-9s: " "$s"
  curl -sf "$BASE/api/$s/healthz" >/dev/null && echo "ok" || echo "fail"
done

echo "== seed product =="
curl -s -X POST "$BASE/api/products/products" -H 'Content-Type: application/json' \
  -d '{"name":"Keyboard","price":999,"stock":5}' | jq .

echo "== register/login =="
curl -s -X POST "$BASE/api/users/auth/register" -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"secret"}' | jq .
TOKEN=$(curl -s -X POST "$BASE/api/users/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"secret"}' | jq -r .token)
echo "token: ${TOKEN:0:16}..."

echo "== order =="
curl -s -X POST "$BASE/api/orders/orders" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"user_id":1,"items":[{"product_id":1,"qty":1}]}' | jq .

echo "== pay =="
curl -s -X POST "$BASE/api/payments/pay" -H 'Content-Type: application/json' \
  -H "X-Idempotency-Key: pay-$(date +%s)" \
  -d '{"order_id":"1","amount":999,"method":"card"}' | jq .


Make it executable:

chmod +x scripts/smoke.sh

.env.example
DATABASE_URL=postgresql://postgres:postgres@product-db:5432/productdb
DB_URL=${DATABASE_URL}
PRODUCT_DB_URL=${DATABASE_URL}

PRODUCT_URL=http://127.0.0.1:8000
USER_URL=http://127.0.0.1:8001
PAYMENT_URL=http://127.0.0.1:8003
