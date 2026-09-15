"""Slice 2 dogfood: inspect the DB the way an operator would."""

import pytest

from tests.slices import skip_reason, slice_ready

pytestmark = [
    pytest.mark.dogfood,
    pytest.mark.slice02,
    pytest.mark.skipif(not slice_ready(2), reason=skip_reason(2)),
]


def test_operator_can_describe_tables(compose_stack: str) -> None:
    pytest.skip("docker compose exec psql \\d when slice 2 lands")
