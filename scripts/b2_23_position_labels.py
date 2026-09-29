"""B2.23 fixed large-y position coverage and new-label feasibility audit."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from b2_5_prototype import atomic_write, canonical_bytes, sha256, source_snapshot
from b2_6_trajectory import _external_root, _small_case
from b2_7_global_load import _peak_rss
from b2_9_vector_load import _index
from b2_22_y_specialist import cohorts as b222_cohorts
from b2_workload_pilot import scaled_case

from topolab.b2_4_labels import B24Label, audit_label, generate_b24_label
from topolab.dataset import DatasetEnvironment
from topolab.experiment import ExperimentCase
from topolab.problem import TopologyProblem

PLAN_VERSION = "topolab.b2_23.position_labels.v1"
EXPECTED_PLAN_SHA256 = "d7ca55687e1f92fdd113991228f95e589242df8ba2ab112fe0c2153b36595a72"
B222_SCREEN_SHA256 = "62ffe463c863f5ff57b88687a5cc9aeb0abf5261087335f4e790e5f3b3f58632"
VOLUMES = (0.5585, 0.5785, 0.5985)
POSITIONS_SMALL = tuple((y, z) for z in (1, 2) for y in (1, 2, 3, 4, 5))
VALIDATION_VOLUME = 0.5785
LABEL_CAP = 3_600.0
MAX_RSS = 1_073_741_824


def load_position(case: ExperimentCase) -> tuple[int, int]:
    """Return the point-load (y,z) node in the case's own mesh coordinates."""

    nx, ny, _ = case.problem.mesh.element_counts
    load = case.problem.loads[0]
    node = load.node
    y_plus_z = (node - nx) // (nx + 1)
    y, z = y_plus_z % (ny + 1), y_plus_z // (ny + 1)
    if node != nx + (nx + 1) * (y + (ny + 1) * z):
        raise ValueError("B2.23 point load is not on the x-max face")
    return y, z


def _source_case(case: ExperimentCase) -> ExperimentCase:
    payload = case.problem.model_dump(mode="json")
    payload["optimization"]["max_iterations"] = 120
    return ExperimentCase.from_problem(TopologyProblem.model_validate(payload))


def _result_id(source: ExperimentCase, case: ExperimentCase) -> str:
    identity = {"version": PLAN_VERSION, "source_case_id": source.case_id,
                "case_id": case.case_id}
    return "tlcase-b223-v1-" + sha256(canonical_bytes(identity))


def cohorts() -> tuple[tuple[dict[str, Any], ...], tuple[ExperimentCase, ...],
                       tuple[ExperimentCase, ...]]:
    groups, prior_screen, prior_blocked = b222_cohorts()
    blocked = tuple(sorted({case.case_id: case for case in (
        *prior_blocked, *prior_screen, *groups["train"], *groups["validation"]
    )}.values(), key=lambda case: case.case_id))
    excluded_volumes = {case.problem.optimization.volume_fraction for case in blocked}
    excluded_volumes.update(index / 100 for index in range(20, 61, 5))
    excluded_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & excluded_volumes:
        raise ValueError("B2.23 label volume intersects prior or final designs")
    selected: list[tuple[dict[str, Any], ExperimentCase]] = []
    for volume in VOLUMES:
        for y, z in POSITIONS_SMALL:
            case = scaled_case(_small_case(volume, "y", y, z))
            source = _source_case(case)
            identity = {"case_id": case.case_id, "source_case_id": source.case_id,
                        "result_id": _result_id(source, case),
                        "split": "validation" if volume == VALIDATION_VOLUME else "train",
                        "scale": "large", "direction": "y", "volume": volume,
                        "load_position": list(load_position(case))}
            selected.append((identity, case))
    selected.sort(key=lambda pair: pair[1].case_id)
    identities = tuple(identity for identity, _ in selected)
    cases = tuple(case for _, case in selected)
    high_prior = [case for case in groups["train"]
                  if case.problem.mesh.element_counts == (24, 12, 6)
                  and case.problem.loads[0].direction == "y"
                  and case.problem.optimization.volume_fraction >= 0.55]
    positions = {load_position(case) for case in high_prior}
    new_train_positions = {tuple(identity["load_position"]) for identity in identities
                           if identity["split"] == "train"}
    splits = Counter(identity["split"] for identity in identities)
    if (len(blocked) != 760 or len(high_prior) != 4 or len(positions) != 4
            or len(cases) != 30 or len({case.case_id for case in (*blocked, *cases)}) != 790
            or splits != {"train": 20, "validation": 10}
            or len(new_train_positions) != 10 or len(positions | new_train_positions) != 13
            or (8, 2) not in new_train_positions
            or any(case.problem.mesh.element_counts != (24, 12, 6)
                   or case.problem.optimization.max_iterations != 240 for case in cases)):
        raise ValueError("B2.23 population, disjointness, or coverage differs")
    return identities, cases, blocked


def plan_payload(identities: tuple[dict[str, Any], ...],
                 blocked: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    groups, _, _ = b222_cohorts()
    prior = [case for case in groups["train"]
             if case.problem.mesh.element_counts == (24, 12, 6)
             and case.problem.loads[0].direction == "y"
             and case.problem.optimization.volume_fraction >= 0.55]
    identity = {
        "version": PLAN_VERSION,
        "intervention": "large_y_position_grid_terminal_label_feasibility_no_fit",
        "b222_screen_index_sha256": B222_SCREEN_SHA256,
        "blocked_case_ids": [case.case_id for case in blocked],
        "prior_high_volume_large_y_train_case_ids": [case.case_id for case in prior],
        "prior_high_volume_large_y_positions": [list(load_position(case)) for case in prior],
        "new_cases": list(identities),
        "volumes": list(VOLUMES),
        "validation_volume": VALIDATION_VOLUME,
        "positions_small": [list(position) for position in POSITIONS_SMALL],
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 240,
        "label_artifact_version": "topolab.b2_4.artifact.v1",
        "label_cap_seconds": LABEL_CAP,
        "max_rss_bytes": MAX_RSS,
        "gate_required_successes": 30,
        "gate_required_train": 20,
        "gate_required_validation": 10,
        "gate_independent_quality": True,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _environment(repository: Path) -> DatasetEnvironment:
    return DatasetEnvironment(
        python_version=platform.python_version(), numpy_version=np.__version__,
        scipy_version=importlib.metadata.version("scipy"),
        lockfile_sha256=sha256((repository / "uv.lock").read_bytes()),
    )


def _artifact_path(root: Path, case_id: str, digest: str) -> Path:
    return root / "labels" / case_id / f"{digest}.json"


def _read_label(root: Path, row: dict[str, Any], identity: dict[str, Any],
                context: dict[str, Any], environment: DatasetEnvironment) -> B24Label:
    if row["identity"] != identity or row["status"] != "succeeded":
        raise ValueError("B2.23 label identity or status differs")
    path = _artifact_path(root, identity["case_id"], row["artifact_sha256"])
    contents = path.read_bytes()
    if sha256(contents) != row["artifact_sha256"] or len(contents) != row["artifact_bytes"]:
        raise ValueError("B2.23 label checksum or size differs")
    label = B24Label.model_validate_json(contents)
    if (label.source_revision != context["source_revision"]
            or label.environment != environment
            or label.case.case_id != identity["case_id"]
            or label.source_case_id != identity["source_case_id"]
            or label.result_id != identity["result_id"]
            or label.split != identity["split"] or label.scale != "large"
            or label.direction != "y" or label.volume != identity["volume"]
            or load_position(label.case) != tuple(identity["load_position"])):
        raise ValueError("B2.23 persisted label provenance differs")
    audit_label(label)
    return label


def summary(index: dict[str, Any]) -> dict[str, Any]:
    successes = Counter(row["identity"]["split"] for row in index["rows"]
                        if row["status"] == "succeeded")
    failures = [row["identity"]["case_id"] for row in index["rows"]
                if row["status"] == "failed"]
    gate = (len(index["rows"]) == 30 and successes == {"train": 20, "validation": 10}
            and not failures and index["elapsed_seconds"] <= LABEL_CAP
            and index["peak_rss_bytes"] < MAX_RSS)
    return {"cases": len(index["rows"]), "successes": dict(successes),
            "failure_case_ids": failures, "gate_passed": gate,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"]}


def run_labels(root: Path, cases: tuple[ExperimentCase, ...],
               identities: tuple[dict[str, Any], ...], context: dict[str, Any],
               environment: DatasetEnvironment) -> dict[str, Any]:
    index = _index(root, "label_index.json", context, 30)
    for row, identity in zip(index["rows"], identities, strict=False):
        if row["identity"] != identity:
            raise ValueError("B2.23 persisted label order differs")
        if row["status"] == "succeeded":
            _read_label(root, row, identity, context, environment)
        elif row["status"] != "failed" or row["failure_code"] != "nonconvergence":
            raise ValueError("B2.23 persisted failure differs")
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 30):
        if prior + perf_counter() - started > LABEL_CAP:
            raise ValueError("B2.23 label time cap exhausted")
        case, identity = cases[position], identities[position]
        case_started = perf_counter()
        try:
            label = generate_b24_label(
                case=case, source_case_id=identity["source_case_id"],
                result_id=identity["result_id"], split=identity["split"],
                scale="large", direction="y", volume=identity["volume"],
                source_revision=context["source_revision"], environment=environment,
            )
        except ValueError as error:
            if "did not converge" not in str(error):
                raise
            row = {"identity": identity, "status": "failed",
                   "failure_code": "nonconvergence"}
        else:
            contents = canonical_bytes(label.model_dump(mode="json"))
            digest = sha256(contents)
            atomic_write(_artifact_path(root, case.case_id, digest), contents)
            row = {"identity": identity, "status": "succeeded",
                   "artifact_sha256": digest, "artifact_bytes": len(contents),
                   "iterations": label.iterations, "compliance": label.compliance,
                   "physical_volume_error": abs(label.physical_volume_fraction
                                                - identity["volume"])}
            _read_label(root, row, identity, context, environment)
        row["case_seconds"] = perf_counter() - case_started
        index["rows"].append(row)
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "label_index.json", canonical_bytes(index))
        print(f"B2.23 labels {position + 1}/30", file=sys.stderr, flush=True)
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b222-root", type=Path, default=Path("/tmp/topolab-b222"))
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--labels", action="store_true")
    stage.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    identities, cases, blocked = cohorts()
    plan = plan_payload(identities, blocked)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.23 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b222_root = _external_root(repository, args.b222_root)
    if root == b222_root:
        raise ValueError("B2.23 labels and B2.22 evidence roots must differ")
    if sha256((b222_root / "screen_index.json").read_bytes()) != B222_SCREEN_SHA256:
        raise ValueError("B2.22 exposure evidence differs")
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime, "b222_screen_index_sha256": B222_SCREEN_SHA256}
    if not args.labels and not args.audit:
        print(json.dumps({"plan_sha256": plan["plan_sha256"],
                          "source_revision": revision, "blocked_cases": len(blocked),
                          "new_cases": len(cases), "train": 20, "validation": 10},
                         sort_keys=True))
        return 0
    environment = _environment(repository)
    if args.labels:
        index = run_labels(root, cases, identities, context, environment)
    else:
        index = _index(root, "label_index.json", context, 30)
        for row, identity in zip(index["rows"], identities, strict=False):
            if row["identity"] != identity:
                raise ValueError("B2.23 audit label order differs")
            if row["status"] == "succeeded":
                _read_label(root, row, identity, context, environment)
            elif row["status"] != "failed" or row["failure_code"] != "nonconvergence":
                raise ValueError("B2.23 audit failure differs")
    result = {**summary(index), "index_sha256": sha256(
        (root / "label_index.json").read_bytes())}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
