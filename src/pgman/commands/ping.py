"""`pgman ping` — test PostgreSQL connectivity."""

import click
import psycopg2


@click.command()
@click.pass_context
def ping(ctx):
    """Test connectivity to the PostgreSQL server."""
    config = ctx.obj["config"]

    host = config["host"]
    port = config["port"]
    dbname = config["dbname"]
    username = config["username"]
    password = config["password"]

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=username,
            password=password,
        )
        conn.close()
        click.echo("Connected to PostgreSQL successfully.")
        click.echo(f"  host:     {host}")
        click.echo(f"  port:     {port}")
        click.echo(f"  dbname:   {dbname}")
        click.echo(f"  username: {username}")
    except psycopg2.Error as exc:
        click.echo("Failed to connect to PostgreSQL.")
        click.echo(f"  host:     {host}")
        click.echo(f"  port:     {port}")
        click.echo(f"  dbname:   {dbname}")
        click.echo(f"  username: {username}")
        click.echo(f"  error:    {exc}")
        ctx.exit(1)
