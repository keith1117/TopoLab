"""Complete synthetic arithmetic, independent weights, tampering and paid closure."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_21_correctness_failure_review as review  # noqa: E402
import b4_21_independent_audit as independent  # noqa: E402
import b4_21_resource_close as closure  # noqa: E402


def fixture():
    cases = []
    for entry in review.selected_entries():
        mesh, _, _ = review._case_system(entry.case)
        filt = review.build_density_filter(mesh, entry.case.problem.optimization.filter_radius)
        n = filt.row_sums.size
        weights = np.asarray(filt.matrix.T @ (1 / filt.row_sums)) / n
        g = -100 * weights + 1e-6 * review.direction_vector(n, "sine")
        rows = []
        for state in ("interior", "clipped"):
            free = np.ones(n, dtype=bool)
            if state == "clipped":
                free[::3] = False
            gradient = np.where(free, g - weights * g[free].sum() / weights[free].sum(), 0)
            differences = []
            for direction in ("sine", "cosine"):
                derivative = float(gradient @ review.direction_vector(n, direction))
                for h in (1e-4, 2e-4):
                    multiplier = (
                        1.0001253
                        if not cases and state == "clipped" and direction == "sine" and h == 1e-4
                        else 1
                    )
                    values = [2 + h * derivative * multiplier, 2 - h * derivative * multiplier]
                    fd = (values[0] - values[1]) / (2 * h)
                    differences.append(
                        {
                            "direction": direction,
                            "step": h,
                            "values": values,
                            "free": [free.tolist(), free.tolist()],
                            "fd": fd,
                            "derivative": derivative,
                            "error": abs(fd - derivative) / max(abs(fd), abs(derivative), 1e-8),
                        }
                    )
            rows.append(
                {
                    "state": state,
                    "free": free.tolist(),
                    "design": [0.5] * n,
                    "gradient": gradient.tolist(),
                    "differences": differences,
                }
            )
        cases.append(
            {
                "case_id": entry.case.case_id,
                "design_gradient": g.tolist(),
                "anchor": [0.4] * n,
                "intercept": 1.0,
                "rows": rows,
            }
        )
    return {"plan": review.prior_plan(), "cases": cases}, {
        "numerical_conditions": 984,
        "failed_numerical_conditions": 1,
    }


def test_default_plan_has_no_reads_or_output(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("artifact read"))
    output = tmp_path / "absent"
    assert review.main(["--probe-root", str(tmp_path / "prior"), "--output-root", str(output)]) == 0
    assert not output.exists()
    assert json.loads(capsys.readouterr().out) == review.plan_payload()


def test_complete_review_preserves_failed_gate_unknowns_and_both_steps():
    probe, prior = fixture()
    report = review.review(probe, prior)
    assert report["review_acceptance_passed"] and len(report["rows"]) == 64
    assert report["next_slice"] == review.NUMERICAL_NEXT
    assert not report["original_correctness_gate_passed"] and not report["cause_established"]
    assert report["side_offsets_and_volume_residuals"] is None
    assert {r["step"] for r in report["rows"]} == {1e-4, 2e-4}
    assert sum(r["failed"] for r in report["rows"]) == 1
    audit = independent.reconstruct(probe, prior, report)
    assert audit["passed"] and audit["solver_calls"] == audit["new_projection_calls"] == 0


@pytest.mark.parametrize(
    "change", ["case", "fixture", "difference", "duplicate", "arithmetic", "nan", "counter"]
)
def test_incomplete_or_modified_population_rejected(change):
    probe, prior = fixture()
    row = probe["cases"][0]["rows"][0]
    if change == "case":
        probe["cases"].pop()
    elif change == "fixture":
        probe["cases"][0]["rows"].reverse()
    elif change == "difference":
        row["differences"].pop()
    elif change == "duplicate":
        row["differences"][1] = copy.deepcopy(row["differences"][0])
    elif change == "arithmetic":
        row["differences"][0]["fd"] += 1
    elif change == "nan":
        row["differences"][0]["values"][0] = float("nan")
    else:
        prior["failed_numerical_conditions"] = 0
    with pytest.raises(ValueError):
        review.review(probe, prior)


@pytest.mark.parametrize("change", ["gradient", "mask"])
def test_review_acceptance_can_fail_without_reclassifying_original(change):
    probe, prior = fixture()
    row = probe["cases"][0]["rows"][0]
    if change == "gradient":
        # A saved gradient can disagree with the implicit cotangent even when
        # all original directional scalars are kept. Use an untested null shift.
        g = np.asarray(probe["cases"][0]["design_gradient"])
        g[0] += 0.1
        probe["cases"][0]["design_gradient"] = g.tolist()
    else:
        row["differences"][0]["free"][0][0] = False
    report = review.review(probe, prior)
    assert not report["review_acceptance_passed"]
    assert report["next_slice"] == review.REVIEW_NEXT
    assert not report["original_correctness_gate_passed"]


@pytest.mark.parametrize("field", ["envelope", "gate", "cause", "next", "unknown"])
def test_independent_auditor_rejects_changed_conclusions(field):
    probe, prior = fixture()
    report = review.review(probe, prior)
    if field == "envelope":
        report["rows"][0]["root_tolerance_envelope"] += 1
    else:
        key, value = {
            "gate": ("original_correctness_gate_passed", True),
            "cause": ("cause_established", True),
            "next": ("next_slice", "B5"),
            "unknown": ("side_offsets_and_volume_residuals", [0, 0]),
        }[field]
        report[key] = value
    with pytest.raises(ValueError):
        independent.reconstruct(probe, prior, report)


@pytest.mark.parametrize(
    "main,name",
    [
        (review.main, "review.json"),
        (independent.main, "independent_audit.json"),
        (closure.main, "resource_close.json"),
    ],
)
def test_existing_stage_refuses_overwrite_before_access(tmp_path, monkeypatch, main, name):
    root, output = (
        tmp_path / "b4-20-surrogate-correctness",
        tmp_path / "b4-21-correctness-failure-review",
    )
    output.mkdir()
    target = output / name
    target.write_bytes(b"preserved\n")
    monkeypatch.setattr(review, "check_inputs", lambda *a: pytest.fail("input read"))
    with pytest.raises(ValueError, match="overwrite"):
        main(["--probe-root", str(root), "--output-root", str(output), "--execute"])
    assert target.read_bytes() == b"preserved\n"


def resource_fixture(tmp_path, monkeypatch):
    probe, prior = fixture()
    report = review.review(probe, prior)
    report.update(charged_seconds=10.1)
    audit = independent.reconstruct(probe, prior, report)
    audit.update(charged_seconds=10.2)
    commands = []
    for name in ("plan", "review", "independent"):
        for folder, suffix in (("profiles", ".time"), ("logs", ".log")):
            directory = tmp_path / folder
            directory.mkdir(exist_ok=True)
            (directory / (name + suffix)).write_bytes(b"synthetic\n")
        commands.append(
            {
                "name": name,
                "exit_code": 0,
                "profile": "profiles/" + name + ".time",
                "profile_sha256": review.sha(b"synthetic\n"),
                "log": "logs/" + name + ".log",
                "log_sha256": review.sha(b"synthetic\n"),
            }
        )
    monkeypatch.setattr(closure, "profile", lambda *a: (1, 100))
    return commands, report, audit


def test_full_reservation_and_failed_stage_charge_are_retained(tmp_path, monkeypatch):
    commands, report, audit = resource_fixture(tmp_path, monkeypatch)
    result = closure.close_resources(tmp_path, commands, report, audit)
    assert result["charged_seconds"] == 82 and result["paid_reservation_seconds"] == 60
    commands[-1]["exit_code"] = 1
    result = closure.close_resources(tmp_path, commands, report, None)
    assert result["failed_attempts"] == 1 and not result["full_panel_review_complete"]
    assert result["charged_seconds"] == 82 and result["next_slice"] == review.REVIEW_NEXT


@pytest.mark.parametrize("change", ["hash", "duplicate", "escape", "cap", "rss", "gate"])
def test_resource_guard_rejects_unaccounted_or_invalid_closure(tmp_path, monkeypatch, change):
    commands, report, audit = resource_fixture(tmp_path, monkeypatch)
    if change == "hash":
        commands[1]["profile_sha256"] = "0" * 64
    elif change == "duplicate":
        commands.append(commands[1])
    elif change == "escape":
        commands[1]["profile"] = "../outside.time"
    elif change == "cap":
        monkeypatch.setattr(closure, "profile", lambda *a: (61, 100))
    elif change == "rss":
        monkeypatch.setattr(closure, "profile", lambda *a: (1, 1073741825))
    else:
        report["repaired_gate"] = True
        audit["review_sha256"] = review.sha(review.canonical(report))
    with pytest.raises(ValueError):
        closure.close_resources(tmp_path, commands, report, audit)
