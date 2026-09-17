"""Slice 7 unit: Webpack 5 SPA foundation, no Vite."""

import json

import pytest

from tests.paths import WEB_PACKAGE, WEBPACK
from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.unit,
    pytest.mark.slice07,
    pytest.mark.skipif(not slice_ready(7), reason=skip_reason(7)),
]


def test_webpack_public_path_and_no_vite() -> None:
    webpack = WEBPACK.read_text()
    assert "publicPath: '/'" in webpack or 'publicPath: "/"' in webpack
    assert "assets/[name].[contenthash].js" in webpack
    assert "assets/[name].[contenthash].css" in webpack
    pkg = json.loads(WEB_PACKAGE.read_text())
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    for forbidden in ("vite", "vitest", "@vitejs/plugin-react"):
        assert forbidden not in deps
    scripts = pkg.get("scripts", {})
    assert "vite" not in json.dumps(scripts)


def test_api_ts_prefixes_api() -> None:
    from tests.paths import ROOT

    api_ts = (ROOT / "web" / "src" / "lib" / "api.ts").read_text()
    assert "const API_BASE = '/api'" in api_ts
    assert "credentials: 'include'" in api_ts
    assert "ragged:unauthorized" in api_ts
    assert "VITE_" not in api_ts
