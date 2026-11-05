"""Isolated execution profiles for the prospective V27 input continuation.

Only explicit new identities/literals select these private module instances.
Historical modules and protocol bytes retain their original defaults and clocks.
"""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECOVERY = "topolab.v2.p17-binding-certificate-recovery.20261104.v5"
INPUT = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v3"
PREFIX = "topolab-public-registered3-source-acquisition-"
PARENT = "/Users/keith1117/Library/Application Support/TopoLab-custody/"
GENERATIONS = (
    PARENT + "p17-m2-local-input-version-v10-strict-binding-20261104",
    PARENT + "p17-m2-local-input-version-v11-strict-binding-remedy-20261104",
)
RECOVERY_PROTOCOL = "docs/planning/p17_m2_source_binding_certificate_recovery_v5_protocol.json"
INPUT_PROTOCOL = "docs/planning/p17_m2_registered_input_v3_protocol.json"
KINDS = {
    "control": "p17_m2_source_acquisition_control",
    "independent": "p17_m2_source_acquisition_independent",
    "registered": "p17_m2_registered_input",
    "recovery": "p17_m2_source_binding_recovery",
}


# Four frozen configurations only; this is not an extension registry.
V31_RECOVERY = "topolab.v2.p17-binding-certificate-recovery.20261104.v6"
V31_INPUT = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v4"
V33_RECOVERY = "topolab.v2.p17-binding-certificate-recovery.20261104.v7"
V33_INPUT = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v5"
V35_RECOVERY = "topolab.v2.p17-binding-certificate-recovery.20261104.v8"
V35_INPUT = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v6"
CONFIGS = {
    INPUT: {
        "input": INPUT,
        "recovery": RECOVERY,
        "prefix": PREFIX,
        "generations": GENERATIONS,
        "recovery_protocol": RECOVERY_PROTOCOL,
        "input_protocol": INPUT_PROTOCOL,
        "schema": "topolab.v2.m2-registered-source-acquisition-authority.v3",
        "recovery_entry": "p17_m2_source_binding_recovery_v5.py",
        "input_entry": "p17_m2_registered_input_v3.py",
        "cache_suffix": "_prospective_v27",
        "global_deadline_ms": 1793828280000,
        "public_attempts_total": 4,
        "public_graphs_max": 1,
        "budget": {
            "path": (
                "/Users/keith1117/Documents/TopoLab-data/"
                "p17-m2-source-binding-v1-20261103T173800Z/"
                "NEW-unstarted-publication-continuation-v27.json"
            ),
            "sha256": "37f0002eb2d80c9dc9dcce66fa0442b6538dd5ea4009f2c15484961b10edf9a6",
        },
    },
    V31_INPUT: {
        "input": V31_INPUT,
        "recovery": V31_RECOVERY,
        "prefix": "topolab-public-registered4-source-acquisition-",
        "generations": (
            PARENT + "p17-m2-local-input-version-v12-strict-binding-20261104",
            PARENT + "p17-m2-local-input-version-v13-strict-binding-remedy-20261104",
        ),
        "recovery_protocol": (
            "docs/planning/p17_m2_source_binding_certificate_recovery_v6_protocol.json"
        ),
        "input_protocol": "docs/planning/p17_m2_registered_input_v4_protocol.json",
        "schema": "topolab.v2.m2-registered-source-acquisition-authority.v4",
        "recovery_entry": "p17_m2_source_binding_recovery_v6.py",
        "input_entry": "p17_m2_registered_input_v4.py",
        "cache_suffix": "_prospective_v31",
        "global_deadline_ms": 1793849880000,
        "public_attempts_total": 6,
        "public_graphs_max": 2,
        "budget": {
            "path": (
                "/Users/keith1117/Documents/TopoLab-data/"
                "p17-m2-source-binding-v1-20261103T173800Z/"
                "NEW-unstarted-continuous-input-and-fixed-science-v31.json"
            ),
            "sha256": "aa591ff55c5b00a57efc6bf671804fd9241b0780baaddbbbd432da33887ef821",
        },
    },
    V33_INPUT: {
        "input": "topolab.v2.p17-m2-registered-source-acquisition.20261104.v5",
        "recovery": "topolab.v2.p17-binding-certificate-recovery.20261104.v7",
        "prefix": "topolab-public-registered5-source-acquisition-",
        "generations": (
            PARENT + "p17-m2-local-input-version-v14-strict-binding-20261104",
            PARENT + "p17-m2-local-input-version-v15-strict-binding-remedy-20261104",
        ),
        "recovery_protocol": (
            "docs/planning/p17_m2_source_binding_certificate_recovery_v7_protocol.json"
        ),
        "input_protocol": "docs/planning/p17_m2_registered_input_v5_protocol.json",
        "schema": "topolab.v2.m2-registered-source-acquisition-authority.v5",
        "recovery_entry": "p17_m2_source_binding_recovery_v7.py",
        "input_entry": "p17_m2_registered_input_v5.py",
        "cache_suffix": "_prospective_v33",
        "global_deadline_ms": 1793869680000,
        "public_attempts_total": 7,
        "public_graphs_max": 1,
        "budget": {
            "path": (
                "/Users/keith1117/Documents/TopoLab-data/"
                "p17-m2-source-binding-v1-20261103T173800Z/"
                "NEW-final-permission-remedy-and-continuation-v33.json"
            ),
            "sha256": "78de11fcc8a47fbbe32accd5958471d0c763db202cbb7f74d343f360ba453641",
        },
    },
    V35_INPUT: {
        "input": "topolab.v2.p17-m2-registered-source-acquisition.20261104.v6",
        "recovery": "topolab.v2.p17-binding-certificate-recovery.20261104.v8",
        "prefix": "topolab-public-registered6-source-acquisition-",
        "generations": (
            PARENT + "p17-m2-local-input-version-v16-strict-binding-20261104",
            PARENT + "p17-m2-local-input-version-v17-strict-binding-remedy-20261104",
        ),
        "recovery_protocol": (
            "docs/planning/p17_m2_source_binding_certificate_recovery_v8_protocol.json"
        ),
        "input_protocol": "docs/planning/p17_m2_registered_input_v6_protocol.json",
        "schema": "topolab.v2.m2-registered-source-acquisition-authority.v6",
        "recovery_entry": "p17_m2_source_binding_recovery_v8.py",
        "input_entry": "p17_m2_registered_input_v6.py",
        "cache_suffix": "_prospective_v35",
        "global_deadline_ms": 1793878200000,
        "public_attempts_total": 7,
        "public_graphs_max": 1,
        "budget": {
            "path": (
                "/Users/keith1117/Documents/TopoLab-data/"
                "p17-m2-source-binding-v1-20261103T173800Z/"
                "NEW-unstarted-clock-fixture-and-continuous-input-v35.json"
            ),
            "sha256": "74331d05644d37e6f0f967b2094b063e225c8b9325f2f9b60d936c0603cd3544",
        },
    },
}
INPUT_IDENTITIES = tuple(CONFIGS)
RECOVERY_IDENTITIES = tuple(value["recovery"] for value in CONFIGS.values())


def config(identity):
    for value in CONFIGS.values():
        if identity in (value["input"], value["recovery"]):
            return value
    raise ValueError("continuation: unregistered exact identity")


def config_for_root(root):
    for value in CONFIGS.values():
        if str(root) in value["generations"] or Path(root).name.startswith(value["prefix"]):
            return value
    return None


def is_root(root):
    return config_for_root(root) is not None


def profile(kind, identity=INPUT):
    """Select one fixed profile; never mutate historical or other profile modules."""
    selected = config(identity)
    name = KINDS[kind]
    key = name + selected["cache_suffix"]
    if key in sys.modules:
        return sys.modules[key]
    path = REPO / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(key, path)
    if spec is None or spec.loader is None:
        raise ValueError("continuation: published implementation unavailable")
    result = importlib.util.module_from_spec(spec)
    sys.modules[key] = result
    try:
        spec.loader.exec_module(result)
        result.CONTINUATION_INPUT = selected["input"]
        result.CONTINUATION_CONFIG = selected
        result.GLOBAL_DEADLINE_MS = selected["global_deadline_ms"]
        if kind == "recovery":
            result.IDENTITY = selected["recovery"]
            result.PROTOCOL_PATH = selected["recovery_protocol"]
            result.AUTHORITY = REPO / result.PROTOCOL_PATH
            result.CLI_ENTRY = selected["recovery_entry"]
        elif kind == "registered":
            result.IDENTITY = selected["input"]
            result.PROTOCOL = selected["input_protocol"]
            result.SCHEMA = selected["schema"]
            result.PUBLIC_PREFIX = selected["prefix"]
            result.GENERATIONS = selected["generations"]
            result.CLI_ENTRY = selected["input_entry"]
            result.GLOBAL_DEADLINE_MS = selected["global_deadline_ms"]
            result.PUBLIC_ATTEMPTS_TOTAL = selected["public_attempts_total"]
            result.PUBLIC_GRAPHS_MAX = selected["public_graphs_max"]
            result.NEW_BUDGET_REFERENCE = selected["budget"]
            result.control = profile("control", identity)
        else:
            result.REGISTERED_IDENTITY = selected["input"]
            result.REGISTERED_PROTOCOL = selected["input_protocol"]
            result.REGISTERED_SCHEMA = selected["schema"]
            if kind == "control":
                result.REGISTERED_PUBLIC_PREFIX = selected["prefix"]
                result.REGISTERED_GENERATIONS = selected["generations"]
            else:
                result.REGISTERED_PREFIX = selected["prefix"]
        return result
    except BaseException:
        sys.modules.pop(key, None)
        raise


def budget_keys(identity):
    if identity == V35_RECOVERY:
        return ("budget", "budget_review", "software_activation", "registration_actual",
                "independent_author_clock")
    if identity == V33_RECOVERY:
        return (
            "budget",
            "budget_review",
            "software_activation",
            "registration_actual",
            "prior_failed_permission",
        )
    keys = (
        "budget",
        "budget_review",
        "software_activation",
        "registration_actual",
        "prior_failed_metadata_closure",
        "prior_failed_metadata_closure_actual",
        "prior_failed_publication",
    )
    return keys + (("prior_failed_continuation",) if identity == V31_RECOVERY else ())


def captured_budget(module, captures):
    """Replay raw preregistration, actual return, finite caps and failed-old seal."""
    if module.IDENTITY == V35_RECOVERY:
        return captured_v35_budget(module, captures)
    if module.IDENTITY == V33_RECOVERY:
        return captured_v33_budget(module, captures)
    if module.IDENTITY == V31_RECOVERY:
        return captured_v31_budget(module, captures)
    policy = module.authority()
    keys = (
        "budget",
        "budget_review",
        "software_activation",
        "registration_actual",
        "prior_failed_metadata_closure",
        "prior_failed_metadata_closure_actual",
        "prior_failed_publication",
    )
    module.need(set(captures) == set(keys), "complete captured V27 budget required")
    values = {}
    for key in keys:
        module.need(captures[key]["reference"] == policy[key], "V27 budget reference differs")
        values[key] = module.captured_value(captures[key])
    budget, review, activation = (
        values[k] for k in ("budget", "budget_review", "software_activation")
    )
    module.need(
        budget.get("schema")
        == ("topolab.owner.NEW-prospective-postpublication-input-continuation.v27")
        and budget.get("no_old_allowance_reopened") is True
        and budget.get("global_deadline_ms_UNCHANGED") == 1793828280000
        and budget.get("NEW_root_independent_each")
        == {
            "software_and_publication_seconds": 7200,
            "metadata_recovery_seconds": 1200,
            "formal_input_seconds": 4500,
            "input_result_seconds": 1800,
            "metadata_dispatches": 320,
        }
        and budget.get("NEW_formal", {}).get("total_read_cap") == 2392
        and budget["NEW_formal"].get("new_registration_Original_reads") == 0
        and budget["NEW_formal"].get("new_registration_Foundation_helpers") == 0
        and budget["NEW_formal"].get("native_RSS_bytes") == 4294967296
        and budget["NEW_public"].get("coordination_seconds") == 240,
        "V27 finite scope/resource budget differs",
    )
    module.need(
        review.get("author") == policy["actors"]["independent"]
        and str(review.get("status", "")).startswith("PASS_"),
        "independent V27 budget review missing",
    )
    registration = values["registration_actual"]
    event = registration.get("event", {})
    terminal = event.get("result", {})
    module.need(
        registration.get("author") == policy["actors"]["producer"]
        and event.get("tool") == "exec_command"
        and type(event.get("requested_ms")) is int
        and event["requested_ms"] <= event.get("returned_ms", -1)
        and terminal.get("exit_code") == 0
        and terminal.get("session_id") is None
        and terminal.get("output")
        == str(len(captures["budget"]["raw"].encode())) + " " + policy["budget"]["sha256"] + "\n"
        and registration.get("grant_sha256") == policy["budget"]["sha256"]
        and registration.get("activation_starts_at") == event["returned_ms"],
        "V27 original registration return differs",
    )
    module.need(
        activation.get("schema")
        == ("topolab.NEW-prospective-input-continuation.software-activation.v1")
        and activation.get("execution_identity") == RECOVERY
        and activation.get("budget_reference") == policy["budget"]
        and activation.get("started_ms")
        == event["returned_ms"]
        == policy["limits"]["software_start_ms"]
        and activation.get("deadline_ms")
        == event["returned_ms"] + 7200000
        == policy["limits"]["software_deadline_ms"]
        and activation.get("global_deadline_ms") == 1793828280000
        and activation.get("no_old_allowance_reopened") is True
        and activation.get("old_deadline_ms") == 1793803589352,
        "V27 true prospective activation differs",
    )
    closed = values["prior_failed_publication"]
    module.need(
        closed.get("status") == ("CLOSED_FAILED_PUBLICATION_MAIN_CI_NOT_READY_FORMAL_UNLAUNCHED")
        and closed.get("hard_deadline_ms") == 1793803589352,
        "V22 publication failure cannot become PASS",
    )
    return values


def captured_v31_budget(module, captures):
    """Replay the real prospective registration and cumulative, nonreset clocks."""
    policy = module.authority()
    module.need(
        isinstance(captures, dict) and set(captures) == set(budget_keys(V31_RECOVERY)),
        "complete captured V31 budget required",
    )
    values = {}
    for key in budget_keys(V31_RECOVERY):
        module.need(captures[key]["reference"] == policy[key], "V31 budget reference differs")
        values[key] = module.captured_value(captures[key])
    budget, activation = values["budget"], values["software_activation"]
    phases = {
        "software_and_protected_publication": 10800,
        "formal_metadata_and_result": 1200,
        "primary_input_formal_and_result": 6300,
        "scientific_contract_and_protected_publication": 7200,
        "original_B_C": 14760,
        "final_retention_filing_actual_return": 1800,
    }
    calls = {
        "software_publication": 512,
        "formal_metadata": 64,
        "input_all_attempts": 512,
        "scientific_contract_publication": 256,
        "scientific_B_C_orchestration": 512,
        "final_retention_filing": 128,
        "total": 1984,
    }
    module.need(
        budget.get("schema") == "topolab.owner.NEW-unstarted-continuous-input-and-fixed-science.v31"
        and budget.get("NEW_each_phase_seconds") == phases
        and budget.get("sum_primary_phase_maxima_seconds") == sum(phases.values()) == 42060
        and budget.get("NEW_each_metadata_calls") == calls
        and sum(value for key, value in calls.items() if key != "total") == calls["total"]
        and budget.get("no_elapsed_or_fee_counter_reset") is True
        and budget.get("all_old_unused_allowances_closed_no_transfer") is True,
        "V31 finite phase/call budgets differ",
    )
    start = budget.get("old_original_author_start_ms")
    module.need(
        type(start) is int
        and start == 1793727480000
        and budget.get("old_original_each_author_cap_seconds100800_retained") is True
        and budget.get("NEW_additional_author_seconds_each") == 21600
        and budget.get("NEW_cumulative_each_author_span_cap_seconds") == 100800 + 21600
        and start + (100800 + 21600) * 1000
        == budget.get("NEW_root_independent_hard_deadline_ms")
        == policy["limits"]["global_deadline_ms"]
        == 1793849880000
        and budget.get("original_outer_span_seconds151200_UNCHANGED") is True
        and start + 151200000
        == budget.get("original_outer_deadline_ms_UNCHANGED")
        == 1793878680000,
        "V31 cumulative author/outer clocks differ",
    )
    source = budget.get("source_boundary", {})
    execution = budget.get("NEW_execution", {})
    module.need(
        source.get("new_Original_registration_reads") == 0
        and source.get("new_Foundation_helpers") == 0
        and source.get("formal_whitelist_files_each_author_attempt") == 598
        and source.get("each_file_reads_each_author_attempt") == 1
        and source.get("formal_all_attempts_Original_read_cap") == 2392
        and source.get("whole_Original_read_cap2484_UNCHANGED") is True
        and source.get("all_old_actual_registration_consumption_carried") is True
        and execution.get("metadata_identity") == V31_RECOVERY
        and execution.get("input_identity") == V31_INPUT
        and execution.get("public_metadata_calls") == execution.get("formal_metadata_calls") == 1
        and execution.get("public_metadata_FULL") == execution.get("formal_metadata_FULL") == 120
        and execution.get("public_six_role_cohorts_max")
        == execution.get("formal_six_role_cohorts_max")
        == 2
        and execution.get("public_FULL_each") == execution.get("formal_FULL_each") == 3780
        and execution.get("coordination_seconds_UNCHANGED") == 240
        and execution.get("native_RSS_bytes_UNCHANGED") == 4294967296
        and execution.get("counts_UNCHANGED")
        == {"metadata": 40, "payload": 558, "version_members": 1071},
        "V31 source/resource limits differ",
    )
    review = values["budget_review"]
    module.need(
        review.get("author") == policy["actors"]["independent"]
        and str(review.get("status", "")).startswith("PASS_"),
        "independent V31 budget review missing",
    )
    registration = values["registration_actual"]
    event = registration.get("event", {})
    terminal = event.get("result", {})
    returned = event.get("returned_ms")
    module.need(
        registration.get("author") == policy["actors"]["producer"]
        and event.get("tool") == "exec_command"
        and type(event.get("requested_ms")) is int
        and type(returned) is int
        and event["requested_ms"] <= returned
        and terminal.get("exit_code") == 0
        and terminal.get("session_id") is None
        and terminal.get("output")
        == str(len(captures["budget"]["raw"].encode())) + " " + policy["budget"]["sha256"] + "\n"
        and registration.get("grant_sha256") == policy["budget"]["sha256"]
        and registration.get("activation_starts_at") == returned,
        "V31 original registration return differs",
    )
    module.need(
        activation.get("schema") == "topolab.NEW-continuous-input.software-activation.v1"
        and activation.get("execution_identity") == V31_RECOVERY
        and activation.get("budget_reference") == policy["budget"]
        and activation.get("started_ms") == returned == policy["limits"]["software_start_ms"]
        and activation.get("deadline_ms")
        == returned + 10800000
        == policy["limits"]["software_deadline_ms"]
        and activation.get("global_deadline_ms") == 1793849880000
        and activation.get("original_author_start_ms") == start
        and activation.get("old_original_author_cap_seconds") == 100800
        and activation.get("additional_author_seconds") == 21600
        and activation.get("new_cumulative_author_span_cap_seconds") == 122400
        and activation.get("original_outer_deadline_ms_UNCHANGED") == 1793878680000
        and activation.get("no_counter_reset_or_old_allowance_transfer") is True
        and returned + 42060000 <= 1793849880000,
        "V31 true prospective activation or complete future suffix differs",
    )
    closed = values["prior_failed_continuation"]
    module.need(
        policy["prior_failed_continuation"]
        == budget.get("old_failure_reference")
        == activation.get("old_failed_reference")
        and str(closed.get("status", "")).startswith("CLOSED_")
        and "FAIL" in str(closed.get("status", "")),
        "V27 failure must remain closed",
    )
    module.need(
        values["prior_failed_publication"].get("status")
        == "CLOSED_FAILED_PUBLICATION_MAIN_CI_NOT_READY_FORMAL_UNLAUNCHED",
        "V22 publication failure cannot become PASS",
    )
    return values


def captured_v33_budget(module, captures):
    """Replay exact V33 raw authority, prospective return, and retained service STOP."""
    policy = module.authority()
    keys = budget_keys(V33_RECOVERY)
    module.need(
        isinstance(captures, dict) and set(captures) == set(keys),
        "complete captured V33 budget required",
    )
    values = {}
    for key in keys:
        module.need(captures[key]["reference"] == policy[key], "V33 reference differs")
        values[key] = module.captured_value(captures[key])
    budget, review, activation, registration, stopped = (values[key] for key in keys)
    phases = {
        "permission_remedy_software_review_publication_public": 14400,
        "formal_metadata": 1200,
        "primary_input_formal_and_result": 6300,
        "scientific_contract_and_publication": 7200,
        "B_C_original": 14760,
        "final_actual_return_retention": 1800,
    }
    calls = {
        "software_publication": 512,
        "formal_metadata": 64,
        "input_all_attempts": 512,
        "scientific_contract_publication": 256,
        "B_C": 512,
        "final_filing": 128,
        "total": 1984,
    }
    module.need(
        budget.get("schema") == "topolab.owner.NEW-final-permission-remedy-and-continuation.v33"
        and budget.get("NEW_primary_phase_maxima_seconds") == phases
        and budget.get("sum_primary_maxima_seconds") == sum(phases.values()) == 45660
        and budget.get("NEW_Root_metadata_calls") == calls
        and sum(v for k, v in calls.items() if k != "total") == 1984
        and budget.get("NEW_global_deadline_ms")
        == policy["limits"]["global_deadline_ms"]
        == 1793869680000
        and budget.get("original_author_start_ms") == 1793727480000
        and budget.get("old_cumulative_author_span_cap_seconds122400_retained") is True
        and budget.get("NEW_additional_Root_author_seconds") == 19800
        and budget.get("NEW_cumulative_Root_author_span_cap_seconds") == 122400 + 19800 == 142200
        and 1793727480000 + 142200000 == 1793869680000
        and budget.get("original_outer_deadline_ms_UNCHANGED") == 1793878680000
        and budget.get("original_outer_span151200_UNCHANGED") is True
        and budget.get("identities") == {"metadata": V33_RECOVERY, "input": V33_INPUT},
        "V33 finite clocks/calls/identities differ",
    )
    source = budget.get("source_and_science_UNCHANGED", {})
    expected = {
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
    }
    module.need(
        source == expected
        and budget.get("NEW_named_NATIVE_FULL")
        == {
            "metadata_public9_once": 120,
            "public_source7_once": 3780,
            "formal_metadata7_once": 120,
            "formal_input_two_attempts": 7560,
            "B_once": 180,
            "C_once14580": True,
            "total_named": 26340,
        },
        "V33 source/resource caps differ",
    )
    selected = config(V33_INPUT)
    module.need(
        budget.get("NEW_independent", {}).get("author") == "/root/permission_remedy_reader_v1"
        and budget["NEW_independent"].get("metadata_calls") == 1984
        and budget["NEW_independent"].get("wall_cap_seconds") == 45660
        and budget["NEW_independent"].get("global_deadline_ms") == 1793869680000
        and budget["NEW_independent"].get("logical_GitHub_GET") == 128
        and budget.get("NEW_Root_logical_GitHub_GET") == 256
        and budget.get("NEW_engineer")
        == {
            "author": "/root/permission_remedy_engineer_v1",
            "seconds_including_startup_filing_actual_return": 1800,
            "calls": 64,
        }
        and budget.get("NEW_reviewers")
        == {
            "authors": [
                "/root/permission_remedy_standards_v1", "/root/permission_remedy_spec_v1"
            ],
            "seconds_each_including_actual_return": 900,
            "calls_each": 32,
        }
        and budget.get("targets")
        == {
            "parent": PARENT.rstrip("/"),
            "public_metadata": policy["targets"]["public"][0],
            "formal_metadata": policy["targets"]["formal"][0],
            "public_source": (
                "/private/tmp/topolab-public-registered5-source-acquisition-20261104-v7"),
            "formal": [Path(root).name for root in selected["generations"]],
            "backup_suffix": "-independent-backup",
            "all_formal_unprobed": True,
            "no_old_failed_lease_unlock_or_scene_reuse": True,
        },
        "V33 exact authors/targets/caps differ",
    )
    event = registration.get("event", {})
    result = event.get("result", {})
    returned = event.get("returned_ms")
    module.need(
        registration.get("author") == "/root"
        and event.get("tool") == "exec_command"
        and type(event.get("requested_ms")) is int
        and type(returned) is int
        and event["requested_ms"] <= returned == 1793823217118
        and result.get("exit_code") == 0
        and result.get("session_id") is None
        and result.get("output")
        == str(len(captures["budget"]["raw"].encode())) + " " + policy["budget"]["sha256"] + "\n"
        and registration.get("grant_sha256") == policy["budget"]["sha256"]
        and registration.get("activation_starts_at") == returned,
        "V33 original registration return differs",
    )
    module.need(
        activation.get("schema") == "topolab.NEW-permission-remedy.software-activation.v1"
        and activation.get("execution_identity") == V33_RECOVERY
        and activation.get("budget_reference") == policy["budget"]
        and activation.get("started_ms") == returned == policy["limits"]["software_start_ms"]
        and activation.get("deadline_ms")
        == returned + 14400000
        == policy["limits"]["software_deadline_ms"]
        and activation.get("global_deadline_ms") == 1793869680000
        and activation.get("original_author_start_ms") == 1793727480000
        and activation.get("old_cumulative_author_cap_seconds") == 122400
        and activation.get("new_additional_Root_author_seconds") == 19800
        and activation.get("new_cumulative_Root_author_cap_seconds") == 142200
        and activation.get("original_outer_deadline_ms") == 1793878680000
        and returned + 45660000 <= 1793869680000
        and 1793869680000 - returned - 45660000 == 802882,
        "V33 prospective activation/full suffix differs",
    )
    module.need(
        review.get("status") == "PASS_budgetonly"
        and review.get("author")
        == policy["actors"]["independent"]
        == "/root/permission_remedy_reader_v1"
        and review.get("arithmetic", {}).get("integer_headroom_ms") == 802882
        and review["arithmetic"].get("primary_sum_seconds") == 45660,
        "V33 exact independent budget-only review differs",
    )
    pin = policy["prior_failed_permission"]
    module.need(
        budget.get("failed_metadata8", {}).get("path") == pin["path"]
        and budget["failed_metadata8"].get("sha256") == pin["sha256"]
        and activation.get("old_failed_metadata8_reference") == pin
        and stopped.get("status")
        == "STOP_PRE_PROCESS_AUTO_APPROVAL_REVIEW_TIMEOUT_NATIVE_NOT_EXECUTED"
        and stopped.get("Native_SUP_processes") == stopped.get("REC_invocations") == 0
        and stopped.get("actor_remaining_at_that_observation_ms") == 167267
        and stopped.get("frozen_FULL_and_return_reserve_ms") == 180000
        and stopped.get("retry_not_executed_because_remaining_less_than_frozen_suffix") is True,
        "V33 old permission STOP must remain closed",
    )
    return values


def captured_v35_budget(module, captures):
    """Replay the finite V35 replacement grant and the original registration return."""
    policy = module.authority()
    keys = budget_keys(V35_RECOVERY)
    module.need(isinstance(captures, dict) and set(captures) == set(keys),
                "complete captured V35 budget required")
    values = {}
    for key in keys:
        module.need(captures[key]["reference"] == policy[key], "V35 reference differs")
        values[key] = module.captured_value(captures[key])
    budget, review, activation, registration, clock = (values[key] for key in keys)
    phases = {
        "software_review_publication_public": 14400, "formal_metadata": 1200,
        "primary_input_formal_and_result": 6300, "scientific_contract_publication": 7200,
        "B_C_original": 14760, "final_actual_return_retention": 1800,
    }
    calls = {"software_publication": 512, "formal_metadata": 64,
             "input_all_attempts": 512, "scientific_contract_publication": 256,
             "B_C": 512, "final_filing": 128, "total": 1984}
    module.need(
        budget.get("schema") == "topolab.owner.NEW-unstarted-clock-fixture-and-continuous-input.v35"
        and budget.get("NEW_primary_phase_maxima_seconds") == phases
        and budget.get("sum_primary_maxima_seconds") == 45660
        and budget.get("NEW_Root_metadata_calls") == calls
        and budget.get("NEW_global_deadline_ms")
        == policy["limits"]["global_deadline_ms"] == 1793878200000
        and budget.get("original_author_start_ms") == 1793727480000
        and budget.get("old_cumulative_Root_author_seconds142200_retained") is True
        and budget.get("NEW_additional_Root_author_seconds") == 8520
        and budget.get("NEW_cumulative_Root_author_seconds") == 150720
        and budget.get("original_outer_deadline_ms_UNCHANGED") == 1793878680000
        and budget.get("original_outer151200_UNCHANGED") is True
        and budget.get("identities") == {"metadata": V35_RECOVERY, "input": V35_INPUT},
        "V35 finite clocks/calls/identities differ")
    source = {"new_Original_registration_reads": 0, "new_Foundation_helpers": 0,
              "files_once_each_author_attempt": 598, "all_formal_Original_reads2392": True,
              "whole_Original_reads2484_helpers138": True,
              "metadata40_payload558_version1071": True,
              "source_coordination_seconds240": True, "native_RSS4294967296": True,
              "fixed_models_panel_quality_speed_windows_and_resources": True,
              "no_scientific_retry_search": True, "same_issuer_two_fix_rounds_not_reopened": True}
    module.need(
        budget.get("source_and_science_UNCHANGED") == source
        and budget.get("NEW_named_Native_FULL") == {"metadata_public9_once": 120,
            "public_source7_once": 3780, "formal_metadata8_once": 120,
            "formal_input_two_attempts": 7560, "B_once": 180, "C_once": 14580, "total": 26340}
        and budget.get("NEW_independent") == {"author": "/root/ci_clock_reader_v1",
            "wall_cap_seconds": 45660, "metadata_calls": 1984, "logical_GitHub_GET": 128,
            "global_deadline_ms": 1793878200000, "no_old_author_balance_reused": True}
        and budget.get("NEW_engineer") == {"author": "/root/ci_clock_engineer_v1",
            "seconds_including_startup_filing_actual_return": 1800, "calls": 64}
        and budget.get("NEW_reviewers") == {"authors": ["/root/ci_clock_standards_v1",
            "/root/ci_clock_spec_v1"], "seconds_each_including_actual_return": 900,
            "calls_each": 32}
        and budget.get("NEW_Root_logical_GitHub_GET") == 256
        and budget.get("NEW_CI_workflow_runs_max") == 12,
        "V35 exact source/resource/author caps differ")
    module.need(budget.get("ROOT_counter_base_before_registration") == 2062
        and budget.get("ROOT_collaboration_upper_base") == 42
        and budget.get("known_NEW_FULL_lower") == 254550
        and budget.get("NEW_software_full_campaigns") == [
            {"label": "R18_CLOCK_FIX_AND_NEW_UNSTARTED_PROFILE", "ordinal": 23,
             "Native_FULL_max": 100000, "UTC_seconds": 4200,
             "closing_suffix_seconds": 600, "calls": 1},
            {"label": "R19_ACTUAL_ACCEPTED_INPUT_SCIENTIFIC_CONTRACT", "ordinal": 24,
             "Native_FULL_max": 100000, "UTC_seconds": 4200,
             "closing_suffix_seconds": 600, "calls": 1,
             "condition": "Only after actual accepted full input; scientific contract/publication "
                          "phase must have complete actual suffix"}],
        "V35 original counters/fresh campaigns differ")
    selected = config(V35_INPUT)
    targets = budget.get("targets", {})
    module.need(targets.get("parent") == PARENT.rstrip("/")
        and targets.get("public_metadata") == policy["targets"]["public"][0]
        and targets.get("formal_metadata") == policy["targets"]["formal"][0]
        and targets.get("public_source")
        == "/private/tmp/topolab-public-registered6-source-acquisition-20261104-v7"
        and targets.get("formal") == [Path(root).name for root in selected["generations"]]
        and targets.get("backup_suffix") == "-independent-backup"
        and targets.get("all_formal_unprobed") is True
        and targets.get("no_old_failed_scene_or_HELD_lease_reuse") is True,
        "V35 exact fixed targets differ")
    event = registration.get("original", {})
    result = event.get("result", {})
    returned = event.get("returned_ms")
    output = {"path": "NEW-unstarted-clock-fixture-and-continuous-input-v35.json",
              "bytes": 7124, "sha256": policy["budget"]["sha256"],
              "software_deadline_ms": 1793844769237, "registered_headroom_ms": 2170763}
    module.need(registration.get("schema") == "topolab.NEW-V35.registration-original-actual.v1"
        and event.get("tool") == "exec_command"
        and event.get("requested_ms") == 1793830370327
        and returned == 1793830370485
        and result.get("exit_code") == 0 and result.get("session_id") is None
        and module.json.loads(result.get("output", "null")) == output
        and len(captures["budget"]["raw"].encode()) == 7124,
        "V35 original registration return differs")
    module.need(activation.get("schema") == "topolab.NEW-V35.software-activation.v1"
        and activation.get("author") == "/root"
        and activation.get("software_start_ms") == budget.get("registered_before_new_work_ms")
        == policy["limits"]["software_start_ms"] == 1793830369237
        and activation.get("registration_actual_return_ms") == returned
        and activation.get("software_deadline_ms")
        == policy["limits"]["software_deadline_ms"] == 1793844769237
        and activation.get("global_deadline_ms") == 1793878200000
        and activation.get("original_author_start_ms") == 1793727480000
        and activation.get("cumulative_Root_author_seconds") == 150720
        and activation.get("old_cumulative142200_retained") is True
        and activation.get("additional8520_not_reset") is True
        and activation.get("old_allocation_unused_closed_not_transferred") is True
        and activation.get("new_grant_sha256") == policy["budget"]["sha256"]
        and 1793878200000 - returned - 45660000 == 2169515,
        "V35 declared start/actual return/complete suffix differs")
    arithmetic = review.get("arithmetic", {})
    module.need(review.get("schema") == "topolab.independent.V35.budget-and-clock-review.v1"
        and review.get("status") == "PASS_budgetonly"
        and review.get("author") == policy["actors"]["independent"] == "/root/ci_clock_reader_v1"
        and arithmetic.get("sum_primary_seconds") == 45660
        and arithmetic.get("registration_headroom_after_all_primary_maxima_ms") == 2169515
        and arithmetic.get("software_start_ms") == 1793830369237
        and arithmetic.get("software_deadline_ms") == 1793844769237
        and review.get("no_old_budget_or_author_balance_reused") is True,
        "V35 independent budget/clock review differs")
    module.need(clock.get("schema")
        == "topolab.independent.V35.conservative-startup-clock-supplement.v1"
        and clock.get("author") == "/root/ci_clock_reader_v1"
        and clock.get("status") == "PASS_budgetonly_STRICTER_CLOCK"
        and clock.get("conservative_author_budget_start_ms") == 1793830369237
        and clock.get("effective_author_deadline_ms") == 1793876029237
        and clock.get("no_clock_reset_or_old_budget_transfer") is True
        and policy.get("independent_author_start_ms") == 1793830369237
        and policy.get("independent_author_deadline_ms") == 1793876029237,
        "V35 conservative independent author clock differs")
    failure = budget.get("failed_PR236", {})
    stopped = budget.get("old_unstarted_scopes_closed", {})
    module.need(failure.get("head") == "1efe58cf4fc877c6fda272b7610ae8bd4ee2436d"
        and failure.get("run") == 41915681708 and failure.get("quality_job") == 126874584970
        and failure.get("status") == "1 failed 3472 passed37skipped"
        and {"path": failure.get("log_path"), "sha256": failure.get("log_sha256")}
        == policy["prior_failed_CI"]
        and all(stopped.get(key) is True for key in ("metadata_public9_Native0",
            "formal_metadata7_0", "Source_PUBLIC7_registered5_actor0",
            "formal_gen14_15_reads0", "B_C0", "old_unused_balances_closed_no_transfer"))
        and stopped.get("Root_V33_used_conservative") == 378
        and stopped.get("Root_V33_unused_closed") == 1606,
        "V35 failed CI/old unstarted allocations must remain closed")
    return values
