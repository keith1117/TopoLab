"""Frozen public B4.43 panel; independent IEEE/error proof and finite denials."""

import copy
import importlib.util
import json
import math
from dataclasses import FrozenInstanceError
from fractions import Fraction
from pathlib import Path

import pytest

from topolab import assembled_residual as candidate

ROOT = Path(__file__).resolve().parents[1]
RAW = (ROOT / "tests/fixtures/b4_43_assembled_residual.json").read_bytes()
ROWS = json.loads(RAW)["fixtures"]
CONTRACT = json.loads(
    (ROOT / "docs/planning/b4_43_public_assembled_residual_enclosure_contract.json").read_bytes()
)
SPEC = importlib.util.spec_from_file_location(
    "b4_43_oracle", ROOT / "scripts/b4_43_residual_oracle.py"
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
        "free_space": "authored-assembly-space:" + identifier,
    }


def run(row):
    fixture = candidate.read_public_fixture(binding(row["id"]), lambda: RAW)
    return candidate.enclose_assembled_residual(fixture)


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["id"])
def test_all_finite_cases_with_separate_exact_audit(row):
    result = run(row)
    assert result["status"] == CONTRACT["expected_outcomes"][row["id"]]
    audit = ORACLE.audit_case(row, result)
    assert audit["passed"], audit
    assert all(audit["checks"].values())


@pytest.mark.parametrize("denial", CONTRACT["binding_denials"])
def test_role_source_identity_denials_before_callback(denial):
    request = binding(ROWS[0]["id"])
    if denial == "unknown-field":
        request["unknown"] = "unknown"
    elif denial == "missing-field":
        del request["role"]
    else:
        field = {
            "label-role": "role",
            "model-role": "role",
            "final-role": "role",
            "expanded-train-role": "role",
            "wrong-version": "version",
            "wrong-id": "fixture_id",
            "wrong-hash": "sha256",
            "wrong-source": "source_main",
            "wrong-space": "free_space",
        }[denial]
        request[field] = denial
    calls = []
    with pytest.raises(candidate.RepresentationScopeError, match="DENY_BEFORE_BYTES"):
        candidate.read_public_fixture(request, lambda: calls.append(True) or RAW)
    assert calls == []


@pytest.mark.parametrize("denial", CONTRACT["structural_denials"])
def test_schema_and_immutable_state_denials(denial):
    row = copy.deepcopy(ROWS[0])
    if denial == "duplicate-field":
        with pytest.raises(candidate.RepresentationScopeError, match="duplicate"):
            json.loads('{"x":0,"x":1}', object_pairs_hook=candidate._closed_object)
        return
    if denial == "changed-public-bytes":
        with pytest.raises(candidate.RepresentationScopeError, match="STOP_BINDING"):
            candidate.read_public_fixture(binding(row["id"]), lambda: RAW + b"\n")
        return
    if denial == "mutable-state":
        fixture = candidate.validate_public_fixture(row)
        with pytest.raises(FrozenInstanceError):
            fixture.fixture_id = "changed"
        object.__setattr__(fixture, "K_terms", [[[0]]])
        with pytest.raises(candidate.RepresentationScopeError, match="immutable"):
            candidate.enclose_assembled_residual(fixture)
        return
    if denial == "unknown-field":
        changed = run(row)
        changed["extra"] = 0
        assert not ORACLE.audit_case(row, changed)["passed"]
        row["extra"] = 0
    elif denial == "missing-field":
        del row["G_terms"]
    elif denial == "unknown-op":
        row["nodes"][0] = {"op": "sin", "args": []}
    elif denial in ("nonfinite-bits", "subnormal-bits"):
        row["nodes"][0] = {
            "op": "bits",
            "value": "7ff0000000000000" if denial == "nonfinite-bits" else "0000000000000001",
        }
    elif denial == "bool-integer":
        row["nodes"][0]["value"] = True
    elif denial == "nonfinite-json":
        row["nodes"][0]["value"] = json.loads("NaN")
    elif denial == "forward-reference":
        row["nodes"][0] = {"op": "add", "args": [0, 0]}
    elif denial == "ragged-matrix":
        row["G_terms"][0][0].append(0)
    elif denial == "wrong-space":
        row["free_space"] = "other"
    elif denial == "changed-identity":
        row["nodes"][0]["value"] = 1
    elif denial == "over-node-limit":
        row["nodes"] = [{"op": "integer", "value": 1}] * 65
    elif denial == "over-dimension-limit":
        row["u_bits"] *= 3
    elif denial == "over-contribution-limit":
        row["K_terms"] *= 4
    else:
        raise AssertionError(denial)
    with pytest.raises(candidate.RepresentationScopeError):
        candidate.validate_public_fixture(row)


@pytest.mark.parametrize("probe", CONTRACT["arithmetic_probes"])
def test_fixed_norm_route_and_range_stops(probe):
    if probe.startswith("sqrt-"):
        q = {"sqrt-zero": Fraction(0), "sqrt-two": Fraction(2), "sqrt-tiny": Fraction(1, 2**1075)}[
            probe
        ]
        lo, hi = candidate._sqrt_grid(q)
        assert lo**2 <= q <= hi**2
        assert hi - lo in (0, Fraction(1, 2**80))
        assert q < (lo + Fraction(1, 2**80)) ** 2
    else:
        with pytest.raises(candidate.RepresentationScopeError):
            if probe == "negative-sqrt":
                candidate._sqrt_grid(Fraction(-1))
            elif probe == "zero-denominator":
                candidate._interval("div", (Fraction(1), Fraction(1)), (Fraction(0), Fraction(0)))
            else:
                candidate._up(
                    {
                        "outward-overflow": Fraction(2**1024),
                        "outward-subnormal": Fraction(1, 2**1023),
                        "outward-positive-underflow": Fraction(1, 2**1075),
                    }[probe]
                )


@pytest.mark.parametrize("tamper", CONTRACT["tampering"])
def test_oracle_rejects_every_registered_tamper(tamper):
    row = ROWS[3]
    changed = copy.deepcopy(run(row))
    flags = {
        "diagnostic-flag": "diagnostic_only",
        "real-FEM-flag": "real_fem_certified",
        "PSD-coercivity-flag": "PSD_or_coercivity_certified",
        "loss-gradient-flag": "loss_gradient_changed",
        "public-intended-flag": "public_intended_only",
    }
    if tamper in flags:
        key = flags[tamper]
        changed[key] = not changed[key]
    elif tamper.endswith("-square"):
        key = tamper[:-7].replace("-", "_")
        key = {
            "beta_G": "beta_G",
            "beta_K": "beta_K",
            "symmetry_G": "symmetry_G",
            "symmetry_K": "symmetry_K",
        }.get(key, key)
        changed["square_uppers"][key] = str(Fraction(changed["square_uppers"][key]) + 1)
    elif tamper in (
        "beta-G",
        "beta-K",
        "beta-f",
        "beta-eval",
        "q-hat",
        "u-plus",
        "intended-residual",
        "q-eval",
        "operator-solution",
        "with-operator",
        "r-plus",
    ):
        key = tamper.replace("-", "_")
        changed["bounds"][key] = (float.fromhex(changed["bounds"][key]) + 1).hex()
    elif tamper in ("G-array", "K-array"):
        changed["arrays"][tamper[0]][0][0] = (7.0).hex()
    elif tamper in ("f-array", "r-hat", "u-bits"):
        key = {"f-array": "f", "r-hat": "r_hat", "u-bits": "u"}[tamper]
        changed["arrays"][key][0] = (7.0).hex()
    elif tamper == "r-array":
        changed["arrays"]["r_arrays"][0] = "7"
    elif tamper == "fixture-id":
        changed["fixture_id"] = ROWS[0]["id"]
    elif tamper == "status":
        changed["status"] = "STOP_ARITHMETIC"
    elif tamper == "failure-stage":
        changed["failure_stage"] = "changed"
    elif tamper == "reason":
        changed["reason"] = "changed"
    elif tamper == "trace-op":
        changed["trace"][0]["op"] = "sub"
    elif tamper == "trace-operand":
        changed["trace"][0]["operand_hex"] = [(1.0).hex()]
    elif tamper == "trace-result":
        changed["trace"][0]["result_hex"] = math.nextafter(0, math.inf).hex()
    elif tamper == "trace-interval":
        changed["trace"][0]["intended_lower"] = "1"
    elif tamper == "trace-order":
        changed["trace"][0], changed["trace"][1] = changed["trace"][1], changed["trace"][0]
    elif tamper == "trace-extra":
        changed["trace"].append(changed["trace"][-1])
    elif tamper == "trace-missing":
        changed["trace"].pop()
    else:
        raise AssertionError(tamper)
    assert not ORACLE.audit_case(row, changed)["passed"]


def test_distinct_unit_anchor_and_signed_zero_bits():
    result = run(ROWS[0])
    assert result["arrays"]["G"] != result["arrays"]["K"]
    assert result["trace"][4]["result_hex"] == (-0.0).hex()
    assert result["bounds"]["r_plus"] == (0.0).hex()


def test_zero_rounded_residual_keeps_intended_assembly_error():
    result = run(ROWS[2])
    assert result["arrays"]["r_hat"] == [(0.0).hex()]
    assert result["square_uppers"]["beta_K"] == "1"
    assert float.fromhex(result["bounds"]["r_plus"]) >= 1


def test_both_actual_triangles_and_symmetry_defect_stay():
    result = run(ROWS[3])
    assert result["arrays"]["K"][0][1] != result["arrays"]["K"][1][0]
    assert result["square_uppers"]["symmetry_K"] == "2"
    assert result["square_uppers"]["symmetry_G"] == "2"
    assert not result["PSD_or_coercivity_certified"]


def test_zero_r_hat_retains_actual_evaluation_error():
    result = run(ROWS[5])
    assert result["arrays"]["r_hat"] == [(0.0).hex()] * 2
    assert result["arrays"]["r_arrays"] == ["1", "1"]
    assert result["square_uppers"]["beta_eval"] == "2"
    assert float.fromhex(result["bounds"]["beta_eval"]) ** 2 >= 2


def test_irrational_intended_and_accepted_bits_force_errors():
    result = run(ROWS[4])
    assert Fraction(float.fromhex(result["trace"][3]["result_hex"])) != Fraction(1, 10)
    assert Fraction(result["square_uppers"]["beta_f"]) > 0
    assert float.fromhex(result["bounds"]["beta_f"]) > 0
    assert result["diagnostic_only"] and not result["loss_gradient_changed"]


def test_four_stops_keep_raw_prefix_without_completed_values():
    for row in ROWS[6:]:
        result = run(row)
        assert result["status"] == "STOP_ARITHMETIC"
        assert result["trace"] and result["reason"] and result["failure_stage"]
        assert result["arrays"] is result["square_uppers"] is result["bounds"] is None
        assert result["trace"][-1]["result_hex"] in ("inf", (0.0).hex())
