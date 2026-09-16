"""Slice 1 dogfood: sit down, start Compose, open the site, hit health."""

import httpx
import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice01,
    pytest.mark.skipif(not slice_ready(1), reason=skip_reason(1)),
]


def test_operator_opens_the_placeholder_and_health(compose_stack: str) -> None:
    home = httpx.get(f"{compose_stack}/", timeout=5.0)
    assert home.status_code == 200
    assert "RAGged" in home.text

    health = httpx.get(f"{compose_stack}/api/health", timeout=5.0)
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    icon = httpx.get(f"{compose_stack}/ragged.png", timeout=5.0)
    assert icon.status_code == 200
    assert icon.headers["content-type"].startswith("image/")
