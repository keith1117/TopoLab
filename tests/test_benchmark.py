import math

import pytest

from topolab.benchmark import BenchmarkCase, generate_report, measure_case


def test_measure_case_reports_sparse_size_timings_and_equilibrium() -> None:
    result = measure_case(BenchmarkCase("tiny", (2, 1, 1)), repeated_runs=2)

    assert result.elements == 2
    assert result.nodes == 12
    assert result.degrees_of_freedom == 36
    assert result.free_degrees_of_freedom == 24
    assert result.nonzero_entries > 0
    assert result.csr_payload_mib > 0.0
    assert result.dense_global_gib_estimate == pytest.approx(
        36**2 * 8 / 1024**3,
    )
    assert result.dense_to_csr_payload_ratio > 0.0
    assert result.process_peak_rss_mib > 0.0
    assert result.process_peak_rss_increase_mib >= 0.0
    assert math.isfinite(result.compliance)
    assert result.equilibrium_relative_residual <= 1.0e-8
    for timing in (result.assembly, result.solve, result.total):
        assert timing.cold_seconds >= 0.0
        assert len(timing.repeated_seconds) == 2
        assert all(value >= 0.0 for value in timing.repeated_seconds)
        assert timing.repeated_median_seconds >= 0.0


def test_generate_report_uses_an_isolated_worker_and_records_configuration() -> None:
    report = generate_report(
        cases=(BenchmarkCase("tiny", (1, 1, 1)),),
        repeated_runs=1,
    )

    assert report["schema_version"] == 1
    assert report["git_revision"]
    configuration = report["configuration"]
    assert isinstance(configuration, dict)
    assert configuration["cold_runs_per_case"] == 1
    assert configuration["repeated_runs_per_case"] == 1
    assert configuration["thread_environment"] == {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "BLIS_NUM_THREADS": "1",
        "OMP_DYNAMIC": "FALSE",
        "MKL_DYNAMIC": "FALSE",
    }
    cases = report["cases"]
    assert isinstance(cases, list)
    assert cases[0]["case"] == "tiny"
    assert cases[0]["element_counts"] == [1, 1, 1]


@pytest.mark.parametrize("repeated_runs", [0, -1])
def test_measure_case_rejects_nonpositive_repeat_count(repeated_runs: int) -> None:
    with pytest.raises(ValueError, match="repeated_runs must be positive"):
        measure_case(
            BenchmarkCase("tiny", (1, 1, 1)),
            repeated_runs=repeated_runs,
        )
