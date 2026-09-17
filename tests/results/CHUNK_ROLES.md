# Chunk roles — test results

- **Branch:** `feat/chunk-roles` @ `f1e3e43a4e583fb75a0c5e605c71a053d9d4cbd9` (`feat(api): chunk roles so queries skip citations and boilerplate`, 2026-09-17 11:12:06 EDT)
- **Date:** 2026-09-17 (America/New_York)
- **Gate:** **PASS** (UAT; dogfood pending)
- **Authority:** UAT by Ragged QA on **box clone** (Mac ExternalShell / machineId `32a32d52-29e1-4c22-bc6d-5d0f23d2e42b` path `/Users/marcbreneiser/Code/ragged/` **unreachable** from this agent). Dogfood not run.

## Feature summary (from PRD / commit / tests — not invented)

Label every chunk with a **role** (`claim`, `finding`, `evaluation`, `method`, `context`, `experience`, `citation`, `boilerplate`). Classify the question into the same roles; retrieve matching chunks; **drop citation and boilerplate** unless the user asks for them. Ingest uses heading-aware split + `classify_chunk`; query expands with last 2 user turns, filters by `allowed_roles`, with nearest-k fallback that still excludes bibliography/boilerplate. Unlabeled historical chunks are classified at query time.

## Commands

```bash
# Prefer Mac (unreachable this run):
# cd /Users/marcbreneiser/Code/ragged && git checkout feat/chunk-roles && git pull
# source api/.venv/bin/activate && pytest -m uat -v --tb=short
# pytest -k 'chunk_role or classify or flexible_search' -m 'not dogfood' -v --tb=short

# Box fallback (this run):
cd /workspace/ragged
git fetch origin feat/chunk-roles
git checkout -B feat/chunk-roles FETCH_HEAD   # f1e3e43
# Host-network override required: Docker bridge TCP api→db timed out on this box
# (untracked docker-compose.override.yml: network_mode host + /tmp/ragged-web-host/nginx.conf)
source api/.venv/bin/activate
export RAG_KEEP_COMPOSE=1
pytest -m uat -v --tb=short
pytest tests/unit/test_unit_classify.py tests/unit/test_unit_flexible_search.py -v --tb=short
pytest -k 'chunk_role or classify or flexible_search' -m 'not dogfood' -v --tb=short
# dogfood not run
```

## Unit (chunk-roles specific)

- `tests/unit/test_unit_classify.py` + `tests/unit/test_unit_flexible_search.py`: **13 passed** (~7.9s)
- Combined `-k 'chunk_role or classify or flexible_search' -m 'not dogfood'`: **14 passed** (includes UAT chunk-roles test)

Key unit assertions verified:

- Bibliography / References heading → `citation`; GraphPad/Mann-Whitney → `method`; “we hypothesize” → `claim`; “we found” → `finding`; diary-style → `experience`
- `allowed_roles("what hypotheses have the best evidence")` includes finding+claim, excludes citation/boilerplate
- Instrumentation query includes `method`; default query uses `DEFAULT_RETRIEVE`
- Headings taken from paper text (not fixed IMRaD list); heading boost; follow-up `expand_query` keeps prior user turns in embed text

## UAT

- Full-suite summary: **19 passed**, **1 failed** (slice01 env-only), **1 skipped**, 81 deselected, ~7.0s (after healthy compose)
- New UAT `tests/uat/test_uat_chunk_roles.py` — `test_evidence_query_skips_reference_block`: **PASSED**
- Key assertions (green):
  - Upload fixture with hypothesis/results + References DOI block
  - Ask “what hypotheses have the best evidence”
  - Sources/content must not include `doi.org` / PRISMA DOI; not canned-only without sources; preferred content contains hypothesize / we found
- Regressions 02–10 + LLM settings / local embeddings green under the same run
- Slice 09 live-key smoke: **SKIPPED** (`no live OPENAI_API_KEY`) — expected
- Slice01 `test_default_compose_does_not_publish_8000`: **FAIL (env-only)** — host-network `docker-compose.override.yml` means `docker compose ps` ports string has no `8080` publish mapping; **not a product defect** on `feat/chunk-roles`

### Compose note (box env)

1. First `pytest -m uat` errored: `docker compose up --build` left `api` unhealthy — bridge network: api TCP to `db:5432` timed out.
2. Restored box-local host-network override (same class as prior slice QA). Stack healthy; health `{"status":"ok"}` on `:8080`.

## Dogfood

- Not run (deferred to Ragged Dogfood per Ragged QA brief)
- Present on branch: `tests/dogfood/test_dogfood_chunk_roles.py` — follow-up “best evidence” after mechanisms question must return sources or content

## UX notes

- No dedicated UI for roles in v1 (PRD: descriptions explain the system in the UI later)
- Prompt now may include `heading` / `role` as **location hints only**, not extra facts
- Operator-visible win: evidence / hypothesis follow-ups should stop answering from bibliography DOI dumps

## Open bugs / blockers

1. Env-only: slice01 `:8000`/`:8080` publish assertion under host-network `docker-compose.override.yml` (same class as slices 07–10 box runs)
2. Box Docker bridge: container-to-container TCP to `db:5432` timed out without host-network override — environment issue, not product
3. Results PR opened from `qa/chunk-roles-uat-results` into `feat/chunk-roles` when applicable

## Remote status

- **Local results path:** `/workspace/ragged/tests/results/CHUNK_ROLES.md`
- Dogfood focus for Ragged Dogfood: same-thread mechanisms → “what hypotheses have the best evidence” on real PDFs; confirm sources are claim/finding/evaluation text, not References; optional instrumentation / personal-experience queries
