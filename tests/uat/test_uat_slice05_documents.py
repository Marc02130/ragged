"""Slice 5 UAT: magic-byte reject and quota."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.uat,
    pytest.mark.slice05,
    pytest.mark.skipif(not slice_ready(5), reason=skip_reason(5)),
]


def test_exe_renamed_pdf_is_415(compose_stack: str) -> None:
    pytest.skip("implemented when slice 5 lands")
