"""Read-only planning and explicit execution of B4.1's fixed twelve CPU fits."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter

from topolab.b3_artifacts import safe_path
from topolab.b3_dataset_cli import build_current_b3_manifest
from topolab.b3_materialization import B3MaterializationIndex
from topolab.b3_training import RECIPES, SEEDS, case_weights, fitting_entries
from topolab.b3_training_artifacts import (
    B3_DATA_INDEX_SHA256,
    FIT_RSS_BYTES,
    FIT_SECONDS,
    MAX_ATTEMPTED_EPOCHS,
    B3TrainingContext,
    digest,
    read_training_index,
    run_b3_fitting,
)
from topolab.dataset_cli import DatasetEntrypointError, validate_external_output_root


def training_preflight(cwd: Path, data_root: Path) -> tuple[Path, B3TrainingContext]:
    repository, current = build_current_b3_manifest(cwd)
    data_root = validate_external_output_root(repository, data_root)
    contents = safe_path(data_root, "b3_materialization.json").read_bytes()
    if digest(contents) != B3_DATA_INDEX_SHA256:
        raise ValueError("data index differs from the passed B3.4 receipt")
    data_index = B3MaterializationIndex.model_validate_json(contents)
    return repository, B3TrainingContext(source=current.context, data_index=data_index)


def main(argv: Sequence[str] | None = None) -> int:
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--audit", action="store_true")
    args = parser.parse_args(argv)
    try:
        repository, context = training_preflight(Path.cwd(), args.data_root)
        root = validate_external_output_root(repository, args.output_root)
        data_root = args.data_root.resolve()
        if root.is_relative_to(data_root) or data_root.is_relative_to(root):
            raise ValueError("fitting output must be separate from the data root")
        if not args.execute and not args.audit:
            summary: dict[str, object] = {
                "mode": "plan", "context_sha256": context.sha256(),
                "source_revision": context.source.source_revision,
                "data_index_sha256": context.data_index_sha256,
                "recipes": [{"recipe": r, "train": len(fitting_entries(r)[0]),
                             "validation": len(fitting_entries(r)[1]),
                             "weighted_cases": sum(w == 8 for w in case_weights(r).values())}
                            for r in RECIPES],
                "seeds": SEEDS, "fits": 12, "max_attempted_epochs": MAX_ATTEMPTED_EPOCHS,
                "maximum_seconds": FIT_SECONDS, "maximum_rss_bytes": FIT_RSS_BYTES,
                "screen_outcomes": 0, "final_artifacts": 0,
            }
            if safe_path(root, "b3_training.json").exists():
                index = read_training_index(root, context)
                summary["retained_fits"] = len(index.outcomes)
                summary["cumulative_seconds"] = index.cumulative_seconds
            print(json.dumps(summary, sort_keys=True, allow_nan=False))
            return 0
        if not Path(__file__).resolve().is_relative_to(repository):
            raise ValueError("fitting must load implementation from the recorded clean checkout")
        index = run_b3_fitting(root, data_root, context, repository_root=repository,
                               audit_only=args.audit, startup_seconds=perf_counter() - started)
        print(json.dumps({"mode": "audit" if args.audit else "execute",
                          "fitting_gate_passed": index.fitting_gate_passed,
                          "retained_fits": len(index.outcomes),
                          "attempted_epochs": index.attempted_epochs,
                          "cumulative_seconds": index.cumulative_seconds,
                          "peak_rss_bytes": index.peak_rss_bytes}, sort_keys=True))
        return 0 if index.fitting_gate_passed else 1
    except (DatasetEntrypointError, OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
