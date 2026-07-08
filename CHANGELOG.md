# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `pgman newdb <dbname>` command: creates a database owned by a dedicated, non-superuser
  role (`LOGIN`, `CREATEDB`). Defaults the owner to `<dbname>_owner` and generates a
  random 13–17 character password (displayed once in the output). Databases are created
  with `UTF8` encoding and `en_US.UTF-8` collation. Supports `--dbowner` and
  `--dbpassword` overrides. An existing owner role is reused without altering its
  password.
- `pgman dropdb <dbname>` command: drops a database after a type-the-name confirmation.
  Supports `--i-really-really-mean-it` to skip the prompt. By default also drops the
  database's owner role; `--keep-owner` retains it. Shared/unresolvable roles (e.g.
  `postgres`) are never dropped.
- `pgman listdbs` command: lists non-template databases. Supports `--json` for
  machine-readable output and `--with-owners` to resolve each database's owner via
  `pg_database.datdba` → `pg_roles` (reported as `unknown` when unresolvable).


## [0.1.0] - 2026-07-06

### Added

- `pgman about` command: displays version, build date, loaded config files, active environment
  variables, and effective merged configuration as multi-document parsable YAML. Supports
  `-q`/`--quiet` for minimal single-document output.
- `pgman ping` command: tests PostgreSQL connectivity using the resolved configuration and
  reports success or failure with connection details.
- Multi-source configuration system with precedence order:
  built-in defaults → config file → environment variables → CLI flags.
- Config file search: `./pgman.yaml` then `$XDG_CONFIG_HOME/pgman/config.yaml`
  (XDG Base Directory Specification).
- `${VAR_NAME}` environment variable interpolation in config files.
- Global CLI flags (`-h`/`--host`, `-P`/`--port`, `-u`/`--username`, `-p`/`--password`,
  `-d`/`--dbname`, `-c`/`--config`) applied to all commands.
- `PGMAN_CONFIG` environment variable as an alternative to `-c`/`--config`.

[0.1.0]: https://github.com/egustafson/pgman/releases/tag/v0.1.0
