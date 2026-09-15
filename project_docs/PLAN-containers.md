# RAGged Container Conversion — Plan

**Author:** Engineering  
**Date:** 2026-09-14  
**Status:** Draft  
**Part:** III of III (Implementation plan / PR Plan). See also `PRD-containers.md` and `TECH-SKETCH-containers.md`.

> Extract of the container conversion design. Source of truth: combined design document (2026-09-14). Keep in sync with that document. The PR Plan, Key Decisions, Open Questions, and References live in `PLAN-containers.md`.


# Part III — Plan

Incremental implementation. Each slice is independently reviewable. New code lives under `api/` and `web/`; do not "fix in place" the Vite app. Copy UI components when the SPA PR starts. Delete legacy trees only in the last PR.

## Implementation principles

- Collapse old migrations into one Alembic revision; do not replay `00000`–`00006`.
- Pin models server-side; never read model/temperature from JSON.
- One writer for conversations: `POST /api/threads/{id}/messages`.
- Tests land in the same PR as the feature.
- `grep` the PR diff for `vite`, `VITE_`, `window.showToast`, `userId`, `text-embedding-ada-002`, `crossThreadSearch`, `confirmDeletion`.

## Ordered work

### Slice A — Scaffold (PR 1)

Compose file, `docker-compose.dev.yml`, Dockerfiles, **final** `web/nginx.conf` (`client_max_body_size 55m`, `proxy_read_timeout 100s`, `/api` 308, `/assets/` cache, `X-Forwarded-*`), stub API `/api/health` (`async def`, no I/O), `.env.example` (`POSTGRES_*`, `JWT_SECRET`, `OPENAI_API_KEY`, `COOKIE_SECURE`, **`PUBLIC_ORIGINS=http://localhost:8080,http://localhost:3000`**; no `VITE_*` / `NEXT_PUBLIC_*` / hand-written `DATABASE_URL`), gitignore `data/uploads`. Compose **constructs** `DATABASE_URL` from `POSTGRES_*`. `api` healthcheck is stdlib `urllib` (no `curl`) with `start_period: 20s`, `retries: 12`; `web depends_on api: condition: service_healthy`. Verification: `docker compose up --build` publishes 8080 only; `/api/health` proxied; `web/nginx.conf` contains `client_max_body_size 55m` (a 20 MB POST body is not 413; a 56 MB POST is).

### Slice B — Schema (PR 2)

SQLAlchemy models + Alembic `0001_initial` as specified in Data Model Changes. `conftest.py` Testcontainers `pgvector/pgvector:pg16` (session-scoped) + Alembic. Verification: `\dx` shows `vector`; `\d vector_chunks` shows `vector(1536)` and `document_id` FK to `documents`; `\d documents` shows `user_id` FK to `users` (not `auth.users`); `\d users` shows `CHECK (email = lower(email))`.

### Slice C — Auth (PR 3)

Register/login/logout/me + cookie helper + pytest on the Testcontainers DB. Verification: register → me 200; login `Set-Cookie` has `HttpOnly`, `SameSite=Lax`, `Path=/`, no `Domain`; JWT **absent** from JSON; logout **without** cookie and with **expired** cookie both 204 and clear the cookie (same attributes); duplicate email 409; short password 422; unknown email still hits dummy bcrypt; **default env** (`PUBLIC_ORIGINS` = `:8080` and `:3000`, `CORS_ORIGINS` empty): `Origin: http://localhost:3000` POST `/threads` is 200; `Origin: http://localhost:8080` POST `/threads` is 200; `Origin: http://evil.example` is 403. CORS middleware is not mounted.

### Slice D — Threads (PR 4)

CRUD + archive + restore + delete cascade (DB only; uploads dir removal wired once documents exist, still call `rmtree` if the path exists). Isolation tests. Verification: user B 404s on user A's thread id; delete removes child rows.

### Slice E — Documents / ingest (PR 5)

Multipart upload, magic bytes, quotas (`FOR UPDATE`, `processing`+`ready`), extract, chunk, embed, relative `file_path`, `embedding_model` stored, per-document `ready`/`failed`, `try/finally`. Pytest with a tiny PDF fixture and a mocked OpenAI embeddings client (sync `OpenAI`). Verification: `.exe` renamed to `.pdf` is 415 **before writes**; 10 MB+1 is 413; mixed type in one request 415 whole; path matches relative UUID regex; status is not `ready` if embed mock raises; two concurrent quota tests do not exceed 20 files.

### Slice F — Messages / RAG (PR 6)

Search SQL, canned refusal, SOURCES prompt, save once, `CreateMessageResponse` envelope, pytest with mocked embeddings + chat. Verification: no chunks → exact refusal string and `chat.completions.create` **not** called; GET `/messages` returns the same `sources`; two POSTs create four conversation rows not eight; extra body field `model` → 422; `content` of 8001 chars → 422; cosine 0.69 refused / 0.71 hits (see matrix).

### Slice G — Webpack SPA foundation (PR 7)

`web/` package.json + **committed `package-lock.json`**, webpack config (`publicPath: '/'`, hashed JS **and** CSS under `/assets/`, CopyWebpackPlugin favicon), `api.ts` (`API_BASE='/api'`, FormData, 401 event), `AuthContext`, `ToastContext`, Login/SignUp/Header. Verification: `NODE_ENV=production npx webpack --mode production` emits `dist/index.html` + `dist/assets/*.js` + `dist/assets/*.css` + `dist/ragged.png`; login POST URL is `/api/auth/login`; `npm test` for login form; no `vite` in `web/package.json`.

### Slice H — App shell (PR 8)

Copy remaining components in **two stacked commits** if the diff exceeds ~1k LOC: (1) `ThreadList` + `CreateThreadModal` + `DocumentUpload` (bugs 2, 9); (2) `ChatInterface` (bug 3, GET-history sources). Verification: RTL highlight uses `id`; drop path calls `validateFile`; chat does not call `saveMessage` and reads `assistant_message` not `response`; after rendering GET history, assistant bubble still shows up to 3 sources.

### Slice I — Integrate & document (PR 9)

README rewrite, smoke script `scripts/smoke.sh` (requires live `OPENAI_API_KEY`; fixture `api/tests/fixtures/sample.pdf`; no mock mode — CI that lacks a key skips this script). Verification: success criteria from Part I. nginx/healthchecks/`DATABASE_URL` construction already landed in PR 1 — this PR only documents them.

### Slice J — Delete legacy (PR 10)

Remove `src/`, `supabase/`, `example-code/`, `vite.config.ts`, `vitest.*.config.ts`, root Vite `package.json` scripts (root should be compose-only or a thin README pointer). Verification: repo has no runtime dependency on Supabase or Vite.

Dependencies: 1 → 2 → 3 → 4 → 5 → 6; 7 after 3 (can overlap 4–6); 8 after 6 and 7; 9 after 8; 10 after 9. Do not reorder 1–6.

## Verification matrix (maps to the 10 bugs)

| Bug | Automated check |
| --- | --- |
| 1 Delete | `DELETE /api/threads/{id}` 204 with only cookie; no body |
| 2 Highlight | RTL: selected class when `currentThreadId === thread.id` |
| 3 Doubled history | pytest: 1 user + 1 assistant row per POST |
| 4 Unauth extract | no `/extract` route; unauth POST documents 401 |
| 5 Storage isolation | user B cannot GET user A's document; files under A's UUID dir |
| 6 Early completed | on embed exception status `failed` and `chunk_count=0` |
| 7 Threshold / cross-thread | SQL always has `thread_id`; extra field `crossThreadSearch` 422; pytest: chunk at cosine **0.69** takes the canned-refusal path (`chat.completions.create` not called); chunk at **0.71** calls chat |
| 8 Fallback embed | mock asserts `embeddings.create` once (query only) on empty retrieval |
| 9 Drop validation | `DocumentUpload` test fires drop of a `.exe` and shows error, no fetch |
| 10 Path sanitization | stored `file_path` matches `^[0-9a-f-]{36}/[0-9a-f-]{36}/[0-9a-f-]{36}\.(pdf\|docx\|txt\|rtf)$`; resolve stays under `UPLOAD_ROOT` |

---

## Key Decisions

1. **FastAPI + Webpack 5 React SPA + Postgres 16/pgvector + Docker Compose, one public port (8080→web:80).** Matches the conversion request; nginx is the only ingress and proxies `/api`.
2. **No Vite / Vitest / Next / CRA / Parcel / Rsbuild.** User constraint plus the one-line rejections in Alternatives.
3. **No Redis, Celery, MinIO, or Kubernetes in v1.** 10 MB sync ingest is enough; fewer failure domains.
4. **Email/password, SHA-256-then-bcrypt cost 12, JWT in httpOnly cookie `ragged_session`.** Cookie: `Path=/`, host-only (no `Domain`), `SameSite=Lax`, `Secure` iff `COOKIE_SECURE`, `Max-Age=JWT_TTL_SECONDS`. Not `localStorage`. Isolation is application `WHERE user_id = current_user.id`, not RLS (RLS already failed in this repo).
5. **Pin `text-embedding-3-small` and `gpt-4o-mini` server-side.** Persist `embedding_model` on documents and chunks. Client cannot choose model or temperature. Temperature 0.2 for grounded answers.
6. **Thread-scoped cosine search, threshold 0.7, top 8.** No cross-thread search. No chat-history vectors. No thread-archive vectors.
7. **Empty retrieval → canned `I don't have that in your documents.`** No general-knowledge chat call; do not embed the refusal.
8. **Single document `status`: `processing | ready | failed`.** `ready` only after chunks are committed.
9. **Server-generated relative storage paths** `{user_id}/{thread_id}/{uuid}{ext}` under `UPLOAD_ROOT`. Magic-byte type check. 10 MB/file, 55 MB request body (nginx + Starlette).
10. **One conversation writer:** `POST /api/threads/{id}/messages`. Fixes doubled history.
11. **Soft archive vs hard delete.** Archive is `status=archived`. Delete cascades DB + files. No vector-blob archive on delete.
12. **Greenfield Alembic `0001_initial`.** Drop `auth.users` FKs, RLS, preference RPCs, SECURITY DEFINER functions. No data migration from Supabase.
13. **Toast via React context**, not `window.showToast`.
14. **Webpack-dev-server is host-only.** Docker always serves the production webpack build from nginx.
15. **Restore endpoint kept** (`POST /api/threads/{id}/restore`) because `ThreadList` already has restore UX; cheap and useful.
16. **Legacy `src/`, `supabase/`, `example-code/` deleted in the last PR**, after the new stack is the default README path.
17. **HNSW cosine index**, not IVFFlat lists=100, because personal corpora are small.
18. **No email verification in v1.** Register sets the session immediately (old Supabase confirm-email flow dropped).
19. **CSRF: `SameSite=Lax` + `PUBLIC_ORIGINS` Origin allowlist (default `http://localhost:8080` and `http://localhost:3000`).** No CSRF token / double-submit cookie in v1. `CORS_ORIGINS` is a **separate** list, default empty (CORS middleware off for Docker **and** the webpack-dev-server proxy). Logout is auth-optional and must `delete_cookie` with the same Path/Domain/Secure/SameSite as set. Production sets `PUBLIC_ORIGINS` to the TLS origin.
20. **Sync `def` for ingest and RAG; 2 uvicorn workers; `/api/health` async with no I/O.** Blocking OpenAI and SQLAlchemy never run on the event loop. Pool 5+5 per worker.
21. **Pytest against Testcontainers `pgvector/pgvector:pg16`, not SQLite.** `conftest.py` lands in PR 2.
22. **Multi-file upload stays one POST `files`.** Type/size failures reject the whole request before writes; extract/embed failures are per-file `failed` with HTTP 201. Quota counts `processing`+`ready` under `SELECT ... FOR UPDATE`.
23. **POST `/messages` envelope is `{ user_message, assistant_message }`.** GET `/messages` returns `Message[]` with `sources` on assistant rows. No `response` field. Query text capped at 8000 chars.
24. **Timeout stack: OpenAI 60 s + nginx 100 s.** No 90 s handler timer (`try/finally` is cleanup only). Stale `processing` > 100 s is `failed`. `proxy_ignore_client_abort on`.

---

## Open Questions

Design choices the conversation already made are **not** listed (FastAPI, React, Postgres, Docker, no Vite, no Redis/Celery/MinIO, OpenAI embeddings + gpt-4o-mini, httpOnly cookie JWT, no cross-thread search, no general-knowledge fallback).

Remaining items are operational, not blockers:

1. **TLS terminator and public hostname** for a deployed VM (Caddy/Traefik vs cloud LB). Out of the Compose v1 unit; set `COOKIE_SECURE=true` when TLS exists.
2. **Backup cadence** for `pgdata` and `data/uploads` (e.g. nightly `pg_dump` + tarball). Operator concern; call out in README, not an app feature.

If a third embedding dimension is ever required, that is a new Alembic revision and a re-embed job — not a v1 question.

---

## References

- Current SPA: `src/App.tsx`, `src/lib/supabase.ts`, `src/lib/edgeFunctions.ts`, `src/types/index.ts`, `src/components/**`
- Edge Functions: `supabase/functions/extract-text/index.ts`, `vectorize/index.ts`, `rag-query/index.ts`, `delete-thread/index.ts`, `shared/auth.ts` (unused by the copies that inlined auth)
- Schema: `supabase/migrations/00000_initial_schema.sql` through `00006_add_similarity_search_function.sql`
- Old product docs (do not implement their extra features): `project_docs/PRD-RAGged.md`, `project_docs/TDD-RAGged.md`
- Env drift (ada vs 3-small): `env.example` vs hardcoded `text-embedding-ada-002` in Edge Functions
- Split copies of this design: `project_docs/PRD-containers.md`, `project_docs/TECH-SKETCH-containers.md`, `project_docs/PLAN-containers.md`

---

## PR Plan

Concrete, ordered pull requests. Each is independently reviewable and mergeable. Later PRs depend on earlier APIs, not on rewriting them.

### PR 1 — Scaffold Compose stack (stub API + nginx)

- **Title:** `chore: scaffold FastAPI / webpack-nginx / pgvector Compose stack`
- **Files/components:** `docker-compose.yml`, `docker-compose.dev.yml`, `api/Dockerfile`, `api/requirements.txt`, `api/app/main.py` (async `/api/health` only), `web/Dockerfile` (placeholder until PR 7), `web/nginx.conf` (**55m / 100s / `/api` 308 / `/assets/` / `X-Forwarded-*`**), `.env.example`, `.gitignore`, `data/uploads/.gitkeep`
- **Dependencies:** none
- **Description:** Bootable three-service compose with one public port. Compose builds `DATABASE_URL` from `POSTGRES_*`. `.env.example` includes `PUBLIC_ORIGINS=http://localhost:8080,http://localhost:3000`. `api` healthcheck is `python -c "import urllib.request; ..."` (no `curl`) with `interval: 5s`, `timeout: 3s`, `retries: 12`, `start_period: 20s`. `web` waits until `api` is healthy. nginx proxies `/api` with the production body/timeout limits. Overlay `docker-compose.dev.yml` publishes `8000`. No Vite. No published DB port in the default file.

### PR 2 — Alembic initial schema

- **Title:** `feat(db): users, threads, documents, conversations, vector_chunks`
- **Files/components:** `api/app/models.py`, `api/app/db.py`, `api/app/config.py`, `api/alembic.ini`, `api/alembic/env.py`, `api/alembic/versions/0001_initial.py`, `api/tests/conftest.py`, `api/requirements-dev.txt`
- **Dependencies:** PR 1
- **Description:** One initial migration as specified in Data Model Changes. Enable `vector` only (no `uuid-ossp`), HNSW cosine index, FKs to `users`, email `CHECK (email = lower(email))`, indexes on `documents(user_id)` and `vector_chunks(document_id)`. Session-scoped Testcontainers `pgvector/pgvector:pg16`. Verification: `\d vector_chunks` shows `vector(1536)` and FK to `documents`/`users`. API container runs `alembic upgrade head` on start.

### PR 3 — Auth API (cookie JWT)

- **Title:** `feat(api): register, login, logout, me with httpOnly JWT cookie`
- **Files/components:** `api/app/auth_utils.py`, `api/app/deps.py`, `api/app/schemas.py` (auth), `api/app/routers/auth.py`, `api/tests/test_auth.py`
- **Dependencies:** PR 2
- **Description:** SHA-256-then-bcrypt passwords, dummy hash at startup, HS256 JWT in `ragged_session` with the cookie table attributes. Logout is auth-optional and always clears the cookie. Pytest: happy path, duplicate email, invalid login, cookie flags (`HttpOnly`, `SameSite=Lax`, `Path=/`), JWT absent from JSON, expired cookie logout, Origin allowlist **with default env** (`http://localhost:3000` and `http://localhost:8080` POST `/threads` 200; `http://evil.example` 403; CORS middleware not mounted). No `userId` in bodies.

### PR 4 — Threads API

- **Title:** `feat(api): thread list/create/archive/restore/delete`
- **Files/components:** `api/app/routers/threads.py`, `api/app/schemas.py`, `api/tests/test_threads.py`
- **Dependencies:** PR 3
- **Description:** All thread routes. Delete cascades conversations/documents/chunks via FK and removes `UPLOAD_ROOT/{user_id}/{thread_id}` if present. Isolation tests (404 across users). Fixes product bug 1 at the API layer.

### PR 5 — Document upload, extract, embed

- **Title:** `feat(api): multipart ingest with magic-byte checks and pgvector inserts`
- **Files/components:** `api/app/routers/documents.py`, `api/app/services/{files,extract,chunk,embeddings}.py`, `api/tests/test_documents.py`, fixtures under `api/tests/fixtures/`
- **Dependencies:** PR 4
- **Description:** Sync `def` extract + chunk + embed on POST. Type/size gate rejects the whole request; per-file `ready` only after chunks commit (bug 6). Relative UUID `file_path` (bug 10). Quota `FOR UPDATE` on `processing`+`ready`. `try/finally` + stale-processing sweeper. Mock OpenAI. Store `embedding_model`. API-only (default compose still does not publish 8000).

### PR 6 — RAG messages endpoint

- **Title:** `feat(api): thread-scoped RAG query with canned empty retrieval`
- **Files/components:** `api/app/routers/messages.py`, `api/app/services/rag.py`, `api/app/prompts.py`, `api/tests/test_messages.py`, `api/tests/test_security.py`
- **Dependencies:** PR 5
- **Description:** Embed query, cosine search `user_id AND thread_id` threshold 0.7 with numeric 0.69/0.71 tests (bug 7), refuse without chat/re-embed (bug 8), save messages once (bug 3), `CreateMessageResponse` only (no `response` field), GET hydrates `sources`, reject extra fields `model`/`temperature`/`userId`/`crossThreadSearch`, 8000-char cap.

### PR 7 — Webpack 5 SPA foundation + auth UI

- **Title:** `feat(web): Webpack 5 React SPA with api.ts, auth, toast context`
- **Files/components:** `web/package.json`, `web/package-lock.json`, `web/webpack.config.js`, `web/tsconfig.json`, `web/postcss.config.js`, `web/tailwind.config.js`, `web/jest.config.js`, `web/src/index.tsx`, `web/src/index.html`, `web/src/index.css`, `web/src/lib/api.ts`, `web/src/types/index.ts`, `web/src/context/*`, `web/src/components/Auth/*`, `web/src/components/Layout/Header.tsx`, `web/src/components/UI/{Toast,ErrorBoundary}*`, `web/Dockerfile` production build, `web/tests/*`
- **Dependencies:** PR 3 (auth contract). Can merge before documents exist.
- **Description:** Production webpack build (`publicPath: '/'`, hashed JS and CSS, favicon copy) copied into nginx. webpack-dev-server optional for host work against `docker-compose.dev.yml`. `api.ts` prefixes `/api`, `credentials: 'include'`, FormData without Content-Type, 401 → `ragged:unauthorized`. Toast context replaces `window.showToast`. Jest, not Vitest. No `VITE_*`. Verification: login POST URL is `/api/auth/login`; favicon 200.

### PR 8 — Threads, upload, chat UI (bugfix pass)

- **Title:** `feat(web): thread sidebar, document upload, chat wired to /api`
- **Files/components:** `web/src/App.tsx`, `web/src/components/Threads/*`, `web/src/components/Documents/DocumentUpload.tsx`, `web/src/components/Chat/ChatInterface.tsx`, `web/src/components/UI/{ConfirmationModal,LoadingSpinner,ProgressBar}.tsx`, corresponding Jest tests
- **Dependencies:** PR 6 and PR 7
- **Description:** Copy structure from `src/components/**`, rewire to `api.ts`. Two stacked commits if the diff is large (threads+upload, then chat). Pass `currentThread.id` (bug 2). No `saveMessage`; read `assistant_message` not `response` (bug 3). Validate drop and picker (bug 9). GET-history RTL: assistant bubble still shows up to 3 sources after reload. Delete confirmation copy no longer mentions vector archival.

### PR 9 — Integration, README, smoke

- **Title:** `chore: README, env example, smoke script`
- **Files/components:** `.env.example` (document `POSTGRES_*`, `JWT_SECRET`, `OPENAI_API_KEY`, `COOKIE_SECURE`, `PUBLIC_ORIGINS`; no `DATABASE_URL` / `VITE_*`), `README.md`, `scripts/smoke.sh`
- **Dependencies:** PR 8
- **Description:** Document `docker compose up --build` and the dev overlay. README: production must set `PUBLIC_ORIGINS` to the TLS origin (replacing the localhost pair). Smoke requires a live `OPENAI_API_KEY` and `api/tests/fixtures/sample.pdf`: health, register, thread, upload fixture, in-corpus query, OOD refusal. No mock mode; CI without a key skips the script. nginx/healthchecks already in PR 1.

### PR 10 — Remove Supabase + Vite legacy trees

- **Title:** `chore: delete src/, supabase/, example-code/, Vite toolchain`
- **Files/components:** delete `src/`, `supabase/`, `example-code/`, `vite.config.ts`, `vitest.*.config.ts`, `index.html` (root), root `package.json` Vite scripts, `tsconfig.app.json` / `tsconfig.node.json` if unused, `public/vite.svg`; trim root `eslint.config.js` or move under `web/`
- **Dependencies:** PR 9
- **Description:** The containerized app is the only runtime. Last PR on purpose so UI copy has a source and rollback via revert is possible until then. Confirm `rg -i 'vite|supabase|VITE_|NEXT_PUBLIC_' --glob '!project_docs/**' --glob '!ai_chats/**' --glob '!documents/**'` is clean of runtime refs (historical docs may remain until a later docs cleanup).

