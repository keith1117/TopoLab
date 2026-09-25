"""Materialize and audit the fixed 522-case B2.4 development labels."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import subprocess
import sys
from collections import Counter
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import perf_counter
from typing import Any

from b2_2_data_feasibility import EXPECTED_PLAN_SHA256 as B22_PLAN_SHA256
from b2_2_data_feasibility import select_plan
from b2_3_budget_sentinel import LABEL_VERSION, MAX_ITERATIONS, BudgetCase, result_id

from topolab.b2_4_labels import B24Label, audit_label, generate_b24_label
from topolab.dataset import DatasetEnvironment
from topolab.experiment import ExperimentCase
from topolab.problem import TopologyProblem
from topolab.simp import PHYSICAL_PLATEAU_SOLVER_VERSION

PLAN_VERSION = "topolab.b2_4.dataset.v1"
INDEX_VERSION = "topolab.b2_4.index.v1"
MAX_SECONDS = 7_200.0
MAX_RSS_BYTES = 1_073_741_824
EXPECTED_PLAN_SHA256 = "015ab799be88a5fef763720b2e1c58281dc17aea67c61435bcb87d254f64169c"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha256(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def select_cases() -> tuple[BudgetCase, ...]:
    """Preserve all B2.2 development cases while versioning the B2.3 budget."""

    sources = select_plan()
    cases: list[BudgetCase] = []
    for source in sources:
        payload = source.case.problem.model_dump(mode="json")
        if payload["optimization"]["max_iterations"] != 120:
            raise ValueError("B2.2 source iteration budget changed")
        payload["optimization"]["max_iterations"] = MAX_ITERATIONS
        case = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
        if case.case_id == source.case.case_id:
            raise ValueError("new budget did not change physical case identity")
        cases.append(BudgetCase(source=source, case=case))
    if len(cases) != 522 or len({item.case.case_id for item in cases}) != 522:
        raise ValueError("B2.4 plan must have 522 distinct cases")
    return tuple(cases)


def row_identity(item: BudgetCase) -> dict[str, Any]:
    return {
        "source_case_id": item.source.case.case_id,
        "new_case_id": item.case.case_id,
        "result_id": result_id(item.source.case.case_id, item.case.case_id),
        "split": item.source.split,
        "scale": item.source.scale,
        "direction": item.source.direction,
        "volume": item.source.volume,
    }


def plan_payload(cases: tuple[BudgetCase, ...]) -> dict[str, Any]:
    identity = {
        "plan_version": PLAN_VERSION,
        "label_version": LABEL_VERSION,
        "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION,
        "max_iterations": MAX_ITERATIONS,
        "b2_2_plan_sha256": B22_PLAN_SHA256,
        "cases": [row_identity(item) for item in cases],
    }
    return {**identity, "plan_sha256": _sha256(_canonical_bytes(identity))}


def _repository_snapshot() -> tuple[Path, str, DatasetEnvironment]:
    repository = Path(
        subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    ).resolve()
    for command in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"]):
        if subprocess.run(command, cwd=repository, check=False).returncode != 0:
            raise ValueError("B2.4 execution requires a clean tracked revision")
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    environment = DatasetEnvironment(
        python_version=platform.python_version(),
        numpy_version=importlib.metadata.version("numpy"),
        scipy_version=importlib.metadata.version("scipy"),
        lockfile_sha256=_sha256((repository / "uv.lock").read_bytes()),
    )
    return repository, revision, environment


def _external_root(repository: Path, requested: Path) -> Path:
    root = requested.resolve()
    if root == repository or root.is_relative_to(repository):
        raise ValueError("B2.4 output root must be outside the repository")
    return root


def _atomic_write(path: Path, contents: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=".b24-", suffix=".tmp", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(contents)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _index_path(root: Path) -> Path:
    return root / "b2_4_index.json"


def _artifact_path(root: Path, case_id: str, digest: str) -> Path:
    return root / "labels" / case_id / f"{digest}.json"


def _read_index(
    root: Path, plan: dict[str, Any], revision: str, environment: DatasetEnvironment
) -> dict[str, Any]:
    path = _index_path(root)
    if path.exists():
        index: dict[str, Any] = json.loads(path.read_bytes())
        if (
            index.get("index_version") != INDEX_VERSION
            or index.get("plan_sha256") != plan["plan_sha256"]
            or index.get("source_revision") != revision
            or index.get("environment") != environment.model_dump(mode="json")
        ):
            raise ValueError("existing B2.4 index has a different frozen identity")
        rows = index.get("rows")
        if not isinstance(rows, list) or len(rows) > len(plan["cases"]):
            raise ValueError("B2.4 index row population is invalid")
        for position, row in enumerate(rows):
            if row.get("identity") != plan["cases"][position]:
                raise ValueError("B2.4 index row order or identity changed")
            if row.get("status") == "succeeded":
                _read_artifact(root, row, revision, environment, solve=False)
            elif row.get("status") != "failed":
                raise ValueError("B2.4 index has unknown row status")
        return index
    return {
        "index_version": INDEX_VERSION,
        "plan_sha256": plan["plan_sha256"],
        "source_revision": revision,
        "source_tree_clean": True,
        "environment": environment.model_dump(mode="json"),
        "rows": [],
        "elapsed_seconds": 0.0,
        "audit_seconds": 0.0,
        "peak_rss_bytes": 0,
    }


def _read_artifact(
    root: Path,
    row: dict[str, Any],
    revision: str,
    environment: DatasetEnvironment,
    *,
    solve: bool,
) -> B24Label:
    identity = row["identity"]
    digest = row["artifact_sha256"]
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("artifact checksum is invalid")
    contents = _artifact_path(root, identity["new_case_id"], digest).read_bytes()
    if _sha256(contents) != digest:
        raise ValueError("B2.4 artifact checksum mismatch")
    label = B24Label.model_validate_json(contents)
    if (
        label.source_revision != revision
        or label.environment != environment
        or label.source_case_id != identity["source_case_id"]
        or label.case.case_id != identity["new_case_id"]
        or label.result_id != identity["result_id"]
        or label.split != identity["split"]
        or label.scale != identity["scale"]
        or label.direction != identity["direction"]
        or label.volume != identity["volume"]
    ):
        raise ValueError("B2.4 artifact differs from frozen case identity")
    if solve:
        audit_label(label)
    return label


def _write_artifact(root: Path, label: B24Label) -> tuple[str, int]:
    contents = _canonical_bytes(label.model_dump(mode="json"))
    digest = _sha256(contents)
    path = _artifact_path(root, label.case.case_id, digest)
    if path.exists():
        if path.read_bytes() != contents:
            raise ValueError("existing B2.4 artifact differs from generated label")
    else:
        _atomic_write(path, contents)
    return digest, len(contents)


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def _audit(
    root: Path,
    plan: dict[str, Any],
    index: dict[str, Any],
    environment: DatasetEnvironment,
    *,
    preflight_seconds: float = 0.0,
) -> dict[str, Any]:
    started = perf_counter()
    revision = index["source_revision"]
    rows = index["rows"]
    succeeded = 0
    failed = 0
    artifact_bytes = 0
    iterations: list[int] = []
    stops: Counter[str] = Counter()
    counts: Counter[str] = Counter()
    for position, row in enumerate(rows):
        if row["identity"] != plan["cases"][position]:
            raise ValueError("B2.4 audit identity order changed")
        identity = row["identity"]
        if row["status"] == "succeeded":
            label = _read_artifact(root, row, revision, environment, solve=True)
            succeeded += 1
            artifact_bytes += row["artifact_bytes"]
            iterations.append(label.iterations)
            stops[label.stop_reason] += 1
            counts[f"{label.scale}_{label.split}"] += 1
            counts[f"{label.direction}_{label.volume:.2f}"] += 1
        else:
            failed += 1
            counts[f"failed_{identity['scale']}_{identity['split']}"] += 1
    audit_seconds = preflight_seconds + perf_counter() - started
    index["audit_seconds"] = float(index.get("audit_seconds", 0.0)) + audit_seconds
    peak_rss = max(int(index["peak_rss_bytes"]), _peak_rss_bytes())
    index["peak_rss_bytes"] = peak_rss
    _atomic_write(_index_path(root), _canonical_bytes(index))
    total_seconds = float(index["elapsed_seconds"]) + float(index["audit_seconds"])
    expected_counts = {
        "small_train": 432,
        "small_validation": 36,
        "large_train": 36,
        "large_validation": 18,
    }
    gate = (
        len(rows) == 522
        and succeeded == 522
        and failed == 0
        and all(counts[key] == value for key, value in expected_counts.items())
        and all(counts[f"{direction}_{volume / 100:.2f}"] == 29
                for direction in ("y", "z")
                for volume in range(20, 61, 5))
        and total_seconds <= MAX_SECONDS
        and peak_rss <= MAX_RSS_BYTES
    )
    return {
        "summary_version": "topolab.b2_4.summary.v1",
        "source_revision": revision,
        "environment": environment.model_dump(mode="json"),
        "plan_sha256": plan["plan_sha256"],
        "index_sha256": _sha256(_index_path(root).read_bytes()),
        "labels_succeeded": succeeded,
        "labels_failed": failed,
        "rows": len(rows),
        "counts": dict(sorted(counts.items())),
        "stop_counts": dict(sorted(stops.items())),
        "max_iterations": max(iterations, default=0),
        "artifact_bytes": artifact_bytes,
        "generation_seconds": index["elapsed_seconds"],
        "audit_seconds": index["audit_seconds"],
        "total_seconds": total_seconds,
        "peak_rss_bytes": peak_rss,
        "data_gate_passed": gate,
    }


def _execute(
    root: Path,
    plan: dict[str, Any],
    cases: tuple[BudgetCase, ...],
    revision: str,
    environment: DatasetEnvironment,
) -> dict[str, Any]:
    started = perf_counter()
    index = _read_index(root, plan, revision, environment)
    base_seconds = float(index["elapsed_seconds"])
    for position in range(len(index["rows"]), len(cases)):
        item = cases[position]
        identity = plan["cases"][position]
        case_started = perf_counter()
        if (
            base_seconds + float(index.get("audit_seconds", 0.0))
            + perf_counter() - started > MAX_SECONDS
        ):
            row: dict[str, Any] = {
                "identity": identity,
                "status": "failed",
                "failure_code": "budget_exhausted",
                "seconds": 0.0,
            }
        else:
            try:
                label = generate_b24_label(
                    case=item.case,
                    source_case_id=item.source.case.case_id,
                    result_id=identity["result_id"],
                    split=item.source.split,
                    scale=item.source.scale,
                    direction=item.source.direction,
                    volume=item.source.volume,
                    source_revision=revision,
                    environment=environment,
                )
                digest, size = _write_artifact(root, label)
                row = {
                    "identity": identity,
                    "status": "succeeded",
                    "artifact_sha256": digest,
                    "artifact_bytes": size,
                    "iterations": label.iterations,
                    "compliance": label.compliance,
                    "physical_volume_error": abs(
                        label.physical_volume_fraction - label.volume
                    ),
                    "stop_reason": label.stop_reason,
                    "seconds": perf_counter() - case_started,
                }
            except (ValueError, RuntimeError, ArithmeticError) as error:
                row = {
                    "identity": identity,
                    "status": "failed",
                    "failure_code": type(error).__name__,
                    "failure_reason": str(error)[:200],
                    "seconds": perf_counter() - case_started,
                }
        index["rows"].append(row)
        index["elapsed_seconds"] = base_seconds + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss_bytes())
        _atomic_write(_index_path(root), _canonical_bytes(index))
        if (position + 1) % 25 == 0 or row["status"] == "failed":
            print(
                f"B2.4 {position + 1}/522 {row['status']} {identity['new_case_id']}",
                file=sys.stderr,
                flush=True,
            )
    index["elapsed_seconds"] = base_seconds + perf_counter() - started
    _atomic_write(_index_path(root), _canonical_bytes(index))
    return _audit(root, plan, index, environment)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if args.execute and args.audit:
        parser.error("select either --execute or --audit")
    cases = select_cases()
    plan = plan_payload(cases)
    if EXPECTED_PLAN_SHA256 and plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.4 plan differs from frozen identity")
    if not args.execute and not args.audit:
        print(json.dumps(plan, sort_keys=True))
        return 0
    if not EXPECTED_PLAN_SHA256:
        parser.error("execution requires a frozen plan checksum")
    if args.output_root is None:
        parser.error("execution and audit require --output-root")
    repository, revision, environment = _repository_snapshot()
    root = _external_root(repository, args.output_root)
    if args.execute:
        summary = _execute(root, plan, cases, revision, environment)
    else:
        audit_started = perf_counter()
        index = _read_index(root, plan, revision, environment)
        summary = _audit(
            root, plan, index, environment,
            preflight_seconds=perf_counter() - audit_started,
        )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["data_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
