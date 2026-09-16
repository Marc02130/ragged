"""Slice 6 dogfood: ask an in-corpus question and an out-of-corpus question."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice06,
    pytest.mark.skipif(not slice_ready(6), reason=skip_reason(6)),
]


def test_operator_asks_in_and_out_of_corpus(compose_stack: str) -> None:
    pytest.skip("RAG dogfood when slice 6 lands")
