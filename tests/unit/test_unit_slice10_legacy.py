"""Slice 10 unit: Vite/Supabase runtime trees are gone."""

import json

import pytest

from tests.paths import ROOT, VITE_CONFIG, WEB_PACKAGE
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice10,
    pytest.mark.skipif(not slice_ready(10), reason=skip_reason(10)),
]


def test_vite_and_supabase_runtime_removed() -> None:
    assert not VITE_CONFIG.exists()
    assert not (ROOT / "src" / "App.tsx").exists()
    assert not (ROOT / "supabase" / "functions").exists()
    assert not (ROOT / "example-code").exists()
    assert not (ROOT / "vitest.unit.config.ts").exists()
    root_pkg = ROOT / "package.json"
    assert root_pkg.exists()
    data = json.loads(root_pkg.read_text())
    assert "vite" not in json.dumps(data.get("scripts") or {})
    assert "vitest" not in json.dumps(data.get("devDependencies") or {})
    assert "@supabase" not in json.dumps(data)
    web = json.loads(WEB_PACKAGE.read_text())
    deps = {**web.get("dependencies", {}), **web.get("devDependencies", {})}
    assert "vite" not in deps
    assert "@supabase/supabase-js" not in deps
