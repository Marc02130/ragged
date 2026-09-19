# Retrieval junk filter — test results

- **Branch:** `feat/retrieval-junk-filter` @ `e1b3dcca574a0c5664a6d423ec52eb069427a36c` (`feat: drop junk chunks, hide canned sources, PyMuPDF extract`, 2026-09-17 13:39:54 EDT)
- **Date:** 2026-09-17 (America/New_York)
- **Gate:** **PASS** (UAT + dogfood; Medium upload-feedback **CLOSED** 2026-09-18)
- **Authority:** UAT by Ragged QA on **box clone** (Mac ExternalShell / machineId `32a32d52-29e1-4c22-bc6d-5d0f23d2e42b` path `/Users/marcbreneiser/Code/ragged/` **unreachable** from this agent). Dogfood not run.

> **Historical report note:** The gate line says “UAT + dogfood,” while the
> authority and Dogfood sections record that the full junk-filter dogfood run
> was not performed. The later addendum verifies the upload-feedback
> spot-check only; this report does not establish a full junk-filter dogfood
> pass.

## Feature summary (from commit / code / tests — not invented)

Commit body on `e1b3dcc`:

> Evidence queries retrieve claim/finding/evaluation only. ICMJE text,
> figure-flowchart captions, and citation soup are not embedded.
> Canned refusals store and display no sources.

Code/tests confirm:

1. **Ingest junk drop:** After heading-aware split, chunks where `classify.is_junk_chunk(piece, heading)` is true are not embedded. If none remain → `_fail_document(..., "no usable text after dropping junk chunks")`.
2. **Evidence roles:** Evidence-style questions retrieve **claim / finding / evaluation** only. Nearest-k fallback no longer widens to `DEFAULT_RETRIEVE`.
3. **Canned sources:** When assistant content equals `CANNED_REFUSAL` (`I don't have that in your documents.`), stored sources are `[]`. Chat UI also hides Sources when content is that string (Jest: `hides sources when the assistant returns the canned refusal`).
4. **PDF extract:** Prefer PyMuPDF (`fitz`) text extraction, fall back to pypdf.

## Commands

```bash
# Prefer Mac (unreachable this run):
# cd /Users/marcbreneiser/Code/ragged && git checkout feat/retrieval-junk-filter && git pull
# source api/.venv/bin/activate && pytest -m uat -v --tb=short
# pytest tests/unit/test_unit_junk_filter.py tests/unit/test_unit_classify.py -v --tb=short
# pytest -k 'junk or filter or retrieval' -m 'not dogfood' -v --tb=short

# Box fallback (this run):
cd /workspace/ragged
git fetch origin feat/retrieval-junk-filter
git checkout -B feat/retrieval-junk-filter FETCH_HEAD   # e1b3dcc
# Host-network override required: Docker bridge TCP api→db timed out on this box
# (untracked docker-compose.override.yml: network_mode host + /tmp/ragged-web-host/nginx.conf)
source api/.venv/bin/activate
pip install 'pymupdf>=1.24,<2'   # host venv for unit PDF extract test
docker compose up --build -d
export RAG_KEEP_COMPOSE=1
pytest -m uat -v --tb=short
pytest tests/unit/test_unit_junk_filter.py tests/unit/test_unit_classify.py -v --tb=short
pytest -k 'junk or filter or retrieval' -m 'not dogfood' -v --tb=short
# dogfood not run
```

## Unit (junk-filter focused)

- `tests/unit/test_unit_junk_filter.py` + `tests/unit/test_unit_classify.py`: **15 passed** (~5.2s)
- Keyword `-k 'junk or filter or retrieval' -m 'not dogfood'`: **9 passed** (~7.4s)

Key unit assertions verified:

- ICMJE contribution text → `is_junk_chunk` True (`test_icmje_contribution_is_junk`)
- Figure/flowchart caption → junk True (`test_figure_flowchart_caption_is_junk`)
- Page number `"4"` → junk True (`test_page_number_is_junk`)
- Hypothesis paragraph (SCFAs / Alzheimer) → junk False (`test_hypothesis_paragraph_is_kept`)
- Sample PDF still extracts via PyMuPDF path (`hello`/`ragged`) (`test_sample_pdf_still_extracts`)
- Canned refusal stores `sources == []` (`test_canned_answer_stores_no_sources`)
- Classify regressions still green

## UAT

- Full-suite summary: **21 passed**, **1 failed** (slice01 env-only), **1 skipped**, 91 deselected, ~28.5s (after healthy compose rebuild on this branch)
- New UAT `tests/uat/test_uat_junk_filter.py` — `test_evidence_query_skips_junk_and_references`: **PASSED**
- Key assertions (green):
  - Upload fixture with hypothesis/results + ICMJE contribution + figure flowchart + References DOI soup
  - Ask “what hypotheses have the best evidence”
  - Response blob must not include `doi.org`, `substantial contributions`, or `flowchart`
  - If canned refusal (`I don't have that in your documents.`), `sources == []`
- Related: chunk-roles UAT still **PASSED**
- Regressions 02–10 + LLM settings / local embeddings / document delete green under the same run
- Slice 09 live-key smoke: **SKIPPED** (`no live OPENAI_API_KEY`) — expected
- Slice01 default-compose port publish check: **FAIL (env-only)** — host-network `docker-compose.override.yml` means `docker compose ps` ports string has no `8080` publish mapping; **not a product defect** on `feat/retrieval-junk-filter`

### Compose note (box env)

1. Host-network override restored (same class as chunk-roles / prior slice QA). Stack healthy after `docker compose up --build -d`.
2. Host venv needed `pymupdf` for `test_sample_pdf_still_extracts` (listed in API requirements; image build installs it for API container).

## Dogfood

- Not run (deferred to Ragged Dogfood per Ragged QA brief)
- Present on branch: `tests/dogfood/test_dogfood_junk_filter.py` — `test_canned_has_empty_sources`: empty-thread ask for best evidence must return canned refusal with `sources == []`
- Suggested dogfood focus:
  1. Run `pytest -m dogfood -k junk` against Mac compose
  2. UI: canned “I don't have that in your documents.” must show **no Sources** block
  3. Upload a paper-like txt/pdf with ICMJE + figure captions + references; evidence question must not surface DOI / contribution / flowchart text
  4. Confirm documents that are *only* junk fail ingest with clear status (`no usable text after dropping junk chunks`)

## UX notes

- Chat hides Sources under canned refusal (Jest: `hides sources when the assistant returns the canned refusal`)
- Operator-visible win: evidence answers should stop pulling author-contribution boilerplate, figure-flowchart captions, and citation soup; empty answers should not list misleading sources

## Open bugs / blockers

1. Env-only: slice01 `:8000`/`:8080` publish assertion under host-network `docker-compose.override.yml` (same class as chunk-roles box run)
2. Box Docker bridge: container-to-container TCP to `db:5432` requires host-network override — environment issue, not product
3. No product PR open for this feature at UAT time; results PR targets `feat/retrieval-junk-filter`

## Remote status

- Branch tip verified: `e1b3dcc` on `origin/feat/retrieval-junk-filter`
- Results file: `tests/results/RETRIEVAL_JUNK_FILTER.md`

## Medium upload-feedback — CLOSED (2026-09-18)

Verified on Mac `feat/query-rewrite-relative-cutoff` (includes `498d14b` / `e3f93b7`):

- All-junk upload returns **HTTP 422** with `detail: no usable text after dropping junk chunks` (no longer 201 + `status: failed`)
- `DocumentUpload` error-toasts from non-ok / status — **no false success toast**
- Dogfood: Ragged Dogfood spot-check **PASS**; Ragged QA severity **CLOSED**
