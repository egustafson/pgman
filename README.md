# pgman

A Python CLI utility for automating PostgreSQL management and maintenance tasks.

## Installation

```sh
uv tool install pgman
```

## Quick Start

```sh
# Display version, configuration sources, and effective settings
pgman about

# Test database connectivity
pgman ping

# Connect to a specific host and database
pgman -h db.example.com -d myapp ping
```

## Commands

### `pgman about`

Displays pgman version, loaded config files, active environment variables, and the effective
merged configuration. Output is valid multi-document YAML, making it easy to parse or redirect.

```sh
pgman about          # full output (two YAML documents)
pgman about --quiet  # single document: name, version, build_date only
```

**Example output:**

```yaml
---
name: pgman
version: 1.0.0
build_date: 2026-01-15T10:30:00+00:00
config_files_loaded:
  - /home/alice/.config/pgman/config.yaml
config_files_failed: []
environment_variables:
  PGMAN_HOST: localhost
  PGMAN_PORT: '5432'
  PGMAN_USERNAME: alice
  PGMAN_PASSWORD: '**REDACTED**'
  PGMAN_DBNAME: postgres
---
host: localhost
port: 5432
username: alice
password: '**REDACTED**'
dbname: postgres
```

### `pgman ping`

Tests connectivity to the PostgreSQL server using the resolved configuration, then reports
success or failure with connection details.

```sh
pgman ping
pgman -h db.example.com -u myuser ping
```

---

## Configuration

Configuration is resolved from multiple sources, applied in order of increasing precedence:

1. **Built-in defaults**
2. **Config file** (first found)
3. **Environment variables** (`PGMAN_*`)
4. **Global CLI flags**

### Config File

pgman searches for a config file in the following locations (first found wins; only one file
is loaded):

1. `./pgman.yaml` — current working directory
2. `$XDG_CONFIG_HOME/pgman/config.yaml` — defaults to `~/.config/pgman/config.yaml`

Use `-c`/`--config` or `PGMAN_CONFIG` to specify a custom path; this skips the default search.

#### Example `pgman.yaml`

```yaml
host: db.example.com
port: 5432
username: alice
password: ${PGMAN_PASSWORD}
dbname: myapp
```

Config values support `${VAR_NAME}` environment variable interpolation. Use `PGMAN_*` variable
names for consistency with pgman's own environment variable conventions.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PGMAN_CONFIG` | — | Path to a config file; equivalent to `-c`/`--config` |
| `PGMAN_HOST` | `localhost` | PostgreSQL server hostname |
| `PGMAN_PORT` | `5432` | PostgreSQL server port |
| `PGMAN_USERNAME` | current OS user | PostgreSQL username |
| `PGMAN_PASSWORD` | — | PostgreSQL password |
| `PGMAN_DBNAME` | `postgres` | Default database name |

### Global CLI Flags

All connection parameters are exposed as global flags that appear before the subcommand
and apply to every command:

```sh
pgman [GLOBAL FLAGS] <command> [COMMAND FLAGS]
```

| Flag | Short | Env Variable | Default | Description |
|---|---|---|---|---|
| `--config` | `-c` | `PGMAN_CONFIG` | — | Path to a config file |
| `--host` | `-h` | `PGMAN_HOST` | `localhost` | PostgreSQL server hostname |
| `--port` | `-P` | `PGMAN_PORT` | `5432` | PostgreSQL server port |
| `--username` | `-u` | `PGMAN_USERNAME` | current OS user | PostgreSQL username |
| `--password` | `-p` | `PGMAN_PASSWORD` | — | PostgreSQL password |
| `--dbname` | `-d` | `PGMAN_DBNAME` | `postgres` | Database name |

> **Note:** `-P` (uppercase) is used for `--port` to avoid collision with `-p`/`--password`.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
