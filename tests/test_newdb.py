"""Tests for `pgman newdb`."""

import psycopg2

from tests.conftest import executed_statements


def test_newdb_default_owner_and_generated_password(runner, clean_env, mock_db, monkeypatch):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = None  # role does not exist
    monkeypatch.setattr("pgman.commands.newdb.generate_password", lambda: "SECRET12345678")

    result = runner.invoke(cli, ["newdb", "mydb"])
    assert result.exit_code == 0, result.output
    assert 'Created database "mydb".' in result.output
    assert "mydb_owner" in result.output
    assert "SECRET12345678" in result.output
    assert conn.autocommit is True


def test_newdb_create_database_sql(runner, clean_env, mock_db, monkeypatch):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = None
    monkeypatch.setattr("pgman.commands.newdb.generate_password", lambda: "pw")

    result = runner.invoke(cli, ["newdb", "mydb"])
    assert result.exit_code == 0, result.output

    stmts = executed_statements(cur)
    create_db = next(s for s in stmts if "CREATE DATABASE" in s)
    assert '"mydb"' in create_db
    assert '"mydb_owner"' in create_db
    assert "'UTF8'" in create_db
    assert "'en_US.UTF-8'" in create_db
    assert "TEMPLATE template0" in create_db


def test_newdb_owner_role_created_without_superuser(runner, clean_env, mock_db, monkeypatch):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = None
    monkeypatch.setattr("pgman.commands.newdb.generate_password", lambda: "pw")

    result = runner.invoke(cli, ["newdb", "mydb"])
    assert result.exit_code == 0, result.output

    stmts = executed_statements(cur)
    create_role = next(s for s in stmts if "CREATE ROLE" in s)
    assert "LOGIN" in create_role
    assert "CREATEDB" in create_role
    assert "SUPERUSER" not in create_role


def test_newdb_dbowner_override(runner, clean_env, mock_db, monkeypatch):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = None
    monkeypatch.setattr("pgman.commands.newdb.generate_password", lambda: "pw")

    result = runner.invoke(cli, ["newdb", "mydb", "--dbowner", "custom_owner"])
    assert result.exit_code == 0, result.output
    assert "custom_owner" in result.output

    stmts = executed_statements(cur)
    create_db = next(s for s in stmts if "CREATE DATABASE" in s)
    assert '"custom_owner"' in create_db


def test_newdb_dbpassword_override_is_displayed(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = None

    result = runner.invoke(cli, ["newdb", "mydb", "--dbpassword", "hunter2pass"])
    assert result.exit_code == 0, result.output
    assert "hunter2pass" in result.output

    stmts = executed_statements(cur)
    create_role = next(s for s in stmts if "CREATE ROLE" in s)
    assert "'hunter2pass'" in create_role


def test_newdb_existing_role_is_reused(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = (1,)  # role already exists

    result = runner.invoke(cli, ["newdb", "mydb"])
    assert result.exit_code == 0, result.output
    assert "already existed" in result.output

    stmts = executed_statements(cur)
    assert not any("CREATE ROLE" in s for s in stmts)
    assert any("CREATE DATABASE" in s for s in stmts)


def test_newdb_failure_exits_nonzero(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = None
    cur.execute.side_effect = psycopg2.errors.DuplicateDatabase("already exists")

    result = runner.invoke(cli, ["newdb", "mydb"])
    assert result.exit_code != 0
    assert "Failed to create database" in result.output


def test_newdb_connect_failure_exits_nonzero(runner, clean_env, monkeypatch):
    from pgman.cli import cli

    monkeypatch.setattr(
        psycopg2, "connect", lambda **kw: (_ for _ in ()).throw(psycopg2.OperationalError("no"))
    )
    result = runner.invoke(cli, ["newdb", "mydb"])
    assert result.exit_code != 0
    assert "Failed to connect" in result.output
