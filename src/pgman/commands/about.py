"""`pgman about` — display version and configuration details."""

from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, distribution, version

import click
import yaml

from pgman.config import KEY_TO_ENV, REDACTED, SENSITIVE_FIELDS


@click.command()
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    default=False,
    help="Output only name, version, and build_date as a single YAML document.",
)
@click.pass_context
def about(ctx, quiet):
    """Display pgman version, configuration sources, and effective configuration."""
    try:
        pkg_version = version("pgman")
    except PackageNotFoundError:
        pkg_version = "unknown"

    build_date = _get_build_date()

    if quiet:
        doc = {"name": "pgman", "version": pkg_version, "build_date": build_date}
        click.echo(yaml.dump(doc, default_flow_style=False, sort_keys=False), nl=False)
        return

    config = ctx.obj["config"]
    meta = ctx.obj["metadata"]

    # Document 1 — About
    # Show effective values for all connection env vars in canonical order.
    env_vars: dict[str, object] = {}
    for key, value in config.items():
        env_var = KEY_TO_ENV.get(key)
        if env_var is None:
            continue
        if key in SENSITIVE_FIELDS:
            env_vars[env_var] = REDACTED
        else:
            # Env vars are inherently strings; render port as string for accuracy.
            env_vars[env_var] = str(value) if isinstance(value, int) else value

    about_doc = {
        "name": "pgman",
        "version": pkg_version,
        "build_date": build_date,
        "config_files_loaded": meta["config_files_loaded"],
        "config_files_failed": meta["config_files_failed"],
        "environment_variables": env_vars,
    }

    # Document 2 — Effective configuration (matches config file schema)
    config_doc = {
        "host": config["host"],
        "port": config["port"],
        "username": config["username"],
        "password": REDACTED,
        "dbname": config["dbname"],
    }

    output = yaml.dump_all(
        [about_doc, config_doc],
        explicit_start=True,
        default_flow_style=False,
        sort_keys=False,
    )
    click.echo(output, nl=False)


def _get_build_date() -> str | None:
    """Return an ISO 8601 timestamp approximating the package install date, or None."""
    try:
        dist = distribution("pgman")
        metadata_file = dist.locate_file("METADATA")
        mtime = metadata_file.stat().st_mtime  # type: ignore[union-attr]
        return datetime.fromtimestamp(mtime, tz=UTC).isoformat()
    except Exception:
        return None
