"""Slice 6 UAT: canned refusal, no doubled history."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice06,
    pytest.mark.skipif(not slice_ready(6), reason=skip_reason(6)),
]


def test_empty_retrieval_returns_canned_refusal(compose_stack: str) -> None:
    pytest.skip("implemented when slice 6 lands")
