# Slice 04 — Threads — test results

- **Branch:** feat/slice-04-threads
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS
- **Authority:** Ragged QA on Marc’s Mac checkout `/Users/marcbreneiser/Code/ragged/` (authoritative). Earlier box clone run had one env-only fail on `:8000` publish under host-network; Mac default compose is clean.

## Commands

```bash
source api/.venv/bin/activate
pytest -m uat
pytest -m dogfood
```

## UAT

- Result: **10 passed**, 6 skipped (05–10), ~19s
- Slice 04 (`tests/uat/test_uat_slice04_threads.py`):
  - Alice creates thread; Bob’s `GET /api/threads` → `[]`; archive/delete of Alice’s id as Bob → **404** (cross-user isolation)
- Regressions 01–03 green under the same run

## Dogfood (`tests/dogfood/test_dogfood_slice04_threads.py`)

- Result: **4 passed** (01–04), 6 skipped, ~17s
- Operator lifecycle: register → create → list → archive → restore → delete 204 → list empty

## UX notes (severity)

- Threads are API-only until shell (slice 08) — **Low / expected**
- Nothing blocking

## Open bugs

None for slice 04.
