# RAGged HTTP API

All routes are under `/api`. The browser uses same-origin requests and an HTTP-only `ragged_session` cookie. JSON requests with a body use `Content-Type: application/json`; uploads use multipart form data.

Except for registration, login, logout, health, and readiness, routes require
a valid session cookie. A missing or invalid session returns `401`. Access to
an unknown or another user's thread is deliberately reported as `404`.

## Health

| Method | Path | Response |
| --- | --- | --- |
| `GET` | `/api/health` | `200 {"status":"ok"}` process liveness |
| `GET` | `/api/ready` | `200 {"status":"ok"}` after a PostgreSQL `SELECT 1` |

## Authentication

### `POST /api/auth/register`

```json
{"email":"user@example.com","password":"at-least-8-characters"}
```

Returns `201` with `{id, email, created_at}` and sets the session cookie. Emails are stored lowercase. Duplicate email returns `409`.

### `POST /api/auth/login`

Uses the same body. Returns `200` with the user and sets the cookie. Invalid credentials return `401`.

### `POST /api/auth/logout`

Returns `204` and clears the cookie.

### `GET /api/auth/me`

Returns the authenticated user.

## Threads

### `GET /api/threads`

Returns active threads ordered by recent activity. Add `?include_archived=true` to include archived threads.

Thread shape:

```json
{
  "id": "uuid",
  "title": "Research",
  "status": "active",
  "document_count": 2,
  "last_activity_at": "2026-09-19T20:00:00Z",
  "created_at": "2026-09-19T19:00:00Z",
  "updated_at": "2026-09-19T20:00:00Z"
}
```

### `POST /api/threads`

```json
{"title":"Research"}
```

Title length is 1–100 characters. Returns `201`.

### `POST /api/threads/{thread_id}/archive`

Sets status to `archived` and returns the thread.

### `POST /api/threads/{thread_id}/restore`

Sets status to `active` and returns the thread.

### `DELETE /api/threads/{thread_id}`

Returns `204`. The delete permanently cascades database records and removes the thread's uploaded-file directory. It does not create an archive.

## Documents

Document shape:

```json
{
  "id": "uuid",
  "thread_id": "uuid",
  "file_name": "paper.pdf",
  "file_size": 12345,
  "file_type": "application/pdf",
  "title": "paper.pdf",
  "status": "ready",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "chunk_count": 12,
  "error_message": null,
  "created_at": "2026-09-19T20:00:00Z",
  "updated_at": "2026-09-19T20:00:03Z"
}
```

Status is `processing`, `ready`, or `failed`.

### `GET /api/threads/{thread_id}/documents`

Returns documents in creation order. Before responding, processing rows older than ten minutes are marked failed.

### `GET /api/threads/{thread_id}/documents/{document_id}`

Returns one document. A document outside the route's thread/user scope returns `404`.

### `POST /api/threads/{thread_id}/documents`

Send one or more multipart fields named `files`:

```bash
curl -b cookies.txt \
  -F 'files=@paper.pdf' \
  -F 'files=@notes.txt' \
  http://localhost:8080/api/threads/THREAD_ID/documents
```

The server processes files sequentially and returns a list of document rows:

- `201`: at least one row is ready; the list can also contain failed rows.
- `422`: no files, or every created row failed ingest (for example, all text was junk).
- `413`: request/file/quota limit exceeded.
- `415`: unsupported file signature.

Supported content is PDF, DOCX, TXT, and RTF. Detection uses file bytes rather than trusting the uploaded MIME type. Default limits are 10 MiB per file, 20 ready/processing files and 50 MiB per thread, and 1 GiB per user.

### `DELETE /api/threads/{thread_id}/documents/{document_id}`

Returns `204`, deletes database chunks through cascade behavior, and removes the stored original file.

## Messages

### `GET /api/threads/{thread_id}/messages`

Returns messages in chronological order:

```json
{
  "id": "uuid",
  "role": "assistant",
  "content": "Grounded answer",
  "created_at": "2026-09-19T20:00:00Z",
  "sources": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "file_name": "paper.pdf",
      "content": "Retrieved text",
      "similarity": 0.72
    }
  ]
}
```

User messages and uncited assistant messages have empty source lists.

### `POST /api/threads/{thread_id}/messages`

```json
{"content":"What does the paper conclude?"}
```

Content length is 1–8000 characters. Returns:

```json
{
  "user_message": {"id":"uuid","role":"user","content":"...","created_at":"...","sources":[]},
  "assistant_message": {"id":"uuid","role":"assistant","content":"...","created_at":"...","sources":[]}
}
```

The server controls rewrite, retrieval, provider model, temperature, and result limits. No cross-thread, model, temperature, or search-strategy request options are accepted.

No retrieval results is a successful `200` containing a saved canned refusal.
If retrieval succeeds but the selected provider has no usable user or operator
key, the current implementation instead returns `200` with assistant content
`Answer based on SOURCES.` and the retrieved sources attached.

## LLM settings

### `GET /api/settings/llm`

Returns configured flags, selected provider, and fixed model names. Secret values are never returned:

```json
{
  "openai": {"configured": true},
  "xai": {"configured": false},
  "anthropic": {"configured": false},
  "chat_provider": "openai",
  "chat_models": {
    "openai": "gpt-4o-mini",
    "xai": "grok-4.5",
    "anthropic": "claude-sonnet-4-5"
  }
}
```

### `PUT /api/settings/llm`

All fields are optional:

```json
{
  "openai_api_key": "sk-...",
  "xai_api_key": "",
  "anthropic_api_key": "",
  "chat_provider": "openai"
}
```

Keys are encrypted before database storage. An empty key clears that user's saved key. Unsupported providers or unusable updates return `422`.

## Origin protection and errors

State-changing cookie-authenticated requests are checked against `PUBLIC_ORIGINS`. Cross-origin browser access is disabled unless explicit `CORS_ORIGINS` are configured.

FastAPI errors use:

```json
{"detail":"Human-readable message"}
```

Validation errors use FastAPI's standard `422` detail array. Do not rely on undocumented Supabase/PostgREST error codes; Supabase is not part of the runtime.
