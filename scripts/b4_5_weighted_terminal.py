"""Metadata-only plan or explicitly charged B4.5 fit/reference/screen/audit."""

import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from torch import nn

from topolab import b4_evidence as evidence
from topolab.b3_access import B3Access
from topolab.b3_artifacts import read_b3_record, safe_path
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_dataset import audit_b3_record
from topolab.b3_materialization import B3DataSuccess
from topolab.b3_queries import QueryOutcome, evaluate_query
from topolab.b3_screen_cli import screening_preflight
from topolab.b3_screening import B3ScreenContext, load_neighbors
from topolab.b3_training import SEEDS, Recipe, fitting_entries, validation_mse
from topolab.b3_training_artifacts import read_selected_model
from topolab.b4_telemetry import Journal, digest, durable_write
from topolab.b4_weighted_terminal import (
    CAPS,
    MAX_EPOCH_ATTEMPTS,
    VERSION,
    assignments,
    development_gate,
    fit_weighted,
    fresh_cases,
    plan,
    publish_weighted_fit,
    read_units,
    read_weighted_model,
    weighted_samples,
)
from topolab.dataset_cli import validate_external_output_root


def units(stage: str) -> tuple[str, ...]:
    if stage == "fit":
        return tuple(f"W/{seed}" for seed in SEEDS)
    if stage == "reference":
        return tuple(c.case_id for c in fresh_cases())
    if stage == "screen":
        return tuple(f"{c}:{m}" for c, m in assignments())
    return (
        "labels",
        "fits",
        *tuple(f"reference:{c}" for c in units("reference")),
        *tuple(f"screen:{a}" for a in units("screen")),
    )


def read_packet(
    root: Path, ref: dict[str, Any], context_sha: str, case_id: str, policy: str
) -> dict[str, Any]:
    return evidence.read_packet(root, ref, context_sha, case_id, policy, VERSION)


def check_packet(packet: dict[str, Any], reference: float | None) -> int:
    case = next(c for c in fresh_cases() if c.case_id == packet["case_id"])
    return evidence.check_packet(packet, reference, case)


def query(
    journal: Journal,
    case_id: str,
    policy: str,
    reference: float | None,
    models: dict[tuple[Recipe, int], nn.Module],
    neighbors: Any,
    context_sha: str,
) -> dict[str, Any]:
    case = next(c for c in fresh_cases() if c.case_id == case_id)
    return evidence.query(
        journal,
        case,
        policy,
        reference,
        models,
        neighbors,
        context_sha,
        VERSION,
        "topolab.b4_5.recording.v1",
        evaluate_query,
    )


def recording_receipt(root: Path, ordinal: int, ref: dict[str, Any], context_sha: str) -> None:
    evidence.recording_receipt(root, ordinal, ref, context_sha, "topolab.b4_5.recording.v1")


def run(
    stage: str,
    output: Path,
    data: Path,
    old_fits: Path,
    context: B3ScreenContext,
    context_sha: str,
    startup: float,
) -> dict[str, Any]:
    journal = Journal(
        output / stage, context_sha, units(stage), *CAPS[stage], opening_seconds=startup
    )
    train_context = context.training_index.context
    summary: dict[str, Any] = {"version": VERSION, "stage": stage, "context_sha256": context_sha}
    try:
        if stage != "fit":
            read_units(output / "fit", context_sha, units("fit"))
        if stage == "fit":
            train, validation = weighted_samples(data, train_context, lambda: journal.pulse())
            path = safe_path(journal.root, "epoch_attempts.json")
            epochs = (
                json.loads(path.read_bytes())
                if path.exists()
                else {
                    "version": "topolab.b4_5.epochs.v1",
                    "context_sha256": context_sha,
                    "attempted": 0,
                }
            )
            if (
                epochs["version"] != "topolab.b4_5.epochs.v1"
                or epochs["context_sha256"] != context_sha
                or type(epochs["attempted"]) is not int
                or not 0 <= epochs["attempted"] <= MAX_EPOCH_ATTEMPTS
                or path.exists()
                and canonical_metadata_bytes(epochs) != path.read_bytes()
            ):
                raise ValueError("epoch ledger differs")

            def checkpoint(new_epoch: bool) -> None:
                if new_epoch:
                    if epochs["attempted"] >= MAX_EPOCH_ATTEMPTS:
                        journal.state = journal.state.model_copy(update={"resource_failed": True})
                        journal.pulse(force=True)
                    epochs["attempted"] += 1
                    durable_write(path, canonical_metadata_bytes(epochs))
                journal.pulse(force=new_epoch)

            retained_epochs = 0
            for i, retained in enumerate(journal.records):
                history, model = read_weighted_model(
                    journal.root, context_sha, SEEDS[i], retained["payload"]
                )
                if validation_mse(model, validation) != history.selected_validation_loss:
                    raise ValueError("completed checkpoint validation differs")
                retained_epochs += len(history.history)
            if retained_epochs > epochs["attempted"]:
                raise ValueError("epoch ledger omits completed fits")
            for seed in SEEDS[journal.state.completed :]:
                journal.begin(f"W/{seed}")
                fit = fit_weighted(train, validation, seed, checkpoint)
                ref = publish_weighted_fit(journal.root, context_sha, seed, fit)
                history, model = read_weighted_model(journal.root, context_sha, seed, ref)
                if validation_mse(model, validation) != history.selected_validation_loss:
                    raise ValueError("selected checkpoint validation differs")
                journal.publish(f"W/{seed}", ref)
                print(
                    json.dumps(
                        {
                            "seed": seed,
                            "epochs": len(history.history),
                            "selected_epoch": history.selected_epoch,
                            "seconds": journal.charged_seconds,
                        }
                    ),
                    flush=True,
                )
            summary["attempted_epochs"] = epochs["attempted"]
        elif stage == "reference":
            for ordinal, retained in enumerate(journal.records):
                recording_receipt(journal.root, ordinal, retained["payload"], context_sha)
            for case in fresh_cases()[journal.state.completed :]:
                packet = query(journal, case.case_id, "uniform", None, {}, None, context_sha)
                check_packet(packet, None)
                print(
                    json.dumps(
                        {"reference": journal.state.completed, "seconds": journal.charged_seconds}
                    ),
                    flush=True,
                )
        else:
            fit_refs = read_units(output / "fit", context_sha, units("fit"))
            references = read_units(output / "reference", context_sha, units("reference"))
            compliance = {}
            for i, (case, ref) in enumerate(zip(fresh_cases(), references, strict=True)):
                recording_receipt(output / "reference", i, ref, context_sha)
                packet = read_packet(
                    output / "reference", ref, context_sha, case.case_id, "uniform"
                )
                result = QueryOutcome.model_validate(packet["outcome"])
                if result.operational is None or result.operational.metrics is None:
                    raise ValueError("mandatory reference failed")
                compliance[case.case_id] = result.operational.metrics.final_compliance
            if stage == "screen":
                models: dict[tuple[Recipe, int], nn.Module] = {}
                weighted: dict[tuple[Recipe, int], nn.Module] = {}
                for outcome in context.training_index.outcomes:
                    if outcome.recipe in ("C", "P", "S"):
                        models[(outcome.recipe, outcome.seed)] = read_selected_model(
                            old_fits, train_context, outcome
                        )[1]
                for seed, ref in zip(SEEDS, fit_refs, strict=True):
                    weighted[("P", seed)] = read_weighted_model(
                        output / "fit", context_sha, seed, ref
                    )[1]
                    weighted[("S", seed)] = models[("S", seed)]
                neighbors = load_neighbors(data, context, lambda: journal.pulse())
                for ordinal, retained in enumerate(journal.records):
                    recording_receipt(journal.root, ordinal, retained["payload"], context_sha)
                for case_id, policy in assignments()[journal.state.completed :]:
                    case = next(c for c in fresh_cases() if c.case_id == case_id)
                    nx, ny, nz = case.problem.mesh.element_counts
                    packet = query(
                        journal,
                        case_id,
                        policy,
                        compliance[case_id],
                        weighted if policy.startswith("W/") else models,
                        neighbors[(nz, ny, nx)],
                        context_sha,
                    )
                    check_packet(packet, compliance[case_id])
                    print(
                        json.dumps(
                            {
                                "query": journal.state.completed,
                                "case_id": case_id,
                                "policy": policy,
                                "seconds": journal.charged_seconds,
                            }
                        ),
                        flush=True,
                    )
            else:
                screen_refs = read_units(output / "screen", context_sha, units("screen"))
                train, validation = weighted_samples(data, train_context, lambda: journal.pulse())
                for unit in journal.units[journal.state.completed :]:
                    journal.begin(unit)
                    result: dict[str, Any] = {}
                    if unit == "labels":
                        train_ids, validation_ids = fitting_entries("P")
                        ids = set((*train_ids, *validation_ids))
                        access = B3Access(consumer="fitting", training_set="expanded")
                        for item in train_context.data_index.entries:
                            if isinstance(item, B3DataSuccess) and item.entry.case.case_id in ids:
                                audit_b3_record(
                                    read_b3_record(
                                        data,
                                        train_context.data_index.manifest,
                                        item.artifact,
                                        access,
                                    )
                                )
                                journal.pulse()
                        result["audited_labels"] = len(ids)
                    elif unit == "fits":
                        epochs = 0
                        for seed, ref in zip(SEEDS, fit_refs, strict=True):
                            history, model = read_weighted_model(
                                output / "fit", context_sha, seed, ref
                            )
                            if (
                                validation_mse(model, validation)
                                != history.selected_validation_loss
                            ):
                                raise ValueError("independent selected-model validation differs")
                            epochs += len(history.history)
                        attempts = json.loads(
                            safe_path(output / "fit", "epoch_attempts.json").read_bytes()
                        )["attempted"]
                        if not epochs <= attempts <= MAX_EPOCH_ATTEMPTS:
                            raise ValueError("attempted epoch charge differs")
                        result.update(
                            audited_fits=3, retained_epochs=epochs, attempted_epochs=attempts
                        )
                    elif unit.startswith("reference:"):
                        case_id = unit.removeprefix("reference:")
                        ordinal = units("reference").index(case_id)
                        ref = references[ordinal]
                        recording_receipt(output / "reference", ordinal, ref, context_sha)
                        result["audited_attempts"] = check_packet(
                            read_packet(output / "reference", ref, context_sha, case_id, "uniform"),
                            None,
                        )
                    else:
                        ordinal = units("screen").index(unit.removeprefix("screen:"))
                        case_id, policy = assignments()[ordinal]
                        ref = screen_refs[ordinal]
                        recording_receipt(output / "screen", ordinal, ref, context_sha)
                        result["audited_attempts"] = check_packet(
                            read_packet(output / "screen", ref, context_sha, case_id, policy),
                            compliance[case_id],
                        )
                    journal.publish(unit, result)
                    if journal.state.completed % 24 == 0:
                        print(
                            json.dumps(
                                {
                                    "audited_units": journal.state.completed,
                                    "seconds": journal.charged_seconds,
                                }
                            ),
                            flush=True,
                        )
                del train, validation
            refs = [r["payload"] for r in journal.records] if stage == "screen" else screen_refs
            summary["decision"] = development_gate(
                read_packet(output / "screen", ref, context_sha, case_id, policy)
                for (case_id, policy), ref in zip(assignments(), refs, strict=True)
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
    parser.add_argument("--stage", choices=CAPS, default="fit")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--fit-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(plan(), sort_keys=True))
        return
    if any(a is None for a in (args.data_root, args.fit_root, args.output)):
        parser.error("execution needs explicit data, fit and output roots")
    repository, context = screening_preflight(Path.cwd(), args.data_root, args.fit_root)
    if not Path(__file__).resolve().is_relative_to(repository):
        raise ValueError("execution must load the recorded clean merged implementation")
    output = validate_external_output_root(repository, args.output)
    # A fixed new sibling prevents accidental writes inside any historical/final root.
    if output != args.data_root.resolve().parent / "b4-5-weighted-terminal":
        raise ValueError("output must be the new b4-5-weighted-terminal data sibling")
    if any(
        output.is_relative_to(p) or p.is_relative_to(output)
        for p in (args.data_root.resolve(), args.fit_root.resolve())
    ):
        raise ValueError("new output must be separate from immutable input roots")
    payload = {
        "version": VERSION,
        "plan_sha256": plan()["plan_sha256"],
        "source": context.source.model_dump(mode="json"),
        "data_sha256": context.training_index.context.data_index_sha256,
        "fixed_fits_sha256": context.training_index_sha256,
        "protocol_sha256": digest(
            (repository / "docs/planning/b4_5_weighted_terminal_protocol.md").read_bytes()
        ),
    }
    raw = canonical_metadata_bytes(payload)
    output.mkdir(parents=True, exist_ok=True)
    path = safe_path(output, "context.json")
    if path.exists() and path.read_bytes() != raw:
        raise ValueError("existing B4.5 execution context differs")
    if not path.exists():
        durable_write(path, raw)
    print(
        json.dumps(
            run(
                args.stage,
                output,
                args.data_root.resolve(),
                args.fit_root.resolve(),
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
