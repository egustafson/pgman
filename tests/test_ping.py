"""Tests for `pgman ping`."""

from unittest.mock import MagicMock

import psycopg2

# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


def test_ping_success(runner, clean_env, monkeypatch):
    from pgman.cli import cli

    mock_conn = MagicMock()
    monkeypatch.setattr(psycopg2, "connect", MagicMock(return_value=mock_conn))
    result = runner.invoke(cli, ["ping"])
    assert result.exit_code == 0
    assert "Connected to PostgreSQL successfully" in result.output
    mock_conn.close.assert_called_once()


def test_ping_success_shows_connection_details(runner, clean_env, monkeypatch):
    from pgman.cli import cli

    monkeypatch.setattr(psycopg2, "connect", MagicMock(return_value=MagicMock()))
    result = runner.invoke(cli, ["ping"])
    assert "host:" in result.output
    assert "port:" in result.output
    assert "dbname:" in result.output
    assert "username:" in result.output


def test_ping_success_uses_global_flags(runner, clean_env, monkeypatch):
    from pgman.cli import cli

    captured = {}

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    monkeypatch.setattr(psycopg2, "connect", fake_connect)
    result = runner.invoke(cli, ["-h", "myhost", "-d", "mydb", "-P", "5433", "ping"])
    assert result.exit_code == 0
    assert captured["host"] == "myhost"
    assert captured["dbname"] == "mydb"
    assert captured["port"] == 5433


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------


def test_ping_auth_failure_exits_nonzero(runner, clean_env, monkeypatch):
    from pgman.cli import cli

    monkeypatch.setattr(
        psycopg2,
        "connect",
        MagicMock(side_effect=psycopg2.OperationalError("password authentication failed")),
    )
    result = runner.invoke(cli, ["ping"])
    assert result.exit_code != 0
    assert "Failed to connect" in result.output
    assert "password authentication failed" in result.output


def test_ping_network_failure_exits_nonzero(runner, clean_env, monkeypatch):
    from pgman.cli import cli

    monkeypatch.setattr(
        psycopg2,
        "connect",
        MagicMock(side_effect=psycopg2.OperationalError("could not connect to server")),
    )
    result = runner.invoke(cli, ["ping"])
    assert result.exit_code != 0
    assert "Failed to connect" in result.output


def test_ping_failure_shows_connection_details(runner, clean_env, monkeypatch):
    from pgman.cli import cli

    monkeypatch.setattr(
        psycopg2, "connect", MagicMock(side_effect=psycopg2.OperationalError("error"))
    )
    result = runner.invoke(cli, ["ping"])
    assert "host:" in result.output
    assert "port:" in result.output
    assert "dbname:" in result.output
    assert "username:" in result.output
    assert "error:" in result.output


# ---------------------------------------------------------------------------
# CLI root group flag tests
# ---------------------------------------------------------------------------


def test_root_group_unknown_flag_rejected(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["--not-a-real-flag", "ping"])
    assert result.exit_code != 0


def test_root_group_port_must_be_integer(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["-P", "notanint", "ping"])
    assert result.exit_code != 0
