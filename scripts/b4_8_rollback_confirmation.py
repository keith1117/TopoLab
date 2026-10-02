"""Metadata-only B4.8 plan or explicit fixed-policy confirmation and audit."""

import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from torch import nn

from topolab import b4_evidence as evidence
from topolab.b3_artifacts import safe_path
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_queries import evaluate_query
from topolab.b3_screen_cli import screening_preflight
from topolab.b3_screening import B3ScreenContext
from topolab.b3_training import SEEDS, Recipe
from topolab.b3_training_artifacts import read_selected_model
from topolab.b4_confirmation import UPSTREAM_CONTEXT
from topolab.b4_development import DevelopmentSpec, run_development
from topolab.b4_rollback_confirmation import (
    CAPS,
    RECEIPT_VERSION,
    UPSTREAM_FILES,
    VERSION,
    assignments,
    confirmation_gate,
    fresh_cases,
    plan,
    upstream_fits,
)
from topolab.b4_telemetry import digest, durable_write
from topolab.b4_weighted_terminal import read_weighted_model
from topolab.dataset_cli import validate_external_output_root


def read_packet(
    root: Path, ref: dict[str, Any], sha: str, case: str, policy: str
) -> dict[str, Any]:
    return evidence.read_packet(root, ref, sha, case, policy, VERSION)


def receipt(root: Path, ordinal: int, ref: dict[str, Any], sha: str) -> None:
    evidence.recording_receipt(root, ordinal, ref, sha, RECEIPT_VERSION)


def load_models(
    context: B3ScreenContext, old: Path, weighted_root: Path
) -> tuple[dict[tuple[Recipe, int], nn.Module], dict[tuple[Recipe, int], nn.Module]]:
    refs = upstream_fits(weighted_root)
    models: dict[tuple[Recipe, int], nn.Module] = {}
    weighted: dict[tuple[Recipe, int], nn.Module] = {}
    for item in context.training_index.outcomes:
        if item.recipe in ("C", "P", "S"):
            models[(item.recipe, item.seed)] = read_selected_model(
                old, context.training_index.context, item
            )[1]
    for seed, ref in zip(SEEDS, refs, strict=True):
        weighted[("P", seed)] = read_weighted_model(
            weighted_root / "fit", UPSTREAM_CONTEXT, seed, ref
        )[1]
        weighted[("S", seed)] = models[("S", seed)]
    return models, weighted


def run(
    stage: str,
    output: Path,
    data: Path,
    old: Path,
    weighted_root: Path,
    context: B3ScreenContext,
    sha: str,
    startup: float,
) -> dict[str, Any]:
    prepared = perf_counter()
    spec = DevelopmentSpec(
        VERSION,
        RECEIPT_VERSION,
        CAPS,
        fresh_cases(),
        assignments(),
        confirmation_gate,
        upstream_fits,
    )
    return run_development(
        stage,
        output,
        data,
        old,
        weighted_root,
        context,
        sha,
        startup + perf_counter() - prepared,
        spec=spec,
        load_models=load_models,
        evaluate_query=evaluate_query,
    )


def main() -> None:
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=CAPS, default="reference")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--fit-root", type=Path)
    parser.add_argument("--weighted-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(plan(), sort_keys=True))
        return
    if any(a is None for a in (args.data_root, args.fit_root, args.weighted_root, args.output)):
        parser.error("execution needs explicit data, fixed-fit, weighted-fit and output roots")
    repository, context = screening_preflight(Path.cwd(), args.data_root, args.fit_root)
    if not Path(__file__).resolve().is_relative_to(repository):
        raise ValueError("execution must load the clean merged source")
    output = validate_external_output_root(repository, args.output)
    weighted_root = validate_external_output_root(repository, args.weighted_root)
    parent = args.data_root.resolve().parent
    if (
        output != parent / "b4-8-rollback-confirmation"
        or weighted_root != parent / "b4-5-weighted-terminal"
    ):
        raise ValueError("rollback confirmation requires its fixed external siblings")
    roots = (args.data_root.resolve(), args.fit_root.resolve(), weighted_root, output)
    if any(
        a.is_relative_to(b) or b.is_relative_to(a)
        for i, a in enumerate(roots)
        for b in roots[i + 1 :]
    ):
        raise ValueError("rollback confirmation output must be separate from immutable inputs")
    upstream_fits(weighted_root)
    payload = {
        "version": VERSION,
        "plan_sha256": plan()["plan_sha256"],
        "source": context.source.model_dump(mode="json"),
        "data_sha256": context.training_index.context.data_index_sha256,
        "fixed_fits_sha256": context.training_index_sha256,
        "upstream_files": UPSTREAM_FILES,
        "protocol_sha256": digest(
            (repository / "docs/planning/b4_8_rollback_confirmation_protocol.md").read_bytes()
        ),
    }
    raw = canonical_metadata_bytes(payload)
    output.mkdir(parents=True, exist_ok=True)
    path = safe_path(output, "context.json")
    if path.exists() and path.read_bytes() != raw:
        raise ValueError("existing rollback confirmation context differs")
    if not path.exists():
        durable_write(path, raw)
    print(
        json.dumps(
            run(
                args.stage,
                output,
                args.data_root.resolve(),
                args.fit_root.resolve(),
                weighted_root,
                context,
                digest(raw),
                perf_counter() - started,
            ),
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
