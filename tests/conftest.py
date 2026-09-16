import pytest

from tests import compose_support


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: fast tests with no Docker")
    config.addinivalue_line("markers", "uat: user-acceptance against the Compose stack")
    config.addinivalue_line("markers", "dogfood: live operator walkthrough of the running stack")


@pytest.fixture(scope="session")
def compose_stack():
    if not compose_support.docker_available():
        pytest.skip("docker is not available")
    url = compose_support.up()
    yield url
    if not compose_support.keep_compose():
        compose_support.down()
