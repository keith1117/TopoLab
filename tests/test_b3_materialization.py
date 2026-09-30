"""B3 prefix, interruption, charged resources, and independent-audit stop boundaries."""

import fcntl
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import topolab.b3_materialization as materialization
from topolab.b3_access import B3ArtifactReference
from topolab.b3_artifacts import B3DataArtifact, write_b3_record
from topolab.b3_dataset import B3_DATA_RSS_BYTES, B3_DATA_SECONDS
from topolab.b3_materialization import (
    B3DataFailure,
    B3DataSuccess,
    B3MaterializationIndex,
    b3_data_summary,
    read_b3_index,
    run_b3_data,
    write_b3_index,
)


def _run(root, manifest, **kwargs):  # type: ignore[no-untyped-def]
    return run_b3_data(
        root, manifest, repository_root=Path(__file__).resolve().parents[1], **kwargs
    )


def _synthetic_success(manifest, entry):  # type: ignore[no-untyped-def]
    # Metadata-only scaffolding for complete-population negative controls.
    kind = "reference" if entry.role == "screen_validation" else "label"
    access = B3ArtifactReference(
        kind=kind, entry=entry, artifact_sha256="c" * 64, origins=(entry.case,)
    )
    return B3DataSuccess(
        entry=entry,
        artifact=B3DataArtifact(
            access=access,
            manifest_sha256=manifest.sha256(),
            source_revision=manifest.context.source_revision,
            byte_size=1,
            relative_path=f"artifacts/{kind}/{entry.case.case_id}/{'c' * 64}.json",
        ),
        seconds=1,
        uniform_compliance=1,
        iterations=1,
        physical_volume_error=0,
    )


def test_gate_requires_complete_audited_population(b3_manifest):  # type: ignore[no-untyped-def]
    entries = tuple(_synthetic_success(b3_manifest, e) for e in b3_manifest.data_entries())
    index = B3MaterializationIndex(
        manifest=b3_manifest,
        manifest_sha256=b3_manifest.sha256(),
        entries=entries,
        audited_case_ids=tuple(e.entry.case.case_id for e in entries),
        cumulative_seconds=608,
        peak_rss_bytes=1,
    )
    assert index.data_gate_passed
    assert b3_data_summary(index)["labels_succeeded"] == 560
    assert b3_data_summary(index)["references_succeeded"] == 48
    for update in (
        {"entries": entries[:-1], "audited_case_ids": index.audited_case_ids[:-1]},
        {"audited_case_ids": index.audited_case_ids[:-1]},
        {"resource_failed": True},
        {"integrity_failed": True},
        {"cumulative_seconds": B3_DATA_SECONDS + 1},
        {"peak_rss_bytes": B3_DATA_RSS_BYTES + 1},
        {"active_checkpoint_at": datetime.now(UTC)},
    ):
        changed = B3MaterializationIndex.model_validate(
            index.model_copy(update=update).model_dump(mode="json")
        )
        assert not b3_data_summary(changed)["data_gate_passed"]
    failed = index.model_copy(
        update={
            "entries": (*entries[:-1], B3DataFailure(entry=entries[-1].entry, seconds=1)),
            "audited_case_ids": index.audited_case_ids[:-1],
        }
    )
    assert not B3MaterializationIndex.model_validate(
        failed.model_dump(mode="json")
    ).data_gate_passed


def test_prefix_and_append_only_failure_records(tmp_path, b3_manifest):  # type: ignore[no-untyped-def]
    task = b3_manifest.data_entries()[0]
    index = B3MaterializationIndex.start(b3_manifest).model_copy(
        update={
            "entries": (B3DataFailure(entry=task, seconds=3),),
            "cumulative_seconds": 3,
            "peak_rss_bytes": 1,
            "resource_failed": True,
        }
    )
    write_b3_index(tmp_path, index)
    assert read_b3_index(tmp_path, b3_manifest) == index
    for update in (
        {"entries": ()},
        {"cumulative_seconds": 2},
        {"peak_rss_bytes": 0},
        {"resource_failed": False},
    ):
        with pytest.raises(ValueError, match="append-only"):
            write_b3_index(tmp_path, index.model_copy(update=update))
    with pytest.raises(ValueError, match="prefix"):
        write_b3_index(
            tmp_path / "new",
            index.model_copy(
                update={"entries": (B3DataFailure(entry=b3_manifest.data_entries()[1], seconds=3),)}
            ),
        )
    other = b3_manifest.model_copy(
        update={"context": b3_manifest.context.model_copy(update={"source_revision": "b" * 40})}
    )
    with pytest.raises(ValueError, match="different frozen identity"):
        read_b3_index(tmp_path, other)


def test_interrupt_resume_skips_terminal_failure_and_charges_time(
    tmp_path, b3_manifest, monkeypatch
):  # type: ignore[no-untyped-def]
    now = [100.0]
    monkeypatch.setattr(materialization, "perf_counter", lambda: now[0])
    monkeypatch.setattr(materialization, "_peak_rss_bytes", lambda: 1024)
    calls = []

    def generate(manifest, entry, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(entry)
        now[0] += 5
        if len(calls) == 1:
            raise ValueError("terminal convergence failure")
        raise KeyboardInterrupt

    monkeypatch.setattr(materialization, "generate_b3_record", generate)
    with pytest.raises(KeyboardInterrupt):
        _run(tmp_path, b3_manifest, startup_seconds=2)
    first = read_b3_index(tmp_path, b3_manifest)
    assert first.cumulative_seconds == 12
    assert first.active_checkpoint_at is None
    assert len(first.entries) == 1 and isinstance(first.entries[0], B3DataFailure)
    with pytest.raises(KeyboardInterrupt):
        _run(tmp_path, b3_manifest)
    second = read_b3_index(tmp_path, b3_manifest)
    assert second.entries == first.entries
    assert second.cumulative_seconds == 17
    assert calls == [
        b3_manifest.data_entries()[0],
        b3_manifest.data_entries()[1],
        b3_manifest.data_entries()[1],
    ]


def test_success_is_resumed_and_independently_audited(
    tmp_path, b3_manifest, b3_record_factory, monkeypatch
):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(materialization, "_peak_rss_bytes", lambda: 1)
    task = b3_manifest.data_entries()[0]
    record = b3_record_factory(task)
    calls = []

    def generate(manifest, entry, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(entry)
        if entry == task:
            return record
        raise KeyboardInterrupt

    monkeypatch.setattr(materialization, "generate_b3_record", generate)
    with pytest.raises(KeyboardInterrupt):
        _run(tmp_path, b3_manifest)
    initial = read_b3_index(tmp_path, b3_manifest)
    assert len(initial.entries) == 1
    audited = _run(tmp_path, b3_manifest, audit_only=True)
    assert audited.audited_case_ids == (task.case.case_id,)
    assert not audited.data_gate_passed
    with pytest.raises(KeyboardInterrupt):
        _run(tmp_path, b3_manifest)
    assert calls.count(task) == 1
    assert read_b3_index(tmp_path, b3_manifest).cumulative_seconds > initial.cumulative_seconds
    artifact = initial.entries[0].artifact
    path = tmp_path / artifact.relative_path
    contents = bytearray(path.read_bytes())
    contents[0] = ord("[")
    path.write_bytes(contents)
    previous_calls = len(calls)
    with pytest.raises(ValueError, match="checksum"):
        _run(tmp_path, b3_manifest)
    assert len(calls) == previous_calls
    corrupted = read_b3_index(tmp_path, b3_manifest)
    assert corrupted.integrity_failed and not corrupted.data_gate_passed
    assert corrupted.active_checkpoint_at is None


def test_numerical_audit_failure_is_persisted(
    tmp_path, b3_manifest, b3_record_factory, monkeypatch
):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(materialization, "_peak_rss_bytes", lambda: 1)
    task = b3_manifest.data_entries()[0]
    record = b3_record_factory(task)
    payload = record.model_dump(mode="json")
    payload["result"]["compliance"] *= 1.001
    payload["result"]["history"][-1]["compliance"] = payload["result"]["compliance"]
    bad = type(record).model_validate(payload)
    artifact = write_b3_record(tmp_path, b3_manifest, bad)
    outcome = B3DataSuccess(
        entry=task,
        artifact=artifact,
        seconds=1,
        uniform_compliance=bad.result.compliance,
        iterations=1,
        physical_volume_error=abs(
            bad.result.history[-1].volume_fraction - task.case.problem.optimization.volume_fraction
        ),
    )
    index = B3MaterializationIndex.start(b3_manifest).model_copy(update={"entries": (outcome,)})
    write_b3_index(tmp_path, index)
    with pytest.raises(RuntimeError, match="independent re-solve"):
        _run(tmp_path, b3_manifest, audit_only=True)
    persisted = read_b3_index(tmp_path, b3_manifest)
    assert persisted.integrity_failed
    assert persisted.audited_case_ids == ()
    with pytest.raises(ValueError, match="immutable integrity failure"):
        _run(tmp_path, b3_manifest, audit_only=True)


@pytest.mark.parametrize("kind", ["time", "rss", "callback"])
def test_resource_exhaustion_keeps_case_pending(tmp_path, b3_manifest, monkeypatch, kind):  # type: ignore[no-untyped-def]
    now = [10.0]
    monkeypatch.setattr(materialization, "perf_counter", lambda: now[0])
    monkeypatch.setattr(
        materialization, "_peak_rss_bytes", lambda: B3_DATA_RSS_BYTES + 1 if kind == "rss" else 1
    )

    def generate(manifest, entry, *, iteration_callback):  # type: ignore[no-untyped-def]
        assert kind == "callback"
        now[0] += B3_DATA_SECONDS
        iteration_callback(None)
        raise AssertionError("budget pulse did not abort")

    monkeypatch.setattr(materialization, "generate_b3_record", generate)
    index = _run(tmp_path, b3_manifest, startup_seconds=B3_DATA_SECONDS if kind == "time" else 0)
    assert index.resource_failed and index.entries == ()
    assert not index.data_gate_passed
    assert index.active_checkpoint_at is None


def test_unclosed_session_is_conservatively_charged(tmp_path, b3_manifest, monkeypatch):  # type: ignore[no-untyped-def]
    now = datetime(2026, 9, 30, tzinfo=UTC)
    monkeypatch.setattr(materialization, "_utc_now", lambda: now)
    monkeypatch.setattr(materialization, "perf_counter", lambda: 1)
    monkeypatch.setattr(materialization, "_peak_rss_bytes", lambda: 1)
    index = B3MaterializationIndex.start(b3_manifest).model_copy(
        update={"active_checkpoint_at": now - timedelta(seconds=60), "cumulative_seconds": 5}
    )
    write_b3_index(tmp_path, index)
    result = _run(tmp_path, b3_manifest, audit_only=True)
    assert result.cumulative_seconds == 65
    assert result.active_checkpoint_at is None


def test_single_writer_and_missing_audit_index(tmp_path, b3_manifest):  # type: ignore[no-untyped-def]
    with (tmp_path / ".b3-writer.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="another B3 data writer"):
            _run(tmp_path, b3_manifest)
    with pytest.raises(ValueError, match="audit requires"):
        _run(tmp_path, b3_manifest, audit_only=True)


@pytest.mark.parametrize("seconds", [-1, float("nan"), float("inf")])
def test_startup_charge_cannot_hide_resource_cost(tmp_path, b3_manifest, seconds):  # type: ignore[no-untyped-def]
    root = tmp_path / "absent"
    with pytest.raises(ValueError, match="startup resource charge"):
        _run(root, b3_manifest, startup_seconds=seconds)
    assert not root.exists()
