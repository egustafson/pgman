"""Shared pytest fixtures."""

from unittest.mock import MagicMock

import psycopg2
import pytest
from click.testing import CliRunner
from psycopg2 import sql


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


@pytest.fixture
def mock_db(monkeypatch):
    """Patch psycopg2.connect and return (conn, cursor) mocks.

    The cursor is exposed both directly and through the ``with conn.cursor()``
    context-manager protocol used by the admin commands.
    """
    cur = MagicMock(name="cursor")
    conn = MagicMock(name="connection")
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = False
    monkeypatch.setattr(psycopg2, "connect", MagicMock(return_value=conn))
    return conn, cur


def render_sql(obj) -> str:
    """Render a psycopg2.sql Composed/plain query into an inspectable string.

    Not a faithful libpq rendering, but sufficient to assert on identifiers,
    literals, and keywords in tests without a live database.
    """
    if isinstance(obj, str):
        return obj
    if isinstance(obj, sql.SQL):
        return obj.string
    if isinstance(obj, sql.Identifier):
        return '"' + '"."'.join(obj.strings) + '"'
    if isinstance(obj, sql.Literal):
        return f"'{obj.wrapped}'"
    if isinstance(obj, sql.Composed):
        return "".join(render_sql(part) for part in obj.seq)
    return str(obj)


def executed_statements(cur) -> list[str]:
    """Return all SQL passed to ``cur.execute``, rendered via :func:`render_sql`."""
    return [render_sql(call.args[0]) for call in cur.execute.call_args_list]
