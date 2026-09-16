"""Slice 8 UAT: thread sidebar, upload, chat on the live SPA."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice08,
    pytest.mark.skipif(not slice_ready(8), reason=skip_reason(8)),
]


def test_spa_shell_loads(compose_stack: str) -> None:
    pytest.skip("implemented when slice 8 lands")
