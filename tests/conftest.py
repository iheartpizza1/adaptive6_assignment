"""Shared pytest fixtures: the committed sample log and the optional real data files."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _data_path(env_var: str, default: Path, what: str) -> Path:
    """Resolve a data file from an env var, then a repo-root default, else skip the test."""
    candidates = []
    if os.environ.get(env_var):
        candidates.append(Path(os.environ[env_var]))
    candidates.append(default)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    pytest.skip(f"{what} not found (set {env_var} or place it at {default})")


@pytest.fixture
def sample_log_path() -> Path:
    """The ~20 line committed fixture (see tests/fixtures/README.md)."""
    return FIXTURES_DIR / "sample.log"


@pytest.fixture
def apache_log_path() -> Path:
    """The real 10k line log: env APACHE_LOG, else ./apache_log.txt, else skip."""
    return _data_path("APACHE_LOG", REPO_ROOT / "apache_log.txt", "apache_log.txt")


@pytest.fixture
def geoip_db_path() -> Path:
    """The GeoLite2-Country MMDB: env GEOIP_DB, else ./data/GeoLite2-Country.mmdb, else skip."""
    return _data_path("GEOIP_DB", REPO_ROOT / "data" / "GeoLite2-Country.mmdb", "GeoLite2 MMDB")
