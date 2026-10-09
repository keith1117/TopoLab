"""Frozen authored witness panel, independent endpoint audit and finite denial families."""

import ast
import copy
import importlib.util
import json
import math
from dataclasses import FrozenInstanceError, asdict, replace
from fractions import Fraction
from pathlib import Path

import pytest

from topolab.coercivity_witness import (
    BUNDLE_SHA256,
    BUNDLE_VERSION,
    FIXTURE_SHA256,
    ROLE,
    SOURCE_MAIN,
    SQRT_BITS,
    WitnessScopeError,
    _closed_object,
    _lower_bound,
    _outward,
    _sqrt_enclosure,
    certify_public_witness,
    read_public_fixture,
    validate_public_fixture,
)

ROOT = Path(__file__).parents[1]
PUBLIC_BYTES = (ROOT / "tests/fixtures/b4_37_coercivity_witness.json").read_bytes()
ROWS = json.loads(PUBLIC_BYTES)["fixtures"]
CONTRACT = json.loads(
    (ROOT / "docs/planning/b4_37_public_coercivity_witness_contract.json").read_bytes()
)
SPEC = importlib.util.spec_from_file_location(
    "b4_37_independent_oracle", ROOT / "scripts/b4_37_coercivity_oracle.py"
)
assert SPEC is not None and SPEC.loader is not None
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def binding(identifier="scalar-exact"):
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
    try:
        return {
            "fixture_id": row["id"],
            "status": "PASS",
            "certificate": asdict(certify_public_witness(fixture)),
            "error": None,
        }
    except WitnessScopeError as exc:
        return {
            "fixture_id": row["id"],
            "status": str(exc).split(":")[0],
            "certificate": None,
            "error": str(exc),
        }


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["id"])
def test_ten_prescribed_witnesses_or_stops_against_independent_exact_inequalities(row):
    output = result(row)
    checks, ref = oracle.audit_case(row, output)
    assert all(checks.values()), checks
    assert output["status"] == CONTRACT["expected_outcomes"][row["id"]] == ref["exact_disposition"]
    if row["id"] in ("scalar-intended-plus", "scalar-intended-minus", "coupled-intended-error"):
        assert ref["delta_squared"] > 0
        assert output["certificate"]["delta_plus"] > 0


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
        {"extra": "unknown"},
        {"free_space": "different"},
    ],
)
def test_ten_wrong_bindings_deny_before_callback_bytes(change):
    calls = []
    with pytest.raises(WitnessScopeError, match="DENY_BEFORE_BYTES"):
        read_public_fixture(binding() | change, lambda: calls.append(1) or PUBLIC_BYTES)
    assert calls == []


@pytest.mark.parametrize("family", CONTRACT["structural_denials"])
def test_fifteen_registered_structural_and_mutation_denials(family):
    row = copy.deepcopy(ROWS[3])
    if family == "duplicate-field":
        with pytest.raises(WitnessScopeError, match="duplicate"):
            json.loads('{"id":"x","id":"y"}', object_pairs_hook=_closed_object)
        return
    if family == "changed-public-bytes":
        with pytest.raises(WitnessScopeError, match="digest"):
            read_public_fixture(binding(), lambda: PUBLIC_BYTES + b" ")
        return
    if family == "mutable-prepared-state":
        fixture = validate_public_fixture(row)
        object.__setattr__(fixture, "energy_factor", [[Fraction(1)]])
        with pytest.raises(WitnessScopeError, match="immutable"):
            certify_public_witness(fixture)
        return
    if family == "missing-field":
        del row["free_space"]
    elif family == "unknown-field":
        row["unknown"] = "UNKNOWN"
    elif family == "nonfinite-rational":
        row["energy_factor"][0][0] = "NaN"
    elif family == "nonsymmetric-element":
        row["unit_matrices"][0][0][1] = "0"
    elif family == "negative-element":
        row["unit_matrices"][0][0][0] = "-1"
    elif family == "ragged-factor":
        row["energy_factor"][0] = ["1"]
    elif family == "wrong-witness-dimension":
        row["left_inverse_witness"] = [["1"]]
    elif family == "wrong-space":
        row["witness_space"] = "different"
    elif family == "nonzero-dirichlet":
        row["dirichlet"] = "nonzero"
    elif family == "changed-identity":
        row["id"] = "unknown"
    elif family == "float-instead-of-rational":
        row["energy_factor"][0][0] = 1.0
    elif family == "out-of-dimension-limit":
        row["energy_factor"] = [["1"]] * 4
    else:
        raise AssertionError(family)
    with pytest.raises(WitnessScopeError):
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
def test_six_exact_fixed_grid_and_binary64_endpoint_vectors(value):
    low, high = _sqrt_enclosure(value)
    assert 0 <= low**2 <= value <= high**2
    assert high - low <= Fraction(1, 2**SQRT_BITS)
    assert Fraction.from_float(_outward(value, upper=False)) <= value
    assert Fraction.from_float(_outward(value, upper=True)) >= value


@pytest.mark.parametrize("family", CONTRACT["arithmetic_stops"])
def test_eight_arithmetic_stops_never_expand_precision(family):
    with pytest.raises(WitnessScopeError):
        if family == "negative-sqrt":
            _sqrt_enclosure(Fraction(-1))
        elif family == "binary64-overflow2**1024":
            _outward(Fraction(2**1024), upper=True)
        elif family == "negative-error":
            _lower_bound(-1.0, 0.0, 1.0, Fraction(1, 1000))
        elif family == "nonfinite-error":
            _lower_bound(math.nan, 0.0, 1.0, Fraction(1, 1000))
        elif family == "eta-boundary":
            _lower_bound(0.0, 1.0, 1.0, Fraction(1, 1000))
        elif family == "zero-M":
            _lower_bound(0.0, 0.0, 0.0, Fraction(1, 1000))
        elif family == "ratio-square-underflow":
            _lower_bound(0.0, 0.0, 1e308, Fraction(1, 1000))
        elif family == "material-lower-underflow":
            _lower_bound(0.0, 0.0, 1.0, Fraction(1, 2**1075))
        else:
            raise AssertionError(family)
    assert SQRT_BITS == 80


@pytest.mark.parametrize("field", CONTRACT["tampered_fields"])
def test_independent_audit_rejects_each_forged_certificate_field(field):
    row = ROWS[5] if field == "eta_plus" else ROWS[4]
    output = result(row)
    c = output["certificate"]
    if field in ("public_intended_only", "diagnostic_only", "real_fem_certified"):
        c[field] = not c[field]
    elif field in ("delta_plus", "eta_plus", "M_plus"):
        c[field] = 0.0
    else:
        c[field] *= 2
    checks, _ = oracle.audit_case(row, output)
    assert not all(checks.values()), (field, checks)


def test_prepared_fingerprint_rechecks_replacement_and_bound_is_immutable():
    fixture = validate_public_fixture(ROWS[0])
    bound = certify_public_witness(fixture)
    with pytest.raises(FrozenInstanceError):
        bound.lower_G_minus = 0
    with pytest.raises(WitnessScopeError, match="changed"):
        certify_public_witness(replace(fixture, energy_factor=((Fraction(2),),)))
    assert bound.public_intended_only and bound.diagnostic_only and not bound.real_fem_certified


def test_intended_positive_operator_can_stop_without_an_alternate_witness():
    output = result(ROWS[8])
    ref = oracle.reference(ROWS[8])
    assert output["status"] == "STOP_COERCIVITY" and output["certificate"] is None
    assert ref["G"] == [[Fraction(1, 100), 0], [0, Fraction(1)]]


def test_four_original_criteria_failure_cost_memory_objects_are_unchanged():
    old = json.loads(
        (ROOT / "docs/planning/b4_36_certificate_limitations_real_route_contract.json").read_bytes()
    )
    for field in (
        "future_criteria_unchanged",
        "preserved_failures",
        "preserved_cost",
        "full_training_memory",
    ):
        assert CONTRACT[field] == old[field]
    assert FIXTURE_SHA256 == CONTRACT["fixture_sha256"]


@pytest.mark.parametrize(
    "path", ["src/topolab/coercivity_witness.py", "scripts/b4_37_coercivity_oracle.py"]
)
def test_candidate_and_independent_oracle_are_stdlib_only_with_no_io_or_solver(path):
    import sys

    tree = ast.parse((ROOT / path).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(x.name.split(".")[0] in sys.stdlib_module_names for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module and node.module.split(".")[0] in sys.stdlib_module_names
        elif isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
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
