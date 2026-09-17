"""Slice 10 dogfood: Compose is the start path; root npm is not Vite."""

import json

import httpx
import pytest

from tests.paths import ROOT
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice10,
    pytest.mark.skipif(not slice_ready(10), reason=skip_reason(10)),
]


def test_operator_cannot_npm_run_dev_vite(compose_stack: str) -> None:
    health = httpx.get(f"{compose_stack}/api/health", timeout=5.0)
    assert health.status_code == 200
    pkg = json.loads((ROOT / "package.json").read_text())
    scripts = pkg.get("scripts") or {}
    assert "vite" not in json.dumps(scripts)
    assert not (ROOT / "vite.config.ts").exists()
    home = httpx.get(f"{compose_stack}/", timeout=5.0)
    assert home.status_code == 200
