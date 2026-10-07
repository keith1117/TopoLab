"""Original small public exact-oracle comparisons and independent tampering."""

import copy
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from topolab.active_set_evidence import IncompleteEvidence, certify_interval, check_interval
from topolab.active_set_trace import trace_interval

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from b4_28_active_set_numerical_evidence import interval_payload  # noqa: E402
from b4_28_common import (  # noqa: E402
    Journal,
    ci_passed,
    contract,
    entries,
    event_prefix,
    train_label,
)
from b4_28_independent_audit import independent_filter, prove_interval  # noqa: E402
from b4_28_resource_close import calculate  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "trace_fixture_oracle", SCRIPTS / "b4_27_fixture_oracle.py"
)
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


@pytest.mark.parametrize("h", [1e-4, 2e-4])
@pytest.mark.parametrize(
    "z,d,w,v",
    [
        ((0.2, 0.4, 0.7), (1.0, -0.5, 0.2), (0.2, 0.3, 0.5), 0.5),
        ((0.10002, 0.6, 0.8), (1.0, -0.5, -0.5), (1 / 3,) * 3, 0.5),
        ((0.10002, 0.10002, 0.8, 0.8), (1.0, 1.0, -1.0, -1.0), (0.25,) * 4, 0.45),
        ((0.8, 0.8, 0.2, 0.2), (1.0, 1.0, -1.0, -1.0), (0.25,) * 4, 0.69999),
        ((0.05, 0.5, 0.95), (-0.4, 0.7, 0.1), (0.25, 0.25, 0.5), 0.7),
        ((0.2, 0.6), (0.0, 0.0), (0.5, 0.5), 0.4),
    ],
)
def test_trace_equals_independent_exhaustive_complete_partitions(z, d, w, v, h):
    actual = trace_interval(z, d, w, v, 0.1, h)
    expected = oracle.enumerate_pieces(z, d, w, v, 0.1, h)
    assert [(p.start, p.end, p.partition) for p in actual] == [
        (a, b, p) for a, b, p, _, _ in expected
    ]
    signed = tuple(float(i - 2) for i in range(len(z)))
    proof = certify_interval(z, d, w, signed, v, 0.1, h, actual)
    delta = float(proof.signed_increment)
    derivative = sum(g * di for g, di in zip(proof.central_gradient, d, strict=True))
    checks = check_interval(
        proof,
        d,
        h,
        0.0,
        delta,
        derivative,
        legacy_mask_passed=not proof.transitions,
        legacy_fd_passed=not proof.transitions,
    )
    assert checks.passed
    retained = {
        "sides": [{"surrogate": delta}, {"surrogate": 0.0}],
        "surrogate_derivative": derivative,
        "same_active_set": not proof.transitions,
        "surrogate_error": 0.0 if not proof.transitions else 1.0,
    }
    independent = prove_interval(
        z, d, w, signed, v, 0.1, h, interval_payload(proof, checks), retained
    )
    assert independent["passed"] and independent["pieces"] == len(actual)


@pytest.mark.parametrize(
    "damage", ["gap", "partition", "slope", "offset", "transition", "integral", "classification"]
)
def test_independent_interval_proof_rejects_tampered_full_evidence(damage):
    z, d, w, signed, h = (
        (0.10002, 0.6, 0.8),
        (1.0, -0.5, -0.5),
        (1 / 3,) * 3,
        (-2.0, 1.0, 3.0),
        1e-4,
    )
    proof = certify_interval(z, d, w, signed, 0.5, 0.1, h, trace_interval(z, d, w, 0.5, 0.1, h))
    derivative = sum(g * di for g, di in zip(proof.central_gradient, d, strict=True))
    checks = check_interval(
        proof,
        d,
        h,
        0.0,
        float(proof.signed_increment),
        derivative,
        legacy_mask_passed=False,
        legacy_fd_passed=False,
    )
    payload = copy.deepcopy(interval_payload(proof, checks))
    retained = {
        "sides": [{"surrogate": float(proof.signed_increment)}, {"surrogate": 0.0}],
        "surrogate_derivative": derivative,
        "same_active_set": False,
        "surrogate_error": 1.0,
    }
    if damage == "gap":
        payload["pieces"][-1]["start"] = [0, 1]
    elif damage == "partition":
        payload["pieces"][0]["partition"][0] = 0
    elif damage == "slope":
        payload["pieces"][0]["value_slope"] = [5, 1]
    elif damage == "offset":
        payload["pieces"][0]["offset_start"] = [5, 1]
    elif damage == "transition":
        payload["transitions"] = []
    elif damage == "integral":
        payload["signed_increment"] = [5, 1]
    else:
        payload["checks"]["legacy_fd_passed"] = True
    with pytest.raises(ValueError):
        prove_interval(z, d, w, signed, 0.5, 0.1, h, payload, retained)


@pytest.mark.parametrize(
    "raw,d,w,v,m,h",
    [
        ((0.2, 0.4), (1.0, -1.0), (0.5, 0.5), 0.5, 0.1, 5e-5),
        ((0.2, float("nan")), (1.0, -1.0), (0.5, 0.5), 0.5, 0.1, 1e-4),
        ((0.2, 0.4), (1.0,), (0.5, 0.5), 0.5, 0.1, 1e-4),
        ((0.2, 0.4), (1.0, -1.0), (0.0, 1.0), 0.5, 0.1, 1e-4),
        ((0.0, 0.4), (1.0, -1.0), (0.5, 0.5), 0.5, 0.1, 1e-4),
        ((0.125, 0.875), (0.0, 0.0), (0.5, 0.5), 0.5, 0.125, 1e-4),
    ],
)
def test_trace_rejects_changed_or_undefined_boundaries(raw, d, w, v, m, h):
    with pytest.raises(IncompleteEvidence):
        trace_interval(raw, d, w, v, m, h)


def test_piece_resource_stop_does_not_extend_bound(monkeypatch):
    monkeypatch.setattr("topolab.active_set_trace.MAX_PIECES", 1)
    with pytest.raises(IncompleteEvidence, match="256-piece"):
        trace_interval((0.10002, 0.6, 0.8), (1.0, -0.5, -0.5), (1 / 3,) * 3, 0.5, 0.1, 1e-4)


def test_independent_filter_matches_original_public_geometry_without_candidate_call():
    from topolab.mesh import generate_structured_hex8
    from topolab.simp import build_density_filter

    mesh = generate_structured_hex8(3, 2, 2)
    matrix, sums, operator, weights = independent_filter(mesh, 0.65)
    original = build_density_filter(mesh, 0.65)
    assert np.array_equal(matrix.toarray(), original.matrix.toarray())
    assert np.array_equal(sums, original.row_sums)
    assert np.array_equal(weights, np.asarray(original.matrix.T @ (1 / original.row_sums)) / 12)
    assert np.max(abs(np.asarray(operator.sum(axis=1)).ravel() - 1)) < 1e-15


def test_durable_failed_numeric_call_retains_attempt_and_pending(tmp_path):
    path = tmp_path / "events.jsonl"
    journal = Journal(path, "a" * 40)
    with pytest.raises(RuntimeError, match="fixture failure"):
        journal.invoke(
            "fem",
            "public-case",
            {"physical_sha256": "b" * 64},
            lambda: (_ for _ in ()).throw(RuntimeError("fixture failure")),
            lambda x: x,
        )
    journal.close()
    _, counts, pending = event_prefix(path, "a" * 40)
    assert counts["fem"] == {"attempted": 1, "completed": 0}
    assert pending[0][0] == "fem"
    with pytest.raises(FileExistsError):
        Journal(path, "a" * 40)


def test_completed_call_is_counted_even_if_result_encoding_fails(tmp_path):
    path = tmp_path / "events.jsonl"
    journal = Journal(path, "a" * 40)
    with pytest.raises(ValueError, match="encoding"):
        journal.invoke(
            "fem",
            "public-case",
            {},
            lambda: 2.0,
            lambda _: (_ for _ in ()).throw(ValueError("encoding")),
        )
    journal.close()
    _, counts, pending = event_prefix(path, "a" * 40)
    assert counts["fem"] == {"attempted": 1, "completed": 1} and not pending


def test_abort_prefix_retains_incomplete_tail_without_calling_numerics(tmp_path):
    path = tmp_path / "events.jsonl"
    journal = Journal(path, "a" * 40)
    journal.close()
    with path.open("ab") as stream:
        stream.write(b'{"incomplete":')
    with pytest.raises(ValueError, match="durable lines"):
        event_prefix(path)
    events, counts, pending = event_prefix(path, allow_incomplete=True)
    assert len(events) == 1 and all(c["attempted"] == 0 for c in counts.values()) and not pending


def test_role_guard_rejects_before_any_payload_lookup(monkeypatch):
    import b4_15_offline_compliance_adjoint

    entry = entries()[0].model_copy(update={"role": "final_id"})
    monkeypatch.setattr(
        b4_15_offline_compliance_adjoint,
        "train_label",
        lambda *_: pytest.fail("payload lookup reached"),
    )
    with pytest.raises(ValueError, match="before artifact"):
        train_label(Path("/unopened"), object(), entry)
    assert contract()["population"]["legacy_predicates"] == 3976


def test_exact_head_ci_requires_real_pr_smoke_and_no_pending_or_stale_checks():
    head = "a" * 40
    checks = [
        {"name": name, "head_sha": head, "status": "completed", "conclusion": "success"}
        for name in ("quality", "frontend", "clean-linux-smoke")
    ]
    assert ci_passed(checks, head, True)
    for key, value in [("head_sha", "b" * 40), ("status", "queued"), ("conclusion", "skipped")]:
        changed = copy.deepcopy(checks)
        changed[-1][key] = value
        assert not ci_passed(changed, head, True)
    assert not ci_passed(checks[:2], head, False)


def test_all_failed_native_invocations_and_reserve_are_charged_unknown_rss_fails():
    profile = {"wall_seconds": 5.0, "user_seconds": 2.0, "system_seconds": 1.0, "rss_bytes": 100}
    commands = [
        {"name": name, "native": profile, "observed_outer_wall_seconds": 6.0}
        for name in ("plan", "producer", "independent")
    ]
    assert calculate(commands, None, None)["total_charged_seconds"] == 90.0
    commands[1]["native"] = None
    result = calculate(commands, None, None)
    assert result["total_charged_seconds"] == 91.0 and not result["numerical_budget_passed"]


def test_failed_plan_has_no_numeric_work_but_pays_entire_reserve():
    result = calculate(
        [{"name": "plan", "native": None, "observed_outer_wall_seconds": 3.0}], None, None
    )
    assert result["total_charged_seconds"] == 60
    assert result["stage_charges"] == {} and not result["native_profiles_complete"]
    assert not result["numerical_budget_passed"]


@pytest.mark.parametrize(
    "wall,rss,passes", [(590, 100, True), (591, 100, False), (1, 1073741825, False)]
)
def test_native_time_and_memory_caps_cannot_be_relaxed(wall, rss, passes):
    profile = {"wall_seconds": wall, "user_seconds": 1, "system_seconds": 1, "rss_bytes": rss}
    commands = [
        {"name": name, "native": profile, "observed_outer_wall_seconds": wall}
        for name in ("plan", "producer", "independent")
    ]
    result = calculate(commands, None, None)
    assert result["numerical_budget_passed"] is passes
    assert result["total_charged_seconds"] == 60 + 2 * (wall + 10)


def test_default_plan_reaches_neither_release_nor_payload_and_creates_no_output(
    tmp_path, monkeypatch, capsys
):
    import b4_28_native_execution

    monkeypatch.setattr(
        b4_28_native_execution, "execute", lambda *_: pytest.fail("production execution reached")
    )
    assert (
        b4_28_native_execution.main(
            [
                "--legacy-root",
                str(tmp_path / "unopened-legacy"),
                "--data-root",
                str(tmp_path / "unopened-data"),
                "--output-root",
                str(tmp_path / "uncreated-output"),
            ]
        )
        == 0
    )
    assert '"final_access":false' in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []
