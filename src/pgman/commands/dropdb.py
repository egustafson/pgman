"""`pgman dropdb` — drop a database (and, by default, its owner role)."""

import click
import psycopg2

from pgman import dbadmin
from pgman.db import get_admin_connection


@click.command()
@click.argument("dbname")
@click.option(
    "--i-really-really-mean-it",
    "skip_confirm",
    is_flag=True,
    default=False,
    help="Skip the confirmation prompt and drop the database immediately.",
)
@click.option(
    "--keep-owner",
    is_flag=True,
    default=False,
    help="Retain the database's owner role instead of dropping it.",
)
@click.pass_context
def dropdb(ctx, dbname, skip_confirm, keep_owner):
    """Drop an existing PostgreSQL database."""
    config = ctx.obj["config"]

    if not skip_confirm:
        click.echo(f'This will permanently drop database "{dbname}".')
        typed = click.prompt("Type the database name to confirm", default="", show_default=False)
        if typed != dbname:
            click.echo("Name did not match; aborting. No database was dropped.")
            ctx.exit(1)

    try:
        conn = get_admin_connection(config)
    except psycopg2.Error as exc:
        click.echo("Failed to connect to PostgreSQL.")
        click.echo(f"  error: {exc}")
        ctx.exit(1)

    owner = None
    try:
        with conn.cursor() as cur:
            if not keep_owner:
                owner = dbadmin.get_database_owner(cur, dbname)
            dbadmin.drop_database(cur, dbname)
    except psycopg2.Error as exc:
        conn.close()
        click.echo(f'Failed to drop database "{dbname}".')
        click.echo(f"  error: {exc}")
        ctx.exit(1)

    click.echo(f'Dropped database "{dbname}".')

    if keep_owner:
        conn.close()
        return

    # Owner cleanup (best-effort, with safeguards).
    if owner is None:
        click.echo("  owner role could not be determined; no role was dropped.")
        conn.close()
        return

    if owner in dbadmin.SHARED_ROLES:
        click.echo(f'  retained shared role "{owner}".')
        conn.close()
        return

    try:
        with conn.cursor() as cur:
            dbadmin.drop_role(cur, owner)
        click.echo(f'Dropped owner role "{owner}".')
    except psycopg2.Error as exc:
        click.echo(f'Retained owner role "{owner}" (could not be dropped).')
        click.echo(f"  error: {exc}")
        ctx.exit(1)
    finally:
        conn.close()
