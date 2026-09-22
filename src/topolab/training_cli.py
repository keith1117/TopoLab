"""Safe production entrypoint for the frozen M1 fitting run."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from pydantic import ValidationError

from topolab.catalog import M0_CASE_CATALOG_ID, build_m0_case_catalog
from topolab.dataset_cli import (
    DatasetEntrypointError,
    inspect_repository,
    validate_external_output_root,
)
from topolab.materialization import (
    DatasetMaterializationIndex,
    MaterializationFailure,
    canonical_materialization_index_bytes,
)
from topolab.training import (
    M1_DATA_MANIFEST_SHA256,
    M1_SEEDS,
    M1DatasetError,
    M1TrainingError,
)
from topolab.training_artifacts import (
    M1ArtifactError,
    M1RuntimeEnvironment,
    M1SelectionReference,
    capture_m1_runtime,
    read_m1_selection,
    train_all_m1_seeds,
)

M1_TRAINING_SUMMARY_VERSION = "topolab.m1.training-summary.v1"


class M1TrainingEntrypointError(RuntimeError):
    """Raised when the frozen production fitting run cannot start safely."""


def load_frozen_m1_materialization(data_root: Path) -> DatasetMaterializationIndex:
    """Read the exact frozen M0 index without opening test or OOD labels."""

    target = (
        data_root
        / "materializations"
        / f"{M1_DATA_MANIFEST_SHA256}.json"
    )
    try:
        contents = target.read_bytes()
    except FileNotFoundError as error:
        raise M1TrainingEntrypointError(
            "the frozen M1 materialization index is missing"
        ) from error
    except OSError as error:
        raise M1TrainingEntrypointError(
            "could not read the frozen M1 materialization index"
        ) from error

    try:
        index = DatasetMaterializationIndex.model_validate_json(contents)
    except ValidationError as error:
        raise M1TrainingEntrypointError(
            "the frozen M1 materialization index is invalid"
        ) from error
    if canonical_materialization_index_bytes(index) != contents:
        raise M1TrainingEntrypointError(
            "the frozen M1 materialization index is not canonical JSON"
        )
    if index.manifest_sha256 != M1_DATA_MANIFEST_SHA256:
        raise M1TrainingEntrypointError(
            "the materialization does not match the frozen M1 manifest"
        )
    if tuple(sample.case for sample in index.manifest.samples) != (
        build_m0_case_catalog().cases
    ):
        raise M1TrainingEntrypointError(
            "the materialization does not match the frozen M0 v2 catalog"
        )
    if index.state != "complete" or any(
        isinstance(entry, MaterializationFailure) for entry in index.entries
    ):
        raise M1TrainingEntrypointError(
            "M1 training requires a complete zero-failure materialization"
        )
    return index


def audit_m1_selections(
    artifact_root: Path,
    references: tuple[M1SelectionReference, ...],
    *,
    materialization: DatasetMaterializationIndex,
    training_source_revision: str,
    runtime: M1RuntimeEnvironment,
) -> tuple[dict[str, object], ...]:
    """Reopen and provenance-check the exact five production selections."""

    if tuple(reference.seed for reference in references) != M1_SEEDS:
        raise M1TrainingEntrypointError(
            "the production run must contain every frozen M1 seed in order"
        )
    expected_training_ids = tuple(
        sample.case.case_id
        for sample in materialization.manifest.samples
        if sample.split == "train"
    )
    expected_validation_ids = tuple(
        sample.case.case_id
        for sample in materialization.manifest.samples
        if sample.split == "validation"
    )
    summaries: list[dict[str, object]] = []
    for reference in references:
        selection = read_m1_selection(artifact_root, reference)
        if (
            selection.manifest_sha256 != materialization.manifest_sha256
            or selection.label_source_revision
            != materialization.manifest.source_revision
            or selection.training_source_revision != training_source_revision
            or selection.runtime != runtime
            or selection.training_case_ids != expected_training_ids
            or selection.validation_case_ids != expected_validation_ids
        ):
            raise M1TrainingEntrypointError(
                "a production selection does not match the fitting context"
            )
        summaries.append(
            {
                "checkpoint_relative_path": selection.checkpoint.relative_path,
                "checkpoint_sha256": selection.checkpoint.sha256,
                "epochs_completed": len(selection.history),
                "seed": selection.seed,
                "selected_epoch": selection.selected_epoch,
                "selected_validation_mse": selection.selected_validation_mse,
                "selection_relative_path": reference.relative_path,
                "selection_sha256": reference.sha256,
                "stopped_early": selection.stopped_early,
                "training_duration_seconds": selection.training_duration_seconds,
            }
        )
    return tuple(summaries)


def main(argv: Sequence[str] | None = None) -> int:
    """Plan or explicitly execute all five frozen M1 fitting seeds."""

    parser = argparse.ArgumentParser(
        description="Plan the frozen M1 fitting run, or execute all five seeds.",
    )
    parser.add_argument(
        "--data-root",
        required=True,
        type=Path,
        help="external root containing the frozen M0 v2 materialization",
    )
    parser.add_argument(
        "--artifact-root",
        required=True,
        type=Path,
        help="external root for M1 checkpoints and selection records",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="fit all five seeds; omission is a read-only plan",
    )
    parsed = parser.parse_args(argv)

    try:
        snapshot = inspect_repository(Path.cwd())
        data_root = validate_external_output_root(
            snapshot.root,
            cast(Path, parsed.data_root),
        )
        artifact_root = validate_external_output_root(
            snapshot.root,
            cast(Path, parsed.artifact_root),
        )
        materialization = load_frozen_m1_materialization(data_root)
        runtime = capture_m1_runtime(snapshot.root / "uv.lock")
    except (DatasetEntrypointError, M1ArtifactError, M1TrainingEntrypointError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    execute = cast(bool, parsed.execute)
    manifest = materialization.manifest
    summary: dict[str, object] = {
        "catalog_id": M0_CASE_CATALOG_ID,
        "data_manifest_sha256": materialization.manifest_sha256,
        "label_source_revision": manifest.source_revision,
        "mode": "execute" if execute else "plan",
        "runtime": runtime.model_dump(mode="json"),
        "seeds": M1_SEEDS,
        "source_tree_clean": True,
        "summary_version": M1_TRAINING_SUMMARY_VERSION,
        "training_cases": manifest.split_counts.train,
        "training_source_revision": snapshot.source_revision,
        "validation_cases": manifest.split_counts.validation,
    }
    if not execute:
        summary["state"] = "planned"
        _print_summary(summary)
        return 0

    try:
        references = train_all_m1_seeds(
            data_root,
            artifact_root,
            materialization,
            training_source_revision=snapshot.source_revision,
            runtime=runtime,
        )
        summary["selections"] = audit_m1_selections(
            artifact_root,
            references,
            materialization=materialization,
            training_source_revision=snapshot.source_revision,
            runtime=runtime,
        )
    except (
        M1ArtifactError,
        M1DatasetError,
        M1TrainingEntrypointError,
        M1TrainingError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    summary["state"] = "complete"
    _print_summary(summary)
    return 0


def _print_summary(summary: dict[str, object]) -> None:
    print(json.dumps(summary, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
