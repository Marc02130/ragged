"""Slice 7 UAT: production webpack assets behind nginx."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice07,
    pytest.mark.skipif(not slice_ready(7), reason=skip_reason(7)),
]


def test_hashed_assets_and_login_form(compose_stack: str) -> None:
    pytest.skip("implemented when slice 7 lands")
