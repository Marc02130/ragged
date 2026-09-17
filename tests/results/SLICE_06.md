# Slice 06 — Messages / RAG — test results

- **Branch:** feat/slice-06-messages
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS
- **Authority:** UAT by Ragged QA on Marc’s Mac; dogfood by Ragged Dogfood.

## Commands

```bash
source api/.venv/bin/activate
pytest -m uat
pytest -m dogfood
```

## UAT

- Result: **12 passed**, 4 skipped (07–10), ~19s
- Slice 06: canned refusal "I don't have that in your documents."; no top-level `response`; second turn → messages length **4**
- Regressions 01–05 green

## Dogfood

- Result: **6 passed** (01–06), 4 skipped, ~18s
- Operator: upload PDF → ask "what does the document say?" → non-canned answer with `sources`; empty thread → canned refusal with empty sources

## UX notes (severity)

- Still API-only chat (no shell UI) — **Low / expected**
- Refusal copy clear; sources on in-corpus answers good
- Nothing blocking

## Open bugs

None for slice 06.
