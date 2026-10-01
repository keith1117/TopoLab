"""Frozen exposed-case engineering sentinel; no fits, labels, NN or final access."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from time import perf_counter
from typing import Any, cast

from topolab.b3_artifacts import safe_path
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_dataset_cli import build_current_b3_manifest
from topolab.b3_queries import QueryOutcome, audit_witness, evaluate_query
from topolab.b3_screening import B3EvaluationIndex, read_case, write_screen_index
from topolab.b3_training import Recipe
from topolab.b3_training_artifacts import read_selected_model
from topolab.b4_telemetry import CheckpointMeter, Journal, digest, durable_write, timed_query
from topolab.dataset_cli import validate_external_output_root

VERSION = "topolab.b4_4.engineering.v1"
MAX_SECONDS = 7200.0
MAX_RSS_BYTES = 2_147_483_648
BINDINGS = {
    "b3_screen.json": "a647f420cb2d498c961a6e8ca965511b4a18e33e26056b10cf987d989df8a421",
    "audit_receipts/execution_index.json": (
        "89a7e66ce2c61294c8dcf36585965d04ffeabe1a00b479cf5bd1843427bd588c"
    ),
}
CASES = (
    ("tlcase-v1-bcb1e840964c813a1ddc3e618c768a088dd484dfc2cf161a4fc1d35c54f014a5", 43),
    ("tlcase-v1-c7932fa2ac5f7ef8b6b3f1fe37d3a9d74efde3c8c6062d6202b9ae9453d353e0", 17),
    ("tlcase-v1-44a485a7a9908ce412b4b5e888b9c4b778b970bea9cf9798db718f8cf63620a2", 29),
    ("tlcase-v1-7c1e479200103239ff80c4e49a4bf5eb95f04124fd5f727d37b077458f400adb", 29),
    ("tlcase-v1-e934fc40079cfa70a01a44e5b62fce3d48607767140c6a85c3b4e40c409431c1", 43),
    ("tlcase-v1-2b3c39c6d795c0e9a16fd123584302406072b190643dd26e8b28cde09dbc1620", 17),
)


def schedule() -> list[dict[str, Any]]:
    result = []
    for repeat, arms in enumerate((("legacy", "compact"), ("compact", "legacy"))):
        for arm in arms:
            for number, (case_id, seed) in enumerate(CASES):
                aliases = (
                    [("P", seed), ("P_without_S", seed)]
                    if number < 5
                    else [("C", seed), ("P", seed), ("A", seed)]
                )
                if repeat:
                    aliases.reverse()
                for method, selected_seed in [("uniform", None), *aliases]:
                    result.append(
                        {
                            "repeat": repeat,
                            "arm": arm,
                            "case_id": case_id,
                            "method": method,
                            "seed": selected_seed,
                        }
                    )
    return result


def plan_payload() -> dict[str, Any]:
    plan = {
        "version": VERSION,
        "bindings": BINDINGS,
        "schedule": schedule(),
        "model_reads": [["P", 17], ["P", 29], ["P", 43], ["S", 17]],
        "max_seconds": MAX_SECONDS,
        "max_rss_bytes": MAX_RSS_BYTES,
        "forced_flush": "second checkpoint call (first solver update)",
        "heartbeat_seconds": 5,
        "max_progress_bytes": 4096,
        "gates": {
            "complete_queries": 76,
            "exact_numerical_identity": True,
            "callback_wall_ratio_max": 0.25,
            "complete_wall_ratio_max": 1.05,
        },
        "scope": "engineering_only; original failed B4 and sealed B5 unchanged",
    }
    return {**plan, "plan_sha256": digest(canonical_metadata_bytes(plan))}


def numerical_payload(outcome: QueryOutcome) -> dict[str, Any]:
    value = outcome.model_dump(mode="json")
    value.pop("route_seconds")
    for key in ("attempt", "fallback"):
        if value[key] is not None:
            value[key].pop("timing")
    return value


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {}
    for arm in ("legacy", "compact"):
        rows = [r["payload"] for r in records if r["payload"]["assignment"]["arm"] == arm]
        totals[arm] = {
            "queries": len(rows),
            "wall_seconds": sum(r["timing"]["wall_seconds"] for r in rows),
            "cpu_seconds": sum(r["timing"]["cpu_seconds"] for r in rows),
            "callback_wall_seconds": sum(r["callback"]["wall_seconds"] for r in rows),
            "callback_cpu_seconds": sum(r["callback"]["cpu_seconds"] for r in rows),
            "flush_wall_seconds": sum(r["callback"]["flush_wall_seconds"] for r in rows),
            "flushes": sum(r["callback"]["flushes"] for r in rows),
            "bytes_written": sum(r["callback"]["bytes_written"] for r in rows),
            "failures": sum(not r["outcome"]["attempt"]["succeeded"] for r in rows),
            "audited": sum(r["audited_attempts"] for r in rows),
        }
    callback_ratio = (
        totals["compact"]["callback_wall_seconds"] / totals["legacy"]["callback_wall_seconds"]
    )
    wall_ratio = totals["compact"]["wall_seconds"] / totals["legacy"]["wall_seconds"]
    complete = len(records) == 76 and all(r["payload"]["numerically_identical"] for r in records)
    return {
        "totals": totals,
        "callback_wall_ratio": callback_ratio,
        "complete_wall_ratio": wall_ratio,
        "engineering_gate_passed": complete and callback_ratio <= 0.25 and wall_ratio <= 1.05,
        "learning_gate_passed": False,
        "final_access": False,
    }


def execute(cwd: Path, screen_root: Path, fit_root: Path, output: Path) -> dict[str, Any]:
    started = perf_counter()
    if output.is_symlink():
        raise ValueError("sentinel output must not be a symlink")
    output = validate_external_output_root(cwd, output)
    for protected in (screen_root.resolve(), fit_root.resolve()):
        if (
            output == protected
            or output.is_relative_to(protected)
            or protected.is_relative_to(output)
        ):
            raise ValueError("sentinel output must be disjoint from all original artifact roots")
    _, manifest = build_current_b3_manifest(cwd)
    inputs = {}
    for name, expected in BINDINGS.items():
        raw = safe_path(screen_root, name).read_bytes()
        if digest(raw) != expected:
            raise ValueError("sentinel input checksum differs")
        inputs[name] = raw
    original = B3EvaluationIndex.model_validate_json(inputs["b3_screen.json"])
    shadow = B3EvaluationIndex.model_validate_json(inputs["audit_receipts/execution_index.json"])
    if (
        original.cases != shadow.cases
        or original.context != shadow.context
        or len(original.cases) != 48
    ):
        raise ValueError("sentinel needs the exact retained complete exposed panel")
    plan = plan_payload()
    context = {
        "plan": plan,
        "source": manifest.context.model_dump(mode="json"),
        "protocol_sha256": digest(
            (cwd / "docs/planning/b4_4_engineering_protocol.md").read_bytes()
        ),
    }
    context_raw = canonical_metadata_bytes(context)
    assignments = schedule()
    units = tuple(digest(canonical_metadata_bytes(a)) for a in assignments)
    journal = Journal(
        output,
        digest(context_raw),
        units,
        MAX_SECONDS,
        MAX_RSS_BYTES,
        opening_seconds=perf_counter() - started,
    )
    try:
        context_path = safe_path(output, "context.json")
        if context_path.exists() and context_path.read_bytes() != context_raw:
            raise ValueError("sentinel execution context changed")
        durable_write(context_path, context_raw)
        models = {}
        for recipe, seed in (("P", 17), ("P", 29), ("P", 43), ("S", 17)):
            fit = next(
                o
                for o in original.context.training_index.outcomes
                if (o.recipe, o.seed) == (recipe, seed)
            )
            _, model = read_selected_model(fit_root, original.context.training_index.context, fit)
            models[(cast(Recipe, recipe), seed)] = model
        records = {}
        for case_id, _ in CASES:
            reference = next(f for f in original.cases if f.access.entry.case.case_id == case_id)
            records[case_id] = read_case(screen_root, original.context, reference)
            journal.pulse()
        shadow_root = safe_path(output, "legacy_shadow")
        shadow_root.mkdir(exist_ok=True)
        shadow_path = safe_path(shadow_root, "b3_screen.json")
        if not shadow_path.exists():
            durable_write(shadow_path, inputs["audit_receipts/execution_index.json"])
        else:
            shadow = B3EvaluationIndex.model_validate_json(shadow_path.read_bytes())
            if shadow.cases != original.cases or shadow.context != original.context:
                raise ValueError("legacy shadow fixture changed")
        for ordinal in range(journal.state.completed, len(assignments)):
            assignment = assignments[ordinal]
            retained = records[assignment["case_id"]]
            journal.begin(units[ordinal])
            last_legacy = perf_counter()

            def pulse(force: bool, arm: str = assignment["arm"]) -> int:
                nonlocal last_legacy, shadow
                written = journal.pulse(force=force)
                if arm == "legacy" and (force or perf_counter() - last_legacy >= 5):
                    shadow = shadow.model_copy(
                        update={
                            "cumulative_seconds": shadow.cumulative_seconds
                            + max(0, perf_counter() - last_legacy),
                            "active_checkpoint_at": datetime.now(UTC),
                        }
                    )
                    write_screen_index(shadow_root, shadow)
                    written += shadow_path.stat().st_size
                    last_legacy = perf_counter()
                return written

            meter = CheckpointMeter(pulse)
            outcome, timing = timed_query(
                partial(
                    evaluate_query,
                    retained.entry.case,
                    assignment["method"],
                    assignment["seed"],
                    retained.mandatory_uniform_compliance,
                    models,
                    None,
                    meter,
                )
            )
            expected = next(
                q for q in retained.outcomes if (q.method, q.seed) == (outcome.method, outcome.seed)
            )
            numerical = numerical_payload(outcome)
            if numerical != numerical_payload(expected):
                raise ValueError("engineering arm changed a retained numerical outcome")
            audited = 0
            for attempt in (outcome.attempt, outcome.fallback):
                if attempt is not None:
                    if attempt.state is None:
                        raise ValueError("sentinel requires every terminal state")
                    metrics = audit_witness(
                        retained.entry.case,
                        attempt.state,
                        retained.mandatory_uniform_compliance,
                        accepted=attempt.succeeded,
                    )
                    if metrics != attempt.metrics:
                        raise ValueError("independent terminal audit differs")
                    audited += 1
            journal.publish(
                units[ordinal],
                {
                    "assignment": assignment,
                    "outcome": outcome.model_dump(mode="json"),
                    "timing": timing,
                    "callback": meter.summary(),
                    "numerically_identical": True,
                    "numerical_sha256": digest(canonical_metadata_bytes(numerical)),
                    "audited_attempts": audited,
                },
            )
            print(
                json.dumps(
                    {
                        "completed": journal.state.completed,
                        "assignment": assignment,
                        "query_wall": timing["wall_seconds"],
                        "charged_seconds": journal.charged_seconds,
                    }
                ),
                flush=True,
            )
        summary = {
            "version": VERSION,
            "context_sha256": journal.state.context_sha256,
            **summarize(journal.records),
        }
        journal.close()
        summary.update(
            charged_seconds=journal.state.charged_seconds,
            peak_rss_bytes=journal.state.peak_rss_bytes,
            head_sha256=journal.state.head_sha256,
            attempted=journal.state.attempted,
        )
        durable_write(safe_path(output, "summary.json"), canonical_metadata_bytes(summary))
        return summary
    except BaseException:
        if not journal.lock.closed:
            journal.close(integrity_failed=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--plan", action="store_true")
    parser.add_argument("--screen-root", type=Path)
    parser.add_argument("--fit-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(plan_payload(), sort_keys=True))
        return
    if any(v is None for v in (args.screen_root, args.fit_root, args.output)):
        parser.error("execution needs explicit screen, fit and output roots")
    print(
        json.dumps(
            execute(Path.cwd(), args.screen_root, args.fit_root, args.output), sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
