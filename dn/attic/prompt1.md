This project is a python based cli utility tool named 'pgman', that will automate management and maintence tasks against a PostgreSQL database. Over time additional commands will be added.

## Technologies Used
- Python 3
- Click (for CLI)
- Psycopg2 (for PostgreSQL interaction)
- uv (for packaging)
- pyproject.toml (for project configuration)
- ruff (for linting)
- pytest (for testing)
- hatchling (for building and distribution)
- hatch-vcs (for version control integration)
- github actions (for CI/CD)

## Project Structure

This project is intended to be an open source project and should follow best practices for open source projects, including the following files:
- README.md file with documentation
- LICENSE file
- CHANGELOG.md file for tracking changes
- CONTRIBUTING.md file with guidelines for contributing to the project.  This file should start out short with a minimal set of guidelines, but should be expanded over time as the project grows and more contributors get involved.

## Python Project Structure

This is a Python project and should follow best practices for Python projects as detailed by the python community.  This project should be "pythonic".

## Installation

pgman's recommended method of installation is to use `uv tool`.

## Initial commands

### `pgman about`

This command will display information about the pgman utility, including its version and build date, and details about the configuration, including:
* configuration files discovered and loaded
* optionally, configuration files that failed to load (e.g. due to syntax errors or missing files)
* environment variables that were loaded and their values (with sensitive information redacted)
* the final, merged configuration that will be used for the utility's operations (with sensitive information redacted).  Default values should be shown where applicable.
* the output of the about commmand should be parsable YAML.
* the output shoudld be two yaml documents, the first containing the about information and the second containing the configuration information.
* the configuration document should be the same structure as the configuration file and should be usable as a configuration file if saved to disk (with sensitive information redacted).

The `about` command should execute without error with no configuration files, environment variables, or cli flags.

### `pgman ping`

This command will attempt to connect to the PostgreSQL database using the provided configuration and will report whether the connection was successful or if there were any issues (e.g. authentication failure, network issues, etc.). It will also provide details about the connection attempt, such as the host, port, and database name used for the connection.

Optional flags should include:
- `-d`, `--dbname`: specify the database name to connect to (overrides configuration)

## General strategies used in pgman

* cli flags should try to be consistent with the `psql` command line tool where possible, to make it familiar to users who are used to working with PostgreSQL from the command line.
* configuration files should support environment variable interpolation.
* users should prefer `pgman`s environment variable names when using interpolation in the configuration file -- make sure this is expressed in documentation and follow this pattern when creating examples.
* configuration files should use the YAML format.

## Environment Variables

Environment variables used by pgman should be prefixed with `PGMAN_` to avoid conflicts with other environment variables. For example, `PGMAN_HOST`, `PGMAN_PORT`, `PGMAN_USER`, etc.

The following environment variables should be supported for database connection configuration:
- `PGMAN_HOST`: the hostname of the PostgreSQL server (default: `localhost`)
- `PGMAN_PORT`: the port number of the PostgreSQL server (default: `5432`)
- `PGMAN_USER`: the username to connect to the PostgreSQL server (default: the current system user)
- `PGMAN_PASSWORD`: the password to connect to the PostgreSQL server (default: empty)
- `PGMAN_DBNAME`: the database name to connect to (default: `postgres`)

## Configuration Files

pgman should support configuration files in YAML format. The configuration file should allow users to specify the same connection parameters as environment variables, as well as any additional configuration options that may be needed for future commands.

pgman prefers the XDG Base Directory Specification for configuration file locations. By default, pgman should look for configuration files in the following locations (in order of precedence):
1. `./pgman.yaml` (current working directory)
2. `~/.config/pgman/config.yaml` (user configuration directory)

pgman should also support specifying a custom configuration file location using the `-c` or `--config` flag. If this flag is used, pgman should only look for the configuration file at the specified location and should not look in the default locations.

pgman also allows variation from the XDG Base Directory Specification by supporting the specification's defined environment variables for overriding the default locations. For example, if `XDG_CONFIG_HOME` is set, pgman should look for the user configuration file in `$XDG_CONFIG_HOME/pgman/config.yaml` instead of `~/.config/pgman/config.yaml`.

