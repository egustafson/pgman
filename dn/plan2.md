# pgman — Implementation Plan (Iteration 2): Database Lifecycle Management

## Overview

Extend `pgman` with database lifecycle management commands: `newdb`, `dropdb`, and
`listdbs`. These commands let an operator provision a database intended for a single
application, together with a dedicated non-superuser owner role, and later inspect or
tear down that database.

These commands are expected to be run with a superuser account (e.g. `postgres`) or a
role holding the `CREATEDB` (and, for creating roles, `CREATEROLE`) attributes. The
resolved connection configuration from iteration 1 (defaults → file → env → CLI flags,
stored in `ctx.obj`) supplies the administrative connection.

---

## Phase 1: Design Principles & Security Model

### 1.1 One database, one application, one owner

- Each database created by `newdb` is intended to be used by a single application.
- The database is owned by a dedicated role (the "owner-user"), which the application
  uses to connect and perform normal operations (create tables, insert data, etc.).
- The owner-user is **not** a superuser. It receives only `LOGIN` and `CREATEDB`
  attributes by default. This limits blast radius if the application's credentials leak.

### 1.2 Administrative connection

- Admin commands connect using the resolved config credentials, which are expected to be
  a superuser or `CREATEDB`/`CREATEROLE`-capable role.
- The connection database is the configured maintenance database (`dbname`, default
  `postgres`). The positional `<dbname>` argument is the **target** database to
  create/drop/inspect, and is never used as the connection database.
- `CREATE DATABASE` and `DROP DATABASE` cannot run inside a transaction block, so admin
  operations use an **autocommit** connection.

### 1.3 SQL safety

- All identifiers (database names, role names) are quoted using
  `psycopg2.sql.Identifier` to prevent SQL injection and correctly handle special
  characters.
- String literals that cannot be identifiers (e.g. the owner password in
  `CREATE ROLE ... PASSWORD`, encoding/collation names) are rendered with
  `psycopg2.sql.Literal`.
- Never build admin SQL via f-strings/`%` string formatting of user input.

---

## Phase 2: Shared Infrastructure

### 2.1 Admin connection helper (`src/pgman/db.py`)

Extend the existing `db.py` with an admin-oriented connection helper:

- `get_admin_connection(config: dict)` — same connection parameters as
  `get_connection`, but sets `conn.autocommit = True` so `CREATE DATABASE` /
  `DROP DATABASE` can execute.
- Keep the existing `get_connection` for non-admin use.

### 2.2 Password generation (`src/pgman/passwords.py`, new module)

- `generate_password() -> str`:
  - Uses the `secrets` module (cryptographically secure) — **not** `random`.
  - Length: random integer in the inclusive range **13–17** characters.
  - Alphabet: uppercase letters + lowercase letters + digits
    (`string.ascii_letters + string.digits`). No symbols, per spec.
  - Returns the generated password (caller is responsible for display).
- Rationale for a dedicated module: keeps the security-sensitive logic isolated and
  independently unit-testable (length bounds, character set).

### 2.3 Admin operation helpers

Provide small, testable helper functions in a new `src/pgman/dbadmin.py`
(Decision 1). Each takes a cursor/connection and uses `psycopg2.sql` composition:

- `role_exists(cur, role_name) -> bool` — query `pg_roles` for the role.
- `create_role(cur, role_name, password)` — `CREATE ROLE <role> WITH LOGIN CREATEDB
  PASSWORD <literal>` (explicitly no `SUPERUSER`).
- `create_database(cur, dbname, owner, encoding, collation)` —
  `CREATE DATABASE <db> OWNER <owner> ENCODING <lit> LC_COLLATE <lit> LC_CTYPE <lit>
  TEMPLATE template0`.
  - `TEMPLATE template0` is required when specifying an encoding/collation that may
    differ from `template1`'s.
- `drop_database(cur, dbname)` — `DROP DATABASE <db>`.
- `drop_role(cur, role_name)` — `DROP ROLE <role>` (used by `dropdb` owner cleanup).
- `list_databases(cur, with_owners: bool) -> list[dict]` — see Phase 5.

---

## Phase 3: `pgman newdb` Command

### 3.1 Synopsis

```
pgman newdb [OPTIONS] <dbname>
```

### 3.2 Options

| Option | Default | Description |
|---|---|---|
| `--dbowner NAME` | `<dbname>_owner` | Owner role for the new database |
| `--dbpassword PASSWORD` | *(generated)* | Password for the owner role |

### 3.3 Defaults

- **Owner name:** `<dbname>` + `_owner` (e.g. `mydb` → `mydb_owner`).
- **Password:** auto-generated per §2.2 (13–17 chars, alnum) when `--dbpassword` is not
  supplied. The effective password is **always displayed** in the command output so the
  operator can hand it to the application — this is the only opportunity to capture a
  generated password.
- **Encoding:** `UTF8`.
- **Collation (`LC_COLLATE`/`LC_CTYPE`):** `en_US.UTF-8`.
- **Owner role attributes:** `LOGIN`, `CREATEDB`. Explicitly **not** `SUPERUSER`.

### 3.4 Flow

1. Resolve `owner` (default `<dbname>_owner`) and `password` (from `--dbpassword` or
   generate).
2. Open an autocommit admin connection (§2.1).
3. If the owner role does not already exist, `create_role(...)`.
   - If it already exists: do **not** silently clobber its password. Report that the
     existing role will be used as owner and skip role creation (see Decision 2).
4. `create_database(...)` with owner, `UTF8`, `en_US.UTF-8`, `TEMPLATE template0`.
5. Print a summary:

```
Created database "mydb".
  owner:    mydb_owner
  encoding: UTF8
  collation: en_US.UTF-8
  password: <generated-or-provided-password>
```

### 3.5 Error handling

- Database already exists → report clearly, exit non-zero.
- Insufficient privileges (`CREATEDB`/`CREATEROLE`) → surface the PostgreSQL error, exit
  non-zero.
- Connection failure → same style as `ping`, exit non-zero.

---

## Phase 4: `pgman dropdb` Command

### 4.1 Synopsis

```
pgman dropdb [OPTIONS] <dbname>
```

### 4.2 Options

| Option | Description |
|---|---|
| `--i-really-really-mean-it` | Skip the confirmation prompt and drop immediately |
| `--keep-owner` | Retain the database's owner role instead of dropping it |

### 4.3 Confirmation

- Unless `--i-really-really-mean-it` is given, prompt the operator to re-type the
  database name:
  ```
  This will permanently drop database "mydb".
  Type the database name to confirm: 
  ```
- If the typed value does not exactly match `<dbname>`, print a message and exit
  **without** dropping (Decision 6: exit non-zero with a clear message).

### 4.4 Owner cleanup

- By default, `dropdb` also drops the database's owner role after dropping the database.
  The owner is determined **before** the drop by resolving `pg_database.datdba` →
  `pg_roles` for the target database (the same lookup used by `listdbs --with-owners`).
- `--keep-owner` retains the owner role (drops only the database).
- Safeguards on owner removal:
  - Determine the owner OID/name before dropping the database (afterward the
    `pg_database` row is gone).
  - Drop the role only after the database is successfully dropped.
  - If the owner still owns objects in, or holds privileges on, **other** databases, the
    `DROP ROLE` will fail; surface the PostgreSQL error and report that the database was
    dropped but the owner role was retained (non-zero exit). Do not attempt
    `DROP OWNED` / `REASSIGN OWNED` automatically.
  - Skip owner removal (with a note) if the owner could not be resolved (`unknown`) or if
    the owner is a well-known/shared role such as `postgres` — never drop the connecting
    superuser or a role not clearly dedicated to this database.

### 4.5 Flow

1. If not skipping confirmation, prompt and compare (exact match required).
2. Open an autocommit admin connection.
3. Resolve the target database's owner (for cleanup, unless `--keep-owner`).
4. `drop_database(...)`.
5. Unless `--keep-owner`, `drop_role(owner)` subject to the §4.4 safeguards.
6. Print confirmation, e.g.:
   ```
   Dropped database "mydb".
   Dropped owner role "mydb_owner".
   ```
   or, with `--keep-owner`:
   ```
   Dropped database "mydb".
   Retained owner role "mydb_owner".
   ```

### 4.6 Notes & error handling

- Database does not exist → report clearly, exit non-zero (Decision 3: plain
  `DROP DATABASE`, no `IF EXISTS`).
- Active connections to the target DB will cause the drop to fail; `dropdb` does **not**
  force disconnects (Decision 5). Surface the error and exit non-zero.
- `drop_role(cur, role_name)` is added to the admin helpers (§2.3) as
  `DROP ROLE <role>`.

---

## Phase 5: `pgman listdbs` Command

### 5.1 Synopsis

```
pgman listdbs [OPTIONS]
```

### 5.2 Options

| Option | Description |
|---|---|
| `--json` | Emit machine-readable JSON instead of human-readable text |
| `--with-owners` | Include the owner of each database |

### 5.3 Query

- Base list: query `pg_database` for database names. Exclude template databases
  (`datistemplate = false`) so the output reflects real, usable databases.
- Owner resolution (`--with-owners`): per the spec, look up `pg_database.datdba` (owner
  OID) and resolve it against `pg_roles` (OID → role name). Implemented as a
  `LEFT JOIN pg_roles r ON r.oid = d.datdba`; when no role matches, report the owner as
  `unknown`.
  - (Simpler equivalent `pg_catalog.pg_get_userbyid(datdba)` is noted as an alternative,
    but the join is used to match the spec's explicit description and to allow the
    `unknown` fallback.)

### 5.4 Output

**Human-readable, without owners:**
```
postgres
mydb
otherdb
```

**Human-readable, with owners** (aligned columns):
```
NAME      OWNER
postgres  postgres
mydb      mydb_owner
orphan    unknown
```

**JSON, without owners:**
```json
["postgres", "mydb", "otherdb"]
```

**JSON, with owners:**
```json
[
  {"name": "postgres", "owner": "postgres"},
  {"name": "mydb", "owner": "mydb_owner"},
  {"name": "orphan", "owner": "unknown"}
]
```

- JSON is emitted via `json.dumps`. `--json` and `--with-owners` compose independently.

### 5.5 Error handling

- Connection failure → same style as `ping`, exit non-zero.

---

## Phase 6: CLI Registration (`src/pgman/cli.py`)

- Import and register the three new commands on the root group:
  ```python
  cli.add_command(newdb)
  cli.add_command(dropdb)
  cli.add_command(listdbs)
  ```
- No changes to the global option set are required; all three reuse the resolved config
  in `ctx.obj`. The connection database remains the configured maintenance DB; the
  positional `<dbname>` is the operable target.

---

## Phase 7: Documentation

### 7.1 `README.md`

- Add a "Database lifecycle" usage section with examples for `newdb`, `dropdb`, and
  `listdbs`, including the security note that the owner role is a non-superuser.
- Document that `newdb` prints the generated password and that it is shown only once.
- Document that `dropdb` removes the database's owner role by default and that
  `--keep-owner` retains it.

### 7.2 `CHANGELOG.md`

- Under `[Unreleased] → Added`:
  - `pgman newdb` — create a database with a dedicated non-superuser owner role;
    `--dbowner`, `--dbpassword`; UTF8 / en_US.UTF-8 defaults; auto-generated password.
  - `pgman dropdb` — drop a database with type-the-name confirmation and
    `--i-really-really-mean-it` override; drops the owner role by default, with
    `--keep-owner` to retain it.
  - `pgman listdbs` — list databases with `--json` and `--with-owners`
    (owner resolved via `pg_database.datdba` → `pg_roles`, `unknown` fallback).

### 7.3 `CONTRIBUTING.md`

- No structural change required; ensure new commands follow existing conventions.

---

## Phase 8: Testing

All tests mock `psycopg2.connect` (and its cursor) so no live database is needed. Use
`click.testing.CliRunner` and the existing `runner` / `clean_env` fixtures. For
autocommit admin connections, assert `autocommit` is set on the mocked connection.

### 8.1 New test files

| File | Coverage |
|---|---|
| `tests/test_passwords.py` | Length within 13–17 inclusive; only `[A-Za-z0-9]`; uses `secrets`; reasonable uniqueness across calls |
| `tests/test_newdb.py` | Default owner `<dbname>_owner`; `--dbowner` override; `--dbpassword` override vs generated; generated password is displayed; role skipped when it already exists; `CREATE DATABASE` issued with UTF8 / en_US.UTF-8 / `template0`; owner created without `SUPERUSER`; autocommit set; error + non-zero exit on failure |
| `tests/test_dropdb.py` | Confirmation match → drops; mismatch → aborts without drop (non-zero); `--i-really-really-mean-it` skips prompt; `DROP DATABASE` issued for correct name; owner resolved and `DROP ROLE` issued by default; `--keep-owner` retains the owner role (no `DROP ROLE`); owner not dropped when unresolved/shared; database-dropped-but-owner-retained path on `DROP ROLE` failure; error + non-zero exit on failure |
| `tests/test_listdbs.py` | Text output; `--json` output parses and matches; `--with-owners` includes owners; `unknown` when owner unresolved; template DBs excluded; `--json` + `--with-owners` compose |

### 8.2 Assertions on generated SQL

- Where practical, capture the composed SQL passed to `cursor.execute` and assert it
  contains the expected quoted identifiers and clauses (`OWNER`, `ENCODING 'UTF8'`,
  `LC_COLLATE 'en_US.UTF-8'`, `TEMPLATE template0`, `LOGIN`, `CREATEDB`, absence of
  `SUPERUSER`).

### 8.3 Lint/format

- `ruff check .` and `ruff format --check .` must pass; new modules follow the existing
  import-sorting and line-length (100) config.

---

## Decisions (resolved)

1. **Helper location:** admin helpers live in a new `src/pgman/dbadmin.py`, keeping
   `db.py` a thin connection module and isolating the more complex, injection-sensitive
   SQL composition.
2. **Owner role already exists (newdb):** reuse the existing role and clearly report it;
   do **not** alter its password.
3. **`dropdb` on a missing database:** use plain `DROP DATABASE` (not
   `IF EXISTS`), so a missing DB is a visible error.
4. **Owner cleanup on `dropdb`:** `dropdb` **drops the database's owner role by
   default**, unless `--keep-owner` is passed. See Phase 4 for details and safeguards.
5. **Forcing disconnects on drop:** not supported. `dropdb` does **not** force
   disconnects (no `WITH (FORCE)`); active connections cause the drop to fail with a
   clear error.
6. **Exit code on `dropdb` confirmation mismatch:** non-zero, to signal the drop did not
   occur.

---

## Implementation Order

1. `src/pgman/passwords.py` + `tests/test_passwords.py`.
2. Admin helpers (`dbadmin.py` or `db.py`): connection + role/db/list functions.
3. `newdb` command + `tests/test_newdb.py`.
4. `dropdb` command + `tests/test_dropdb.py`.
5. `listdbs` command + `tests/test_listdbs.py`.
6. Register commands in `cli.py`.
7. Update `README.md` and `CHANGELOG.md`.
8. Run `ruff` + `pytest`; final review and polish.
