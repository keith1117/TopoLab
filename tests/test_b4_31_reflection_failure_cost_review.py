"""Synthetic scalar panels verify access boundaries, full statuses and independent costs."""

import subprocess
import sys
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_31_common as common
import b4_31_native_execution as execution
from b4_29_common import canonical, decode, digest, read, save, sha
from b4_31_independent_audit import independent
from b4_31_reflection_failure_cost_review import review


@pytest.fixture
def panel():
    c = common.contract()
    old = c["b4_30"]
    units = [[u["case_id"], u["policy"]] for u in old["historical_target_units"]]
    audit = {
        "passed": True,
        "gate_passed": False,
        "references": 18,
        "outcomes": 270,
        "selected_terminal_classifications": 323,
        "guard_witness_classifications": 204,
        "prediction_replays": 78,
        "unchanged_outcome_identities": 249,
        "decision": {
            "repaired": units[:4],
            "unrepaired": units[4:],
            "negative_controls": old["negative_controls"],
            "primary_failures": [old["failed_case_id"]],
            "regressions": [],
            "non_target_status_identity": True,
            "fixed_primary": 17,
            "target_cases": 13,
            "final_access": False,
            "sentinel_gate_passed": False,
            "repair_gate_passed": False,
            "large_y_primary_mean": 1.02,
            "large_y_primary_total_ratio": 0.98,
        },
    }
    counts = {
        "methods": {
            m: {"queries": 18, "failures": n, "fallbacks": n}
            for m, n in zip(old["methods"], old["method_failures"], strict=True)
        },
        "total_failures": 35,
        "all_from_audited_stored_packets": True,
        "new_execution": False,
    }
    targets = {
        "rows": [],
        "historical_target_predicates_passed": 4,
        "historical_target_predicates_failed": 3,
        "all_seven_matched_current_P_R_statuses_same": True,
        "currently_failed_B4_12_P_target_units_newly_repaired": 0,
        "B4_12_identity_already_verified_by_independent_audit": True,
        "historical_failures_do_not_imply_current_P_failure": True,
    }
    for i, u in enumerate(old["historical_target_units"]):
        r, p = u["policy"], u["policy"].replace("R/", "P/")
        targets["rows"].append(
            {
                "case_id": u["case_id"],
                "R_policy": r,
                r: {"succeeded": i < 4, "fallback": i >= 4},
                p: {"succeeded": i < 4, "fallback": i >= 4},
            }
        )
    names = ["uniform", "P/17", "P/29", "P/43", "R/17", "R/29", "R/43"]
    packet = {
        "case_id": old["failed_case_id"],
        "rows": [
            {
                "policy": m,
                "compliance_ratio": 1.0 if not i else 1.002 + i * 1e-5,
                "volume_error": 1e-8,
                "iterations": 128 if not i else 60 + i,
                "failed": bool(i),
                "fallback": bool(i),
                "failure_code": "quality_error" if i else None,
                "failure_type": "_BaselineQualityError" if i else None,
                "fully_charged_query_cost_seconds": 30.0 + i,
                "outcome_path": "sealed/DO_NOT_OPEN",
                "outcome_sha256": "0" * 64,
            }
            for i, m in enumerate(names)
        ],
    }
    with localcontext() as context:
        context.prec = 50
        stage = (
            Decimal(old["cumulative_charge_decimal"])
            - Decimal(old["original_failed_charge_decimal"])
            - 180
        ) / 5
    processes = [
        "sentinel_" + s for s in ("reference", "screen", "audit", "policy-audit", "independent")
    ]
    ledger = {
        "processes": [
            {
                "process": p,
                "closed_charge_decimal": str(stage),
                "complete_resource_evidence": True,
                "native": {"rss_bytes": 100},
                "peak_rss_bytes": 100,
            }
            for p in processes
        ],
        "source_revision": old["source_revision"],
        "charged_decimal": old["cumulative_charge_decimal"],
        "charged_seconds": float(old["cumulative_charge_decimal"]),
        "retained_failed_charge_decimal": old["original_failed_charge_decimal"],
        "aggregate_fully_paid_chain_reserve_seconds": 360,
        "fully_paid_chain_reserve_seconds": 180,
        "retained_failed_paid_chain_reserve_seconds": 180,
        "fresh_sealed": True,
        "final_access": False,
        "new_fits": 0,
        "whole_resource_acceptance": "PENDING_POSTEXIT",
        "full_training_memory": "PENDING/4GiB",
    }
    resource = {
        "independent_stage_rows": [
            {
                "process": p,
                "independent_charge_decimal": str(stage),
                "cap_decimal": "21600",
                "complete_native_resource": True,
            }
            for p in processes
        ],
        "source_revision": old["source_revision"],
        "charged_decimal": old["cumulative_charge_decimal"],
        "charged_seconds": float(old["cumulative_charge_decimal"]),
        "retained_failed_charge_decimal": old["original_failed_charge_decimal"],
        "aggregate_FULL_reserves_seconds": 360,
        "whole_resource_passed": True,
        "final_native_verifier_exit_checked": True,
        "scientific_gate": "FAIL",
        "repair_gate_passed": False,
        "conservative_whole_chain_rss_upper_bound_bytes": 800047104,
        "administrative_invocations": 2,
        "maximum_completed_numerical_campaigns": 1,
        "full_training_memory": "PENDING/4GiB",
    }
    values = {
        "b4-30-z-reflection-repair-v2/sentinel/independent_audit.json": audit,
        "b4-30-z-reflection-repair-v2/resource_close.json": ledger,
        "b4-30-software-validation-v2/final_native_profile_review.json": resource,
        "b4-30-software-validation-v2/report_failure_scalars.json": packet,
        "b4-30-software-validation-v2/report_method_failure_counts.json": counts,
        "b4-30-software-validation-v2/historical_target_status_reporting.json": targets,
        "b4-30-software-validation-v2/extra_progress_snapshot_preservation.json": {
            "passed": True,
            "preserved": True,
            "origin": "UNKNOWN",
            "not_used_as_canonical_progress": True,
            "does_not_replace_final_chain_or_its_audits": True,
        },
        "b4-30-z-reflection-repair/resource_close.json": {
            "charged_decimal": old["original_failed_charge_decimal"],
            "fully_paid_chain_reserve_seconds": 180,
        },
    }
    return values, c


def audit_pair(panel, tmp_path):
    values, c = panel
    result = review(values, c, tmp_path)
    save(tmp_path / "review.json", result)
    return result, independent(values, c, tmp_path)


def test_all_scalars_independent_decimal_no_new_repair(panel, tmp_path, monkeypatch):
    a = review(*panel, tmp_path)
    save(tmp_path / "review.json", a)
    monkeypatch.setattr(execution, "review", lambda *_: pytest.fail("auditor called reviewer"))
    b = independent(*panel, tmp_path)
    assert a["passed"] and b["passed"]
    assert b["old_cumulative_charge_decimal"] == "7323.1004352501081506"
    assert sum(r["failures"] for r in b["facts"]["methods"]) == 35
    assert not any(r["newly_repaired_P_failure"] for r in b["facts"]["historical_statuses"])
    assert b["facts"]["target_mean_margin_to_limit"] == -0.02
    assert b["facts"]["scientific_gate"] == "FAIL"
    assert b["facts"]["unknowns"]["failure_mechanism_cause"] == "NOT_ESTABLISHED"


@pytest.mark.parametrize("method", common.contract()["b4_30"]["methods"])
def test_every_method_failure_is_required(panel, tmp_path, method):
    values, _ = panel
    values["b4-30-software-validation-v2/report_method_failure_counts.json"]["methods"][method][
        "failures"
    ] += 1
    a, b = audit_pair(panel, tmp_path)
    assert not a["passed"] and not b["passed"]


@pytest.mark.parametrize("index", range(7))
def test_every_historical_P_status_is_required(panel, tmp_path, index):
    values, c = panel
    row = values["b4-30-software-validation-v2/historical_target_status_reporting.json"]["rows"][
        index
    ]
    p = c["b4_30"]["historical_target_units"][index]["policy"].replace("R/", "P/")
    row[p]["succeeded"] = not row[p]["succeeded"]
    a, b = audit_pair(panel, tmp_path)
    assert not a["passed"] and not b["passed"]


@pytest.mark.parametrize("index", range(1, 7))
def test_fallback_cannot_erase_failed_attempt(panel, tmp_path, index):
    panel[0]["b4-30-software-validation-v2/report_failure_scalars.json"]["rows"][index][
        "failed"
    ] = False
    a, b = audit_pair(panel, tmp_path)
    assert not a["passed"] and not b["passed"]


@pytest.mark.parametrize("name", ["mean", "reserve", "charge", "origin", "source"])
def test_cannot_replace_failed_predicate_or_history(panel, tmp_path, name):
    values, _ = panel
    if name == "mean":
        values["b4-30-z-reflection-repair-v2/sentinel/independent_audit.json"]["decision"][
            "large_y_primary_mean"
        ] = 0.98
    elif name == "reserve":
        values["b4-30-z-reflection-repair-v2/resource_close.json"][
            "aggregate_fully_paid_chain_reserve_seconds"
        ] = 180
    elif name == "charge":
        values["b4-30-z-reflection-repair-v2/resource_close.json"]["processes"][4][
            "closed_charge_decimal"
        ] = "1"
    elif name == "origin":
        values["b4-30-software-validation-v2/extra_progress_snapshot_preservation.json"][
            "origin"
        ] = "KNOWN"
    else:
        values["b4-30-software-validation-v2/final_native_profile_review.json"][
            "source_revision"
        ] = "other"
    a, b = audit_pair(panel, tmp_path)
    assert not a["passed"] and not b["passed"]


def test_independent_detects_reviewer_arithmetic_tamper(panel, tmp_path):
    result = review(*panel, tmp_path)
    result["facts"]["paired"][0]["paid_cost_ratio_R_over_P"] += 0.1
    save(tmp_path / "review.json", result)
    assert not independent(*panel, tmp_path)["passed"]


def scalar_inputs(tmp_path, raw=b'{"n":1}\n'):
    root = tmp_path / "TopoLab-data"
    root.mkdir()
    (root / "allowed.json").write_bytes(raw)
    spec = {
        "allowed_input_root_name": "TopoLab-data",
        "inputs_sha256": {"allowed.json": sha(raw)},
        "max_input_file_bytes": 262144,
    }
    return root, spec, common.ScalarInputs(root, tmp_path / "access.jsonl", spec)


def test_unregistered_path_rejected_before_open(tmp_path, monkeypatch):
    _, _, inputs = scalar_inputs(tmp_path)
    monkeypatch.setattr(Path, "read_bytes", lambda *_: pytest.fail("unregistered bytes opened"))
    with pytest.raises(ValueError, match="unregistered"):
        inputs.load("sealed/final.json")


@pytest.mark.parametrize("fault", ["sha", "symlink", "size", "directory"])
def test_input_identity_or_path_failure_before_decode(tmp_path, monkeypatch, fault):
    root, spec, inputs = scalar_inputs(tmp_path)
    p = root / "allowed.json"
    if fault == "sha":
        p.write_text('{"n":2}')
    elif fault == "size":
        spec["max_input_file_bytes"] = 1
    else:
        p.unlink()
        if fault == "symlink":
            p.symlink_to(tmp_path / "sealed.json")
        else:
            p.mkdir()
    with pytest.raises(ValueError):
        inputs.load("allowed.json")
    journal = (tmp_path / "access.jsonl").read_text()
    assert '"phase":"after"' not in journal


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}'])
def test_duplicate_and_nonfinite_rejected(tmp_path, raw):
    _, _, inputs = scalar_inputs(tmp_path, raw)
    with pytest.raises(ValueError):
        inputs.all()


def test_root_symlink_rejected_and_no_repeat_journal(tmp_path):
    root, spec, _ = scalar_inputs(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(root)
    with pytest.raises(ValueError, match="nonsymlink"):
        common.ScalarInputs(alias, tmp_path / "new.jsonl", spec)
    with pytest.raises(FileExistsError):
        common.ScalarInputs(root, tmp_path / "access.jsonl", spec)


def test_source_only_plan_never_reads_external_or_creates_output(tmp_path):
    path = tmp_path / "absent"
    script = Path(execution.__file__)
    result = subprocess.run(
        [sys.executable, str(script), "--input-root", str(path), "--output-root", str(path)],
        check=True,
        capture_output=True,
    )
    assert not path.exists()
    assert decode(result.stdout) == common.plan_payload()


def test_dirty_source_refused_before_output_or_inputs(tmp_path, monkeypatch):
    target = tmp_path / common.contract()["output_root_name"]

    def refuse(_):
        raise ValueError("whole-clean source required")

    monkeypatch.setattr(execution, "release", refuse)
    with pytest.raises(ValueError, match="whole-clean"):
        execution.campaign(tmp_path / "TopoLab-data", target, tmp_path / "release.json")
    assert not target.exists()


@pytest.mark.parametrize("fault", ["dirty", "branch", "origin", "tree", "ci", "lock"])
def test_release_checks_actual_source_and_ci_receipt(tmp_path, monkeypatch, fault):
    receipt = {
        "source_revision": "head",
        "source_tree": "tree",
        "tested_tree": "tree",
        "required_checks": {
            n: {"head": "success", "main": "success"}
            for n in ("quality", "frontend", "clean-linux-smoke")
        },
        "passed": True,
        "locked_sync_passed": True,
        "protected_merge": True,
        "all_applicable_ci_passed_before_merge": True,
        "plan": common.plan_payload(),
        "owner_authorization_sha256": common.contract()["authority"]["owner_authorization_sha256"],
    }
    if fault == "ci":
        receipt["required_checks"]["clean-linux-smoke"]["head"] = "skipped"
    if fault == "lock":
        receipt["locked_sync_passed"] = False
    save(tmp_path / "release.json", receipt)

    def git(*args):
        if args[0] == "status":
            return "?? owner.md" if fault == "dirty" else ""
        if args[0] == "branch":
            return "feature" if fault == "branch" else "main"
        if args[-1] == "HEAD^{tree}":
            return "other" if fault == "tree" else "tree"
        if args[-1] == "origin/main" and fault == "origin":
            return "other"
        return "head"

    monkeypatch.setattr(common, "git", git)
    with pytest.raises(ValueError, match="whole-clean"):
        common.release(tmp_path / "release.json")


def test_failed_read_preserves_attempt_and_no_retry(tmp_path, monkeypatch):
    root, spec, _ = scalar_inputs(tmp_path)
    out = tmp_path / "output"
    out.mkdir()
    (root / "allowed.json").write_text("changed")
    monkeypatch.setattr(common, "release", lambda _: "source")
    monkeypatch.setattr(common, "contract", lambda: spec)
    monkeypatch.setattr(common, "plan_payload", lambda: {"plan_sha256": "plan"})
    result = common.execute_stage("review", root, out, lambda *_: pytest.fail("decoded bad input"))
    assert not result["passed"] and read(out / "review.json")["numerical_calls"] == 0
    assert '"phase":"failure"' in (out / "review.access.jsonl").read_text()
    with pytest.raises(FileExistsError):
        common.execute_stage("review", root, out, lambda *_: {})


@pytest.mark.parametrize("fault", ["missing", "failed_exit", "budget", "clean"])
def test_native_charge_retains_failure_and_FULL60(tmp_path, monkeypatch, fault):
    (tmp_path / "audit_receipts").mkdir()
    commands = []
    for name in ("review", "independent"):
        commands.append(
            {
                "name": name,
                "native": None if fault == "missing" else {"wall_seconds": 0.1, "rss_bytes": 10},
                "observed_outer_wall_seconds": 70 if fault == "budget" else 0.3,
                "exit_code": 1 if fault == "failed_exit" else 0,
                "terminated": False,
            }
        )
        save(tmp_path / (name + ".json"), {"internal_seconds": 0.05, "passed": False})
    save(tmp_path / "audit_receipts/execution_commands.json", commands)
    monkeypatch.setattr(execution, "checked_native", lambda _, command: command["native"])
    _, charges, total, complete, _ = execution.stage_accounting(tmp_path)
    assert total == Decimal(60) + sum(charges.values())
    assert charges["review"] == (Decimal(80) if fault == "budget" else Decimal("10.3"))
    assert complete is (fault == "clean")  # Metadata FAIL remains distinct from resource PASS.


def test_frozen_contract_and_plan_bind_all_shared_helpers():
    assert digest(common.CONTRACT) == common.CONTRACT_SHA
    p = common.plan_payload()
    assert len(p["inputs_sha256"]) == 8
    assert "scripts/b4_29_common.py" in p["source_sha256"]
    assert "scripts/b4_29_native_execution.py" in p["source_sha256"]
    assert sha(canonical({k: v for k, v in p.items() if k != "plan_sha256"})) == p["plan_sha256"]
