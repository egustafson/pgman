"""CLI entry point for pgman."""

import click

from pgman.commands.about import about
from pgman.commands.ping import ping
from pgman.config import load_config


@click.group(context_settings={"max_content_width": 100})
@click.option(
    "-c",
    "--config",
    "config_path",
    default=None,
    envvar="PGMAN_CONFIG",
    metavar="FILE",
    help="Path to a config file (skips default location search).",
)
@click.option("-h", "--host", default=None, metavar="HOST", help="PostgreSQL server hostname.")
@click.option(
    "-P", "--port", default=None, type=int, metavar="PORT", help="PostgreSQL server port."
)
@click.option("-u", "--username", default=None, metavar="USERNAME", help="PostgreSQL username.")
@click.option("-p", "--password", default=None, metavar="PASSWORD", help="PostgreSQL password.")
@click.option("-d", "--dbname", default=None, metavar="DBNAME", help="Database name.")
@click.pass_context
def cli(ctx, config_path, host, port, username, password, dbname):
    """pgman — PostgreSQL management and maintenance utility."""
    ctx.ensure_object(dict)

    cli_overrides = {
        k: v
        for k, v in {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "dbname": dbname,
        }.items()
        if v is not None
    }

    config, metadata = load_config(
        config_path=config_path,
        cli_overrides=cli_overrides,
    )

    ctx.obj["config"] = config
    ctx.obj["metadata"] = metadata


cli.add_command(about)
cli.add_command(ping)
