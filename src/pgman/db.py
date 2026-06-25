"""PostgreSQL connection helpers."""

import psycopg2


def get_connection(config: dict):
    """Create and return a psycopg2 connection using *config*."""
    return psycopg2.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["dbname"],
        user=config["username"],
        password=config["password"],
    )
