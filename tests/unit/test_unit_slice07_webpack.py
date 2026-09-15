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
    pkg = json.loads(WEB_PACKAGE.read_text())
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    for forbidden in ("vite", "vitest", "@vitejs/plugin-react"):
        assert forbidden not in deps
