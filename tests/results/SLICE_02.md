# Slice 02 — Schema — test results

- **Branch:** feat/slice-02-schema
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS

## Commands
```bash
source api/.venv/bin/activate
pytest -m uat
pytest -m dogfood
```

## UAT
- Result: **7 passed** (slice01 5 + slice02 2), 8 skipped (slices 03–10), ~17s
- Slice 02 cases (`tests/uat/test_uat_slice02_schema.py`):
  - `vector` extension present
  - `vector_chunks` has 1536-dim embedding + document_id; no auth.users FK
  - `documents.user_id` references `users` (not auth.users)
  - users email lower() check constraint
  - GET /api/ready → {status: ok}

## Dogfood (`tests/dogfood/test_dogfood_slice02_schema.py`)
- Result: **2 passed** (slice01 + slice02), 8 skipped, ~17s
- Operator checks: psql describe users (email, password_hash), documents (thread_id, user_id), vector_chunks (embedding, 1536); public tables users, threads, documents, conversations, vector_chunks present

## UX notes (severity)
- Schema is Compose/psql only — no UI yet — **Low / expected**
- Manual follow-up needs `docker compose exec db psql` with `.env` creds; stack tears down after pytest unless `RAG_KEEP_COMPOSE=1` — **Low / expected**
- Nothing blocking

## Open bugs
None for slice 02.
