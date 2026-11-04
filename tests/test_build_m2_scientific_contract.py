"""Pure metadata constructor checks; synthetic bindings confer no admission."""
import ast
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(os.environ.get("TOPO_SCIENCE_SOURCE", Path(__file__).parents[1]))
CANDIDATE = Path(__file__).parents[1]
pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="fixed M2 native Darwin contract")


def load_builder():
    path = CANDIDATE / "scripts/build_m2_scientific_contract.py"
    spec = importlib.util.spec_from_file_location("m2_scientific_contract_candidate", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.REPO = REPO
    return module


@pytest.fixture(scope="module")
def inputs():
    builder = load_builder()
    control = builder.orchestration()
    local = control.load("p17_m2_local_input_independent")
    from topolab.b4_reflection_repair import cases

    definitions = [case.model_dump(mode="json") for case in cases("sentinel")]
    proposal = json.loads((REPO / builder.PROPOSAL_PATH).read_bytes())
    assert hashlib.sha256(control.canonical(definitions)).hexdigest() == (
        "c68758e494d62515bfe189323c328209e023b3df73dd7c4ee49495857d40a388"
    )
    registry = {
        "models": [
            {"family": family, "seed": seed, "epoch": epoch}
            for family, epochs in local.EPOCHS.items()
            for seed, epoch in zip((17, 29, 43), epochs, strict=True)
        ],
        "labels": [
            {"case_id": "tlcase-v1-" + hashlib.sha256(str(i).encode()).hexdigest()}
            for i in range(528)
        ],
    }
    registry["labels"].sort(key=lambda item: item["case_id"])
    members = local.expected_members(registry)
    producer = sorted(name for name in members if name == "models.json" or
                      name.startswith(("checkpoints/", "nn/producer/")))
    auditor = sorted(producer + [name for name in members if name.startswith("nn/audit/")])
    registry_raw = control.canonical(registry)
    manifest = {
        "schema": local.MANIFEST_SCHEMA,
        "frozen_contract_sha256": "a" * 64,
        "content_scope_sha256": local.CONTENT_SCOPE_SHA256,
        "source_registry_sha256": hashlib.sha256(registry_raw).hexdigest(),
        "members": [
            {"path": name, "type": kind,
             "byte_size": len(registry_raw) if name == "source_registry.json" else 1,
             "sha256": hashlib.sha256(registry_raw).hexdigest()
             if name == "source_registry.json" else "b" * 64}
            for name, kind in sorted(members.items())
        ],
        "role_views": {"scientific-producer": producer, "scientific-auditor": auditor,
                       "reference-compatibility": ["uniform-scalars.json"]},
    }
    version = hashlib.sha256(control.canonical(manifest)).hexdigest()
    acquisition = {"plan_sha256": "c" * 64, "version_id": version,
                   "manifest_sha256": version,
                   "content_root": "/private/tmp/new-accepted-public-metadata-only/content",
                   "shared_packet_sha256": "d" * 64}
    return builder, acquisition, definitions, manifest, registry, proposal


def construct(inputs, **changes):
    builder, acquisition, definitions, manifest, registry, _ = inputs
    arguments = {"acquisition": deepcopy(acquisition), "case_definitions": deepcopy(definitions),
                 "manifest": deepcopy(manifest), "registry": deepcopy(registry)}
    arguments.update(changes)
    return builder.build_contract(**arguments)


def test_full_contract_passes_existing_independent_checker_without_checker_patch(inputs):
    builder, _, definitions, _, _, proposal = inputs
    value = construct(inputs)
    control = builder.orchestration()
    audit = control.load("p17_m2_scientific_independent")
    assert audit.check_contract(value) == hashlib.sha256(control.canonical(value)).hexdigest()
    assert value["runtime"] == control.scientific_runtime()
    assert value["source_freeze"] == control.source_manifest()
    assert value["case_definitions"] == definitions
    assert value["call_plan"] == control.load("p17_m2_scientific_control").build_call_plan(proposal)
    assert value["independent_operation_caps"] == audit.OPERATIONS
    assert len(value["historical_accepted_P_units"]) == 49
    assert len(control.canonical(value)) <= 4 * 1024**2
    assert value["public_fixture_only"] is False
    assert value["scientific_available_bytes_min"] >= sum(
        cap["total_bytes_max"] for cap in value["output_caps"].values()
    ) + value["api_metadata"]["limits"]["max_total_bytes"]


def test_complete_graph_has_exact_registered_starts_and_five_shared_helpers(inputs):
    builder = inputs[0]
    value = construct(inputs)
    control = builder.orchestration()
    role_names = ["resource-preflight", "scientific-producer", "scientific-auditor"]
    assert list(value["roles"]) == role_names
    assert [value["roles"][r]["FULL_seconds"] for r in role_names] == [180, 10800, 3600]
    assert value["shared_FULL_seconds"] == 180
    assert sum(len(v) for v in value["shared_helpers"].values()) == 5
    assert len(value["input_role_views"]["scientific-producer"]) == 542
    assert len(value["input_role_views"]["scientific-auditor"]) == 1070
    sha = hashlib.sha256(control.canonical(value)).hexdigest()
    for role in role_names:
        spec = value["roles"][role]
        for label in ["controller", "binder", "verifier", "final-observer"]:
            dispatch = spec["native_dispatch"][label]
            timed = spec["exit_argv"][label]
            assert timed[:4] == ["/usr/bin/time", "-l", "-o", dispatch["profile_path"]]
            assert dispatch["dispatch_argv"][-2:] == ["--label", label]
            assert "@SCIENTIFIC_CONTRACT_SHA256@" in dispatch["dispatch_argv"]
            assert "@SCIENTIFIC_CONTRACT_SHA256@" not in control.resolved_argv(timed, sha)
        for label, helper in value["shared_helpers"][role].items():
            assert helper["argv"][:4] == ["/usr/bin/time", "-l", "-o", helper["profile_path"]]
            assert helper["dispatch_argv"][-2:] == ["--label", label]
        if role != "resource-preflight":
            actions = value["reader_actions"][role]
            assert actions["consume"] == spec["inner_starts"][0]["argv"]
            assert actions["ack"] == value["shared_helpers"][role]["reader-ack"]["argv"][4:]
            assert actions["ack"][0] == value["runtime"]["python_entry"]
            assert spec["inner_starts"][0]["expected_exit_code"] == 0
    assert value["api_metadata"]["root"] == builder.OUTPUT_ROOT
    assert set(value["api_metadata"]["manifests"]) == {"B", "FINAL"}


def test_preflight_contract_matches_real_public_controller_without_native_start(inputs):
    builder = inputs[0]
    control = builder.orchestration()
    value = construct(inputs)
    spec = value["roles"]["resource-preflight"]
    # Execute only the original function's literal metadata assignment. No
    # controller, native wrapper, filesystem operation or scientific call runs.
    tree = ast.parse(inspect.getsource(control.public_preflight))
    assignment = next(node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "specifications"
                              for t in node.targets))
    context = {"python": value["runtime"]["python_entry"], "program": str(
        REPO / "scripts/p17_m2_scientific_orchestration.py"),
        "REPO": REPO, "output": Path(spec["root"]) / "controls"}
    exec(compile(ast.Module(body=[assignment], type_ignores=[]), "public-specifications", "exec"),
         context)
    for (name, argv, maximum), registered in zip(context["specifications"],
                                                spec["inner_starts"], strict=True):
        assert (name, argv, maximum) == (registered["name"], registered["argv"],
                                         registered["timeout_seconds"])


@pytest.mark.parametrize("mutation", ["missing", "extra", "bad-sha", "relative", "trailing",
                                    "manifest-hash", "version"])
def test_rejects_malformed_or_unbound_acquisition(inputs, mutation):
    value = deepcopy(inputs[1])
    if mutation == "missing":
        del value["plan_sha256"]
    elif mutation == "extra":
        value["accepted"] = True
    elif mutation == "bad-sha":
        value["plan_sha256"] = "A" * 64
    elif mutation == "relative":
        value["content_root"] = "relative/content"
    elif mutation == "trailing":
        value["content_root"] += "/"
    elif mutation == "manifest-hash":
        value["manifest_sha256"] = "e" * 64
    else:
        value["version_id"] = "e" * 64
    with pytest.raises(ValueError):
        construct(inputs, acquisition=value)


@pytest.mark.parametrize("mutation", ["missing", "reverse", "id", "quality"])
def test_rejects_nonfrozen_case_population(inputs, mutation):
    values = deepcopy(inputs[2])
    if mutation == "missing":
        values.pop()
    elif mutation == "reverse":
        values.reverse()
    elif mutation == "id":
        values[0]["case_id"] = "tlcase-v1-" + "a" * 64
    else:
        values[0]["problem"]["optimization"]["convergence_tolerance"] = 0.02
    with pytest.raises(ValueError):
        construct(inputs, case_definitions=values)


@pytest.mark.parametrize("mutation", ["epoch", "seed", "duplicate", "label-count"])
def test_rejects_model_or_train_identity_change_using_existing_manifest_checker(inputs, mutation):
    registry = deepcopy(inputs[4])
    if mutation == "epoch":
        registry["models"][0]["epoch"] += 1
    elif mutation == "seed":
        registry["models"][0]["seed"] = 18
    elif mutation == "duplicate":
        registry["models"][1] = deepcopy(registry["models"][0])
    else:
        registry["labels"].pop()
    with pytest.raises(ValueError):
        construct(inputs, registry=registry)


def test_rejects_unfrozen_runtime_and_source(inputs):
    builder = inputs[0]
    runtime = builder.orchestration().scientific_runtime()
    runtime["python_entry"] = runtime["python_physical"]
    with pytest.raises(ValueError):
        construct(inputs, runtime=runtime)
    freeze = builder.orchestration().source_manifest()
    freeze["scripts/p17_m2_scientific_independent.py"] = "a" * 64
    with pytest.raises(ValueError):
        construct(inputs, source_freeze=freeze)


def audit_payload(inputs, contract):
    builder, _, definitions, _, _, proposal = inputs
    control = builder.orchestration()
    audit = control.load("p17_m2_scientific_independent")
    metadata = {item["case_id"]: {"scale": tuple(item["problem"]["mesh"]["element_counts"]),
                "direction": item["problem"]["loads"][0]["direction"],
                "volume": item["problem"]["optimization"]["volume_fraction"]}
                for item in definitions}
    target = "tlcase-v1-55c1b3e64135c23125fc286de5d780fc5d9a1e226d5e43ff0dbc8925b423936a"
    negatives = set(proposal["acceptance"]["negative_control_case_ids"])
    rows = [{"case_id": row["case_id"], "method": row["method"],
             "attempt_accepted": not (row["case_id"] == target and row["method"] == "plain-P/17"
              or row["case_id"] in negatives and row["method"] in ("plain-P/29", "H/29")),
             "fallback_occurred": False, "charged_seconds": 2.0}
            for row in contract["call_plan"]["queries"]]
    decision = audit.assess_panel(proposal, metadata, rows, contract["historical_accepted_P_units"])
    descriptors = [{"phase": phase, "ordinal": row["ordinal"], "case_id": row["case_id"],
                    "method": row["method"], "attempt_accepted": True}
                   for phase, key in (("reference", "references"), ("query", "queries"))
                   for row in contract["call_plan"][key]]
    sha = hashlib.sha256(control.canonical(contract)).hexdigest()
    summary = {"schema": "topolab.v2.m2-scientific-auditor-summary.v1",
               "execution_identity": contract["execution_identity"],
               "scientific_contract_sha256": sha, "status": decision["outcome_status"],
               "attempted_rows": 360, "completed_rows": descriptors, "decision": decision,
               "internal_row_charge_seconds": 360.0,
               "own_resource_and_actual_exit": "PENDING_INDEPENDENT_NATIVE_OUTER_RETURN",
               "seed17_repaired": "NOT_ESTABLISHED_BEFORE_OWN_NATIVE_RETURN"}
    raw = control.canonical(summary)
    summary["summary_packet"] = {"path": "auditor-summary.json", "byte_size": len(raw),
                                 "sha256": hashlib.sha256(raw).hexdigest()}
    start = contract["roles"]["scientific-auditor"]["inner_starts"][0]
    startup = control.startup_argv(start["argv"], sha, contract["runtime"])
    return {"result": summary, "reader_pending": {"public_seam_only": True},
            "actual_numerical_runtime": {"python_entry": contract["runtime"]["python_entry"],
                "startup_orig_argv": startup,
                "torch_threads": contract["runtime"]["torch_threads_policy"]}}


def test_auditor_transport_preserves_original_packet_decision_failure_and_reader(inputs):
    builder = inputs[0]
    contract = construct(inputs)
    payload = audit_payload(inputs, contract)
    original = deepcopy(payload)
    result = builder.project_auditor_completion(contract, payload)
    assert payload == original
    assert result["result"]["completed_rows"] == 360
    assert result["result"]["completed_row_descriptors"] == original["result"]["completed_rows"]
    assert result["result"]["summary_packet"] == original["result"]["summary_packet"]
    assert result["result"]["decision"] == original["result"]["decision"]
    assert result["result"]["status"] == original["result"]["status"] == "FAIL_SCIENCE_GATE"
    assert result["reader_pending"] == original["reader_pending"]
    reconstructed = deepcopy(result["result"])
    reconstructed["completed_rows"] = reconstructed.pop("completed_row_descriptors")
    del reconstructed["completion_transport_projection"]
    assert reconstructed == original["result"]


@pytest.mark.parametrize("mutation", ["missing", "reverse", "duplicate", "forged-acceptance",
                                    "receipt-hash", "receipt-size"])
def test_auditor_transport_rejects_incomplete_or_changed_independent_results(inputs, mutation):
    builder = inputs[0]
    contract = construct(inputs)
    payload = audit_payload(inputs, contract)
    summary = payload["result"]
    if mutation == "missing":
        summary["completed_rows"].pop()
    elif mutation == "reverse":
        summary["completed_rows"].reverse()
    elif mutation == "duplicate":
        summary["completed_rows"][1] = deepcopy(summary["completed_rows"][0])
    elif mutation == "forged-acceptance":
        summary["completed_rows"][0]["attempt_accepted"] = "true"
    elif mutation == "receipt-hash":
        summary["summary_packet"]["sha256"] = "0" * 64
    else:
        summary["summary_packet"]["byte_size"] += 1
    with pytest.raises(ValueError):
        builder.project_auditor_completion(contract, payload)


def test_original_native_return_checker_accepts_registered_projected_startup(inputs, monkeypatch):
    builder = inputs[0]
    contract = construct(inputs)
    control = builder.orchestration()
    audit = control.load("p17_m2_scientific_independent")
    payload = builder.project_auditor_completion(contract, audit_payload(inputs, contract))
    sha = hashlib.sha256(control.canonical(contract)).hexdigest()
    # Only the resource envelope is a public seam; the original startup/Torch
    # validator and opaque checked-return constructor execute unmodified.
    monkeypatch.setattr(audit, "_check_role_envelope", lambda *args: {
        "scientific_contract_sha256": sha, "public_envelope_seam_only": True})
    evidence = {"cases": [{"log": control.canonical(payload),
                           "record": {"samples": [{"roles": [{"pid": 123}]}]}}]}
    result = audit.check_scientific_role(contract, "scientific-auditor", evidence)
    assert result.command_log == control.canonical(payload)
    assert result.proof["public_envelope_seam_only"] is True
    assert result.proof["observed_command_pids"] == [123]


def test_actual_js_validator_rejects_original_list_and_accepts_transparent_projection(inputs,
                                                                                   tmp_path):
    builder = inputs[0]
    contract = construct(inputs)
    control = builder.orchestration()
    original = audit_payload(inputs, contract)
    projected = builder.project_auditor_completion(contract, original)
    path = tmp_path / "public-auditor-transport-metadata.json"
    path.write_bytes(control.canonical({"contract": contract, "original": original,
                                       "projected": projected}))
    program = CANDIDATE / "tests/check_auditor_transport.mjs"
    command = ["node", str(program), str(REPO), str(path)]
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "original-list rejected; projected FAIL preserved" in result.stdout


def test_construct_cli_requires_tracked_builder_before_reading_metadata(inputs, monkeypatch):
    builder = inputs[0]
    control = builder.orchestration()
    monkeypatch.setattr(control, "source_manifest", lambda: {})
    monkeypatch.setattr(sys, "argv", ["build_m2_scientific_contract.py", "construct", "--metadata",
                                    "/UNGRANTED_METADATA_MUST_NOT_BE_READ.json"])
    with pytest.raises(ValueError, match="tracked builder source required"):
        builder.main()


def test_construction_never_opens_or_stats_acquisition_or_future_science_roots(inputs, monkeypatch):
    builder = inputs[0]
    target_prefixes = (builder.OUTPUT_ROOT, inputs[1]["content_root"])
    original_open, original_stat = Path.open, os.stat
    def opened(path, *args, **kwargs):
        assert not str(path).startswith(target_prefixes)
        return original_open(path, *args, **kwargs)
    def stated(path, *args, **kwargs):
        assert not str(path).startswith(target_prefixes)
        return original_stat(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", opened)
    monkeypatch.setattr(os, "stat", stated)
    construct(inputs)
