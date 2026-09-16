# Slice 05 — Documents — test results

- **Branch:** feat/slice-05-documents
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS (UAT portion; dogfood pending)
- **Authority:** Ragged QA on Marc’s Mac checkout `/Users/marcbreneiser/Code/ragged/` (authoritative). Box clone earlier had one env-only `:8000` fail under host-network; Mac default compose is clean.

## Commands

```bash
source api/.venv/bin/activate
pytest -m uat
pytest -m dogfood
```

## UAT

- Result: **11 passed**, 5 skipped (06–10), ~19s
- Slice 05 (`tests/uat/test_uat_slice05_documents.py`):
  - register → create thread "UAT docs"
  - POST exe-magic bytes as `malware.pdf` / `application/pdf` → **415**
  - GET documents → **200** and `[]`
- Regressions 01–04 green under the same run

## Dogfood

- Pending (Ragged Dogfood)

## UX notes (severity)

- Documents ingest is API-only until shell (slice 08) — **Low / expected**
- Nothing blocking for slice 05 UAT

## Open bugs

None for slice 05 product behavior (UAT).
