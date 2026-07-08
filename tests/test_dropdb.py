"""Tests for `pgman dropdb`."""

import psycopg2

from tests.conftest import executed_statements


def test_dropdb_confirmation_match_drops(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = ("mydb_owner",)

    result = runner.invoke(cli, ["dropdb", "mydb"], input="mydb\n")
    assert result.exit_code == 0, result.output
    assert 'Dropped database "mydb".' in result.output

    stmts = executed_statements(cur)
    assert any('DROP DATABASE "mydb"' in s for s in stmts)
    assert conn.autocommit is True


def test_dropdb_confirmation_mismatch_aborts(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db

    result = runner.invoke(cli, ["dropdb", "mydb"], input="wrong\n")
    assert result.exit_code != 0
    assert "aborting" in result.output.lower()

    # No connection or drop should have occurred.
    assert psycopg2.connect.call_count == 0
    assert cur.execute.call_count == 0


def test_dropdb_skip_confirmation(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = ("mydb_owner",)

    result = runner.invoke(cli, ["dropdb", "mydb", "--i-really-really-mean-it"])
    assert result.exit_code == 0, result.output
    assert 'Dropped database "mydb".' in result.output


def test_dropdb_drops_owner_by_default(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = ("mydb_owner",)

    result = runner.invoke(cli, ["dropdb", "mydb"], input="mydb\n")
    assert result.exit_code == 0, result.output
    assert 'Dropped owner role "mydb_owner".' in result.output

    stmts = executed_statements(cur)
    assert any('DROP ROLE "mydb_owner"' in s for s in stmts)


def test_dropdb_keep_owner_retains_role(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = ("mydb_owner",)

    result = runner.invoke(cli, ["dropdb", "mydb", "--keep-owner"], input="mydb\n")
    assert result.exit_code == 0, result.output

    stmts = executed_statements(cur)
    assert any("DROP DATABASE" in s for s in stmts)
    assert not any("DROP ROLE" in s for s in stmts)


def test_dropdb_unresolved_owner_not_dropped(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = None  # owner cannot be resolved

    result = runner.invoke(cli, ["dropdb", "mydb"], input="mydb\n")
    assert result.exit_code == 0, result.output
    assert "could not be determined" in result.output

    stmts = executed_statements(cur)
    assert not any("DROP ROLE" in s for s in stmts)


def test_dropdb_shared_owner_not_dropped(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = ("postgres",)

    result = runner.invoke(cli, ["dropdb", "mydb"], input="mydb\n")
    assert result.exit_code == 0, result.output
    assert "retained shared role" in result.output.lower()

    stmts = executed_statements(cur)
    assert not any("DROP ROLE" in s for s in stmts)


def test_dropdb_owner_drop_failure_reports_retained(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = ("mydb_owner",)

    def execute(sql_obj, *args):
        from tests.conftest import render_sql

        if "DROP ROLE" in render_sql(sql_obj):
            raise psycopg2.errors.DependentObjectsStillExist("owner owns objects elsewhere")

    cur.execute.side_effect = execute

    result = runner.invoke(cli, ["dropdb", "mydb"], input="mydb\n")
    assert result.exit_code != 0
    assert 'Dropped database "mydb".' in result.output
    assert 'Retained owner role "mydb_owner"' in result.output


def test_dropdb_drop_database_failure_exits_nonzero(runner, clean_env, mock_db):
    from pgman.cli import cli

    conn, cur = mock_db
    cur.fetchone.return_value = ("mydb_owner",)
    cur.execute.side_effect = psycopg2.errors.InvalidCatalogName("does not exist")

    result = runner.invoke(cli, ["dropdb", "mydb"], input="mydb\n")
    assert result.exit_code != 0
    assert "Failed to drop database" in result.output


def test_dropdb_connect_failure_exits_nonzero(runner, clean_env, monkeypatch):
    from pgman.cli import cli

    monkeypatch.setattr(
        psycopg2, "connect", lambda **kw: (_ for _ in ()).throw(psycopg2.OperationalError("no"))
    )
    result = runner.invoke(cli, ["dropdb", "mydb", "--i-really-really-mean-it"])
    assert result.exit_code != 0
    assert "Failed to connect" in result.output
