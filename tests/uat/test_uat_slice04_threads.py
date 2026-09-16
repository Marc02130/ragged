"""Slice 4 UAT: isolation — user B cannot see user A's thread."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice04,
    pytest.mark.skipif(not slice_ready(4), reason=skip_reason(4)),
]


def test_cross_user_thread_is_404(compose_stack: str) -> None:
    pytest.skip("implemented with auth helpers when slice 4 lands")
