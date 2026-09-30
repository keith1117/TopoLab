import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from topolab.b3_catalog import (
    B3_CATALOG_SHA256,
    B3_CONTRACT_SHA256,
    B3_EXPOSURE_SHA256,
    B3CaseCatalog,
    B3CatalogEntry,
    B3ExposureLedger,
    build_b3_case_catalog,
    build_b3_exposure_ledger,
    physical_fingerprint,
)
from topolab.catalog import build_m0_case_catalog
from topolab.experiment import ExperimentCase
from topolab.problem import TopologyProblem


def test_frozen_hashes_canonical_bytes_and_round_trips() -> None:
    catalog, ledger = build_b3_case_catalog(), build_b3_exposure_ledger()
    assert hashlib.sha256(catalog.canonical_identity_bytes()).hexdigest() == B3_CATALOG_SHA256
    assert hashlib.sha256(ledger.canonical_identity_bytes()).hexdigest() == B3_EXPOSURE_SHA256
    root = Path(__file__).resolve().parents[1]
    assert hashlib.sha256((root / "docs/b3_experiment_contract.md").read_bytes()).hexdigest() == (
        B3_CONTRACT_SHA256
    )
    assert B3CaseCatalog.model_validate_json(catalog.model_dump_json()) == catalog
    assert B3ExposureLedger.model_validate_json(ledger.model_dump_json()) == ledger
    for data in (catalog.canonical_identity_bytes(), ledger.canonical_identity_bytes()):
        assert data.endswith(b"\n") and not data.endswith(b"\n\n")
        assert (
            data.decode("ascii")
            == json.dumps(
                json.loads(data), sort_keys=True, separators=(",", ":"), ensure_ascii=True
            )
            + "\n"
        )


def test_all_roles_strata_training_memberships_and_ood_pairs() -> None:
    catalog = build_b3_case_catalog()
    assert Counter(e.role for e in catalog.entries) == {
        "train": 528,
        "fit_validation": 32,
        "screen_validation": 48,
        "final_id": 96,
        "final_ood": 48,
    }
    assert Counter(e.case.problem.mesh.element_counts for e in catalog.for_role("train")) == {
        (12, 6, 3): 432,
        (24, 12, 6): 96,
    }
    memberships = {
        name: {e.case.case_id for e in catalog.for_training_set(name)}
        for name in ("base", "expanded", "specialist")
    }
    assert {name: len(ids) for name, ids in memberships.items()} == {
        "base": 468,
        "expanded": 508,
        "specialist": 488,
    }
    assert memberships["expanded"] & memberships["specialist"] == memberships["base"]
    assert memberships["expanded"] | memberships["specialist"] == {
        e.case.case_id for e in catalog.for_role("train")
    }
    historical = {e.physical_fingerprint for e in build_b3_exposure_ledger().entries}
    assert len({e.physical_fingerprint for e in catalog.entries}) == 752
    for role, per_cell in (
        ("fit_validation", 2),
        ("screen_validation", 3),
        ("final_id", 6),
        ("final_ood", 6),
    ):
        entries = catalog.for_role(role)
        cells = Counter(
            (
                e.case.problem.mesh.element_counts,
                e.case.problem.loads[0].direction,
                e.case.problem.optimization.volume_fraction,
            )
            for e in entries
        )
        assert set(cells.values()) == {per_cell}
        assert len(cells) == (8 if role == "final_ood" else 16)
        assert not {e.physical_fingerprint for e in entries} & historical
    final_ids = {e.case.case_id for e in catalog.for_role("final_id")}
    for entry in catalog.for_role("final_ood"):
        payload = entry.case.problem.model_dump(mode="json")
        payload["loads"][0]["direction"] = "y"
        assert ExperimentCase.from_problem(TopologyProblem.model_validate(payload)).case_id in (
            final_ids
        )
    for entry in catalog.entries:
        problem = entry.case.problem
        assert problem.optimization.max_iterations == 360 and problem.initial_density is None
        assert problem.mesh.lengths == (12.0, 6.0, 3.0)
        assert problem.optimization.filter_radius == 1.5
        if entry.role == "train":
            payload = problem.model_dump(mode="json")
            payload["optimization"]["max_iterations"] = 240
            assert (
                entry.source_case_id
                == ExperimentCase.from_problem(TopologyProblem.model_validate(payload)).case_id
            )
            assert entry.physical_fingerprint in historical


def test_exposure_source_counts_and_budget_insensitive_membership() -> None:
    ledger = build_b3_exposure_ledger()
    assert len(ledger.entries) == 1376
    assert sum(len(e.case_ids) for e in ledger.entries) == 1982
    assert Counter(source for entry in ledger.entries for source in entry.sources) == {
        "m0_v1": 160,
        "m0_v2_m1": 160,
        "m2_all": 756,
        "m3_final_design": 96,
        "b2_development_and_reserved": 958,
    }
    source_ids = {
        source: {
            case_id
            for entry in ledger.entries
            if source in entry.sources
            for case_id in entry.case_ids
        }
        for source in (
            "m0_v1",
            "m0_v2_m1",
            "m2_all",
            "m3_final_design",
            "b2_development_and_reserved",
        )
    }
    # Membership is per physical problem: each source sees all known budget aliases.
    assert source_ids["m0_v1"] == source_ids["m0_v2_m1"]
    assert len(source_ids["m0_v1"]) > 160
    original = build_m0_case_catalog().cases[0]
    payload = original.problem.model_dump(mode="json")
    payload["optimization"]["max_iterations"] = 720
    alias = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
    assert alias.case_id != original.case_id
    assert physical_fingerprint(alias) == physical_fingerprint(original)
    assert ledger.contains(alias)
    fit_case = build_b3_case_catalog().for_role("fit_validation")[0].case
    payload = fit_case.problem.model_dump(mode="json")
    payload["optimization"]["max_iterations"] = 720
    alias = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
    assert physical_fingerprint(alias) == physical_fingerprint(fit_case)
    assert not ledger.contains(alias)
    payload["optimization"]["filter_radius"] = 1.6
    changed = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
    assert physical_fingerprint(changed) != physical_fingerprint(fit_case)


def test_fingerprint_normalizes_support_and_load_representation() -> None:
    case = build_m0_case_catalog().cases[0]
    payload = case.problem.model_dump(mode="json")
    payload["supports"] = [
        {"axis": "x", "side": "min", "directions": ["z", "y"]},
        {"axis": "x", "side": "min", "directions": ["x", "z"]},
    ]
    payload["loads"][0]["direction"] = 1 if case.problem.loads[0].direction == "y" else 2
    equivalent = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
    assert equivalent.case_id == case.case_id
    assert physical_fingerprint(equivalent) == physical_fingerprint(case)


@pytest.mark.parametrize(
    "change",
    (
        "duplicate",
        "missing",
        "role",
        "membership",
        "source",
        "fingerprint",
        "case",
        "version",
        "extra",
    ),
)
def test_catalog_rejects_forged_or_incomplete_metadata(change: str) -> None:
    payload = build_b3_case_catalog().model_dump(mode="json")
    entries = payload["entries"]
    if change == "duplicate":
        entries.append(entries[0])
    elif change == "missing":
        entries.pop()
    elif change == "version":
        payload["catalog_version"] = "topolab.b3.catalog.v2"
    elif change == "extra":
        payload["unexpected"] = True
    else:
        entry = next(e for e in entries if e["role"] == "train")
        if change == "role":
            entry.update(role="final_id", source_case_id=None, training_sets=[])
        elif change == "membership":
            entry["training_sets"] = ["expanded"]
        elif change == "source":
            entry["source_case_id"] = "tlcase-v1-" + "0" * 64
        elif change == "fingerprint":
            entry["physical_fingerprint"] = "0" * 64
        elif change == "case":
            entry["case"]["problem"]["optimization"]["volume_fraction"] = 0.41
    with pytest.raises(ValueError):
        B3CaseCatalog.model_validate(payload)


def test_catalog_rejects_budget_variant_and_historical_role_reassignment() -> None:
    entry = build_b3_case_catalog().for_role("fit_validation")[0]
    payload = entry.model_dump(mode="json")
    problem = entry.case.problem.model_dump(mode="json")
    problem["optimization"]["max_iterations"] = 720
    payload["case"] = ExperimentCase.from_problem(
        TopologyProblem.model_validate(problem)
    ).model_dump()
    with pytest.raises(ValueError, match="360-update"):
        B3CatalogEntry.model_validate(payload)
    train = build_b3_case_catalog().for_role("train")[0]
    reassigned = train.model_copy(
        update={"role": "final_id", "source_case_id": None, "training_sets": ()}
    )
    catalog = build_b3_case_catalog().model_dump(mode="json")
    catalog["entries"] = [
        reassigned.model_dump(mode="json") if e["case"]["case_id"] == (train.case.case_id) else e
        for e in catalog["entries"]
    ]
    with pytest.raises(ValueError, match="frozen B3 hash"):
        B3CaseCatalog.model_validate(catalog)


@pytest.mark.parametrize("change", ("missing", "fingerprint", "case_id", "source", "duplicate"))
def test_ledger_rejects_stale_or_forged_identity(change: str) -> None:
    payload = build_b3_exposure_ledger().model_dump(mode="json")
    if change == "missing":
        payload["entries"].pop()
    elif change == "duplicate":
        payload["entries"].append(payload["entries"][0])
    elif change == "fingerprint":
        payload["entries"][0]["physical_fingerprint"] = "0" * 64
    elif change == "case_id":
        payload["entries"][0]["case_ids"] = ["tlcase-v1-" + "0" * 64]
    else:
        payload["entries"][0]["sources"] = ["m0_v1"]
    with pytest.raises(ValueError):
        B3ExposureLedger.model_validate(payload)


def test_catalog_revalidates_nested_instances_with_forged_fingerprints() -> None:
    catalog = build_b3_case_catalog()
    target = catalog.for_role("final_id")[0]
    forged = target.model_copy(update={"physical_fingerprint": "0" * 64})
    entries = tuple(forged if entry == target else entry for entry in catalog.entries)
    with pytest.raises(ValueError, match="physical_fingerprint"):
        B3CaseCatalog(entries=entries)


def test_cold_metadata_build_uses_no_solver_or_artifact_io() -> None:
    program = """
import sys
from pathlib import Path
import topolab.problem as problem
import topolab.experiment as experiment
from topolab.b3_catalog import build_b3_case_catalog, build_b3_exposure_ledger
def forbidden(*args, **kwargs):
    raise AssertionError('metadata attempted computation or artifact access')
problem.solve_problem = forbidden
problem.optimize_simp = forbidden
experiment.encode_case = forbidden
Path.open = forbidden
Path.write_bytes = forbidden
Path.mkdir = forbidden
assert len(build_b3_case_catalog().entries) == 752
assert len(build_b3_exposure_ledger().entries) == 1376
assert not any(name.startswith('b2_') for name in sys.modules)
"""
    root = Path(__file__).resolve().parents[1]
    program = f"import sys\nsys.path.insert(0, {str(root / 'src')!r})\n" + program
    result = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
