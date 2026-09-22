import json

import pytest
from pydantic import ValidationError

from topolab.catalog import (
    CASE_CATALOG_ID_PREFIX,
    CASE_CATALOG_VERSION,
    M0_CASE_CATALOG_ID,
    CaseCatalog,
    build_catalog_id,
    build_m0_case_catalog,
    canonical_catalog_json,
)
from topolab.dataset import DatasetEnvironment
from topolab.problem import PointLoadDefinition


def test_m0_catalog_has_stable_identity_and_json_round_trip() -> None:
    catalog = build_m0_case_catalog()
    restored = CaseCatalog.model_validate_json(catalog.model_dump_json())

    assert restored == catalog
    assert catalog.catalog_version == CASE_CATALOG_VERSION
    assert catalog.catalog_id == M0_CASE_CATALOG_ID
    assert catalog.catalog_id == (
        "tlcatalog-v1-e532ad3d9de3083918e1ab074e7ba3b88a254d0b6729af508f96959ea1eedc3d"
    )
    assert catalog.catalog_id.startswith(CASE_CATALOG_ID_PREFIX)
    assert catalog.catalog_id == build_catalog_id(reversed(catalog.cases))
    assert json.loads(catalog.canonical_identity_json()) == json.loads(
        canonical_catalog_json(catalog.cases)
    )
    assert tuple(case.case_id for case in catalog.cases) == tuple(
        sorted(case.case_id for case in catalog.cases)
    )
    assert catalog.cases[0].case_id == (
        "tlcase-v1-03dc455163a08145ffd01c55cba407a50414f07dfab550111784d0a141c66527"
    )
    assert catalog.cases[-1].case_id == (
        "tlcase-v1-f97f8a73dc947430cca6abfe1ea1d832c4d54a4a9d7b18a7307e2bd86fb26274"
    )


def test_m0_catalog_exactly_enumerates_frozen_cohort_and_matched_ood_axis() -> None:
    catalog = build_m0_case_catalog()

    assert len(catalog.cases) == 160
    assert len({case.case_id for case in catalog.cases}) == 160
    assert {case.problem.mesh.element_counts for case in catalog.cases} == {(12, 6, 3)}
    assert {case.problem.mesh.lengths for case in catalog.cases} == {(12.0, 6.0, 3.0)}
    assert {
        case.problem.optimization.volume_fraction for case in catalog.cases
    } == {0.2, 0.3, 0.4, 0.5, 0.6}

    signatures: set[tuple[int, float, str]] = set()
    for case in catalog.cases:
        problem = case.problem
        assert problem.initial_density is None
        assert problem.material.model_dump() == {
            "solid_modulus": 1000.0,
            "minimum_modulus": 1.0,
            "poisson_ratio": 0.3,
        }
        assert tuple(support.model_dump() for support in problem.supports) == (
            {
                "axis": "x",
                "side": "min",
                "directions": ("x", "y", "z"),
            },
        )
        assert len(problem.loads) == 1
        load = problem.loads[0]
        assert isinstance(load, PointLoadDefinition)
        assert load.magnitude == -1.0
        assert load.direction in {"y", "z"}
        signatures.add(
            (load.node, problem.optimization.volume_fraction, str(load.direction))
        )
        assert problem.optimization.model_dump() == {
            "volume_fraction": problem.optimization.volume_fraction,
            "filter_radius": 1.5,
            "penalty": 3.0,
            "minimum_density": 0.05,
            "move_limit": 0.2,
            "convergence_tolerance": 0.01,
            "max_iterations": 100,
        }

    nx, ny = 12, 6
    expected_nodes = {
        nx + (nx + 1) * (y_index + (ny + 1) * z_index)
        for y_index in (0, 2, 4, 6)
        for z_index in (0, 1, 2, 3)
    }
    assert {signature[0] for signature in signatures} == expected_nodes
    assert len(signatures) == 160
    for loaded_node in expected_nodes:
        for volume_fraction in (0.2, 0.3, 0.4, 0.5, 0.6):
            assert (loaded_node, volume_fraction, "y") in signatures
            assert (loaded_node, volume_fraction, "z") in signatures


def test_m0_catalog_builds_manifest_with_frozen_nonempty_partitions() -> None:
    manifest = build_m0_case_catalog().build_manifest(
        source_revision="b" * 40,
        environment=_environment(),
    )

    assert manifest.split_counts.model_dump() == {
        "train": 60,
        "validation": 9,
        "test": 11,
        "ood": 80,
    }
    assert len(manifest.samples) == 160
    assert {sample.load_scale for sample in manifest.samples} == {1.0}


def test_catalog_rejects_duplicate_stale_and_changed_schema() -> None:
    catalog = build_m0_case_catalog()

    with pytest.raises(ValueError, match="unique case IDs"):
        CaseCatalog.from_cases((*catalog.cases, catalog.cases[0]))

    payload = catalog.model_dump(mode="json")
    payload["cases"] = payload["cases"][1:]  # type: ignore[index]
    with pytest.raises(ValidationError, match="catalog_id does not match"):
        CaseCatalog.model_validate(payload)

    payload = catalog.model_dump(mode="json")
    payload["catalog_version"] = "topolab.m0.catalog.v2"
    with pytest.raises(ValidationError):
        CaseCatalog.model_validate(payload)

    payload = catalog.model_dump(mode="json")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        CaseCatalog.model_validate(payload)


def _environment() -> DatasetEnvironment:
    return DatasetEnvironment(
        python_version="3.12.10",
        numpy_version="2.3.3",
        scipy_version="1.16.2",
        lockfile_sha256="a" * 64,
    )
