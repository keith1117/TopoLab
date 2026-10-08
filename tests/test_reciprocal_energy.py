"""Frozen eight public systems, independent exact oracle and before-byte denials."""

import ast
import copy
import hashlib
import importlib.util
import json
import sys
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from pathlib import Path

import pytest

from topolab.reciprocal_energy import (
    BUNDLE_SHA256,
    BUNDLE_VERSION,
    FIXTURE_SHA256,
    ROLE,
    STEPS,
    SoftwareScopeError,
    _closed_object,
    prepare_toy_anchor,
    read_public_fixture,
    validate_public_fixture,
)

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "tests/fixtures/b4_33_reciprocal_energy.json"
PUBLIC_BYTES = BUNDLE.read_bytes()
ROWS = json.loads(PUBLIC_BYTES)["fixtures"]
SPEC = importlib.util.spec_from_file_location(
    "b4_33_exact_oracle", ROOT / "scripts/b4_33_fixture_oracle.py"
)
assert SPEC is not None and SPEC.loader is not None
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def binding(identifier="single-soften"):
    return {
        "version": BUNDLE_VERSION,
        "role": ROLE,
        "fixture_id": identifier,
        "sha256": BUNDLE_SHA256,
    }


def prepared(row):
    ref = oracle.reference(row)
    fixture = read_public_fixture(binding(row["id"]), lambda: PUBLIC_BYTES)
    return prepare_toy_anchor(fixture, ref["u_star"], ref["stored_compliance"]), ref


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["id"])
def test_exact_physics_and_float_anchor_current_and_both_fd_steps(row):
    anchor, ref = prepared(row)
    assert ref["upper"](ref["anchor"]) == ref["anchor_compliance"]
    assert ref["upper_gradient"](ref["anchor"]) == ref["anchor_adjoint"]
    assert ref["upper"](ref["current"]) >= ref["current_compliance"]
    assert ref["upper"](ref["current"]) - ref["current_compliance"] == sum(ref["gap_squares"])
    assert all(x >= 0 for x in ref["gap_squares"])
    assert anchor.coefficients == ref["coefficients"]
    for point in (ref["anchor"], ref["current"]):
        for normalized in (False, True):
            scale = ref["stored_compliance"] if normalized else 1
            value, gradient = anchor.value_gradient(tuple(map(float, point)), normalized=normalized)
            assert value == pytest.approx(float(ref["upper"](point) / scale), rel=1e-9, abs=1e-10)
            assert gradient == pytest.approx(
                tuple(float(x / scale) for x in ref["upper_gradient"](point)), rel=1e-9, abs=1e-10
            )
    assert anchor.value_gradient(tuple(map(float, ref["anchor"])))[0] == pytest.approx(
        10 / 11, rel=1e-9, abs=1e-10
    )
    current = tuple(map(float, ref["current"]))
    _, gradient = anchor.value_gradient(current)
    for i in range(len(current)):
        for step in STEPS:
            plus, minus = list(current), list(current)
            plus[i] += step
            minus[i] -= step
            high, low = anchor.value_gradient(plus)[0], anchor.value_gradient(minus)[0]
            fd = (high - low) / (2 * step)
            assert abs(fd - gradient[i]) / max(abs(fd), abs(gradient[i]), 1e-8) <= 1e-4
            # Compare each actual binary64 point to independent exact arithmetic too.
            for point in (plus, minus):
                exact = tuple(Fraction.from_float(x) for x in point)
                value, derivatives = anchor.value_gradient(point)
                assert value == pytest.approx(
                    float(ref["upper"](exact) / ref["stored_compliance"]), rel=1e-9, abs=1e-10
                )
                assert derivatives == pytest.approx(
                    tuple(
                        float(x / ref["stored_compliance"]) for x in ref["upper_gradient"](exact)
                    ),
                    rel=1e-9,
                    abs=1e-10,
                )


def test_common_modulus_scaling_and_zero_energy_are_exact():
    common = oracle.reference(ROWS[5])
    scale = common["modulus"](common["anchor"][0]) / common["modulus"](common["current"][0])
    assert (
        common["upper"](common["current"])
        == common["current_compliance"]
        == scale * common["anchor_compliance"]
    )
    assert sum(common["gap_squares"]) == 0
    zero, ref = prepared(ROWS[6])
    assert zero.coefficients[1] == ref["coefficients"][1] == 0
    assert zero.value_gradient(tuple(map(float, ref["current"])))[1][1] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("role", "label"),
        ("role", "model"),
        ("role", "final"),
        ("role", "expanded-train"),
        ("version", "UNKNOWN"),
        ("fixture_id", "UNKNOWN"),
        ("sha256", "0" * 64),
        ("unknown", "field"),
    ],
)
def test_unbound_roles_and_fields_deny_before_bytes(field, value):
    request = binding()
    request[field] = value
    calls = []

    def reader():
        calls.append(True)
        return PUBLIC_BYTES

    with pytest.raises(SoftwareScopeError):
        read_public_fixture(request, reader)
    assert calls == []


@pytest.mark.parametrize("bad", [PUBLIC_BYTES + b" ", b'{"role":"label"}', "not-bytes"])
def test_changed_authorized_public_bytes_reject_after_one_read(bad):
    calls = []

    def reader():
        calls.append(True)
        return bad

    with pytest.raises(SoftwareScopeError):
        read_public_fixture(binding(), reader)
    assert calls == [True]


def mutated(name):
    raw = copy.deepcopy(ROWS[4])
    if name == "unknown-field":
        raw["unknown"] = "UNKNOWN"
    elif name == "bad-support":
        raw["dirichlet"] = "nonzero-prescribed-displacement"
    elif name == "nonfinite":
        raw["load"][0] = "nan"
    elif name == "ragged-matrix":
        raw["unit_matrices"][0][0].pop()
    elif name == "nonsymmetric":
        raw["unit_matrices"][0][0][1] = "2"
    elif name == "non-PSD":
        raw["unit_matrices"][0] = [["1", "2"], ["2", "1"]]
    elif name == "singular-free":
        raw["unit_matrices"] = [[["0", "0"], ["0", "0"]]] * 2
    elif name == "zero-load":
        raw["load"] = ["0", "0"]
    elif name == "invalid-density":
        raw["current_density"][0] = "0"
    elif name == "too-many-elements":
        raw["unit_matrices"] *= 2
    elif name == "too-many-dofs":
        raw["load"].append("1")
    elif name == "changed-fixture-identity":
        raw["current_density"][0] = "1/2"
    else:
        raise AssertionError(name)
    return raw


@pytest.mark.parametrize(
    "name",
    [
        "unknown-field",
        "bad-support",
        "nonfinite",
        "ragged-matrix",
        "nonsymmetric",
        "non-PSD",
        "singular-free",
        "zero-load",
        "invalid-density",
        "too-many-elements",
        "too-many-dofs",
        "changed-fixture-identity",
    ],
)
def test_structural_or_identity_tampering_rejects(name):
    with pytest.raises(SoftwareScopeError):
        validate_public_fixture(mutated(name))


@pytest.mark.parametrize(
    "change", [{"minimum_modulus": Fraction(0)}, {"normalizer_scale": Fraction(1)}]
)
def test_material_and_normalizer_tampering_rejects(change):
    anchor, ref = prepared(ROWS[0])
    with pytest.raises(SoftwareScopeError):
        prepare_toy_anchor(
            replace(anchor.fixture, **change), ref["u_star"], ref["stored_compliance"]
        )


@pytest.mark.parametrize(
    "kind",
    [
        "wrong-exact-equilibrium",
        "small-nonzero-residual",
        "floating-certificate",
        "wrong-dimension",
    ],
)
def test_exact_certificate_denials(kind):
    anchor, ref = prepared(ROWS[0])
    u = ref["u_star"]
    if kind == "wrong-exact-equilibrium":
        u = (u[0] + 1,)
    elif kind == "small-nonzero-residual":
        u = (u[0] + Fraction(1, 10**12),)
    elif kind == "floating-certificate":
        u = tuple(map(float, u))
    else:
        u = ()
    with pytest.raises(SoftwareScopeError):
        prepare_toy_anchor(anchor.fixture, u, ref["stored_compliance"])


@pytest.mark.parametrize("bad", [(float("nan"),), (), (0,), (1.01,), (0.25 + 1e-5,), (0.4,)])
def test_outside_point_panel_and_invalid_density_reject(bad):
    anchor, _ = prepared(ROWS[0])
    with pytest.raises(SoftwareScopeError):
        anchor.value_gradient(bad)


def test_prepared_evidence_is_immutable_and_replacement_recertifies():
    anchor, ref = prepared(ROWS[0])
    with pytest.raises(TypeError):
        FIXTURE_SHA256["unregistered"] = "0" * 64
    with pytest.raises(FrozenInstanceError):
        anchor.stored_compliance = Fraction(1)
    with pytest.raises(ValueError):
        replace(anchor, coefficients=(Fraction(999),))
    with pytest.raises(SoftwareScopeError):
        replace(anchor, stored_compliance=ref["anchor_compliance"])
    with pytest.raises(SoftwareScopeError):
        replace(anchor, exact_displacement=(ref["u_star"][0] + Fraction(1, 10**12),))
    with pytest.raises(SoftwareScopeError):
        replace(anchor, exact_displacement=list(ref["u_star"]))
    with pytest.raises(SoftwareScopeError):
        replace(anchor, fixture=replace(anchor.fixture, current_density=list(ref["current"])))


def test_closed_json_does_not_accept_duplicate_fields():
    with pytest.raises(SoftwareScopeError):
        json.loads('{"unknown":1,"unknown":2}', object_pairs_hook=_closed_object)


def test_fixture_identity_limits_and_import_access_boundary():
    contract = json.loads(
        (ROOT / "docs/planning/b4_33_reciprocal_energy_evidence_contract.json").read_bytes()
    )
    assert (
        hashlib.sha256(PUBLIC_BYTES).hexdigest()
        == contract["fixture_bundle_sha256"]
        == BUNDLE_SHA256
    )
    assert contract["fixture_fingerprints_sha256"] == FIXTURE_SHA256
    assert len(ROWS) == contract["public_fixture_count"] == 8
    assert sum(len(x["anchor_density"]) for x in ROWS) == contract["physical_coordinates"] == 15
    assert contract["fd_intervals"] == 30 and contract["nominal_float_points"] == 76
    for file in ["src/topolab/reciprocal_energy.py", "scripts/b4_33_fixture_oracle.py"]:
        tree = ast.parse((ROOT / file).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(x.name.split(".")[0] in sys.stdlib_module_names for x in node.names)
            if isinstance(node, ast.ImportFrom):
                assert node.module.split(".")[0] in sys.stdlib_module_names
            if isinstance(node, ast.Call):
                assert not (
                    isinstance(node.func, ast.Name)
                    and node.func.id in {"open", "eval", "exec", "__import__"}
                )
                assert not (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"read_bytes", "write_bytes", "read_text", "write_text"}
                )
