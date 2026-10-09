"""Frozen panel, independent operation/interval audit and bounded rejection probes."""

import ast
import copy
import importlib.util
import json
import math
import sys
from dataclasses import FrozenInstanceError, asdict, replace
from fractions import Fraction
from pathlib import Path

import pytest

from topolab.fixed_construction_witness import (
    BUNDLE_SHA256,
    BUNDLE_VERSION,
    FIXTURE_SHA256,
    ROLE,
    SOURCE_MAIN,
    SQRT_BITS,
    ConstructionScopeError,
    _closed_object,
    _fixed_qr,
    _lower_bound,
    _outward,
    _Recorder,
    _sqrt_enclosure,
    construct_public_witness,
    read_public_fixture,
    validate_public_fixture,
)

ROOT = Path(__file__).parents[1]
PUBLIC_BYTES = (ROOT / "tests/fixtures/b4_39_fixed_construction_witness.json").read_bytes()
ROWS = json.loads(PUBLIC_BYTES)["fixtures"]
CONTRACT = json.loads(
    (ROOT / "docs/planning/b4_39_public_fixed_construction_witness_contract.json").read_bytes()
)
SPEC = importlib.util.spec_from_file_location(
    "b4_39_independent_oracle", ROOT / "scripts/b4_39_construction_oracle.py"
)
assert SPEC is not None and SPEC.loader is not None
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def binding(identifier="constructed-scalar"):
    return {
        "version": BUNDLE_VERSION,
        "role": ROLE,
        "fixture_id": identifier,
        "sha256": BUNDLE_SHA256,
        "source_main": SOURCE_MAIN,
        "free_space": "public-free-space:" + identifier,
    }


def result(row):
    fixture = read_public_fixture(binding(row["id"]), lambda: PUBLIC_BYTES)
    return asdict(construct_public_witness(fixture))


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["id"])
def test_fixed_construction_full_trace_intended_errors_and_bound_or_prescribed_stop(row):
    output = result(row)
    checks, ref = oracle.audit_case(row, output)
    assert all(checks.values()), checks
    assert output["status"] == CONTRACT["expected_outcomes"][row["id"]] == ref["exact_disposition"]
    if row["id"] == "constructed-third":
        assert ref["error_squares"]["stack_to_represented"] > 0
    if row["id"].startswith("intended-stack-"):
        assert ref["error_squares"]["intended_to_stack"] > 0
    if output["status"] == "PASS":
        assert all(output["R_hat"][i][i] > 0 for i in range(len(output["R_hat"])))
        assert output["certificate"]["m_global_minus"] > 0


@pytest.mark.parametrize(
    "change",
    [
        {"role": "label"},
        {"role": "model"},
        {"role": "final"},
        {"role": "expanded-train"},
        {"version": "unknown"},
        {"fixture_id": "unknown"},
        {"sha256": "0" * 64},
        {"source_main": "0" * 40},
        {"extra": "UNKNOWN"},
        {"free_space": "different"},
    ],
)
def test_registered_bindings_deny_before_callback_bytes(change):
    calls = []
    with pytest.raises(ConstructionScopeError, match="DENY_BEFORE_BYTES"):
        read_public_fixture(binding() | change, lambda: calls.append(1) or PUBLIC_BYTES)
    assert calls == []


@pytest.mark.parametrize("family", CONTRACT["structural_denials"])
def test_registered_structural_and_mutation_denials(family):
    row = copy.deepcopy(ROWS[4])
    if family == "duplicate-field":
        with pytest.raises(ConstructionScopeError, match="duplicate"):
            json.loads('{"id":"x","id":"y"}', object_pairs_hook=_closed_object)
        return
    if family == "changed-public-bytes":
        with pytest.raises(ConstructionScopeError, match="changed public bytes"):
            read_public_fixture(binding(), lambda: PUBLIC_BYTES + b" ")
        return
    if family == "mutable-prepared-state":
        fixture = validate_public_fixture(row)
        object.__setattr__(fixture, "intended_stack", [[Fraction(1)]])
        with pytest.raises(ConstructionScopeError, match="immutable"):
            construct_public_witness(fixture)
        return
    if family == "missing-field":
        del row["free_space"]
    elif family == "unknown-field":
        row["unknown"] = "UNKNOWN"
    elif family == "nonfinite-rational":
        row["intended_stack"][0][0] = "NaN"
    elif family == "nonsymmetric-element":
        row["unit_matrices"][1][0][1] = "0"
    elif family == "negative-element":
        row["unit_matrices"][0][0][0] = "-1"
    elif family == "ragged-stack":
        row["intended_stack"][0] = ["1"]
    elif family == "wrong-stack-space":
        row["stack_space"] = "different"
    elif family == "nonzero-dirichlet":
        row["dirichlet"] = "nonzero"
    elif family == "changed-identity":
        row["id"] = "unknown"
    elif family == "float-instead-of-rational":
        row["intended_stack"][0][0] = 1.0
    elif family == "out-of-dimension-limit":
        row["intended_stack"] = [["1"]] * 4
    else:
        raise AssertionError(family)
    with pytest.raises(ConstructionScopeError):
        validate_public_fixture(row)


@pytest.mark.parametrize(
    "value",
    [
        Fraction(0),
        Fraction(1),
        Fraction(2),
        Fraction(1, 3),
        Fraction(1, 2**40),
        Fraction(1, 2**1075),
    ],
)
def test_six_fixed_grid_outward_endpoint_vectors(value):
    low, high = _sqrt_enclosure(value)
    assert 0 <= low**2 <= value <= high**2
    assert high - low <= Fraction(1, 2**SQRT_BITS)
    assert Fraction(_outward(value, upper=False)) <= value
    assert Fraction(_outward(value, upper=True)) >= value


@pytest.mark.parametrize("family", CONTRACT["arithmetic_stops"])
def test_registered_arithmetic_stops_do_not_change_algorithm_or_precision(family):
    rec = _Recorder()
    with pytest.raises(ConstructionScopeError):
        if family == "negative-sqrt":
            _sqrt_enclosure(Fraction(-1))
        elif family == "binary64-overflow2**1024":
            _outward(Fraction(2**1024), upper=True)
        elif family == "negative-error":
            _lower_bound(-1.0, 0.0, 1.0)
        elif family == "nonfinite-error":
            _lower_bound(math.nan, 0.0, 1.0)
        elif family == "eta-boundary":
            _lower_bound(0.0, 1.0, 1.0)
        elif family == "zero-M":
            _lower_bound(0.0, 0.0, 0.0)
        elif family == "qr-product-overflow":
            _fixed_qr(((1e308,),), rec)
        elif family == "qr-square-underflow":
            _fixed_qr(((1e-200,),), rec)
        else:
            raise AssertionError(family)
    if family.startswith("qr-"):
        assert rec.trace
    assert SQRT_BITS == 80


@pytest.mark.parametrize("field", CONTRACT["tampered_fields"])
def test_independent_audit_rejects_forged_certificate_field(field):
    output = result(ROWS[4])
    c = output["certificate"]
    if field in ("public_intended_only", "diagnostic_only", "real_fem_certified"):
        c[field] = not c[field]
    elif field in ("delta_plus", "eta_plus", "M_plus"):
        c[field] = -1.0
    else:
        c[field] *= 2
    checks, _ = oracle.audit_case(ROWS[4], output)
    assert not all(checks.values()), (field, checks)


@pytest.mark.parametrize("family", CONTRACT["construction_tampering"])
def test_independent_audit_rejects_forged_construction_or_trace(family):
    output = result(ROWS[4])
    if family in ("A_hat", "Q_transpose_hat", "R_hat", "Y_hat"):
        output[family] = [list(row) for row in output[family]]
        output[family][0][0] += 1.0
    elif family == "trace-op":
        output["trace"][6]["op"] = "div"
    elif family == "trace-operand":
        output["trace"][6]["left"] = "0x1p+8"
    elif family == "trace-result":
        output["trace"][6]["result"] = "0x1p+8"
    elif family == "trace-extra":
        output["trace"] = [*output["trace"], output["trace"][0]]
    checks, _ = oracle.audit_case(ROWS[4], output)
    assert not all(checks.values()), (family, checks)


def test_immutable_fixture_revalidates_replacement_and_evidence_is_immutable():
    f = validate_public_fixture(ROWS[0])
    evidence = construct_public_witness(f)
    with pytest.raises(FrozenInstanceError):
        evidence.status = "repaired"
    with pytest.raises(ConstructionScopeError, match="changed public fixture"):
        construct_public_witness(replace(f, intended_stack=((Fraction(2),),)))


def test_four_original_objects_and_frozen_fixture_fingerprints_match_in_full():
    old = json.loads(
        (
            ROOT / "docs/planning/b4_38_public_witness_limitations_real_construction_contract.json"
        ).read_bytes()
    )
    for field in (
        "future_criteria_unchanged",
        "preserved_failures",
        "preserved_cost",
        "full_training_memory",
    ):
        assert CONTRACT[field] == old[field]
    assert FIXTURE_SHA256 == CONTRACT["fixture_sha256"]
    assert BUNDLE_SHA256 == CONTRACT["bundle_sha256"]


@pytest.mark.parametrize(
    "path",
    ["src/topolab/fixed_construction_witness.py", "scripts/b4_39_construction_oracle.py"],
)
def test_candidate_and_oracle_stdlib_only_no_actual_access(path):
    for node in ast.walk(ast.parse((ROOT / path).read_text())):
        if isinstance(node, ast.Import):
            assert all(x.name.split(".")[0] in sys.stdlib_module_names for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module and node.module.split(".")[0] in sys.stdlib_module_names
        elif isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
            )
            assert name not in {
                "open",
                "Path",
                "read_bytes",
                "read_text",
                "solve",
                "eigh",
                "cholesky",
                "spsolve",
                "fit",
                "backward",
            }
