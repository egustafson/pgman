"""Configuration loading and merging for pgman.

Sources are applied in order of increasing precedence:
  1. Built-in defaults
  2. Config file (first found in default locations, or explicit path)
  3. Environment variables (PGMAN_*)
  4. CLI flag overrides
"""

import getpass
import os
import re
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Schema & defaults
# ---------------------------------------------------------------------------

DEFAULTS: dict[str, Any] = {
    "host": "localhost",
    "port": 5432,
    "username": getpass.getuser(),
    "password": "",
    "dbname": "postgres",
}

SENSITIVE_FIELDS: frozenset[str] = frozenset({"password"})

REDACTED = "**REDACTED**"

# Canonical ordering: (env_var_name, config_key)
# Used to build ENV_MAP and to ensure consistent display order everywhere.
_ENV_SCHEMA: list[tuple[str, str]] = [
    ("PGMAN_HOST", "host"),
    ("PGMAN_PORT", "port"),
    ("PGMAN_USERNAME", "username"),
    ("PGMAN_PASSWORD", "password"),
    ("PGMAN_DBNAME", "dbname"),
]

# env_var -> config_key
ENV_MAP: dict[str, str] = {env_var: key for env_var, key in _ENV_SCHEMA}

# config_key -> env_var  (reverse lookup)
KEY_TO_ENV: dict[str, str] = {key: env_var for env_var, key in _ENV_SCHEMA}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _interpolate(value: Any) -> Any:
    """Expand ``${VAR_NAME}`` references in string config values."""
    if not isinstance(value, str):
        return value
    return re.sub(
        r"\$\{([^}]+)\}",
        lambda m: os.environ.get(m.group(1), m.group(0)),
        value,
    )


def _interpolate_dict(data: dict) -> dict:
    return {k: _interpolate(v) for k, v in data.items()}


def _default_config_paths() -> list[Path]:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return [
        Path.cwd() / "pgman.yaml",
        Path(xdg_config_home) / "pgman" / "config.yaml",
    ]


def redact(config: dict) -> dict:
    """Return a copy of *config* with sensitive fields replaced by REDACTED."""
    return {k: REDACTED if k in SENSITIVE_FIELDS else v for k, v in config.items()}


# ---------------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------------


def load_config(
    config_path: str | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load and merge configuration from all sources.

    Parameters
    ----------
    config_path:
        Explicit path to a config file.  When provided (including via the
        ``PGMAN_CONFIG`` environment variable), the default location search is
        skipped entirely.
    cli_overrides:
        Dict of key/value pairs from CLI flags.  ``None`` values are ignored
        so that unset flags do not mask lower-precedence sources.

    Returns
    -------
    config:
        Fully merged configuration dict.
    metadata:
        Dict with keys ``config_files_loaded``, ``config_files_failed``, and
        ``env_vars_applied``.
    """
    config: dict[str, Any] = dict(DEFAULTS)
    metadata: dict[str, Any] = {
        "config_files_loaded": [],
        "config_files_failed": [],
        "env_vars_applied": {},
    }

    # ------------------------------------------------------------------
    # 1. File config
    # ------------------------------------------------------------------
    # Explicit path wins over PGMAN_CONFIG which wins over default search.
    file_to_load: Path | None = None
    if config_path:
        file_to_load = Path(config_path)
    elif pgman_config_env := os.environ.get("PGMAN_CONFIG"):
        file_to_load = Path(pgman_config_env)
    else:
        for path in _default_config_paths():
            if path.exists():
                file_to_load = path
                break

    if file_to_load is not None:
        try:
            with open(file_to_load) as fh:
                raw = yaml.safe_load(fh)
            if isinstance(raw, dict):
                valid_keys = {k: v for k, v in raw.items() if k in DEFAULTS}
                config.update(_interpolate_dict(valid_keys))
            metadata["config_files_loaded"].append(str(file_to_load))
        except Exception:
            metadata["config_files_failed"].append(str(file_to_load))

    # ------------------------------------------------------------------
    # 2. Environment variables
    # ------------------------------------------------------------------
    for env_var, key in _ENV_SCHEMA:
        value: str | None = os.environ.get(env_var)
        if value is not None:
            coerced: Any = value
            if key == "port":
                try:
                    coerced = int(value)
                except ValueError:
                    pass
            config[key] = coerced
            metadata["env_vars_applied"][env_var] = coerced

    # ------------------------------------------------------------------
    # 3. CLI overrides
    # ------------------------------------------------------------------
    if cli_overrides:
        for key, value in cli_overrides.items():
            if value is not None and key in config:
                config[key] = value

    return config, metadata
