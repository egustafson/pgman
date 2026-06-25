"""Tests for pgman.config."""

import getpass

from pgman.config import REDACTED, load_config, redact

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_defaults(clean_env):
    config, meta = load_config()
    assert config["host"] == "localhost"
    assert config["port"] == 5432
    assert config["username"] == getpass.getuser()
    assert config["password"] == ""
    assert config["dbname"] == "postgres"
    assert meta["config_files_loaded"] == []
    assert meta["config_files_failed"] == []
    assert meta["env_vars_applied"] == {}


# ---------------------------------------------------------------------------
# Config file loading
# ---------------------------------------------------------------------------


def test_loads_cwd_config_file(clean_env):
    tmp = clean_env
    (tmp / "pgman.yaml").write_text("host: file.host\n")
    config, meta = load_config()
    assert config["host"] == "file.host"
    assert str(tmp / "pgman.yaml") in meta["config_files_loaded"]


def test_loads_xdg_config_file(clean_env, monkeypatch):
    tmp = clean_env
    xdg_dir = tmp / "xdg"
    pgman_dir = xdg_dir / "pgman"
    pgman_dir.mkdir(parents=True)
    (pgman_dir / "config.yaml").write_text("host: xdg.host\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_dir))
    config, meta = load_config()
    assert config["host"] == "xdg.host"
    assert len(meta["config_files_loaded"]) == 1


def test_first_file_wins_cwd_over_xdg(clean_env, monkeypatch):
    tmp = clean_env
    (tmp / "pgman.yaml").write_text("host: cwd.host\n")
    xdg_dir = tmp / "xdg"
    (xdg_dir / "pgman").mkdir(parents=True)
    (xdg_dir / "pgman" / "config.yaml").write_text("host: xdg.host\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_dir))
    config, meta = load_config()
    assert config["host"] == "cwd.host"
    assert len(meta["config_files_loaded"]) == 1


def test_config_path_bypasses_default_search(clean_env):
    tmp = clean_env
    (tmp / "pgman.yaml").write_text("host: cwd.host\n")
    explicit = tmp / "explicit.yaml"
    explicit.write_text("host: explicit.host\n")
    config, meta = load_config(config_path=str(explicit))
    assert config["host"] == "explicit.host"
    assert str(explicit) in meta["config_files_loaded"]


def test_pgman_config_env_var_bypasses_default_search(clean_env, monkeypatch):
    tmp = clean_env
    (tmp / "pgman.yaml").write_text("host: cwd.host\n")
    custom = tmp / "custom.yaml"
    custom.write_text("host: custom.host\n")
    monkeypatch.setenv("PGMAN_CONFIG", str(custom))
    config, meta = load_config()
    assert config["host"] == "custom.host"


def test_missing_explicit_config_recorded_as_failed(clean_env):
    _, meta = load_config(config_path="/nonexistent/pgman.yaml")
    assert "/nonexistent/pgman.yaml" in meta["config_files_failed"]
    assert meta["config_files_loaded"] == []


def test_invalid_yaml_recorded_as_failed(clean_env):
    tmp = clean_env
    bad = tmp / "pgman.yaml"
    bad.write_text("host: [unclosed bracket\n")
    _, meta = load_config()
    assert str(bad) in meta["config_files_failed"]


def test_unknown_config_keys_are_ignored(clean_env):
    tmp = clean_env
    (tmp / "pgman.yaml").write_text("host: myhost\nunknown_key: ignored\n")
    config, _ = load_config()
    assert config["host"] == "myhost"
    assert "unknown_key" not in config


# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------


def test_env_var_host_override(clean_env, monkeypatch):
    monkeypatch.setenv("PGMAN_HOST", "env.host")
    config, meta = load_config()
    assert config["host"] == "env.host"
    assert meta["env_vars_applied"]["PGMAN_HOST"] == "env.host"


def test_env_var_port_coerced_to_int(clean_env, monkeypatch):
    monkeypatch.setenv("PGMAN_PORT", "5433")
    config, _ = load_config()
    assert config["port"] == 5433
    assert isinstance(config["port"], int)


def test_env_var_overrides_file(clean_env, monkeypatch):
    tmp = clean_env
    (tmp / "pgman.yaml").write_text("host: file.host\n")
    monkeypatch.setenv("PGMAN_HOST", "env.host")
    config, _ = load_config()
    assert config["host"] == "env.host"


# ---------------------------------------------------------------------------
# CLI overrides
# ---------------------------------------------------------------------------


def test_cli_override_beats_env(clean_env, monkeypatch):
    monkeypatch.setenv("PGMAN_HOST", "env.host")
    config, _ = load_config(cli_overrides={"host": "cli.host"})
    assert config["host"] == "cli.host"


def test_cli_none_values_are_ignored(clean_env, monkeypatch):
    monkeypatch.setenv("PGMAN_HOST", "env.host")
    config, _ = load_config(cli_overrides={"host": None})
    assert config["host"] == "env.host"


# ---------------------------------------------------------------------------
# Interpolation
# ---------------------------------------------------------------------------


def test_env_var_interpolation_in_config_file(clean_env, monkeypatch):
    tmp = clean_env
    monkeypatch.setenv("MY_DB_HOST", "interpolated.host")
    (tmp / "pgman.yaml").write_text("host: ${MY_DB_HOST}\n")
    config, _ = load_config()
    assert config["host"] == "interpolated.host"


def test_interpolation_missing_var_keeps_placeholder(clean_env):
    tmp = clean_env
    (tmp / "pgman.yaml").write_text("host: ${DOES_NOT_EXIST}\n")
    config, _ = load_config()
    assert config["host"] == "${DOES_NOT_EXIST}"


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


def test_redact_masks_password():
    config = {
        "host": "localhost",
        "port": 5432,
        "username": "alice",
        "password": "s3cr3t",
        "dbname": "mydb",
    }
    redacted = redact(config)
    assert redacted["password"] == REDACTED
    assert redacted["host"] == "localhost"
    assert redacted["port"] == 5432


def test_redact_does_not_mutate_original():
    config = {"password": "secret"}
    redact(config)
    assert config["password"] == "secret"
