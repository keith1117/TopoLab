"""Versioned engineering query envelopes and bounded single-writer progress."""

import fcntl
import hashlib
import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter, process_time
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from topolab.b3_artifacts import atomic_write, safe_path
from topolab.b3_catalog import Sha256, canonical_metadata_bytes
from topolab.b3_dataset import NonnegativeSeconds
from topolab.b3_materialization import _peak_rss_bytes
from topolab.b3_queries import QueryOutcome, QueryResourceExceeded
from topolab.problem import ContractModel

HEARTBEAT_SECONDS = 5.0
MAX_PROGRESS_BYTES = 4096
CLOSE_ALLOWANCE = 10.0


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def durable_write(path: Path, raw: bytes) -> None:
    """Publish a file then sync its directory before acknowledging the boundary."""
    atomic_write(path, raw)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Progress(ContractModel):
    version: Literal["topolab.b4.progress.v1"] = "topolab.b4.progress.v1"
    context_sha256: Sha256
    units_sha256: Sha256
    completed: Annotated[int, Field(strict=True, ge=0)] = 0
    head_sha256: Sha256 = "0" * 64
    pending: Annotated[int, Field(strict=True, ge=0)] | None = None
    attempted: Annotated[int, Field(strict=True, ge=0)] = 0
    charged_seconds: NonnegativeSeconds = 0
    peak_rss_bytes: Annotated[int, Field(strict=True, ge=0)] = 0
    active_at: datetime | None = None
    resource_failed: bool = False
    integrity_failed: bool = False

    @model_validator(mode="after")
    def validate_boundary(self) -> "Progress":
        if (
            self.attempted < self.completed
            or self.pending not in (None, self.completed)
            or self.active_at is not None
            and self.active_at.utcoffset() is None
        ):
            raise ValueError("progress attempt count, pending ordinal or UTC boundary differs")
        return self


class Journal:
    """Immutable chained units; only constant-size progress is touched by pulse."""

    def __init__(
        self,
        root: Path,
        context_sha256: str,
        units: tuple[str, ...],
        max_seconds: float,
        max_rss_bytes: int,
        *,
        opening_seconds: float = 0,
    ) -> None:
        opened = perf_counter()
        units_sha256 = digest(canonical_metadata_bytes(list(units)))
        if opening_seconds < 0 or root.is_symlink() or len(set(units)) != len(units):
            raise ValueError("journal requires a real root and unique frozen units")
        root.mkdir(parents=True, exist_ok=True)
        self.root, self.units = root.resolve(), units
        self.max_seconds, self.max_rss_bytes = max_seconds, max_rss_bytes
        self.lock = safe_path(self.root, "writer.lock").open("a+b")
        try:
            fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise ValueError("engineering journal already has a writer") from None
        try:
            path = safe_path(self.root, "progress.json")
            self.state = (
                Progress.model_validate_json(path.read_bytes())
                if path.exists()
                else Progress(context_sha256=context_sha256, units_sha256=units_sha256)
            )
            if (
                self.state.context_sha256 != context_sha256
                or self.state.units_sha256 != units_sha256
                or path.exists()
                and path.read_bytes()
                != canonical_metadata_bytes(self.state.model_dump(mode="json"))
            ):
                raise ValueError("journal context differs")
            self.records: list[dict[str, Any]] = []
            head = "0" * 64
            for ordinal, unit in enumerate(units):
                target = self.unit_path(ordinal)
                if not target.exists():
                    break
                raw = target.read_bytes()
                record = json.loads(raw)
                if (
                    canonical_metadata_bytes(record) != raw
                    or record.get("version") != "topolab.b4.unit.v1"
                    or record.get("context_sha256") != context_sha256
                    or record.get("unit") != unit
                    or record.get("previous_sha256") != head
                ):
                    raise ValueError("journal unit identity, bytes or chain differs")
                head = digest(raw)
                self.records.append(record)
                if ordinal + 1 == self.state.completed and head != self.state.head_sha256:
                    raise ValueError("journal committed head differs")
            count = len(self.records)
            if (
                self.state.completed > count
                or count > self.state.completed + 1
                or count > self.state.completed
                and self.state.pending != count - 1
                or self.state.pending not in (None, self.state.completed)
                or self.state.completed == 0
                and self.state.head_sha256 != "0" * 64
                or any(self.unit_path(i).exists() for i in range(count, len(units)))
            ):
                raise ValueError("journal must retain its exact completed/pending prefix")
            downtime = (
                0.0
                if self.state.active_at is None
                else (datetime.now(UTC) - self.state.active_at).total_seconds()
            )
            if downtime < 0:
                raise ValueError("recovery clock moved backwards")
            self.prior = (
                self.state.charged_seconds + downtime + opening_seconds + perf_counter() - opened
            )
            self.started = perf_counter()
            self.last_flush = self.started
            self.state = self.state.model_copy(
                update={
                    "completed": count,
                    "head_sha256": head,
                    "pending": None if count > self.state.completed else self.state.pending,
                }
            )
            self.pulse(force=True)
        except BaseException:
            self.release()
            raise

    def unit_path(self, ordinal: int) -> Path:
        return safe_path(self.root, f"units/{ordinal:04d}.json")

    @property
    def charged_seconds(self) -> float:
        return self.prior + perf_counter() - self.started

    def pulse(self, *, force: bool = False) -> int:
        now = perf_counter()
        rss = max(self.state.peak_rss_bytes, _peak_rss_bytes())
        exceeded = (
            self.charged_seconds + CLOSE_ALLOWANCE > self.max_seconds or rss > self.max_rss_bytes
        )
        self.state = self.state.model_copy(
            update={
                "peak_rss_bytes": rss,
                "resource_failed": self.state.resource_failed or exceeded,
            }
        )
        if force or exceeded or now - self.last_flush >= HEARTBEAT_SECONDS:
            # The start-of-write UTC conservatively charges a crash during fsync.
            self._save(active_at=datetime.now(UTC))
            self.last_flush = perf_counter()  # Costly writes do not consume the next interval.
            written = safe_path(self.root, "progress.json").stat().st_size
        else:
            written = 0
        if self.state.resource_failed:
            raise QueryResourceExceeded("engineering resource cap is permanently exceeded")
        if self.state.integrity_failed:
            raise ValueError("engineering journal has a permanent integrity failure")
        return written

    def _save(self, *, active_at: datetime | None, allowance: float = 0) -> None:
        self.state = self.state.model_copy(
            update={
                "charged_seconds": self.charged_seconds + allowance,
                "active_at": active_at,
            }
        )
        raw = canonical_metadata_bytes(self.state.model_dump(mode="json"))
        if len(raw) > MAX_PROGRESS_BYTES:
            raise ValueError("bounded progress exceeds its byte limit")
        durable_write(safe_path(self.root, "progress.json"), raw)

    def begin(self, unit: str) -> None:
        ordinal = self.state.completed
        if ordinal >= len(self.units) or self.units[ordinal] != unit:
            raise ValueError("queries require the exact frozen next unit")
        self.state = self.state.model_copy(
            update={
                "pending": ordinal,
                "attempted": self.state.attempted + 1,
            }
        )
        self.pulse(force=True)

    def publish(self, unit: str, payload: dict[str, Any]) -> None:
        ordinal = self.state.completed
        if self.state.pending != ordinal or self.units[ordinal] != unit:
            raise ValueError("publication requires its durably opened attempt")
        path = self.unit_path(ordinal)
        if path.exists():
            raise ValueError("completed unit records are immutable")
        record = {
            "version": "topolab.b4.unit.v1",
            "context_sha256": self.state.context_sha256,
            "unit": unit,
            "previous_sha256": self.state.head_sha256,
            "payload": payload,
        }
        raw = canonical_metadata_bytes(record)
        durable_write(path, raw)
        self.records.append(record)
        self.state = self.state.model_copy(
            update={
                "completed": ordinal + 1,
                "head_sha256": digest(raw),
                "pending": None,
            }
        )
        self.pulse(force=True)

    def close(self, *, integrity_failed: bool = False) -> None:
        try:
            self.state = self.state.model_copy(
                update={
                    "integrity_failed": self.state.integrity_failed or integrity_failed,
                    "peak_rss_bytes": max(self.state.peak_rss_bytes, _peak_rss_bytes()),
                }
            )
            self._save(active_at=None, allowance=CLOSE_ALLOWANCE)
        finally:
            self.release()

    def release(self) -> None:
        if not self.lock.closed:
            fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
            self.lock.close()


class CheckpointMeter:
    """Measure inclusive callback work, including writes, without subtracting it."""

    def __init__(self, pulse: Callable[[bool], int]) -> None:
        self.pulse = pulse
        self.calls = self.flushes = self.bytes_written = 0
        self.wall_seconds = self.cpu_seconds = self.flush_wall_seconds = 0.0

    def __call__(self) -> None:
        wall, cpu = perf_counter(), process_time()
        self.calls += 1
        try:
            written = self.pulse(self.calls == 2)
            if written:
                self.flushes += 1
                self.bytes_written += written
                self.flush_wall_seconds += perf_counter() - wall
        finally:
            self.wall_seconds += perf_counter() - wall
            self.cpu_seconds += process_time() - cpu

    def summary(self) -> dict[str, int | float]:
        return {
            name: getattr(self, name)
            for name in (
                "calls",
                "flushes",
                "bytes_written",
                "wall_seconds",
                "cpu_seconds",
                "flush_wall_seconds",
            )
        }


def timed_query(operation: Callable[[], QueryOutcome]) -> tuple[QueryOutcome, dict[str, float]]:
    """Include callbacks, witness construction, validation and full fallback."""
    wall, cpu = perf_counter(), process_time()
    outcome = operation()
    return outcome, {
        "wall_seconds": perf_counter() - wall,
        "cpu_seconds": process_time() - cpu,
        "legacy_phase_seconds": outcome.seconds,
    }
