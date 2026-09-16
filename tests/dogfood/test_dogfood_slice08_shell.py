"""Slice 8 dogfood: full UI — thread, upload, chat."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice08,
    pytest.mark.skipif(not slice_ready(8), reason=skip_reason(8)),
]


def test_operator_uses_the_spa(compose_stack: str) -> None:
    pytest.skip("SPA dogfood when slice 8 lands")
