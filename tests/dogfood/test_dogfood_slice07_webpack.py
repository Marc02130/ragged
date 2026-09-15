"""Slice 7 dogfood: load the login page from nginx, submit via /api."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice07,
    pytest.mark.skipif(not slice_ready(7), reason=skip_reason(7)),
]


def test_operator_sees_login_form(compose_stack: str) -> None:
    pytest.skip("login page dogfood when slice 7 lands")
