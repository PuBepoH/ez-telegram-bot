from urllib.parse import ParseResult, urlparse, urlunparse

import psycopg
from psycopg import errors

from app.config import logger, settings

DB_EXISTS_CHECK_SQL = """
SELECT 1 FROM pg_database WHERE datname = %s;
"""

CREATE_DB_SQL = """
CREATE DATABASE {}
"""

SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS bot;
"""

CREATE_USERS_SQL = """
CREATE TABLE IF NOT EXISTS bot.users (
    tg_id        BIGINT PRIMARY KEY,
    role         TEXT NOT NULL,
    username     TEXT,
    first_name   TEXT,
    last_name    TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active    BOOLEAN NOT NULL DEFAULT TRUE
);
"""

UPSERT_ADMIN_SQL = """
INSERT INTO bot.users (tg_id, role, username, first_name, last_name)
VALUES (%s, 'admin', 'superadmin', 'Super', 'Admin')
ON CONFLICT (tg_id) DO UPDATE
SET role = EXCLUDED.role;
"""

HEALTHCHECK_SQL = "SELECT 1;"


def _replace_path_in_dsn(dsn: str, new_dbname: str) -> str:
    """
    Replace DB name in DSN for "new_dbname" and keep other options
    """
    parsed = urlparse(dsn)
    new_path = f"/{new_dbname}"
    new_parsed = ParseResult(
        scheme=parsed.scheme,
        netloc=parsed.netloc,
        path=new_path,
        params=parsed.params,
        query=parsed.query,
        fragment=parsed.fragment,
    )
    return urlunparse(new_parsed)


def ensure_database_exists(dsn: str, target_dbname: str | None = None) -> None:
    """
    Ensure that target_dbname DB actually exists
    If target_dbname is not specified - get it from dsn
    Connects to MAINTENANCE_DB_NAME and create target_dbname if it doesn't exists
    """
    parsed = urlparse(dsn)
    current_dbname = parsed.path[1:] if parsed.path and parsed.path != "/" else None

    if target_dbname is None:
        if not current_dbname:
            raise RuntimeError("Cant get DB name from POSTGRES_DSN, set target_dbname")
        target_dbname = current_dbname

    if target_dbname == settings.maintenance_db_name:
        logger.info(
            "Target DB equals maintenance DB (%s) - skipping DB creation step",
            settings.maintenance_db_name,
        )
        return

    maintenance_dsn = _replace_path_in_dsn(dsn, settings.maintenance_db_name)
    logger.info("Connecting to maintenance DB to ensure '%s' exists", target_dbname)

    try:
        with psycopg.connect(maintenance_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(DB_EXISTS_CHECK_SQL, (target_dbname,))
                if cur.fetchone():
                    logger.info("Database '%s' already exists.", target_dbname)
                    return

                create_sql = psycopg.sql.SQL(CREATE_DB_SQL).format(
                    psycopg.sql.Identifier(target_dbname)
                )
                try:
                    cur.execute(create_sql)
                    logger.info("Database '%s' created successfully", target_dbname)
                except errors.DuplicateDatabase:
                    logger.warning(
                        "Database '%s' already created by concurrent process.",
                        target_dbname,
                    )
                    return
    except Exception as exc:
        logger.exception("Failed to ensure database exists: %s", exc)
        raise


def init_db() -> None:
    """
    Check connection to Postgres
    Create schema/table, insert admin-user if does not exist
    """
    logger.info("Database init started")
    ensure_database_exists(settings.postgres_dsn)

    with psycopg.connect(settings.postgres_dsn, autocommit=True) as conn:
        with conn.cursor() as cur:

            # healthcheck
            cur.execute(HEALTHCHECK_SQL)
            row = cur.fetchone()
            if row != (1,):
                raise RuntimeError("Unexpected Postgres healthcheck result")
            logger.info("Postgres connection OK")

            logger.info("Ensuring schema 'bot' exists")
            cur.execute(SCHEMA_SQL)

            logger.info("Ensuring table bot.users exists")
            cur.execute(CREATE_USERS_SQL)

            logger.info("Ensuring admin user %s exists", settings.admin_user_id)
            cur.execute(UPSERT_ADMIN_SQL, (settings.admin_user_id,))

    logger.info("DB init completed successfully")
