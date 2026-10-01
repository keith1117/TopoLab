"""Read-only planning and explicit B4 screening/prospective-freeze execution."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter

from topolab.b3_artifacts import safe_path
from topolab.b3_dataset_cli import build_current_b3_manifest
from topolab.b3_queries import METHODS
from topolab.b3_screening import (
    SCREEN_RSS_BYTES,
    SCREEN_SECONDS,
    TRAINING_INDEX_SHA256,
    B3ScreenContext,
    publish_freeze,
    read_screen_index,
    run_screen,
    screen_summary,
)
from topolab.b3_training_artifacts import B3TrainingIndex, digest
from topolab.dataset_cli import DatasetEntrypointError, validate_external_output_root


def screening_preflight(cwd: Path, data_root: Path, fit_root: Path) -> tuple[Path, B3ScreenContext]:
    repository, current = build_current_b3_manifest(cwd)
    data_root = validate_external_output_root(repository, data_root)
    fit_root = validate_external_output_root(repository, fit_root)
    contents = safe_path(fit_root, "b3_training.json").read_bytes()
    if digest(contents) != TRAINING_INDEX_SHA256:
        raise ValueError("fitting index differs from the passed B4.1 receipt")
    fitting = B3TrainingIndex.model_validate_json(contents)
    if digest(safe_path(data_root, "b3_materialization.json").read_bytes()) != (
        fitting.context.data_index_sha256
    ):
        raise ValueError("data index differs from the unchanged passed B3.4 receipt")
    return repository, B3ScreenContext(source=current.context, training_index=fitting)


def main(argv: Sequence[str] | None = None) -> int:
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--fit-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--audit", action="store_true")
    args = parser.parse_args(argv)
    try:
        repository, context = screening_preflight(Path.cwd(), args.data_root, args.fit_root)
        root = validate_external_output_root(repository, args.output_root)
        data_root, fit_root = args.data_root.resolve(), args.fit_root.resolve()
        roots = (data_root, fit_root, root)
        if any(
            a.is_relative_to(b) or b.is_relative_to(a)
            for i, a in enumerate(roots)
            for b in roots[i + 1 :]
        ):
            raise ValueError("data, fitting and screening roots must be separate")
        if not args.execute and not args.audit:
            summary: dict[str, object] = {
                "mode": "plan",
                "context_sha256": context.sha256(),
                "source_revision": context.source.source_revision,
                "training_index_sha256": context.training_index_sha256,
                "data_index_sha256": context.training_index.context.data_index_sha256,
                "cases": 48,
                "outcomes": 720,
                "methods": METHODS,
                "nn_train_labels": 528,
                "checkpoints": 12,
                "new_fits": 0,
                "maximum_seconds": SCREEN_SECONDS,
                "maximum_rss_bytes": SCREEN_RSS_BYTES,
                "final_artifacts": 0,
            }
            if safe_path(root, "b3_screen.json").exists():
                index = read_screen_index(root, context)
                summary["retained_cases"] = len(index.cases)
                summary["cumulative_seconds"] = index.cumulative_seconds
            print(json.dumps(summary, sort_keys=True, allow_nan=False))
            return 0
        if not Path(__file__).resolve().is_relative_to(repository):
            raise ValueError("screen must load implementation from the recorded clean checkout")
        index = run_screen(
            root,
            data_root,
            fit_root,
            context,
            repository_root=repository,
            audit_only=args.audit,
            startup_seconds=perf_counter() - started,
        )
        summary = screen_summary(index)
        freeze = publish_freeze(root, index)
        summary["freeze_sha256"] = None if freeze is None else freeze.stem
        summary["mode"] = "audit" if args.audit else "execute"
        print(json.dumps(summary, sort_keys=True, allow_nan=False))
        return 0 if summary["b4_gate_passed"] else 1
    except (DatasetEntrypointError, OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
