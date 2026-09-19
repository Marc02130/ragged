# Tests

Conversion suite (pytest): see `tests/CONVERSION.md`.

```bash
python -m pip install -r api/requirements-dev.txt
pytest                 # unit
pytest -m uat          # Compose
pytest -m dogfood
cd web && npm test     # Jest
```

Query-path retrieval (rewrite / relative cutoff / citation override): `pytest tests/unit/test_unit_rewrite.py tests/unit/test_unit_classify.py` then `pytest -m 'uat or dogfood' -k query_rewrite`. Results: `tests/results/QUERY_REWRITE.md`.

The old Vitest/Supabase Edge Function tests were removed in slice 10.
