"""Slice 10 dogfood: only the Compose app is startable."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice10,
    pytest.mark.skipif(not slice_ready(10), reason=skip_reason(10)),
]


def test_operator_cannot_npm_run_dev_vite(compose_stack: str) -> None:
    pytest.skip("legacy gone dogfood when slice 10 lands")
