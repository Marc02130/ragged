# Security and Data Scoping

RAGged is a self-hosted, cookie-authenticated application. Security depends on FastAPI ownership checks, same-origin request protection, private service networking, and correct secret handling.

## Authentication

- Passwords are SHA-256 pre-hashed and bcrypt-hashed.
- Sessions are HS256 JWTs in an HTTP-only, `SameSite=Lax` cookie.
- The default session lifetime is seven days.
- Production HTTPS deployments must set `COOKIE_SECURE=true`.
- `JWT_SECRET` must be unique and at least 32 characters.

See [AUTH_SYSTEM.md](AUTH_SYSTEM.md) for the complete flow.

## Authorization and isolation

All protected routes derive the user from the session cookie; clients do not submit a trusted `user_id`.

Thread routes use `get_owned_thread`. Document routes verify both thread and user ownership. Retrieval SQL filters by `user_id` and `thread_id`. Unknown and unowned resources return `404`.

PostgreSQL is accessed by the API service account. The current schema does not use Supabase Auth or PostgreSQL RLS, so new server queries must preserve these explicit ownership filters.

## CSRF and CORS

State-changing methods are checked against `PUBLIC_ORIGINS` by
`OriginAllowlistMiddleware` when the request has an `Origin` header.
Registration and login are exempt. Configure only exact trusted origins;
startup rejects an empty list or wildcard.

CORS is off by default. If enabled, `CORS_ORIGINS` must be an explicit allowlist and requests can include credentials. Do not use `*`.

## File handling

- Supported signatures: PDF, DOCX, TXT, RTF.
- The API detects type from bytes rather than trusting filename or MIME headers.
- Original names are reduced to display names; generated server paths use user/thread IDs and random IDs.
- Default maximum size is 10 MiB per file with thread/user quotas.
- Files are stored in a private Docker volume, not served directly by nginx.
- Deleting a document or thread removes its stored original file.

Parsing untrusted documents still carries parser risk. Keep extraction libraries and base images updated and do not expose the API upload directory as a static mount.

## Provider keys and outbound data

User provider keys are encrypted before database storage and are never returned by the API. Operator keys in `.env` are fallbacks.

Query rewriting sends the question, recent questions, thread title, file names, and headings to the selected chat provider. Final answer generation sends the question and retrieved source text. Optional retrieval grading sends short source snippets. Operators should account for these outbound data flows when selecting providers and writing privacy notices.

Document embeddings are generated locally by default.

## Network and deployment

The base Compose file publishes only nginx on port `8080`; FastAPI and PostgreSQL remain on the internal network. Put TLS in front of nginx and avoid publishing the database port.

`/api/health` is unauthenticated liveness. `/api/ready` is unauthenticated readiness and performs a database query; neither returns credentials or database details.

## Known boundaries

The repository does not implement:

- OAuth or multi-factor authentication;
- rate limiting or account lockout;
- user self-service export/deletion workflows;
- antivirus scanning;
- field-level encryption for document/message content;
- formal compliance controls or automatic retention policies.

Do not claim those controls in deployment or privacy materials without adding and verifying them.

## Incident-sensitive data

Protect all of the following:

- `.env` and orchestration secrets;
- database dumps;
- uploads-volume backups;
- per-user provider-key ciphertext and the secret needed to decrypt it;
- container logs and support bundles;
- retrieved source text and chat messages.

Rotate exposed provider keys immediately. Before rotating `JWT_SECRET`, review its relationship to encrypted provider keys in `api/app/crypto.py`.
