# pgman — Implementation Plan

## Overview

Build `pgman`, a Python-based CLI utility for automating PostgreSQL management and maintenance tasks.

---

## Phase 1: Project Scaffolding

### 1.1 Repository Structure

```
pgman/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── pgman/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py              # Click group entry point
│       ├── config.py           # Configuration loading and merging
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── about.py
│       │   └── ping.py
│       └── db.py               # PostgreSQL connection helpers
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_about.py
│   └── test_ping.py
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── pyproject.toml
```

### 1.2 `pyproject.toml`

- Build backend: `hatchling` with `hatch-vcs` for version derived from git tags.
- Dependencies: `click`, `psycopg2-binary`, `pyyaml`.
- Dev/test dependencies: `pytest`, `pytest-cov`, `ruff`.
- Entry point: `pgman = "pgman.cli:cli"`.
- Ruff configured for linting and formatting.
- Recommended installation method documented as `uv tool install pgman`.

---

## Phase 2: Configuration System

### 2.1 Configuration Sources (in order of lowest → highest precedence)

1. Built-in defaults
2. File config: the **first** file found by searching the following locations in order (only one file is loaded):
   1. `./pgman.yaml` (current working directory)
   2. `$XDG_CONFIG_HOME/pgman/config.yaml` (defaults to `~/.config/pgman/config.yaml`)
3. Environment variables (`PGMAN_*`)
4. CLI flags

### 2.2 Supported Configuration Keys

```yaml
host: localhost          # PGMAN_HOST
port: 5432               # PGMAN_PORT
user: <current-user>     # PGMAN_USER
password: ""             # PGMAN_PASSWORD
dbname: postgres         # PGMAN_DBNAME
```

### 2.3 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PGMAN_HOST` | `localhost` | PostgreSQL server hostname |
| `PGMAN_PORT` | `5432` | PostgreSQL server port |
| `PGMAN_USER` | current OS user | PostgreSQL username |
| `PGMAN_PASSWORD` | *(empty)* | PostgreSQL password |
| `PGMAN_DBNAME` | `postgres` | Default database name |

### 2.4 `--config` / `-c` Flag

- When provided, the specified file is loaded directly; the default location search is skipped entirely.
- This is a global flag on the root `cli` group, passed via Click context.

### 2.5 Environment Variable Interpolation in Config Files

- Config file values may reference environment variables using `${VAR_NAME}` syntax.
- Documentation and examples should use `PGMAN_*` variable names for interpolation.

### 2.6 XDG Support

- Respect `XDG_CONFIG_HOME` when set; fall back to `~/.config`.

### 2.7 `config.py` Responsibilities

- Search default locations in order and load the **first** file found (stop after first match).
- If `-c`/`--config` is provided, load that file directly instead of searching.
- Track files that were found but failed to load (e.g. syntax errors).
- Apply environment variables over the file config, then CLI flags on top.
- Redact sensitive fields (`password`) for display.
- Return a structured config object/dict and a metadata object (file loaded, file failed if any, env vars applied).

---

## Phase 3: CLI Entry Point

### 3.1 Root Group (`cli.py`)

- Click group named `pgman`.
- Global options: `-c`/`--config` (path to config file).
- Loads configuration once and stores in Click context (`ctx.obj`).
- Subcommands registered: `about`, `ping`.

---

## Phase 4: `pgman about` Command

### 4.1 Behavior

- Runs successfully with no config files, environment variables, or CLI flags.
- Accepts `-q`/`--quiet` flag: when present, outputs only a single YAML document containing `name`, `version`, and `build_date`; all other output is suppressed.
- Default (non-quiet) mode outputs two YAML documents separated by `---`:

**Document 1 — About**
```yaml
name: pgman
version: <version from package metadata>
build_date: <ISO 8601 build/install date if available, else null>
config_files_loaded:
  - /home/user/.config/pgman/config.yaml
config_files_failed: []
environment_variables:
  PGMAN_HOST: localhost
  PGMAN_PORT: "5432"
  PGMAN_USER: ericg
  PGMAN_PASSWORD: "**REDACTED**"
  PGMAN_DBNAME: postgres
```

**Document 2 — Effective Configuration**
```yaml
host: localhost
port: 5432
user: ericg
password: "**REDACTED**"
dbname: postgres
```

- The second document is structurally identical to a valid config file (usable as one if saved to disk, with sensitive info redacted).

### 4.2 Implementation Notes

- Use `importlib.metadata.version("pgman")` for version.
- Sensitive fields: `password` → `**REDACTED**`.
- YAML output via `pyyaml` with `yaml.dump(..., default_flow_style=False)`.
- `-q`/`--quiet` suppresses everything except `name`, `version`, and `build_date` (single document, no config or env var details).

---

## Phase 5: `pgman ping` Command

### 5.1 Behavior

- Attempts a connection to PostgreSQL using resolved configuration.
- Reports success or failure with meaningful error context (auth failure, network error, etc.).
- Displays connection details used (host, port, dbname, user) — password redacted.

### 5.2 Optional Flags

| Flag | Description |
|---|---|
| `-d`, `--dbname` | Override the database name for this connection attempt |

### 5.3 Output (success)

```
Connected to PostgreSQL successfully.
  host:   localhost
  port:   5432
  dbname: postgres
  user:   ericg
```

### 5.4 Output (failure)

```
Failed to connect to PostgreSQL.
  host:   localhost
  port:   5432
  dbname: postgres
  user:   ericg
  error:  <error message>
```

- Exit with non-zero status on failure.

### 5.5 Implementation Notes

- Use `psycopg2.connect(...)` wrapped in try/except.
- Close connection immediately after successful connect (this is a ping, not a persistent session).
- Flag naming aligned with `psql` conventions (`-d`/`--dbname`).

---

## Phase 6: Open Source Files

### 6.1 `README.md`

- Project description and purpose.
- Installation instructions (`uv tool install pgman`).
- Quick start / usage examples for `about` and `ping`.
- Configuration reference (files, env vars, flags).
- Contributing pointer.

### 6.2 `CHANGELOG.md`

- Follow [Keep a Changelog](https://keepachangelog.com) format.
- Start with `[Unreleased]` section.

### 6.3 `CONTRIBUTING.md`

- Start minimal: how to set up dev environment, run tests, submit a PR.
- Expand over time as project grows.

### 6.4 `LICENSE`

- Already present in the repo.

---

## Phase 7: CI/CD (GitHub Actions)

### 7.1 Workflow: `ci.yml`

Triggered on: push to `main`, pull requests.

Steps:
1. Checkout code.
2. Set up Python (matrix: 3.11, 3.12).
3. Install `uv`.
4. Install dependencies via `uv sync`.
5. Run `ruff check .` (lint).
6. Run `ruff format --check .` (format check).
7. Run `pytest --cov=pgman` (tests with coverage).

---

## Phase 8: Testing

### 8.1 Coverage Goals

| Module | Tests |
|---|---|
| `config.py` | Default values, first-file-wins search, env var override, precedence order, redaction, XDG support, `--config` flag bypass, interpolation |
| `about` command | Output parses as valid YAML, two documents, redacted password, no-config baseline; `--quiet` emits only name/version/build_date |
| `ping` command | Success path (mock psycopg2), failure paths (auth, network), `--dbname` override, non-zero exit on failure |

### 8.2 Test Tooling

- `pytest` with fixtures in `conftest.py`.
- Mock `psycopg2.connect` for ping tests to avoid requiring a live database.
- Use `click.testing.CliRunner` for CLI invocation in tests.

---

## Implementation Order

1. `pyproject.toml` + project skeleton
2. `config.py` + tests
3. CLI root group (`cli.py`)
4. `about` command + tests
5. `ping` command + tests
6. Open source files (README, CHANGELOG, CONTRIBUTING)
7. GitHub Actions workflow
8. Final review and polish
