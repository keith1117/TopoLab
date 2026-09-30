"""SQLite persistence for optimization run state."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from sqlalchemy import (
    Boolean,
    Integer,
    String,
    Text,
    case,
    create_engine,
    literal,
    or_,
    select,
    update,
)
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from topolab.problem import TopologyProblem, TopologyResult
from topolab.run_migrations import migrate_run_database

INTERRUPTED_ERROR = "RunInterruptedError: process exited before run reached a terminal state"


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
    owner_id: str | None = None
    lease_expires_at: datetime | None = None


class RunStore(Protocol):
    """Storage operations required by the run manager."""

    def load_all(self) -> tuple[StoredRun, ...]:
        """Load every stored run."""

        ...

    def save(self, run: StoredRun) -> None:
        """Insert one historical run record; existing records are immutable here."""

        ...

    def load_one(self, run_id: str) -> StoredRun | None: ...

    def load_active(self) -> tuple[StoredRun, ...]: ...

    def insert_queued(self, run: StoredRun) -> None: ...

    def claim(
        self, run_id: str, owner_id: str, now: datetime, lease_expires_at: datetime
    ) -> bool: ...

    def save_owned(self, run: StoredRun, owner_id: str, now: datetime) -> bool: ...

    def renew(
        self, run_id: str, owner_id: str, now: datetime, lease_expires_at: datetime
    ) -> tuple[bool, bool]: ...

    def request_cancel(self, run_id: str, now: datetime) -> tuple[StoredRun | None, bool]: ...

    def recover_expired(self, now: datetime) -> None: ...


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
    owner_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lease_expires_at: Mapped[str | None] = mapped_column(String(40), nullable=True)


class SqliteRunStore:
    """Persist run snapshots and immutable contracts in one SQLite database."""

    def __init__(self, database_path: str | Path) -> None:
        path = Path(database_path).expanduser().resolve()
        url = URL.create("sqlite+pysqlite", database=str(path))
        self._engine = create_engine(url)
        self._session_factory = sessionmaker(self._engine)
        migrate_run_database(self._engine)

    def load_all(self) -> tuple[StoredRun, ...]:
        """Load and validate all persisted contracts."""

        with self._session_factory() as session:
            rows = session.scalars(select(_RunRow).order_by(_RunRow.run_id)).all()
            return tuple(self._decode(row) for row in rows)

    def load_one(self, run_id: str) -> StoredRun | None:
        with self._session_factory() as session:
            row = session.get(_RunRow, run_id)
            return None if row is None else self._decode(row)

    def load_active(self) -> tuple[StoredRun, ...]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(_RunRow).where(_RunRow.status.in_(("queued", "running")))
            ).all()
            return tuple(self._decode(row) for row in rows)

    def insert_queued(self, run: StoredRun) -> None:
        if run.status != "queued" or run.owner_id is not None or run.cancel_requested:
            raise ValueError("new runs must be unowned and queued")
        with self._session_factory.begin() as session:
            session.add(_RunRow(run_id=run.run_id, **_values(run)))

    def claim(
        self, run_id: str, owner_id: str, now: datetime, lease_expires_at: datetime
    ) -> bool:
        """Atomically move one unowned queued run to a leased running state."""

        with self._session_factory.begin() as session:
            changed = session.connection().execute(
                update(_RunRow)
                .where(
                    _RunRow.run_id == run_id,
                    _RunRow.status == "queued",
                    _RunRow.owner_id.is_(None),
                    _RunRow.cancel_requested.is_(False),
                )
                .values(
                    status="running",
                    owner_id=owner_id,
                    lease_expires_at=_serialize_timestamp(lease_expires_at),
                    updated_at=_serialize_timestamp(now),
                )
            ).rowcount
            return changed == 1

    def save_owned(self, run: StoredRun, owner_id: str, now: datetime) -> bool:
        """Write progress or a terminal result only while the lease is valid."""

        terminal = run.status in {"succeeded", "failed", "cancelled"}
        result_json = None if run.result is None else run.result.model_dump_json()
        status_value: object = run.status
        result_value: object = result_json
        if run.status == "succeeded":
            status_value = case(
                (_RunRow.cancel_requested.is_(True), "cancelled"), else_="succeeded"
            )
            result_value = case(
                (_RunRow.cancel_requested.is_(True), None), else_=result_json
            )
        with self._session_factory.begin() as session:
            changed = session.connection().execute(
                update(_RunRow)
                .where(
                    _RunRow.run_id == run.run_id,
                    _RunRow.status == "running",
                    _RunRow.owner_id == owner_id,
                    _RunRow.lease_expires_at > _serialize_timestamp(now),
                )
                .values(
                    status=status_value,
                    iteration=run.iteration,
                    cancel_requested=or_(
                        _RunRow.cancel_requested, literal(run.cancel_requested)
                    ),
                    result_json=result_value,
                    error=run.error,
                    updated_at=_serialize_timestamp(run.updated_at),
                    owner_id=None if terminal else owner_id,
                    lease_expires_at=None if terminal else _RunRow.lease_expires_at,
                )
            ).rowcount
            return changed == 1

    def renew(
        self, run_id: str, owner_id: str, now: datetime, lease_expires_at: datetime
    ) -> tuple[bool, bool]:
        """Renew a live lease and report a persisted cancellation request."""

        with self._session_factory.begin() as session:
            changed = session.connection().execute(
                update(_RunRow)
                .where(
                    _RunRow.run_id == run_id,
                    _RunRow.status == "running",
                    _RunRow.owner_id == owner_id,
                    _RunRow.lease_expires_at > _serialize_timestamp(now),
                )
                .values(lease_expires_at=_serialize_timestamp(lease_expires_at))
            ).rowcount
            if changed != 1:
                return False, False
            cancel_requested = session.scalar(
                select(_RunRow.cancel_requested).where(_RunRow.run_id == run_id)
            )
            return True, bool(cancel_requested)

    def request_cancel(self, run_id: str, now: datetime) -> tuple[StoredRun | None, bool]:
        """Cancel queued work or persist a running worker's cancellation request."""

        with self._session_factory.begin() as session:
            queued = session.connection().execute(
                update(_RunRow)
                .where(_RunRow.run_id == run_id, _RunRow.status == "queued")
                .values(
                    status="cancelled", cancel_requested=True,
                    updated_at=_serialize_timestamp(now),
                )
            ).rowcount
            running = session.connection().execute(
                update(_RunRow)
                .where(_RunRow.run_id == run_id, _RunRow.status == "running")
                .values(cancel_requested=True, updated_at=_serialize_timestamp(now))
            ).rowcount
            row = session.get(_RunRow, run_id)
            return (None if row is None else self._decode(row), queued == 1 or running == 1)

    def recover_expired(self, now: datetime) -> None:
        """Fail ownerless or expired runs; release expired queued ownership."""

        with self._session_factory.begin() as session:
            session.connection().execute(
                update(_RunRow)
                .where(
                    _RunRow.status == "running",
                    or_(
                        _RunRow.owner_id.is_(None),
                        _RunRow.lease_expires_at.is_(None),
                        _RunRow.lease_expires_at <= _serialize_timestamp(now),
                    ),
                )
                .values(
                    status="failed", owner_id=None, lease_expires_at=None,
                    result_json=None, error=INTERRUPTED_ERROR,
                    updated_at=_serialize_timestamp(now),
                )
            )
            session.connection().execute(
                update(_RunRow)
                .where(
                    _RunRow.status == "queued",
                    _RunRow.owner_id.is_not(None),
                    or_(
                        _RunRow.lease_expires_at.is_(None),
                        _RunRow.lease_expires_at <= _serialize_timestamp(now),
                    ),
                )
                .values(owner_id=None, lease_expires_at=None)
            )

    def save(self, run: StoredRun) -> None:
        """Insert a complete record without bypassing the ownership protocol."""

        with self._session_factory.begin() as session:
            if session.get(_RunRow, run.run_id) is not None:
                raise ValueError("existing runs require a fenced write")
            session.add(_RunRow(run_id=run.run_id, **_values(run)))

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
            owner_id=row.owner_id,
            lease_expires_at=(
                None if row.lease_expires_at is None
                else _deserialize_timestamp(row.lease_expires_at)
            ),
        )


def _values(run: StoredRun) -> dict[str, object]:
    return {
        "problem_json": run.problem.model_dump_json(),
        "status": run.status,
        "iteration": run.iteration,
        "cancel_requested": run.cancel_requested,
        "result_json": None if run.result is None else run.result.model_dump_json(),
        "error": run.error,
        "created_at": _serialize_timestamp(run.created_at),
        "updated_at": _serialize_timestamp(run.updated_at),
        "owner_id": run.owner_id,
        "lease_expires_at": (
            None if run.lease_expires_at is None
            else _serialize_timestamp(run.lease_expires_at)
        ),
    }


def _serialize_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("run timestamps must include a timezone")
    return value.astimezone(UTC).isoformat()


def _deserialize_timestamp(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("stored run timestamps must include a timezone")
    return timestamp.astimezone(UTC)
