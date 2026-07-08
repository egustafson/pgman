"""Tests for `pgman listdbs`."""

import json

import psycopg2


def test_listdbs_text_without_owners(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchall.return_value = [("mydb",), ("postgres",)]

    result = runner.invoke(cli, ["listdbs"])
    assert result.exit_code == 0, result.output
    lines = result.output.split()
    assert "mydb" in lines
    assert "postgres" in lines


def test_listdbs_excludes_templates_via_query(runner, clean_env, mock_db):
    from pgman.cli import cli
    from tests.conftest import executed_statements

    conn, cur = mock_db
    cur.fetchall.return_value = [("mydb",)]

    result = runner.invoke(cli, ["listdbs"])
    assert result.exit_code == 0, result.output
    stmts = " ".join(executed_statements(cur))
    assert "datistemplate = false" in stmts


def test_listdbs_json_without_owners(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchall.return_value = [("mydb",), ("postgres",)]

    result = runner.invoke(cli, ["listdbs", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == ["mydb", "postgres"]


def test_listdbs_text_with_owners(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchall.return_value = [("mydb", "mydb_owner"), ("postgres", "postgres")]

    result = runner.invoke(cli, ["listdbs", "--with-owners"])
    assert result.exit_code == 0, result.output
    assert "NAME" in result.output
    assert "OWNER" in result.output
    assert "mydb" in result.output
    assert "mydb_owner" in result.output


def test_listdbs_json_with_owners(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchall.return_value = [("mydb", "mydb_owner")]

    result = runner.invoke(cli, ["listdbs", "--json", "--with-owners"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == [{"name": "mydb", "owner": "mydb_owner"}]


def test_listdbs_unknown_owner(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchall.return_value = [("orphan", None)]

    result = runner.invoke(cli, ["listdbs", "--json", "--with-owners"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == [{"name": "orphan", "owner": "unknown"}]


def test_listdbs_connect_failure_exits_nonzero(runner, clean_env, monkeypatch):
    from pgman.cli import cli

    monkeypatch.setattr(
        psycopg2, "connect", lambda **kw: (_ for _ in ()).throw(psycopg2.OperationalError("no"))
    )
    result = runner.invoke(cli, ["listdbs"])
    assert result.exit_code != 0
    assert "Failed to connect" in result.output
