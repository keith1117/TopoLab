"""Accepted R0 literal registry must remain the R1 source boundary."""

import importlib.util
import os
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


@pytest.mark.parametrize("role", ["exporter-r1", "independent-r1"])
@pytest.mark.parametrize("changed", [False, True])
def test_changed_registry_refuses_before_any_r1_payload_stat_or_open(
    tmp_path, monkeypatch, role, changed
):
    """Real R0 algorithms; native acceptance is an explicit unit boundary only."""
    spec = importlib.util.spec_from_file_location(
        "registry_acceptance_public_control", REPO / "scripts/p17_m2_source_acquisition_control.py")
    assert spec and spec.loader
    control = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = control
    spec.loader.exec_module(control)
    helper = control.base()
    monkeypatch.setattr(control, "base", lambda: helper)
    root = tmp_path.resolve() / "topolab-public-new-source-acquisition-registry-boundary"
    root.mkdir(mode=0o700)
    producer = control.load("p17_m2_input_export")
    local = control.load("p17_m2_local_input_version")
    checker = control.load("p17_m2_source_acquisition_independent")
    source = root / "public-source"
    public_fixture = control.load("p17_m2_content_verified_public_fixture")
    contract, source_identity = public_fixture.create_sources(
        source, control.load("p17_m2_input_export_independent"))
    plan = control.make_plan(root, contract, source_identity)
    plan_sha = helper.sha(helper.canonical(plan))
    reader = producer.Reader(
        source, execution_identity=producer.LOCAL_IDENTITY, source_identity_checks=True,
        source_identity_policy=control.SOURCE_IDENTITY_POLICY)
    registry = producer.register(reader, contract)
    reviewed = checker.independent_r0(
        source, contract, registry, reader.source_observations, source_identity, plan=plan)
    assert reviewed["status"] == "SOURCE_ACQUISITION_R0_CHECKED"
    assert reviewed["source_count"] == 40
    assert reviewed["source_registry_sha256"] == helper.sha(helper.canonical(registry))
    helper.put(root / "registry.json", registry)
    helper.put(root / "r0-proof.json", reviewed)
    # The producer records this NEW receipt's digest after its complete export.
    helper.put(root / "custody-acquired.json", {"unit_custody_metadata": True})
    transport = control.AcquisitionTransport(root, plan_sha)
    # This test checks content ingress, not native process/resource admission.
    # Connected-native regressions and the separately frozen public32 own that evidence.
    wire = {"inner_evidence": {"log": helper.canonical(reviewed)}}
    (root / "receipts").mkdir(mode=0o700)
    helper.put(root / "receipts/independent-r0-wire.json", {"unit_native_packet": True})
    monkeypatch.setattr(control.AcquisitionTransport, "resource_evidence", lambda *args:
                        {"inner_evidence": wire["inner_evidence"], "native_profiles": {}})

    def audited(*args, **kwargs):
        if "wire" in kwargs:
            assert kwargs["wire"]["inner_evidence"] is wire["inner_evidence"]
        return {"full_role_evidence_accepted": True}

    monkeypatch.setattr(control.AcquisitionTransport, "audit_saved", audited)
    previous = "independent-r0" if role == "exporter-r1" else "exporter-r1"
    helper.put(root / "independent-r0-accepted.json", {"raw_tool_events": ["UNIT_ONLY"]})
    if previous != "independent-r0":
        helper.put(root / (previous + "-accepted.json"), {"raw_tool_events": ["UNIT_ONLY"]})
    transport.predecessor(root, plan, role)
    if role == "independent-r1":
        content = local.LocalContent(root / "content", registry, plan["contract_sha256"])
        content.write("source_registry.json", producer.canonical(registry))
        original = producer.Reader(
            source, execution_identity=producer.LOCAL_IDENTITY, source_identity_checks=True,
            source_identity_policy=control.SOURCE_IDENTITY_POLICY)
        producer.export(original, registry, contract, content.root, local_content=content)
        closed = content.finish()
        closed["root_identity"] = helper.physical(content.root.stat())
        helper.put(root / "closed.json", closed)
        helper.put(root / "r1-source-rows.json", original.source_observations)
    checkpoint = registry["models"][0]["checkpoint"]
    bad_name = "f" * 64 + ".safetensors"
    if changed:
        checkpoint.update(sha256="f" * 64,
                          path=str(Path(checkpoint["path"]).with_name(bad_name)))
        (root / "registry.json").write_bytes(helper.canonical(registry))
    attempted_payload_io = []
    real_stat, real_open = os.stat, os.open

    def refuse_payload(path, *args, **kwargs):
        if not isinstance(path, int) and Path(os.fsdecode(path)).name == bad_name:
            attempted_payload_io.append({"operation": "stat", "path": str(path)})
            raise ValueError("PUBLIC_PAYLOAD_STAT_BEFORE_R0_BINDING")
        return real_stat(path, *args, **kwargs)

    def refuse_payload_open(path, *args, **kwargs):
        if not isinstance(path, int) and Path(os.fsdecode(path)).name == bad_name:
            attempted_payload_io.append({"operation": "open", "path": str(path)})
            raise ValueError("PUBLIC_PAYLOAD_OPEN_BEFORE_R0_BINDING")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", refuse_payload)
    monkeypatch.setattr(os, "open", refuse_payload_open)
    result = control.payload_body(root, plan, role, transport)
    assert attempted_payload_io == [], attempted_payload_io
    if changed:
        assert result["status"] == "STOP_NO_RETRY"
        assert result["attempted_source_paths"] == []
        context = result["independent_context"]
        assert context["stage"] == "accepted R0 registry before R1"
        assert context["original_payload_reads"] == 0
        observed = context["metadata_reader"]
        assert observed["attempts"] == [
            "independent-r0-accepted.json", "receipts/independent-r0-wire.json", "registry.json"]
        assert len(observed["failures"]) == 1
        failure = observed["failures"][0]
        assert failure["path"] == "registry.json"
        assert all(failure[key] is not None for key in ("declared", "before", "after", "closing"))
    else:
        assert result.get("status") != "STOP_NO_RETRY", result
        assert result["source_count"] == 558
        if role == "exporter-r1":
            assert result["member_count"] == 1071


@pytest.fixture(scope="module")
def registered_public_sources(tmp_path_factory):
    """Derive real finite source declarations; never construct a native acceptance."""
    spec = importlib.util.spec_from_file_location(
        "registry_semantics_control", REPO / "scripts/p17_m2_source_acquisition_control.py")
    assert spec and spec.loader
    control = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = control
    spec.loader.exec_module(control)
    root = (tmp_path_factory.mktemp("registry-semantic-public")
            / "topolab-public-new-source-acquisition-registry-semantic")
    root.mkdir(mode=0o700)
    checker = control.load("p17_m2_source_acquisition_independent")
    producer = control.load("p17_m2_input_export")
    source = root / "public-source"
    contract, identity = control.load("p17_m2_content_verified_public_fixture").create_sources(
        source, control.load("p17_m2_input_export_independent"))
    plan = control.make_plan(root, contract, identity)
    reader = producer.Reader(
        source, execution_identity=producer.LOCAL_IDENTITY, source_identity_checks=True,
        source_identity_policy=control.SOURCE_IDENTITY_POLICY)
    registry = producer.register(reader, contract)
    proof = checker.independent_r0(
        source, contract, registry, reader.source_observations, identity, plan=plan)
    return checker, plan, registry, proof


def test_accepted_registry_uses_the_same_buffer_and_actual_r0_semantic_proof(
    registered_public_sources
):
    checker, plan, registry, proof = registered_public_sources
    raw = checker.canonical(registry)
    wire = {"inner_evidence": {"log": checker.canonical(proof)}}
    accepted = checker.accepted_r0_registry(raw, wire, plan=plan)
    assert accepted == registry
    assert accepted is not registry


@pytest.mark.parametrize("case", [
    "raw-after-r0", "wrong-contract", "wrong-root", "wrong-source-binding", "bool-count",
    "missing-comparison", "missing-observations", "helper-relabel", "wrong-scope",
    "old-identity", "duplicate-payload", "wrong-fixed-model", "noncanonical", "short-buffer",
])
def test_accepted_registry_refuses_changed_or_incomplete_r0_semantic_bindings(
    registered_public_sources, case
):
    checker, plan, original_registry, original_proof = registered_public_sources
    registry, proof = deepcopy(original_registry), deepcopy(original_proof)
    raw = checker.canonical(registry)
    if case == "raw-after-r0":
        registry["models"][0]["checkpoint"]["sha256"] = "f" * 64
        raw = checker.canonical(registry)
    elif case == "wrong-contract":
        proof["source_contract_sha256"] = "f" * 64
    elif case == "wrong-root":
        proof["root"] += "-other"
    elif case == "wrong-source-binding":
        proof["source_identity"]["B3_DATA_HASH"] = "f" * 64
    elif case == "bool-count":
        proof["source_count"] = True
    elif case == "missing-comparison":
        proof.pop("source_comparison")
    elif case == "missing-observations":
        proof["source_rows"] = proof["source_rows"][:-1]
    elif case == "helper-relabel":
        proof["helper_identity_relabelled"] = True
    elif case == "wrong-scope":
        proof["scope"] = checker.FORMAL_SCOPE
    elif case == "old-identity":
        proof["execution_identity"] = checker.FUNDED_IDENTITY
    elif case == "duplicate-payload":
        registry["models"][1]["checkpoint"] = deepcopy(registry["models"][0]["checkpoint"])
        raw = checker.canonical(registry)
        proof["source_registry_sha256"] = checker.digest(raw)
    elif case == "wrong-fixed-model":
        registry["models"][0]["epoch"] += 1
        raw = checker.canonical(registry)
        proof["source_registry_sha256"] = checker.digest(raw)
    elif case == "noncanonical":
        raw += b" "
        proof["source_registry_sha256"] = checker.digest(raw)
    elif case == "short-buffer":
        raw = raw[:-1]
    wire = {"inner_evidence": {"log": checker.canonical(proof)}}
    with pytest.raises(ValueError):
        checker.accepted_r0_registry(raw, wire, plan=plan)


@pytest.mark.parametrize("prefix", [
    "topolab-public-formal-binding-", "topolab-public-hash-bound-",
    "topolab-public-funded-acquisition-",
])
@pytest.mark.parametrize("role", ["exporter-r1", "independent-r1"])
def test_legacy_registry_route_keeps_its_original_metadata_interface(
    tmp_path, monkeypatch, prefix, role
):
    spec = importlib.util.spec_from_file_location(
        "legacy_registry_route_control", REPO / "scripts/p17_m2_source_acquisition_control.py")
    assert spec and spec.loader
    control = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = control
    spec.loader.exec_module(control)
    root = tmp_path / (prefix + "original-route")
    root.mkdir(mode=0o700)
    expected = {"public_legacy_registry": True}
    control.base().put(root / "registry.json", expected)

    def forbidden(*args, **kwargs):
        pytest.fail("legacy registry route attempted new native acceptance requirements")

    monkeypatch.setattr(control.AcquisitionTransport, "resource_evidence", forbidden)
    monkeypatch.setattr(control.AcquisitionTransport, "audit_saved", forbidden)
    transport = control.AcquisitionTransport(root, "a" * 64)
    assert transport.read_registry(root, {}, role) == expected
