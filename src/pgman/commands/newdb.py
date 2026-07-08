"""`pgman newdb` — create a database with a dedicated non-superuser owner."""

import click
import psycopg2

from pgman import dbadmin
from pgman.db import get_admin_connection
from pgman.passwords import generate_password


@click.command()
@click.argument("dbname")
@click.option("--dbowner", default=None, metavar="NAME", help="Owner role for the new database.")
@click.option("--dbpassword", default=None, metavar="PASSWORD", help="Password for the owner role.")
@click.pass_context
def newdb(ctx, dbname, dbowner, dbpassword):
    """Create a new PostgreSQL database owned by a dedicated role."""
    config = ctx.obj["config"]

    owner = dbowner or f"{dbname}_owner"
    password = dbpassword if dbpassword is not None else generate_password()

    try:
        conn = get_admin_connection(config)
    except psycopg2.Error as exc:
        click.echo("Failed to connect to PostgreSQL.")
        click.echo(f"  error: {exc}")
        ctx.exit(1)

    try:
        with conn.cursor() as cur:
            if dbadmin.role_exists(cur, owner):
                role_created = False
            else:
                dbadmin.create_role(cur, owner, password)
                role_created = True

            dbadmin.create_database(cur, dbname, owner)
    except psycopg2.Error as exc:
        click.echo(f'Failed to create database "{dbname}".')
        click.echo(f"  error: {exc}")
        ctx.exit(1)
    finally:
        conn.close()

    click.echo(f'Created database "{dbname}".')
    click.echo(f"  owner:     {owner}")
    if not role_created:
        click.echo("  (owner role already existed; its password was left unchanged)")
    click.echo("  encoding:  UTF8")
    click.echo("  collation: en_US.UTF-8")
    if role_created:
        click.echo(f"  password:  {password}")
