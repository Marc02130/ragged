# Integration Guide

RAGged is a same-origin Docker Compose application:

```text
Browser
  └─ http://host:8080
       └─ nginx (Webpack React build)
            ├─ /          static SPA
            └─ /api/*     FastAPI
                             └─ PostgreSQL + pgvector
```

There is no Supabase, Deno, Vite, or client-side database runtime.

## Components

- `web/`: React + TypeScript, built with Webpack and served by nginx.
- `api/`: FastAPI, SQLAlchemy, Alembic, local file extraction, local embeddings, and chat-provider calls.
- PostgreSQL 16 + pgvector: users, sessions' backing users, threads, messages, document metadata/content, and vectors.
- `uploads` volume: original files under user/thread-specific server paths.

The browser calls relative `/api` URLs and sends the HTTP-only session cookie with every request. nginx proxies those requests to FastAPI.

## Main flow

1. Register or log in through `/api/auth/*`.
2. Create a thread with `POST /api/threads`.
3. Upload PDF, DOCX, TXT, or RTF files to `/api/threads/{thread_id}/documents`.
4. FastAPI validates quotas and file signatures, saves each file, extracts text, drops junk chunks, embeds retained chunks in batches of 32, and stores pgvector rows.
5. Ask a question through `/api/threads/{thread_id}/messages`.
6. FastAPI rewrites and expands the query when a chat key is available, retrieves only that thread's chunks, generates a grounded response, and saves both messages.

## Upload integration

The API accepts multiple `files` parts in one multipart request. The current React UI deliberately sends selected files one at a time, sequentially, so each file gets independent progress and error state.

The returned document status is authoritative:

- `ready`: extraction and embedding succeeded;
- `failed`: inspect `error_message`;
- `processing`: transient while ingest is active; a row older than ten minutes is marked failed when documents are listed or fetched.

An all-failed API batch returns `422`. A mixed batch returns `201` and includes both ready and failed rows. The UI counts `ready` rows rather than treating every `201` as success.

## Chat provider integration

Embeddings are local and require no cloud key. Query rewrite, optional retrieval grading, and final answers use one selected provider:

- OpenAI;
- xAI through its OpenAI-compatible endpoint;
- Anthropic Messages API.

Users can store encrypted provider keys through `/api/settings/llm`; operator environment keys act as fallback values. The API response exposes only configured booleans, provider choice, and model names.

## Thread lifecycle

Archiving changes a thread's status and hides it from the default list. Restoring makes it active again. Deleting a thread permanently cascades its database data and removes its upload directory. Deletion does not archive or vectorize conversation history.

## Development

The production-like stack:

```bash
cp .env.example .env
docker compose up --build
```

Optional host frontend development:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
cd web
npm install
npm run dev
```

webpack-dev-server runs on `http://localhost:3000`; the overlay publishes FastAPI on host port `8001`. See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production settings.
