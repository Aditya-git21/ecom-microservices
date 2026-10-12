# Notes: after the 3 services were running

Raw notes, Oct 2026. Written for me, not polished.

## Where I am
- user, product, order services work (ports 8000, 8001, 8002), each with its own DB inside one Postgres
- smoke_test.sh passes all 15 checks, locally and against Docker Compose
- next: Kubernetes (kind), then AWS

## Protecting product-service
- reduce-stock now needs an X-Internal-Key header (service-to-service key)
- POST /products is still open (todo: JWT check)
- INTERNAL_API_KEY lives in product-service/.env and order-service/.env, values must be identical
- compare with secrets.compare_digest (constant-time compare, no timing leaks)
- Header(default=None) reads a header. x_internal_key in Python = X-Internal-Key on the wire
- BUG: two @app.post decorators stacked on one function. The old unprotected one won, so the key check never ran and all three test curls returned 200. Fix: delete the old decorator. Lesson: always test the negative case (no key must give 401) and check the route definition
- BUG: curl HTTP 000 means no response at all, the service was not running. Check the process first, then debug the request
- BUG: orders returned 503. Order-service loaded the key but never sent it. Product-service logs showed 401 on reduce-stock. Both keys matched (I compared a shasum of each value so the secret was never printed). Fix: headers={"X-Internal-Key": INTERNAL_API_KEY} inside reduce_stock in clients.py, then rebuild the image
- a 401 from product-service is turned into a 503 for the user (it's my config error, not theirs). The order is saved as FAILED
- Lesson: when I add protection on one service, test the caller end to end right away

## Docker basics
- Dockerfile = recipe, image = built result, container = a running image
- docker build -t name:tag ./folder. The folder is the build context. COPY can only see inside it
- copy requirements.txt first, run pip install, then copy the code. Code edits then reuse the cached pip layer (saw CACHED)
- .dockerignore has .venv, __pycache__, .env, .git so secrets never get baked into an image
- uvicorn needs --host 0.0.0.0 inside a container, otherwise nothing outside can reach it
- EXPOSE is only documentation. -p host:container is what publishes a port
- localhost inside a container means that container itself. Postgres on my Mac's localhost:5432 gives "connection refused" from inside the container
- quick fix: host.docker.internal (means my Mac). Real fix: Compose service names
- docker run -d --rm --name x -p 8000:8000 --env-file path -e KEY=val image
- -e overrides --env-file
- Ctrl+C in a foreground container stops it, and --rm deletes it. Use -d to keep the terminal free
- image is about 388MB on disk (Debian base ~110MB, pip install ~135MB)
- containers run as root by default (todo: add a non-root user)
- image uses python:3.11-slim, my local venv is 3.10. Works, but try to match them

## Docker Compose
- one file, one command: docker compose up --build -d
- services reach each other by service name: postgres:5432 and http://product-service:8001 (Compose network DNS)
- env_file loads each service's .env. environment: overrides DATABASE_URL and PRODUCT_SERVICE_URL, so the .env files still work for local uvicorn
- ports "8000:8000" is host:container. Services talk over the internal network, ports are only so my Mac can reach them
- depends_on plus a healthcheck makes apps wait for Postgres (my apps crash at import if the DB isn't ready)
- the pg_isready healthcheck only says the server is up, not that my databases exist
- db-init/ is mounted at /docker-entrypoint-initdb.d. It runs only when the volume is empty
- commands: up, up --build, up -d, down, down -v, ps, logs -f <service>, exec <service> <cmd>, stop/start <service>
- down keeps the volume (data survives). down -v deletes it (data gone)
- changed .env? needs up -d --force-recreate (restart is not enough)
- changed code? needs --build, because code is copied into the image at build time
- use "docker compose" (new), not "docker-compose" (old)

## Errors I hit and the fixes
1. seed.sh had API_URL="http://127.0.0" (no port, no path). curl timed out. Fix: http://127.0.0.1:8001/products
2. zsh treats <id>, <token>, <generate ...> as redirects, not text. Replace placeholders with real values (no angle brackets)
3. zsh passes a trailing # comment as an argument when typed in the terminal (curl: no host part, grep: no such file #). Comments are safe inside script files only
4. role "aditya8050" does not exist: wrong DB user. The real one is whatever POSTGRES_USER was (postgres)
5. connection refused on 5432 (running locally): Postgres container wasn't running (Docker Desktop off or container stopped)
6. container got connection refused to localhost:5432: localhost inside a container. Used host.docker.internal
7. Compose: "ignoring /docker-entrypoint-initdb.d/init-sql". The file must end in .sql. Renamed to init.sql. Then needed down -v, because init scripts only run on an empty volume
8. users_db / products_db / orders_db does not exist: same cause as 7. Services exited with code 1 and docker compose ps showed only postgres
9. could not translate host name "postgres": services weren't on a working network after a couple of days. docker compose down then up recreated the network
10. Bind for 0.0.0.0:5432 failed: port is already allocated. The old standalone ecom-postgres container held 5432. Fix: docker stop ecom-postgres. Alternative: remove ports from postgres in compose, or map 5433:5432
11. Order returned 503: missing X-Internal-Key header (see the protection section)
12. logs from 3 services interleave and are unreadable. Use docker compose logs <service>

## Postgres error cheat sheet
- connection refused: server not running or wrong port
- database "x" does not exist: reached the server, DB never created
- could not translate host name: name doesn't resolve, wrong network
- role "x" does not exist: wrong user
- password authentication failed: server up, wrong credentials

## Reading HTTP results
- 000: no response, service down or wrong host/port
- 401 not logged in / bad token or key, 404 not found or wrong path, 405 wrong method
- 409 conflict (duplicate email, insufficient stock), 422 body failed validation
- 503 dependency unavailable (connection failed), 504 dependency timed out
- first thing to do on a 500 or 503: read that service's logs

## Experiments
- A: docker kill a container. It does NOT come back on its own. Compose without a restart policy doesn't heal anything. To compare later: a Kubernetes Deployment recreates the pod
- B: stopped product-service and tried an order. What I saw: "connecting but not receiving traffic". TODO confirm the exact status code, how long it took, and that no new row was saved in orders_db
- stress test: 20 parallel reduce-stock calls on stock 5 gave 5 x 200, 15 x 400, final stock 0. The atomic UPDATE ... WHERE stock >= qty works
- race through orders: one 201, one 409, stock 0. Not sure whether the pre-check or the atomic update caught it. Look for a FAILED row to find out

## Things I should be able to explain
- why one DB per service and no foreign keys across services
- why unit_price is stored on the order
- why the order is saved as PENDING before stock is reduced, and why a timeout leaves it PENDING (outcome unknown)
- why a 401 from product-service becomes a 503 for the user
- why wrong email and wrong password give the same 401
- JWT is signed, not encrypted. The payload is readable. Services verify with the shared secret
- running is not the same as ready (this becomes probes in Kubernetes)
- startup order: Compose has depends_on, Kubernetes doesn't (probes and retries instead)

## Still open
- JWT check on POST /products
- non-root user in the Dockerfiles
- smoke_test.sh: wait for health with a retry loop before testing
- cleanup or reconciliation of PENDING orders
- idempotency key so retries don't create duplicates
- confirm experiment B
- Kubernetes: kind, namespace, Secret, ConfigMap, Postgres with a PVC, Deployments, Services, probes, crash experiments
- AWS after that
