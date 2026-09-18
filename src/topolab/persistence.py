"""SQLite persistence for optimization run state."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from sqlalchemy import Boolean, Integer, String, Text, create_engine, inspect, select
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from topolab.problem import TopologyProblem, TopologyResult


@dataclass(frozen=True, slots=True)
class StoredRun:
    """Serializable state stored for one optimization run."""

    run_id: str
    problem: TopologyProblem
    status: str
    iteration: int
    cancel_requested: bool
    result: TopologyResult | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class RunStore(Protocol):
    """Storage operations required by the run manager."""

    def load_all(self) -> tuple[StoredRun, ...]:
        """Load every stored run."""

        ...

    def save(self, run: StoredRun) -> None:
        """Insert or replace one stored run."""

        ...


class _Base(DeclarativeBase):
    pass


class _RunRow(_Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    problem_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16))
    iteration: Mapped[int] = mapped_column(Integer)
    cancel_requested: Mapped[bool] = mapped_column(Boolean)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(40))
    updated_at: Mapped[str] = mapped_column(String(40))


class SqliteRunStore:
    """Persist run snapshots and immutable contracts in one SQLite database."""

    def __init__(self, database_path: str | Path) -> None:
        path = Path(database_path).expanduser().resolve()
        url = URL.create("sqlite+pysqlite", database=str(path))
        self._engine = create_engine(url)
        self._session_factory = sessionmaker(self._engine)
        _Base.metadata.create_all(self._engine)
        self._migrate_timestamp_columns()

    def load_all(self) -> tuple[StoredRun, ...]:
        """Load and validate all persisted contracts."""

        with self._session_factory() as session:
            rows = session.scalars(select(_RunRow).order_by(_RunRow.run_id)).all()
            return tuple(self._decode(row) for row in rows)

    def save(self, run: StoredRun) -> None:
        """Atomically insert or update a complete run record."""

        values = {
            "problem_json": run.problem.model_dump_json(),
            "status": run.status,
            "iteration": run.iteration,
            "cancel_requested": run.cancel_requested,
            "result_json": None if run.result is None else run.result.model_dump_json(),
            "error": run.error,
            "created_at": _serialize_timestamp(run.created_at),
            "updated_at": _serialize_timestamp(run.updated_at),
        }
        with self._session_factory.begin() as session:
            row = session.get(_RunRow, run.run_id)
            if row is None:
                session.add(_RunRow(run_id=run.run_id, **values))
                return
            for name, value in values.items():
                setattr(row, name, value)

    def close(self) -> None:
        """Release pooled SQLite connections."""

        self._engine.dispose()

    @staticmethod
    def _decode(row: _RunRow) -> StoredRun:
        result = (
            None
            if row.result_json is None
            else TopologyResult.model_validate_json(row.result_json)
        )
        return StoredRun(
            run_id=row.run_id,
            problem=TopologyProblem.model_validate_json(row.problem_json),
            status=row.status,
            iteration=row.iteration,
            cancel_requested=row.cancel_requested,
            result=result,
            error=row.error,
            created_at=_deserialize_timestamp(row.created_at),
            updated_at=_deserialize_timestamp(row.updated_at),
        )

    def _migrate_timestamp_columns(self) -> None:
        columns = {
            column["name"] for column in inspect(self._engine).get_columns("runs")
        }
        missing = {"created_at", "updated_at"} - columns
        if not missing:
            return
        timestamp = datetime.now(UTC).isoformat()
        with self._engine.begin() as connection:
            if "created_at" in missing:
                connection.exec_driver_sql(
                    "ALTER TABLE runs ADD COLUMN created_at TEXT"
                )
            if "updated_at" in missing:
                connection.exec_driver_sql(
                    "ALTER TABLE runs ADD COLUMN updated_at TEXT"
                )
            connection.exec_driver_sql(
                "UPDATE runs SET created_at = COALESCE(created_at, ?), "
                "updated_at = COALESCE(updated_at, ?)",
                (timestamp, timestamp),
            )


def _serialize_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("run timestamps must include a timezone")
    return value.astimezone(UTC).isoformat()


def _deserialize_timestamp(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("stored run timestamps must include a timezone")
    return timestamp.astimezone(UTC)
