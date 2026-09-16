# Slice 05 — Documents — test results

- **Branch:** feat/slice-05-documents
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS (UAT portion for slice 05)
- **Authority:** Ragged QA. Mac machineId `32a32d52-29e1-4c22-bc6d-5d0f23d2e42b` ExternalShell not available to this executor (`/Users/marcbreneiser/Code/ragged/` not reachable). Ran against a clone of `feat/slice-05-documents` @ `6b9930e`. Artifact `api/app/routers/documents.py` present (unskips slice 05). Compose used host-network override because box bridge CNI blocked container→container TCP.

## Commands

```bash
source api/.venv/bin/activate
pytest -m uat -v --tb=short
```

## UAT

- Exact summary: **1 failed, 10 passed, 5 skipped, 51 deselected, 3 warnings in 4.59s**
- Slice 05 (`tests/uat/test_uat_slice05_documents.py`) **passed**:
  - Register → create thread `"UAT docs"`
  - POST `/api/threads/{id}/documents` with `malware.pdf` body `MZ` + nulls (exe magic bytes, `application/pdf`) → **415**
  - `GET /api/threads/{id}/documents` → **200** and `[]` (rejected upload not listed)
- Regressions slices 01–04 otherwise green under this stack
- The single failure is **env-only**, not product: `test_default_compose_does_not_publish_8000` — host-network override discards published ports so `compose ps` lacks `8080` (would not apply on Marc’s Mac default bridge compose)

## Dogfood

- Not run (slice 05 UAT-only request; dogfood file skimmed for awareness only)

## UX notes (severity)

- Documents ingest is API-only until shell (slice 08) — **Low / expected**
- Nothing blocking for slice 05 UAT

## Open bugs

- None for slice 05 product behavior.
- Executor note: re-run on Marc’s Mac checkout when ExternalShell is available to confirm slice01 port-publish UAT under default compose (expected PASS there).
