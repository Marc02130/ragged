"""Slice 4 dogfood: create, archive, restore, delete a thread."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice04,
    pytest.mark.skipif(not slice_ready(4), reason=skip_reason(4)),
]


def test_operator_thread_lifecycle(compose_stack: str) -> None:
    pytest.skip("thread lifecycle dogfood when slice 4 lands")
