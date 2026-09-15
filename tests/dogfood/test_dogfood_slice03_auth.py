"""Slice 3 dogfood: register in the browser origin, refresh, still logged in."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice03,
    pytest.mark.skipif(not slice_ready(3), reason=skip_reason(3)),
]


def test_operator_registers_and_calls_me(compose_stack: str) -> None:
    pytest.skip("cookie session dogfood when slice 3 lands")
