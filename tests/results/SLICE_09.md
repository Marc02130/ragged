# Slice 09 — Docs / smoke — test results

- **Branch:** feat/slice-09-docs
- **Date:** 2026-09-17 (America/New_York)
- **Gate:** PASS (UAT portion; dogfood re-run pending)
- **Authority:** Ragged QA on Marc’s Mac checkout.

## UAT

- Result: **18 passed**, 2 skipped, ~10s
- Slice 09: `scripts/smoke.sh` executable; text includes CI-skip guidance + sample.pdf + OPENAI/XAI keys
- Live-key operator smoke skipped without real key (expected)
- Regressions 01–08 + LLM settings / local embeddings green

## Dogfood

- Pending re-run after smoke-contract fix (prior README walk had passed)

## Open bugs

None for slice 09 UAT.
