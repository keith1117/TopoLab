"""Independent acceptance case for the versioned B2.3 budget extension."""

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_3_budget_diagnosis import LARGE_FAILED_ID, select_failed_sources  # noqa: E402
from b2_workload_pilot import _raw_uniform  # noqa: E402

from topolab.baselines import validate_refinement_quality  # noqa: E402
from topolab.experiment import ExperimentCase, project_design_density  # noqa: E402
from topolab.problem import TopologyProblem, solve_problem  # noqa: E402


def test_budget_240_accepts_fixed_large_z_failure_without_threshold_change() -> None:
    source = next(
        row.case for row in select_failed_sources() if row.case.case_id == LARGE_FAILED_ID
    )
    payload = source.problem.model_dump(mode="json")
    payload["optimization"]["max_iterations"] = 240
    new_case = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
    assert new_case.case_id != source.case_id
    assert new_case.problem.optimization.convergence_tolerance == 0.01
    projected = project_design_density(new_case, _raw_uniform(new_case))
    payload["initial_density"] = tuple(float(value) for value in projected.design_density)

    result = solve_problem(
        TopologyProblem.model_validate(payload), termination_policy="physical_plateau"
    )

    assert result.converged
    assert 120 < len(result.history) <= 240
    assert result.history[-1].density_change <= 0.01
    assert result.design_density == result.history[-1].design_density
    assert result.physical_density == result.history[-1].physical_density
    assert result.compliance == result.history[-1].compliance
    validate_refinement_quality(new_case, result, None)
