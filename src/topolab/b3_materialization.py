"""Single-writer B3 materialization, recoverable resource charges, and data audit."""

import fcntl
import hashlib
import resource
import sys
from collections import Counter
from datetime import UTC, datetime
from math import isfinite
from pathlib import Path
from time import perf_counter
from typing import Annotated, Literal

from pydantic import Field, model_validator

from topolab.b3_access import B3Access
from topolab.b3_artifacts import (
    B3DataArtifact,
    atomic_write,
    read_b3_record,
    safe_path,
    write_b3_record,
)
from topolab.b3_catalog import B3CatalogEntry, CaseId, Sha256, canonical_metadata_bytes
from topolab.b3_dataset import (
    B3_DATA_RSS_BYTES,
    B3_DATA_SECONDS,
    B3DatasetManifest,
    NonnegativeSeconds,
    audit_b3_record,
    generate_b3_record,
)
from topolab.dataset_cli import validate_external_output_root
from topolab.problem import ContractModel
from topolab.simp import SimpIteration


class B3ResourceExceeded(RuntimeError):
    """Stop pending work without extending the frozen data-stage budget."""


class B3DataSuccess(ContractModel):
    status: Literal["succeeded"] = "succeeded"
    entry: B3CatalogEntry
    artifact: B3DataArtifact
    seconds: NonnegativeSeconds
    uniform_compliance: Annotated[float, Field(gt=0.0)]
    iterations: Annotated[int, Field(strict=True, gt=0, le=360)]
    physical_volume_error: Annotated[float, Field(ge=0.0, le=0.005)]


class B3DataFailure(ContractModel):
    status: Literal["failed"] = "failed"
    entry: B3CatalogEntry
    seconds: NonnegativeSeconds
    failure_code: Literal["generation_or_quality"] = "generation_or_quality"


type B3DataOutcome = Annotated[B3DataSuccess | B3DataFailure, Field(discriminator="status")]


class B3MaterializationIndex(ContractModel):
    """Exact canonical prefix; completed outcomes and cumulative charges cannot shrink."""

    index_version: Literal["topolab.b3.materialization.v1"] = "topolab.b3.materialization.v1"
    manifest: B3DatasetManifest
    manifest_sha256: Sha256
    entries: tuple[B3DataOutcome, ...] = ()
    cumulative_seconds: NonnegativeSeconds = 0.0
    peak_rss_bytes: Annotated[int, Field(strict=True, ge=0)] = 0
    active_checkpoint_at: datetime | None = None
    resource_failed: bool = False
    integrity_failed: bool = False
    audited_case_ids: tuple[CaseId, ...] = ()

    @classmethod
    def start(cls, manifest: B3DatasetManifest) -> "B3MaterializationIndex":
        return cls(manifest=manifest, manifest_sha256=manifest.sha256())

    @model_validator(mode="after")
    def validate_index(self) -> "B3MaterializationIndex":
        if self.manifest_sha256 != self.manifest.sha256():
            raise ValueError("index manifest checksum differs from the embedded manifest")
        tasks = self.manifest.data_entries()
        if len(self.entries) > len(tasks):
            raise ValueError("index contains too many outcomes")
        for outcome, task in zip(self.entries, tasks, strict=False):
            if outcome.entry != task:
                raise ValueError("index must retain the exact canonical data-case prefix")
            if isinstance(outcome, B3DataSuccess):
                artifact = outcome.artifact
                expected_kind = "reference" if task.role == "screen_validation" else "label"
                if (
                    artifact.access.entry != task
                    or artifact.access.kind != expected_kind
                    or artifact.manifest_sha256 != self.manifest_sha256
                    or artifact.source_revision != self.manifest.context.source_revision
                ):
                    raise ValueError("success artifact differs from its frozen task/provenance")
        successes = tuple(
            e.entry.case.case_id for e in self.entries if isinstance(e, B3DataSuccess)
        )
        if self.audited_case_ids != tuple(c for c in successes if c in self.audited_case_ids):
            raise ValueError("audit IDs must be a unique ordered subset of successful cases")
        if self.active_checkpoint_at is not None and self.active_checkpoint_at.utcoffset() != (
            UTC.utcoffset(self.active_checkpoint_at)
        ):
            raise ValueError("active resource checkpoint must have a UTC timestamp")
        return self

    @property
    def data_gate_passed(self) -> bool:
        expected = tuple(e.case.case_id for e in self.manifest.data_entries())
        return (
            len(self.entries) == 608
            and self.audited_case_ids == expected
            and not self.resource_failed
            and not self.integrity_failed
            and self.active_checkpoint_at is None
            and self.cumulative_seconds <= B3_DATA_SECONDS
            and self.peak_rss_bytes <= B3_DATA_RSS_BYTES
        )


def index_path(root: Path) -> Path:
    # A stable path prevents a changed source/runtime from silently starting another budget.
    return safe_path(root, "b3_materialization.json")


def read_b3_index(root: Path, manifest: B3DatasetManifest) -> B3MaterializationIndex:
    """Read metadata only; planning never follows artifact references."""

    contents = index_path(root).read_bytes()
    index = B3MaterializationIndex.model_validate_json(contents)
    if canonical_metadata_bytes(index.model_dump(mode="json")) != contents:
        raise ValueError("materialization index is not canonical JSON")
    if index.manifest != manifest:
        raise ValueError("existing data index has a different frozen identity")
    return index


def _verify_success(
    root: Path, manifest: B3DatasetManifest, outcome: B3DataSuccess, *, numerical: bool
) -> None:
    record = read_b3_record(root, manifest, outcome.artifact, B3Access(consumer="data_audit"))
    volume_error = abs(
        record.result.history[-1].volume_fraction
        - record.entry.case.problem.optimization.volume_fraction
    )
    if (
        record.entry != outcome.entry
        or record.result.compliance != outcome.uniform_compliance
        or len(record.result.history) != outcome.iterations
        or volume_error != outcome.physical_volume_error
    ):
        raise ValueError("success summary differs from its verified artifact")
    if numerical:
        audit_b3_record(record)


def write_b3_index(root: Path, index: B3MaterializationIndex) -> None:
    """Atomically append outcomes; verify new successful artifacts before publication."""

    index = B3MaterializationIndex.model_validate(index.model_dump(mode="json"))
    target = index_path(root)
    previous = read_b3_index(root, index.manifest) if target.exists() else None
    prefix = 0 if previous is None else len(previous.entries)
    if previous is not None:
        if (
            len(index.entries) < prefix
            or index.entries[:prefix] != previous.entries
            or index.cumulative_seconds < previous.cumulative_seconds
            or index.peak_rss_bytes < previous.peak_rss_bytes
            or previous.resource_failed
            and not index.resource_failed
            or previous.integrity_failed
            and not index.integrity_failed
        ):
            raise ValueError("completed B3 outcomes and resource/failure records are append-only")
    for outcome in index.entries[prefix:]:
        if isinstance(outcome, B3DataSuccess):
            _verify_success(root, index.manifest, outcome, numerical=False)
    atomic_write(target, canonical_metadata_bytes(index.model_dump(mode="json")))


def _peak_rss_bytes() -> int:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss if sys.platform == "darwin" else rss * 1024


def _utc_now() -> datetime:
    return datetime.now(UTC)


def run_b3_data(
    root: Path,
    manifest: B3DatasetManifest,
    *,
    repository_root: Path,
    audit_only: bool = False,
    startup_seconds: float = 0.0,
) -> B3MaterializationIndex:
    """Resume the fixed data program or audit it, charging every invocation and interruption."""

    started = perf_counter() - startup_seconds
    manifest = B3DatasetManifest.model_validate(manifest.model_dump(mode="json"))
    if startup_seconds < 0 or not isfinite(startup_seconds):
        raise ValueError("startup resource charge must be finite and nonnegative")
    root = validate_external_output_root(repository_root, root)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = safe_path(root, ".b3-writer.lock")
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("another B3 data writer owns this root") from error
        target = index_path(root)
        if audit_only and not target.exists():
            raise ValueError("audit requires an existing B3 data index")
        index = (
            read_b3_index(root, manifest)
            if target.exists()
            else (B3MaterializationIndex.start(manifest))
        )
        if index.active_checkpoint_at is not None:
            # No durable process-end receipt: conservatively charge the whole unclosed interval.
            unclosed = max(0.0, (_utc_now() - index.active_checkpoint_at).total_seconds())
            index = index.model_copy(
                update={"cumulative_seconds": index.cumulative_seconds + unclosed}
            )
        charged_at = started

        def checkpoint(*, close: bool = False) -> None:
            nonlocal index, charged_at
            now = perf_counter()
            elapsed = index.cumulative_seconds + now - charged_at
            rss = max(index.peak_rss_bytes, _peak_rss_bytes())
            index = index.model_copy(
                update={
                    "cumulative_seconds": elapsed,
                    "peak_rss_bytes": rss,
                    "active_checkpoint_at": None if close else _utc_now(),
                    "resource_failed": index.resource_failed
                    or elapsed > B3_DATA_SECONDS
                    or rss > B3_DATA_RSS_BYTES,
                }
            )
            write_b3_index(root, index)
            charged_at = now

        def check_budget() -> None:
            elapsed = index.cumulative_seconds + perf_counter() - charged_at
            if (
                index.resource_failed
                or elapsed >= B3_DATA_SECONDS
                or _peak_rss_bytes() > B3_DATA_RSS_BYTES
            ):
                raise B3ResourceExceeded("B3 data-stage resource budget is exhausted")

        def pulse(_state: SimpIteration) -> None:
            check_budget()
            if perf_counter() - charged_at >= 5.0:
                checkpoint()

        index = index.model_copy(update={"audited_case_ids": ()})
        checkpoint()
        try:
            if index.integrity_failed:
                raise ValueError("B3 data index has an immutable integrity failure")
            check_budget()
            # Resume checks all persisted successes before solving another pending case.
            for outcome in index.entries:
                check_budget()
                if isinstance(outcome, B3DataSuccess):
                    _verify_success(root, manifest, outcome, numerical=False)
            if not audit_only:
                for task in manifest.data_entries()[len(index.entries) :]:
                    check_budget()
                    case_started = perf_counter()
                    try:
                        record = generate_b3_record(manifest, task, iteration_callback=pulse)
                    except B3ResourceExceeded:
                        raise
                    except (ValueError, RuntimeError, ArithmeticError):
                        outcome = B3DataFailure(entry=task, seconds=perf_counter() - case_started)
                    else:
                        artifact = write_b3_record(root, manifest, record)
                        outcome = B3DataSuccess(
                            entry=task,
                            artifact=artifact,
                            seconds=perf_counter() - case_started,
                            uniform_compliance=record.result.compliance,
                            iterations=len(record.result.history),
                            physical_volume_error=abs(
                                record.result.history[-1].volume_fraction
                                - task.case.problem.optimization.volume_fraction
                            ),
                        )
                    index = index.model_copy(update={"entries": (*index.entries, outcome)})
                    checkpoint()
            audited = []
            for outcome in index.entries:
                check_budget()
                if isinstance(outcome, B3DataSuccess):
                    _verify_success(root, manifest, outcome, numerical=True)
                    audited.append(outcome.entry.case.case_id)
                    index = index.model_copy(update={"audited_case_ids": tuple(audited)})
                    checkpoint()
        except B3ResourceExceeded:
            index = index.model_copy(update={"resource_failed": True})
        except (ValueError, RuntimeError, PermissionError, FileNotFoundError):
            index = index.model_copy(update={"integrity_failed": True})
            raise
        finally:
            checkpoint(close=True)
        return index


def b3_data_summary(index: B3MaterializationIndex) -> dict[str, object]:
    """Report every role/stratum and bind the exact final checkpoint bytes."""

    successes = tuple(e for e in index.entries if isinstance(e, B3DataSuccess))
    counts = Counter(_stratum(e.entry) for e in successes)
    expected = Counter(_stratum(e) for e in index.manifest.data_entries())
    return {
        "summary_version": "topolab.b3.data-audit.v1",
        "manifest_sha256": index.manifest_sha256,
        "index_sha256": hashlib.sha256(
            canonical_metadata_bytes(index.model_dump(mode="json"))
        ).hexdigest(),
        "source_revision": index.manifest.context.source_revision,
        "labels_succeeded": sum(e.entry.role != "screen_validation" for e in successes),
        "references_succeeded": sum(e.entry.role == "screen_validation" for e in successes),
        "failed": len(index.entries) - len(successes),
        "pending": 608 - len(index.entries),
        "audited": len(index.audited_case_ids),
        "counts": dict(sorted(counts.items())),
        "expected_counts": dict(sorted(expected.items())),
        "artifact_bytes": sum(e.artifact.byte_size for e in successes),
        "cumulative_seconds": index.cumulative_seconds,
        "peak_rss_bytes": index.peak_rss_bytes,
        "resource_failed": index.resource_failed,
        "integrity_failed": index.integrity_failed,
        "data_gate_passed": index.data_gate_passed and counts == expected,
    }


def _stratum(entry: B3CatalogEntry) -> str:
    mesh = "x".join(map(str, entry.case.problem.mesh.element_counts))
    direction = entry.case.problem.loads[0].direction
    volume = entry.case.problem.optimization.volume_fraction
    return f"{entry.role}:{mesh}:{direction}:{volume:.4f}"
