# Tests

Conversion suite (pytest): see `tests/CONVERSION.md`.

```bash
python -m pip install -r api/requirements-dev.txt
pytest                 # unit
pytest -m uat          # Compose
pytest -m dogfood
cd web && npm test     # Jest
```

The old Vitest/Supabase Edge Function tests were removed in slice 10.
