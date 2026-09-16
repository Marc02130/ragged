"""Slice 5 dogfood: upload a small PDF and see status ready."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice05,
    pytest.mark.skipif(not slice_ready(5), reason=skip_reason(5)),
]


def test_operator_uploads_a_pdf(compose_stack: str) -> None:
    pytest.skip("upload dogfood when slice 5 lands")
