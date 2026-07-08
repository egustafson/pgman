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


def get_admin_connection(config: dict):
    """Create and return an autocommit psycopg2 connection using *config*.

    ``CREATE DATABASE`` and ``DROP DATABASE`` cannot run inside a transaction
    block, so administrative commands require autocommit.
    """
    conn = get_connection(config)
    conn.autocommit = True
    return conn
