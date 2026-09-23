"""Safe production entrypoint for the frozen M2 dataset catalog."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from topolab.dataset_cli import (
    DatasetEntrypointError,
    RepositorySnapshot,
    inspect_repository,
    validate_external_output_root,
)
from topolab.m2_dataset import (
    M2_CASE_CATALOG_ID,
    M2DatasetManifest,
    build_m2_case_catalog,
)
from topolab.materialization import (
    MaterializationFailure,
    build_manifest_sha256,
    materialize_dataset,
)

M2_MATERIALIZATION_SUMMARY_VERSION = "topolab.m2.materialization-summary.v1"


def build_current_m2_manifest(
    cwd: Path,
) -> tuple[RepositorySnapshot, M2DatasetManifest]:
    """Build the frozen M2 manifest from the current clean checkout."""

    snapshot = inspect_repository(cwd)
    manifest = build_m2_case_catalog().build_manifest(
        source_revision=snapshot.source_revision,
        environment=snapshot.environment,
    )
    return snapshot, manifest


def main(argv: Sequence[str] | None = None) -> int:
    """Plan or explicitly execute production materialization for the M2 catalog."""

    parser = argparse.ArgumentParser(
        description="Plan the frozen M2 catalog, or materialize it explicitly.",
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
        snapshot, manifest = build_current_m2_manifest(Path.cwd())
        output_root = validate_external_output_root(
            snapshot.root,
            cast(Path, parsed.output_root),
        )
    except DatasetEntrypointError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    execute = cast(bool, parsed.execute)
    summary: dict[str, object] = {
        "catalog_id": M2_CASE_CATALOG_ID,
        "environment": manifest.environment.model_dump(mode="json"),
        "manifest_sha256": build_manifest_sha256(manifest),
        "mode": "execute" if execute else "plan",
        "source_revision": manifest.source_revision,
        "source_tree_clean": manifest.source_tree_clean,
        "split_counts": manifest.split_counts.model_dump(mode="json"),
        "summary_version": M2_MATERIALIZATION_SUMMARY_VERSION,
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


def _print_summary(summary: dict[str, object]) -> None:
    print(json.dumps(summary, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
