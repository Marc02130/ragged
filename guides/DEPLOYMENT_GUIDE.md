# Deployment Guide

RAGged deploys as three Docker Compose services: nginx/React, FastAPI, and PostgreSQL/pgvector.

## Requirements

- Docker with Compose v2
- A host with persistent Docker volumes
- At least one OpenAI, xAI, or Anthropic key if users will not supply their own chat keys

Embeddings run locally in the API container. The first model initialization may download model assets during the image build/runtime environment.

## Configure

```bash
cp .env.example .env
```

Set at minimum:

```dotenv
POSTGRES_USER=ragged
POSTGRES_PASSWORD=replace-with-a-strong-password
POSTGRES_DB=ragged
JWT_SECRET=replace-with-at-least-32-random-characters
COOKIE_SECURE=false
PUBLIC_ORIGINS=http://localhost:8080
```

`docker-compose.yml` constructs `DATABASE_URL`; do not add it to `.env`. Do not add `VITE_*`, `NEXT_PUBLIC_*`, or Supabase variables.

Optional operator-wide chat fallbacks are `OPENAI_API_KEY`, `XAI_API_KEY`, and `ANTHROPIC_API_KEY`. Users can instead enter keys in **API keys**.

## Start

```bash
docker compose up -d --build
docker compose ps
curl http://localhost:8080/api/health
curl http://localhost:8080/api/ready
```

The API container runs Alembic migrations before starting two Uvicorn workers. `/api/health` is liveness; `/api/ready` also checks PostgreSQL.

## TLS and origins

The included nginx listens on HTTP port `8080`. Put a TLS proxy or load balancer in front, then set:

```dotenv
COOKIE_SECURE=true
PUBLIC_ORIGINS=https://ragged.example
```

`PUBLIC_ORIGINS` protects state-changing cookie-authenticated requests. It must be a nonempty comma-separated allowlist and cannot contain `*`.

Leave `CORS_ORIGINS` empty for same-origin deployment. Set explicit origins only when a separate trusted frontend needs cross-origin API access; wildcard CORS is rejected.

## Persistent data

| Volume | Contents |
| --- | --- |
| `pgdata` | PostgreSQL data, including users, messages, extracted content, and vectors |
| `uploads` | Original uploaded files |

Normal rebuilds and `docker compose down` preserve both volumes. `docker compose down -v`, `docker volume prune`, and `docker system prune --volumes` can destroy data.

## Backup and restore

```bash
docker compose exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > ragged-$(date +%F).sql

docker compose exec -T api \
  tar -C /data/uploads -czf - . > uploads-$(date +%F).tar.gz
```

Restore the database:

```bash
docker compose exec -T db \
  psql -U "$POSTGRES_USER" "$POSTGRES_DB" < ragged-YYYY-MM-DD.sql
```

Restore files:

```bash
docker compose exec -T api \
  tar -C /data/uploads -xzf - < uploads-YYYY-MM-DD.tar.gz
```

Back up both artifacts together so database paths and uploaded files remain consistent.

## Updating

```bash
git pull
docker compose up -d --build
```

Review new environment variables and migrations before updating production. The API applies committed Alembic migrations automatically on startup.

## Operational checks

```bash
docker compose ps
docker compose logs api
docker compose logs web
docker compose logs db
docker compose exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

Upload limits and retrieval settings are defined in `api/app/config.py`. Scale tests should account for synchronous extraction/embedding work and the two configured API workers.

## Development overlay

For webpack development on port `3000` and direct API access on host port `8001`:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
cd web && npm install && npm run dev
```

The nginx SPA remains available on port `8080`.
