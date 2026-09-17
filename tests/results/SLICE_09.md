# Slice 09 — Docs / smoke — test results

- **Branch:** feat/slice-09-docs
- **Date:** 2026-09-17 (America/New_York)
- **Gate:** PASS
- **Authority:** UAT by Ragged QA on Marc’s Mac; dogfood by Ragged Dogfood.

## UAT

- Result: **18 passed**, 2 skipped, ~10s
- Slice 09: `scripts/smoke.sh` executable; CI-skip guidance + sample.pdf + OPENAI/XAI keys
- Live-key operator smoke skipped without real key (expected)
- Regressions 01–08 + LLM settings / local embeddings green

## Dogfood

- Result: **11 passed**, 1 skipped (slice 10), ~19s
- README walk: compose up, PUBLIC_ORIGINS, COOKIE_SECURE, pg_dump, data/uploads, MiniLM/local
- LLM-settings + local-embeddings walks green
- Slice 06 in/out-of-corpus green on re-run

## UX notes (severity)

- Ask without chat keys → canned refusal — **Low / expected** (README documents need for API keys)
- Nothing blocking

## Open bugs

None for slice 09.
