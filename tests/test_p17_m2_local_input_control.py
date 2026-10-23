"""NEW local-input preparation interfaces; no source IO or formal execution."""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def load_control():
    spec = importlib.util.spec_from_file_location(
        "local_input_control", REPO / "scripts/p17_m2_local_input_control.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def protocol():
    return {
        "schema": "topolab.v2.m2-local-input-contract.v1",
        "execution_identity": "topolab.v2.p17-m2-local-input-version.v1",
        "authority": {
            "owner_adoption_record": "new public test fixture owner record",
            "new_custody_model_adopted": True,
            "software_implementation_public_checks_and_target_preparation_authorized": True,
            "old_metadata_and_payload_stat_read_temporary_parse_authorized": False,
            "new_six_role_activation_authorized": False,
            "source_copy_now_authorized": False,
            "scientific_B_authorized": False,
            "scientific_C_authorized": False,
            "old_quota_reopening_authorized": False,
        },
        "preparation_grant": {"executor_seconds": 14400, "independent_seconds": 10800,
                              "continuous_clock": True},
        "budget_request_NOT_GRANTED": {
            "preparation_including_public_checks_CI_and_target_readiness": {
                "executor_seconds": 14400,
                "independent_seconds": 10800,
            },
            "formal": {
                "common_window_seconds": 4500,
                "FULL_seconds_by_role": {
                    "independent-public-check": 300,
                    "exporter-r0": 300,
                    "independent-r0": 300,
                    "exporter-r1": 1200,
                    "independent-r1": 1200,
                    "shared-closeout": 300,
                },
                "FULL_sum_seconds": 3600,
                "setup_lease_seconds": 300,
                "between_roles_total_seconds": 240,
                "final_frontier_seal_handoff_seconds": 360,
                "first_dispatch_remaining_minimum": 4200,
            },
        },
    }


def test_preparation_grant_does_not_authorize_source_or_formal_execution():
    control = load_control()
    actual = control.authority_checked(protocol(), "preparation")
    assert actual == "PREPARATION_AUTHORIZED_FORMAL_CLOSED"
    with pytest.raises(ValueError, match="source and six-role activation grants"):
        control.authority_checked(protocol(), "formal")


def test_isolated_actual_cli_reports_only_software_capability_and_refuses_activation():
    import json
    import subprocess
    import sys

    script = REPO / "scripts/p17_m2_local_input_control.py"
    capability = subprocess.run(
        [sys.executable, "-I", str(script), "capability"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert capability.returncode == 0, capability.stderr
    result = json.loads(capability.stdout)
    assert result["status"] == "SOFTWARE_PREPARATION_CAPABILITY_ONLY"
    assert result["formal_launch_binding"] == "INCOMPLETE"
    assert result["old_source_stat_read_copy"] == 0
    assert result["runtime"]["isolated"] is True
    assert result["runtime"]["orig_argv"][1:] == ["-I", str(script), "capability"]
    assert Path(result["runtime"]["orig_argv"][0]).is_absolute()
    rejected = subprocess.run(
        [sys.executable, "-I", str(script), "activate"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert rejected.returncode == 1
    assert json.loads(rejected.stdout)["reason"] == "FORMAL_LAUNCH_BINDING_INCOMPLETE"
    assert json.loads(rejected.stdout)["old_source_stat_read_copy"] == 0


def test_nonisolated_actual_cli_cannot_claim_registered_runtime():
    import json
    import subprocess
    import sys

    rejected = subprocess.run(
        [sys.executable, str(REPO / "scripts/p17_m2_local_input_control.py"), "capability"],
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    assert rejected.returncode == 1
    assert json.loads(rejected.stdout)["reason"] == "ACTUAL_ISOLATED_ENTRY_REQUIRED"


@pytest.mark.parametrize("fault", ["draft", "old_identity", "unattributed", "truthy_grant",
                                    "old_quota", "missing_actual_prep_grant", "prep_cap",
                                    "FULL", "window", "handoff", "boolean_owner_record"])
def test_contract_rejects_old_or_ungranted_or_changed_authority(fault):
    control = load_control()
    value = protocol()
    if fault == "draft":
        value["schema"] = "topolab.v2.m2-local-input-contract.draft.v1"
    elif fault == "old_identity":
        value["execution_identity"] = "topolab.v2.p17-m2-source-stable-export.v1"
    elif fault == "unattributed":
        value["authority"]["owner_adoption_record"] = None
    elif fault == "boolean_owner_record":
        value["authority"]["owner_adoption_record"] = True
    elif fault == "truthy_grant":
        value["authority"]["new_custody_model_adopted"] = 1
    elif fault == "old_quota":
        value["authority"]["old_quota_reopening_authorized"] = True
    elif fault == "missing_actual_prep_grant":
        del value["preparation_grant"]
    elif fault == "prep_cap":
        value["preparation_grant"]["executor_seconds"] = 14401
    elif fault == "FULL":
        value["budget_request_NOT_GRANTED"]["formal"]["FULL_seconds_by_role"]["exporter-r1"] = 1201
    elif fault == "window":
        value["budget_request_NOT_GRANTED"]["formal"]["common_window_seconds"] = 4501
    else:
        value["budget_request_NOT_GRANTED"]["formal"]["final_frontier_seal_handoff_seconds"] = 0
    with pytest.raises((ValueError, KeyError)):
        control.authority_checked(value, "preparation")


def plan():
    sources = [
        "scripts/p17_m2_local_input_control.py", "scripts/p17_m2_local_input_version.py",
        "scripts/p17_m2_local_input_independent.py", "scripts/p17_m2_input_export.py",
        "scripts/p17_m2_input_export_independent.py", "scripts/p17_m2_input_export_control.py",
        "scripts/p17_m2_input_export_dispatch.js", "scripts/p17_m2_resource_control.py",
        "scripts/p17_m2_homotopy.py", "uv.lock",
        "docs/planning/p17_m2_input_export_preparation_proposal.json",
        "docs/planning/p17_m2_local_input_version_protocol.md",
        "docs/planning/p17_m2_local_input_version_protocol.json",
    ]
    return {
        "schema": "topolab.v2.m2-local-input-launch-plan.v1",
        "execution_identity": "topolab.v2.p17-m2-local-input-version.v1",
        "original_root_literal": "/Users/keith1117/Documents/TopoLab-data",
        "generation_root_literal": (
            "/Users/Shared/TopoLab-input-versions/p17-m2-local-input-version-v1"),
        "backup_root_literal": (
            "/Users/Shared/TopoLab-input-versions/p17-m2-local-input-version-v1-independent-backup"),
        "content_sha256": "f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad",
        "protocol_sha256": "a" * 64,
        "merged_source": "a" * 40, "merged_tree": "b" * 40,
        "source_files": {name: "c" * 64 for name in sources},
        "authors": {"executor": "public fixture executor", "independent": "other fixture author"},
        "actor_activation_UTC_seconds": 1000.0,
        "actor_window_seconds": 4500,
        "actor_deadlines_UTC": {"exporter": "1970-01-01T01:31:40.000Z",
                                "independent": "1970-01-01T01:31:40.000Z"},
        "FULL_caps_seconds": (
            protocol()["budget_request_NOT_GRANTED"]["formal"]["FULL_seconds_by_role"]),
        "formal_overhead_caps": {"setup_lease_seconds": 300, "between_roles_total_seconds": 240,
                                 "final_frontier_seal_handoff_seconds": 360},
    }


def test_local_plan_has_distinct_original_generation_and_backup_roots_without_path_io():
    control = load_control()
    assert control.validate_plan(plan(), 1000.0) == "PLAN_STRUCTURE_ONLY_NO_LAUNCH_ADMISSION"


@pytest.mark.parametrize("fault", ["original_root", "generation_root", "same_root", "old_identity",
                                    "source_omitted", "source_added", "hash", "same_author",
                                    "window", "FULL", "expired", "nonfinite_time"])
def test_frozen_local_plan_rejects_changed_identity_or_domain(fault):
    control = load_control()
    value = plan()
    now = 1000.0
    if fault == "original_root":
        value["original_root_literal"] = "/private/tmp/other"
    elif fault == "generation_root":
        value["generation_root_literal"] += "-retry"
    elif fault == "same_root":
        value["backup_root_literal"] = value["generation_root_literal"]
    elif fault == "old_identity":
        value["execution_identity"] = "topolab.v2.p17-m2-source-stable-export.v1"
    elif fault == "source_omitted":
        value["source_files"].pop("uv.lock")
    elif fault == "source_added":
        value["source_files"]["unknown-helper.py"] = "a" * 64
    elif fault == "hash":
        value["source_files"]["uv.lock"] = "UNKNOWN"
    elif fault == "same_author":
        value["authors"]["independent"] = value["authors"]["executor"]
    elif fault == "window":
        value["actor_window_seconds"] = 4501
    elif fault == "FULL":
        value["FULL_caps_seconds"]["exporter-r0"] = 0
    elif fault == "expired":
        now = 5500.001
    else:
        now = float("nan")
    with pytest.raises(ValueError):
        control.validate_plan(value, now)


def lease():
    import hashlib
    import json

    frozen = plan()
    raw = (json.dumps(frozen, sort_keys=True, separators=(",", ":"),
                      allow_nan=False) + "\n").encode("ascii")
    return {
        "schema": "topolab.v2.m2-local-generation-lease.v1",
        "execution_identity": "topolab.v2.p17-m2-local-input-version.v1",
        "plan_sha256": hashlib.sha256(raw).hexdigest(),
        "root": frozen["generation_root_literal"], "backup": frozen["backup_root_literal"],
        "custodian": frozen["authors"]["executor"],
        "scope": "LOCAL_GENERATION_WRITER_EXCLUSION_ONLY",
        "active": True, "acquired_UTC_seconds": 1100,
        "old_source_quiescence_claim": False,
        "held_until": "LAST_REGISTERED_READER_ACTUAL_RETURN_INCLUDING_FILING",
        "content_writers": ["exporter-r0", "exporter-r1"],
        "content_mutation_after_exporter_r1_exit": False,
    }


def test_target_lease_is_local_only_and_outlives_formal_close():
    control = load_control()
    assert (control.target_lease_checked(plan(), lease())
            == "LEASE_STRUCTURE_ONLY_NO_CUSTODY_ADMISSION")


@pytest.mark.parametrize("fault", ["old_scope", "source_pause", "early_release", "old_root",
                                    "changed_plan", "late_acquisition", "released", "extra_writer",
                                    "post_exit_content_mutation"])
def test_target_lease_refuses_false_original_pause_or_premature_release(fault):
    control = load_control()
    value = lease()
    release = None
    if fault == "old_scope":
        value["scope"] = "OLD_SOURCE_WRITER_EXCLUSION"
    elif fault == "source_pause":
        value["old_source_quiescence_claim"] = True
    elif fault == "early_release":
        value["held_until"] = "SHARED_FORMAL_CLOSE"
    elif fault == "old_root":
        value["root"] = plan()["original_root_literal"]
    elif fault == "changed_plan":
        value["plan_sha256"] = "0" * 64
    elif fault == "late_acquisition":
        value["acquired_UTC_seconds"] = 1300.001
    elif fault == "released":
        release = {"released_UTC_seconds": 1200, "claimed": "READY"}
    elif fault == "extra_writer":
        value["content_writers"].append("shared-closeout")
    else:
        value["content_mutation_after_exporter_r1_exit"] = True
    with pytest.raises(ValueError):
        control.target_lease_checked(plan(), value, release=release)


def new_ledger():
    return {"attempted_roles": [], "active_role": None, "STOP": False,
            "between_roles_seconds_used": 0, "FULL_charges_seconds": {},
            "observed": {}}


def test_first_dispatch_reserves_complete_suffix_and_books_shared_once_if_started():
    control = load_control()
    ledger = new_ledger()
    checked = control.dispatch_gate(plan(), ledger, "independent-public-check", 1300.0)
    assert checked["status"] == "RESERVE_STRUCTURE_ONLY_NO_DISPATCH_ADMISSION"
    assert checked["required_remaining_seconds"] == 4200
    assert checked["new_FULL_charge_if_started"] == 600
    assert checked["FULL_charges_after_start"] == {
        "independent-public-check": 300, "shared-closeout": 300,
    }
    assert ledger == new_ledger()  # Planning is not an actual dispatch/charge.
    with pytest.raises(ValueError, match="complete remaining suffix"):
        control.dispatch_gate(plan(), ledger, "independent-public-check", 1300.001)


def test_later_dispatch_does_not_refund_or_rebook_reserved_shared_FULL():
    control = load_control()
    ledger = new_ledger()
    ledger["attempted_roles"] = ["independent-public-check"]
    ledger["FULL_charges_seconds"] = {"independent-public-check": 300, "shared-closeout": 300}
    ledger["between_roles_seconds_used"] = 20
    ledger["observed"] = {"independent-public-check": {
        "status": "PASS_R_LOCAL_FULL_ROLE", "cleanup": {"group_gone": True},
    }}
    checked = control.dispatch_gate(plan(), ledger, "exporter-r0", 1400.0)
    assert checked["new_FULL_charge_if_started"] == 300
    assert checked["required_remaining_seconds"] == 3880
    assert checked["FULL_charges_after_start"] == {
        "independent-public-check": 300, "exporter-r0": 300, "shared-closeout": 300,
    }


@pytest.mark.parametrize("fault", ["STOP", "repeat", "wrong_order", "active", "refund",
                                    "missing_predecessor", "unknown_cleanup", "coord_overrun"])
def test_dispatch_structure_rejects_STOP_retries_and_missing_complete_predecessors(fault):
    control = load_control()
    ledger = new_ledger()
    role = "independent-public-check"
    if fault == "STOP":
        ledger["STOP"] = True
    elif fault == "repeat":
        ledger["attempted_roles"] = [role]
        ledger["FULL_charges_seconds"] = {role: 300, "shared-closeout": 300}
    elif fault == "wrong_order":
        role = "exporter-r0"
    elif fault == "active":
        ledger["active_role"] = role
    elif fault == "refund":
        ledger["attempted_roles"] = ["independent-public-check"]
        ledger["FULL_charges_seconds"] = {"independent-public-check": 0, "shared-closeout": 300}
        role = "exporter-r0"
    elif fault in {"missing_predecessor", "unknown_cleanup"}:
        ledger["attempted_roles"] = ["independent-public-check"]
        ledger["FULL_charges_seconds"] = {"independent-public-check": 300, "shared-closeout": 300}
        role = "exporter-r0"
        if fault == "unknown_cleanup":
            ledger["observed"] = {"independent-public-check": {
                "status": "PASS_R_LOCAL_FULL_ROLE", "cleanup": {"group_gone": None},
            }}
    else:
        ledger["between_roles_seconds_used"] = 241
    with pytest.raises(ValueError):
        control.dispatch_gate(plan(), ledger, role, 1300)


def test_stopped_prefix_keeps_full_charge_and_only_allows_structural_shared_reserve():
    control = load_control()
    ledger = new_ledger()
    ledger.update(STOP=True, attempted_roles=["independent-public-check"],
                  FULL_charges_seconds={"independent-public-check": 300, "shared-closeout": 300},
                  observed={"independent-public-check": {
                      "status": "STOP_NO_RETRY", "cleanup": {"group_gone": True},
                  }})
    checked = control.dispatch_gate(plan(), ledger, "shared-closeout", 1300)
    assert checked["new_FULL_charge_if_started"] == 0
    assert checked["FULL_charges_after_start"] == ledger["FULL_charges_seconds"]
    assert ledger["STOP"] is True
    ledger["observed"]["independent-public-check"]["cleanup"]["group_gone"] = None
    with pytest.raises(ValueError, match="UNKNOWN cleanup"):
        control.dispatch_gate(plan(), ledger, "shared-closeout", 1300)
