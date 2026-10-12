# ecom-microservices

A small e-commerce backend split into three services, built by hand to learn how REST APIs, inter-service calls, containers and Kubernetes actually work.

Status: three services working, containerized, and run together with Docker Compose. Kubernetes and AWS deployment are next.

## Architecture

```
client (curl / browser)
   |
   +--> user-service     :8000  --> users_db
   +--> product-service  :8001  --> products_db
   +--> order-service    :8002  --> orders_db
                 |
                 +--> product-service (REST: get product, reduce stock)

all three databases live in one Postgres container
```

- **user-service**: register, login, current user. Issues JWT tokens.
- **product-service**: product catalog and atomic stock reduction.
- **order-service**: creates orders. Verifies the user's JWT, calls product-service over REST for price and stock, then saves the order.
- Each service owns its own database. Services never read each other's tables, only each other's APIs.

## Tech stack

- Python 3.11, FastAPI, SQLAlchemy, Pydantic
- PostgreSQL 16
- PyJWT and bcrypt (auth)
- httpx (service-to-service calls)
- Docker and Docker Compose
- Planned: Kubernetes (kind), AWS

## Project structure

```
ecom-microservices/
  docker-compose.yml
  db-init/init.sql          creates users_db, products_db, orders_db on first start
  smoke_test.sh             end-to-end checks against the running services
  user-service/
    app/ (main, database, models, schemas, security)
    Dockerfile
    requirements.txt
    .env.example
  product-service/
    app/ (main, database, models, schemas, security)
    Dockerfile
    seed.sh                 sample products
    requirements.txt
    .env.example
  order-service/
    app/ (main, database, models, schemas, auth, clients)
    Dockerfile
    requirements.txt
    .env.example
  NOTES.md                  my running learning notes
```

## Configuration

Each service reads its own `.env` file (never committed). Copy each `.env.example` to `.env` and fill in values.

- user-service: `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`
- product-service: `DATABASE_URL`, `INTERNAL_API_KEY`
- order-service: `DATABASE_URL`, `PRODUCT_SERVICE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `INTERNAL_API_KEY`

Rules:
- `JWT_SECRET` must be identical in user-service and order-service.
- `INTERNAL_API_KEY` must be identical in product-service and order-service.
- Generate secrets with `python3 -c "import secrets; print(secrets.token_hex(32))"`.
- In Docker Compose, `DATABASE_URL` and `PRODUCT_SERVICE_URL` are overridden to use service names (`postgres`, `product-service`), so the same `.env` files also work for running a service locally with uvicorn.

## Run with Docker Compose

Requirements: Docker Desktop, and port 5432 free on your machine.

```bash
docker compose up --build -d
docker compose ps
./product-service/seed.sh        # add sample products
./smoke_test.sh                  # 15 end-to-end checks
```

Useful commands:

```bash
docker compose logs -f order-service     # follow one service's logs
docker compose down                      # stop, keep database data
docker compose down -v                   # stop and delete database data
docker compose up -d --build order-service   # rebuild one service after a code change
```

After editing a `.env` file, recreate the containers: `docker compose up -d --force-recreate`.

## Run a single service locally (without Docker)

```bash
cd user-service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

This needs a running Postgres with the three databases created. Use ports 8000, 8001 and 8002 for user, product and order service.

## API overview

Interactive docs for each service are at `/docs` (for example http://localhost:8000/docs).

user-service (8000)
- `POST /register` create an account
- `POST /login` get a JWT access token
- `GET /me` current user (Bearer token)
- `GET /health`

product-service (8001)
- `GET /products` list products (`limit`, `offset`)
- `GET /products/{id}`
- `POST /products` create a product
- `POST /products/{id}/reduce-stock` atomically reduce stock (requires the `X-Internal-Key` header, used by order-service)
- `GET /health`

order-service (8002)
- `POST /orders` place an order (Bearer token)
- `GET /orders` my orders
- `GET /orders/{id}` one of my orders
- `GET /health`

Example flow:

```bash
curl -X POST localhost:8000/register -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","name":"Me","password":"password123"}'

TOKEN=$(curl -s -X POST localhost:8000/login -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","password":"password123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST localhost:8002/orders -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"product_id":1,"quantity":2}'
```

## Design decisions

- **One database per service, no cross-service foreign keys.** Orders store plain `user_id` and `product_id` values.
- **Passwords are hashed with bcrypt**, and the hash is never returned by any endpoint.
- **JWT is verified by each service itself** using a shared secret, so no service has to call user-service on every request. The user id comes from the token, never from the request body.
- **Stock reduction is one atomic SQL statement** (`UPDATE ... WHERE stock >= quantity`), so concurrent orders can never oversell. Verified with 20 parallel requests against 5 units: exactly 5 succeed.
- **Order flow:** look up the product, save the order as `PENDING`, reduce stock, then mark it `CONFIRMED` or `FAILED`. This keeps a record even if something fails halfway.
- **Order price is copied onto the order** (`unit_price`), so later price changes don't rewrite history.
- **A timeout while reducing stock leaves the order `PENDING`**, because the outcome is unknown (the stock may or may not have been reduced).
- **Service-to-service auth:** `reduce-stock` requires an internal API key, compared in constant time. A failure with that key is reported to the user as 503, not 401, since it is a configuration problem and not the user's fault.
- **Status codes:** 404 product not found, 409 insufficient stock, 503 product-service unavailable, 504 product-service timed out.

## Known limitations

- `POST /products` is not authenticated yet (no admin role).
- A timed-out order stays `PENDING`; nothing reconciles it yet.
- No idempotency keys, so retrying a request can create a duplicate order.
- No order cancellation, so stock cannot be returned.
- Tables are created at startup with `create_all`; there are no migrations.
- Services crash at startup if the database isn't reachable (no retry loop).
- Containers run as root.
- No automated unit tests; `smoke_test.sh` is the only check.

## Roadmap

1. Kubernetes locally with kind: Deployments, Services, ConfigMap, Secret, Postgres with a persistent volume, readiness and liveness probes
2. Failure experiments: delete pods, CrashLoopBackOff, scaling, rolling updates
3. Deploy to AWS
4. Later: cart service, payment (mock), API gateway, CI with GitHub Actions, monitoring
