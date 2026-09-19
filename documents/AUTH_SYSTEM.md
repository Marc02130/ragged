# Authentication System

RAGged uses application-managed email/password accounts and a signed cookie. Supabase Auth is not part of the runtime.

## Flow

1. `POST /api/auth/register` creates a user and signs them in.
2. `POST /api/auth/login` verifies the password and signs them in.
3. FastAPI sets `ragged_session`, an HTTP-only JWT cookie.
4. Protected routes decode the JWT, load the current user, and enforce resource ownership.
5. `POST /api/auth/logout` clears the cookie.

The JWT is signed with HS256 using `JWT_SECRET` and defaults to a seven-day lifetime (`JWT_TTL_SECONDS=604800`). The cookie uses `SameSite=Lax`, path `/`, and the configured `COOKIE_SECURE` value.

## Password handling

Passwords must be 8–1024 characters. Before bcrypt, the password is SHA-256 encoded so bcrypt always receives a bounded-length value. `BCRYPT_ROUNDS` defaults to 12.

Login uses a precomputed dummy hash when an email does not exist, avoiding a fast user-enumeration path. Invalid email and invalid password receive the same `401` message.

## Authorization

`get_current_user` in `api/app/deps.py` rejects missing, invalid, expired, or orphaned sessions with `401`.

`get_owned_thread` loads a thread and compares `thread.user_id` with the current user. Missing and unowned threads both return `404`. Document routes additionally check document thread/user ownership. Retrieval SQL always includes authenticated user and thread filters.

The application connects to PostgreSQL with one server credential. Isolation is enforced by FastAPI dependencies and query filters, not PostgreSQL Row Level Security.

## Browser request protection

`OriginAllowlistMiddleware` checks state-changing requests against `PUBLIC_ORIGINS`. Configure the exact public HTTPS origin in production. Wildcard and empty public-origin settings are rejected at startup.

CORS is disabled when `CORS_ORIGINS` is empty. For a separately hosted trusted frontend, configure an explicit allowlist; credentialed wildcard CORS is not supported.

## Provider keys

Per-user OpenAI, xAI, and Anthropic keys are encrypted before storage. The encryption key is derived by `api/app/crypto.py`; API responses expose only whether each provider is configured. User keys take precedence over operator environment fallbacks.

Treat `JWT_SECRET` as both an authentication secret and part of secret-management continuity. Review `api/app/crypto.py` before rotating it in an installation with stored provider keys.

## Production checklist

- Generate a unique `JWT_SECRET` of at least 32 characters.
- Set `COOKIE_SECURE=true` only when the public endpoint is HTTPS.
- Set `PUBLIC_ORIGINS` to the exact public origin.
- Leave `CORS_ORIGINS` empty unless cross-origin access is required.
- Use a strong PostgreSQL password and do not expose the database publicly.
- Restrict `.env`, database backups, upload backups, and container logs.
- Back up the database and upload volume together.

## Implementation references

- Routes: `api/app/routers/auth.py`
- Cookie/JWT/password functions: `api/app/auth_utils.py`
- Current-user and ownership dependencies: `api/app/deps.py`
- Origin checks: `api/app/origin.py`
- Provider-key storage: `api/app/services/llm_keys.py`, `api/app/crypto.py`
