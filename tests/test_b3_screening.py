"""Synthetic screen selection, artifact boundaries, recovery and CLI preflight."""

import fcntl
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import topolab.b3_screen_cli as cli
import topolab.b3_screening as screen
import topolab.b3_training_artifacts as training
from topolab.b3_access import B3Access, B3ArtifactReference
from topolab.b3_artifacts import B3DataArtifact
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_materialization import B3DataSuccess, B3MaterializationIndex
from topolab.b3_queries import (
    METHODS,
    AttemptTiming,
    QueryAttempt,
    QueryOutcome,
    TerminalWitness,
    policy_route,
)
from topolab.b3_screening import (
    B3CaseRecord,
    B3EvaluationIndex,
    B3Freeze,
    B3ScreenContext,
    CaseFile,
    CaseMeasures,
    QueryMeasure,
    publish_freeze,
    read_case,
    read_screen_index,
    run_screen,
    screen_entries,
    screen_summary,
    selection_decision,
    write_case,
    write_screen_index,
)
from topolab.b3_training_artifacts import B3TrainingContext, B3TrainingIndex, FitFile, FitOutcome
from topolab.baselines import BaselineMetrics


@pytest.fixture(scope="module")
def synthetic_data(b3_manifest):  # type: ignore[no-untyped-def]
    entries = []
    for entry in b3_manifest.data_entries():
        kind = "reference" if entry.role == "screen_validation" else "label"
        access = B3ArtifactReference(
            kind=kind, entry=entry, artifact_sha256="c" * 64, origins=(entry.case,)
        )
        entries.append(
            B3DataSuccess(
                entry=entry,
                artifact=B3DataArtifact(
                    access=access,
                    manifest_sha256=b3_manifest.sha256(),
                    source_revision=b3_manifest.context.source_revision,
                    byte_size=1,
                    relative_path=f"artifacts/{kind}/{entry.case.case_id}/{'c' * 64}.json",
                ),
                seconds=1,
                uniform_compliance=1,
                iterations=1,
                physical_volume_error=0,
            )
        )
    return B3MaterializationIndex(
        manifest=b3_manifest,
        manifest_sha256=b3_manifest.sha256(),
        entries=tuple(entries),
        audited_case_ids=tuple(e.entry.case.case_id for e in entries),
        cumulative_seconds=608,
        peak_rss_bytes=1,
    )


@pytest.fixture
def context(synthetic_data, monkeypatch):  # type: ignore[no-untyped-def]
    # Exact synthetic metadata-only receipts replace only the two expected digests.
    # These scaffolds read no production artifact and make no fitting/quality claim.
    data_bytes = canonical_metadata_bytes(synthetic_data.model_dump(mode="json"))
    digest = training.digest
    monkeypatch.setattr(
        training,
        "digest",
        lambda b: training.B3_DATA_INDEX_SHA256 if b == data_bytes else digest(b),
    )
    fitting_context = B3TrainingContext(
        source=synthetic_data.manifest.context, data_index=synthetic_data
    )
    fitting = B3TrainingIndex(
        context=fitting_context,
        context_sha256=fitting_context.sha256(),
        outcomes=tuple(
            FitOutcome(
                recipe=r, seed=s, selection=FitFile(kind="selection", sha256="d" * 64, byte_size=1)
            )
            for r, s in training.TASKS
        ),
        audited_fits=training.TASKS,
        attempted_epochs=312,
        cumulative_seconds=100,
        peak_rss_bytes=1,
    )
    fit_bytes = canonical_metadata_bytes(fitting.model_dump(mode="json"))
    monkeypatch.setattr(
        screen, "digest", lambda b: screen.TRAINING_INDEX_SHA256 if b == fit_bytes else digest(b)
    )
    return B3ScreenContext(source=synthetic_data.manifest.context, training_index=fitting)


def _rows():  # type: ignore[no-untyped-def]
    metrics = BaselineMetrics(iterations=50, final_compliance=1, physical_volume_error=0)
    rows = []
    for entry in screen_entries():
        queries = []
        for method, seed in METHODS:
            ratio = 1 if method == "uniform" else 0.6 if method == "P" else 0.8
            seconds = 10 * ratio
            queries.append(
                QueryMeasure(
                    name=screen.method_name(method, seed),
                    succeeded=True,
                    candidate_failed=False,
                    rejected=False,
                    fallback_used=False,
                    end_to_end_seconds=seconds,
                    paired_time_ratio=seconds / 10,
                    candidate=metrics,
                    operational=metrics,
                )
            )
        rows.append(CaseMeasures(entry=entry, queries=tuple(queries)))
    return tuple(rows)


def _edit(rows, name, predicate=lambda e: True, *, ratio=None, failed=False):  # type: ignore[no-untyped-def]
    result = []
    for row in rows:
        updated = []
        for q in row.queries:
            if q.name == name and predicate(row.entry):
                updates = {}
                if ratio is not None:
                    updates.update(
                        end_to_end_seconds=ratio * 10, paired_time_ratio=(ratio * 10) / 10
                    )
                if failed:
                    updates.update(succeeded=False, candidate_failed=True, fallback_used=True)
                q = q.model_copy(update=updates)
            updated.append(q)
        result.append(row.model_copy(update={"queries": tuple(updated)}))
    return tuple(result)


def _complete_index(context, rows=None):  # type: ignore[no-untyped-def]
    rows = _rows() if rows is None else rows
    references = tuple(
        CaseFile(
            access=B3ArtifactReference(
                kind="outcome", entry=row.entry, artifact_sha256="e" * 64, origins=(row.entry.case,)
            ),
            byte_size=1,
            measures=row,
        )
        for row in rows
    )
    return B3EvaluationIndex(
        context=context,
        context_sha256=context.sha256(),
        cases=references,
        attempted_cases=48,
        cumulative_seconds=100,
        peak_rss_bytes=1,
        audited_case_ids=tuple(e.case.case_id for e in screen_entries()),
    )


def test_frozen_selection_and_ties_retain_all_controls() -> None:
    result = selection_decision(_rows())
    assert result["passing_seeds"] == [17, 29, 43]
    assert result["selected_seed"] == 17 and result["model_gate_passed"]
    assert result["quality_cells"] == {"0.5351": 9, "0.5931": 9}
    assert len(result["selection_table"]) == 15
    result = selection_decision(_edit(_rows(), "P/29", ratio=0.59))
    assert result["selected_seed"] == 29


def test_scale_direction_bounds_and_diagnostics_cannot_replace_primary() -> None:
    rows = _rows()

    def large(e):  # type: ignore[no-untyped-def]
        return e.case.problem.mesh.element_counts[0] == 24

    rows = _edit(rows, "P/17", large, ratio=0.91)
    rows = _edit(
        rows, "P/29", lambda e: large(e) and e.case.problem.loads[0].direction == "y", ratio=1.1
    )
    rows = _edit(
        rows, "P/29", lambda e: large(e) and e.case.problem.loads[0].direction == "z", ratio=0.3
    )
    result = selection_decision(rows)
    assert result["passing_seeds"] == [43] and not result["model_gate_passed"]
    assert result["selected_seed"] == 43


def test_primary_requires_zero_failures_and_strict_control_gain() -> None:
    first = screen_entries()[0].case.case_id

    def only(e):  # type: ignore[no-untyped-def]
        return e.case.case_id == first

    rows = _rows()
    for seed in (17, 29, 43):
        rows = _edit(rows, f"P/{seed}", only, failed=True)
        rows = _edit(rows, f"C/{seed}", only, failed=True)
    result = selection_decision(rows)
    assert result["passing_seeds"] == [17, 29, 43]
    assert result["selected_seed"] is None and not result["model_gate_passed"]
    rows = _rows()
    for seed in (17, 29, 43):
        rows = _edit(rows, f"C/{seed}", ratio=0.6)
    assert selection_decision(rows)["selected_seed"] is None
    for comparator in ("physics_heuristic", "nearest_neighbor"):
        equal = _edit(_rows(), comparator, ratio=0.6)
        assert selection_decision(equal)["passing_seeds"] == []


def test_matched_failure_and_non_specialist_y_limits() -> None:
    first = screen_entries()[0].case.case_id
    rows = _edit(_rows(), "P/17", lambda e: e.case.case_id == first, failed=True)
    assert 17 not in selection_decision(rows)["passing_seeds"]
    y = [
        e.case.case_id
        for e in screen_entries()
        if e.case.problem.loads[0].direction == "y" and policy_route(e.case, "P") != "specialist"
    ][:2]
    z = [e.case.case_id for e in screen_entries() if e.case.problem.loads[0].direction == "z"][:2]
    rows = _edit(_rows(), "P/17", lambda e: e.case.case_id in y, failed=True)
    rows = _edit(rows, "C/17", lambda e: e.case.case_id in z, failed=True)
    assert 17 not in selection_decision(rows)["passing_seeds"]


def test_pooled_large_y_quality_cells_remain_mandatory() -> None:
    cases = [
        e.case.case_id
        for e in screen_entries()
        if e.case.problem.mesh.element_counts == (24, 12, 6)
        and e.case.problem.loads[0].direction == "y"
        and e.case.problem.optimization.volume_fraction == 0.5351
    ][:2]
    rows = _rows()
    for seed in (29, 43):
        for method in ("P", "C"):
            rows = _edit(rows, f"{method}/{seed}", lambda e: e.case.case_id in cases, failed=True)
    result = selection_decision(rows)
    assert result["selected_seed"] == 17 and result["quality_cells"]["0.5351"] == 5
    assert not result["model_gate_passed"]


@pytest.mark.parametrize("change", ["missing_case", "missing_method", "quality", "ratio", "volume"])
def test_gate_rejects_incomplete_or_unpaid_or_bad_quality_measures(change):  # type: ignore[no-untyped-def]
    rows = _rows()
    if change == "missing_case":
        rows = rows[:-1]
    else:
        q = rows[0].queries[3]
        if change == "missing_method":
            updated = rows[0].queries[:-1]
        else:
            updates = (
                {"paired_time_ratio": 0.001}
                if change == "ratio"
                else {
                    "operational": q.operational.model_copy(
                        update={"final_compliance": 1.002}
                        if change == "quality"
                        else {"physical_volume_error": 0.006}
                    )
                }
            )
            updated = (*rows[0].queries[:3], q.model_copy(update=updates), *rows[0].queries[4:])
        rows = (rows[0].model_copy(update={"queries": updated}), *rows[1:])
    assert not selection_decision(rows)["model_gate_passed"]


def test_freeze_requires_complete_audit_and_unchanged_statistics(context, tmp_path):  # type: ignore[no-untyped-def]
    index = _complete_index(context)
    path = publish_freeze(tmp_path, index)
    freeze = B3Freeze.model_validate_json(path.read_bytes())
    assert freeze.selected_seed == 17 and len(freeze.context.training_index.outcomes) == 12
    assert freeze.screen_index_sha256 == screen_summary(index)["index_sha256"]
    for update in (
        {"resource_failed": True},
        {"audited_case_ids": ()},
        {"cumulative_seconds": screen.SCREEN_SECONDS + 1},
        {"peak_rss_bytes": screen.SCREEN_RSS_BYTES + 1},
    ):
        assert publish_freeze(tmp_path / "failed", index.model_copy(update=update)) is None
    for field, value in (
        ("selected_seed", 29),
        ("statistics", {"seed": 1}),
        ("screen_index_sha256", "0" * 64),
    ):
        with pytest.raises(ValueError, match="freeze"):
            B3Freeze.model_validate(
                freeze.model_copy(update={field: value}).model_dump(mode="json")
            )


def _case(context, entry, b3_record_factory):  # type: ignore[no-untyped-def]
    # Synthetic artifact IO state: no optimizer runs and no real label bytes.
    result = b3_record_factory(entry).result
    result = result.model_copy(
        update={
            "compliance": 1,
            "history": tuple(s.model_copy(update={"compliance": 1}) for s in result.history),
        }
    )
    state = TerminalWitness.from_result(result)
    metrics = BaselineMetrics(iterations=1, final_compliance=1, physical_volume_error=0)
    outcomes = tuple(
        QueryOutcome(
            method=m,
            seed=s,
            route=policy_route(entry.case, m),
            attempt=QueryAttempt(
                succeeded=True,
                timing=AttemptTiming(
                    refinement_seconds=1 if m == "uniform" else 0.6 if m == "P" else 0.8
                ),
                metrics=metrics,
                state=state,
            ),
        )
        for m, s in METHODS
    )
    return B3CaseRecord(
        context_sha256=context.sha256(),
        entry=entry,
        mandatory_uniform_compliance=1,
        outcomes=outcomes,
    )


def test_case_hash_role_and_immutable_prefix_boundaries(context, tmp_path, b3_record_factory):  # type: ignore[no-untyped-def]
    record = _case(context, screen_entries()[0], b3_record_factory)
    reference = write_case(tmp_path, record)
    assert read_case(tmp_path, context, reference) == record
    index = B3EvaluationIndex(
        context=context,
        context_sha256=context.sha256(),
        cases=(reference,),
        attempted_cases=1,
        cumulative_seconds=10,
        peak_rss_bytes=1,
    )
    write_screen_index(tmp_path, index)
    for update in (
        {"cases": ()},
        {"cumulative_seconds": 9},
        {"attempted_cases": 0},
        {"peak_rss_bytes": 0},
    ):
        with pytest.raises(ValueError):
            write_screen_index(tmp_path, index.model_copy(update=update))
    (tmp_path / reference.relative_path).write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        read_case(tmp_path, context, reference)
    final = next(e for e in B3Access(consumer="planning").case_entries() if e.role == "final_id")
    with pytest.raises((ValueError, PermissionError)):
        read_case(
            tmp_path,
            context,
            reference.model_copy(
                update={
                    "access": reference.access.model_copy(
                        update={"entry": final, "origins": (final.case,)}
                    )
                }
            ),
        )


def _run(root, context, **kwargs):  # type: ignore[no-untyped-def]
    return run_screen(
        root,
        root.parent / "synthetic-data",
        root.parent / "synthetic-fit",
        context,
        repository_root=Path(__file__).resolve().parents[1],
        **kwargs,
    )


def test_interruption_reruns_pending_case_and_preserves_completed_costs(
    context, tmp_path, monkeypatch, b3_record_factory
):  # type: ignore[no-untyped-def]
    now = [100.0]
    calls = []
    monkeypatch.setattr(screen, "perf_counter", lambda: now[0])
    monkeypatch.setattr(screen, "_peak_rss_bytes", lambda: 1)
    monkeypatch.setattr(screen, "read_selected_model", lambda *args: (None, None))
    monkeypatch.setattr(
        screen, "load_neighbors", lambda *args: {(3, 6, 12): None, (6, 12, 24): None}
    )

    def evaluate(entry, *args):  # type: ignore[no-untyped-def]
        calls.append(entry)
        now[0] += 5
        if len(calls) == 1:
            return _case(context, entry, b3_record_factory)
        raise KeyboardInterrupt

    monkeypatch.setattr(screen, "evaluate_screen_case", evaluate)
    with pytest.raises(KeyboardInterrupt):
        _run(tmp_path, context, startup_seconds=2)
    initial = read_screen_index(tmp_path, context)
    assert len(initial.cases) == 1 and initial.attempted_cases == 2
    assert initial.cumulative_seconds == 22 and initial.active_checkpoint_at is None
    with pytest.raises(KeyboardInterrupt):
        _run(tmp_path, context)
    resumed = read_screen_index(tmp_path, context)
    assert resumed.cases == initial.cases and resumed.attempted_cases == 3
    assert resumed.cumulative_seconds == 37
    assert calls == [screen_entries()[0], screen_entries()[1], screen_entries()[1]]
    monkeypatch.setattr(screen, "audit_case", lambda *args: None)
    audited = _run(tmp_path, context, audit_only=True)
    assert audited.audited_case_ids == (screen_entries()[0].case.case_id,)
    assert not audited.completeness_passed


@pytest.mark.parametrize("kind", ["time", "rss", "callback"])
def test_resource_stops_leave_pending_case_and_do_not_extend_budget(
    context, tmp_path, monkeypatch, kind
):  # type: ignore[no-untyped-def]
    now = [100.0]
    monkeypatch.setattr(screen, "perf_counter", lambda: now[0])
    monkeypatch.setattr(
        screen, "_peak_rss_bytes", lambda: screen.SCREEN_RSS_BYTES + 1 if kind == "rss" else 1
    )
    monkeypatch.setattr(screen, "read_selected_model", lambda *args: (None, None))
    monkeypatch.setattr(
        screen, "load_neighbors", lambda *args: {(3, 6, 12): None, (6, 12, 24): None}
    )

    def evaluate(entry, context, models, neighbors, checkpoint):  # type: ignore[no-untyped-def]
        assert kind == "callback"
        now[0] += screen.SCREEN_SECONDS
        checkpoint()
        pytest.fail("resource stop returned")

    monkeypatch.setattr(screen, "evaluate_screen_case", evaluate)
    result = _run(tmp_path, context, startup_seconds=screen.SCREEN_SECONDS if kind == "time" else 0)
    assert result.resource_failed and not result.cases and not result.completeness_passed
    assert result.active_checkpoint_at is None


def test_hard_crash_and_partial_setup_charges_cannot_disappear(context, tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(screen, "_peak_rss_bytes", lambda: 1)
    original = B3EvaluationIndex(
        context=context,
        context_sha256=context.sha256(),
        cumulative_seconds=5,
        setup_seconds=2,
        setup_active=True,
        active_checkpoint_at=datetime.now(UTC) - timedelta(seconds=60),
    )
    write_screen_index(tmp_path, original)
    result = _run(tmp_path, context, audit_only=True)
    assert result.cumulative_seconds >= 75 and result.setup_seconds >= 62
    assert not result.setup_active and result.active_checkpoint_at is None


def test_single_writer_and_planning_are_side_effect_free(context, tmp_path, monkeypatch, capsys):  # type: ignore[no-untyped-def]
    with (tmp_path / ".b3-screen-writer.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="another B3"):
            _run(tmp_path, context)
    monkeypatch.setattr(
        cli, "screening_preflight", lambda *args: (Path(__file__).resolve().parents[1], context)
    )
    root = tmp_path / "absent"
    assert (
        cli.main(
            [
                "--data-root",
                str(tmp_path / "data"),
                "--fit-root",
                str(tmp_path / "fit"),
                "--output-root",
                str(root),
            ]
        )
        == 0
    )
    assert not root.exists() and '"outcomes": 720' in capsys.readouterr().out


def test_incomplete_nn_population_fails_before_first_byte_read(context, tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    data = context.training_index.context.data_index
    broken = data.model_copy(update={"entries": data.entries[1:]})
    fake = context.model_copy(
        update={
            "training_index": context.training_index.model_copy(
                update={
                    "context": context.training_index.context.model_copy(
                        update={"data_index": broken}
                    )
                }
            )
        }
    )
    monkeypatch.setattr(
        screen, "_read_bytes", lambda *args: pytest.fail("opened incomplete NN labels")
    )
    with pytest.raises(ValueError, match="population"):
        screen.load_neighbors(tmp_path, fake, lambda: None)


def test_uniform_mismatch_is_terminal_and_preserves_the_failed_case(
    context, tmp_path, monkeypatch, b3_record_factory
):  # type: ignore[no-untyped-def]
    entry = screen_entries()[0]
    first = _case(context, entry, b3_record_factory).outcomes[0].model_dump(mode="json")
    first["attempt"]["metrics"]["final_compliance"] = 1.01
    first["attempt"]["state"]["result"]["compliance"] = 1.01
    first["attempt"]["state"]["result"]["history"][-1]["compliance"] = 1.01
    first["attempt"]["state"]["trace"][-1]["compliance"] = 1.01
    query = QueryOutcome.model_validate(first)
    calls = []

    def evaluate(case, method, *args):  # type: ignore[no-untyped-def]
        calls.append(method)
        return query

    monkeypatch.setattr(screen, "evaluate_query", evaluate)
    record = screen.evaluate_screen_case(entry, context, {}, None, lambda: None)
    assert record.fatal_code == "uniform_mismatch" and calls == ["uniform"]
    reference = write_case(tmp_path, record)
    index = B3EvaluationIndex(
        context=context,
        context_sha256=context.sha256(),
        cases=(reference,),
        attempted_cases=1,
        numerical_failed=True,
    )
    write_screen_index(tmp_path, index)
    assert not screen_summary(index)["b4_gate_passed"]
    with pytest.raises(ValueError, match="permanent failure"):
        _run(tmp_path, context)
    assert read_screen_index(tmp_path, context).cases == index.cases


def test_independent_audit_failure_is_durable(context, tmp_path, monkeypatch, b3_record_factory):  # type: ignore[no-untyped-def]
    reference = write_case(tmp_path, _case(context, screen_entries()[0], b3_record_factory))
    index = B3EvaluationIndex(
        context=context, context_sha256=context.sha256(), cases=(reference,), attempted_cases=1
    )
    write_screen_index(tmp_path, index)

    def audit(*args):  # type: ignore[no-untyped-def]
        raise ValueError("synthetic independent audit failure")

    monkeypatch.setattr(screen, "audit_case", audit)
    with pytest.raises(ValueError, match="independent audit failure"):
        _run(tmp_path, context, audit_only=True)
    failed = read_screen_index(tmp_path, context)
    assert failed.integrity_failed and not failed.completeness_passed
    assert failed.active_checkpoint_at is None and not failed.audited_case_ids
    with pytest.raises(ValueError, match="permanent failure"):
        _run(tmp_path, context, audit_only=True)


@pytest.mark.parametrize("change", ["missing_fit", "source", "resource", "failure"])
def test_screen_context_requires_the_exact_complete_fitting_receipt(context, change):  # type: ignore[no-untyped-def]
    fitting = context.training_index.model_dump(mode="json")
    if change == "missing_fit":
        fitting["outcomes"] = fitting["outcomes"][:-1]
        fitting["audited_fits"] = fitting["audited_fits"][:-1]
    elif change == "source":
        fitting["context"]["source"]["source_revision"] = "b" * 40
    elif change == "resource":
        fitting["cumulative_seconds"] = training.FIT_SECONDS + 1
    else:
        fitting["fitting_failed"] = True
    payload = context.model_dump(mode="json")
    payload["training_index"] = fitting
    with pytest.raises(ValueError):
        B3ScreenContext.model_validate(payload)


def test_failed_operational_fallback_stops_before_other_methods(
    context, monkeypatch, b3_record_factory
):  # type: ignore[no-untyped-def]
    entry = screen_entries()[0]
    uniform = _case(context, entry, b3_record_factory).outcomes[0]
    failed = QueryAttempt(
        succeeded=False,
        failure_code="quality_error",
        failure_type="SyntheticFailure",
        timing=AttemptTiming(refinement_seconds=2),
    )
    fallback_failed = QueryOutcome(
        method="physics_heuristic", seed=None, route="baseline", attempt=failed, fallback=failed
    )
    calls = []

    def evaluate(case, method, *args):  # type: ignore[no-untyped-def]
        calls.append(method)
        return uniform if method == "uniform" else fallback_failed

    monkeypatch.setattr(screen, "evaluate_query", evaluate)
    record = screen.evaluate_screen_case(entry, context, {}, None, lambda: None)
    assert record.fatal_code == "fallback_failure"
    assert calls == ["uniform", "physics_heuristic"]
    assert record.measures().queries[-1].operational is None
