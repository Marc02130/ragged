# Slice 08 — Shell — test results

- **Branch:** feat/slice-07-webpack (App.tsx on this branch; no separate feat/slice-08-shell on remote)
- **Date:** 2026-09-16 (America/New_York)
- **Gate:** PASS
- **Authority:** UAT by Ragged QA on Marc’s Mac; dogfood by Ragged Dogfood.

## UAT
- Overall: **14 passed**, 2 skipped, ~19s
- Slice 08: SPA shell strings — Create New Thread, assistant_message, exceeds 10MB limit; no saveMessage

## Dogfood
- Overall: **8 passed**, 2 skipped, ~15s
- Live UI walk: login solid; viewport + hashed CSS/JS OK

## UX notes (severity)
1. Sign-up fields placeholder-only vs login sr-only — **Low** (a11y inconsistency)
2. Thread switch clears in-session doc list; no fetch of existing docs — **Low** (UX gap)
3. Empty-state Create New Thread hover/focus thinner than auth buttons — **Low** (polish)
Nothing blocking.

## Open bugs
None blocking for slice 08.
