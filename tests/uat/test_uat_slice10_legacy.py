"""Slice 10 UAT: Compose runtime has no Vite or Supabase app dependency."""

import json

import pytest

from tests.paths import COMPOSE, ROOT, WEB_PACKAGE
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice10,
    pytest.mark.skipif(not slice_ready(10), reason=skip_reason(10)),
]


def test_grep_vite_clean_in_runtime_trees() -> None:
    compose = COMPOSE.read_text().lower()
    assert "vite" not in compose
    assert "supabase" not in compose
    web = json.loads(WEB_PACKAGE.read_text())
    deps = {**web.get("dependencies", {}), **web.get("devDependencies", {})}
    assert "vite" not in deps
    assert "@vitejs/plugin-react" not in deps
    assert "@supabase/supabase-js" not in deps
    root = json.loads((ROOT / "package.json").read_text())
    assert "vite" not in json.dumps(root)
