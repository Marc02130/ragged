# Troubleshooting

Start with service state and health:

```bash
docker compose ps
docker compose logs api
docker compose logs web
docker compose logs db
curl -i http://localhost:8080/api/health
curl -i http://localhost:8080/api/ready
```

## Startup validation fails

FastAPI validates configuration at import time.

- `JWT_SECRET must be at least 32 characters`: replace the placeholder with a longer random value.
- `PUBLIC_ORIGINS must be a non-empty allowlist without *`: set exact browser origins.
- `CORS_ORIGINS must not contain *`: remove wildcard CORS.
- Database connection errors: verify `POSTGRES_*` values and database health. Compose constructs `DATABASE_URL`; do not set a conflicting value in `.env`.

## Login works, but state-changing requests fail

Check the browser's public origin against `PUBLIC_ORIGINS`, including scheme and port. Behind TLS, set `COOKIE_SECURE=true`; on local HTTP, keep it `false`.

The client must send credentials. The checked-in web client uses `credentials: 'include'`.

## Upload rejected

| Status | Meaning |
| --- | --- |
| `413` | File, request body, thread count, thread bytes, or user bytes exceed a quota |
| `415` | File signature is not PDF, DOCX, TXT, or RTF |
| `422` | No files, or every file in the request failed ingest |

Use `GET /api/threads/{thread_id}/documents` and inspect `status`, `chunk_count`, and `error_message`.

Common failed messages:

- `empty extract`: parser found no text;
- `extracted text too large`: more than `MAX_CONTENT_CHARS`;
- `no usable text after dropping junk chunks`: every chunk matched junk filtering;
- `too many chunks`: more than `MAX_CHUNKS_PER_DOCUMENT`;
- `ingest timed out` or `ingest interrupted`: processing did not finish normally.

A mixed API batch can return `201` with both ready and failed documents. The current UI uploads files sequentially and reports each status.

## Document remains processing

Listing or fetching documents marks processing rows older than ten minutes as failed and removes their chunks. If a recent row remains processing, inspect API logs and worker health before retrying.

## Query returns the refusal

The refusal with `200` means retrieval retained no source chunks.

1. Confirm the document is `ready` and has chunks.
2. Confirm the question uses the same thread.
3. Confirm the document's `embedding_model` matches `EMBEDDING_MODEL`.
4. Review ingest and role filtering in `api/app/services/classify.py`.
5. Remember that citation and boilerplate are excluded unless explicitly requested.

RAGged does not search other threads or vectorized chat history and does not answer from general knowledge.

## Query returns `400`

The selected final-answer provider has no usable user or operator API key. Open **API keys**, configure the selected provider, or set its environment fallback.

Rewrite failures do not produce this status; rewrite is best effort and falls back to original-query retrieval.

## Embedding model mismatch

The current local model produces 384-dimensional vectors. Do not change `EMBEDDING_MODEL` or `EMBEDDING_DIM` independently on an existing database. Retrieval also filters by model name, so old rows remain invisible after a model-name change even if dimensions happen to match.

Restore the prior settings or plan a complete re-ingest/migration.

## Frontend development

The application uses Webpack, not Vite.

```bash
cd web
npm install
npm run dev
```

webpack-dev-server listens on `3000`. With `docker-compose.dev.yml`, FastAPI is published on host port `8001`; the nginx production build remains on `8080`.

## Data disappeared

Check whether a volume-destructive command was run:

- `docker compose down -v`
- `docker volume prune`
- `docker system prune --volumes`

Both `pgdata` and `uploads` are required for a full restore. A database-only restore can leave metadata pointing to missing originals; an uploads-only restore cannot recover users, threads, chunks, or messages.
