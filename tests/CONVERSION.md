# Container conversion tests

Run results: see `tests/results/`.

Three layers, ten slices. Default `pytest` runs **unit** only.

The legacy Vitest/Supabase suite (`tests/unit/*.ts`, `tests/integration`,
`tests/e2e`) was removed in slice 10. Historical setup discussions remain
under `ai_chats/`; they are not instructions for this suite.

| Layer | Command | What it is |
| --- | --- | --- |
| **Unit** | `pytest` or `pytest -m unit` | Fast, no Docker. Parses Compose/nginx/env, hits FastAPI `TestClient`. |
| **UAT** | `pytest -m uat` | Acceptance against `docker compose up`. Ports, proxies, body limits, later API contracts. |
| **Dogfood** | `pytest -m dogfood` | Operator walkthrough of the live stack the way a human uses it. |

Install into a venv (Homebrew Python is PEP 668 managed; do not pip-install system-wide):

```bash
python3 -m venv api/.venv
source api/.venv/bin/activate
pip install -r api/requirements-dev.txt
pytest                 # unit
pytest -m uat          # needs Docker
pytest -m dogfood      # needs Docker
```

Without activating:

```bash
api/.venv/bin/pip install -r api/requirements-dev.txt
api/.venv/bin/pytest
```

UAT and dogfood need Docker. They copy `.env.example` → `.env` if missing, then `docker compose up --build -d`. Set `RAG_KEEP_COMPOSE=1` to leave the stack running.

Filenames are unique per layer (`test_unit_slice01_…`, `test_uat_slice01_…`, `test_dogfood_slice01_…`) so pytest can collect all three.

All slice artifacts have landed. The table below records the `skipif` artifact
each conversion test used while the migration was in progress; it remains
useful when running the suite against an older conversion commit.

| Slice | Artifact that unskips tests |
| --- | --- |
| 01 scaffold | `api/app/main.py` + `docker-compose.yml` |
| 02 schema | `api/alembic/versions/0001_initial.py` |
| 03 auth | `api/app/routers/auth.py` |
| 04 threads | `api/app/routers/threads.py` |
| 05 ingest | `api/app/routers/documents.py` |
| 06 RAG | `api/app/routers/messages.py` |
| 07 webpack | `web/webpack.config.js` |
| 08 shell | `web/src/App.tsx` |
| 09 smoke | `scripts/smoke.sh` |
| 10 legacy gone | `vite.config.ts` deleted |
