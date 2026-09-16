# Slice 03 — Auth — test results

- **Branch:** feat/slice-03-auth
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS
- **Authority:** Ran by Ragged QA on local checkout `/Users/marcbreneiser/Code/ragged/`; ignore any parallel Grok Build results for this slice.

## Commands

```bash
source api/.venv/bin/activate
pytest -m uat
pytest -m dogfood
```

## UAT

- Result: **9 passed** (slices 01–03), 7 skipped (04–10), ~18s
- Slice 03 (`tests/uat/test_uat_slice03_auth.py`):
  - register → 201, Set-Cookie `ragged_session` HttpOnly SameSite=Lax Path=/ (no Domain), no `access_token` in JSON; GET `/api/auth/me` returns email
  - Origin allowlist: `localhost:3000` and `:8080` allowed for POST `/api/threads`; `evil.example` → 403

## Dogfood (`tests/dogfood/test_dogfood_slice03_auth.py`)

- Result: **3 passed** (01–03), 7 skipped, ~17s
- Operator: register → `/me` → `/me` again (still logged in) → logout → `/me` 401

## UX notes (severity)

- Auth is API/cookie only; no UI login shell yet — **Low / expected** until slice 08
- Nothing blocking

## Open bugs

None for slice 03.
