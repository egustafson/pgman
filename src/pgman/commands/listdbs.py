"""`pgman listdbs` — list databases accessible by the configuration."""

import json

import click
import psycopg2

from pgman import dbadmin
from pgman.db import get_admin_connection


@click.command()
@click.option("--json", "as_json", is_flag=True, default=False, help="Output in JSON format.")
@click.option(
    "--with-owners", is_flag=True, default=False, help="Include the owner of each database."
)
@click.pass_context
def listdbs(ctx, as_json, with_owners):
    """List all PostgreSQL databases."""
    config = ctx.obj["config"]

    try:
        conn = get_admin_connection(config)
    except psycopg2.Error as exc:
        click.echo("Failed to connect to PostgreSQL.")
        click.echo(f"  error: {exc}")
        ctx.exit(1)

    try:
        with conn.cursor() as cur:
            databases = dbadmin.list_databases(cur, with_owners=with_owners)
    except psycopg2.Error as exc:
        click.echo("Failed to list databases.")
        click.echo(f"  error: {exc}")
        ctx.exit(1)
    finally:
        conn.close()

    if as_json:
        if with_owners:
            payload = databases
        else:
            payload = [db["name"] for db in databases]
        click.echo(json.dumps(payload, indent=2))
        return

    if with_owners:
        _echo_table(databases)
    else:
        for db in databases:
            click.echo(db["name"])


def _echo_table(databases: list[dict]) -> None:
    """Print name/owner rows in aligned columns."""
    name_width = max((len(db["name"]) for db in databases), default=0)
    name_width = max(name_width, len("NAME"))
    click.echo(f"{'NAME'.ljust(name_width)}  OWNER")
    for db in databases:
        click.echo(f"{db['name'].ljust(name_width)}  {db['owner']}")
