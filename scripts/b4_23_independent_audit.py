"""Uncached energy/Brent reconstruction of the entire finite v3 panel."""

import json
import traceback
from time import perf_counter

import numpy as np
from b4_15_independent_audit import energy
from b4_16_independent_audit import agree
from b4_19_independent_audit import relative_metrics
from b4_22_independent_audit import independent_projection, projection_conditions
from b4_23_versioned_surrogate_feasibility import (
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
    safe_hash,
    selected_entries,
    sha,
    state_specs,
    train_label,
)

from topolab.baselines import _case_system
from topolab.simp import build_density_filter


def event_prefix(output, name, revision):
    events = [
        json.loads(line) for line in (output / (name + ".events.jsonl")).read_bytes().splitlines()
    ]
    if (
        not events
        or events[0]["event"] != "start"
        or [e["sequence"] for e in events] != list(range(len(events)))
    ):
        raise ValueError("durable prefix identity/sequence differs")
    counts = {k: {"attempted": 0, "completed": 0} for k in ("label", "fem", "projection")}
    pending = []
    plan_sha256 = plan_payload()["plan_sha256"]
    for event in events:
        if event["source_revision"] != revision or event["plan_sha256"] != plan_sha256:
            raise ValueError("durable source/plan differs")
        for kind in counts:
            if event["event"] == "before_" + kind:
                counts[kind]["attempted"] += 1
                pending.append((kind, event))
            elif event["event"] == "after_" + kind:
                if not pending:
                    raise ValueError("completion without durable before-call")
                before_kind, before = pending.pop()
                if (
                    before_kind != kind
                    or before["case_id"] != event["case_id"]
                    or before["context"] != event["context"]
                ):
                    raise ValueError("durable before/after context differs")
                counts[kind]["completed"] += 1
        if event["counts"] != counts:
            raise ValueError("durable actual counters differ")
    return events, counts, [kind for kind, _ in pending]


def expected_events(independent=False):
    events = ["start"]
    for _ in selected_entries():
        events += [
            "case_start",
            "before_label",
            "after_label",
            "before_fem",
            "after_fem",
            "before_fem",
            "after_fem",
            "anchor",
        ]
        for state in range(9):
            events += ["state_start"]
            events += ["before_projection", "after_projection"] * (1 if independent else 5)
            events += ["before_fem", "after_fem"]
            if not independent:
                events += ["central"]
            if state in (0, 4):
                for _ in range(4):
                    events += ["direction_start"]
                    for _ in range(2):
                        events += ["before_projection", "after_projection"] * (
                            1 if independent else 2
                        )
                        events += ["before_fem", "after_fem"]
                    events += ["direction"]
            events += ["state"]
        events += ["case_complete"]
    return events + ["complete"]


def journal_check(output, panel):
    events, counts, pending = event_prefix(output, "probe", panel["source_revision"])
    if (
        sha((output / "probe.events.jsonl").read_bytes()) != panel["journal_sha256"]
        or counts != panel["counts"]
        or pending
        or [e["event"] for e in events] != expected_events()
        or len(events) != 2050
    ):
        raise ValueError("complete durable attempt identity/order/hash/count differs")
    ids = [e.case.case_id for e in selected_entries()]
    if [e["case_id"] for e in events if e["event"] == "case_start"] != ids:
        raise ValueError("durable case population differs")
    for label, setup in zip(panel["labels"], panel["setup"], strict=True):
        cid = label["case_id"]
        subset = [e for e in events if e.get("case_id") == cid]
        rows = [r for r in panel["rows"] if r["case_id"] == cid]
        if (
            next(e["result"] for e in subset if e["event"] == "after_label")
            != {k: label[k] for k in ("artifact", "normalizer", "anchor", "stored_physical")}
            or next(e["result"] for e in subset if e["event"] == "anchor")
            != {"label": label, "setup": setup}
            or [e["result"] for e in subset if e["event"] == "state"] != rows
            or [e["result"] for e in subset if e["event"] == "central"]
            != [{**r, "differences": []} for r in rows]
            or [e["result"] for e in subset if e["event"] == "direction"]
            != [d for r in rows for d in r["differences"]]
        ):
            raise ValueError("durable numerical prefix differs from full panel")
        for state in ("stored", "continuous"):
            event = next(
                e for e in subset if e["event"] == "after_fem" and e["context"]["state"] == state
            )
            rho = np.asarray(label[state + "_physical"], dtype="<f8")
            if (
                event["context"]
                != {
                    "state": state,
                    "normalizer": label["normalizer"],
                    "physical": rho.tolist(),
                    "physical_sha256": sha(rho.tobytes()),
                }
                or event["result"]["compliance"] != label[state + "_compliance"]
            ):
                raise ValueError("durable anchor FEM differs")
        for row in rows:
            state = row["state"]
            raw = np.asarray(row["raw"], dtype="<f8")
            calls = [
                e
                for e in subset
                if e["event"] == "after_projection" and e["context"]["state"] == state
            ]
            fem = [
                e for e in subset if e["event"] == "after_fem" and e["context"]["state"] == state
            ]
            central = {k: row[k] for k in ("design", "physical", "free", "projection")}
            if calls[0]["context"] != {
                "state": state,
                "kind": "direct",
                "raw_sha256": sha(raw.tobytes()),
            } or calls[0]["result"] != {
                "value": row["surrogate"],
                "gradient": row["gradient"],
                **central,
            }:
                raise ValueError("durable direct root/gradient differs")
            for j in range(3):
                call = calls[j + 1]
                if (
                    call["context"]
                    != {
                        "state": state,
                        "kind": "torch",
                        "repeat": j,
                        "raw_sha256": sha(raw.tobytes()),
                    }
                    or call["result"]["value"] != row["repeat_values"][j]
                    or call["result"]["timing"] != row["timings"][j]
                    or float(np.max(abs(np.asarray(call["result"]["gradient"]) - row["gradient"])))
                    > row["repeat_gradient_max_difference"]
                ):
                    raise ValueError("durable complete Torch timing/gradient differs")

            def exact_calls(root_call, fem_call, x, physics, value, context, label=label):
                if (
                    root_call["context"]
                    != {
                        **context,
                        "kind": "exact_root",
                        "raw_sha256": sha(np.asarray(x, dtype="<f8").tobytes()),
                    }
                    or root_call["result"] != physics
                    or fem_call["context"]
                    != {
                        **context,
                        "kind": "exact_fem",
                        "normalizer": label["normalizer"],
                        "physical": physics["physical"],
                        "physical_sha256": sha(
                            np.asarray(physics["physical"], dtype="<f8").tobytes()
                        ),
                    }
                    or fem_call["result"]["compliance"] / label["normalizer"] != value
                ):
                    raise ValueError("durable exact root/FEM context differs")

            exact_calls(calls[4], fem[0], raw, row["physics"], row["exact"], {"state": state})
            for j, item in enumerate(row["differences"]):
                i = np.arange(1, raw.size + 1)
                d = np.sin(0.37 * i) if item["direction"] == "sine" else np.cos(0.13 * i)
                d /= max(abs(d))
                for k, sign in enumerate((1, -1)):
                    side = item["sides"][k]
                    x = raw + sign * item["step"] * d
                    context = {
                        "state": state,
                        "direction": item["direction"],
                        "step": item["step"],
                        "sign": sign,
                    }
                    call = calls[5 + j * 4 + k * 2]
                    if call["context"] != {
                        **context,
                        "kind": "side",
                        "raw_sha256": sha(np.asarray(x, dtype="<f8").tobytes()),
                    } or call["result"] != {
                        "value": side["surrogate"],
                        "gradient": side["gradient"],
                        **{k: side["physics"][k] for k in ("design", "physical", "free")},
                        "projection": side["projection"],
                    }:
                        raise ValueError("durable side root/value differs")
                    exact_calls(
                        calls[6 + j * 4 + k * 2],
                        fem[1 + j * 2 + k],
                        x,
                        side["physics"],
                        side["exact"],
                        context,
                    )
    return len(events)


def project(case, operator, raw, journal, cid, context):
    return journal.invoke(
        "projection",
        cid,
        {**context, "raw_sha256": sha(np.asarray(raw, dtype="<f8").tobytes())},
        lambda: independent_projection(case, operator, raw),
        lambda r: {"projection": r[-1]},
    )


def solve(case, rho, mesh, loads, constrained, journal, cid, context, normalizer):
    return journal.invoke(
        "fem",
        cid,
        {
            **context,
            "normalizer": normalizer,
            "physical": rho.tolist(),
            "physical_sha256": sha(np.asarray(rho, dtype="<f8").tobytes()),
        },
        lambda: energy(case, rho, mesh, loads, constrained),
        lambda r: {"compliance": r[0], "sensitivity": r[1].tolist()},
    )


def physics_conditions(actual, design, physical, free, info):
    return projection_conditions(actual["projection"], info) + [
        bool(np.allclose(actual["design"], design, rtol=0, atol=2e-11)),
        bool(np.allclose(actual["physical"], physical, rtol=0, atol=2e-11)),
        bool(np.array_equal(actual["free"], free)),
    ]


def audit(panel, data, index, journal, started):
    entries = selected_entries()
    ids = [e.case.case_id for e in entries]
    if (
        panel["plan"] != plan_payload()
        or [r["case_id"] for r in panel["labels"]] != ids
        or [r["case_id"] for r in panel["setup"]] != ids
        or [(r["case_id"], r["state"]) for r in panel["rows"]]
        != [(cid, j) for cid in ids for j in range(9)]
        or panel["counts"]
        != {
            k: {"attempted": n, "completed": n}
            for k, n in (("label", 8), ("fem", 216), ("projection", 616))
        }
        or panel["fits"]
        or panel["new_labels"]
        or panel["final_access"]
        or panel["repaired_gate"]
        or not panel["old_fresh_sealed"]
    ):
        raise ValueError("complete frozen panel population/boundary differs")
    checks, local, errors, exact_errors = [], [], [], []
    conditions, rejected, crossings = 0, 0, 0
    for number, (entry, label, setup) in enumerate(
        zip(entries, panel["labels"], panel["setup"], strict=True)
    ):
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
            label["artifact"] != artifact
            or label["normalizer"] != normalizer
            or not np.array_equal(anchor, label["anchor"])
        ):
            raise ValueError("training origin/constant denominator differs")
        mesh, loads, constrained = _case_system(entry.case)
        filt = build_density_filter(mesh, entry.case.problem.optimization.filter_radius)
        operator = filt.matrix.multiply((1 / filt.row_sums)[:, None]).tocsr()
        physical = np.asarray(operator @ anchor)
        stored = physical.astype(np.float32).astype(np.float64)
        cs = solve(
            entry.case,
            stored,
            mesh,
            loads,
            constrained,
            journal,
            cid,
            {"state": "stored"},
            normalizer,
        )
        cc = solve(
            entry.case,
            physical,
            mesh,
            loads,
            constrained,
            journal,
            cid,
            {"state": "continuous"},
            normalizer,
        )
        signed = np.asarray(operator.T @ cc[1]) / normalizer
        intercept = cc[0] / normalizer
        old_rejects = not bool(np.isclose(cc[0], normalizer, rtol=1e-9, atol=0))
        rejected += old_rejects
        arrays = [
            anchor,
            signed,
            filt.row_sums,
            filt.matrix.data,
            filt.matrix.indices,
            filt.matrix.indptr,
        ]
        if setup["retained_array_bytes"] != sum(a.nbytes for a in arrays) or any(
            not np.isfinite(setup[k]) or setup[k] <= 0 for k in ("wall_seconds", "cpu_seconds")
        ):
            raise ValueError("complete preparation bytes/timer differs")
        checks.extend(
            [
                bool(np.array_equal(stored, record.stored.physical_density)),
                bool(np.array_equal(label["stored_physical"], stored)),
                bool(np.allclose(label["continuous_physical"], physical, rtol=0, atol=2e-11)),
                bool(np.isclose(cs[0], normalizer, rtol=1e-9, atol=0)),
                bool(np.isclose(cs[0], label["stored_compliance"], rtol=1e-9, atol=0)),
                bool(np.isclose(cc[0], label["continuous_compliance"], rtol=1e-9, atol=0)),
                bool(np.isclose(intercept, label["intercept"], rtol=1e-9, atol=1e-10)),
                bool(np.allclose(signed, label["design_gradient"], rtol=1e-9, atol=1e-10)),
                old_rejects == label["old_equality_rejects_new_anchor"],
            ]
        )
        journal.emit("anchor", case_id=cid, result={"intercept": intercept})
        i = np.arange(1, anchor.size + 1)
        for j, spec in enumerate(state_specs()):
            check_budget(started)
            journal.emit("state_start", case_id=cid, state=j)
            row = panel["rows"][number * 9 + j]
            region, amplitude, name, sign = spec
            d = np.sin(0.37 * i) if name == "sine" else np.cos(0.13 * i)
            d /= max(abs(d))
            raw = (
                np.full(anchor.size, entry.case.problem.optimization.volume_fraction)
                if region == "uniform"
                else np.clip(anchor + sign * amplitude * d, 5e-4, 1 - 5e-4)
            )
            if (
                row["spec"] != list(spec)
                or row["scale"] != ("small" if anchor.size == 216 else "large")
                or not np.array_equal(raw, row["raw"])
            ):
                raise ValueError("fixed fixture/order/scale differs")
            design, rho, free, weights, info = project(
                entry.case, operator, raw, journal, cid, {"state": j, "kind": "central"}
            )
            result = solve(
                entry.case,
                rho,
                mesh,
                loads,
                constrained,
                journal,
                cid,
                {"state": j, "kind": "central"},
                normalizer,
            )
            filtered = np.asarray(operator.T @ result[1]) / normalizer
            exact_gradient = np.where(
                free, filtered - weights * sum(filtered[free]) / sum(weights[free]), 0
            )
            gradient = np.where(free, signed - weights * sum(signed[free]) / sum(weights[free]), 0)
            value = intercept + float(signed @ (design - anchor))
            exact = result[0] / normalizer
            checks.extend(projection_conditions(row["projection"], info))
            checks.extend(physics_conditions(row["physics"], design, rho, free, info))
            checks.extend(
                [
                    bool(np.allclose(row["design"], design, rtol=0, atol=2e-11)),
                    bool(np.allclose(row["physical"], rho, rtol=0, atol=2e-11)),
                    bool(np.array_equal(row["free"], free)),
                    bool(np.isclose(row["surrogate"], value, rtol=1e-9, atol=1e-10)),
                    bool(np.isclose(row["exact"], exact, rtol=1e-9, atol=0)),
                    bool(np.allclose(row["gradient"], gradient, rtol=1e-9, atol=1e-10)),
                    bool(np.allclose(row["exact_gradient"], exact_gradient, rtol=1e-9, atol=1e-10)),
                    row["volume_error"] <= 1e-12,
                    abs(row["gradient_shift_sum"]) <= 1e-10,
                    row["repeat_values"] == [row["surrogate"]] * 3,
                    row["repeat_gradient_max_difference"] == 0,
                ]
            )
            conditions += agree(
                {
                    "maximum_design_distance": float(
                        np.max(abs(np.asarray(row["design"]) - anchor))
                    ),
                    "maximum_physical_distance": float(
                        np.max(abs(np.asarray(row["physical"]) - stored))
                    ),
                },
                {k: row[k] for k in ("maximum_design_distance", "maximum_physical_distance")},
            )
            if [t["repeat"] for t in row["timings"]] != [0, 1, 2] or any(
                not np.isfinite(t[k]) or t[k] <= 0
                for t in row["timings"]
                for k in ("wall_seconds", "cpu_seconds")
            ):
                raise ValueError("complete timing population differs")
            metrics = relative_metrics(
                row["surrogate"],
                row["exact"],
                np.asarray(row["gradient"]),
                np.asarray(row["exact_gradient"]),
            )
            conditions += agree(metrics, row["fidelity"])
            accepted = (
                metrics["normalized_value_error"] <= 1e-4
                and metrics["increment_relative_error"] <= 0.25
                and metrics["gradient_relative_error"] <= 0.25
                and metrics["increment_sign_agrees"]
            )
            if row["local_pass"] != (accepted if region == "local" else None):
                raise ValueError("local acceptance differs")
            if region == "local":
                local.append(accepted)
            expected = (
                [(n, h) for n in ("sine", "cosine") for h in (1e-4, 2e-4)] if j in (0, 4) else []
            )
            if [(d["direction"], d["step"]) for d in row["differences"]] != expected:
                raise ValueError("complete directional population differs")
            for item in row["differences"]:
                journal.emit(
                    "direction_start",
                    case_id=cid,
                    state=j,
                    direction=item["direction"],
                    step=item["step"],
                )
                d = np.sin(0.37 * i) if item["direction"] == "sine" else np.cos(0.13 * i)
                d /= max(abs(d))
                h = item["step"]
                for sign, side in zip((1, -1), item["sides"], strict=True):
                    context = {
                        "state": j,
                        "kind": "side",
                        "direction": item["direction"],
                        "step": h,
                        "sign": sign,
                    }
                    xd, xr, xf, xw, side_info = project(
                        entry.case, operator, raw + sign * h * d, journal, cid, context
                    )
                    side_result = solve(
                        entry.case, xr, mesh, loads, constrained, journal, cid, context, normalizer
                    )
                    side_gradient = np.where(xf, signed - xw * sum(signed[xf]) / sum(xw[xf]), 0)
                    checks.extend(projection_conditions(side["projection"], side_info))
                    checks.extend(physics_conditions(side["physics"], xd, xr, xf, side_info))
                    checks.extend(
                        [
                            bool(
                                np.isclose(
                                    side["surrogate"],
                                    intercept + float(signed @ (xd - anchor)),
                                    rtol=1e-9,
                                    atol=1e-10,
                                )
                            )
                            and bool(
                                np.allclose(side["gradient"], side_gradient, rtol=1e-9, atol=1e-10)
                            ),
                            bool(
                                np.isclose(
                                    side["exact"], side_result[0] / normalizer, rtol=1e-9, atol=0
                                )
                            ),
                            bool(np.array_equal(side["free"], xf)),
                        ]
                    )
                plus, minus = item["sides"]
                fd = (plus["surrogate"] - minus["surrogate"]) / (2 * h)
                derivative = float(np.asarray(row["gradient"]) @ d)
                error = abs(fd - derivative) / max(abs(fd), abs(derivative), 1e-8)
                stable = all(np.array_equal(s["free"], row["free"]) for s in item["sides"])
                reconstruction = {
                    "surrogate_fd": fd,
                    "surrogate_derivative": derivative,
                    "surrogate_error": error,
                    "same_active_set": stable,
                    "exact_fd": (plus["exact"] - minus["exact"]) / (2 * h),
                    "exact_derivative": float(np.asarray(row["exact_gradient"]) @ d),
                }
                conditions += agree(reconstruction, {k: item[k] for k in reconstruction})
                checks.extend([stable, error <= 1e-4])
                errors.append(error)
                crossings += not stable
                exact_errors.append(
                    abs(reconstruction["exact_fd"] - reconstruction["exact_derivative"])
                    / max(
                        abs(reconstruction["exact_fd"]),
                        abs(reconstruction["exact_derivative"]),
                        1e-8,
                    )
                )
                journal.emit("direction", case_id=cid, state=j, result=reconstruction)
            journal.emit("state", case_id=cid, result={"state": j, "value": value, "exact": exact})
        journal.emit("case_complete", case_id=cid)
    if (
        len(checks) != 3976
        or conditions != 960
        or journal.counts
        != {
            k: {"attempted": n, "completed": n}
            for k, n in (("label", 8), ("fem", 216), ("projection", 200))
        }
    ):
        raise ValueError("complete independent condition/call population differs")
    return {
        "passed": True,
        "metadata_only": False,
        "integrity_passed": all(checks),
        "numerical_conditions": len(checks),
        "failed_numerical_conditions": sum(not c for c in checks),
        "condition_results": [bool(c) for c in checks],
        "failed_condition_indices": [i for i, c in enumerate(checks) if not c],
        "arithmetic_conditions": conditions,
        "local_states": len(local),
        "local_states_passed": sum(local),
        "local_fidelity_passed": all(local),
        "directional_rows": len(errors),
        "crossing_directional_rows": crossings,
        "maximum_surrogate_directional_error": max(errors),
        "maximum_exact_directional_error_diagnostic": max(exact_errors),
        "old_equality_rejects_new_anchors": rejected,
        "measurements": 216,
        "central_states": 72,
        "cases": 8,
        "counts": journal.counts,
        "total_solver_calls": 432,
        "total_projection_calls": 816,
        "probe_sha256": sha(canonical(panel)),
        "plan_sha256": plan_payload()["plan_sha256"],
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
    }


def abort_audit(output, revision):
    command = read(output, "audit_receipts/probe_command.json")
    if command["exit_code"] == 0:
        raise ValueError("absent panel after successful command")
    safe_hash(output, command["profile"], command["profile_sha256"])
    safe_hash(output, command["log"], command["log_sha256"])
    events, counts, pending = event_prefix(output, "probe", revision)
    return {
        "passed": True,
        "metadata_only": True,
        "integrity_passed": False,
        "local_fidelity_passed": None,
        "actual_probe_counts": counts,
        "pending_operations": pending,
        "actual_completed_cases": sum(e["event"] == "case_complete" for e in events),
        "actual_completed_states": sum(e["event"] == "state" for e in events),
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


def independent_proxy(panel, charge):
    maximum = [
        max(t["wall_seconds"] for r in panel["rows"] if r["scale"] == s for t in r["timings"])
        for s in ("small", "large")
    ]
    scales = {r["case_id"]: r["scale"] for r in panel["rows"]}
    preparation = [
        max(r["wall_seconds"] for r in panel["setup"] if scales[r["case_id"]] == s)
        for s in ("small", "large")
    ]
    sizes = [
        max(r["retained_array_bytes"] for r in panel["setup"] if scales[r["case_id"]] == s)
        for s in ("small", "large")
    ]
    forward = 750 * (432 * maximum[0] + 76 * maximum[1])
    setup = 3.75 * (432 * preparation[0] + 76 * preparation[1])
    return {
        "additional_surrogate_seconds": forward,
        "full_population_preparation_seconds": setup,
        "population_retained_array_bytes_estimate": 432 * sizes[0] + 76 * sizes[1],
        "total_prospective_seconds": forward
        + setup
        + 3870.204341
        + 84.33
        + 55.99
        + 112.34
        + 86.13
        + 73.93
        + 100.30
        + 90.27
        + 104.62
        + charge,
    }


def main(argv=None):
    started = perf_counter()
    args, root, data, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    if (output / "independent_audit.json").exists():
        raise ValueError("refuses to overwrite independent audit")
    revision = execution_release(output)
    journal = Journal(output / "independent.events.jsonl", revision)
    try:
        index = check_inputs(root, data)
        if not (output / "probe.json").exists():
            result = abort_audit(output, revision)
            journal.emit("metadata_abort_audit", result=result)
        else:
            panel = read(output, "probe.json")
            if panel["source_revision"] != revision:
                raise ValueError("execution source differs")
            events = journal_check(output, panel)
            result = audit(panel, data, index, journal, started)
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
                    k: result[k]
                    for k in ("integrity_passed", "local_fidelity_passed", "metadata_only")
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
