"""Safe production entrypoint for the frozen M1 held-out experiment."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from topolab.baselines import BaselineEvaluationError
from topolab.catalog import M0_CASE_CATALOG_ID
from topolab.dataset_cli import (
    DatasetEntrypointError,
    inspect_repository,
    validate_external_output_root,
)
from topolab.learned_evaluation import (
    M1EvaluationError,
    M1LearnedCandidate,
    load_m1_candidate,
)
from topolab.m1_experiment import (
    M1EvaluationContext,
    M1ExperimentError,
    build_m1_evaluation_id,
    compute_m1_experiment_statistics,
    run_m1_experiment,
)
from topolab.materialization import DatasetMaterializationIndex
from topolab.training import M1_DATA_MANIFEST_SHA256, M1_SEEDS
from topolab.training_artifacts import (
    M1ArtifactError,
    M1CheckpointReference,
    M1SelectionReference,
    capture_m1_runtime,
    read_m1_selection,
)
from topolab.training_cli import (
    M1TrainingEntrypointError,
    load_frozen_m1_materialization,
)

M1_EVALUATION_SUMMARY_VERSION = "topolab.m1.evaluation-summary.v1"
M1_PRODUCTION_SELECTION_SHA256 = (
    (17, "09b38b66bf10b05f572d6238db628a626b7bdd20be8858b90be8e48ec3577d0e"),
    (29, "df41955903a0e6ef8867f54197ac564f90f3608eb51ad47fd035045f2ba341f0"),
    (43, "30504204cef125ae8beae6d973d69f6bd62b530cbd83da63c4d07241597f68d8"),
    (71, "a011c03fdf74ed8287169543cc5bfa0cf16092eaaba39d84afecc23fb488fc76"),
    (113, "b100af75f5d706981b7fd640467aad97a8420e2d4f5a349e58d77416b2015a39"),
)


class M1EvaluationEntrypointError(RuntimeError):
    """Raised when the frozen production evaluation cannot start safely."""


def production_selection_references(
    artifact_root: Path,
) -> tuple[
    M1SelectionReference,
    M1SelectionReference,
    M1SelectionReference,
    M1SelectionReference,
    M1SelectionReference,
]:
    """Resolve the exact five production selection references from external storage."""

    references: list[M1SelectionReference] = []
    for seed, digest in M1_PRODUCTION_SELECTION_SHA256:
        relative_path = (
            f"m1/selections/{M1_DATA_MANIFEST_SHA256}/{seed}/{digest}.json"
        )
        target = artifact_root / relative_path
        try:
            byte_size = target.stat().st_size
        except FileNotFoundError as error:
            raise M1EvaluationEntrypointError(
                f"production selection for seed {seed} is missing"
            ) from error
        except OSError as error:
            raise M1EvaluationEntrypointError(
                f"could not inspect production selection for seed {seed}"
            ) from error
        references.append(
            M1SelectionReference(
                manifest_sha256=M1_DATA_MANIFEST_SHA256,
                seed=seed,
                sha256=digest,
                byte_size=byte_size,
                relative_path=relative_path,
            )
        )
    return cast(
        tuple[
            M1SelectionReference,
            M1SelectionReference,
            M1SelectionReference,
            M1SelectionReference,
            M1SelectionReference,
        ],
        tuple(references),
    )


def audit_evaluation_selections(
    artifact_root: Path,
    references: tuple[
        M1SelectionReference,
        M1SelectionReference,
        M1SelectionReference,
        M1SelectionReference,
        M1SelectionReference,
    ],
    *,
    materialization: DatasetMaterializationIndex,
) -> tuple[
    tuple[dict[str, object], ...],
    tuple[
        M1CheckpointReference,
        M1CheckpointReference,
        M1CheckpointReference,
        M1CheckpointReference,
        M1CheckpointReference,
    ],
]:
    """Verify all five selections against the frozen fitting partitions."""

    if tuple(reference.seed for reference in references) != M1_SEEDS:
        raise M1EvaluationEntrypointError(
            "evaluation requires every frozen M1 seed in order"
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
    training_context: tuple[str, object] | None = None
    summaries: list[dict[str, object]] = []
    checkpoints: list[M1CheckpointReference] = []
    for reference in references:
        selection = read_m1_selection(artifact_root, reference)
        if (
            selection.manifest_sha256 != materialization.manifest_sha256
            or selection.label_source_revision
            != materialization.manifest.source_revision
            or selection.training_case_ids != expected_training_ids
            or selection.validation_case_ids != expected_validation_ids
        ):
            raise M1EvaluationEntrypointError(
                "a production selection does not match the frozen fitting data"
            )
        current_training_context = (
            selection.training_source_revision,
            selection.runtime,
        )
        if training_context is None:
            training_context = current_training_context
        elif current_training_context != training_context:
            raise M1EvaluationEntrypointError(
                "production selections do not share one fitting context"
            )
        summaries.append(
            {
                "checkpoint_sha256": selection.checkpoint.sha256,
                "seed": selection.seed,
                "selected_epoch": selection.selected_epoch,
                "selection_sha256": reference.sha256,
                "training_source_revision": selection.training_source_revision,
            }
        )
        checkpoints.append(selection.checkpoint)
    return tuple(summaries), cast(
        tuple[
            M1CheckpointReference,
            M1CheckpointReference,
            M1CheckpointReference,
            M1CheckpointReference,
            M1CheckpointReference,
        ],
        tuple(checkpoints),
    )


def load_evaluation_candidates(
    artifact_root: Path,
    references: tuple[
        M1SelectionReference,
        M1SelectionReference,
        M1SelectionReference,
        M1SelectionReference,
        M1SelectionReference,
    ],
) -> tuple[
    M1LearnedCandidate,
    M1LearnedCandidate,
    M1LearnedCandidate,
    M1LearnedCandidate,
    M1LearnedCandidate,
]:
    """Load all verified candidates in the frozen seed order."""

    return cast(
        tuple[
            M1LearnedCandidate,
            M1LearnedCandidate,
            M1LearnedCandidate,
            M1LearnedCandidate,
            M1LearnedCandidate,
        ],
        tuple(load_m1_candidate(artifact_root, reference) for reference in references),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Plan or explicitly execute the frozen five-seed held-out comparison."""

    parser = argparse.ArgumentParser(
        description="Plan the frozen M1 held-out comparison, or execute it.",
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
        help="external root containing the five production M1 selections",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="external root for the recoverable evaluation checkpoint",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="run held-out solvers; omission is a read-only verified plan",
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
        output_root = validate_external_output_root(
            snapshot.root,
            cast(Path, parsed.output_root),
        )
        materialization = load_frozen_m1_materialization(data_root)
        references = production_selection_references(artifact_root)
        selection_summaries, checkpoints = audit_evaluation_selections(
            artifact_root,
            references,
            materialization=materialization,
        )
        runtime = capture_m1_runtime(snapshot.root / "uv.lock")
        context = M1EvaluationContext(
            manifest_sha256=materialization.manifest_sha256,
            evaluation_source_revision=snapshot.source_revision,
            runtime=runtime,
            selections=references,
            checkpoints=checkpoints,
        )
    except (
        DatasetEntrypointError,
        M1ArtifactError,
        M1EvaluationEntrypointError,
        M1TrainingEntrypointError,
        ValueError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    execute = cast(bool, parsed.execute)
    manifest = materialization.manifest
    summary: dict[str, object] = {
        "catalog_id": M0_CASE_CATALOG_ID,
        "data_manifest_sha256": materialization.manifest_sha256,
        "evaluation_id": build_m1_evaluation_id(context),
        "evaluation_source_revision": snapshot.source_revision,
        "mode": "execute" if execute else "plan",
        "ood_cases": manifest.split_counts.ood,
        "runtime": runtime.model_dump(mode="json"),
        "seeds": M1_SEEDS,
        "selections": selection_summaries,
        "source_tree_clean": True,
        "summary_version": M1_EVALUATION_SUMMARY_VERSION,
        "test_cases": manifest.split_counts.test,
    }
    if not execute:
        summary["state"] = "planned"
        _print_summary(summary)
        return 0

    try:
        candidates = load_evaluation_candidates(artifact_root, references)
        index = run_m1_experiment(
            data_root,
            output_root,
            materialization,
            context,
            candidates,
        )
        statistics = compute_m1_experiment_statistics(index, materialization)
    except (
        BaselineEvaluationError,
        M1ArtifactError,
        M1EvaluationError,
        M1ExperimentError,
        ValueError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    summary["completed_cases"] = len(index.entries)
    summary["state"] = index.state
    summary["statistics"] = statistics.model_dump(mode="json")
    _print_summary(summary)
    return 0


def _print_summary(summary: dict[str, object]) -> None:
    print(json.dumps(summary, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
