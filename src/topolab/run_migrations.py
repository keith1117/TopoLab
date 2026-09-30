"""Ordered, transactional SQLite schema migrations for run records."""

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.engine import Connection, Engine

SCHEMA_VERSION = 2


def migrate_run_database(engine: Engine) -> None:
    """Upgrade a new or existing run database through every known version."""

    with engine.connect() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            version = int(connection.exec_driver_sql("PRAGMA user_version").scalar_one())
            if version > SCHEMA_VERSION:
                raise ValueError(f"run database schema version {version} is newer than supported")
            for target, migration in enumerate(_MIGRATIONS, start=1):
                if version >= target:
                    continue
                migration(connection)
                connection.exec_driver_sql(f"PRAGMA user_version = {target}")
            required = {
                "run_id", "problem_json", "status", "iteration", "cancel_requested",
                "result_json", "error", "created_at", "updated_at", "owner_id",
                "lease_expires_at",
            }
            if not required.issubset(_columns(connection)):
                raise ValueError("run database schema does not match its version")
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def _columns(connection: Connection) -> set[str]:
    return {str(row[1]) for row in connection.exec_driver_sql("PRAGMA table_info(runs)")}


def _timestamps(connection: Connection) -> None:
    connection.exec_driver_sql(
        "CREATE TABLE IF NOT EXISTS runs ("
        "run_id VARCHAR(32) PRIMARY KEY, problem_json TEXT NOT NULL, "
        "status VARCHAR(16) NOT NULL, iteration INTEGER NOT NULL, "
        "cancel_requested BOOLEAN NOT NULL, result_json TEXT, error TEXT)"
    )
    columns = _columns(connection)
    if "created_at" not in columns:
        connection.exec_driver_sql("ALTER TABLE runs ADD COLUMN created_at TEXT")
    if "updated_at" not in columns:
        connection.exec_driver_sql("ALTER TABLE runs ADD COLUMN updated_at TEXT")
    timestamp = datetime.now(UTC).isoformat()
    connection.exec_driver_sql(
        "UPDATE runs SET created_at = COALESCE(created_at, ?), "
        "updated_at = COALESCE(updated_at, ?)",
        (timestamp, timestamp),
    )


def _ownership(connection: Connection) -> None:
    columns = _columns(connection)
    if "owner_id" not in columns:
        connection.exec_driver_sql("ALTER TABLE runs ADD COLUMN owner_id VARCHAR(32)")
    if "lease_expires_at" not in columns:
        connection.exec_driver_sql("ALTER TABLE runs ADD COLUMN lease_expires_at TEXT")


_MIGRATIONS: tuple[Callable[[Connection], None], ...] = (_timestamps, _ownership)
