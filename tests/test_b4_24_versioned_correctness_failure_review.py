"""Saved scalar identities, all failures, independent arithmetic and paid closure."""

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import eye

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_24_independent_audit as independent  # noqa: E402
import b4_24_resource_close as closure  # noqa: E402
import b4_24_versioned_correctness_failure_review as review  # noqa: E402


@pytest.mark.parametrize("main", [review.main, independent.main, closure.main])
def test_plan_reads_no_saved_artifact_or_creates_output(tmp_path, monkeypatch, capsys, main):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("unreleased artifact read"))
    output = tmp_path / "absent"
    assert main(["--probe-root", str(tmp_path / "prior"), "--output-root", str(output)]) == 0
    assert not output.exists()
    plan = json.loads(capsys.readouterr().out)
    assert plan == review.plan_payload() and len(plan["bindings"]) == 16
    assert plan["new_objective_gradient_calls"] == plan["new_timing_measurements"] == 0


def test_independent_geometry_weights_match_public_filter():
    for entry in review.selected_entries():
        mesh, _, _ = review._case_system(entry.case)
        filt = review.build_density_filter(mesh, entry.case.problem.optimization.filter_radius)
        actual = np.asarray(filt.matrix.T @ (1 / filt.row_sums)) / filt.row_sums.size
        assert np.allclose(independent.volume_weights(entry.case), actual, rtol=1e-14, atol=1e-16)


def test_changed_binding_stops_before_any_saved_payload_parse(monkeypatch):
    def reject(*args):
        raise ValueError("changed binding")

    monkeypatch.setattr(review, "safe_hash", reject)
    monkeypatch.setattr(review, "read", lambda *a: pytest.fail("payload parsed before bindings"))
    with pytest.raises(ValueError, match="changed binding"):
        review.check_inputs(Path("/unused"))


def test_fifth_thread_setting_is_required_before_release_read(monkeypatch):
    monkeypatch.setenv("NUMEXPR_NUM_THREADS", "2")
    monkeypatch.setattr(review, "prior_execution_release", lambda *a: pytest.fail("release read"))
    with pytest.raises(ValueError, match="five"):
        review.execution_release(Path("/unused"))


def toy_state(raw, offset, signed, anchor, weights, target=0.745):
    shifted = raw + offset
    design = np.clip(shifted, 0.0005, 1)
    free = (shifted > 0.0005) & (shifted < 1)
    gradient = np.where(free, signed - weights * signed[free].sum() / weights[free].sum(), 0)
    return {
        "design": design.tolist(),
        "physical": design.tolist(),
        "free": free.tolist(),
        "gradient": gradient.tolist(),
        "surrogate": 1 + float(signed @ (design - anchor)),
        "projection": {
            "offset": offset,
            "weighted_volume_residual": float(weights @ design) - target,
            "physical_volume_residual": float(design.mean()) - target,
            "kink_margin": float(np.minimum(abs(shifted - 0.0005), abs(shifted - 1)).min()),
        },
    }


def fixture(monkeypatch):
    # Deliberate synthetic saved residuals expose a non-clipping explanation too;
    # these are scalar records, not a fabricated certificate of solved roots.
    entries = [
        SimpleNamespace(
            case=SimpleNamespace(
                case_id=f"synthetic-{i}",
                problem=SimpleNamespace(
                    optimization=SimpleNamespace(
                        filter_radius=1, volume_fraction=0.745, minimum_density=0.0005
                    )
                ),
            )
        )
        for i in range(8)
    ]
    for module in (review, independent):
        monkeypatch.setattr(module, "selected_entries", lambda: entries)
    monkeypatch.setattr(review, "_case_system", lambda *a: (None, None, None))
    monkeypatch.setattr(
        review,
        "build_density_filter",
        lambda *a: SimpleNamespace(matrix=eye(2, format="csr"), row_sums=np.ones(2)),
    )
    monkeypatch.setattr(independent, "volume_weights", lambda *a: [0.5, 0.5])
    raw, signed, weights = np.array([0.5, 0.99]), np.array([1.0, 2.0]), np.array([0.5, 0.5])
    labels, rows, condition_results, direction_index = [], [], [True] * 3976, 0
    mapping = review.condition_map()
    for entry in entries:
        labels.append(
            {
                "case_id": entry.case.case_id,
                "design_gradient": signed.tolist(),
                "anchor": raw.tolist(),
                "intercept": 1.0,
            }
        )
        for state, spec in enumerate(review.state_specs()):
            row = {
                **toy_state(raw, 0.0, signed, raw, weights),
                "case_id": entry.case.case_id,
                "raw": raw.tolist(),
                "state": state,
                "spec": list(spec),
                "exact_gradient": [-0.5, 0.5],
                "timings": [{"repeat": r, "wall_seconds": r + 1.0} for r in range(3)],
                "differences": [],
            }
            if state in (0, 4):
                for name in ("sine", "cosine"):
                    d = review.direction_vector(2, name)
                    derivative = float(np.asarray(row["gradient"]) @ d)
                    for h in (1e-4, 2e-4):
                        plus_offset = 0.02 if direction_index < 35 else -h * float(d.mean())
                        minus_offset = (
                            0.02 + 2 * h * (d[0] - derivative)
                            if direction_index == 34
                            else h * float(d.mean())
                        )
                        sides = []
                        for sign, offset in ((1, plus_offset), (-1, minus_offset)):
                            side = toy_state(raw + sign * h * d, offset, signed, raw, weights)
                            physics = {
                                k: side[k] for k in ("design", "physical", "free", "projection")
                            }
                            sides.append({**side, "physics": physics, "exact": side["surrogate"]})
                        fd = (sides[0]["surrogate"] - sides[1]["surrogate"]) / (2 * h)
                        stable = all(s["free"] == row["free"] for s in sides)
                        error = abs(fd - derivative) / max(abs(fd), abs(derivative), 1e-8)
                        item = {
                            "direction": name,
                            "step": h,
                            "sides": sides,
                            "fd": fd,
                            "derivative": derivative,
                            "error": error,
                            "same_active_set": stable,
                            "exact_fd": fd,
                            "exact_derivative": derivative,
                        }
                        row["differences"].append(item)
                        condition_results[mapping[direction_index]["mask_condition"]] = stable
                        condition_results[mapping[direction_index]["fd_condition"]] = error <= 1e-4
                        direction_index += 1
            rows.append(row)
    panel = {"plan": review.prior_plan(), "labels": labels, "rows": rows}
    prior = {
        "numerical_conditions": 3976,
        "failed_numerical_conditions": 69,
        "condition_results": condition_results,
        "failed_condition_indices": [i for i, v in enumerate(condition_results) if not v],
    }
    closed = {
        "fit_proxy": {
            "total_prospective_seconds": 57546.0720687792,
            "limit_seconds": 7200,
            "cost_feasible": False,
        }
    }
    assert sum(not v for v in condition_results) == 69
    return panel, prior, closed


def test_complete_saved_review_preserves_all_failures_cost_steps_and_unknowns(monkeypatch):
    panel, prior, closed = fixture(monkeypatch)
    report = review.review(panel, prior, closed)
    assert report["review_acceptance_passed"] and report["scalar_conditions"] == 2104
    assert (
        len(report["rows"]) == 64 and report["mask_failures"] == 35 and report["fd_failures"] == 34
    )
    assert report["overlapping_mask_and_fd_failures"] == 34
    assert report["original_fit_proxy_unchanged"] == closed["fit_proxy"]
    assert not report["all_fd_failures_have_saved_clipping_explanation"]
    assert report["next_slice"] == review.EVIDENCE_NEXT
    assert not report["original_correctness_gate_passed"]
    assert not report["global_cause_or_gradient_failure_established"]
    assert report["prior_b4_19_actual_counts_and_gap_still_unknown"]
    result = independent.reconstruct(panel, prior, closed, report)
    assert result["passed"] and result["independent_scalar_conditions"] == 1728
    assert result["solver_calls"] == result["new_projection_calls"] == 0


def test_volume_balanced_clipping_identity_explains_finite_interval_gap():
    raw = np.array([0.00051, 0.3, 0.7, 0.99949])
    g, w = np.array([1.0, -2.0, 3.0, 4.0]), np.full(4, 0.25)
    d = review.direction_vector(4, "sine")
    h = 0.0002
    center = toy_state(raw, 0.0, g, raw, w, 0.5)
    sides = []
    for sign in (1, -1):
        # Synthetic scalar root construction for software verification only.
        x = raw + sign * h * d
        offset = 0.0
        for _ in range(4):
            y = x + offset
            f = (y > 0.0005) & (y < 1)
            offset += (0.5 - float(w @ np.clip(y, 0.0005, 1))) / w[f].sum()
        side = toy_state(x, offset, g, raw, w, 0.5)
        sides.append(
            {
                **side,
                "physics": {k: side[k] for k in ("design", "physical", "free")},
                "exact": side["surrogate"],
            }
        )
    item = {
        "step": h,
        "direction": "sine",
        "sides": sides,
        "derivative": float(np.asarray(center["gradient"]) @ d),
        "exact_derivative": 0.0,
    }
    result = review.decompose(center, item, g, w)
    assert result["mask_failed"] and result["fd_failed"]
    assert abs(result["volume_residual_contribution"]) < result["arithmetic_envelope"]
    assert result["clipping_accounts_for_gap_within_arithmetic_envelope"]
    assert abs(result["decomposition_residual"]) < result["arithmetic_envelope"]


@pytest.mark.parametrize("change", ["case", "state", "direction", "side", "first", "index", "nan"])
def test_missing_or_changed_saved_population_is_rejected(monkeypatch, change):
    panel, prior, closed = fixture(monkeypatch)
    if change == "case":
        panel["labels"].pop()
    elif change == "state":
        panel["rows"].reverse()
    elif change == "direction":
        panel["rows"][0]["differences"].reverse()
    elif change == "side":
        panel["rows"][0]["differences"][0]["sides"].pop()
    elif change == "first":
        panel["rows"][0]["timings"].pop(0)
    elif change == "index":
        prior["failed_condition_indices"][0] = 0
    else:
        panel["rows"][0]["raw"][0] = float("nan")
    with pytest.raises(ValueError):
        review.review(panel, prior, closed)


@pytest.mark.parametrize(
    "change", ["decomposition", "explanation", "cause", "gate", "cost", "unknown"]
)
def test_independent_audit_rejects_forged_diagnostic_or_boundary(monkeypatch, change):
    panel, prior, closed = fixture(monkeypatch)
    report = review.review(panel, prior, closed)
    if change == "decomposition":
        report["rows"][0]["clipping_departure_contribution"] += 1
    elif change == "explanation":
        report["rows"][0]["clipping_accounts_for_gap_within_arithmetic_envelope"] = True
    elif change == "cost":
        report["original_fit_proxy_unchanged"] = copy.deepcopy(closed["fit_proxy"])
        report["original_fit_proxy_unchanged"]["total_prospective_seconds"] = 1
    else:
        key = {
            "cause": "global_cause_or_gradient_failure_established",
            "gate": "original_correctness_gate_passed",
            "unknown": "prior_b4_19_actual_counts_and_gap_still_unknown",
        }[change]
        report[key] = not report[key]
    with pytest.raises(ValueError):
        independent.reconstruct(panel, prior, closed, report)


@pytest.mark.parametrize(
    "main,name",
    [
        (review.main, "review.json"),
        (independent.main, "independent_audit.json"),
        (closure.main, "resource_close.json"),
    ],
)
def test_exclusive_execution_refuses_existing_result_before_access(tmp_path, main, name):
    root = tmp_path / "b4-23-versioned-surrogate-feasibility"
    output = tmp_path / "b4-24-versioned-correctness-failure-review"
    output.mkdir()
    target = output / name
    target.write_bytes(b"retain")
    with pytest.raises(ValueError, match="overwrite"):
        main(["--probe-root", str(root), "--output-root", str(output), "--execute"])
    assert target.read_bytes() == b"retain"


def resource_fixture(tmp_path, monkeypatch):
    panel, prior, closed = fixture(monkeypatch)
    report = review.review(panel, prior, closed)
    report["charged_seconds"] = 10.1
    audit = independent.reconstruct(panel, prior, closed, report)
    audit["charged_seconds"] = 10.2
    commands = []
    for name in ("plan", "review", "independent"):
        for folder, suffix in (("profiles", ".time"), ("logs", ".log")):
            (tmp_path / folder).mkdir(exist_ok=True)
            (tmp_path / folder / (name + suffix)).write_bytes(b"synthetic\n")
        commands.append(
            {
                "name": name,
                "exit_code": 0,
                "profile": "profiles/" + name + ".time",
                "log": "logs/" + name + ".log",
                "profile_sha256": review.sha(b"synthetic\n"),
                "log_sha256": review.sha(b"synthetic\n"),
            }
        )
    monkeypatch.setattr(closure, "profile", lambda *a: (1.0, 100))
    monkeypatch.setattr(closure, "peak_rss", lambda: 100)
    return commands, report, audit


def test_full_reserve_and_failed_process_are_paid_without_gate_reclassification(
    tmp_path, monkeypatch
):
    commands, report, audit = resource_fixture(tmp_path, monkeypatch)
    result = closure.close_resources(tmp_path, commands, report, audit)
    assert result["charged_seconds"] == 82 and result["paid_reservation_seconds"] == 60
    assert result["original_charge_seconds_unchanged"] == 143.47
    commands[-1]["exit_code"] = 1
    result = closure.close_resources(tmp_path, commands, report, None)
    assert result["failed_attempts"] == 1 and not result["full_panel_review_complete"]
    assert result["charged_seconds"] == 82 and result["next_slice"] == review.EVIDENCE_NEXT


@pytest.mark.parametrize("change", ["hash", "escape", "duplicate", "cap", "rss", "gate"])
def test_native_resource_guards_reject_invalid_closure(tmp_path, monkeypatch, change):
    commands, report, audit = resource_fixture(tmp_path, monkeypatch)
    if change == "hash":
        commands[1]["log_sha256"] = "0" * 64
    elif change == "escape":
        commands[1]["profile"] = "../outside.time"
    elif change == "duplicate":
        commands.append(commands[1])
    elif change == "cap":
        monkeypatch.setattr(closure, "profile", lambda *a: (51.0, 100))
    elif change == "rss":
        monkeypatch.setattr(closure, "profile", lambda *a: (1.0, 1073741825))
    else:
        report["repaired_gate"] = True
        audit["review_sha256"] = review.sha(review.canonical(report))
    with pytest.raises(ValueError):
        closure.close_resources(tmp_path, commands, report, audit)
