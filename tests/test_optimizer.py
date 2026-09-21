import numpy as np
import pytest

from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.mesh import Hex8Mesh, generate_structured_hex8
from topolab.model import FixedFaceSupport, PointLoad
from topolab.simp import (
    OptimizationCancelledError,
    SimpConfig,
    SimpIteration,
    SimpResult,
    apply_density_filter,
    backpropagate_density_gradient,
    build_density_filter,
    evaluate_compliance,
    optimality_criteria_update,
    optimize_simp,
)

FILTER_GRADIENT_STEP = 1e-7
FILTER_GRADIENT_RELATIVE_TOLERANCE = 1e-8
VOLUME_ABSOLUTE_TOLERANCE = 5e-3
FINAL_COMPLIANCE_RELATIVE_TOLERANCE = 1e-9


def test_density_filter_uses_documented_distance_weights() -> None:
    mesh = generate_structured_hex8(3, 1, 1, lengths=(3.0, 1.0, 1.0))
    density_filter = build_density_filter(mesh, radius=1.5)

    physical = apply_density_filter(density_filter, np.array([1.0, 0.0, 0.0]))

    np.testing.assert_allclose(physical, [0.75, 0.2, 0.0], rtol=0.0, atol=1e-15)
    np.testing.assert_allclose(
        density_filter.matrix.toarray(),
        density_filter.matrix.toarray().T,
        rtol=0.0,
        atol=0.0,
    )


@pytest.mark.parametrize("density", [0.05, 1.0])
def test_density_filter_preserves_constant_bound_fields_exactly(density: float) -> None:
    mesh = generate_structured_hex8(12, 6, 3, lengths=(12.0, 6.0, 3.0))
    density_filter = build_density_filter(mesh, radius=1.5)
    design = np.full(12 * 6 * 3, density)

    physical = apply_density_filter(density_filter, design)

    np.testing.assert_array_equal(physical, design)
    assert np.all(physical >= density)
    assert np.all(physical <= density)


def test_density_filter_gradient_matches_central_finite_difference() -> None:
    mesh = generate_structured_hex8(3, 1, 1, lengths=(3.0, 1.0, 1.0))
    density_filter = build_density_filter(mesh, radius=1.5)
    design = np.array([0.3, 0.6, 0.8])
    physical_gradient = np.array([1.2, -0.4, 0.7])
    analytical = backpropagate_density_gradient(density_filter, physical_gradient)
    finite_difference = np.empty_like(design)

    for element in range(design.size):
        positive = design.copy()
        negative = design.copy()
        positive[element] += FILTER_GRADIENT_STEP
        negative[element] -= FILTER_GRADIENT_STEP
        positive_value = float(
            np.dot(
                physical_gradient,
                apply_density_filter(density_filter, positive),
            )
        )
        negative_value = float(
            np.dot(
                physical_gradient,
                apply_density_filter(density_filter, negative),
            )
        )
        finite_difference[element] = (
            positive_value - negative_value
        ) / (2.0 * FILTER_GRADIENT_STEP)

    np.testing.assert_allclose(
        analytical,
        finite_difference,
        rtol=FILTER_GRADIENT_RELATIVE_TOLERANCE,
        atol=1e-10,
    )


def test_oc_update_enforces_filtered_volume_and_move_bounds() -> None:
    mesh = generate_structured_hex8(4, 2, 1, lengths=(4.0, 2.0, 1.0))
    density_filter = build_density_filter(mesh, radius=1.5)
    design = np.full(8, 0.5)
    objective_gradient = -np.linspace(1.0, 3.0, 8)
    volume_gradient = backpropagate_density_gradient(
        density_filter,
        np.full(8, 1.0 / 8.0),
    )

    updated = optimality_criteria_update(
        design,
        objective_gradient,
        volume_gradient,
        density_filter,
        volume_fraction=0.5,
        minimum_density=0.05,
        move_limit=0.2,
    )
    physical = apply_density_filter(density_filter, updated)

    assert abs(float(np.mean(physical)) - 0.5) <= 1e-8
    assert np.all(updated >= 0.3)
    assert np.all(updated <= 0.7)


def test_optimizer_history_and_final_resolve_are_state_consistent() -> None:
    mesh, loads, constrained_dofs, config = _optimization_case()
    result = _run_optimizer(mesh, loads, constrained_dofs, config)
    density_filter = build_density_filter(mesh, config.filter_radius)
    previous_design = np.full(mesh.element_dofs.shape[0], config.volume_fraction)

    assert result.history
    assert result.converged
    assert len(result.history) <= config.max_iterations
    for expected_iteration, state in enumerate(result.history, start=1):
        assert state.iteration == expected_iteration
        np.testing.assert_allclose(
            state.physical_density,
            apply_density_filter(density_filter, state.design_density),
            rtol=0.0,
            atol=1e-15,
        )
        assert state.volume_fraction == pytest.approx(
            float(np.mean(state.physical_density)),
            abs=1e-15,
        )
        assert state.density_change == pytest.approx(
            float(np.max(np.abs(state.design_density - previous_design))),
            abs=1e-15,
        )
        previous_design = state.design_density

    final_state = result.history[-1]
    np.testing.assert_array_equal(result.design_density, final_state.design_density)
    np.testing.assert_array_equal(result.physical_density, final_state.physical_density)
    assert result.compliance == final_state.compliance
    assert abs(float(np.mean(result.physical_density)) - config.volume_fraction) <= (
        VOLUME_ABSOLUTE_TOLERANCE
    )
    independently_resolved = evaluate_compliance(
        mesh,
        result.physical_density,
        loads,
        constrained_dofs,
        solid_modulus=1000.0,
        minimum_modulus=1.0,
        poisson_ratio=0.3,
        penalty=config.penalty,
    )
    assert result.compliance == pytest.approx(
        independently_resolved.compliance,
        rel=FINAL_COMPLIANCE_RELATIVE_TOLERANCE,
    )
    np.testing.assert_allclose(
        result.displacements,
        independently_resolved.displacements,
        rtol=FINAL_COMPLIANCE_RELATIVE_TOLERANCE,
        atol=1e-12,
    )


def test_optimizer_handles_filter_roundoff_at_saturated_density_bound() -> None:
    mesh = generate_structured_hex8(12, 6, 3, lengths=(12.0, 6.0, 3.0))
    constrained_dofs = build_constrained_dofs(
        mesh,
        [FixedFaceSupport(axis="x", side="min")],
    )
    loads = build_load_vector(
        mesh,
        [PointLoad(node=12, direction="y", magnitude=-1.0)],
    )
    config = SimpConfig(
        volume_fraction=0.5,
        filter_radius=1.5,
        minimum_density=0.05,
        convergence_tolerance=0.01,
        max_iterations=100,
    )

    result = _run_optimizer(mesh, loads, constrained_dofs, config)

    assert result.converged
    assert np.all(result.physical_density > 0.0)
    assert np.all(result.physical_density <= 1.0)


def test_optimizer_is_deterministic() -> None:
    mesh, loads, constrained_dofs, config = _optimization_case()

    first = _run_optimizer(mesh, loads, constrained_dofs, config)
    second = _run_optimizer(mesh, loads, constrained_dofs, config)

    assert first.converged == second.converged
    assert first.compliance == second.compliance
    assert len(first.history) == len(second.history)
    np.testing.assert_array_equal(first.design_density, second.design_density)
    np.testing.assert_array_equal(first.physical_density, second.physical_density)
    for first_state, second_state in zip(first.history, second.history, strict=True):
        assert first_state.compliance == second_state.compliance
        assert first_state.volume_fraction == second_state.volume_fraction
        assert first_state.density_change == second_state.density_change
        np.testing.assert_array_equal(
            first_state.design_density,
            second_state.design_density,
        )


def test_optimizer_accepts_custom_initial_density() -> None:
    mesh, loads, constrained_dofs, config = _optimization_case()
    initial_density = np.full(mesh.element_dofs.shape[0], 0.55)

    result = _run_optimizer(
        mesh,
        loads,
        constrained_dofs,
        config,
        initial_density=initial_density,
    )

    assert result.history
    assert result.history[0].density_change == pytest.approx(
        float(np.max(np.abs(result.history[0].design_density - initial_density))),
        abs=1e-15,
    )


def test_optimizer_reports_iterations_and_honors_cooperative_cancellation() -> None:
    mesh, loads, constrained_dofs, config = _optimization_case()
    observed_iterations: list[SimpIteration] = []
    cancel_requested = False

    def record_iteration(state: SimpIteration) -> None:
        nonlocal cancel_requested
        observed_iterations.append(state)
        cancel_requested = True

    with pytest.raises(OptimizationCancelledError, match="cancelled"):
        optimize_simp(
            mesh,
            loads,
            constrained_dofs,
            solid_modulus=1000.0,
            minimum_modulus=1.0,
            poisson_ratio=0.3,
            config=config,
            iteration_callback=record_iteration,
            should_cancel=lambda: cancel_requested,
        )

    assert len(observed_iterations) == 1


@pytest.mark.parametrize(
    "config",
    [
        SimpConfig(volume_fraction=0.0, filter_radius=1.5),
        SimpConfig(volume_fraction=1.1, filter_radius=1.5),
        SimpConfig(volume_fraction=0.5, filter_radius=0.0),
        SimpConfig(volume_fraction=0.5, filter_radius=1.5, minimum_density=0.5),
        SimpConfig(volume_fraction=0.5, filter_radius=1.5, move_limit=0.0),
        SimpConfig(
            volume_fraction=0.5,
            filter_radius=1.5,
            convergence_tolerance=0.0,
        ),
        SimpConfig(volume_fraction=0.5, filter_radius=1.5, max_iterations=0),
    ],
)
def test_optimizer_rejects_invalid_configuration(config: SimpConfig) -> None:
    mesh, loads, constrained_dofs, _ = _optimization_case()

    with pytest.raises((TypeError, ValueError)):
        _run_optimizer(mesh, loads, constrained_dofs, config)


def test_optimizer_rejects_invalid_initial_density() -> None:
    mesh, loads, constrained_dofs, config = _optimization_case()

    with pytest.raises(ValueError, match=r"initial_density must have shape \(8,\)"):
        _run_optimizer(
            mesh,
            loads,
            constrained_dofs,
            config,
            initial_density=np.full(7, 0.5),
        )
    with pytest.raises(ValueError, match="at least minimum_density"):
        initial = np.full(8, 0.5)
        initial[0] = 0.01
        _run_optimizer(
            mesh,
            loads,
            constrained_dofs,
            config,
            initial_density=initial,
        )


def test_density_filter_rejects_invalid_radius_and_vectors() -> None:
    mesh = generate_structured_hex8(2, 1, 1)

    with pytest.raises(ValueError, match="radius must be positive"):
        build_density_filter(mesh, radius=0.0)

    density_filter = build_density_filter(mesh, radius=1.5)
    with pytest.raises(ValueError, match=r"design_density must have shape \(2,\)"):
        apply_density_filter(density_filter, np.ones(3))
    with pytest.raises(ValueError, match="interval"):
        apply_density_filter(density_filter, np.array([0.5, 1.1]))


def _optimization_case() -> tuple[Hex8Mesh, np.ndarray, np.ndarray, SimpConfig]:
    mesh = generate_structured_hex8(4, 2, 1, lengths=(4.0, 2.0, 1.0))
    constrained_dofs = build_constrained_dofs(
        mesh,
        [FixedFaceSupport(axis="x", side="min")],
    )
    loaded_node = int(
        np.flatnonzero(np.all(mesh.coordinates == [4.0, 2.0, 1.0], axis=1))[0]
    )
    loads = build_load_vector(
        mesh,
        [PointLoad(node=loaded_node, direction="y", magnitude=-1.0)],
    )
    config = SimpConfig(
        volume_fraction=0.5,
        filter_radius=1.5,
        penalty=3.0,
        minimum_density=0.05,
        move_limit=0.2,
        convergence_tolerance=0.01,
        max_iterations=60,
    )
    return mesh, loads, constrained_dofs, config


def _run_optimizer(
    mesh: Hex8Mesh,
    loads: np.ndarray,
    constrained_dofs: np.ndarray,
    config: SimpConfig,
    *,
    initial_density: np.ndarray | None = None,
) -> SimpResult:
    return optimize_simp(
        mesh,
        loads,
        constrained_dofs,
        solid_modulus=1000.0,
        minimum_modulus=1.0,
        poisson_ratio=0.3,
        config=config,
        initial_density=initial_density,
    )
