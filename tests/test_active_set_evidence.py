"""Independent analytic, exhaustive and tampering tests with no production inputs."""

import importlib.util
import math
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from topolab.active_set_evidence import (
    IncompleteEvidence,
    Piece,
    PointWitness,
    UndefinedDerivative,
    certify_interval,
    certify_pointwise,
    check_interval,
    check_pointwise,
)

spec = importlib.util.spec_from_file_location(
    "independent_fixture_oracle", Path(__file__).parents[1] / "scripts/b4_27_fixture_oracle.py"
)
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


def point():
    z, w, g = (0.2, 0.4, 0.7), (0.2, 0.3, 0.5), (-1.0, 2.0, -3.0)
    return z, w, g, certify_pointwise(z, w, g, 0.5, 0.1, -0.01)


def witness(reference):
    return PointWitness(
        reference.design,
        reference.design,
        reference.gradient,
        reference.offset,
        reference.kink_margin,
        0.0,
        0.0,
        -0.5,
        2.0,
        -0.5,
        reference.gradient,
    )


def predicates(reference, observed, weights):
    return check_pointwise(
        reference,
        observed,
        weights=weights,
        independent_physical=reference.design,
        independent_value=-0.5,
        independent_compliance=2.0,
        volume=0.5,
    )


def test_full_cotangent_matches_analytic_volume_constraint_and_keeps_signed_value():
    _, w, _, reference = point()
    assert reference.gradient == pytest.approx((-0.6, 2.6, -2.0), abs=1e-15)
    assert reference.offset == pytest.approx(-0.01, abs=1e-15)
    # Physical density is deliberately independent of the weighted fixture filter.
    physical = (0.5, 0.5, 0.5)
    observed = replace(witness(reference), physical=physical)
    assert all(
        check_pointwise(
            reference,
            observed,
            weights=w,
            independent_physical=physical,
            independent_value=-0.5,
            independent_compliance=2.0,
            volume=0.5,
        )
    )


def test_clipped_coordinates_are_zero_but_free_signed_cotangent_is_not_clipped():
    reference = certify_pointwise(
        (0.0001, 0.4, 0.6, 0.9999), (0.1, 0.2, 0.3, 0.4), (-2.0, 3.0, -4.0, 1.0), 0.675, 0.1, 0.01
    )
    assert reference.partition == (-1, 0, 0, 1)
    assert reference.gradient == pytest.approx((0, 3.4, -3.4, 0), abs=1e-15)
    assert math.fsum(reference.gradient) == 0


def test_pointwise_volume_context_cannot_be_substituted_after_certification():
    _, w, _, reference = point()
    with pytest.raises(IncompleteEvidence, match="context"):
        predicates(reference, witness(reference), tuple(reversed(w)))


def test_pointwise_value_retains_original_v3_bound_separately_from_interval_identity():
    _, w, _, reference = point()
    observed = replace(
        witness(reference), physical=(0.5, 0.5, 0.5), value=-0.5 + 4e-10, torch_value=-0.5 + 4e-10
    )
    assert all(
        check_pointwise(
            reference,
            observed,
            weights=w,
            independent_physical=(0.5,) * 3,
            independent_value=-0.5,
            independent_compliance=2.0,
            volume=0.5,
        )
    )
    assert not all(
        check_pointwise(
            reference,
            replace(observed, value=-0.5 + 1e-8),
            weights=w,
            independent_physical=(0.5,) * 3,
            independent_value=-0.5,
            independent_compliance=2.0,
            volume=0.5,
        )
    )



def test_pointwise_independent_physical_pair_requires_complete_grid_dimension():
    _, w, _, reference = point()
    observed = replace(witness(reference), physical=(0.5, 0.5))
    assert not all(
        check_pointwise(
            reference,
            observed,
            weights=w,
            independent_physical=(0.5, 0.5),
            independent_value=-0.5,
            independent_compliance=2.0,
            volume=0.5,
        )
    )


def test_existing_v3_synthetic_projection_and_pullback_match_independent_certificate():
    import numpy as np
    from scipy import sparse

    from topolab.offline_compliance import pullback
    from topolab.simp import DensityFilter
    from topolab.stable_projection import project_stable

    filt = DensityFilter(sparse.csr_matrix(np.eye(3)), np.ones(3))
    raw, g = np.array([0.2, 0.4, 0.7]), np.array([-1.0, 2.0, -3.0])
    state = project_stable(filt, raw, 0.5, 0.1)
    gradient = pullback(state, g)
    reference = certify_pointwise(raw.tolist(), [1 / 3] * 3, g.tolist(), 0.5, 0.1, state.offset)
    observed = PointWitness(
        tuple(state.design),
        tuple(state.physical),
        tuple(gradient),
        state.offset,
        min(min(abs(x - 0.1), abs(x - 1)) for x in raw + state.offset),
        float(state.weights @ state.design) - 0.5,
        float(state.physical.mean()) - 0.5,
        -0.5,
        2.0,
        -0.5,
        tuple(gradient),
    )
    assert all(
        check_pointwise(
            reference,
            observed,
            weights=[1 / 3] * 3,
            independent_physical=reference.design,
            independent_value=-0.5,
            independent_compliance=2.0,
            volume=0.5,
        )
    )


@pytest.mark.parametrize(
    "damage",
    [
        "gradient",
        "offset",
        "physical",
        "kink",
        "residual",
        "compliance",
        "torch_value",
        "torch_gradient",
        "nonfinite",
    ],
)
def test_pointwise_tampering_is_retained_as_a_failed_predicate(damage):
    _, w, _, reference = point()
    # Independent physical state has the prescribed volume, unrelated to simple mean(design).
    observed = replace(witness(reference), physical=(0.5, 0.5, 0.5))
    changes = {
        "gradient": {"gradient": (0.6, 2.6, -2.0)},
        "offset": {"offset": reference.offset + 1e-8},
        "physical": {"physical": (0.6, 0.5, 0.5)},
        "kink": {"kink_margin": 1e-11},
        "residual": {"weighted_residual": 1e-8},
        "compliance": {"compliance": 2.01},
        "torch_value": {"torch_value": -0.5000000000000001},
        "torch_gradient": {"torch_gradient": (0.0, 0.0, 0.0)},
        "nonfinite": {"value": math.nan},
    }
    checks = check_pointwise(
        reference,
        replace(observed, **changes[damage]),
        weights=w,
        independent_physical=(0.5, 0.5, 0.5),
        independent_value=-0.5,
        independent_compliance=2.0,
        volume=0.5,
    )
    assert len(checks) == 15 and not all(checks)


@pytest.mark.parametrize(
    "z,w,g,v,m,s",
    [
        ((0.1, 0.9), (0.5, 0.5), (1.0, -1.0), 0.5, 0.1, 0.0),
        ((0.0, 1.0), (0.5, 0.5), (1.0, -1.0), 0.55, 0.1, 0.05),
        ((0.2, math.nan), (0.5, 0.5), (1.0, -1.0), 0.5, 0.1, 0.0),
        ((0.2, 0.6), (0.0, 1.0), (1.0, -1.0), 0.5, 0.1, 0.0),
    ],
)
def test_undefined_or_invalid_reference_never_substitutes_a_derivative(z, w, g, v, m, s):
    with pytest.raises(IncompleteEvidence):
        certify_pointwise(z, w, g, v, m, s)


def interval(z, d, w, g, v, m, h):
    rows = oracle.enumerate_pieces(z, d, w, v, m, h)
    pieces = [Piece(a, b, p) for a, b, p, _, _ in rows]
    reference = certify_interval(z, d, w, g, v, m, h, pieces)
    independent_delta = sum(
        Fraction(gi) * (b - a) for gi, a, b in zip(g, rows[0][3], rows[-1][4], strict=True)
    )
    assert reference.signed_increment == independent_delta
    return pieces, reference


@pytest.mark.parametrize("h", [1e-4, 2e-4])
def test_fixed_set_requires_original_fd_and_every_full_gradient_coordinate(h):
    z, w, g, point_reference = point()
    d = (1.0, -0.5, 0.2)
    _, reference = interval(z, d, w, g, 0.5, 0.1, h)
    assert len(reference.pieces) == 1 and not reference.transitions
    derivative = math.fsum(a * b for a, b in zip(point_reference.gradient, d, strict=True))
    plus = float(reference.signed_increment)
    checks = check_interval(
        reference, d, h, 0.0, plus, derivative, legacy_mask_passed=True, legacy_fd_passed=True
    )
    assert checks.passed and not checks.crossing
    assert not check_interval(
        reference,
        d,
        h,
        0.0,
        plus,
        derivative + 0.1,
        legacy_mask_passed=True,
        legacy_fd_passed=False,
    ).passed


@pytest.mark.parametrize("h", [1e-4, 2e-4])
def test_crossing_integral_does_not_reclassify_failed_legacy_fd_or_mask(h):
    z, d, w, g = (0.10002, 0.6, 0.8), (1.0, -0.5, -0.5), (1 / 3,) * 3, (-2.0, 1.0, 3.0)
    _, reference = interval(z, d, w, g, 0.5, 0.1, h)
    assert len(reference.pieces) == 2 and reference.transitions == ((0,),)
    derivative = math.fsum(a * b for a, b in zip(reference.central_gradient, d, strict=True))
    assert abs(reference.secant - derivative) / max(abs(derivative), 1e-8) > 1e-4
    result = check_interval(
        reference,
        d,
        h,
        0.0,
        float(reference.signed_increment),
        derivative,
        legacy_mask_passed=False,
        legacy_fd_passed=False,
    )
    assert result.passed and result.crossing
    assert result.legacy_mask_passed is result.legacy_fd_passed is False
    assert not check_interval(
        reference,
        d,
        h,
        0.0,
        float(reference.signed_increment) + 1e-8,
        derivative,
        legacy_mask_passed=False,
        legacy_fd_passed=False,
    ).passed


def simultaneous():
    z, d, w = (0.10002, 0.10002, 0.74999, 0.95), (-1.0, -1.0, 1.0, 1.0), (0.25,) * 4
    g, v, m, h = (-3.0, 2.0, -1.0, 4.0), 0.475, 0.1, 1e-4
    pieces, reference = interval(z, d, w, g, v, m, h)
    return z, d, w, g, v, m, h, pieces, reference


def test_simultaneous_transitions_retain_both_coordinates_and_one_sided_slopes():
    *_, reference = simultaneous()
    assert reference.transitions == ((0, 1),)
    left, right = reference.pieces
    assert left.value_slope != right.value_slope
    assert left.offset_end == right.offset_start
    assert left.design_end == right.design_start
    assert all(x == 0 for p in reference.pieces for x in p.weighted_residuals)


@pytest.mark.parametrize(
    "damage",
    [
        "gap",
        "tiny_gap",
        "overlap",
        "order",
        "suffix",
        "prefix",
        "hidden",
        "wrong_partition",
        "zero_length",
        "redundant",
    ],
)
def test_complete_coverage_rejects_tampered_pieces_including_sub_tolerance_gaps(damage):
    z, d, w, g, v, m, h, pieces, _ = simultaneous()
    cut = pieces[0].end
    damaged = {
        "gap": [pieces[0], replace(pieces[1], start=cut + Fraction(1, 10**8))],
        "tiny_gap": [pieces[0], replace(pieces[1], start=cut + Fraction(1, 10**30))],
        "overlap": [pieces[0], replace(pieces[1], start=cut - Fraction(1, 10**30))],
        "order": list(reversed(pieces)),
        "suffix": pieces[:1],
        "prefix": pieces[1:],
        "hidden": [Piece(-Fraction(h), Fraction(h), pieces[0].partition)],
        "wrong_partition": [pieces[0], replace(pieces[1], partition=(0, 0, 0, 0))],
        "zero_length": [replace(pieces[0], end=pieces[0].start), pieces[1]],
        "redundant": [
            replace(pieces[0], end=(pieces[0].start + cut) / 2),
            replace(pieces[0], start=(pieces[0].start + cut) / 2),
            pieces[1],
        ],
    }[damage]
    with pytest.raises(IncompleteEvidence):
        certify_interval(z, d, w, g, v, m, h, damaged)


def test_piece_cap_cannot_be_extended_or_replaced_by_a_smaller_step():
    z, d, w, g, v, m, h, pieces, _ = simultaneous()
    with pytest.raises(IncompleteEvidence, match="256"):
        certify_interval(z, d, w, g, v, m, h, pieces * 129)
    with pytest.raises(IncompleteEvidence, match="original step"):
        certify_interval(z, d, w, g, v, m, 5e-5, pieces)


@pytest.mark.parametrize("damage", ["step", "direction", "unknown_legacy", "nonfinite_secant"])
def test_interval_comparison_binds_original_context_and_preserves_unknowns(damage):
    *_, h, _, reference = simultaneous()
    direction = reference.direction
    args = {
        "step": 2e-4 if damage == "step" else h,
        "direction": tuple(-x for x in direction) if damage == "direction" else direction,
        "minus_value": 0.0,
        "plus_value": math.nan
        if damage == "nonfinite_secant"
        else float(reference.signed_increment),
        "central_derivative": 0.0,
        "legacy_mask_passed": None if damage == "unknown_legacy" else False,
        "legacy_fd_passed": False,
    }
    if damage == "nonfinite_secant":
        assert not check_interval(reference, **args).passed
    else:
        with pytest.raises(IncompleteEvidence):
            check_interval(reference, **args)


def test_constant_bound_contact_and_out_of_bounds_interval_are_incomplete():
    h = 1e-4
    # Coordinate zero persists exactly on a bound: no ordinary derivative is selected.
    pieces = [Piece(-Fraction(h), Fraction(h), (0, 0, 0))]
    with pytest.raises(IncompleteEvidence, match="degenerate"):
        certify_interval(
            (0.125, 0.5, 0.875),
            (0.0, 0.0, 0.0),
            (0.25, 0.5, 0.25),
            (1.0, -2.0, 3.0),
            0.5,
            0.125,
            h,
            pieces,
        )
    with pytest.raises(IncompleteEvidence, match="input bounds"):
        certify_interval(
            (0.0, 0.5, 0.875),
            (1.0, 0.0, 0.0),
            (0.25, 0.5, 0.25),
            (1.0, -2.0, 3.0),
            0.5,
            0.125,
            h,
            pieces,
        )


def test_central_kink_is_not_assigned_one_sided_or_zero_derivative():
    z, d, w, g = (0.125, 0.5, 0.875), (1.0, -0.5, -0.5), (0.25, 0.5, 0.25), (1.0, -2.0, 3.0)
    h, m, v = 1e-4, 0.125, 0.5
    rows = oracle.enumerate_pieces(z, d, w, v, m, h)
    with pytest.raises(UndefinedDerivative, match="central"):
        certify_interval(z, d, w, g, v, m, h, [Piece(a, b, p) for a, b, p, _, _ in rows])


def test_oracle_and_checker_import_no_candidate_or_artifact_readers():
    checker = (Path(__file__).parents[1] / "src/topolab/active_set_evidence.py").read_text()
    independent = (Path(__file__).parents[1] / "scripts/b4_27_fixture_oracle.py").read_text()
    assert "from topolab" not in checker and "import topolab" not in checker
    assert "from topolab" not in independent and "import topolab" not in independent
    assert ".read_bytes(" not in checker + independent
