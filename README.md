# RAGged

Personal document Q&A: register, create a thread, upload PDF/DOCX/TXT/RTF, ask questions against **that thread**. One public HTTP port via Docker Compose.

This is a Compose app: FastAPI (`api/`), Webpack React (`web/`), Postgres/pgvector. There is no Vite or Supabase runtime.

## Quick start

Prerequisites: Docker. A chat API key (OpenAI, [xAI/Grok](https://console.x.ai), or [Anthropic](https://console.anthropic.com)) is needed to **answer** questions. Uploads embed on-server with a local MiniLM model and do not need a cloud key.

```bash
cp .env.example .env
# set JWT_SECRET (and optionally OPENAI_API_KEY / XAI_API_KEY / ANTHROPIC_API_KEY)
docker compose up --build
```

Open **http://localhost:8080/**. Register, paste keys under **API keys**, create a thread, upload a file, ask a question.

Health: `GET http://localhost:8080/api/health` → `{"status":"ok"}`.

Compose builds `DATABASE_URL` from `POSTGRES_*`. Do not set `DATABASE_URL`, `VITE_*`, or `NEXT_PUBLIC_*`.

## Environment

| Variable | Purpose |
| --- | --- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Database; Compose interpolates these into `DATABASE_URL` |
| `JWT_SECRET` | ≥ 32 characters |
| `OPENAI_API_KEY` | Optional operator fallback for OpenAI **chat**. Users can also paste keys in the UI |
| `XAI_API_KEY` | Optional operator fallback for Grok chat |
| `ANTHROPIC_API_KEY` | Optional operator fallback for Claude chat |
| `EMBEDDING_PROVIDER` | `local` (default) or `stub` (tests). Local = `all-MiniLM-L6-v2` (384-d) |
| `COOKIE_SECURE` | `false` on HTTP. Set `true` behind TLS |
| `PUBLIC_ORIGINS` | CSRF Origin allowlist. Default: `http://localhost:8080,http://localhost:3000` |
| `CORS_ORIGINS` | Leave empty (CORS off). Do not set `*` |

Production: set `PUBLIC_ORIGINS` to the TLS origin (e.g. `https://ragged.example`) and `COOKIE_SECURE=true`.

## Dev overlay (optional)

Host webpack-dev-server on **:3000**, API published on **:8001** (host `:8000` is often taken):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
cd web && npm install && npm run dev
```

The SPA you dogfood is still nginx at **http://localhost:8080/** unless you are iterating on webpack.

## Tests

```bash
python3 -m venv api/.venv
source api/.venv/bin/activate
pip install -r api/requirements-dev.txt
pytest                 # unit
pytest -m uat          # Compose
pytest -m dogfood      # live walkthrough
cd web && npm test     # Jest
```

## Smoke (live chat key)

Requires a real OpenAI, xAI, or Anthropic key in the environment or `.env` for the **in-corpus answer**. Upload uses local embeddings. No mock mode. CI without a key should skip this script.

```bash
./scripts/smoke.sh
```

Hits health, register, thread, upload `api/tests/fixtures/sample.pdf`, an in-corpus query, and an out-of-corpus refusal.

## Docker and volumes

All app data lives in **named Docker volumes**, not in the git checkout. The same Compose file works on any machine with Docker; you do not depend on a host path like `./data/uploads`.

| Volume | Service mount | Contents |
| --- | --- | --- |
| `pgdata` | `db` → `/var/lib/postgresql/data` | Users, threads, chat, extracted text, embeddings |
| `uploads` | `api` → `/data/uploads` | Original PDFs/DOCX/TXT/RTF |

Compose names them with the project directory, usually `ragged_pgdata` and `ragged_uploads` (`docker volume ls`).

### Commands that keep data

These recreate **containers and images** only. Volumes stay.

```bash
docker compose up --build          # start or rebuild images, keep volumes
docker compose up -d --build       # same, detached
docker compose down                # stop and remove containers; keep volumes
docker compose restart             # restart containers
docker compose build --no-cache    # rebuild images; does not delete volumes
docker image prune                 # unused images only
docker system prune                # unused images/networks; volumes kept unless you pass --volumes
```

### Commands that delete papers and the database

```bash
docker compose down -v             # remove containers AND volumes
docker volume rm ragged_pgdata ragged_uploads
docker volume prune                # unused volumes
docker system prune --volumes      # includes unused volumes
```

Do not use `-v` / `--volumes` / `volume prune` if you want to keep chats and uploads.

### Backups

Nightly dump of both volumes:

```bash
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > ragged-$(date +%F).sql
docker compose exec -T api tar -C /data/uploads -czf - . > uploads-$(date +%F).tar.gz
```

Restore SQL with `docker compose exec -T db psql -U "$POSTGRES_USER" "$POSTGRES_DB" < ragged-YYYY-MM-DD.sql`. Restore uploads by unpacking the tarball into the `uploads` volume (for example `docker compose exec -T api tar -C /data/uploads -xzf - < uploads-YYYY-MM-DD.tar.gz`).

### TLS

Compose v1 is HTTP on `:8080`. Put Caddy, Traefik, or a cloud load balancer in front; then set `COOKIE_SECURE=true` and `PUBLIC_ORIGINS` to the `https://` origin.

## What this app does not do

Cross-thread search, chat-history vectorization, client-chosen model/temperature, OAuth, sharing, or Kubernetes.
