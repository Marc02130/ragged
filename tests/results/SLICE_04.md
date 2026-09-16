# Slice 04 — Threads — test results

- **Branch:** feat/slice-04-threads
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS
- **Authority:** Slice 04 UAT + dogfood executed against a clone of `feat/slice-04-threads` (Mac machineId `32a32d52-29e1-4c22-bc6d-5d0f23d2e42b` ExternalShell not available to this executor; local `/Users/marcbreneiser/Code/ragged/` not reachable). Artifact `api/app/routers/threads.py` present (unskips slice 04). Compose used host-network override because box bridge CNI blocked container→container TCP.

## Commands

```bash
source api/.venv/bin/activate
pytest -m uat -v --tb=short
pytest -m dogfood -v --tb=short
```

## UAT

- Exact summary: **1 failed, 9 passed, 6 skipped, 45 deselected, 3 warnings in 15.40s**
- Slice 04 (`tests/uat/test_uat_slice04_threads.py`) **passed**:
  - Alice registers, creates thread "Alice secret" → 201
  - Bob registers; `GET /api/threads` → `[]`; archive/delete Alice’s thread id → **404** (cross-user isolation)
- Regression slices 01–03 assertions otherwise green under this stack
- The single failure is **env-only**, not product: `test_default_compose_does_not_publish_8000` — host-network override discards published ports so `compose ps` lacks `8080` (would not apply on Marc’s Mac default bridge compose)

## Dogfood (`tests/dogfood/test_dogfood_slice04_threads.py`)

- Exact summary: **4 passed, 6 skipped, 51 deselected, 3 warnings in 27.49s**
- Slice 04 operator lifecycle **passed**: register → create "Lab notes" → listed → archive (`status=archived`, list empty) → restore (`status=active`) → delete 204 → list empty

## UX notes (severity)

- Threads are API-only until shell (slice 08) — **Low / expected** (no UI surface yet)
- Nothing blocking for slice 04

## Open bugs

- None for slice 04 product behavior.
- Executor note: re-run on Marc’s Mac checkout when ExternalShell is available to confirm slice01 port-publish UAT under default compose (expected PASS there).
