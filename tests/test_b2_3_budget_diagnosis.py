"""The B2.3 diagnostic population is the exact failed B2.2 development set."""

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_3_budget_diagnosis import (  # noqa: E402
    FAILED_IDS,
    LARGE_FAILED_ID,
    select_failed_sources,
)

from topolab.m2_dataset import assign_m2_case_splits, build_m2_case_catalog  # noqa: E402


def test_diagnostic_population_is_exactly_eight_exposed_failures() -> None:
    sources = select_failed_sources()
    splits = assign_m2_case_splits(build_m2_case_catalog())

    assert len(sources) == 8
    assert {row.case.case_id for row in sources} == FAILED_IDS
    assert all(row.split == "train" for row in sources)
    assert all(splits[row.source_case_id] == "train" for row in sources)
    assert sum(row.scale == "large" for row in sources) == 1
    assert sum(row.scale == "small" for row in sources) == 7
    assert next(row for row in sources if row.scale == "large").case.case_id == (
        LARGE_FAILED_ID
    )
