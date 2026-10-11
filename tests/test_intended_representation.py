"""Frozen B4.41 public panel, independent interval/IEEE proofs and denials."""

import copy
import importlib.util
import json
import math
from dataclasses import FrozenInstanceError
from fractions import Fraction
from pathlib import Path

import pytest

from topolab import intended_representation as candidate

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_BYTES = (ROOT / "tests/fixtures/b4_41_intended_representation.json").read_bytes()
ROWS = json.loads(BUNDLE_BYTES)["fixtures"]
CONTRACT = json.loads(
    (
        ROOT / "docs/planning/b4_41_public_intended_representation_enclosure_contract.json"
    ).read_bytes()
)
SPEC = importlib.util.spec_from_file_location(
    "b4_41_representation_oracle", ROOT / "scripts/b4_41_representation_oracle.py"
)
assert SPEC is not None and SPEC.loader is not None
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)


def binding(identifier):
    return {
        "version": candidate.BUNDLE_VERSION,
        "role": candidate.ROLE,
        "fixture_id": identifier,
        "sha256": candidate.BUNDLE_SHA256,
        "source_main": candidate.SOURCE_MAIN,
        "free_space": "authored-expression-space:" + identifier,
    }


def run(row):
    f = candidate.read_public_fixture(binding(row["id"]), lambda: BUNDLE_BYTES)
    return candidate.enclose_representation(f).payload()


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["id"])
def test_complete_public_program_and_independent_enclosures(row):
    result = run(row)
    assert result["status"] == CONTRACT["expected_outcomes"][row["id"]]
    audited = ORACLE.audit_case(row, result)
    assert audited["passed"], audited
    assert all(audited["checks"].values())


@pytest.mark.parametrize("denial", CONTRACT["binding_denials"])
def test_all_registered_bindings_deny_before_bytes(denial):
    request = binding(ROWS[0]["id"])
    field = {
        "label-role": "role",
        "model-role": "role",
        "final-role": "role",
        "expanded-train-role": "role",
        "unknown-version": "version",
        "unknown-id": "fixture_id",
        "wrong-bundle-hash": "sha256",
        "wrong-source": "source_main",
        "wrong-space": "free_space",
    }
    if denial == "unknown-field":
        request["extra"] = "unknown"
    elif denial == "missing-field":
        del request["role"]
    else:
        request[field[denial]] = denial
    calls = []
    with pytest.raises(candidate.RepresentationScopeError, match="DENY_BEFORE_BYTES"):
        candidate.read_public_fixture(request, lambda: calls.append(True) or BUNDLE_BYTES)
    assert calls == []


@pytest.mark.parametrize("denial", CONTRACT["structural_denials"])
def test_registered_schema_and_immutable_state_denials(denial):
    row = copy.deepcopy(ROWS[0])
    if denial == "duplicate-field":
        with pytest.raises(candidate.RepresentationScopeError, match="duplicate"):
            json.loads(
                '{"op":"integer","op":"integer","value":1}',
                object_pairs_hook=candidate._closed_object,
            )
        return
    if denial == "changed-public-bytes":
        with pytest.raises(candidate.RepresentationScopeError, match="STOP_BINDING"):
            candidate.read_public_fixture(binding(row["id"]), lambda: BUNDLE_BYTES + b"\n")
        return
    if denial == "mutable-state":
        f = candidate.validate_public_fixture(row)
        with pytest.raises(FrozenInstanceError):
            f.fixture_id = "changed"
        object.__setattr__(f, "factor_roots", [[0], [1]])
        with pytest.raises(candidate.RepresentationScopeError, match="immutable"):
            candidate.enclose_representation(f)
        return
    if denial == "unknown-field":
        receipt = run(row)
        receipt["extra"] = 0
        assert not ORACLE.audit_case(row, receipt)["passed"]
        row["extra"] = 0
    elif denial == "missing-field":
        del row["G"]
    elif denial == "unknown-op":
        row["nodes"][0] = {"op": "sin", "args": []}
    elif denial in ("nonfinite-bits", "subnormal-bits"):
        word = "7ff0000000000000" if denial == "nonfinite-bits" else "0000000000000001"
        row["nodes"][0] = {"op": "bits", "value": word}
    elif denial == "bool-integer":
        row["nodes"][0]["value"] = True
    elif denial == "forward-reference":
        row["nodes"][0] = {"op": "add", "args": [0, 0]}
    elif denial == "ragged-matrix":
        row["A0"][0].append(1)
    elif denial == "asymmetric-root-ids":
        row = copy.deepcopy(ROWS[4])
        row["G"][0][1] = 0
    elif denial == "wrong-space":
        row["free_space"] = "other"
    elif denial == "changed-identity":
        row["nodes"][0]["value"] = 2
    elif denial == "over-node-limit":
        row["nodes"] = [{"op": "integer", "value": 1}] * 65
    elif denial == "out-of-dimension-limit":
        row["A0"] = [[0]] * 4
    else:
        raise AssertionError(denial)
    with pytest.raises(candidate.RepresentationScopeError):
        candidate.validate_public_fixture(row)


@pytest.mark.parametrize("probe", CONTRACT["arithmetic_probes"])
def test_fixed_grid_and_range_stops(probe):
    if probe.startswith("sqrt-"):
        q = {
            "sqrt-0": Fraction(0),
            "sqrt-1": Fraction(1),
            "sqrt-2": Fraction(2),
            "sqrt-third": Fraction(1, 3),
            "sqrt-2^-40": Fraction(1, 2**40),
            "sqrt-2^-1075": Fraction(1, 2**1075),
        }[probe]
        low, high = candidate._sqrt_grid(q)
        assert low**2 <= q <= high**2
        assert q < (low + Fraction(1, 2**80)) ** 2
        assert high - low in (0, Fraction(1, 2**80))
        assert (low == high) == (low**2 == q)
    else:
        with pytest.raises(candidate.RepresentationScopeError):
            if probe == "negative-sqrt":
                candidate._sqrt_grid(Fraction(-1))
            elif probe == "zero-denominator":
                candidate._interval("div", (Fraction(1), Fraction(1)), (Fraction(0), Fraction(0)))
            else:
                q = {
                    "outward-overflow": Fraction(2**1024),
                    "outward-subnormal": Fraction(1, 2**1023),
                    "outward-positive-underflow": Fraction(1, 2**1075),
                }[probe]
                candidate._up(q)


@pytest.mark.parametrize("tamper", CONTRACT["tampering"])
def test_independent_audit_rejects_all_registered_tampering(tamper):
    row = ROWS[4]
    changed = copy.deepcopy(run(row))
    flags = {
        "public-intended-flag": "public_intended_only",
        "diagnostic-flag": "diagnostic_only",
        "real-FEM-flag": "real_fem_certified",
        "PSD-coercivity-flag": "PSD_or_coercivity_certified",
    }
    squares = {
        "factor-error-square": "e",
        "structural-error-square": "d0",
        "representation-error-square": "d1",
        "complete-error-square": "complete",
    }
    if tamper in flags:
        key = flags[tamper]
        changed[key] = not changed[key]
    elif tamper in squares:
        changed["square_uppers"][squares[tamper]] = "0"
    elif tamper in ("delta", "e", "a", "d0", "d1", "complete", "cross", "square", "change"):
        changed["bounds"][tamper] = (0.0).hex()
    elif tamper == "fixture-id":
        changed["fixture_id"] = "exact-dyadic"
    elif tamper == "status":
        changed["status"] = "STOP_SIGN"
    elif tamper == "failure-node":
        changed["failure_node"] = 0
    elif tamper == "A_hat":
        changed["A_hat"][0][0] = (0.0).hex()
    elif tamper == "trace-op":
        changed["trace"][0]["op"] = "sub"
    elif tamper == "trace-operand":
        changed["trace"][4]["operand_hex"] = [(0.0).hex()]
    elif tamper == "trace-result":
        changed["trace"][0]["result_hex"] = math.nextafter(0, math.inf).hex()
    elif tamper == "trace-interval":
        changed["trace"][1]["intended_lower"] = "0"
    elif tamper == "trace-order":
        changed["trace"][0], changed["trace"][1] = changed["trace"][1], changed["trace"][0]
    elif tamper == "trace-extra":
        changed["trace"].append(changed["trace"][-1])
    elif tamper == "trace-missing":
        changed["trace"].pop()
    else:
        raise AssertionError(tamper)
    assert not ORACLE.audit_case(row, changed)["passed"]


def test_accepted_bits_remain_distinct_from_decimal_spelling():
    result = run(ROWS[1])
    accepted = Fraction(float.fromhex(result["trace"][0]["result_hex"]))
    assert accepted != Fraction(1, 10)
    intended = accepted / 3
    represented = Fraction(float.fromhex(result["A_hat"][0][0]))
    assert intended != represented
    assert Fraction(float.fromhex(result["bounds"]["e"])) >= abs(intended - represented)


def test_structural_identity_is_not_assumed_from_irrational_input():
    result = run(ROWS[2])
    assert Fraction(result["square_uppers"]["d0"]) > 0
    actual_error = abs(2 - Fraction(float.fromhex(result["A_hat"][0][0])) ** 2)
    assert Fraction(float.fromhex(result["bounds"]["delta"])) >= actual_error > 0


@pytest.mark.parametrize("row", ROWS[5:7], ids=lambda r: r["id"])
def test_both_nonzero_structural_signs_are_retained(row):
    result = run(row)
    assert Fraction(result["square_uppers"]["d0"]) >= Fraction(1, 64)
    assert Fraction(float.fromhex(result["bounds"]["d0"])) >= Fraction(1, 8)


def test_rounded_cancellation_cannot_erase_intended_factor_error():
    result = run(ROWS[7])
    assert result["A_hat"] == [[(0.0).hex()]]
    assert Fraction(result["trace"][4]["intended_lower"]) > 0
    assert Fraction(result["square_uppers"]["e"]) > 0
    assert float.fromhex(result["bounds"]["delta"]) > 0


def test_prescribed_stops_preserve_full_prefix_and_no_fabricated_enclosure():
    for row in ROWS[8:]:
        result = run(row)
        assert result["reason"] and result["failure_node"] is not None
        assert result["A_hat"] is result["square_uppers"] is result["bounds"] is None
        assert result["trace"]
    assert run(ROWS[10])["trace"][-1]["result_hex"] == "inf"
    assert run(ROWS[11])["trace"][-1]["result_hex"] == (0.0).hex()
