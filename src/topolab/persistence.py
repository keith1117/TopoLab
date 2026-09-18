"""SQLite persistence for optimization run state."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sqlalchemy import Boolean, Integer, String, Text, create_engine, select
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


class SqliteRunStore:
    """Persist run snapshots and immutable contracts in one SQLite database."""

    def __init__(self, database_path: str | Path) -> None:
        path = Path(database_path).expanduser().resolve()
        url = URL.create("sqlite+pysqlite", database=str(path))
        self._engine = create_engine(url)
        self._session_factory = sessionmaker(self._engine)
        _Base.metadata.create_all(self._engine)

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
        )
