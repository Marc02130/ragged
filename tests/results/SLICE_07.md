# Slice 07 — Webpack production assets — test results

- **Branch:** feat/slice-07-webpack
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS (UAT portion; dogfood pending)
- **Authority:** Ragged QA. Marc’s Mac is authoritative when available.
- **Note:** Webpack (slice 07) and the SPA shell (`App.tsx`, slice 08) both live on `feat/slice-07-webpack`. There is no separate `feat/slice-08-shell` on remote.

## Commands

```bash
source api/.venv/bin/activate
pytest -m uat
pytest -m dogfood
```

## UAT (`tests/uat/test_uat_slice07_webpack.py`)

- Case: hashed assets + login form
  - GET `/` → **200** and `#root` (`id=root` or `id="root"`)
  - GET `/ragged.png` → **200**
  - Hashed `/assets/*.js` and `/assets/*.css` from the document → **200**
  - JS body contains `auth/login`
- Overall Mac expected if the stack is clean: **14 passed / 2 skipped** (slices 09–10), because slice 08 is also on this branch. Parent will confirm.

## Dogfood

Pending.

## UX notes (severity)

- Production webpack SPA replaces the slice-01 placeholder page; hashed JS/CSS and the login form are in the UAT path — **Low / expected**
- Full operator click-through of login is dogfood, not this UAT — **Low / expected**
- Nothing blocking the UAT gate

## Open bugs

None for product.
