"""Independent B2.1 acceptance case for the opt-in physical-state policy."""

import sys
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_1_convergence import EXPECTED_LARGE_IDS, result_id, select_cases  # noqa: E402
from b2_workload_pilot import scaled_case  # noqa: E402

from topolab.baselines import validate_refinement_quality  # noqa: E402
from topolab.experiment import project_design_density  # noqa: E402
from topolab.m2_dataset import build_m2_case_catalog  # noqa: E402
from topolab.problem import TopologyProblem, solve_problem  # noqa: E402


def test_new_solver_identity_covers_exact_b2_cohort_without_labels() -> None:
    cohort = select_cases()

    assert len(cohort) == 12
    assert tuple(item.case.case_id for item in cohort if item.scale == "large") == (
        EXPECTED_LARGE_IDS
    )
    assert len({result_id(item.case.case_id) for item in cohort}) == 12
    assert all(result_id(item.case.case_id).startswith("tlcase-b21-v1-") for item in cohort)
    assert all(item.source_case_id != item.case.case_id for item in cohort if item.scale == "large")


def test_physical_plateau_accepts_fixed_large_high_volume_case() -> None:
    source_id = (
        "tlcase-v1-c107c6c0660eb2a8b85a2470d1f9ae663abc2148edf764856f2b5c948e0bca7b"
    )
    source = next(
        case for case in build_m2_case_catalog().cases if case.case_id == source_id
    )
    case = scaled_case(source)
    assert case.case_id == (
        "tlcase-v1-17b81b5d678bd05109b31b55272ace9421584ea2e06fad1d39c39c4afa846fdd"
    )
    nx, ny, nz = case.problem.mesh.element_counts
    raw = np.full((1, nz, ny, nx), 0.6, dtype=np.float32)
    projected = project_design_density(case, raw)
    payload = case.problem.model_dump(mode="json")
    payload["initial_density"] = tuple(float(v) for v in projected.design_density)
    problem = TopologyProblem.model_validate(payload)

    result = solve_problem(problem, termination_policy="physical_plateau")

    assert result.converged
    assert len(result.history) <= 120
    assert result.history[-1].density_change > 0.01
    recent = result.history[-11:]
    assert all(
        np.max(np.abs(np.asarray(right.physical_density) - left.physical_density))
        <= 0.01
        for left, right in zip(recent[:-1], recent[1:], strict=True)
    )
    improvement = 1.0 - recent[-1].compliance / recent[0].compliance
    assert 0.0 <= improvement <= 0.0002
    assert result.design_density == result.history[-1].design_density
    assert result.physical_density == result.history[-1].physical_density
    assert result.compliance == result.history[-1].compliance
    validate_refinement_quality(case, result, None)
