import numpy as np
import pytest

from topolab.fem import (
    build_constrained_dofs,
    build_load_vector,
    hex8_element_stiffness,
)
from topolab.mesh import Hex8Mesh, generate_structured_hex8
from topolab.model import FixedFaceSupport, PointLoad
from topolab.simp import ComplianceResult, evaluate_compliance, simp_element_moduli

ENERGY_RELATIVE_TOLERANCE = 1e-12
FINITE_DIFFERENCE_STEP = 1e-6
FINITE_DIFFERENCE_TARGET_RELATIVE_ERROR = 1e-4
FINITE_DIFFERENCE_MAX_RELATIVE_ERROR = 1e-3


def test_simp_interpolation_uses_absolute_minimum_modulus() -> None:
    densities = np.array([0.5, 1.0])

    moduli = simp_element_moduli(
        densities,
        solid_modulus=100.0,
        minimum_modulus=2.0,
        penalty=3.0,
    )

    np.testing.assert_allclose(moduli, [14.25, 100.0], rtol=0.0, atol=1e-14)


def test_compliance_matches_sum_of_element_strain_energies() -> None:
    mesh, loads, constrained_dofs = _three_element_case()
    densities = np.array([0.45, 0.65, 0.85])
    result = _evaluate(mesh, densities, loads, constrained_dofs)

    unit_stiffness = hex8_element_stiffness(
        1.0,
        0.3,
        dimensions=(1.0, 1.0, 1.0),
    )
    moduli = simp_element_moduli(
        densities,
        solid_modulus=1000.0,
        minimum_modulus=1.0,
        penalty=3.0,
    )
    element_displacements = result.displacements[mesh.element_dofs]
    unit_energies = np.einsum(
        "ei,ij,ej->e",
        element_displacements,
        unit_stiffness,
        element_displacements,
    )
    energy_sum = float(np.dot(moduli, unit_energies))

    assert result.compliance > 0.0
    assert np.all(result.sensitivity < 0.0)
    assert result.compliance == pytest.approx(
        energy_sum,
        rel=ENERGY_RELATIVE_TOLERANCE,
    )


def test_analytical_sensitivity_matches_central_finite_difference() -> None:
    mesh, loads, constrained_dofs = _three_element_case()
    densities = np.array([0.45, 0.65, 0.85])
    result = _evaluate(mesh, densities, loads, constrained_dofs)
    finite_difference = np.empty_like(densities)

    for element in range(densities.size):
        positive = densities.copy()
        negative = densities.copy()
        positive[element] += FINITE_DIFFERENCE_STEP
        negative[element] -= FINITE_DIFFERENCE_STEP
        positive_compliance = _evaluate(
            mesh,
            positive,
            loads,
            constrained_dofs,
        ).compliance
        negative_compliance = _evaluate(
            mesh,
            negative,
            loads,
            constrained_dofs,
        ).compliance
        finite_difference[element] = (
            positive_compliance - negative_compliance
        ) / (2.0 * FINITE_DIFFERENCE_STEP)

    relative_errors = np.abs(result.sensitivity - finite_difference) / np.abs(
        finite_difference
    )
    assert np.count_nonzero(
        relative_errors <= FINITE_DIFFERENCE_TARGET_RELATIVE_ERROR
    ) >= 2
    assert np.max(relative_errors) <= FINITE_DIFFERENCE_MAX_RELATIVE_ERROR


@pytest.mark.parametrize(
    "densities",
    [
        np.array([]),
        np.ones((1, 1)),
        np.array([0.0]),
        np.array([1.01]),
        np.array([np.nan]),
    ],
)
def test_simp_interpolation_rejects_invalid_densities(densities: np.ndarray) -> None:
    with pytest.raises(ValueError):
        simp_element_moduli(
            densities,
            solid_modulus=1.0,
            minimum_modulus=1e-3,
            penalty=3.0,
        )


@pytest.mark.parametrize(
    ("solid_modulus", "minimum_modulus", "penalty"),
    [
        (0.0, 1e-3, 3.0),
        (1.0, 0.0, 3.0),
        (1.0, 1.0, 3.0),
        (1.0, 1e-3, 0.5),
        (1.0, 1e-3, float("inf")),
    ],
)
def test_simp_interpolation_rejects_invalid_parameters(
    solid_modulus: float,
    minimum_modulus: float,
    penalty: float,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        simp_element_moduli(
            np.array([0.5]),
            solid_modulus=solid_modulus,
            minimum_modulus=minimum_modulus,
            penalty=penalty,
        )


def test_compliance_rejects_density_count_that_does_not_match_mesh() -> None:
    mesh, loads, constrained_dofs = _three_element_case()

    with pytest.raises(ValueError, match=r"densities must have shape \(3,\)"):
        _evaluate(mesh, np.array([0.5, 0.5]), loads, constrained_dofs)


def _three_element_case() -> tuple[Hex8Mesh, np.ndarray, np.ndarray]:
    mesh = generate_structured_hex8(3, 1, 1, lengths=(3.0, 1.0, 1.0))
    constrained_dofs = build_constrained_dofs(
        mesh,
        [FixedFaceSupport(axis="x", side="min")],
    )
    loaded_node = int(
        np.flatnonzero(np.all(mesh.coordinates == [3.0, 1.0, 1.0], axis=1))[0]
    )
    loads = build_load_vector(
        mesh,
        [PointLoad(node=loaded_node, direction="y", magnitude=-1.0)],
    )
    return mesh, loads, constrained_dofs


def _evaluate(
    mesh: Hex8Mesh,
    densities: np.ndarray,
    loads: np.ndarray,
    constrained_dofs: np.ndarray,
) -> ComplianceResult:
    return evaluate_compliance(
        mesh,
        densities,
        loads,
        constrained_dofs,
        solid_modulus=1000.0,
        minimum_modulus=1.0,
        poisson_ratio=0.3,
        penalty=3.0,
    )
