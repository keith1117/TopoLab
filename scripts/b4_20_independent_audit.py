"""Independent uncached anchor FEM and Brent/affine arithmetic, with durable calls."""

import json
import traceback
from time import perf_counter

import numpy as np
from b4_15_independent_audit import energy
from b4_20_surrogate_correctness import (
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
    return design, np.asarray(operator @ design), free, weights


def journal_check(output, probe):
    events = [
        json.loads(line) for line in (output / "probe.events.jsonl").read_bytes().splitlines()
    ]
    if (
        sha((output / "probe.events.jsonl").read_bytes()) != probe["journal_sha256"]
        or [e["sequence"] for e in events] != list(range(len(events)))
        or events[0]["event"] != "start"
        or events[-1]["event"] != "complete"
        or events[0]["source_revision"] != probe["source_revision"]
        or events[0]["plan_sha256"] != plan_payload()["plan_sha256"]
        or events[-1]["counts"] != probe["counts"]
    ):
        raise ValueError("durable attempt identity/sequence/hash differs")
    expected = (
        ["start"]
        + [
            name
            for _ in selected_entries()
            for name in (
                [
                    "case_start",
                    "before_label",
                    "after_label",
                    "before_fem",
                    "after_fem",
                    "before_fem",
                    "after_fem",
                    "anchor",
                ]
                + [
                    name
                    for _ in range(2)
                    for name in (["fixture_start"] + ["direction"] * 4 + ["fixture"])
                ]
                + ["case_complete"]
            )
        ]
        + ["complete"]
    )
    if [e["event"] for e in events] != expected:
        raise ValueError("durable before-call and completed-prefix order differs")
    counts = {k: {"attempted": 0, "completed": 0} for k in ("label", "fem")}
    pairs = []
    for event in events:
        if (
            event["source_revision"] != probe["source_revision"]
            or event["plan_sha256"] != plan_payload()["plan_sha256"]
        ):
            raise ValueError("durable event source/plan binding differs")
        for kind in ("label", "fem"):
            if event["event"] == "before_" + kind:
                counts[kind]["attempted"] += 1
                pairs.append(event)
            if event["event"] == "after_" + kind:
                before = pairs.pop()
                if before["case_id"] != event["case_id"] or before["context"] != event["context"]:
                    raise ValueError("before/after call binding differs")
                counts[kind]["completed"] += 1
        if event["counts"] != counts:
            raise ValueError("durable attempted/completed counters differ")
    for case in probe["cases"]:
        subset = [e for e in events if e.get("case_id") == case["case_id"]]
        if (
            len(subset) != 21
            or next(e["result"] for e in subset if e["event"] == "after_label")
            != {k: case[k] for k in ("artifact", "normalizer", "anchor", "stored_physical")}
            or [e["result"] for e in subset if e["event"] == "fixture"] != case["rows"]
            or [e["result"] for e in subset if e["event"] == "direction"]
            != [d for row in case["rows"] for d in row["differences"]]
        ):
            raise ValueError("durable numerical prefix differs from published panel")
        anchor_event = next(e["result"] for e in subset if e["event"] == "anchor")
        if anchor_event != {**case, "rows": []}:
            raise ValueError("durable anchor prefix differs")
        for state in ("stored", "continuous"):
            call = next(
                e for e in subset if e["event"] == "after_fem" and e["context"]["state"] == state
            )
            physical = np.asarray(case[state + "_physical"], dtype="<f8")
            if (
                call["context"]["normalizer"] != case["normalizer"]
                or call["context"]["physical"] != physical.tolist()
                or call["context"]["physical_sha256"] != sha(physical.tobytes())
                or call["result"]["compliance"] != case[state + "_compliance"]
            ):
                raise ValueError("durable anchor compliance/normalizer/density differs")
    return len(events)


def audit(probe, data, index, journal, started):
    entries = selected_entries()
    if (
        probe["plan"] != plan_payload()
        or [r["case_id"] for r in probe["cases"]] != [e.case.case_id for e in entries]
        or probe["counts"]
        != {"label": {"attempted": 8, "completed": 8}, "fem": {"attempted": 16, "completed": 16}}
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
            design, rho, free, weights = independent_projection(entry.case, operator, raw)
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
                for sign, value_side, free_side in zip(
                    (1, -1),
                    item["values"],
                    item["free"],
                    strict=True,
                ):
                    xd, xr, xf, _ = independent_projection(
                        entry.case,
                        operator,
                        raw + sign * item["step"] * d,
                    )
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
        "probe_sha256": sha(canonical(probe)),
        "plan_sha256": plan_payload()["plan_sha256"],
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
        probe = read(output, "probe.json")
        if probe["source_revision"] != revision:
            raise ValueError("execution source differs")
        events = journal_check(output, probe)
        result = audit(probe, data, index, journal, started)
        check_inputs(root, data)
        check_budget(started)
        result.update(
            source_revision=revision,
            durable_probe_events=events,
            charged_seconds=perf_counter() - started + 10,
            peak_rss_bytes=peak_rss(),
        )
        journal.emit("complete")
        result["journal_sha256"] = sha((output / "independent.events.jsonl").read_bytes())
        with (output / "independent_audit.json").open("xb") as stream:
            stream.write(canonical(result))
        print(canonical(result).decode(), end="")
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
