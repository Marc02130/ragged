# Slice 08 — SPA shell — test results

- **Branch:** feat/slice-07-webpack
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS (UAT portion; dogfood pending)
- **Authority:** Ragged QA. Marc’s Mac is authoritative when available.
- **Note:** Both webpack and `App.tsx` are on `feat/slice-07-webpack`. There is no separate `feat/slice-08-shell` on remote.

## Commands

```bash
source api/.venv/bin/activate
pytest -m uat
pytest -m dogfood
```

## UAT (`tests/uat/test_uat_slice08_shell.py`)

- Case: SPA shell loads
  - GET `/` → **200**; hashed `/assets/*.js` present and **200**
  - Bundle contains `Create New Thread`, `assistant_message`, and `exceeds 10MB limit`
  - Bundle does **not** contain `saveMessage`
- Overall Mac expected if the stack is clean: **14 passed / 2 skipped** (slices 09–10). Parent will confirm.

## Dogfood

Pending.

## UX notes (severity)

- Shell copy and 10MB upload limit are asserted from the hashed bundle, not a browser click-through — **Low / expected** until dogfood
- Threads, upload, and chat UI ship with this branch; operator flow remains dogfood — **Low / expected**
- Nothing blocking the UAT gate

## Open bugs

None for product.
