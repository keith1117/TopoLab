"""NEW literal source authority public metadata, never original or target IO."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).parents[1]
GENERATION = (
    "/Users/keith1117/Library/Application Support/TopoLab-custody/"
    "p17-m2-local-input-version-v7-hash-bound-20261028"
)


def controller():
    spec = importlib.util.spec_from_file_location(
        "new_source_control_test", REPO / "scripts/p17_m2_source_acquisition_control.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_new_exact_literal_routes_new_authority_without_target_io(monkeypatch):
    control = controller()
    raw = b"new public authority marker"
    monkeypatch.setattr(control, "NEW_AUTHORITY_RAW", raw, raising=False)

    def forbidden(*args, **kwargs):
        raise AssertionError("literal routing performed path or module IO")

    with monkeypatch.context() as guard:
        guard.setattr(control, "load", forbidden)
        guard.setattr(control.os, "open", forbidden)
        guard.setattr(Path, "stat", forbidden)
        guard.setattr(Path, "read_bytes", forbidden)
        selected, attempt = control.authority_for_root(GENERATION)
    assert selected is raw
    assert attempt == 1


def test_new_public_plan_uses_new_policy_without_changing_old_software_closure(tmp_path):
    control = controller()
    contract = json.loads(
        (REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json").read_bytes()
    )
    plan = control.make_plan(
        tmp_path / "topolab-public-new-source-acquisition-plan", contract,
        {"B3_DATA_HASH": "2" * 64, "CATALOG_HASH": "3" * 64},
    )
    assert plan["execution_identity"] == "topolab.v2.p17-m2-hash-bound-source-acquisition.v3"
    assert plan["source_identity_policy"] == "topolab.source-identity.prebound-sha256.v1"
    assert plan["scope"] == "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
    assert plan["formal_authority"] is False
    assert plan["binding"]["authority_protocol_path"] == (
        "docs/planning/p17_m2_new_source_acquisition_protocol.json"
    )
    assert "docs/planning/p17_m2_new_source_acquisition_protocol.json" in plan["source_tree"]
    assert (
        "docs/planning/p17_m2_new_source_acquisition_protocol.json" not in control.source_freeze()
    )


def test_new_formal_metadata_is_once_only_and_keeps_complete_input_contract():
    control = controller()
    plan = control.formal_plan(control.NEW_AUTHORITY_RAW)
    assert plan["execution_identity"] == "topolab.v2.p17-m2-hash-bound-source-acquisition.v3"
    assert plan["root"] == GENERATION
    assert plan["backup_root"] == GENERATION + "-independent-backup"
    assert plan["source_root"] == "/Users/keith1117/Documents/TopoLab-data"
    assert plan["binding"]["formal_attempt"] == 1
    assert plan["binding"]["authority_protocol_path"] == (
        "docs/planning/p17_m2_new_source_acquisition_protocol.json"
    )
    assert plan["source_identity_policy"] == "topolab.source-identity.prebound-sha256.v1"
    assert plan["result_window_projection_seconds"] == {"exporter": 9000, "independent": 9000}
    assert plan["binding"]["B_C"] is False


@pytest.mark.parametrize("formal", [False, True])
def test_new_transport_keeps_prebound_policy_on_both_scopes(formal, tmp_path):
    control = controller()
    root = Path(GENERATION) if formal else tmp_path / "topolab-public-new-source-acquisition-role"
    transport = control.AcquisitionTransport(
        root, "1" * 64, scope=control.FORMAL_SCOPE if formal else control.REHEARSAL_SCOPE,
    )
    assert transport.identity == "topolab.v2.p17-m2-hash-bound-source-acquisition.v3"
    assert transport.source_identity_policy == "topolab.source-identity.prebound-sha256.v1"
    assert transport.result_windows == (("exporter", 9000), ("independent", 9000))


@pytest.mark.parametrize("field", ["total", "actors", "target", "reads", "attempts"])
def test_new_formal_metadata_rejects_changed_finite_authority(field):
    control = controller()
    value = json.loads(control.NEW_AUTHORITY_RAW)
    if field == "total":
        value["total_new_author_charged_seconds_cap"] = 235800
    elif field == "actors":
        value["actors"]["independent"] = "/root/acquisition_funded_audit"
    elif field == "target":
        value["fixed_target"]["attempts"]["1"]["generation"] += "-other"
    elif field == "reads":
        value["budget"]["source_max_reads_each_attempt"] = 1197
    else:
        value["budget"]["source_attempts"] = 2
    with pytest.raises(ValueError, match="NEW_SOURCE_AUTHORITY_PARAMETERS_DIFFER"):
        control.formal_plan(control.base().canonical(value))


def test_new_pending_readiness_denies_before_loader_target_or_network(monkeypatch):
    control = controller()
    value = json.loads(control.NEW_AUTHORITY_RAW)
    value["readiness_freeze_state"] = "DRAFT_PUBLIC_PREPARATION_NOT_FORMAL"

    def forbidden(*args, **kwargs):
        raise AssertionError("pending readiness reached loader, target or network")

    with monkeypatch.context() as guard:
        guard.setattr(control, "load", forbidden)
        guard.setattr(control.os, "open", forbidden)
        guard.setattr(control.subprocess, "run", forbidden)
        with pytest.raises(ValueError, match="NEW_READINESS_NOT_FROZEN"):
            control.activation_readiness(value)


def test_new_ready_gate_checks_fresh_proofs_and_all_four_main_jobs(monkeypatch):
    control = controller()
    value = json.loads(control.NEW_AUTHORITY_RAW)
    value.update(
        readiness_freeze_state="REVIEWED_FROZEN",
        implementation_base_commit="d" * 40,
        published_source_sha256={
            k: v for k, v in control.source_freeze(control.NEW_IDENTITY).items()
            if k != control.NEW_PROTOCOL
        },
        preparation_closure_sha256=hashlib.sha256(b"new paired closure").hexdigest(),
        independent_preflight_sha256=hashlib.sha256(b"new independent preflight").hexdigest(),
    )
    checker = control.load("p17_m2_source_acquisition_independent")
    observed = []

    def software(path):
        observed.append(str(path))
        if path == REPO / control.NEW_PROTOCOL:
            return control.base().canonical(value)
        if str(path) == value["independent_preflight_path"]:
            return b"new independent preflight"
        if str(path) in value["preparation_closure_paths"]:
            return b"new paired closure"
        raise AssertionError("unexpected metadata read: " + str(path))

    def preflight(plan, raw):
        assert plan["execution_identity"] == control.NEW_IDENTITY
        assert plan["binding"]["formal_attempt"] == 1
        assert raw == b"new independent preflight"
        return {"independently_checked": True}

    head = "e" * 40

    def command(argv, **kwargs):
        if argv[:3] == ["git", "status", "--porcelain=v1"]:
            return SimpleNamespace(stdout=b"")
        if argv == ["git", "rev-parse", "HEAD"]:
            return SimpleNamespace(stdout=head.encode())
        assert argv[:2] == ["gh", "api"]
        endpoint = argv[2].removeprefix("repos/keith1117/TopoLab/")
        if endpoint == "commits/main":
            result = {"sha": head}
        elif endpoint == "branches/main/protection":
            result = {
                "required_status_checks": {"strict": True, "contexts": [
                    "quality", "frontend", "clean-linux-smoke",
                ]},
                "enforce_admins": {"enabled": True},
                "allow_force_pushes": {"enabled": False},
                "allow_deletions": {"enabled": False},
                "required_conversation_resolution": {"enabled": True},
            }
        elif endpoint == "actions/runs?head_sha=" + head + "&per_page=100":
            result = {"workflow_runs": [{"head_sha": head, "head_branch": "main",
                                        "status": "completed", "conclusion": "success",
                                        "id": 4242}]}
        elif endpoint == "actions/runs/4242/jobs?per_page=100":
            result = {"jobs": [{"name": name, "status": "completed", "conclusion": "success"}
                               for name in ["quality", "frontend", "clean-linux-smoke",
                                            "i1-native-software"]]}
        else:
            raise AssertionError("unexpected network endpoint: " + endpoint)
        return SimpleNamespace(stdout=json.dumps(result).encode())

    monkeypatch.setattr(checker.native, "_software_bytes", software)
    monkeypatch.setattr(checker, "check_funded_preflight", preflight)
    monkeypatch.setattr(control.subprocess, "run", command)
    monkeypatch.setattr(control.time, "time", lambda: 1793169554 + 3600)
    result = control.activation_readiness(value)
    assert result["main"] == head
    assert result["main_CI_run"] == 4242
    assert set(observed) == {
        str(REPO / control.NEW_PROTOCOL), value["independent_preflight_path"],
        *value["preparation_closure_paths"],
    }


def test_new_source_clock_charges_setup_and_refuses_a_shortened_suffix():
    control = controller()
    value = json.loads(control.NEW_AUTHORITY_RAW)
    clocks = control.source_role_windows(value, 1000, 1001, 1002)
    assert clocks["caller_deadline"] == 5500
    assert clocks["native_deadline"] == 5501
    with pytest.raises(ValueError, match="SOURCE_CALLER_SUFFIX_UNAVAILABLE"):
        control.source_role_windows(value, 1000, 1001, 1301)
    with pytest.raises(ValueError, match="NEW_SOURCE_SUFFIX_RESERVATION_REQUIRED"):
        control.source_role_windows(value, 1000, 1001, 1002, minimum_remaining=1)


def test_unstarted_closeout_funding_never_reopens_source_calls_or_old_windows():
    control = controller()
    value = json.loads(control.NEW_AUTHORITY_RAW)
    value["total_new_author_charged_seconds_cap"] = 201600
    value["budget"]["total_author_seconds_cap"] = 201600
    value["budget"]["all_review_and_new_adapter_author_seconds_cap"] = 36000
    value["budget"]["independent_author_seconds_cap"] = 82800
    value["budget"]["conditional_independent_seconds_cap"] = 39600
    value["budget"]["source_result_each_author_each_attempt"] = 9000
    value["result_seconds"] = {"exporter": 9000, "independent": 9000}
    value["budget_allocation_raw_sha256"] = (
        "02d3e2853a6d9e474b2eaa201d7a1cc88675dd9c58f64e61b9ae93beec4022b3"
    )
    plan = control.formal_plan(control.base().canonical(value))
    assert plan["binding"]["formal_attempt"] == 1
    assert value["budget"]["source_CLI_max"] == 26
    assert value["budget"]["source_max_reads_each_attempt"] == 1196
    assert value["budget"]["source_FULL_max"] == 3780
    value["budget"]["source_attempts"] = 2
    with pytest.raises(ValueError, match="NEW_SOURCE_AUTHORITY_PARAMETERS_DIFFER"):
        control.formal_plan(control.base().canonical(value))
