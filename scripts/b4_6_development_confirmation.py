"""Metadata-only B4.6 plan or explicit fixed-policy confirmation and audit."""

import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from torch import nn

from topolab import b4_evidence as evidence
from topolab.b3_access import B3Access
from topolab.b3_artifacts import _parse_record, _read_bytes, safe_path
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_dataset import audit_b3_record
from topolab.b3_materialization import B3DataSuccess
from topolab.b3_queries import QueryOutcome, evaluate_query
from topolab.b3_screen_cli import screening_preflight
from topolab.b3_screening import B3ScreenContext, load_neighbors
from topolab.b3_training import SEEDS, Recipe
from topolab.b3_training_artifacts import read_selected_model
from topolab.b4_confirmation import (
    CAPS,
    RECEIPT_VERSION,
    UPSTREAM_CONTEXT,
    UPSTREAM_FILES,
    VERSION,
    assignments,
    confirmation_gate,
    fresh_cases,
    plan,
    units,
    upstream_fits,
)
from topolab.b4_telemetry import Journal, digest, durable_write
from topolab.b4_weighted_terminal import read_units, read_weighted_model
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
    journal = Journal(output / stage, sha, units(stage), *CAPS[stage], opening_seconds=startup)
    cases = {c.case_id: c for c in fresh_cases()}
    summary: dict[str, Any] = {"version": VERSION, "stage": stage, "context_sha256": sha}
    try:
        upstream_fits(weighted_root)
        if stage == "reference":
            for i, retained in enumerate(journal.records):
                receipt(journal.root, i, retained["payload"], sha)
                evidence.check_packet(
                    read_packet(journal.root, retained["payload"], sha, units(stage)[i], "uniform"),
                    None,
                    cases[units(stage)[i]],
                )
            for case_id in units(stage)[journal.state.completed :]:
                packet = evidence.query(
                    journal,
                    cases[case_id],
                    "uniform",
                    None,
                    {},
                    None,
                    sha,
                    VERSION,
                    RECEIPT_VERSION,
                    evaluate_query,
                )
                evidence.check_packet(packet, None, cases[case_id])
                print(json.dumps({"references": journal.state.completed}), flush=True)
        else:
            references = read_units(output / "reference", sha, units("reference"), caps=CAPS)
            compliance = {}
            for i, (case_id, ref) in enumerate(zip(units("reference"), references, strict=True)):
                receipt(output / "reference", i, ref, sha)
                packet = read_packet(output / "reference", ref, sha, case_id, "uniform")
                outcome = QueryOutcome.model_validate(packet["outcome"])
                if outcome.operational is None or outcome.operational.metrics is None:
                    raise ValueError("mandatory reference failed")
                compliance[case_id] = outcome.operational.metrics.final_compliance
            if stage == "screen":
                models, weighted = load_models(context, old, weighted_root)
                neighbors = load_neighbors(data, context, lambda: journal.pulse())
                for i, retained in enumerate(journal.records):
                    receipt(journal.root, i, retained["payload"], sha)
                for case_id, policy in assignments()[journal.state.completed :]:
                    case = cases[case_id]
                    nx, ny, nz = case.problem.mesh.element_counts
                    packet = evidence.query(
                        journal,
                        case,
                        policy,
                        compliance[case_id],
                        weighted if policy.startswith("W/") else models,
                        neighbors[(nz, ny, nx)],
                        sha,
                        VERSION,
                        RECEIPT_VERSION,
                        evaluate_query,
                    )
                    evidence.check_packet(packet, compliance[case_id], case)
                    print(
                        json.dumps({"queries": journal.state.completed, "policy": policy}),
                        flush=True,
                    )
                screen_refs = [r["payload"] for r in journal.records]
            else:
                screen_refs = read_units(output / "screen", sha, units("screen"), caps=CAPS)
                for unit in units("audit")[journal.state.completed :]:
                    journal.begin(unit)
                    result: dict[str, Any] = {}
                    if unit == "inputs":
                        models, weighted = load_models(context, old, weighted_root)
                        result["audited_checkpoints"] = len(models) + 3
                        del models, weighted
                    elif unit == "nn_labels":
                        index = context.training_index.context.data_index
                        artifacts = sorted(
                            (
                                o.artifact
                                for o in index.entries
                                if isinstance(o, B3DataSuccess) and o.entry.role == "train"
                            ),
                            key=lambda a: a.access.entry.case.case_id,
                        )
                        by_id = {a.access.entry.case.case_id: a for a in artifacts}
                        contents = B3Access(consumer="nearest_neighbor").iter_population(
                            (a.access for a in artifacts),
                            "label",
                            lambda a, by_id=by_id: _read_bytes(data, by_id[a.entry.case.case_id]),
                        )
                        count = 0
                        for raw, artifact in zip(contents, artifacts, strict=True):
                            audit_b3_record(_parse_record(raw, artifact, index.manifest))
                            count += 1
                            journal.pulse()
                        result["audited_nn_labels"] = count
                    else:
                        is_ref = unit.startswith("reference:")
                        target = "reference" if is_ref else "screen"
                        i = units(target).index(unit.removeprefix(target + ":"))
                        case_id, policy = (
                            (units(target)[i], "uniform") if is_ref else assignments()[i]
                        )
                        ref = (references if is_ref else screen_refs)[i]
                        receipt(output / target, i, ref, sha)
                        result["audited_attempts"] = evidence.check_packet(
                            read_packet(output / target, ref, sha, case_id, policy),
                            None if is_ref else compliance[case_id],
                            cases[case_id],
                        )
                    journal.publish(unit, result)
                    if journal.state.completed % 48 == 0:
                        print(json.dumps({"audited_units": journal.state.completed}), flush=True)
            summary["decision"] = confirmation_gate(
                read_packet(output / "screen", ref, sha, case_id, policy)
                for (case_id, policy), ref in zip(assignments(), screen_refs, strict=True)
            )
        journal.close()
        summary.update(
            completed=journal.state.completed,
            attempted=journal.state.attempted,
            charged_seconds=journal.state.charged_seconds,
            peak_rss_bytes=journal.state.peak_rss_bytes,
            head_sha256=journal.state.head_sha256,
        )
        durable_write(safe_path(journal.root, "summary.json"), canonical_metadata_bytes(summary))
        return summary
    except KeyboardInterrupt:
        journal.close()
        raise
    except BaseException:
        if not journal.lock.closed:
            journal.close(integrity_failed=True)
        raise


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
        output != parent / "b4-6-development-confirmation"
        or weighted_root != parent / "b4-5-weighted-terminal"
    ):
        raise ValueError("confirmation requires its fixed external siblings")
    roots = (args.data_root.resolve(), args.fit_root.resolve(), weighted_root, output)
    if any(
        a.is_relative_to(b) or b.is_relative_to(a)
        for i, a in enumerate(roots)
        for b in roots[i + 1 :]
    ):
        raise ValueError("confirmation output must be separate from immutable inputs")
    upstream_fits(weighted_root)
    payload = {
        "version": VERSION,
        "plan_sha256": plan()["plan_sha256"],
        "source": context.source.model_dump(mode="json"),
        "data_sha256": context.training_index.context.data_index_sha256,
        "fixed_fits_sha256": context.training_index_sha256,
        "upstream_files": UPSTREAM_FILES,
        "protocol_sha256": digest(
            (repository / "docs/planning/b4_6_confirmation_protocol.md").read_bytes()
        ),
    }
    raw = canonical_metadata_bytes(payload)
    output.mkdir(parents=True, exist_ok=True)
    path = safe_path(output, "context.json")
    if path.exists() and path.read_bytes() != raw:
        raise ValueError("existing confirmation context differs")
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
