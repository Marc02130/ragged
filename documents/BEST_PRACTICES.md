# Maintainer Best Practices

This document covers practices specific to the current FastAPI, Webpack React, PostgreSQL/pgvector, and Docker Compose application.

## Preserve user and thread scope

- Use `get_current_user` and `get_owned_thread` on protected routes.
- Include `user_id` and `thread_id` in document, conversation, and retrieval queries.
- Return `404` for unowned resources so ownership is not disclosed.
- Keep cross-thread retrieval out unless it is deliberately designed, implemented, and tested.

RAGged does not use Supabase Row Level Security; server-side ownership checks are the security boundary.

## Keep retrieval grounded

- Never replace the canned no-results refusal with general-knowledge generation without a product decision.
- Keep source metadata attached to saved assistant messages.
- Treat role matches as boosts, while retaining hard citation/boilerplate exclusion by default.
- Test query-time citation overrides when changing DOI, PubMed, zero-width-character, or bibliography heuristics.
- Tune the relative score margin using representative corpora; do not reintroduce an undocumented fixed cosine threshold.

## Change embeddings safely

Stored vectors are tagged with `embedding_model`, and retrieval requires the configured model tag. A model or dimension change therefore needs an explicit migration/re-ingest plan. Changing only `.env` can make existing documents unsearchable.

Keep `EMBEDDING_PROVIDER=stub` in tests only.

## Handle uploads by status

- Use file signatures, server quotas, and extracted-content checks as authoritative.
- Expect per-file `failed` rows in a successful mixed batch.
- Expect `422` when every file in the request fails ingest.
- In clients, count `ready` documents rather than equating `201` with every file succeeding.
- Preserve sequential client upload unless concurrency and resource behavior are re-evaluated.

## Protect secrets and sessions

- Use a unique `JWT_SECRET` with at least 32 characters.
- Set exact production `PUBLIC_ORIGINS`.
- Enable secure cookies behind TLS.
- Never return stored provider keys.
- Do not log passwords, cookies, provider keys, or full private documents.
- Back up `.env`/secret-management data separately from normal source control.

## Operate persistent state deliberately

- Back up both PostgreSQL and the uploads volume.
- Avoid `docker compose down -v` and volume-pruning commands on installations with data.
- Review Alembic migrations before release.
- Test restore procedures, not only backup creation.

## Verification before merge

Run the smallest relevant checks first, followed by the broader suites:

```bash
pytest api/tests
pytest
cd web && npm test -- --runInBand
cd web && npm run build
```

Compose, UAT, dogfood, and live-provider tests have additional environment requirements; see `tests/README.md`.

When changing documentation, verify route names and response models against `api/app/routers/` and `api/app/schemas.py`, not historical PRDs or chat logs.
