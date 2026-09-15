# RAGged Container Conversion — PRD

**Author:** Engineering  
**Date:** 2026-09-14  
**Status:** Draft  
**Part:** I of III (PRD). See also `TECH-SKETCH-containers.md` and `PLAN-containers.md`.

> Extract of the container conversion design. Source of truth: combined design document (2026-09-14). Keep in sync with that document. The PR Plan, Key Decisions, Open Questions, and References live in `PLAN-containers.md`.


# Part I — PRD

A new product requirements document for the containerized app. This is **not** a rewrite of `project_docs/PRD-RAGged.md`. Features that made the old app worse (cross-thread search, chat-history vectorization, thread-archive-as-vector-blob, client-driven model/temperature) are explicitly out of product scope.

## Background & Motivation

The current product is specified in `project_docs/PRD-RAGged.md` and implemented as:

- React 18 + Vite + Tailwind in `src/` (`App.tsx`, `components/{Auth,Chat,Documents,Threads,Layout,UI}`, `lib/supabase.ts`, `lib/edgeFunctions.ts`, `types/index.ts`).
- Supabase Auth (`auth.users`) with FKs from every table (`supabase/migrations/00000_initial_schema.sql`).
- Edge Functions that duplicate auth, trust body `userId`, and (in `extract-text`) skip JWT entirely while using the service role.
- Dual document status fields (`status` and `vector_status`), user preference JSON driving model/temperature (`00004_add_user_preferences.sql` + `get_user_preferences` SECURITY DEFINER RPC), and `search_similar_chunks` used by a RAG path that defaults `crossThreadSearch` to true (`src/lib/edgeFunctions.ts` line 193; `rag-query` `RAG_CONFIG.SIMILARITY_THRESHOLD = 0.1`).

Pain points that motivate the conversion:

1. **Security**: `extract-text` has no JWT check (`supabase/functions/extract-text/index.ts`). Storage policies in `00005_storage_bucket_setup.sql` allow any authenticated user to read/write/delete the entire `documents` bucket. Several SECURITY DEFINER RPCs take a caller-supplied `user_id`.
2. **Correctness**: Thread delete is broken (`threads.delete` sends only `{ threadId }`; `delete-thread` requires `userId` + `confirmDeletion: true`). Thread highlight never matches (`App.tsx` passes `currentThread?.thread_id` but `Thread` only has `id`). Chat history doubles because `ChatInterface` and `rag-query` both insert conversations.
3. **Product quality**: Cross-thread retrieval leaks context. Fallback answers invent facts, then get embedded as if they were sources. Drop-to-upload bypasses the type/size checks the file picker runs.
4. **Operability**: Vite + Supabase + Deno is four moving parts for a personal app. A Compose stack with one public port is the unit we want to run and back up.

The conversion is a **greenfield runtime**. We do not migrate rows from the existing Supabase project. Users re-register and re-upload. Old trees (`src/`, `supabase/`, `example-code/`) remain in git until the last PR so UI components can be copied, then they are deleted.

## Goals & Non-Goals

### Goals

- Personal RAG for individual users (researchers, students, professionals interrogating their own files). Not enterprise collab.
- Email/password sign up and log in. Session survives refresh via httpOnly cookie. Sign out clears the cookie.
- Create, list, archive, restore, and delete conversation threads. Archive is a soft `status=archived`. Delete is a hard cascade of DB rows **and** files on disk, after an in-UI confirmation.
- Upload PDF, DOCX, TXT, RTF (≤ 10 MB each) into a thread. Server validates type by magic bytes, stores the file under a server-generated path, extracts text, chunks, embeds, and returns only when the document is `ready` or `failed`.
- Ask a question against **that thread's** documents. See the assistant answer and up to 8 source snippets with similarity scores.
- If no chunk meets similarity 0.7, show a fixed message that the answer is not in the user's documents. Do not invent an answer. Do not treat the refusal as a source.
- Run locally and on a single VM via `docker compose up`, one public HTTP port.
- Keep the existing UI information architecture (sidebar threads, upload strip, chat pane, Tailwind look) while replacing the data layer.

### Non-Goals

- Cross-thread search (defaults on today in `performRAGQuery` / `rag-query`; leaks context).
- Vectorizing chat history or re-embedding general-knowledge / fallback answers.
- Archiving a deleted thread as a vector blob (`delete-thread` `archiveThread`).
- User preference JSON, client-chosen `model` / `temperature` / `searchStrategy`.
- Client-supplied `userId`, `filePath`, `documentId` as authorization inputs.
- OAuth, magic links, email verification, password-reset mail (v1 is local/personal).
- Multi-user sharing, orgs, roles, audit log UI.
- Streaming tokens, citations as PDF page numbers, OCR for scanned PDFs.
- Redis, Celery, MinIO, Kubernetes, a separate object store.
- Vite, Vitest-as-bundler, `VITE_*` / `NEXT_PUBLIC_*` env, Next.js, CRA, Parcel, Rsbuild.
- Porting `example-code/` Fund Flow AI grant-writer functions.
- Migrating existing Supabase data.
- Individual document delete, download, or retry-embed endpoints (thread delete is the cleanup path; re-upload is the retry).
- Login / register rate limiting (no 429 in v1; personal single-node). Dummy bcrypt on unknown emails still applies.
- CSRF tokens / double-submit cookies. v1 is same-origin nginx + `SameSite=Lax` + Origin allowlist on mutating routes.

## Users

| Persona | Need | v1 support |
| --- | --- | --- |
| Individual knowledge worker | Upload a handful of PDFs/DOCX and ask questions in separate topical threads | Yes |
| Same user, second device | Log in with email/password; see the same threads | Yes, if they hit the same Compose stack |
| Collaborator / org admin | Shared threads, SSO, DLP | No |

Capacity target (from the old PRD, still appropriate): **≤ 100 users**, tens of threads each, tens of documents per thread. This is a single-node personal app, not a multi-tenant SaaS.

## Features

### 1. Authentication

- **Register** with email + password (min 8 characters, max 128). Email is stored lowercased and unique (`CHECK (email = lower(email))`). Success sets the session cookie and lands the user in the empty-thread shell. No confirmation email (the old `SignUpForm` waited on Supabase mail; that is dropped).
- **Log in** with email + password. Generic error on failure ("Invalid email or password"). Success sets the cookie.
- **Log out** always clears the cookie (auth-optional: expired/missing JWT still 204) and client state (current thread, documents, messages).
- **Session restore**: on load, `GET /api/auth/me`. 401 shows Login/SignUp. 200 shows the app shell with `Header` displaying `user.email`.
- Passwords: SHA-256 the UTF-8 password, then bcrypt the hex digest (cost 12). This avoids bcrypt’s silent 72-byte truncation on the 128-char max. JWT lives only in an httpOnly, `SameSite=Lax`, `Path=/`, host-only cookie named `ragged_session`. Not `localStorage`. Not returned in JSON.

### 2. Threads

Parity with `ThreadList` + `CreateThreadModal`, minus the "deleted-and-archived-as-vectors" copy.

- Create with title (1–100 chars). New thread is `status=active`, `document_count=0`.
- List active threads, newest `last_activity_at` first, showing title, document count, relative date.
- Select a thread: highlight uses `thread.id` (fixes bug 2).
- Archive: `status=archived`. Hidden from the default list. "Show archived" lists them with Restore + Delete.
- Restore: `status=active`.
- Delete: `ConfirmationModal` required. On confirm, hard-delete the thread, its documents, chunks, messages, and files under `data/uploads/{user_id}/{thread_id}/`. Copy must **not** say "archive the conversation as vectors".

### 3. Documents

Parity with `DocumentUpload`, with validation on **both** picker and drop (fixes bug 9).

- Allowed types: PDF, DOCX, TXT, RTF. Enforced by magic bytes on the server; the client also checks MIME + 10 MB as a UX filter.
- Caps: 10 MB per file, 20 files per thread, 50 MB total per thread, 1 GB total per user (same numbers as `env.example`). Quota counts rows with `status IN ('processing','ready')` only (`failed` does not occupy a slot). nginx and Starlette both allow a **55 MB** request body so a 20-file / 50 MB thread upload is not 413’d by the proxy.
- Upload is one multipart POST to `/api/threads/{id}/documents`, field `files`. If **any** file fails type or per-file size, the whole request is 413/415 **before writes**. After that, each file is processed independently; the response is `201` with a `Document[]` whose items are `ready` or `failed`. There is no separate vectorize job to poll.
- List documents for the selected thread (metadata only: name, size, type, status, chunk_count, timestamps — **not** extracted text).
- Original filename is a display field only. Storage path is a **relative** `{user_id}/{thread_id}/{uuid}{ext}` under `UPLOAD_ROOT` (fixes bug 10).

### 4. Chat / RAG

Parity with `ChatInterface` sources UI, with doubled-insert and fallback bugs fixed.

- Load history: `GET /api/threads/{id}/messages` ordered by `created_at` ascending. Each item is `{ id, role, content, created_at, sources }`. User rows have `sources: []`. Assistant rows hydrate `sources` from `conversations.metadata` so a refresh still shows citations (the current `ChatInterface.loadChatHistory` drops them).
- Send: `POST /api/threads/{id}/messages` with `{ "content": "..." }` (max 8000 characters; 422 if longer). The server embeds the query, searches chunks for **this user and this thread**, generates (or refuses), **saves user + assistant once**, and returns:

```json
{
  "user_message": { "id": "...", "role": "user", "content": "...", "created_at": "...", "sources": [] },
  "assistant_message": { "id": "...", "role": "assistant", "content": "...", "created_at": "...", "sources": [ /* 0–8 */ ] }
}
```

  There is **no** `response` field (the old Edge Function / `data.response` shape must not be cargo-culted). The client reads `assistant_message.content` and `assistant_message.sources`. Do **not** call a separate save-message API (fixes bug 3). SPA types use `created_at`, not `timestamp`.
- Sources: up to 3 shown in the bubble (current UI), from up to 8 retrieved chunks. Each source: `chunk_id`, `document_id`, truncated `content`, `similarity`, `file_name`.
- Empty retrieval: `assistant_message.content` is exactly `I don't have that in your documents.` and `assistant_message.sources` is `[]`. No OpenAI chat call. No embedding of the refusal (fixes bugs 7 and 8).
- Client cannot send `model`, `temperature`, `userId`, `crossThreadSearch`.

### 5. Notifications and errors

- Replace `window.showToast` (`ToastContainer.tsx` lines 28–34) with a React `ToastContext`. All of `LoginForm`, `SignUpForm`, `ThreadList`, `DocumentUpload`, `CreateThreadModal`, `ChatInterface` consume the hook.
- `ErrorBoundary` stays as a last-resort full-page fallback.

## UX

Keep the current three-pane shell from `src/App.tsx`:

1. Unauthenticated: centered `LoginForm` / `SignUpForm` (Tailwind gray-50, blue-600 primary).
2. Authenticated, no thread: `Header` + `ThreadList` sidebar + welcome empty state with "Create New Thread".
3. Authenticated, thread selected: sidebar + upload card + chat column.

Copy changes vs today:

| Location | Old | New |
| --- | --- | --- |
| `ChatInterface` loading | "Vectorizing and generating response..." | "Searching your documents..." |
| Delete modal | "This will archive the conversation and delete the live chat data." | "This permanently deletes the thread, its documents, and its chat history." |
| Sign up success | "Check your email for a confirmation link!" | Immediate session; toast "Account created." |
| Delete success toast | "Thread deleted and archived successfully" | "Thread deleted." |

No settings page. No model picker. No cross-thread toggle.

## Non-functional requirements

| ID | Requirement | Target |
| --- | --- | --- |
| NFR-1 | RAG answer latency | p95 < 3 s **excluding** OpenAI; OpenAI client timeout 60 s is the hard cap for embed + chat. No separate 30 s kill. |
| NFR-2 | Upload + extract + embed | Typical 1–5 MB PDF < 30 s. Enforcement: OpenAI client timeout 60 s, nginx `proxy_read_timeout` 100 s, `try/finally` + `processing` > 100 s sweeper. No separate 90 s handler timer. |
| NFR-3 | File size | 10 MB exact cap (`10485760` bytes) per file; 50 MB / 20 files per thread; request body ≤ 55 MB. |
| NFR-4 | Availability | Single Compose stack, `restart: unless-stopped`; no HA in v1 |
| NFR-5 | Isolation | User A never reads User B's threads, files, chunks, or messages. Enforced in application SQL, tested. |
| NFR-6 | Secrets | `OPENAI_API_KEY`, `JWT_SECRET`, `POSTGRES_PASSWORD` only in server env. SPA has **no** secrets and **no** `VITE_*` / `NEXT_PUBLIC_*`. |
| NFR-7 | Cookie | `HttpOnly`, `SameSite=Lax`, `Path=/`, host-only (no `Domain`), `Secure` iff `COOKIE_SECURE=true`, `Max-Age=JWT_TTL_SECONDS` (604800). JWT never in JSON. |
| NFR-8 | Password | SHA-256 then bcrypt cost 12; never logged; max 128 chars |
| NFR-9 | Prompt injection | Retrieved text is fenced as untrusted `SOURCES`; model instructed to ignore instructions inside sources |
| NFR-10 | Test | pytest + Testcontainers `pgvector/pgvector:pg16` for API; Jest + React Testing Library for SPA. Not Vitest, not SQLite. |

## Out of scope (product)

Everything in **Non-Goals**, plus: billing, usage dashboards, mobile native apps, i18n, dark mode as a persisted preference, admin impersonation.

## Known bugs the conversion MUST fix

These are current defects. The new product is not done if any of them reappear.

| # | Defect | Evidence | Required fix |
| --- | --- | --- | --- |
| 1 | Thread delete is broken | `src/lib/supabase.ts` `threads.delete` body is `{ threadId }` only; `delete-thread` requires `userId` + `confirmDeletion: true` | `DELETE /api/threads/{id}` authorizes from the cookie; UI confirmation is enough; no body `userId` |
| 2 | Selection highlight never matches | `src/App.tsx` line 122: `currentThread?.thread_id` but `Thread` in `src/types/index.ts` has `id` | Pass `currentThread.id` |
| 3 | Chat history doubles | `ChatInterface` calls `chat.saveMessage` for user and assistant; `rag-query` `saveConversation` does it again | Only the messages endpoint writes rows |
| 4 | `extract-text` is unauthenticated and trusts the body | No JWT; service role; body `documentId` / `userId` / `filePath` | Upload is an authenticated route; path is server-chosen; no extract public API |
| 5 | Storage RLS is bucket-wide | `00005_storage_bucket_setup.sql` policies `USING (bucket_id = 'documents')` | Local volume paths namespaced by `user_id`/`thread_id`; API never serves another user's file |
| 6 | Document marked completed before vectors exist | `extract-text` sets `status=completed` before `vectorize` runs | Single `status`: `processing` → `ready` only after chunks are inserted; else `failed` |
| 7 | Similarity 0.1 vs 0.7; cross-thread default true | `rag-query` `SIMILARITY_THRESHOLD = 0.1`; `edgeFunctions.ts` `crossThreadSearch ?? true` | Threshold 0.7; `WHERE user_id AND thread_id`; no cross-thread flag |
| 8 | General-knowledge fallback then re-embed | `generateFallbackResponse` + `vectorizeFallbackConversation` | Canned refusal; no chat completion; no embed |
| 9 | Drop-to-upload skips validation | `DocumentUpload.handleDrop` calls `uploadFiles` directly; picker uses `validateFile` | Same `validateFile` on drop and picker; server still enforces |
| 10 | Filename interpolated into storage path | `` `${timestamp}_${file.name}` `` in `supabase.ts` | UUID + extension derived from detected type |

## Success criteria

A reviewer can `docker compose up --build`, open the published port, register, create a thread, upload a small PDF, ask a question whose answer is in the PDF and see a source, ask a question that is not in the PDF and see the canned refusal, archive/restore/delete the thread, and confirm a second user cannot see the first user's data. `grep -R vite web api docker-compose.yml` is empty. No `window.showToast`. No client-supplied `userId` on any request body.

---

