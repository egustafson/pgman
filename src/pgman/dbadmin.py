"""Administrative PostgreSQL operations (role and database lifecycle).

All identifiers are quoted with :class:`psycopg2.sql.Identifier` and all
literals with :class:`psycopg2.sql.Literal`, so no user input is ever
interpolated into SQL via string formatting.
"""

from psycopg2 import sql

DEFAULT_ENCODING = "UTF8"
DEFAULT_COLLATION = "en_US.UTF-8"

# Roles that must never be dropped as part of owner cleanup.
SHARED_ROLES = frozenset({"postgres"})


def role_exists(cur, role_name: str) -> bool:
    """Return True if a role named *role_name* exists."""
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role_name,))
    return cur.fetchone() is not None


def create_role(cur, role_name: str, password: str) -> None:
    """Create a login role with CREATEDB (and explicitly no SUPERUSER)."""
    cur.execute(
        sql.SQL("CREATE ROLE {role} WITH LOGIN CREATEDB PASSWORD {password}").format(
            role=sql.Identifier(role_name),
            password=sql.Literal(password),
        )
    )


def drop_role(cur, role_name: str) -> None:
    """Drop the role named *role_name*."""
    cur.execute(sql.SQL("DROP ROLE {role}").format(role=sql.Identifier(role_name)))


def create_database(
    cur,
    dbname: str,
    owner: str,
    encoding: str = DEFAULT_ENCODING,
    collation: str = DEFAULT_COLLATION,
) -> None:
    """Create a database owned by *owner* with the given encoding/collation.

    ``TEMPLATE template0`` is required to specify an encoding/collation that
    may differ from ``template1``'s.
    """
    cur.execute(
        sql.SQL(
            "CREATE DATABASE {db} OWNER {owner} ENCODING {encoding} "
            "LC_COLLATE {collation} LC_CTYPE {collation} TEMPLATE template0"
        ).format(
            db=sql.Identifier(dbname),
            owner=sql.Identifier(owner),
            encoding=sql.Literal(encoding),
            collation=sql.Literal(collation),
        )
    )


def drop_database(cur, dbname: str) -> None:
    """Drop the database named *dbname*."""
    cur.execute(sql.SQL("DROP DATABASE {db}").format(db=sql.Identifier(dbname)))


def get_database_owner(cur, dbname: str) -> str | None:
    """Return the owner role name for *dbname*, or None if it cannot be resolved."""
    cur.execute(
        """
        SELECT r.rolname
        FROM pg_database d
        LEFT JOIN pg_roles r ON r.oid = d.datdba
        WHERE d.datname = %s
        """,
        (dbname,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return row[0]


def list_databases(cur, with_owners: bool = False) -> list[dict]:
    """Return non-template databases as a list of dicts.

    Each dict has a ``name`` key and, when *with_owners* is True, an ``owner``
    key (``"unknown"`` when the owner OID cannot be resolved to a role name).
    """
    if with_owners:
        cur.execute(
            """
            SELECT d.datname, r.rolname
            FROM pg_database d
            LEFT JOIN pg_roles r ON r.oid = d.datdba
            WHERE d.datistemplate = false
            ORDER BY d.datname
            """
        )
        return [
            {"name": name, "owner": owner if owner is not None else "unknown"}
            for name, owner in cur.fetchall()
        ]

    cur.execute(
        """
        SELECT datname
        FROM pg_database
        WHERE datistemplate = false
        ORDER BY datname
        """
    )
    return [{"name": name} for (name,) in cur.fetchall()]
