"""Tests for `pgman about`."""

import yaml


def _parse_docs(output: str) -> list[dict]:
    """Parse multi-document YAML from about command output."""
    return [doc for doc in yaml.safe_load_all(output) if doc is not None]


# ---------------------------------------------------------------------------
# Default (no-config) baseline
# ---------------------------------------------------------------------------


def test_about_exits_zero_with_no_config(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["about"])
    assert result.exit_code == 0, result.output


def test_about_output_is_valid_yaml(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["about"])
    docs = _parse_docs(result.output)
    assert len(docs) == 2


def test_about_doc1_structure(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["about"])
    doc1, _ = _parse_docs(result.output)
    assert doc1["name"] == "pgman"
    assert "version" in doc1
    assert "build_date" in doc1
    assert isinstance(doc1["config_files_loaded"], list)
    assert isinstance(doc1["config_files_failed"], list)
    assert isinstance(doc1["environment_variables"], dict)


def test_about_doc1_contains_all_env_vars(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["about"])
    doc1, _ = _parse_docs(result.output)
    env_vars = doc1["environment_variables"]
    assert "PGMAN_HOST" in env_vars
    assert "PGMAN_PORT" in env_vars
    assert "PGMAN_USERNAME" in env_vars
    assert "PGMAN_PASSWORD" in env_vars
    assert "PGMAN_DBNAME" in env_vars


def test_about_doc1_password_is_redacted(runner, clean_env, monkeypatch):
    from pgman.cli import cli

    monkeypatch.setenv("PGMAN_PASSWORD", "supersecret")
    result = runner.invoke(cli, ["about"])
    doc1, _ = _parse_docs(result.output)
    assert doc1["environment_variables"]["PGMAN_PASSWORD"] == "**REDACTED**"


def test_about_doc2_is_effective_config(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["about"])
    _, doc2 = _parse_docs(result.output)
    assert "host" in doc2
    assert "port" in doc2
    assert "username" in doc2
    assert "password" in doc2
    assert "dbname" in doc2


def test_about_doc2_password_is_redacted(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["about"])
    _, doc2 = _parse_docs(result.output)
    assert doc2["password"] == "**REDACTED**"


def test_about_doc2_port_is_integer(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["about"])
    _, doc2 = _parse_docs(result.output)
    assert isinstance(doc2["port"], int)


# ---------------------------------------------------------------------------
# Config file reflected in about output
# ---------------------------------------------------------------------------


def test_about_shows_loaded_config_file(runner, clean_env):
    from pgman.cli import cli

    tmp = clean_env
    (tmp / "pgman.yaml").write_text("host: myhost\n")
    result = runner.invoke(cli, ["about"])
    doc1, _ = _parse_docs(result.output)
    assert len(doc1["config_files_loaded"]) == 1
    assert doc1["config_files_loaded"][0].endswith("pgman.yaml")


# ---------------------------------------------------------------------------
# Global CLI flag overrides appear in effective config
# ---------------------------------------------------------------------------


def test_about_reflects_global_host_flag(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["-h", "flaghost", "about"])
    _, doc2 = _parse_docs(result.output)
    assert doc2["host"] == "flaghost"


def test_about_reflects_global_dbname_flag(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["-d", "flagdb", "about"])
    _, doc2 = _parse_docs(result.output)
    assert doc2["dbname"] == "flagdb"


# ---------------------------------------------------------------------------
# Quiet mode
# ---------------------------------------------------------------------------


def test_about_quiet_exits_zero(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["about", "--quiet"])
    assert result.exit_code == 0


def test_about_quiet_single_document(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["about", "-q"])
    docs = _parse_docs(result.output)
    assert len(docs) == 1


def test_about_quiet_contains_only_name_version_build_date(runner, clean_env):
    from pgman.cli import cli

    result = runner.invoke(cli, ["about", "-q"])
    doc = _parse_docs(result.output)[0]
    assert set(doc.keys()) == {"name", "version", "build_date"}
    assert doc["name"] == "pgman"
