"""V31 fixed profile selection through the real prospective execution interfaces."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
RECOVERY = "topolab.v2.p17-binding-certificate-recovery.20261104.v6"
INPUT = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v4"
PUBLIC = "/private/tmp/topolab-public-registered4-source-acquisition-20261104-v5"
PARENT = "/Users/keith1117/Library/Application Support/TopoLab-custody/"


def module(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def test_v31_selects_same_explicit_profile_at_producer_auditor_and_native_cli(monkeypatch):
    old = module("p17_m2_source_binding_recovery")
    recovery = old.for_identity(RECOVERY)
    control = module("p17_m2_source_acquisition_control").for_registered_identity(INPUT)
    registered = control.load("p17_m2_registered_input")
    auditor = control.load("p17_m2_source_acquisition_independent")
    assert (
        recovery.IDENTITY == RECOVERY
        and registered.IDENTITY == auditor.REGISTERED_IDENTITY == INPUT
    )
    assert registered.authority()["global_deadline_ms"] == 1793849880000
    assert control.for_root(PUBLIC) is control
    assert control.load("p17_m2_source_binding_recovery") is recovery
    native = module("p17_m2_source_binding_native")
    plan = {
        "schema": native.METADATA_SCHEMA,
        "context": {"execution_identity": RECOVERY, "attempt": 1, "scope": native.RECOVERY_SCOPE},
        "runtime": {"python": "/public/python", "cwd": str(REPO)},
        "root": "/public/metadata",
    }
    assert native.execution_profile(plan) == (RECOVERY, 300)
    assert native.argv_for(plan, "supervise", "binding-certificate-auditor")[2].endswith(
        "/p17_m2_source_binding_recovery_v6.py"
    )
    assert native.transport_for(plan).__class__.__module__ == recovery.__name__
    captured = {}

    def capture(plan, **kwargs):
        captured.update(kwargs)
        raise RuntimeError("compiler seam reached without runtime IO")

    monkeypatch.setattr(auditor, "validate_binding", lambda plan: None)
    monkeypatch.setattr(auditor.native, "_check_software", capture)
    with pytest.raises(RuntimeError, match="compiler seam reached"):
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
    for entry in ("p17_m2_source_binding_recovery_v6.py", "p17_m2_registered_input_v4.py"):
        result = subprocess.run(
            [sys.executable, "-I", str(REPO / "scripts" / entry), "--help"],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout


@pytest.mark.parametrize(
    "attempt,basename",
    [
        (1, "p17-m2-local-input-version-v12-strict-binding-20261104"),
        (2, "p17-m2-local-input-version-v13-strict-binding-remedy-20261104"),
    ],
)
def test_v31_genuine_opaque_issuer_and_scientific_callbacks_use_exact_new_roots(
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


def test_v31_waiter_and_historical_clocks_remain_separate():
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
    projected = waiter.project(plan, b"public metadata", PUBLIC)
    assert projected["applicable_deadline_ms"] == 1793818000406
    plan["execution_identity"] = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v3"
    with pytest.raises(ValueError, match="identity"):
        waiter.project(plan, b"public metadata", PUBLIC)
    old = module("p17_m2_source_binding_recovery")
    prior = old.for_identity("topolab.v2.p17-binding-certificate-recovery.20261104.v5")
    current = old.for_identity(RECOVERY)
    assert old.IDENTITY.endswith(".v4") and prior is not current
    assert prior.authority()["limits"]["software_deadline_ms"] == 1793810821805
    assert current.authority()["limits"]["software_deadline_ms"] == 1793818000406


def test_v31_scientific_grant_accepts_only_genuine_issuer_before_other_gates(monkeypatch):
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


def test_v31_public_remedy_stays_closed_before_any_registration_or_target_io(monkeypatch):
    registered = (
        module("p17_m2_source_acquisition_control")
        .for_registered_identity(INPUT)
        .load("p17_m2_registered_input")
    )

    def forbidden(*args, **kwargs):
        pytest.fail("closed remedy reached registration metadata or target IO")

    monkeypatch.setattr(registered, "_registration_plan", forbidden)
    with pytest.raises(ValueError, match="remedy requires separately diagnosed"):
        registered.prepare_rehearsal(Path(PUBLIC.replace("-v5", "-v6")), {})


def v31_budget_fixture(subject, tmp_path, monkeypatch):
    """Public metadata only; exact values come from the preregistered V31 grant."""
    import json

    policy = json.loads(subject.AUTHORITY.read_bytes())
    start = 1793807200406
    source = {
        "new_Original_registration_reads": 0,
        "new_Foundation_helpers": 0,
        "formal_whitelist_files_each_author_attempt": 598,
        "each_file_reads_each_author_attempt": 1,
        "formal_all_attempts_Original_read_cap": 2392,
        "whole_Original_read_cap2484_UNCHANGED": True,
        "all_old_actual_registration_consumption_carried": True,
    }
    execution = {
        "metadata_identity": RECOVERY,
        "input_identity": INPUT,
        "public_metadata_calls": 1,
        "formal_metadata_calls": 1,
        "public_metadata_FULL": 120,
        "formal_metadata_FULL": 120,
        "public_six_role_cohorts_max": 2,
        "formal_six_role_cohorts_max": 2,
        "public_FULL_each": 3780,
        "formal_FULL_each": 3780,
        "coordination_seconds_UNCHANGED": 240,
        "native_RSS_bytes_UNCHANGED": 4294967296,
        "counts_UNCHANGED": {"metadata": 40, "payload": 558, "version_members": 1071},
    }
    budget = {
        "schema": "topolab.owner.NEW-unstarted-continuous-input-and-fixed-science.v31",
        "NEW_each_phase_seconds": {
            "software_and_protected_publication": 10800,
            "formal_metadata_and_result": 1200,
            "primary_input_formal_and_result": 6300,
            "scientific_contract_and_protected_publication": 7200,
            "original_B_C": 14760,
            "final_retention_filing_actual_return": 1800,
        },
        "sum_primary_phase_maxima_seconds": 42060,
        "NEW_each_metadata_calls": {
            "software_publication": 512,
            "formal_metadata": 64,
            "input_all_attempts": 512,
            "scientific_contract_publication": 256,
            "scientific_B_C_orchestration": 512,
            "final_retention_filing": 128,
            "total": 1984,
        },
        "no_elapsed_or_fee_counter_reset": True,
        "all_old_unused_allowances_closed_no_transfer": True,
        "old_original_author_start_ms": 1793727480000,
        "old_original_each_author_cap_seconds100800_retained": True,
        "NEW_additional_author_seconds_each": 21600,
        "NEW_cumulative_each_author_span_cap_seconds": 122400,
        "NEW_root_independent_hard_deadline_ms": 1793849880000,
        "original_outer_span_seconds151200_UNCHANGED": True,
        "original_outer_deadline_ms_UNCHANGED": 1793878680000,
        "source_boundary": source,
        "NEW_execution": execution,
        "old_failure_reference": policy["prior_failed_continuation"],
    }
    raw = subject.canonical(budget)
    policy["budget"] = {"path": str(tmp_path / "budget.json"), "sha256": subject.sha(raw)}
    values = {
        "budget": budget,
        "budget_review": {
            "author": policy["actors"]["independent"],
            "status": "PASS_PUBLIC_TEST_METADATA_ONLY",
        },
        "prior_failed_continuation": {
            "status": "CLOSED_FAILED_PUBLIC_BEFORE_NATIVE_INSUFFICIENT_SUFFIX"
        },
        "prior_failed_publication": {
            "status": "CLOSED_FAILED_PUBLICATION_MAIN_CI_NOT_READY_FORMAL_UNLAUNCHED"
        },
        "prior_failed_metadata_closure": {"public_fixture": True},
        "prior_failed_metadata_closure_actual": {"public_fixture": True},
        "registration_actual": {
            "author": "/root",
            "grant_sha256": policy["budget"]["sha256"],
            "activation_starts_at": start,
            "event": {
                "tool": "exec_command",
                "requested_ms": start - 1,
                "returned_ms": start,
                "result": {
                    "exit_code": 0,
                    "output": str(len(raw)) + " " + policy["budget"]["sha256"] + "\n",
                },
            },
        },
        "software_activation": {
            "schema": "topolab.NEW-continuous-input.software-activation.v1",
            "execution_identity": RECOVERY,
            "budget_reference": policy["budget"],
            "started_ms": start,
            "deadline_ms": 1793818000406,
            "global_deadline_ms": 1793849880000,
            "original_author_start_ms": 1793727480000,
            "old_original_author_cap_seconds": 100800,
            "additional_author_seconds": 21600,
            "new_cumulative_author_span_cap_seconds": 122400,
            "original_outer_deadline_ms_UNCHANGED": 1793878680000,
            "no_counter_reset_or_old_allowance_transfer": True,
            "old_failed_reference": policy["prior_failed_continuation"],
        },
    }
    captures = {}
    for key, value in values.items():
        raw = subject.canonical(value)
        if key not in ("budget", "prior_failed_continuation"):
            policy[key] = {"path": str(tmp_path / (key + ".json")), "sha256": subject.sha(raw)}
        captures[key] = {"reference": dict(policy[key]), "raw": raw.decode(), "value": value}
    # The fixture's old failure has its own honest raw identity.
    key = "prior_failed_continuation"
    policy[key]["sha256"] = subject.sha(subject.canonical(values[key]))
    for key in ("budget", "software_activation", "prior_failed_continuation"):
        raw = subject.canonical(values[key])
        policy[key]["sha256"] = subject.sha(raw)
        captures[key] = {"reference": dict(policy[key]), "raw": raw.decode(), "value": values[key]}
    values["registration_actual"]["grant_sha256"] = policy["budget"]["sha256"]
    values["registration_actual"]["event"]["result"]["output"] = (
        str(len(captures["budget"]["raw"].encode())) + " " + policy["budget"]["sha256"] + "\n"
    )
    raw = subject.canonical(values["registration_actual"])
    policy["registration_actual"]["sha256"] = subject.sha(raw)
    captures["registration_actual"] = {
        "reference": dict(policy["registration_actual"]),
        "raw": raw.decode(),
        "value": values["registration_actual"],
    }
    monkeypatch.setattr(subject, "authority", lambda: policy)
    return captures, policy


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "cumulative",
        "late-activation",
        "source-cap",
        "old-failure",
        "phase-cap",
        "registration-return",
    ],
)
def test_v31_raw_budget_registration_and_nonreset_clock_negatives(tmp_path, monkeypatch, fault):
    subject = module("p17_m2_source_binding_recovery").for_identity(RECOVERY)
    captures, policy = v31_budget_fixture(subject, tmp_path, monkeypatch)
    if fault:
        key = {
            "cumulative": "budget",
            "late-activation": "software_activation",
            "source-cap": "budget",
            "old-failure": "prior_failed_continuation",
            "phase-cap": "budget",
            "registration-return": "registration_actual",
        }[fault]
        value = captures[key]["value"]
        if fault == "cumulative":
            value["NEW_cumulative_each_author_span_cap_seconds"] += 1
        elif fault == "late-activation":
            value["deadline_ms"] += 1
        elif fault == "source-cap":
            value["source_boundary"]["formal_all_attempts_Original_read_cap"] += 1
        elif fault == "old-failure":
            value["status"] = "PASS"
        elif fault == "phase-cap":
            value["NEW_each_phase_seconds"]["primary_input_formal_and_result"] += 1
        else:
            value["event"]["returned_ms"] += 1
        raw = subject.canonical(value)
        policy[key]["sha256"] = subject.sha(raw)
        captures[key] = {"reference": dict(policy[key]), "raw": raw.decode(), "value": value}
        with pytest.raises(ValueError):
            subject._captured_budget(captures)
    else:
        assert (
            subject._captured_budget(captures)["software_activation"]["started_ms"] == 1793807200406
        )


@pytest.mark.parametrize(
    "identity,entry",
    [
        (
            "topolab.v2.p17-binding-certificate-recovery.20261104.v5",
            "p17_m2_source_binding_recovery_v5.py",
        ),
        (RECOVERY, "p17_m2_source_binding_recovery_v6.py"),
    ],
)
def test_prospective_resource_literal_admission_selects_exact_payload_before_native(
    monkeypatch, identity, entry
):
    module("p17_m2_homotopy")
    resource = module("p17_m2_resource_control")

    def before_native(*args, **kwargs):
        raise RuntimeError("literal payload admitted before any runtime IO")

    monkeypatch.setattr(Path, "mkdir", before_native)
    argv = [
        "/public/python",
        "-I",
        str(REPO / "scripts" / entry),
        "payload",
        "--plan",
        "/public/plan.json",
        "--plan-sha",
        "a" * 64,
        "--role",
        "binding-certificate-auditor",
    ]
    with pytest.raises(RuntimeError, match="literal payload admitted"):
        resource.invoke(
            "/PUBLIC_NOT_CREATED",
            "binding-certificate-auditor",
            argv,
            timeout=1,
            measurement_execution_identity=identity,
            measurement_scope="STRICT_BINDING_CERTIFICATE_RECOVERY_METADATA_ONLY",
        )
    argv[2] = str(REPO / "scripts/p17_m2_source_binding_recovery.py")
    with pytest.raises(ValueError, match="literal payload argv"):
        resource.invoke(
            "/PUBLIC_NOT_CREATED",
            "binding-certificate-auditor",
            argv,
            timeout=1,
            measurement_execution_identity=identity,
            measurement_scope="STRICT_BINDING_CERTIFICATE_RECOVERY_METADATA_ONLY",
        )
