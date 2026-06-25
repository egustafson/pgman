"""Shared pytest fixtures."""

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    """Clear all PGMAN_* env vars, clear XDG_CONFIG_HOME, and chdir to tmp_path.

    Returns tmp_path for convenience so tests can create config files there.
    """
    for var in (
        "PGMAN_CONFIG",
        "PGMAN_HOST",
        "PGMAN_PORT",
        "PGMAN_USERNAME",
        "PGMAN_PASSWORD",
        "PGMAN_DBNAME",
        "XDG_CONFIG_HOME",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    return tmp_path
