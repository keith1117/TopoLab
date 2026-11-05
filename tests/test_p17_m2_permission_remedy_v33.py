"""V33 fixed identity is admitted at both live issuer and literal runtime seams."""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
RECOVERY = "topolab.v2.p17-binding-certificate-recovery.20261104.v7"
INPUT = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v5"
PUBLIC = "/private/tmp/topolab-public-registered5-source-acquisition-20261104-v7"
PARENT = "/Users/keith1117/Library/Application Support/TopoLab-custody/"


def module(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def test_v33_readiness_contract_names_the_actual_selected_preflight_entry():
    control = module("p17_m2_source_acquisition_control").for_registered_identity(INPUT)
    registered = control.load("p17_m2_registered_input")
    description = registered.authority()["readiness_schema"]["preflight_actual"]
    assert "explicit registered_input_v5.py preflight --readiness-sha SHA" in description
    assert "registered_input_v4.py" not in description
    assert registered.CLI_ENTRY == "p17_m2_registered_input_v5.py"


def test_v33_profile_native_author_deadlines_and_fixed_targets():
    old = module("p17_m2_source_binding_recovery")
    recovery = old.for_identity(RECOVERY)
    control = module("p17_m2_source_acquisition_control").for_registered_identity(INPUT)
    registered = control.load("p17_m2_registered_input")
    policy = registered.authority()
    assert policy["actors"] == {
        "executor": "/root",
        "independent": "/root/permission_remedy_reader_v1",
    }
    assert policy["global_deadline_ms"] == 1793869680000
    assert policy["public_roots"] == [PUBLIC]
    assert policy["input_limits"]["public_graphs_max"] == 1
    assert (
        policy["fixed_target"]["attempts"]["1"]["generation"]
        == PARENT + "p17-m2-local-input-version-v14-strict-binding-20261104"
    )
    assert (
        policy["fixed_target"]["attempts"]["2"]["generation"]
        == PARENT + "p17-m2-local-input-version-v15-strict-binding-remedy-20261104"
    )
    assert recovery.authority()["limits"]["software_deadline_ms"] == 1793837617118
    native = module("p17_m2_source_binding_native")
    plan = {
        "schema": native.METADATA_SCHEMA,
        "context": {"execution_identity": RECOVERY, "attempt": 1, "scope": native.RECOVERY_SCOPE},
        "runtime": {"python": "/public/python", "cwd": str(REPO)},
        "root": "/public/metadata",
    }
    assert native.execution_profile(plan) == (RECOVERY, 300)
    assert native.role_profile(plan)[3] == {
        "binding-certificate-auditor": "/root/permission_remedy_reader_v1"
    }
    assert native.argv_for(plan, "supervise", "binding-certificate-auditor")[2].endswith(
        "/p17_m2_source_binding_recovery_v7.py"
    )
    assert old.IDENTITY.endswith(".v4")


@pytest.mark.parametrize("attempt,number,suffix", [(1, 14, "20261104"), (2, 15, "remedy-20261104")])
def test_v33_opaque_issuer_and_scientific_root_result_callbacks(
    monkeypatch, attempt, number, suffix
):
    control = module("p17_m2_source_acquisition_control").for_registered_identity(INPUT)
    auditor = control.load("p17_m2_source_acquisition_independent")
    policy = control.load("p17_m2_registered_input").authority()
    root = PARENT + f"p17-m2-local-input-version-v{number}-strict-binding-{suffix}"
    plan = {
        "execution_identity": INPUT,
        "scope": auditor.FORMAL_SCOPE,
        "binding": {"formal_attempt": attempt},
        "root": root,
        "content_root": root + "/content",
    }
    binding = {
        "verified_plan": plan,
        "scope": auditor.FORMAL_SCOPE,
        "root": root + "/content",
        "root_identity": {},
        "version_id": "a" * 64,
        "contract_sha256": "b" * 64,
        "plan_sha256": "c" * 64,
        "shared_packet_sha256": "d" * 64,
    }
    certificate = auditor.CheckedAcquisitionInput(
        binding, _authority=auditor._ACQUISITION_AUTHORITY
    )
    reader = module("p17_m2_source_verified_input")
    assert reader.checked_acquisition_issuer(certificate) is auditor
    with pytest.raises(ValueError, match="independent authority"):
        auditor.CheckedAcquisitionInput(binding)
    monkeypatch.setattr(auditor, "_registered_authority", lambda plan: policy)
    monkeypatch.setattr(auditor, "validate_binding", lambda plan: None)
    science = module("p17_m2_scientific_independent")
    granted = science.CheckedScientificInput(binding, {}, _authority=science._SCIENCE_AUTHORITY)
    assert granted._reader_root(Path(root + "/content")) == Path(root + "/content")
    assert granted._reader_result_seconds() == (1800, 1800)
    admission = object.__new__(science.CheckedBAdmission)
    admission.contract_sha256 = "e" * 64
    monkeypatch.setattr(science, "check_contract", lambda value: "e" * 64)
    with pytest.raises(ValueError, match="independently accepted acquisition"):
        science.grant_scientific_input(granted, {}, "scientific-producer", admission)
    with pytest.raises(ValueError, match="independently accepted acquisition"):
        science.grant_scientific_input({"status": "PASS"}, {}, "scientific-producer", admission)
    certificate._binding["verified_plan"]["execution_identity"] = "UNREGISTERED"
    assert reader.checked_acquisition_issuer(certificate) is None


def test_v33_waiter_fixed_deadline_and_independent_software_closure(monkeypatch):
    waiter = module("await_m2_acquisition_receipt")
    plan = {
        "execution_identity": INPUT,
        "root": PUBLIC,
        "role_order": list(waiter.ROLES),
        "actor_window_seconds": 4500,
        "formal_authority": False,
        "scope": "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY",
        "actor_activation_UTC_seconds": 1,
    }
    assert (
        waiter.project(plan, b"public metadata", PUBLIC)["applicable_deadline_ms"] == 1793837617118
    )
    control = module("p17_m2_source_acquisition_control").for_registered_identity(INPUT)
    auditor = control.load("p17_m2_source_acquisition_independent")
    captured = {}

    def capture(plan, **kwargs):
        captured.update(kwargs)
        raise RuntimeError("compiler seam before runtime IO")

    monkeypatch.setattr(auditor, "validate_binding", lambda plan: None)
    monkeypatch.setattr(auditor.native, "_check_software", capture)
    with pytest.raises(RuntimeError, match="compiler seam"):
        auditor._check_software(
            {
                "execution_identity": INPUT,
                "scope": auditor.REHEARSAL_SCOPE,
                "source_identity_policy": auditor.HASH_BOUND_POLICY,
                "binding": {
                    "source_identity_policy": auditor.HASH_BOUND_POLICY,
                    "authority_protocol_path": auditor.REGISTERED_PROTOCOL,
                    "strict23_registration": {
                        "certificate_sha256": "a" * 64,
                        "finalize_actual_sha256": "b" * 64,
                    },
                },
            }
        )
    assert auditor.native._software_closure(
        REPO, contracts=captured["contracts"]
    ) == control.source_freeze(INPUT)
    closure = control.source_freeze(INPUT)
    for name in [
        "scripts/p17_m2_source_verified_input.py",
        "scripts/m2_acquisition_actual_boundary.mjs",
        "scripts/p17_m2_source_binding_recovery_v7.py",
        "scripts/p17_m2_registered_input_v5.py",
    ]:
        assert name in closure


def test_v33_permission_is_required_before_any_target_preparation(monkeypatch):
    recovery = module("p17_m2_source_binding_recovery").for_identity(RECOVERY)
    monkeypatch.setattr(
        recovery, "review_readiness", lambda *args: pytest.fail("review read before permission")
    )
    with pytest.raises(ValueError, match="approved permission preflight required"):
        recovery.prepare("public", 1)


def test_v33_literal_payload_is_admitted_before_native_and_old_entry_rejected(monkeypatch):
    module("p17_m2_homotopy")
    resource = module("p17_m2_resource_control")

    def before_native(*args, **kwargs):
        raise RuntimeError("literal admitted before native")

    monkeypatch.setattr(Path, "mkdir", before_native)
    argv = [
        "/public/python",
        "-I",
        str(REPO / "scripts/p17_m2_source_binding_recovery_v7.py"),
        "payload",
        "--plan",
        "/public/plan.json",
        "--plan-sha",
        "a" * 64,
        "--role",
        "binding-certificate-auditor",
    ]
    with pytest.raises(RuntimeError, match="literal admitted"):
        resource.invoke(
            "/PUBLIC_NOT_CREATED",
            "binding-certificate-auditor",
            argv,
            timeout=1,
            measurement_execution_identity=RECOVERY,
            measurement_scope="STRICT_BINDING_CERTIFICATE_RECOVERY_METADATA_ONLY",
        )
    argv[2] = str(REPO / "scripts/p17_m2_source_binding_recovery_v6.py")
    with pytest.raises(ValueError, match="literal payload argv"):
        resource.invoke(
            "/PUBLIC_NOT_CREATED",
            "binding-certificate-auditor",
            argv,
            timeout=1,
            measurement_execution_identity=RECOVERY,
            measurement_scope="STRICT_BINDING_CERTIFICATE_RECOVERY_METADATA_ONLY",
        )


# Literal owner registration fixture; public tests never open external evidence.
V33_GRANT = {
    "schema": "topolab.owner.NEW-final-permission-remedy-and-continuation.v33",
    "authority": "Current owner explicitly authorizes automatic sufficient finite NEW budgets "
    "for unstarted repairs/closing/input and conditional B/C; no old allowance "
    "reopens",
    "registered_before_new_work_ms": 1793823216480,
    "base_owner_grant": {
        "path": (
            "/Users/keith1117/Documents/TopoLab-data/p17-m2-source-binding-v1-"
            "20261103T173800Z/NEW-unstarted-continuous-input-and-fixed-science"
            "-v31.json"
        ),
        "sha256": "aa591ff55c5b00a57efc6bf671804fd9241b0780baaddbbbd432da33887ef821",
    },
    "failed_metadata8": {
        "path": (
            "/Users/keith1117/Documents/TopoLab-data/p17-m2-source-binding-v1-"
            "20261103T173800Z/independent/V31-metadata8-auto-approval-timeout-"
            "STOP-v1.json"
        ),
        "sha256": "5ce2b6c849128b2bcd3b5efbcfa903a95b33296f69e25b4feca971f08d6507e0",
        "reason": "Automatic permission approval review deadline elapsed "
        "before CreateProcess; unsafe judgment not asserted; "
        "remaining167267ms below fixed180000, no "
        "retry/REC/process/Source",
    },
    "R15": {
        "complete_sha256": "aefadb4d34a2eb6a12359e733f6390af2b8a798c55c9a8d59d0c5b7b57cfa62c",
        "all_checks_source_and_driver_budget_pass": True,
        "original_actual_sha256": (
            "f46d84edf34483a36395e683fe99cf1894dd0d7ea600a53501329cf3770142f7"
        ),
        "actual_last_return_late_600_and18_46_parent_expired": True,
        "old_stage_not_completed_or_reopened": True,
        "Root_sampling_gap_cause": "UNKNOWN; independent agent separately reported "
        "selected model at capacity, no causal attribution to "
        "Root invented",
    },
    "old_scope_unused_closed": {
        "S31_named_public5_and6_actual0": True,
        "S31_formal6_actual0": True,
        "S31_formal_input_actual0": True,
        "S31_B_C_actual0": True,
        "S32_R16_actual0_unused_closed": True,
        "all_old_clocks_counters_fees_and_gap_records_retained": True,
        "no_transfer_refund_or_reuse": True,
    },
    "original_author_start_ms": 1793727480000,
    "old_cumulative_author_span_cap_seconds122400_retained": True,
    "NEW_additional_Root_author_seconds": 19800,
    "NEW_cumulative_Root_author_span_cap_seconds": 142200,
    "NEW_global_deadline_ms": 1793869680000,
    "original_outer_deadline_ms_UNCHANGED": 1793878680000,
    "original_outer_span151200_UNCHANGED": True,
    "NEW_primary_phase_maxima_seconds": {
        "permission_remedy_software_review_publication_public": 14400,
        "formal_metadata": 1200,
        "primary_input_formal_and_result": 6300,
        "scientific_contract_and_publication": 7200,
        "B_C_original": 14760,
        "final_actual_return_retention": 1800,
    },
    "sum_primary_maxima_seconds": 45660,
    "all_launches_require_full_remaining_suffix_and_global_fit": True,
    "NEW_Root_metadata_calls": {
        "software_publication": 512,
        "formal_metadata": 64,
        "input_all_attempts": 512,
        "scientific_contract_publication": 256,
        "B_C": 512,
        "final_filing": 128,
        "total": 1984,
    },
    "ROOT_counter_base_before_registration": 1726,
    "NEW_independent": {
        "author": "/root/permission_remedy_reader_v1",
        "metadata_calls": 1984,
        "wall_cap_seconds": 45660,
        "global_deadline_ms": 1793869680000,
        "logical_GitHub_GET": 128,
        "old_I_calls572_and_capacity_error_preserved": True,
        "no_old_author_budget_reused": True,
    },
    "NEW_Root_logical_GitHub_GET": 256,
    "NEW_engineer": {
        "author": "/root/permission_remedy_engineer_v1",
        "seconds_including_startup_filing_actual_return": 1800,
        "calls": 64,
    },
    "NEW_reviewers": {
        "authors": ["/root/permission_remedy_standards_v1", "/root/permission_remedy_spec_v1"],
        "seconds_each_including_actual_return": 900,
        "calls_each": 32,
    },
    "NEW_software_full_campaign": {
        "calls": 1,
        "ordinal": 21,
        "label": "R16_NEW_PERMISSION_ROUTE",
        "Native_FULL_max": 100000,
        "UTC_whole_wall_max_seconds": 4200,
        "closing_suffix_seconds": 600,
        "preexpired_no_Popen_public_regression_before_new_helper": True,
        "old_R15_helper_bytes_not_modified": True,
    },
    "NEW_CI_workflow_runs_max": 12,
    "identities": {
        "metadata": "topolab.v2.p17-binding-certificate-recovery.20261104.v7",
        "input": "topolab.v2.p17-m2-registered-source-acquisition.20261104.v5",
    },
    "NEW_named_NATIVE_FULL": {
        "metadata_public9_once": 120,
        "public_source7_once": 3780,
        "formal_metadata7_once": 120,
        "formal_input_two_attempts": 7560,
        "B_once": 180,
        "C_once14580": True,
        "total_named": 26340,
    },
    "permission_remedy_RULE": "Only one new public9 Native attempt. Freeze old8; real "
    "original error collector regression, new compatible contract, "
    "distinct review/all-five normal protected PR+exact-main4CI "
    "BEFORE public9; same-author permission prefix preflight "
    "WITHOUT actor/root/Native first, then new300s actor only after "
    "actual approval. One service retry allowed only if all "
    "original remaining180s/role guards still hold; no "
    "expired-window/reset. If service still prevents safe "
    "execution, preserve STOP and finish authorized "
    "software/evidence closing; no automatic new public10.",
    "targets": {
        "parent": "/Users/keith1117/Library/Application Support/TopoLab-custody",
        "public_metadata": (
            "/Users/keith1117/Documents/TopoLab-data/p17-m2-source-binding-v1-"
            "20261103T173800Z/topolab-public-binding-certificate-recovery-v9"
        ),
        "formal_metadata": (
            "/Users/keith1117/Documents/TopoLab-data/p17-m2-source-binding-v1-"
            "20261103T173800Z/binding-formal-v3-certificate-recovery-v7"
        ),
        "public_source": "/private/tmp/topolab-public-registered5-source-acquisition-20261104-v7",
        "formal": [
            "p17-m2-local-input-version-v14-strict-binding-20261104",
            "p17-m2-local-input-version-v15-strict-binding-remedy-20261104",
        ],
        "backup_suffix": "-independent-backup",
        "all_formal_unprobed": True,
        "no_old_failed_lease_unlock_or_scene_reuse": True,
    },
    "source_and_science_UNCHANGED": {
        "new_Original_registration_reads": 0,
        "new_Foundation_helpers": 0,
        "files_once_each_author_attempt": 598,
        "all_formal_Original_reads2392": True,
        "whole_Original_reads2484_helpers138": True,
        "metadata40_payload558_version1071": True,
        "source_coordination_seconds240": True,
        "metadata_actor_seconds300": True,
        "metadata_FULL120_timeout110_reserve60": True,
        "native_RSS4294967296": True,
        "B_FULL180_C_FULL14580": True,
        "fixed_models_panel_quality_speed_windows_and_resources_unchanged": True,
        "no_scientific_retry_search": True,
    },
    "same_issuer_two_fix_rounds_already_used_no_third_by_rename": True,
    "known_NEW_FULL_lower_before_this_grant": 201750,
    "all_other_fees_R15_pending_and_service_waits": "UNKNOWN_NOT_ZERO",
    "P17": "UNREPAIRED",
    "all_old25_and_failed_HELD_scenes_preserved": True,
}

V33_ACTIVATION = {
    "schema": "topolab.NEW-permission-remedy.software-activation.v1",
    "execution_identity": "topolab.v2.p17-binding-certificate-recovery.20261104.v7",
    "budget_reference": {
        "path": (
            "/Users/keith1117/Documents/TopoLab-data/p17-m2-source-binding-v1-"
            "20261103T173800Z/NEW-final-permission-remedy-and-continuation-v33"
            ".json"
        ),
        "sha256": "78de11fcc8a47fbbe32accd5958471d0c763db202cbb7f74d343f360ba453641",
    },
    "started_ms": 1793823217118,
    "deadline_ms": 1793837617118,
    "global_deadline_ms": 1793869680000,
    "original_author_start_ms": 1793727480000,
    "old_cumulative_author_cap_seconds": 122400,
    "new_additional_Root_author_seconds": 19800,
    "new_cumulative_Root_author_cap_seconds": 142200,
    "original_outer_deadline_ms": 1793878680000,
    "old_failed_metadata8_reference": {
        "path": (
            "/Users/keith1117/Documents/TopoLab-data/p17-m2-source-binding-v1-"
            "20261103T173800Z/independent/V31-metadata8-auto-approval-timeout-"
            "STOP-v1.json"
        ),
        "sha256": "5ce2b6c849128b2bcd3b5efbcfa903a95b33296f69e25b4feca971f08d6507e0",
    },
    "old_actual_costs_counters_waits_preserved": True,
    "no_old_Actor8_retry_or_reset": True,
    "own_future_return": "NOT_CLAIMED",
}


@pytest.mark.parametrize(
    "fault",
    [None, "raw", "phase", "cumulative", "source", "deadline", "return", "old-stop", "review"],
)
def test_v33_raw_registration_budget_and_retained_service_stop(monkeypatch, tmp_path, fault):
    import json
    from copy import deepcopy

    subject = module("p17_m2_source_binding_recovery").for_identity(RECOVERY)
    policy = json.loads(subject.AUTHORITY.read_bytes())
    values = {
        "budget": deepcopy(V33_GRANT),
        "software_activation": deepcopy(V33_ACTIVATION),
        "registration_actual": {
            "author": "/root",
            "activation_starts_at": 1793823217118,
            "event": {
                "tool": "exec_command",
                "requested_ms": 1793823216941,
                "returned_ms": 1793823217118,
                "result": {"exit_code": 0},
            },
        },
        "budget_review": {
            "author": "/root/permission_remedy_reader_v1",
            "status": "PASS_budgetonly",
            "arithmetic": {"integer_headroom_ms": 802882, "primary_sum_seconds": 45660},
        },
        "prior_failed_permission": {
            "status": "STOP_PRE_PROCESS_AUTO_APPROVAL_REVIEW_TIMEOUT_NATIVE_NOT_EXECUTED",
            "Native_SUP_processes": 0,
            "REC_invocations": 0,
            "actor_remaining_at_that_observation_ms": 167267,
            "frozen_FULL_and_return_reserve_ms": 180000,
            "retry_not_executed_because_remaining_less_than_frozen_suffix": True,
        },
    }
    if fault == "phase":
        values["budget"]["NEW_primary_phase_maxima_seconds"]["formal_metadata"] += 1
    if fault == "cumulative":
        values["budget"]["NEW_cumulative_Root_author_span_cap_seconds"] += 1
    if fault == "source":
        values["budget"]["source_and_science_UNCHANGED"]["new_Original_registration_reads"] = 1
    if fault == "deadline":
        values["software_activation"]["deadline_ms"] += 1
    if fault == "return":
        values["registration_actual"]["event"]["returned_ms"] += 1
    if fault == "old-stop":
        values["prior_failed_permission"]["status"] = "PASS"
    if fault == "review":
        values["budget_review"]["status"] = "PASS_forged"

    # Honest raw identities remain coherent, so negative verdicts exercise the stated field.
    def pin(key):
        raw = subject.canonical(values[key])
        return {"path": str(tmp_path / (key + ".json")), "sha256": subject.sha(raw)}

    policy["prior_failed_permission"] = pin("prior_failed_permission")
    values["budget"]["failed_metadata8"].update(policy["prior_failed_permission"])
    values["software_activation"]["old_failed_metadata8_reference"] = policy[
        "prior_failed_permission"
    ]
    policy["budget"] = pin("budget")
    values["software_activation"]["budget_reference"] = policy["budget"]
    values["registration_actual"]["grant_sha256"] = policy["budget"]["sha256"]
    values["registration_actual"]["event"]["result"]["output"] = (
        str(len(subject.canonical(values["budget"]))) + " " + policy["budget"]["sha256"] + "\n"
    )
    captures = {}
    for key, value in values.items():
        policy[key] = pin(key)
        captures[key] = {
            "reference": policy[key],
            "raw": subject.canonical(value).decode(),
            "value": value,
        }
    monkeypatch.setattr(subject, "authority", lambda: policy)
    if fault == "raw":
        captures["budget"]["raw"] += " "
    if fault:
        with pytest.raises(ValueError):
            subject._captured_budget(captures)
    else:
        result = subject._captured_budget(captures)
        assert result["registration_actual"]["event"]["returned_ms"] == 1793823217118


@pytest.mark.parametrize("fault", [None, "author", "prefix", "late", "session", "no-escalation"])
def test_v33_permission_actual_raw_replay_before_actor(monkeypatch, fault):
    subject = module("p17_m2_source_binding_recovery").for_identity(RECOVERY)
    runtime = {"python": "/PUBLIC/python"}
    argv = [
        runtime["python"],
        "-I",
        str(REPO / "scripts/p17_m2_source_binding_recovery_v7.py"),
        "--help",
    ]
    request = {
        "cmd": subject.load("p17_m2_source_binding").literal_command(argv),
        "workdir": str(REPO),
        "sandbox_permissions": "require_escalated",
        "prefix_rule": [
            "env",
            "OMP_NUM_THREADS=1",
            "OPENBLAS_NUM_THREADS=1",
            "MKL_NUM_THREADS=1",
            "VECLIB_MAXIMUM_THREADS=1",
            "NUMEXPR_NUM_THREADS=1",
            *argv[:3],
        ],
    }
    packet = {
        "schema": "topolab.v2.m2-strict-source-binding.actual-call.v1",
        "author": "/root/permission_remedy_reader_v1",
        "argv": argv,
        "request": request,
        "responses": [
            {
                "tool": "exec_command",
                "arguments": request,
                "requested_ms": 1793823217120,
                "returned_ms": 1793823217121,
                "result": {"exit_code": 0, "output": "usage: recovery\n"},
            }
        ],
    }
    if fault == "author":
        packet["author"] = "/root/binding_route_independent_v1"
    if fault == "prefix":
        request["prefix_rule"] = ["env"]
    if fault == "late":
        packet["responses"][0]["returned_ms"] = 1793823217123
    if fault == "session":
        packet["responses"][0]["result"]["session_id"] = 3
    if fault == "no-escalation":
        request["sandbox_permissions"] = "use_default"
    raw = subject.canonical(packet)
    capture = {
        "reference": {
            "path": subject.authority()["permission_preflight"]["packet_paths"]["public"],
            "sha256": subject.sha(raw),
        },
        "raw": raw.decode(),
        "value": packet,
    }
    if fault:
        with pytest.raises(ValueError):
            subject.checked_permission(capture, runtime, before_ms=1793823217122)
    else:
        assert subject.checked_permission(capture, runtime, before_ms=1793823217122) == (
            1793823217120,
            1793823217121,
        )


@pytest.mark.parametrize(
    "name,identity",
    [
        (
            "topolab-public-binding-certificate-recovery-v8",
            "topolab.v2.p17-binding-certificate-recovery.20261104.v6",
        ),
        ("topolab-public-binding-certificate-recovery-v9", RECOVERY),
        (
            "topolab-public-binding-certificate-recovery-v9",
            "topolab.v2.p17-binding-certificate-recovery.20261104.v8",
        ),
        ("binding-formal-v3-certificate-recovery-v7", RECOVERY),
    ],
)
def test_exact_metadata_plan_ingress_selects_fixed_profile(monkeypatch, name, identity):
    core = module("p17_m2_source_binding")
    recovery = core.load("p17_m2_source_binding_recovery")
    path = Path("/PUBLIC_NOT_OPENED") / name / "plan.json"
    context = {"context": {"execution_identity": identity}}
    raw = core.canonical(context)
    pin = core.sha(raw)
    reads = []

    def read_metadata(actual_path, limit, *, expected):
        assert name == "topolab-public-binding-certificate-recovery-v9"
        assert (actual_path, limit, expected) == (path, 16 * 1024**2, pin)
        reads.append(actual_path)
        return context, raw

    class Selected:
        def __init__(self, selected_identity):
            self.identity = selected_identity

        def for_identity(self, selected_identity):
            return Selected(selected_identity)

        def load_plan(self, path, pin):
            raise RuntimeError("selected " + self.identity)

    def select(actual):
        return Selected(actual)

    monkeypatch.setattr(core, "read_metadata", read_metadata)
    monkeypatch.setattr(recovery, "for_identity", select)
    with pytest.raises(RuntimeError, match="selected " + identity):
        core.load_plan(path, pin)
    assert reads == ([path] if name.endswith("recovery-v9") else [])


def test_v33_permission_path_rejected_before_any_metadata_read(monkeypatch):
    subject = module('p17_m2_source_binding_recovery').for_identity(RECOVERY)
    def forbidden(*args, **kwargs):
        pytest.fail('unregistered permission path reached metadata IO')
    monkeypatch.setattr(subject, 'capture_ref', forbidden)
    with pytest.raises(ValueError, match='literal permission packet path required'):
        subject.prepare('public', 1, permission_packet='/PUBLIC_UNREGISTERED/packet.json',
                        permission_packet_sha='a'*64)
