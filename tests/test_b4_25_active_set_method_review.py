"""Complete scalar/failure preservation and bounded read-only execution tests."""

import ast
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_25_active_set_method_review as candidate  # noqa: E402
from b4_25_independent_audit import audit  # noqa: E402


def fixture():
    rows = []
    for case in range(8):
        for state in (0, 4):
            for d, direction in enumerate(("sine", "cosine")):
                for s, step in enumerate((1e-4, 2e-4)):
                    index = len(rows)
                    gap = 0.1 if index < 34 else 0.0
                    fd = 1.0 + gap
                    discrepancy = fd - 1.0
                    position = case * 497 + (65 if state == 0 else 297) + 34 * (2 * d + s)
                    rows.append(
                        {
                            "case_id": candidate.CASE_IDS[case],
                            "state": state,
                            "direction": direction,
                            "step": step,
                            "mask_condition": position,
                            "fd_condition": position + 1,
                            "fd": fd,
                            "derivative": 1.0,
                            "error": abs(discrepancy) / fd,
                            "fd_failed": index < 34,
                            "mask_failed": index < 35,
                            "exact_fd": 0.9,
                            "exact_derivative": 0.9,
                            "signed_discrepancy": discrepancy,
                            "projected_chord_derivative": fd,
                            "central_tangent_derivative": 1.0,
                            "clipping_departure_contribution": discrepancy,
                            "volume_residual_contribution": 0.0,
                            "saved_value_roundoff_contribution": 0.0,
                            "saved_gradient_roundoff_contribution": 0.0,
                            "decomposition_residual": 0.0,
                            "arithmetic_envelope": 1e-9,
                            "clipping_accounts_for_gap_within_arithmetic_envelope": True,
                            "changed_plus_components": int(index < 35),
                            "changed_minus_components": 0,
                            "offsets": [0.0, 0.0, 0.0],
                            "weighted_residuals": [0.0, 0.0, 0.0],
                        }
                    )
    proxy = {
        "maximum_seconds_per_scale": {"small": 0.16, "large": 0.005},
        "maximum_setup_seconds_per_scale": {"small": 0.2, "large": 1.2},
        "additional_surrogate_seconds": 52125.0,
        "full_population_preparation_seconds": 666.0,
        "total_prospective_seconds": 57512.584341,
        "limit_seconds": 7200,
        "cost_feasible": False,
        "planning_proxy_only": True,
        "full_fit_memory_feasibility_pending": True,
        "population_retained_array_bytes_estimate": 127992304,
        "original_b4_15_proxy_seconds_unchanged": 60339.39413004646,
        "original_b4_17_proxy_seconds_unchanged": 58257.4579573346,
    }
    return {"rows": rows, "original_fit_proxy_unchanged": proxy}


def test_default_plan_reads_no_evidence_or_source_and_creates_no_output(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("artifact read"))
    monkeypatch.setattr(Path, "open", lambda *a, **k: pytest.fail("file open"))
    output = tmp_path / "absent"
    assert (
        candidate.main(["--review-root", str(tmp_path / "prior"), "--output-root", str(output)])
        == 0
    )
    plan = json.loads(capsys.readouterr().out)
    assert plan == candidate.plan_payload() and not output.exists()
    assert len(plan["bindings"]) == 15 and plan["max_seconds"] == 180
    assert plan["original_fd_tolerance"] == 1e-4 and plan["original_fd_floor"] == 1e-8
    assert plan["fit_epochs"] == 200 and plan["fit_population"] == [432, 76]
    assert plan["historical_whole_slice_peak_rss_bytes"] is None


def test_complete_population_original_failures_and_independent_cost(monkeypatch):
    prior = fixture()
    before = candidate.canonical(prior)
    report = candidate.review(prior)
    for name in ("review", "cost_review", "row_identities"):
        monkeypatch.setattr(candidate, name, lambda *a: pytest.fail("candidate computation called"))
    result = audit(prior, report)
    assert result["passed"] and result["scalar_conditions"] == 448
    assert result["independent_scalar_comparisons"] > 1500
    assert report["mask_failures"] == 35 and report["fd_failures"] == 34
    assert report["overlapping_mask_and_fd_failures"] == 34
    assert len(report["failed_condition_indices"]) == 69
    assert all(g["rows"] == 16 for g in report["groups"].values())
    assert report["review_acceptance_passed"] and report["next_slice"] == candidate.METHOD_NEXT
    assert report["cost_diagnostics"]["original_maximum_seconds"] > 7200
    assert report["cost_diagnostics"]["zero_small_recorded_large_max_seconds"] < 7200
    assert not report["original_correctness_gate_passed"] and not report["repaired_gate"]
    assert before == candidate.canonical(prior)


def test_retained_row_schema_matches_actual_frozen_writer():
    source = (
        Path(__file__).resolve().parents[1]
        / "scripts/b4_24_versioned_correctness_failure_review.py"
    )
    tree = ast.parse(source.read_text())
    keys = set()
    for function in tree.body:
        if isinstance(function, ast.FunctionDef) and function.name in (
            "decompose",
            "condition_map",
        ):
            for node in ast.walk(function):
                if isinstance(node, ast.Dict):
                    keys.update(
                        k.value
                        for k in node.keys
                        if isinstance(k, ast.Constant) and isinstance(k.value, str)
                    )
    assert set(fixture()["rows"][0]) == keys


def test_case_order_matches_actual_public_metadata_producer():
    from b4_15_offline_compliance_adjoint import selected_entries

    entries = selected_entries()
    assert tuple(e.case.case_id for e in entries) == candidate.CASE_IDS
    assert candidate.CASE_IDS != tuple(sorted(candidate.CASE_IDS))
    assert [
        (e.case.problem.mesh.element_counts[0], e.case.problem.loads[0].direction) for e in entries
    ] == [(12, "y")] * 2 + [(12, "z")] * 2 + [(24, "y")] * 2 + [(24, "z")] * 2


@pytest.mark.parametrize(
    "change", ["drop", "reorder", "case", "state", "step", "condition", "changed_count", "nan"]
)
def test_complete_order_counts_and_finite_records_are_required(change):
    prior = fixture()
    if change == "drop":
        prior["rows"].pop()
    elif change == "reorder":
        prior["rows"][0], prior["rows"][1] = prior["rows"][1], prior["rows"][0]
    else:
        field, value = {
            "case": ("case_id", "not-registered"),
            "state": ("state", 8),
            "step": ("step", 1e-5),
            "condition": ("mask_condition", 0),
            "changed_count": ("changed_plus_components", True),
            "nan": ("fd", float("nan")),
        }[change]
        prior["rows"][0][field] = value
    with pytest.raises(ValueError):
        candidate.review(prior)


@pytest.mark.parametrize(
    "field,value",
    [
        ("next_slice", candidate.EVIDENCE_NEXT),
        ("review_acceptance_passed", False),
        ("repaired_gate", True),
        ("full_fit_memory_feasibility_pending", False),
        ("historical_whole_slice_peak_rss_bytes", 1),
        ("mask_failures", 34),
    ],
)
def test_independent_audit_rejects_forged_acceptance_unknowns_and_failures(field, value):
    prior = fixture()
    report = candidate.review(prior)
    report[field] = value
    with pytest.raises(ValueError, match="independent"):
        audit(prior, report)


@pytest.mark.parametrize("field", ["fd", "exact_fd", "offsets", "weighted_residuals"])
def test_independent_audit_preserves_all_original_scalar_fields(field):
    prior = fixture()
    report = candidate.review(prior)
    report["retained_rows"][0][field] = (
        0.0 if field not in ("offsets", "weighted_residuals") else [1.0, 0.0, 0.0]
    )
    with pytest.raises(ValueError, match="byte-identical"):
        audit(prior, report)


def test_incompatible_saved_clipping_preserves_failure_and_selects_evidence_review():
    prior = fixture()
    row = prior["rows"][0]
    row["clipping_departure_contribution"] -= 0.01
    row["saved_value_roundoff_contribution"] = 0.01
    row["clipping_accounts_for_gap_within_arithmetic_envelope"] = False
    report = candidate.review(prior)
    assert report["review_acceptance_passed"] and report["next_slice"] == candidate.EVIDENCE_NEXT
    assert audit(prior, report)["passed"]
    assert report["fd_failures"] == 34 and not report["repaired_gate"]


def test_failed_new_scalar_check_is_retained_and_independently_reconstructed():
    prior = fixture()
    prior["rows"][0]["decomposition_residual"] = 1.0
    report = candidate.review(prior)
    assert report["failed_scalar_conditions"] == 1 and not report["review_acceptance_passed"]
    assert audit(prior, report)["passed"] and report["next_slice"] == candidate.EVIDENCE_NEXT


@pytest.mark.parametrize(
    "field,value",
    [
        ("cost_feasible", True),
        ("limit_seconds", 72000),
        ("additional_surrogate_seconds", 285.0),
        ("total_prospective_seconds", 5000.0),
        ("full_fit_memory_feasibility_pending", False),
    ],
)
def test_first_inclusive_complete_original_cost_is_not_replaced(field, value):
    prior = fixture()
    prior["original_fit_proxy_unchanged"][field] = value
    with pytest.raises(ValueError, match="cost"):
        candidate.review(prior)


def resource_fixture(tmp_path, wall=1.0, rss=1024):
    report = candidate.review(fixture())
    report.update(charged_seconds=10.0, peak_rss_bytes=rss)
    result = audit(fixture(), report)
    result.update(charged_seconds=10.0, peak_rss_bytes=rss)
    (tmp_path / "profiles").mkdir()
    (tmp_path / "logs").mkdir()
    commands = []
    for name in ("plan", "review", "independent"):
        profile = f"profiles/{name}.time"
        log = f"logs/{name}.log"
        (tmp_path / profile).write_text(
            f"{wall} real 0.1 user 0.1 sys\n{rss} maximum resident set size\n"
        )
        (tmp_path / log).write_bytes(b"test\n")
        commands.append(
            {
                "name": name,
                "profile": profile,
                "log": log,
                "exit_code": 0,
                "profile_sha256": candidate.sha((tmp_path / profile).read_bytes()),
                "log_sha256": candidate.sha((tmp_path / log).read_bytes()),
            }
        )
    return commands, report, result


def test_complete_native_cost_counts_each_stage_and_full_reserve(tmp_path):
    commands, report, result = resource_fixture(tmp_path, wall=50.0, rss=1073741824)
    closed = candidate.close_resources(tmp_path, commands, report, result)
    assert closed["charged_seconds"] == 180 and closed["paid_reservation_seconds"] == 60
    assert closed["review_acceptance_passed"] and closed["stage_charges"] == {
        "review": 60,
        "independent": 60,
    }
    assert closed["prospective_accounting_diagnostic"][
        "with_b4_24_and_b4_25_seconds"
    ] == pytest.approx(57512.584341 + 200.98 + 180)
    assert closed["historical_whole_slice_peak_rss_bytes"] is None


def test_failed_review_is_charged_without_unexecuted_audit_or_metrics(tmp_path):
    commands, _, _ = resource_fixture(tmp_path)
    commands = commands[:2]
    commands[1]["exit_code"] = 1
    closed = candidate.close_resources(tmp_path, commands, None, None)
    assert closed["charged_seconds"] == 71 and closed["failed_processes"] == 1
    assert not closed["full_review_complete"] and not closed["review_acceptance_passed"]
    assert closed["prospective_accounting_diagnostic"] is None
    assert closed["next_slice"] == candidate.EVIDENCE_NEXT


@pytest.mark.parametrize(
    "change", ["retry", "log_escape", "profile_hash", "missing_rss", "memory", "time"]
)
def test_native_limits_hashes_containment_and_no_retry(change, tmp_path):
    commands, report, result = resource_fixture(
        tmp_path,
        wall=50.01 if change == "time" else 1.0,
        rss=1073741825 if change == "memory" else 1024,
    )
    if change == "retry":
        commands.append(copy.deepcopy(commands[1]))
    elif change == "log_escape":
        commands[1]["log"] = "../outside.log"
    elif change == "profile_hash":
        commands[1]["profile_sha256"] = "0" * 64
    elif change == "missing_rss":
        path = tmp_path / commands[1]["profile"]
        path.write_text("1 real .1 user .1 sys\n")
        commands[1]["profile_sha256"] = candidate.sha(path.read_bytes())
    with pytest.raises(ValueError):
        candidate.close_resources(tmp_path, commands, report, result)


def test_execute_refuses_existing_output_before_source_or_evidence_read(tmp_path, monkeypatch):
    root = tmp_path / "b4-24-registered-continuation-v3"
    output = tmp_path / "b4-25-active-set-method-review"
    output.mkdir()
    (output / "review.json").write_text("preserved")
    monkeypatch.setattr(candidate, "execution_release", lambda *a: pytest.fail("source read"))
    with pytest.raises(ValueError, match="overwrite"):
        candidate.main(
            [
                "--review-root",
                str(root),
                "--output-root",
                str(output),
                "--mode",
                "review",
                "--execute",
            ]
        )
    assert (output / "review.json").read_text() == "preserved"


def test_canonical_hash_reader_rejects_escape_and_noncanonical_data(tmp_path):
    (tmp_path / "record.json").write_bytes(candidate.canonical({"ok": True}))
    digest = candidate.sha((tmp_path / "record.json").read_bytes())
    assert candidate.read(tmp_path, "record.json", digest) == {"ok": True}
    with pytest.raises(ValueError, match="contained"):
        candidate.safe_hash(tmp_path, "../record.json", digest)
    (tmp_path / "record.json").write_text('{"ok": true}\n')
    with pytest.raises(ValueError, match="canonical"):
        candidate.read(tmp_path, "record.json")


def metadata_fixture():
    prior = fixture()
    plan = {"version": "topolab.b4_24.registered-continuation.v3"}
    prior.update(
        plan=plan,
        review_acceptance_passed=True,
        scalar_conditions=2104,
        failed_scalar_conditions=0,
        original_correctness_gate_passed=False,
        original_feasibility_gate_passed=False,
        retained_measurements=216,
        fits=0,
        final_access=False,
        repaired_gate=False,
        old_fresh_sealed=True,
    )
    ci = {
        "passed": True,
        "head": "frozen-head",
        "checks": [
            {
                "name": name,
                "head_sha": "frozen-head",
                "status": "completed",
                "conclusion": "success",
            }
            for name in ("quality", "frontend", "clean-linux-smoke")
        ],
    }
    commands = {
        name: {"name": name, "exit_code": 0}
        for name in ("plan", "review", "independent", "closure", "verification")
    }
    bound = {
        "review.json": prior,
        "independent_audit.json": {
            "passed": True,
            "independent_scalar_conditions": 1728,
            "review_sha256": candidate.BINDINGS["review.json"],
        },
        "resource_close.json": {
            "closed": True,
            "review_acceptance_passed": True,
            "charged_seconds": 200.98,
            "historical_resource_proof_complete": False,
            "whole_slice_peak_rss_bytes": None,
            "whole_slice_memory_compliance": None,
            "historical_time_charge_seconds": 76.19,
            "historical_reserved_use_seconds": 50.53,
            "historical_failed_native_processes": 2,
            "continuation_failed_processes": 0,
            "next_slice": "B4.25 bounded active-set objective-method review",
        },
        "resource_verification.json": {"passed": True},
        "audit_receipts/postexit_reservation.json": {
            "passed": True,
            "historical_resource_proof_complete": False,
            "whole_slice_peak_rss_bytes": None,
            "new_reserved_use_seconds": 42.49,
            "continuation_peak_rss_bytes": 415268864,
        },
        "audit_receipts/plan.json": plan,
        "audit_receipts/production_release.json": {
            "all_applicable_ci_passed_before_merge": True,
            "same_tree_as_tested_head": True,
            "source_sha256": {"scripts/original.py": "a" * 64},
        },
        "audit_receipts/evidence_release.json": {
            "all_applicable_ci_passed_before_merge": True,
            "same_tree_as_tested_head": True,
            "publication_complete": True,
        },
        "audit_receipts/execution_commands.json": [
            commands[n] for n in ("plan", "review", "independent")
        ],
        **{f"audit_receipts/{n}_command.json": commands[n] for n in ("closure", "verification")},
        **{
            f"audit_receipts/{s}_{n}_ci.json": copy.deepcopy(ci)
            for s in ("source", "evidence")
            for n in ("final_head", "main")
        },
    }
    assert set(bound) == set(candidate.BINDINGS)
    return bound


@pytest.mark.parametrize(
    "field,value",
    [
        ("historical_resource_proof_complete", True),
        ("whole_slice_peak_rss_bytes", 415268864),
        ("whole_slice_memory_compliance", True),
        ("historical_time_charge_seconds", 0),
        ("historical_reserved_use_seconds", 0),
        ("historical_failed_native_processes", 0),
        ("charged_seconds", 76.19),
        ("review_acceptance_passed", False),
    ],
)
def test_prior_scoped_memory_unknowns_and_all_charges_cannot_be_imputed(
    field, value, tmp_path, monkeypatch
):
    bound = metadata_fixture()
    bound["resource_close.json"][field] = value
    monkeypatch.setattr(candidate, "read", lambda root, name, expected=None: bound[name])
    with pytest.raises(ValueError, match="historical unknowns"):
        candidate.check_inputs(tmp_path)


def test_input_guard_reads_only_frozen_compact_files_and_original_source_hashes(
    tmp_path, monkeypatch
):
    bound = metadata_fixture()
    opened, hashed, profiled = [], [], []

    def reader(root, name, expected=None):
        opened.append(name)
        assert expected == candidate.BINDINGS[name]
        return bound[name]

    monkeypatch.setattr(candidate, "read", reader)
    monkeypatch.setattr(candidate, "safe_hash", lambda root, name, expected: hashed.append(name))
    monkeypatch.setattr(
        candidate,
        "check_command",
        lambda root, command: profiled.append(command["name"]) or {"rss_bytes": 415268864},
    )
    assert candidate.check_inputs(tmp_path) == bound
    assert set(opened) == set(candidate.BINDINGS) and hashed == ["scripts/original.py"]
    assert profiled == ["plan", "review", "independent", "closure", "verification"]


def test_input_guard_accepts_original_binary_charge_without_rewriting(tmp_path, monkeypatch):
    bound = metadata_fixture()
    charge = 16.19 + 120 + sum((31.37, 33.42))
    assert charge != 200.98
    bound["resource_close.json"]["charged_seconds"] = charge
    before = candidate.canonical(bound)
    monkeypatch.setattr(candidate, "read", lambda root, name, expected=None: bound[name])
    monkeypatch.setattr(candidate, "safe_hash", lambda *args: None)
    monkeypatch.setattr(candidate, "check_command", lambda *args: {"rss_bytes": 415268864})
    assert candidate.check_inputs(tmp_path) == bound
    assert candidate.canonical(bound) == before


def test_applicable_ci_requires_pr_smoke_and_no_pending_or_failed_checks():
    ci = metadata_fixture()["audit_receipts/source_final_head_ci.json"]
    assert candidate.ci_passed(ci, False) and candidate.ci_passed(ci, True)
    ci["checks"].append(
        {
            "name": "clean-linux-smoke",
            "head_sha": ci["head"],
            "status": "completed",
            "conclusion": "skipped",
        }
    )
    assert candidate.ci_passed(ci, False) and not candidate.ci_passed(ci, True)
    ci["checks"][2]["conclusion"] = "skipped"
    assert not candidate.ci_passed(ci, False)
