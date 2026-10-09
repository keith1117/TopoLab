"""Frozen public certificates, independent exact checks and finite denial families."""

import ast
import copy
import importlib.util
import json
import math
from dataclasses import FrozenInstanceError, asdict, replace
from fractions import Fraction
from pathlib import Path

import pytest

from topolab.admissibility_certificate import (
    BUNDLE_SHA256,
    BUNDLE_VERSION,
    FIXTURE_SHA256,
    ROLE,
    SOURCE_MAIN,
    SQRT_BITS,
    CertificateScopeError,
    _bound,
    _closed_object,
    _outward,
    _sqrt_enclosure,
    certify_public_point,
    read_public_fixture,
    validate_public_fixture,
)

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "tests/fixtures/b4_35_admissibility_certificate.json"
PUBLIC_BYTES = BUNDLE.read_bytes()
ROWS = json.loads(PUBLIC_BYTES)["fixtures"]
SPEC = importlib.util.spec_from_file_location(
    "b4_35_independent_oracle", ROOT / "scripts/b4_35_certificate_oracle.py"
)
assert SPEC is not None and SPEC.loader is not None
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def binding(identifier="single-exact"):
    return {
        "version": BUNDLE_VERSION,
        "role": ROLE,
        "fixture_id": identifier,
        "sha256": BUNDLE_SHA256,
        "source_main": SOURCE_MAIN,
    }


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["id"])
def test_every_fixed_point_against_candidate_free_exact_operator_and_all_enclosures(row):
    fixture = read_public_fixture(binding(row["id"]), lambda: PUBLIC_BYTES)
    for name, point in (("anchor", fixture.anchor_density), ("current", fixture.current_density)):
        certificate = certify_public_point(fixture, point)
        checks, ref = oracle.audit_point(row, name, asdict(certificate))
        assert all(checks.values()), checks
        assert Fraction.from_float(certificate.B_plus) >= ref["compliance"]
        assert ref["stored"] == Fraction(11, 10) * ref["anchor_compliance"]
        assert certificate.residual_is_exact_zero == (
            row["id"] in ("single-exact", "zero-energy-element")
        )
    if row["id"] == "zero-energy-element":
        assert ref["energy"][1] == 0


def test_tiny_nonzero_residual_is_not_a_tolerant_unmodified_upper_certificate():
    row = ROWS[1]
    fixture = validate_public_fixture(row)
    certificate = certify_public_point(fixture, fixture.current_density)
    ref = oracle.reference(row, "current")
    assert ref["residual_squared"] == Fraction(1, 10**24)
    assert ref["upper"] < ref["compliance"]
    assert certificate.r_plus > 0
    assert not certificate.unmodified_U_certified
    assert not certificate.residual_is_exact_zero


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
    ],
)
def test_nine_wrong_bindings_reject_before_callback_bytes(change):
    calls = []
    with pytest.raises(CertificateScopeError, match="DENY_BEFORE_BYTES"):
        read_public_fixture(binding() | change, lambda: calls.append(1) or PUBLIC_BYTES)
    assert calls == []


@pytest.mark.parametrize(
    "family",
    [
        "unknown-field",
        "duplicate-field",
        "nonsymmetric",
        "non-PSD",
        "ragged-matrix",
        "wrong-displacement-dimension",
        "zero-load",
        "nonzero-Dirichlet",
        "nonpositive-lower_G",
        "overoptimistic-lower_G",
        "nonpositive-normalizer",
        "changed-fixture-identity",
    ],
)
def test_twelve_structural_denials(family):
    row = copy.deepcopy(ROWS[3])
    if family == "duplicate-field":
        with pytest.raises(CertificateScopeError, match="duplicate"):
            json.loads('{"id":"x","id":"y"}', object_pairs_hook=_closed_object)
        return
    if family == "unknown-field":
        row["unknown"] = "UNKNOWN"
    elif family == "nonsymmetric":
        row["unit_matrices"][0][0][1] = "0"
    elif family == "non-PSD":
        row["unit_matrices"][0][0][0] = "-1"
    elif family == "ragged-matrix":
        row["unit_matrices"][0][0] = []
    elif family == "wrong-displacement-dimension":
        row["approximate_displacement"] = ["1"]
    elif family == "zero-load":
        row["load"] = ["0", "0"]
    elif family == "nonzero-Dirichlet":
        row["dirichlet"] = "nonzero"
    elif family == "nonpositive-lower_G":
        row["lower_G"] = "0"
    elif family == "overoptimistic-lower_G":
        row["lower_G"] = "1"
    elif family == "nonpositive-normalizer":
        row["stored_normalizer"] = "0"
    elif family == "changed-fixture-identity":
        row["id"] = "unknown"
    with pytest.raises(CertificateScopeError):
        validate_public_fixture(row)


@pytest.mark.parametrize(
    "value",
    [
        Fraction(0),
        Fraction(1),
        Fraction(2),
        Fraction(1, 10),
        Fraction(1, 3),
        Fraction(1, 2**80),
        Fraction(1, 2**1074),
        Fraction(1, 2**1075),
    ],
)
def test_exact_outward_binary64_and_fixed_sqrt_endpoint_inequalities(value):
    low, high = _sqrt_enclosure(value)
    assert low >= 0 and low**2 <= value <= high**2
    assert high - low <= Fraction(1, 2**SQRT_BITS)
    assert Fraction.from_float(_outward(value, upper=False)) <= value
    assert Fraction.from_float(_outward(value, upper=True)) >= value
    assert Fraction.from_float(_outward(high, upper=True)) ** 2 >= value


@pytest.mark.parametrize(
    "family", ["overflow-2**1024", "negative-sqrt", "zero-sqrt-denominator-at-fixed-grid"]
)
def test_three_frozen_arithmetic_stops_never_expand_precision(family):
    with pytest.raises(CertificateScopeError):
        if family == "overflow-2**1024":
            _outward(Fraction(2**1024), upper=True)
        elif family == "negative-sqrt":
            _sqrt_enclosure(Fraction(-1))
        else:
            _bound(Fraction(1), Fraction(1), Fraction(1, 2**164), Fraction(1))
    assert SQRT_BITS == 80


@pytest.mark.parametrize(
    "point", ["unknown-point-name", (Fraction(3, 5),), (math.nan,), (Fraction(1), Fraction(1))]
)
def test_four_outside_point_denials(point):
    fixture = validate_public_fixture(ROWS[0])
    with pytest.raises(CertificateScopeError):
        certify_public_point(fixture, point)


def test_prepared_identity_rechecks_mutations_and_bound_is_immutable():
    fixture = validate_public_fixture(ROWS[0])
    bound = certify_public_point(fixture, fixture.anchor_density)
    with pytest.raises(FrozenInstanceError):
        bound.B_plus = 0
    with pytest.raises(FrozenInstanceError):
        fixture.stored_normalizer = Fraction(2)
    changed = replace(fixture, stored_normalizer=Fraction(2))
    with pytest.raises(CertificateScopeError, match="changed"):
        certify_public_point(changed, changed.anchor_density)
    object.__setattr__(fixture, "displacement", (Fraction(2),))
    with pytest.raises(CertificateScopeError, match="changed"):
        certify_public_point(fixture, fixture.anchor_density)


def test_changed_public_bytes_never_authorize_a_fixture():
    with pytest.raises(CertificateScopeError, match="digest"):
        read_public_fixture(binding(), lambda: PUBLIC_BYTES + b" ")
    assert set(FIXTURE_SHA256) == {row["id"] for row in ROWS}


@pytest.mark.parametrize(
    "field",
    [
        "r_plus",
        "m_minus",
        "sqrt_U_up",
        "sqrt_m_down",
        "residual_division_up",
        "B_plus",
        "normalized_B_plus",
        "C_s_minus",
        "unmodified_U_certified",
    ],
)
def test_independent_oracle_detects_each_broken_enclosure_or_zero_claim(field):
    row = ROWS[1]
    fixture = validate_public_fixture(row)
    result = asdict(certify_public_point(fixture, fixture.current_density))
    result[field] = (
        True
        if field == "unmodified_U_certified"
        else (result[field] * 2 if field in ("m_minus", "sqrt_m_down", "C_s_minus") else 0.0)
    )
    checks, _ = oracle.audit_point(row, "current", result)
    assert not all(checks.values()), (field, checks)


@pytest.mark.parametrize(
    "path", ["src/topolab/admissibility_certificate.py", "scripts/b4_35_certificate_oracle.py"]
)
def test_candidate_and_independent_oracle_import_only_stdlib_and_have_no_io(path):
    tree = ast.parse((ROOT / path).read_text())
    import sys

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(name.name.split(".")[0] in sys.stdlib_module_names for name in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None and node.module.split(".")[0] in sys.stdlib_module_names
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
