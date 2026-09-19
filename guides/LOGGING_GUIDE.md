# Logging Guide

RAGged writes application logs to container stdout/stderr. It does not use Supabase Edge Function logs or a structured application logging service.

## View logs

```bash
docker compose logs api
docker compose logs web
docker compose logs db
docker compose logs -f api
```

FastAPI/Uvicorn access logs show request method, path, status, and timing information provided by the server. nginx logs browser requests and proxy errors. PostgreSQL logs database startup and server errors.

## Health checks

Use endpoints rather than log text for automated health monitoring:

```bash
curl -f http://localhost:8080/api/health  # process liveness
curl -f http://localhost:8080/api/ready   # includes SELECT 1 against PostgreSQL
```

Compose also defines health checks for PostgreSQL and FastAPI.

## Upload failures

Document ingest catches failures per file, stores `status="failed"` and an `error_message`, and continues with other files in the request. Inspect the API response or:

```http
GET /api/threads/{thread_id}/documents
GET /api/threads/{thread_id}/documents/{document_id}
```

Rows left in `processing` for more than ten minutes are marked failed the next time the thread's documents are listed or fetched.

An all-failed upload request returns `422` using the first failed row's message. A mixed result returns `201`, so monitoring should inspect document statuses rather than count only HTTP success codes.

## Query failures

- No retained sources is a normal `200` refusal, not a server error.
- A missing selected-provider key during final generation returns `400`.
- Rewrite and retrieval-grading provider failures intentionally degrade without a dedicated error response.
- Unhandled provider or database exceptions appear in API container logs and produce a server error.

## Sensitive data

Logs can contain request paths, document error messages, and exception text. Do not add API keys, session cookies, raw passwords, or full document/query content to logs. Restrict production log access and apply retention at the container platform or host level.
