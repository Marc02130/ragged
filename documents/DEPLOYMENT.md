# RAGged Deployment

The supported deployment is Docker Compose. FastAPI, Webpack React/nginx, and PostgreSQL/pgvector are built and run together; Supabase, Deno, and Vite are not deployment dependencies.

For complete commands, TLS settings, backups, updates, and health checks, see [../guides/DEPLOYMENT_GUIDE.md](../guides/DEPLOYMENT_GUIDE.md).

## Minimal deployment

```bash
git clone https://github.com/Marc02130/ragged.git
cd ragged
cp .env.example .env
# Edit POSTGRES_PASSWORD and JWT_SECRET.
docker compose up -d --build
curl -f http://localhost:8080/api/health
curl -f http://localhost:8080/api/ready
```

Open `http://localhost:8080`.

## Services

| Service | Role | Published port |
| --- | --- | --- |
| `web` | nginx serving the Webpack SPA and proxying `/api` | `8080` |
| `api` | Alembic migrations and two Uvicorn workers | internal `8000` |
| `db` | PostgreSQL 16 with pgvector | internal `5432` |

Only nginx is published by the base Compose file.

## Required production changes

```dotenv
POSTGRES_PASSWORD=<strong unique value>
JWT_SECRET=<at least 32 random characters>
COOKIE_SECURE=true
PUBLIC_ORIGINS=https://ragged.example
CORS_ORIGINS=
```

Terminate TLS in a reverse proxy or load balancer in front of port `8080`. Keep PostgreSQL and FastAPI on the private Compose network.

The app needs a chat-provider key to rewrite and answer questions. Set an operator fallback (`OPENAI_API_KEY`, `XAI_API_KEY`, or `ANTHROPIC_API_KEY`) or have each user configure a key in the UI. Local document embeddings do not use those keys.

## State and migration

The `pgdata` and `uploads` named volumes are both required for a complete restore. API startup runs `alembic upgrade head`; inspect migration changes before deploying a new image.

Do not run Supabase migrations, create storage buckets, deploy Edge Functions, or build a Vite frontend. Those commands belong to an earlier design and do not operate this repository's current application.
