"""Safe production entrypoint for the frozen M0 dataset catalog."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from topolab.catalog import M0_CASE_CATALOG_ID, build_m0_case_catalog
from topolab.dataset import DatasetEnvironment, DatasetManifest
from topolab.materialization import (
    MaterializationFailure,
    build_manifest_sha256,
    materialize_dataset,
)

_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
MATERIALIZATION_SUMMARY_VERSION = "topolab.m0.materialization-summary.v1"


class DatasetEntrypointError(RuntimeError):
    """Raised when production materialization cannot start safely."""


@dataclass(frozen=True, slots=True)
class RepositorySnapshot:
    """Clean source revision and non-sensitive locked runtime metadata."""

    root: Path
    source_revision: str
    environment: DatasetEnvironment


def inspect_repository(cwd: Path) -> RepositorySnapshot:
    """Capture the clean Git revision and locked environment for one checkout."""

    root_text = _git_output(cwd, "rev-parse", "--show-toplevel")
    root = Path(root_text).resolve()
    revision = _git_output(root, "rev-parse", "--verify", "HEAD")
    if _REVISION_PATTERN.fullmatch(revision) is None:
        raise DatasetEntrypointError("Git HEAD is not a 40-character commit revision")

    status = _git_output(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise DatasetEntrypointError("the source worktree must be clean")

    lockfile = root / "uv.lock"
    try:
        lockfile_sha256 = hashlib.sha256(lockfile.read_bytes()).hexdigest()
    except OSError as error:
        raise DatasetEntrypointError("could not read the repository uv.lock") from error

    environment = DatasetEnvironment(
        python_version=platform.python_version(),
        numpy_version=importlib.metadata.version("numpy"),
        scipy_version=importlib.metadata.version("scipy"),
        lockfile_sha256=lockfile_sha256,
    )
    return RepositorySnapshot(
        root=root,
        source_revision=revision,
        environment=environment,
    )


def build_current_m0_manifest(cwd: Path) -> tuple[RepositorySnapshot, DatasetManifest]:
    """Build the frozen M0 manifest from the current clean checkout."""

    snapshot = inspect_repository(cwd)
    manifest = build_m0_case_catalog().build_manifest(
        source_revision=snapshot.source_revision,
        environment=snapshot.environment,
    )
    return snapshot, manifest


def validate_external_output_root(repository_root: Path, output_root: Path) -> Path:
    """Resolve an output root and reject every location inside the repository."""

    repository = repository_root.resolve()
    output = output_root.resolve()
    if output == repository or output.is_relative_to(repository):
        raise DatasetEntrypointError("output root must be outside the source repository")
    return output


def main(argv: Sequence[str] | None = None) -> int:
    """Plan or explicitly execute production materialization for the M0 catalog."""

    parser = argparse.ArgumentParser(
        description="Plan the frozen M0 catalog, or materialize it explicitly.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="external root for generated labels and the materialization checkpoint",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="run the solver; omission is a read-only plan",
    )
    parsed = parser.parse_args(argv)

    try:
        snapshot, manifest = build_current_m0_manifest(Path.cwd())
        output_root = validate_external_output_root(
            snapshot.root,
            cast(Path, parsed.output_root),
        )
    except DatasetEntrypointError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    execute = cast(bool, parsed.execute)
    summary: dict[str, object] = {
        "catalog_id": M0_CASE_CATALOG_ID,
        "environment": manifest.environment.model_dump(mode="json"),
        "manifest_sha256": build_manifest_sha256(manifest),
        "mode": "execute" if execute else "plan",
        "source_revision": manifest.source_revision,
        "source_tree_clean": manifest.source_tree_clean,
        "split_counts": manifest.split_counts.model_dump(mode="json"),
        "summary_version": MATERIALIZATION_SUMMARY_VERSION,
        "total_cases": len(manifest.samples),
    }
    if not execute:
        summary["state"] = "planned"
        _print_summary(summary)
        return 0

    index = materialize_dataset(output_root, manifest)
    failed = sum(isinstance(entry, MaterializationFailure) for entry in index.entries)
    summary.update(
        {
            "failed": failed,
            "state": index.state,
            "succeeded": len(index.entries) - failed,
        }
    )
    _print_summary(summary)
    return 1 if failed else 0


def _git_output(cwd: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise DatasetEntrypointError("could not inspect the Git repository") from error
    if completed.returncode != 0:
        raise DatasetEntrypointError("could not inspect the Git repository")
    return completed.stdout.strip()


def _print_summary(summary: dict[str, object]) -> None:
    print(json.dumps(summary, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
