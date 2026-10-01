"""Engineering timing, bounded callbacks, immutable publication and recovery."""

import importlib.util
import json
import multiprocessing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import sleep

import pytest

import topolab.b4_telemetry as telemetry
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_queries import AttemptTiming, QueryAttempt, QueryOutcome, QueryResourceExceeded
from topolab.b4_telemetry import CheckpointMeter, Journal, Progress, timed_query

CONTEXT = "a" * 64


def journal(root: Path, units: tuple[str, ...] = ("one", "two")) -> Journal:
    return Journal(root, CONTEXT, units, 1000, 2**40)


def test_lock_and_context_are_exclusive(tmp_path):  # type: ignore[no-untyped-def]
    first = journal(tmp_path)
    with pytest.raises(ValueError, match="writer"):
        journal(tmp_path)
    first.close()
    with pytest.raises(ValueError, match="context"):
        Journal(tmp_path, "b" * 64, ("one", "two"), 1000, 2**40)


def test_immutable_units_and_exact_prefix(tmp_path):  # type: ignore[no-untyped-def]
    writer = journal(tmp_path)
    with pytest.raises(ValueError, match="next unit"):
        writer.begin("two")
    with pytest.raises(ValueError, match="opened"):
        writer.publish("one", {})
    writer.begin("one")
    writer.publish("one", {"failed": True})
    writer.close()
    recovered = journal(tmp_path)
    assert recovered.state.completed == 1
    assert recovered.records[0]["payload"]["failed"]
    with pytest.raises(ValueError, match="next unit"):
        recovered.begin("one")
    recovered.close()
    path = tmp_path / "units/0000.json"
    record = json.loads(path.read_bytes())
    record["payload"]["failed"] = False
    path.write_bytes(canonical_metadata_bytes(record))
    with pytest.raises(ValueError, match="head"):
        journal(tmp_path)


def test_pending_recovery_preserves_attempt_and_downtime(tmp_path):  # type: ignore[no-untyped-def]
    writer = journal(tmp_path)
    writer.begin("one")
    writer.release()  # Simulate abrupt exit without close.
    path = tmp_path / "progress.json"
    state = Progress.model_validate_json(path.read_bytes())
    path.write_bytes(
        canonical_metadata_bytes(
            state.model_copy(
                update={
                    "active_at": datetime.now(UTC) - timedelta(seconds=20),
                }
            ).model_dump(mode="json")
        )
    )
    recovered = journal(tmp_path)
    assert recovered.state.pending == 0
    assert recovered.state.attempted == 1
    assert recovered.charged_seconds >= state.charged_seconds + 20
    recovered.begin("one")
    recovered.publish("one", {"fallback_seconds": 15})
    assert recovered.state.attempted == 2
    recovered.close()


def test_published_unit_recovers_before_progress_ack(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    writer = journal(tmp_path)
    writer.begin("one")
    original = writer.pulse
    monkeypatch.setattr(writer, "pulse", lambda **_: (_ for _ in ()).throw(RuntimeError("crash")))
    with pytest.raises(RuntimeError):
        writer.publish("one", {"complete": True})
    monkeypatch.setattr(writer, "pulse", original)
    writer.release()
    recovered = journal(tmp_path)
    assert recovered.state.completed == 1 and recovered.state.pending is None
    assert recovered.state.attempted == 1
    recovered.close()


def test_callbacks_never_read_units_and_remain_bounded(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    writer = journal(tmp_path, tuple(str(i) for i in range(48)))
    for i in range(48):
        writer.begin(str(i))
        writer.publish(str(i), {"large": "x" * 20_000})
    monkeypatch.setattr(Path, "read_bytes", lambda _: pytest.fail("callback read an existing file"))
    written = writer.pulse(force=True)
    assert 0 < written < telemetry.MAX_PROGRESS_BYTES
    writer.close()


def test_cadence_starts_after_write(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    now = [0.0]
    monkeypatch.setattr(telemetry, "perf_counter", lambda: now[0])
    original = telemetry.durable_write

    def slow_write(path, raw):  # type: ignore[no-untyped-def]
        original(path, raw)
        now[0] += 10

    monkeypatch.setattr(telemetry, "durable_write", slow_write)
    writer = journal(tmp_path)
    assert writer.last_flush == 10
    now[0] = 14
    assert writer.pulse() == 0
    now[0] = 15
    assert writer.pulse() > 0
    assert writer.last_flush == 25
    writer.close()


def test_resource_and_integrity_stops_are_permanent(tmp_path):  # type: ignore[no-untyped-def]
    writer = journal(tmp_path)
    writer.close(integrity_failed=True)
    with pytest.raises(ValueError, match="permanent"):
        journal(tmp_path)
    other = tmp_path / "resource"
    with pytest.raises(QueryResourceExceeded):
        Journal(other, CONTEXT, ("one",), 1, 2**40)
    with pytest.raises(QueryResourceExceeded):
        Journal(other, CONTEXT, ("one",), 1000, 2**40)


def test_query_envelope_covers_unphased_packaging_and_callbacks():
    failed = QueryAttempt(
        succeeded=False,
        failure_code="quality_error",
        failure_type="ValueError",
        timing=AttemptTiming(refinement_seconds=0.001),
    )
    meter = CheckpointMeter(lambda _: (sleep(0.005), 500)[1])

    def operation():  # type: ignore[no-untyped-def]
        meter()
        sleep(0.02)  # Witness construction outside legacy phase timers.
        meter()
        return QueryOutcome(method="uniform", seed=None, route="baseline", attempt=failed)

    outcome, timing = timed_query(operation)
    assert timing["wall_seconds"] >= 0.03
    assert timing["legacy_phase_seconds"] == outcome.seconds == 0.001
    assert meter.calls == meter.flushes == 2 and meter.bytes_written == 1000
    assert meter.wall_seconds >= 0.01 and timing["cpu_seconds"] >= 0


def _crash_writer(root: str) -> None:
    writer = journal(Path(root))
    writer.begin("one")
    __import__("os")._exit(7)


def test_actual_process_exit_recovers_pending_work(tmp_path):  # type: ignore[no-untyped-def]
    child = multiprocessing.get_context("spawn").Process(
        target=_crash_writer, args=(str(tmp_path),)
    )
    child.start()
    child.join(30)
    assert child.exitcode == 7
    recovered = journal(tmp_path)
    assert recovered.state.pending == 0 and recovered.state.attempted == 1
    recovered.close()


def test_sentinel_schedule_is_fixed_and_counterbalanced():
    spec = importlib.util.spec_from_file_location(
        "sentinel", "scripts/b4_4_engineering_sentinel.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    schedule = module.schedule()
    assert len(schedule) == 76
    assert [schedule[i]["arm"] for i in (0, 19, 38, 57)] == [
        "legacy",
        "compact",
        "compact",
        "legacy",
    ]
    assert len({(a["case_id"], a["method"], a["seed"]) for a in schedule}) == 19
    assert sum(a["method"] == "uniform" for a in schedule) == 24
    plan = module.plan_payload()
    assert (
        module.digest(
            canonical_metadata_bytes({k: v for k, v in plan.items() if k != "plan_sha256"})
        )
        == plan["plan_sha256"]
    )


def test_symlink_root_and_changed_unit_population_rejected(tmp_path):  # type: ignore[no-untyped-def]
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="real root"):
        journal(link)
    writer = journal(target)
    writer.close()
    with pytest.raises(ValueError, match="context"):
        journal(target, ("changed",))


def test_missing_committed_unit_rejected(tmp_path):  # type: ignore[no-untyped-def]
    writer = journal(tmp_path)
    writer.begin("one")
    writer.publish("one", {})
    writer.close()
    (tmp_path / "units/0000.json").unlink()
    with pytest.raises(ValueError, match="prefix"):
        journal(tmp_path)


def test_resource_exception_is_not_converted_to_candidate_failure():
    meter = CheckpointMeter(lambda _: (_ for _ in ()).throw(QueryResourceExceeded("cap")))
    with pytest.raises(QueryResourceExceeded):
        timed_query(lambda: meter())  # type: ignore[arg-type,func-returns-value]
    assert meter.calls == 1 and meter.wall_seconds > 0
