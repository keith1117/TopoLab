import numpy as np
import pytest
from pydantic import ValidationError

from topolab.dataset import DatasetEnvironment
from topolab.experiment import ExperimentCase
from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.labels import (
    LABEL_RECORD_VERSION,
    LabelGenerationError,
    LabelRecord,
    generate_label,
)
from topolab.mesh import generate_structured_hex8
from topolab.model import FixedFaceSupport, PointLoad
from topolab.problem import (
    FaceLoadDefinition,
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)
from topolab.simp import evaluate_compliance


def test_label_generation_is_deterministic_state_consistent_and_serializable() -> None:
    case = ExperimentCase.from_problem(_problem())

    first = generate_label(
        case,
        source_revision="b" * 40,
        environment=_environment(),
    )
    second = generate_label(
        case,
        source_revision="b" * 40,
        environment=_environment(),
    )
    restored = LabelRecord.model_validate_json(first.model_dump_json())

    assert first == second == restored
    assert first.label_version == LABEL_RECORD_VERSION
    assert first.case == case
    assert first.tensor_dtype == "float32"
    assert first.tensor_axis_order == "channel,z,y,x"
    assert first.tensor_shape == (1, 1, 2, 4)
    assert first.termination_reason == "density_change"
    assert first.iterations == 13
    assert first.terminal_density_change == pytest.approx(
        0.009107108670230402,
        abs=1e-12,
    )

    design = first.design_tensor()
    physical = first.physical_tensor()
    assert design.shape == first.tensor_shape
    assert physical.shape == first.tensor_shape
    assert design.dtype == np.float32
    assert physical.dtype == np.float32
    assert design.flags.c_contiguous
    assert physical.flags.c_contiguous
    assert first.physical_volume_fraction == pytest.approx(
        float(np.mean(physical, dtype=np.float64)),
        abs=0.0,
    )
    assert abs(first.physical_volume_fraction - 0.5) <= 5e-3

    independently_resolved = _evaluate(case, physical.reshape(-1).astype(np.float64))
    assert first.compliance == pytest.approx(
        independently_resolved,
        rel=1e-9,
    )


def test_label_record_rejects_tampered_density_shape_mapping_and_metrics() -> None:
    label = generate_label(
        ExperimentCase.from_problem(_problem()),
        source_revision="b" * 40,
        environment=_environment(),
    )

    payload = label.model_dump(mode="json")
    payload["tensor_shape"] = [1, 1, 4, 2]
    with pytest.raises(ValidationError, match="shape does not match"):
        LabelRecord.model_validate(payload)

    payload = label.model_dump(mode="json")
    payload["design_density"][0] = 0.123456789  # type: ignore[index]
    with pytest.raises(ValidationError, match="float32 values"):
        LabelRecord.model_validate(payload)

    payload = label.model_dump(mode="json")
    payload["physical_density"][0] = 0.25  # type: ignore[index]
    with pytest.raises(ValidationError, match="density filter"):
        LabelRecord.model_validate(payload)

    payload = label.model_dump(mode="json")
    payload["physical_volume_fraction"] = 0.25
    with pytest.raises(ValidationError, match="physical_volume_fraction"):
        LabelRecord.model_validate(payload)

    payload = label.model_dump(mode="json")
    payload["terminal_density_change"] = 0.02
    with pytest.raises(ValidationError, match="convergence tolerance"):
        LabelRecord.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("label_version", "topolab.m0.label.v2"),
        ("generator_version", "topolab.m0.generator.v2"),
        ("solver_contract_version", "topolab.simp.v2"),
        ("source_revision", "not-a-commit"),
        ("source_tree_clean", False),
        ("tensor_dtype", "float64"),
        ("tensor_axis_order", "channel,x,y,z"),
        ("termination_reason", "iteration_limit"),
    ],
)
def test_label_record_rejects_changed_frozen_metadata(
    field: str,
    value: object,
) -> None:
    label = generate_label(
        ExperimentCase.from_problem(_problem()),
        source_revision="b" * 40,
        environment=_environment(),
    )
    payload = label.model_dump(mode="json")
    payload[field] = value

    with pytest.raises(ValidationError):
        LabelRecord.model_validate(payload)


def test_label_generation_rejects_nonconvergence() -> None:
    case = ExperimentCase.from_problem(
        _problem(max_iterations=1, convergence_tolerance=1e-12)
    )

    with pytest.raises(LabelGenerationError, match="did not converge"):
        generate_label(
            case,
            source_revision="b" * 40,
            environment=_environment(),
        )


def test_label_generation_supports_face_resultants() -> None:
    problem = _problem()
    payload = problem.model_dump(mode="json")
    payload["loads"] = [
        FaceLoadDefinition(
            axis="x",
            side="max",
            direction="y",
            total=-1.0,
        ).model_dump(mode="json")
    ]
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))

    label = generate_label(
        case,
        source_revision="b" * 40,
        environment=_environment(),
    )

    assert label.compliance > 0.0
    assert label.termination_reason == "density_change"


def test_label_generation_wraps_solver_failures() -> None:
    problem = _problem()
    payload = problem.model_dump(mode="json")
    payload["supports"] = [
        {
            "axis": "x",
            "side": "min",
            "directions": ["x"],
        }
    ]
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))

    with pytest.raises(LabelGenerationError, match="solver failed"):
        generate_label(
            case,
            source_revision="b" * 40,
            environment=_environment(),
        )


def _environment() -> DatasetEnvironment:
    return DatasetEnvironment(
        python_version="3.12.10",
        numpy_version="2.3.3",
        scipy_version="1.16.2",
        lockfile_sha256="a" * 64,
    )


def _problem(
    *,
    max_iterations: int = 60,
    convergence_tolerance: float = 0.01,
) -> TopologyProblem:
    return TopologyProblem(
        mesh=MeshDefinition(
            element_counts=(4, 2, 1),
            lengths=(4.0, 2.0, 1.0),
        ),
        material=MaterialDefinition(
            solid_modulus=1000.0,
            minimum_modulus=1.0,
            poisson_ratio=0.3,
        ),
        supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
        loads=(
            PointLoadDefinition(
                node=29,
                direction="y",
                magnitude=-1.0,
            ),
        ),
        optimization=OptimizationDefinition(
            volume_fraction=0.5,
            filter_radius=1.5,
            minimum_density=0.05,
            convergence_tolerance=convergence_tolerance,
            max_iterations=max_iterations,
        ),
    )


def _evaluate(case: ExperimentCase, physical_density: np.ndarray) -> float:
    problem = case.problem
    mesh = generate_structured_hex8(
        *problem.mesh.element_counts,
        lengths=problem.mesh.lengths,
    )
    loads = build_load_vector(
        mesh,
        [PointLoad(node=29, direction="y", magnitude=-1.0)],
    )
    constrained_dofs = build_constrained_dofs(
        mesh,
        [FixedFaceSupport(axis="x", side="min")],
    )
    result = evaluate_compliance(
        mesh,
        physical_density,
        loads,
        constrained_dofs,
        solid_modulus=problem.material.solid_modulus,
        minimum_modulus=problem.material.minimum_modulus,
        poisson_ratio=problem.material.poisson_ratio,
        penalty=problem.optimization.penalty,
    )
    return result.compliance
