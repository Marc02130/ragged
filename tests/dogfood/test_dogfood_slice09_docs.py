"""Slice 9 dogfood: follow the README from a clean checkout."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice09,
    pytest.mark.skipif(not slice_ready(9), reason=skip_reason(9)),
]


def test_operator_follows_readme(compose_stack: str) -> None:
    pytest.skip("README walkthrough when slice 9 lands")
