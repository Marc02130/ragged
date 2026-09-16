# Slice 01 — Compose scaffold — test results

- **Branch:** feat/slice-01-compose-scaffold
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS

## Commands
```bash
source api/.venv/bin/activate
pytest -m uat
pytest -m dogfood
```

## UAT (`tests/uat/test_uat_slice01_scaffold.py`)
- Result: **5 passed**, 9 skipped (slices 02–10), ~22s
- Cases verified:
  - GET /api/health through nginx on :8080 returns {status: ok}
  - GET /api returns 308 → /api/
  - Default Compose does not publish :8000
  - 20 MB POST is not 413
  - 56 MB POST is 413

## Dogfood (`tests/dogfood/test_dogfood_slice01_scaffold.py`)
- Result: **1 passed**, 9 skipped (slices 02–10), ~14s
- Operator checks: `/` shows “RAGged”; `/api/health` → `{status: ok}`; `/ragged.png` loads as image

## UX notes (severity)
- Bare `<h1>` + one line, no CSS/viewport meta, no in-page link to health — **Low / expected** for scaffold; revisit at shell (slice 08)
- Favicon wired; copy correctly notes Webpack SPA in slice 7
- Nothing blocking

## Open bugs
None for slice 01.
