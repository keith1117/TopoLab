import pytest
from pydantic import ValidationError

from topolab.problem import (
    FaceLoadDefinition,
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
    TopologyResult,
    solve_problem,
)


def test_problem_contract_runs_and_round_trips_result_json() -> None:
    problem = make_problem()

    result = solve_problem(problem)
    restored = TopologyResult.model_validate_json(result.model_dump_json())

    assert result.converged
    assert len(result.design_density) == 8
    assert len(result.physical_density) == 8
    assert len(result.displacements) == 90
    assert len(result.reactions) == 90
    assert result.history
    assert restored == result


def test_problem_contract_accepts_valid_initial_density() -> None:
    initial_density = (0.55,) * 8
    problem = make_problem(initial_density=initial_density)

    result = solve_problem(problem)

    assert result.history
    assert result.history[0].density_change == pytest.approx(
        max(
            abs(updated - initial)
            for updated, initial in zip(
                result.history[0].design_density,
                initial_density,
                strict=True,
            )
        ),
        abs=1e-15,
    )


def test_problem_contract_runs_a_face_resultant() -> None:
    payload = make_problem().model_dump(mode="json")
    payload["loads"] = [
        FaceLoadDefinition(
            axis="x",
            side="max",
            direction="y",
            total=-1.0,
        ).model_dump(mode="json")
    ]

    result = solve_problem(TopologyProblem.model_validate(payload))

    assert result.converged
    assert result.compliance > 0.0


@pytest.mark.parametrize(
    "update",
    [
        {"supports": []},
        {"loads": []},
        {"initial_density": [0.5] * 7},
        {"initial_density": [0.01] + [0.5] * 7},
        {
            "loads": [
                {
                    "kind": "point",
                    "node": 30,
                    "direction": "y",
                    "magnitude": -1.0,
                }
            ]
        },
    ],
)
def test_problem_contract_rejects_invalid_cross_field_inputs(
    update: dict[str, object],
) -> None:
    payload = make_problem().model_dump(mode="json")
    payload.update(update)

    with pytest.raises(ValidationError):
        TopologyProblem.model_validate(payload)


def test_problem_contract_rejects_extra_fields_and_boolean_dimensions() -> None:
    payload = make_problem().model_dump(mode="json")
    payload["unexpected"] = True

    with pytest.raises(ValidationError):
        TopologyProblem.model_validate(payload)

    payload = make_problem().model_dump(mode="json")
    payload["mesh"]["element_counts"] = [True, 2, 1]  # type: ignore[index]
    with pytest.raises(ValidationError):
        TopologyProblem.model_validate(payload)


def make_problem(
    *,
    element_counts: tuple[int, int, int] = (4, 2, 1),
    initial_density: tuple[float, ...] | None = None,
) -> TopologyProblem:
    nx, ny, nz = element_counts
    loaded_node = nx + (nx + 1) * (ny + (ny + 1) * nz)
    return TopologyProblem(
        mesh=MeshDefinition(
            element_counts=element_counts,
            lengths=(float(nx), float(ny), float(nz)),
        ),
        material=MaterialDefinition(
            solid_modulus=1000.0,
            minimum_modulus=1.0,
            poisson_ratio=0.3,
        ),
        supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
        loads=(
            PointLoadDefinition(
                node=loaded_node,
                direction="y",
                magnitude=-1.0,
            ),
        ),
        optimization=OptimizationDefinition(
            volume_fraction=0.5,
            filter_radius=1.5,
            minimum_density=0.05,
            convergence_tolerance=0.01,
            max_iterations=60,
        ),
        initial_density=initial_density,
    )
