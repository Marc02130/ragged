"""Session-scoped pgvector Testcontainers harness.

Repo-root `pytest` loads `tests/conftest.py` (same fixture) so this directory
is not on testpaths. Keep this file: `cd api && pytest` uses it.
"""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from testcontainers.postgres import PostgresContainer

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def _psycopg_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _upgrade(url: str) -> None:
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    if not shutil.which("docker"):
        pytest.skip("docker is not available")

    if os.environ.get("RAG_USE_COMPOSE_DB") == "1" and os.environ.get("DATABASE_URL"):
        url = _psycopg_url(os.environ["DATABASE_URL"])
        _upgrade(url)
        yield url
        return

    with PostgresContainer("pgvector/pgvector:pg16") as postgres:
        url = _psycopg_url(postgres.get_connection_url())
        os.environ["DATABASE_URL"] = url
        _upgrade(url)
        yield url
