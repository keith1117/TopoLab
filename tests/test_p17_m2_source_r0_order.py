"""Both NEW R0 readers follow the frozen metadata order; legacy order stays."""

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def actual_public_r0(tmp_path_factory):
    spec = importlib.util.spec_from_file_location(
        "source_r0_order_control", REPO / "scripts/p17_m2_source_acquisition_control.py")
    assert spec and spec.loader
    control = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = control
    spec.loader.exec_module(control)
    root = (tmp_path_factory.mktemp("source-r0-order")
            / "topolab-public-new-source-acquisition-r0-order")
    root.mkdir(mode=0o700)
    source = root / "public-source"
    source_checker = control.load("p17_m2_input_export_independent")
    contract, identity = control.load("p17_m2_content_verified_public_fixture").create_sources(
        source, source_checker)
    plan = control.make_plan(root, contract, identity)
    producer = control.load("p17_m2_input_export")
    reader = producer.Reader(
        source, execution_identity=producer.LOCAL_IDENTITY, source_identity_checks=True,
        source_identity_policy=control.SOURCE_IDENTITY_POLICY)
    registry = producer.register(reader, contract)
    checker = control.load("p17_m2_source_acquisition_independent")
    proof = checker.independent_r0(
        source, contract, registry, reader.source_observations, identity, plan=plan)
    bootstrap = [row["relative_path"] for row in contract["R0"]["literal_bootstrap_files"]]
    weighted = [f"b4-5-weighted-terminal/fit/units/{i:04d}.json" for i in range(3)]
    selections = [row["selection"]["path"] for row in registry["models"]]
    references = [f"b4-30-z-reflection-repair-v2/sentinel/reference/units/{i:04d}.json"
                  for i in range(18)]
    return {
        "control": control, "checker": checker, "plan": plan,
        "source": source, "contract": contract, "identity": identity,
        "registry": registry, "producer_rows": reader.source_observations, "proof": proof,
        "new_order": bootstrap + weighted + selections + references,
        "legacy_order": bootstrap + weighted + references + selections,
    }


def assert_exact_metadata_reads(rows, expected, *, strict_count=21):
    actual = [row["path"] for row in rows]
    assert len(actual) == len(set(actual)) == len(expected) == 40
    assert set(actual) == set(expected)
    assert sum(row["expected_sha256"] is None for row in rows) == strict_count
    assert sum(row["expected_sha256"] is not None for row in rows) == 40 - strict_count
    for row in rows:
        assert row["identity_policy"] == "topolab.source-identity.prebound-sha256.v1"
        assert all(row[key] is not None for key in ("declared", "before", "after", "closing"))
    assert actual == expected


def test_both_new_r0_readers_observe_frozen_7_3_12_18_order(actual_public_r0):
    data = actual_public_r0
    assert data["proof"]["status"] == "SOURCE_ACQUISITION_R0_CHECKED"
    assert data["proof"]["source_count"] == 40
    assert_exact_metadata_reads(data["producer_rows"], data["new_order"])
    assert_exact_metadata_reads(data["proof"]["source_rows"], data["new_order"])


def test_legacy_registry_reader_keeps_reference_before_selection_order(
    actual_public_r0, monkeypatch
):
    data = actual_public_r0
    checker = data["control"].load("p17_m2_input_export_independent")
    monkeypatch.setattr(checker, "B3_DATA_HASH", data["identity"]["B3_DATA_HASH"])
    monkeypatch.setattr(checker, "CATALOG_HASH", data["identity"]["CATALOG_HASH"])
    reader = checker.OnceReader(
        data["source"], 40, 32 * checker.MIB, source_identity_checks=True,
        source_identity_policy="topolab.source-identity.prebound-sha256.v1")
    registry = checker.build_registry(reader, data["contract"])
    assert registry == data["registry"]
    assert_exact_metadata_reads(reader.observations, data["legacy_order"])


def test_new_registry_order_preserves_23_strict_and_17_prebound_reads(
    actual_public_r0, monkeypatch
):
    """Real reader seam with formal trust split; no formal/native admission."""
    data = actual_public_r0
    contract = deepcopy(data["contract"])
    unbound = {
        "b4-30-z-reflection-repair-v2/sentinel/reference/progress.json",
        "b4-30-z-reflection-repair-v2/sentinel/reference/summary.json",
    }
    for row in contract["R0"]["literal_bootstrap_files"]:
        if row["relative_path"] in unbound:
            row["expected_sha256"] = None
    producer = data["control"].load("p17_m2_input_export")
    produced = producer.Reader(
        data["source"], execution_identity=producer.LOCAL_IDENTITY, source_identity_checks=True,
        source_identity_policy="topolab.source-identity.prebound-sha256.v1")
    registry = producer.register(produced, contract)
    checker = data["control"].load("p17_m2_input_export_independent")
    monkeypatch.setattr(checker, "B3_DATA_HASH", data["identity"]["B3_DATA_HASH"])
    monkeypatch.setattr(checker, "CATALOG_HASH", data["identity"]["CATALOG_HASH"])
    reader = checker.OnceReader(
        data["source"], 40, 32 * checker.MIB, source_identity_checks=True,
        source_identity_policy="topolab.source-identity.prebound-sha256.v1")
    reviewed = checker.build_registry(reader, contract, selection_before_reference=True)
    assert registry == reviewed
    assert_exact_metadata_reads(produced.source_observations, data["new_order"], strict_count=23)
    assert_exact_metadata_reads(reader.observations, data["new_order"], strict_count=23)


@pytest.mark.parametrize("boundary", ["certificate-policy", "R1-registry"])
def test_new_audit_and_r1_ingress_refuse_reordered_real_r0_rows(actual_public_r0, boundary):
    """Replay real read observations at semantic seams, without native authority."""
    data = actual_public_r0
    checker, plan, registry = data["checker"], data["plan"], data["registry"]
    proof = deepcopy(data["proof"])
    rows = {row["path"]: row for row in proof["source_rows"]}
    proof["source_rows"] = [rows[path] for path in data["new_order"]]
    policy = checker._AcquisitionCertificatePolicy(plan)

    def validate():
        if boundary == "certificate-policy":
            return policy.check_source_rows(proof, 40, registry)
        return checker.accepted_r0_registry(
            checker.canonical(registry),
            {"inner_evidence": {"log": checker.canonical(proof)}}, plan=plan)

    validate()
    proof["source_rows"][0], proof["source_rows"][1] = (
        proof["source_rows"][1], proof["source_rows"][0])
    with pytest.raises(ValueError, match="R0.*order"):
        validate()
