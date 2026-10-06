"""Independent uncached anchor FEM and Brent/affine arithmetic, with durable calls."""

import json
import traceback
from time import perf_counter

import numpy as np
from b4_15_independent_audit import energy
from b4_22_stable_projection_correctness import (
    Journal,
    arguments,
    canonical,
    check_budget,
    check_inputs,
    execution_release,
    label_metadata,
    peak_rss,
    plan_payload,
    read,
    selected_entries,
    sha,
    train_label,
)
from scipy.optimize import brentq

from topolab.baselines import _case_system
from topolab.simp import build_density_filter


def independent_projection(case, operator, raw):
    weights = np.asarray(operator.sum(axis=0)).ravel() / raw.size
    minimum = case.problem.optimization.minimum_density
    volume = case.problem.optimization.volume_fraction
    offset = brentq(
        lambda s: float(weights @ np.clip(raw + s, minimum, 1)) - volume, -1, 1, xtol=1e-14
    )
    shifted = raw + offset
    if np.any(np.minimum(abs(shifted - minimum), abs(shifted - 1)) <= 1e-10):
        raise ValueError("independent projection at a kink")
    design = np.clip(shifted, minimum, 1)
    free = (shifted > minimum) & (shifted < 1)
    physical = np.asarray(operator @ design)
    info = {
        "offset": offset,
        "weighted_volume_residual": float(weights @ design) - volume,
        "physical_volume_residual": float(physical.mean()) - volume,
        "kink_margin": float(np.min(np.minimum(abs(shifted - minimum), abs(shifted - 1)))),
    }
    return design, physical, free, weights, info


def projection_conditions(actual, expected):
    if actual.keys() != expected.keys() or not all(np.isfinite(v) for v in actual.values()):
        raise ValueError("finite complete saved projection scalars required")
    return [
        abs(actual["offset"] - expected["offset"]) <= 2e-11,
        abs(actual["weighted_volume_residual"] - expected["weighted_volume_residual"]) <= 1e-12,
        abs(actual["physical_volume_residual"] - expected["physical_volume_residual"]) <= 1e-12,
        abs(actual["kink_margin"] - expected["kink_margin"]) <= 2e-11,
        abs(actual["weighted_volume_residual"]) <= 1e-12
        and abs(actual["physical_volume_residual"]) <= 1e-12
        and actual["kink_margin"] > 1e-10,
    ]


def project_independent(case, operator, raw, journal, cid, context):
    return journal.invoke(
        "projection",
        cid,
        {**context, "raw_sha256": sha(np.asarray(raw, dtype="<f8").tobytes())},
        lambda: independent_projection(case, operator, raw),
        lambda result: {"projection": result[-1]},
    )


def event_prefix(output, name, revision):
    path = output / (name + ".events.jsonl")
    events = [json.loads(line) for line in path.read_bytes().splitlines()]
    if (
        not events
        or events[0]["event"] != "start"
        or [e["sequence"] for e in events] != list(range(len(events)))
    ):
        raise ValueError("durable prefix identity/sequence differs")
    counts = {k: {"attempted": 0, "completed": 0} for k in ("label", "fem", "projection")}
    pending = []
    for event in events:
        if (
            event["source_revision"] != revision
            or event["plan_sha256"] != plan_payload()["plan_sha256"]
        ):
            raise ValueError("durable source/plan differs")
        for kind in counts:
            if event["event"] == "before_" + kind:
                counts[kind]["attempted"] += 1
                pending.append((kind, event))
            elif event["event"] == "after_" + kind:
                if not pending:
                    raise ValueError("completion without durable before-call")
                prior_kind, before = pending.pop()
                if (
                    prior_kind != kind
                    or before["case_id"] != event["case_id"]
                    or before["context"] != event["context"]
                ):
                    raise ValueError("durable before/after context differs")
                counts[kind]["completed"] += 1
        if event["counts"] != counts:
            raise ValueError("durable actual counters differ")
    return events, counts, [kind for kind, _ in pending]


def journal_check(output, probe):
    events, counts, pending = event_prefix(output, "probe", probe["source_revision"])
    if (
        sha((output / "probe.events.jsonl").read_bytes()) != probe["journal_sha256"]
        or events[-1]["event"] != "complete"
        or counts != probe["counts"]
        or pending
        or len(events) != 554
    ):
        raise ValueError("complete durable attempt identity/hash/count differs")
    expected = ["start"]
    for _ in selected_entries():
        expected += [
            "case_start",
            "before_label",
            "after_label",
            "before_fem",
            "after_fem",
            "before_fem",
            "after_fem",
            "anchor",
        ]
        for _ in range(2):
            expected += [
                "fixture_start",
                "before_projection",
                "after_projection",
                "before_projection",
                "after_projection",
            ]
            for _ in range(4):
                expected += [
                    "direction_start",
                    "before_projection",
                    "after_projection",
                    "before_projection",
                    "after_projection",
                    "direction",
                ]
            expected += ["fixture"]
        expected += ["case_complete"]
    expected += ["complete"]
    if [e["event"] for e in events] != expected:
        raise ValueError("durable complete operation order differs")
    for case in probe["cases"]:
        subset = [e for e in events if e.get("case_id") == case["case_id"]]
        if (
            len(subset) != 69
            or next(e["result"] for e in subset if e["event"] == "after_label")
            != {k: case[k] for k in ("artifact", "normalizer", "anchor", "stored_physical")}
            or next(e["result"] for e in subset if e["event"] == "anchor") != {**case, "rows": []}
            or [e["result"] for e in subset if e["event"] == "fixture"] != case["rows"]
            or [e["result"] for e in subset if e["event"] == "direction"]
            != [d for row in case["rows"] for d in row["differences"]]
        ):
            raise ValueError("durable numerical prefix differs from full panel")
        for state in ("stored", "continuous"):
            event = next(
                e for e in subset if e["event"] == "after_fem" and e["context"]["state"] == state
            )
            rho = np.asarray(case[state + "_physical"], dtype="<f8")
            if (
                event["context"]["normalizer"] != case["normalizer"]
                or event["context"]["physical"] != rho.tolist()
                or event["context"]["physical_sha256"] != sha(rho.tobytes())
                or event["result"]["compliance"] != case[state + "_compliance"]
            ):
                raise ValueError("durable FEM result/context differs")
        for row in case["rows"]:
            calls = [
                e
                for e in subset
                if e["event"] == "after_projection" and e["context"]["state"] == row["state"]
            ]
            if len(calls) != 10:
                raise ValueError("durable projection population differs")
            raw = np.asarray(row["raw"], dtype="<f8")
            if (
                calls[0]["context"]
                != {"state": row["state"], "kind": "direct", "raw_sha256": sha(raw.tobytes())}
                or calls[0]["result"] != {"value": row["value"], "projection": row["projection"]}
                or calls[1]["context"]
                != {"state": row["state"], "kind": "torch", "raw_sha256": sha(raw.tobytes())}
                or calls[1]["result"]
                != {"value": row["torch_value"], "gradient": row["torch_gradient"]}
            ):
                raise ValueError("durable direct/Torch root result differs")
            for j, item in enumerate(row["differences"]):
                i = np.arange(1, raw.size + 1)
                d = np.sin(0.37 * i) if item["direction"] == "sine" else np.cos(0.13 * i)
                d /= max(abs(d))
                for side, sign in enumerate((1, -1)):
                    call = calls[2 + j * 2 + side]
                    x = raw + sign * item["step"] * d
                    context = {
                        "state": row["state"],
                        "kind": "side",
                        "direction": item["direction"],
                        "step": item["step"],
                        "sign": sign,
                        "raw_sha256": sha(np.asarray(x, dtype="<f8").tobytes()),
                    }
                    if call["context"] != context or call["result"] != {
                        "value": item["values"][side],
                        "projection": item["projections"][side],
                    }:
                        raise ValueError("durable side root/offset/value differs")
    return len(events)


def audit(probe, data, index, journal, started):
    entries = selected_entries()
    if (
        probe["plan"] != plan_payload()
        or [r["case_id"] for r in probe["cases"]] != [e.case.case_id for e in entries]
        or probe["counts"]
        != {
            "label": {"attempted": 8, "completed": 8},
            "fem": {"attempted": 16, "completed": 16},
            "projection": {"attempted": 160, "completed": 160},
        }
        or probe["fits"]
        or probe["final_access"]
        or probe["repaired_gate"]
        or not probe["old_fresh_sealed"]
    ):
        raise ValueError("frozen correctness population/boundary differs")
    checks, errors, clipped, free_count, rejected = [], [], 0, 0, 0
    gaps = []
    for entry, case in zip(entries, probe["cases"], strict=True):
        check_budget(started)
        cid = entry.case.case_id
        journal.emit("case_start", case_id=cid)
        record, artifact = journal.invoke(
            "label",
            cid,
            {"role": "train", "training_set": "expanded"},
            lambda entry=entry: train_label(data, index, entry),
            label_metadata,
        )
        anchor = np.asarray(record.stored.design_density)
        normalizer = record.stored.compliance
        if (
            case["artifact"] != artifact
            or case["normalizer"] != normalizer
            or not np.array_equal(
                case["anchor"],
                anchor,
            )
        ):
            raise ValueError("training origin/constant denominator differs")
        mesh, loads, constrained = _case_system(entry.case)
        filt = build_density_filter(mesh, entry.case.problem.optimization.filter_radius)
        operator = filt.matrix.multiply((1 / filt.row_sums)[:, None]).tocsr()
        physical = np.asarray(operator @ anchor)
        stored = physical.astype(np.float32).astype(np.float64)
        cs, cc = [
            journal.invoke(
                "fem",
                cid,
                {
                    "state": name,
                    "normalizer": normalizer,
                    "physical": rho.tolist(),
                    "physical_sha256": sha(np.asarray(rho, dtype="<f8").tobytes()),
                },
                lambda rho=rho, case=entry.case, mesh=mesh, loads=loads, constrained=constrained: (
                    energy(case, rho, mesh, loads, constrained)
                ),
                lambda result: {"compliance": result[0], "sensitivity": result[1].tolist()},
            )
            for name, rho in (("stored", stored), ("continuous", physical))
        ]
        signed = np.asarray(operator.T @ cc[1]) / normalizer
        intercept = cc[0] / normalizer
        old_rejects = not bool(np.isclose(cc[0], normalizer, rtol=1e-9, atol=0))
        rejected += old_rejects
        gaps.append(intercept - 1)
        checks.extend(
            [
                bool(np.array_equal(stored, record.stored.physical_density)),
                bool(np.array_equal(case["stored_physical"], stored)),
                bool(np.allclose(case["continuous_physical"], physical, rtol=0, atol=2e-11)),
                bool(np.isclose(cs[0], normalizer, rtol=1e-9, atol=0)),
                bool(np.isclose(cs[0], case["stored_compliance"], rtol=1e-9, atol=0)),
                bool(np.isclose(cc[0], case["continuous_compliance"], rtol=1e-9, atol=0)),
                bool(np.isclose(intercept, case["intercept"], rtol=1e-9, atol=1e-10)),
                bool(np.allclose(signed, case["design_gradient"], rtol=1e-9, atol=1e-10)),
                case["old_equality_rejects_new_anchor"] == old_rejects,
            ]
        )
        if [r["state"] for r in case["rows"]] != ["interior", "clipped"]:
            raise ValueError("fixed ordered fixture population differs")
        i = np.arange(1, anchor.size + 1)
        for row in case["rows"]:
            check_budget(started)
            raw = (
                entry.case.problem.optimization.volume_fraction
                + 0.02 * np.sin(0.37 * i)
                + 0.01 * np.cos(0.13 * i)
                if row["state"] == "interior"
                else np.resize(np.array([0.02, 0.5, 0.98]), i.size)
            )
            if not np.array_equal(raw, row["raw"]):
                raise ValueError("frozen synthetic fixture differs")
            design, rho, free, weights, info = project_independent(
                entry.case, operator, raw, journal, cid, {"state": row["state"], "kind": "direct"}
            )
            checks.extend(projection_conditions(row["projection"], info))
            gradient = np.where(free, signed - weights * sum(signed[free]) / sum(weights[free]), 0)
            value = intercept + float(signed @ (design - anchor))
            clipped += int((~free).sum())
            free_count += int(free.sum())
            checks.extend(
                [
                    bool(np.allclose(row["design"], design, rtol=0, atol=2e-11)),
                    bool(np.allclose(row["physical"], rho, rtol=0, atol=2e-11)),
                    bool(np.array_equal(row["free"], free)),
                    bool(np.isclose(row["value"], value, rtol=1e-9, atol=1e-10)),
                    bool(np.allclose(row["gradient"], gradient, rtol=1e-9, atol=1e-10)),
                    bool(np.isclose(row["torch_value"], row["value"], rtol=0, atol=0)),
                    bool(np.array_equal(row["torch_gradient"], row["gradient"])),
                    abs(float(rho.mean()) - entry.case.problem.optimization.volume_fraction)
                    <= 1e-12,
                    abs(float(gradient.sum())) <= 1e-10,
                ]
            )
            if [(d["direction"], d["step"]) for d in row["differences"]] != [
                (name, h) for name in ("sine", "cosine") for h in (1e-4, 2e-4)
            ]:
                raise ValueError("fixed directional population differs")
            for item in row["differences"]:
                d = np.sin(0.37 * i) if item["direction"] == "sine" else np.cos(0.13 * i)
                d /= max(abs(d))
                if len(item["projections"]) != 2:
                    raise ValueError("two saved side roots required")
                for side, (sign, value_side, free_side) in enumerate(
                    zip(
                        (1, -1),
                        item["values"],
                        item["free"],
                        strict=True,
                    )
                ):
                    xd, xr, xf, _, side_info = project_independent(
                        entry.case,
                        operator,
                        raw + sign * item["step"] * d,
                        journal,
                        cid,
                        {
                            "state": row["state"],
                            "kind": "side",
                            "direction": item["direction"],
                            "step": item["step"],
                            "sign": sign,
                        },
                    )
                    checks.extend(projection_conditions(item["projections"][side], side_info))
                    checks.extend(
                        [
                            bool(
                                np.isclose(
                                    value_side,
                                    intercept + float(signed @ (xd - anchor)),
                                    rtol=1e-9,
                                    atol=1e-10,
                                )
                            ),
                            bool(np.array_equal(free_side, xf)),
                            bool(np.array_equal(xf, free)),
                            abs(float(xr.mean()) - entry.case.problem.optimization.volume_fraction)
                            <= 1e-12,
                        ]
                    )
                fd = (item["values"][0] - item["values"][1]) / (2 * item["step"])
                derivative = float(np.asarray(row["gradient"]) @ d)
                error = abs(fd - derivative) / max(abs(fd), abs(derivative), 1e-8)
                checks.extend(
                    [
                        item["fd"] == fd,
                        item["derivative"] == derivative,
                        item["error"] == error,
                        error <= 1e-4,
                    ]
                )
                errors.append(error)
            journal.emit("fixture", case_id=cid, result={"state": row["state"], "value": value})
        journal.emit("case_complete", case_id=cid)
    return {
        "passed": True,
        "metadata_only": False,
        "correctness_passed": all(checks) and clipped > 0 and free_count > 0,
        "numerical_conditions": len(checks),
        "failed_numerical_conditions": sum(not c for c in checks),
        "cases": len(entries),
        "fixtures": 16,
        "directional_rows": len(errors),
        "maximum_directional_error": max(errors),
        "clipped_entries": clipped,
        "free_entries": free_count,
        "old_equality_rejects_new_anchors": rejected,
        "normalized_anchor_gaps": gaps,
        "maximum_absolute_normalized_anchor_gap": max(abs(g) for g in gaps),
        "counts": journal.counts,
        "total_solver_calls": 32,
        "total_projection_calls": 304,
        "probe_sha256": sha(canonical(probe)),
        "plan_sha256": plan_payload()["plan_sha256"],
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
    }


def abort_audit(output, revision):
    from b4_22_stable_projection_correctness import safe_hash

    command = read(output, "audit_receipts/probe_command.json")
    if command["exit_code"] == 0:
        raise ValueError("absent panel after successful command")
    safe_hash(output, command["profile"], command["profile_sha256"])
    safe_hash(output, command["log"], command["log_sha256"])
    events, counts, pending = event_prefix(output, "probe", revision)
    return {
        "passed": True,
        "metadata_only": True,
        "correctness_passed": False,
        "actual_probe_counts": counts,
        "pending_operations": pending,
        "actual_completed_cases": sum(e["event"] == "case_complete" for e in events),
        "actual_completed_fixtures": sum(e["event"] == "fixture" for e in events),
        "actual_completed_directional_rows": sum(e["event"] == "direction" for e in events),
        "actual_failed_context": next(
            (e.get("context") for e in reversed(events) if e["event"] == "failure"), None
        ),
        "full_panel_directional_error": None,
        "numerical_conditions": None,
        "failed_numerical_conditions": None,
        "probe_sha256": None,
        "probe_journal_sha256": sha((output / "probe.events.jsonl").read_bytes()),
        "new_label_fem_projection_calls": 0,
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
    }


def main(argv=None):
    started = perf_counter()
    args, root, data, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    revision = execution_release(output)
    journal = Journal(output / "independent.events.jsonl", revision)
    try:
        index = check_inputs(root, data)
        if not (output / "probe.json").exists():
            result = abort_audit(output, revision)
            journal.emit("metadata_abort_audit", result=result)
        else:
            probe = read(output, "probe.json")
            if probe["source_revision"] != revision:
                raise ValueError("execution source differs")
            events = journal_check(output, probe)
            result = audit(probe, data, index, journal, started)
            result["durable_probe_events"] = events
        check_inputs(root, data)
        check_budget(started)
        result.update(
            source_revision=revision,
            charged_seconds=perf_counter() - started + 10,
            peak_rss_bytes=peak_rss(),
        )
        journal.emit("complete")
        result["journal_sha256"] = sha((output / "independent.events.jsonl").read_bytes())
        with (output / "independent_audit.json").open("xb") as stream:
            stream.write(canonical(result))
        print(
            canonical(
                {
                    "correctness_passed": result["correctness_passed"],
                    "metadata_only": result["metadata_only"],
                }
            ).decode(),
            end="",
        )
    except Exception as error:
        journal.emit(
            "abort",
            error_type=type(error).__name__,
            error=str(error),
            traceback=traceback.format_exc(),
        )
        raise
    finally:
        journal.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
