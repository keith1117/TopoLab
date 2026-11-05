"""V35 fixed profile selection without subprocess or source IO."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
RECOVERY = "topolab.v2.p17-binding-certificate-recovery.20261104.v8"
INPUT = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v6"


@pytest.fixture(autouse=True)
def no_processes(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("V35 pure regression attempted subprocess.Popen")
    monkeypatch.setattr(subprocess, "Popen", forbidden)


def module(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def test_v35_exact_profile_retains_old_defaults_and_new_deadline():
    old = module("p17_m2_source_binding_recovery")
    original = old.IDENTITY, old.PROTOCOL_PATH, old.AUTHORITY.read_bytes()
    recovery = old.for_identity(RECOVERY)
    control = module("p17_m2_source_acquisition_control").for_registered_identity(INPUT)
    registered = control.load("p17_m2_registered_input")
    assert recovery.IDENTITY == RECOVERY
    assert registered.IDENTITY == INPUT
    assert registered.authority()["global_deadline_ms"] == 1793878200000
    assert recovery.authority()["limits"]["software_start_ms"] == 1793830369237
    assert recovery.authority()["limits"]["software_deadline_ms"] == 1793844769237
    assert (old.IDENTITY, old.PROTOCOL_PATH, old.AUTHORITY.read_bytes()) == original


PARENT = "/Users/keith1117/Library/Application Support/TopoLab-custody/"
@pytest.mark.parametrize(
    "attempt,basename",
    [
        (1, "p17-m2-local-input-version-v16-strict-binding-20261104"),
        (2, "p17-m2-local-input-version-v17-strict-binding-remedy-20261104"),
    ],
)
def test_v35_genuine_opaque_issuer_and_scientific_callbacks_use_exact_new_roots(
    monkeypatch, attempt, basename
):
    control = module("p17_m2_source_acquisition_control").for_registered_identity(INPUT)
    auditor = control.load("p17_m2_source_acquisition_independent")
    registered = control.load("p17_m2_registered_input")
    policy = registered.authority()
    root = PARENT + basename
    assert policy["fixed_target"]["attempts"][str(attempt)]["generation"] == root
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

    def reached(*args, **kwargs):
        raise RuntimeError("genuine issuer reached binding")

    monkeypatch.setattr(auditor.CheckedAcquisitionInput, "binding_for", reached)
    with pytest.raises(RuntimeError, match="genuine issuer reached binding"):
        reader.VerifiedAcquisitionInput(certificate, "scientific-producer")
    certificate._binding["verified_plan"]["execution_identity"] = "UNREGISTERED"
    assert reader.checked_acquisition_issuer(certificate) is None



def test_v35_scientific_grant_accepts_only_genuine_issuer_before_other_gates(monkeypatch):
    control = module("p17_m2_source_acquisition_control").for_registered_identity(INPUT)
    checker = control.load("p17_m2_source_acquisition_independent")
    binding = {
        "root": "/PUBLIC_NOT_OPENED/content",
        "root_identity": {},
        "version_id": "a" * 64,
        "contract_sha256": "b" * 64,
        "plan_sha256": "c" * 64,
        "shared_packet_sha256": "d" * 64,
        "verified_plan": {"execution_identity": INPUT},
        "scope": checker.REHEARSAL_SCOPE,
    }
    certificate = checker.CheckedAcquisitionInput(
        binding, _authority=checker._ACQUISITION_AUTHORITY
    )
    science = module("p17_m2_scientific_independent")
    admission = object.__new__(science.CheckedBAdmission)
    admission.contract_sha256 = "c" * 64
    monkeypatch.setattr(science, "check_contract", lambda value: "c" * 64)
    with pytest.raises(ValueError, match="scientific reader role differs"):
        science.grant_scientific_input(certificate, {}, "UNREGISTERED", admission)
    with pytest.raises(ValueError, match="independently accepted acquisition"):
        science.grant_scientific_input({"status": "PASS"}, {}, "UNREGISTERED", admission)



def test_v35_producer_independent_compiler_and_native_routes_match(monkeypatch):
    control = module("p17_m2_source_acquisition_control").for_registered_identity(INPUT)
    auditor = control.load("p17_m2_source_acquisition_independent")
    recovery = control.load("p17_m2_source_binding_recovery")
    native = module("p17_m2_source_binding_native")
    plan = {"schema": native.METADATA_SCHEMA,
            "context": {"execution_identity": RECOVERY, "attempt": 1,
                        "scope": native.RECOVERY_SCOPE},
            "runtime": {"python": "/public/python", "cwd": str(REPO)},
            "root": "/public/metadata"}
    assert native.execution_profile(plan) == (RECOVERY, 300)
    assert native.role_profile(plan)[3] == {
        "binding-certificate-auditor": "/root/ci_clock_reader_v1"}
    assert native.argv_for(plan, "supervise", "binding-certificate-auditor")[2].endswith(
        "/p17_m2_source_binding_recovery_v8.py")
    assert native.transport_for(plan).__class__.__module__ == recovery.__name__
    captured = {}

    def reached(plan, **kwargs):
        captured.update(kwargs)
        raise RuntimeError("compiler reached before any runtime IO")

    monkeypatch.setattr(auditor, "validate_binding", lambda plan: None)
    monkeypatch.setattr(auditor.native, "_check_software", reached)
    with pytest.raises(RuntimeError, match="compiler reached"):
        auditor._check_software({"execution_identity": INPUT, "scope": auditor.REHEARSAL_SCOPE,
            "source_identity_policy": auditor.HASH_BOUND_POLICY,
            "binding": {"source_identity_policy": auditor.HASH_BOUND_POLICY,
                "authority_protocol_path": auditor.REGISTERED_PROTOCOL,
                "strict23_registration": {"certificate_sha256": "a" * 64,
                                          "finalize_actual_sha256": "b" * 64}}})
    compiled = auditor.native._software_closure(REPO, contracts=captured["contracts"])
    assert compiled == control.source_freeze(INPUT)
    assert len(compiled) == 54
    assert len(recovery.source_freeze()) == 35
    assert "scripts/p17_m2_source_verified_input.py" in recovery.source_freeze()


@pytest.mark.parametrize("root,formal,deadline", [
    ("/private/tmp/topolab-public-registered6-source-acquisition-20261104-v7", False,
     1793844769237),
    (PARENT + "p17-m2-local-input-version-v16-strict-binding-20261104", True, 1793876029237),
    (PARENT + "p17-m2-local-input-version-v17-strict-binding-remedy-20261104", True,
     1793876029237),
])
def test_v35_waiter_uses_exact_identity_and_stronger_author_deadline(root, formal, deadline):
    waiter = module("await_m2_acquisition_receipt")
    plan = {"execution_identity": INPUT, "root": root, "role_order": list(waiter.ROLES),
            "actor_window_seconds": 4500, "formal_authority": formal,
            "scope": ("SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY" if formal
                      else "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"),
            "actor_activation_UTC_seconds": 1}
    assert waiter.project(plan, b"new public metadata", root)["applicable_deadline_ms"] == deadline
    plan["execution_identity"] = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v5"
    with pytest.raises(ValueError, match="identity"):
        waiter.project(plan, b"new public metadata", root)


def v35_public_budget(subject, monkeypatch):
    """Synthetic public metadata: no external evidence, inputs or target IO."""
    import copy
    import json

    policy = copy.deepcopy(subject.authority())
    budget = {
        "schema": "topolab.owner.NEW-unstarted-clock-fixture-and-continuous-input.v35",
        "registered_before_new_work_ms": 1793830369237,
        "NEW_primary_phase_maxima_seconds": {
            "software_review_publication_public": 14400, "formal_metadata": 1200,
            "primary_input_formal_and_result": 6300, "scientific_contract_publication": 7200,
            "B_C_original": 14760, "final_actual_return_retention": 1800},
        "sum_primary_maxima_seconds": 45660,
        "NEW_Root_metadata_calls": {"software_publication": 512, "formal_metadata": 64,
            "input_all_attempts": 512, "scientific_contract_publication": 256,
            "B_C": 512, "final_filing": 128, "total": 1984},
        "NEW_global_deadline_ms": 1793878200000, "original_author_start_ms": 1793727480000,
        "old_cumulative_Root_author_seconds142200_retained": True,
        "NEW_additional_Root_author_seconds": 8520, "NEW_cumulative_Root_author_seconds": 150720,
        "original_outer_deadline_ms_UNCHANGED": 1793878680000,
        "original_outer151200_UNCHANGED": True,
        "identities": {"metadata": RECOVERY, "input": INPUT},
        "source_and_science_UNCHANGED": {"new_Original_registration_reads": 0,
            "new_Foundation_helpers": 0, "files_once_each_author_attempt": 598,
            "all_formal_Original_reads2392": True, "whole_Original_reads2484_helpers138": True,
            "metadata40_payload558_version1071": True, "source_coordination_seconds240": True,
            "native_RSS4294967296": True,
            "fixed_models_panel_quality_speed_windows_and_resources": True,
            "no_scientific_retry_search": True, "same_issuer_two_fix_rounds_not_reopened": True},
        "NEW_named_Native_FULL": {"metadata_public9_once": 120, "public_source7_once": 3780,
            "formal_metadata8_once": 120, "formal_input_two_attempts": 7560,
            "B_once": 180, "C_once": 14580, "total": 26340},
        "NEW_independent": {"author": "/root/ci_clock_reader_v1", "wall_cap_seconds": 45660,
            "metadata_calls": 1984, "logical_GitHub_GET": 128, "global_deadline_ms": 1793878200000,
            "no_old_author_balance_reused": True},
        "NEW_engineer": {"author": "/root/ci_clock_engineer_v1",
            "seconds_including_startup_filing_actual_return": 1800, "calls": 64},
        "NEW_reviewers": {"authors": ["/root/ci_clock_standards_v1", "/root/ci_clock_spec_v1"],
            "seconds_each_including_actual_return": 900, "calls_each": 32},
        "NEW_Root_logical_GitHub_GET": 256, "NEW_CI_workflow_runs_max": 12,
        "targets": {"parent": PARENT.rstrip("/"),
            "public_metadata": policy["targets"]["public"][0],
            "formal_metadata": policy["targets"]["formal"][0],
            "public_source": (
                "/private/tmp/topolab-public-registered6-source-acquisition-20261104-v7"),
            "formal": ["p17-m2-local-input-version-v16-strict-binding-20261104",
                       "p17-m2-local-input-version-v17-strict-binding-remedy-20261104"],
            "backup_suffix": "-independent-backup", "all_formal_unprobed": True,
            "no_old_failed_scene_or_HELD_lease_reuse": True},
        "failed_PR236": {"head": "1efe58cf4fc877c6fda272b7610ae8bd4ee2436d",
            "run": 41915681708, "quality_job": 126874584970,
            "status": "1 failed 3472 passed37skipped",
            "log_path": policy["prior_failed_CI"]["path"],
            "log_sha256": policy["prior_failed_CI"]["sha256"]},
        "old_unstarted_scopes_closed": {"metadata_public9_Native0": True,
            "formal_metadata7_0": True, "Source_PUBLIC7_registered5_actor0": True,
            "formal_gen14_15_reads0": True, "B_C0": True,
            "old_unused_balances_closed_no_transfer": True,
            "Root_V33_used_conservative": 378, "Root_V33_unused_closed": 1606},
        "ROOT_counter_base_before_registration": 2062, "ROOT_collaboration_upper_base": 42,
        "known_NEW_FULL_lower": 254550,
        "NEW_software_full_campaigns": [
            {"label": "R18_CLOCK_FIX_AND_NEW_UNSTARTED_PROFILE", "ordinal": 23,
             "Native_FULL_max": 100000, "UTC_seconds": 4200,
             "closing_suffix_seconds": 600, "calls": 1},
            {"label": "R19_ACTUAL_ACCEPTED_INPUT_SCIENTIFIC_CONTRACT", "ordinal": 24,
             "Native_FULL_max": 100000, "UTC_seconds": 4200,
             "closing_suffix_seconds": 600, "calls": 1,
             "condition": "Only after actual accepted full input; scientific contract/publication "
                          "phase must have complete actual suffix"}],
        "public_fixture_padding": ""}
    budget["public_fixture_padding"] = "x" * (7124 - len(subject.canonical(budget)))
    activation = {"schema": "topolab.NEW-V35.software-activation.v1", "author": "/root",
        "software_start_ms": 1793830369237, "registration_actual_return_ms": 1793830370485,
        "software_deadline_ms": 1793844769237, "global_deadline_ms": 1793878200000,
        "original_author_start_ms": 1793727480000, "cumulative_Root_author_seconds": 150720,
        "old_cumulative142200_retained": True, "additional8520_not_reset": True,
        "old_allocation_unused_closed_not_transferred": True}
    review = {"schema": "topolab.independent.V35.budget-and-clock-review.v1",
        "author": "/root/ci_clock_reader_v1", "status": "PASS_budgetonly",
        "arithmetic": {"sum_primary_seconds": 45660,
            "registration_headroom_after_all_primary_maxima_ms": 2169515,
            "software_start_ms": 1793830369237, "software_deadline_ms": 1793844769237},
        "no_old_budget_or_author_balance_reused": True}
    registration = {"schema": "topolab.NEW-V35.registration-original-actual.v1",
        "original": {"tool": "exec_command", "requested_ms": 1793830370327,
            "returned_ms": 1793830370485, "result": {"exit_code": 0}}}
    clock = {"schema": "topolab.independent.V35.conservative-startup-clock-supplement.v1",
        "author": "/root/ci_clock_reader_v1", "status": "PASS_budgetonly_STRICTER_CLOCK",
        "conservative_author_budget_start_ms": 1793830369237,
        "effective_author_deadline_ms": 1793876029237,
        "no_clock_reset_or_old_budget_transfer": True}
    values = dict(budget=budget, budget_review=review, software_activation=activation,
                  registration_actual=registration, independent_author_clock=clock)
    monkeypatch.setattr(subject, "authority", lambda: policy)

    def captures():
        budget["public_fixture_padding"] = ""
        budget["public_fixture_padding"] = "x" * (7124 - len(subject.canonical(budget)))
        budget_raw = subject.canonical(budget)
        policy["budget"] = {"path": "/new-public/budget.json", "sha256": subject.sha(budget_raw)}
        activation["new_grant_sha256"] = policy["budget"]["sha256"]
        registration["original"]["result"]["output"] = json.dumps({
            "path": "NEW-unstarted-clock-fixture-and-continuous-input-v35.json", "bytes": 7124,
            "sha256": policy["budget"]["sha256"], "software_deadline_ms": 1793844769237,
            "registered_headroom_ms": 2170763}) + "\n"
        result = {}
        for key, value in values.items():
            raw = subject.canonical(value)
            policy[key] = {"path": "/new-public/" + key + ".json", "sha256": subject.sha(raw)}
            result[key] = {"reference": policy[key], "raw": raw.decode(), "value": value}
        return result

    return values, captures


@pytest.mark.parametrize("changed", [None, "global", "calls", "reads", "helpers", "source-target",
    "old-closed", "old-CI", "registration-return", "activation-start", "review-author",
    "headroom", "author-deadline", "issuer-fixes", "outer"])
def test_v35_captured_budget_rejects_changed_scope_clocks_and_closed_history(monkeypatch, changed):
    subject = module("p17_m2_source_binding_recovery").for_identity(RECOVERY)
    values, capture = v35_public_budget(subject, monkeypatch)
    if changed == "global":
        values["budget"]["NEW_global_deadline_ms"] += 1
    if changed == "calls":
        values["budget"]["NEW_Root_metadata_calls"]["total"] += 1
    if changed == "reads":
        values["budget"]["source_and_science_UNCHANGED"]["files_once_each_author_attempt"] += 1
    if changed == "helpers":
        values["budget"]["source_and_science_UNCHANGED"]["new_Foundation_helpers"] += 1
    if changed == "source-target":
        values["budget"]["targets"]["public_source"] = "/new-public/not-the-fixed-root"
    if changed == "old-closed":
        values["budget"]["old_unstarted_scopes_closed"][
            "old_unused_balances_closed_no_transfer"] = False
    if changed == "old-CI":
        values["budget"]["failed_PR236"]["status"] = "PASS"
    if changed == "registration-return":
        values["registration_actual"]["original"]["returned_ms"] += 1
    if changed == "activation-start":
        values["software_activation"]["software_start_ms"] += 1
    if changed == "review-author":
        values["budget_review"]["author"] = "/old-closed-reader"
    if changed == "headroom":
        values["budget_review"]["arithmetic"][
            "registration_headroom_after_all_primary_maxima_ms"] += 1
    if changed == "author-deadline":
        values["independent_author_clock"]["effective_author_deadline_ms"] += 1
    if changed == "issuer-fixes":
        values["budget"]["source_and_science_UNCHANGED"][
            "same_issuer_two_fix_rounds_not_reopened"] = False
    if changed == "outer":
        values["budget"]["original_outer_deadline_ms_UNCHANGED"] += 1
    captures = capture()
    if changed is None:
        accepted = subject._captured_budget(captures)
        assert accepted["software_activation"]["software_start_ms"] == 1793830369237
    else:
        expected = ("clocks/calls/identities" if changed in {"global", "calls", "outer"}
            else "source/resource/author" if changed in {"reads", "helpers", "issuer-fixes"}
            else "fixed targets" if changed == "source-target"
            else "failed CI/old unstarted" if changed in {"old-closed", "old-CI"}
            else "original registration return" if changed == "registration-return"
            else "declared start" if changed == "activation-start"
            else "independent budget/clock review" if changed in {"review-author", "headroom"}
            else "conservative independent author clock")
        with pytest.raises(ValueError, match=expected):
            subject._captured_budget(captures)


@pytest.mark.parametrize("kind", ["public", "formal"])
def test_v35_permission_required_before_metadata_actor_or_target_creation(monkeypatch, kind):
    recovery = module("p17_m2_source_binding_recovery").for_identity(RECOVERY)
    monkeypatch.setattr(recovery, "review_readiness",
                        lambda *args: pytest.fail("permission failure reached reviews"))
    with pytest.raises(ValueError, match="permission preflight required before actor/root"):
        recovery.prepare(kind, 1)
    with pytest.raises(ValueError, match="literal permission packet path"):
        recovery.prepare(kind, 1, permission_packet="/old-closed/permission.json",
                         permission_packet_sha="a" * 64)


def test_v35_resource_payload_literal_is_selected_before_native(monkeypatch):
    module("p17_m2_homotopy")
    resource = module("p17_m2_resource_control")

    def reached(*args, **kwargs):
        raise RuntimeError("literal admitted before runtime IO")

    monkeypatch.setattr(Path, "mkdir", reached)
    argv = ["/public/python", "-I", str(REPO / "scripts/p17_m2_source_binding_recovery_v8.py"),
            "payload", "--plan", "/public/plan.json", "--plan-sha", "a" * 64,
            "--role", "binding-certificate-auditor"]
    with pytest.raises(RuntimeError, match="literal admitted"):
        resource.invoke("/PUBLIC_NOT_CREATED", "binding-certificate-auditor", argv, timeout=1,
            measurement_execution_identity=RECOVERY,
            measurement_scope="STRICT_BINDING_CERTIFICATE_RECOVERY_METADATA_ONLY")
    argv[2] = str(REPO / "scripts/p17_m2_source_binding_recovery_v7.py")
    with pytest.raises(ValueError, match="literal payload argv"):
        resource.invoke("/PUBLIC_NOT_CREATED", "binding-certificate-auditor", argv, timeout=1,
            measurement_execution_identity=RECOVERY,
            measurement_scope="STRICT_BINDING_CERTIFICATE_RECOVERY_METADATA_ONLY")
