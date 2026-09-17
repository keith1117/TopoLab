import numpy as np
import pytest

from topolab.fem import hex8_element_stiffness, isotropic_elasticity_matrix

MATRIX_RELATIVE_TOLERANCE = 1e-12
RIGID_MODE_RELATIVE_TOLERANCE = 1e-14
EIGENVALUE_RELATIVE_TOLERANCE = 1e-12


def test_isotropic_elasticity_matrix_uses_documented_voigt_order() -> None:
    matrix = isotropic_elasticity_matrix(120.0, 0.25)

    expected = np.array(
        [
            [144.0, 48.0, 48.0, 0.0, 0.0, 0.0],
            [48.0, 144.0, 48.0, 0.0, 0.0, 0.0],
            [48.0, 48.0, 144.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 48.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 48.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 48.0],
        ]
    )
    np.testing.assert_allclose(matrix, expected, rtol=MATRIX_RELATIVE_TOLERANCE)


def test_hex8_stiffness_is_symmetric_with_six_rigid_body_modes() -> None:
    stiffness = hex8_element_stiffness(1.0, 0.3, dimensions=(2.0, 3.0, 4.0))

    assert stiffness.shape == (24, 24)
    assert stiffness.dtype == np.float64
    np.testing.assert_allclose(
        stiffness,
        stiffness.T,
        rtol=MATRIX_RELATIVE_TOLERANCE,
        atol=MATRIX_RELATIVE_TOLERANCE,
    )
    eigenvalues = np.linalg.eigvalsh(stiffness)
    spectral_scale = np.max(np.abs(eigenvalues))
    assert np.all(eigenvalues >= -EIGENVALUE_RELATIVE_TOLERANCE * spectral_scale)
    assert np.all(np.abs(eigenvalues[:6]) <= EIGENVALUE_RELATIVE_TOLERANCE * spectral_scale)
    assert np.all(eigenvalues[6:] > EIGENVALUE_RELATIVE_TOLERANCE * spectral_scale)


def test_hex8_stiffness_annihilates_explicit_rigid_body_modes() -> None:
    dimensions = (2.0, 3.0, 4.0)
    stiffness = hex8_element_stiffness(1.0, 0.3, dimensions=dimensions)
    coordinates = _element_coordinates(dimensions)
    translations = [
        np.tile([1.0, 0.0, 0.0], 8),
        np.tile([0.0, 1.0, 0.0], 8),
        np.tile([0.0, 0.0, 1.0], 8),
    ]
    rotations = [
        np.column_stack((np.zeros(8), -coordinates[:, 2], coordinates[:, 1])).ravel(),
        np.column_stack((coordinates[:, 2], np.zeros(8), -coordinates[:, 0])).ravel(),
        np.column_stack((-coordinates[:, 1], coordinates[:, 0], np.zeros(8))).ravel(),
    ]

    stiffness_norm = np.linalg.norm(stiffness)
    for mode in translations + rotations:
        relative_residual = np.linalg.norm(stiffness @ mode) / (
            stiffness_norm * np.linalg.norm(mode)
        )
        assert relative_residual <= RIGID_MODE_RELATIVE_TOLERANCE


def test_hex8_affine_displacement_matches_constant_strain_energy() -> None:
    dimensions = (1.5, 2.0, 0.75)
    youngs_modulus = 210.0
    poisson_ratio = 0.29
    strain = np.array([0.01, -0.004, 0.007, 0.006, -0.003, 0.005])
    coordinates = _element_coordinates(dimensions)
    strain_tensor = np.array(
        [
            [strain[0], strain[3] / 2.0, strain[5] / 2.0],
            [strain[3] / 2.0, strain[1], strain[4] / 2.0],
            [strain[5] / 2.0, strain[4] / 2.0, strain[2]],
        ]
    )
    displacement = (coordinates @ strain_tensor.T).ravel()

    stiffness = hex8_element_stiffness(
        youngs_modulus,
        poisson_ratio,
        dimensions=dimensions,
    )
    constitutive_matrix = isotropic_elasticity_matrix(youngs_modulus, poisson_ratio)
    finite_element_energy = 0.5 * displacement @ stiffness @ displacement
    analytical_energy = (
        0.5 * np.prod(dimensions) * strain @ constitutive_matrix @ strain
    )

    assert finite_element_energy == pytest.approx(
        analytical_energy,
        rel=MATRIX_RELATIVE_TOLERANCE,
    )


def test_hex8_stiffness_scales_linearly_with_youngs_modulus() -> None:
    base = hex8_element_stiffness(1.0, 0.25)
    scaled = hex8_element_stiffness(7.5, 0.25)

    np.testing.assert_allclose(
        scaled,
        7.5 * base,
        rtol=MATRIX_RELATIVE_TOLERANCE,
        atol=MATRIX_RELATIVE_TOLERANCE,
    )


@pytest.mark.parametrize(
    ("youngs_modulus", "poisson_ratio", "error_type", "message"),
    [
        (0.0, 0.3, ValueError, "youngs_modulus must be positive and finite"),
        (-1.0, 0.3, ValueError, "youngs_modulus must be positive and finite"),
        (float("inf"), 0.3, ValueError, "youngs_modulus must be finite"),
        (1.0, -1.0, ValueError, "poisson_ratio must be greater than -1"),
        (1.0, 0.5, ValueError, "poisson_ratio must be greater than -1"),
        (1.0, float("nan"), ValueError, "poisson_ratio must be finite"),
        (True, 0.3, TypeError, "youngs_modulus must be a real number"),
    ],
)
def test_invalid_material_parameters_are_rejected(
    youngs_modulus: object,
    poisson_ratio: object,
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        isotropic_elasticity_matrix(  # type: ignore[arg-type]
            youngs_modulus,
            poisson_ratio,
        )


@pytest.mark.parametrize(
    ("dimensions", "error_type", "message"),
    [
        ((0.0, 1.0, 1.0), ValueError, "hx must be positive and finite"),
        ((1.0, -1.0, 1.0), ValueError, "hy must be positive and finite"),
        ((1.0, 1.0, float("inf")), ValueError, "hz must be finite"),
        ((True, 1.0, 1.0), TypeError, "hx must be a real number"),
    ],
)
def test_invalid_element_dimensions_are_rejected(
    dimensions: tuple[object, object, object],
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        hex8_element_stiffness(1.0, 0.3, dimensions=dimensions)  # type: ignore[arg-type]


def test_wrong_number_of_element_dimensions_is_rejected() -> None:
    with pytest.raises(ValueError, match="dimensions must contain exactly three values"):
        hex8_element_stiffness(1.0, 0.3, dimensions=(1.0, 1.0))  # type: ignore[arg-type]


def _element_coordinates(dimensions: tuple[float, float, float]) -> np.ndarray:
    hx, hy, hz = dimensions
    return np.array(
        [
            [0.0, 0.0, 0.0],
            [hx, 0.0, 0.0],
            [hx, hy, 0.0],
            [0.0, hy, 0.0],
            [0.0, 0.0, hz],
            [hx, 0.0, hz],
            [hx, hy, hz],
            [0.0, hy, hz],
        ]
    )
