"""Independent raw B4.12 arithmetic audit; imports no B4.13 diagnostic helper."""

import argparse
import json
import math
from itertools import combinations
from pathlib import Path
from time import perf_counter

from b4_10_independent_audit import canonical, classify, close, qualifies, sentinel_decision, sha
from b4_11_independent_audit import certificate, costs, read
from b4_11_polish_diagnosis import peak_rss
from b4_12_independent_audit import classify_guard, fresh_decision, selection

PLAN_SHA = "165bdf5be73e3f62a719bf6931580ead53ed685f74b564aebb6dd1ecacd5094f"
VERSION = "topolab.b4_13.preservation-diagnosis.v1"


def journal(root, prefix, names, context):
    progress = read(root, prefix + "/progress.json")
    summary = read(root, prefix + "/summary.json")
    assert progress["context_sha256"] == context
    assert progress["units_sha256"] == sha(canonical(names))
    assert progress["attempted"] == progress["completed"] == len(names)
    assert progress["pending"] is None and progress["active_at"] is None
    assert not progress["resource_failed"] and not progress["integrity_failed"]
    for k in ("attempted", "completed", "head_sha256", "charged_seconds", "peak_rss_bytes"):
        assert progress[k] == summary[k]
    head, items = "0" * 64, []
    for i, name in enumerate(names):
        item = read(root, f"{prefix}/units/{i:04d}.json")
        assert (item["unit"], item["context_sha256"], item["previous_sha256"]) == (
            name,
            context,
            head,
        )
        head = sha(canonical(item))
        items.append(item["payload"])
    assert head == progress["head_sha256"]
    return items


def artifact(root, prefix, ref, kind):
    assert ref["path"] == f"artifacts/{kind}/{ref['sha256']}.json"
    value = read(root, prefix + "/" + ref["path"], ref["sha256"])
    assert len(canonical(value)) == ref["byte_size"]
    return value


def record(root, prefix, i, ref, context):
    value = read(root, f"{prefix}/recording/{i:04d}.json")
    assert value["context_sha256"] == context and value["outcome_sha256"] == ref["sha256"]
    assert value["version"] == "topolab.b4_12.recording.v1"
    assert 0 <= value["recording_seconds_before_receipt"] <= 1
    return value["recording_seconds_before_receipt"]


def recommendation(rows):
    residual = []
    for row in rows:
        if row["method"] != "P/17" or row["candidate"]["succeeded"]:
            continue
        residual.append(row)
        endpoint, original = row["endpoint"], row["before"]
        if (
            not row["triggered"]
            or row["selection"] != "endpoint"
            or row["added_updates"] != 20
            or not endpoint["converged"]
            or endpoint["quality_reasons"] != ["compliance_above_matched_uniform"]
            or original["succeeded"]
            or endpoint["compliance_ratio"] >= original["compliance_ratio"]
        ):
            return "terminal_certificate_and_cost_method_review"
    return (
        "generalist_reliability_refinement_method_review"
        if residual
        else "terminal_certificate_and_cost_method_review"
    )


def summary(rows, methods, bounds):
    strata = []
    for name in methods:
        for scale in ("small", "large"):
            for direction in ("y", "z"):
                group = [
                    r
                    for r in rows
                    if (r["method"], r["scale"], r["direction"]) == (name, scale, direction)
                ]
                strata.append(
                    {
                        "method": name,
                        "scale": scale,
                        "direction": direction,
                        **costs(group, "measured"),
                        "selected_updates": sum(r["candidate"]["iterations"] for r in group),
                        "performed_updates": sum(r["performed_iterations"] for r in group),
                        "fallback_seconds": sum(r["fallback_seconds"] for r in group),
                    }
                )
    primary = [r for r in rows if r["method"] == "P/17"]
    groups = {
        "all": primary,
        "small": [r for r in primary if r["scale"] == "small"],
        "large": [r for r in primary if r["scale"] == "large"],
        "large_y_generalist": [
            r
            for r in primary
            if r["scale"] == "large" and r["direction"] == "y" and r["route"] == "generalist"
        ],
    }
    return {
        "strata": strata,
        "fixed_primary_cost_scenarios": {
            name: {b: costs(g, b) for b in bounds} for name, g in groups.items()
        },
        "timing_totals": {
            k: math.fsum(r["timing"][k] for r in rows)
            for k in ("wall_seconds", "cpu_seconds", "legacy_phase_seconds")
        },
        "callback_totals": {
            k: math.fsum(r["callback"][k] for r in rows)
            for k in ("wall_seconds", "cpu_seconds", "bytes_written")
        },
    }


def audit_cohort(root, name, plan, report, context, started):
    cases = {c["case_id"]: c for c in plan["cases"][name]}
    assigned = plan["assignments"][name]
    names = [c + ":" + m for c, m in assigned]
    refs = journal(root, name + "/reference", list(cases), context)
    queries = journal(root, name + "/screen", names, context)
    audited = journal(
        root,
        name + "/audit",
        [
            "inputs",
            "nn_labels",
            *("reference:" + c for c in cases),
            *("screen:" + n for n in names),
        ],
        context,
    )
    journal(
        root,
        name + "/policy-audit",
        [*("reference:" + c for c in cases), *("policy:" + n for n in names)],
        context,
    )
    assert audited[0]["audited_checkpoints"] == 12 and audited[1]["audited_nn_labels"] == 528
    rows, references, pairs = [], [], []
    selected = guards = continued = preserved = 0
    for i, (cid, case) in enumerate(cases.items()):
        assert perf_counter() - started + 10 <= 120 and peak_rss() <= 1073741824
        problem = case["problem"]
        nx = problem["mesh"]["element_counts"][0]
        volume = problem["optimization"]["volume_fraction"]
        direction = problem["loads"][0]["direction"]
        prefix = name + "/reference"
        packet = artifact(root, prefix, refs[i], "outcome")
        assert (
            packet["case_id"],
            packet["policy"],
            packet["context_sha256"],
            packet["version"],
        ) == (cid, "uniform", context, plan["version"])
        attempt = packet["outcome"]["attempt"]
        ref = attempt["metrics"]["final_compliance"]
        selected += classify(case, attempt, ref)
        status = certificate(attempt["state"], ref, volume)
        assert status["succeeded"]
        references.append({"case_id": cid, **status})
        record(root, prefix, i, refs[i], context)
        panel, uniform = {}, None
        for j in range(i * 12, i * 12 + 12):
            assigned_cid, method = assigned[j]
            prefix = name + "/screen"
            packet = artifact(root, prefix, queries[j], "outcome")
            assert (
                assigned_cid,
                packet["case_id"],
                packet["policy"],
                packet["context_sha256"],
                packet["version"],
            ) == (cid, cid, method, context, plan["version"])
            out, t, cb = packet["outcome"], packet["timing"], packet["callback"]
            arm, _, seed = method.partition("/")
            route = (
                "baseline"
                if not seed
                else "specialist"
                if nx == 24 and direction == "y" and volume >= 0.55
                else "generalist"
            )
            assert (out["method"], out["seed"], out["route"]) == (
                "P" if arm == "W" else arm,
                int(seed) if seed else None,
                route,
            )
            assert packet["recording_allowance_seconds"] == 1 and t["wall_seconds"] > 0
            assert all(math.isfinite(v) and v >= 0 for v in t.values())
            assert t["legacy_phase_seconds"] <= t["wall_seconds"]
            phases = [out["attempt"]["timing"]]
            if out["fallback"] is not None:
                phases.append(out["fallback"]["timing"])
            assert math.isfinite(out["route_seconds"]) and out["route_seconds"] >= 0
            assert all(math.isfinite(v) and v >= 0 for p in phases for v in p.values())
            close(
                t["legacy_phase_seconds"],
                out["route_seconds"] + sum(sum(p.values()) for p in phases),
            )
            assert all(math.isfinite(v) and v >= 0 for v in cb.values())
            assert cb["wall_seconds"] <= t["wall_seconds"]
            recorded = record(root, prefix, j, queries[j], context)
            paid = t["wall_seconds"] + 1
            if method == "uniform":
                uniform = paid
            assert uniform is not None
            before = endpoint = None
            trigger, updates, choice = False, 0, "endpoint"
            if arm == "P" and route == "generalist":
                receipt = read(root, f"{prefix}/polish/{cid}_{seed}.json")
                original = artifact(root, prefix, receipt["before"], "prepolish")
                ending = artifact(root, prefix, receipt["endpoint"], "endpoint")
                trigger = qualifies(case, original)
                before = certificate(original, ref, volume)
                endpoint = certificate(ending, ref, volume, trigger)
                updates = min(20, 360 - before["iterations"]) if trigger else 0
                choice = selection(case, original, ending)
                chosen = original if choice == "original" else ending
                assert (
                    receipt["case_id"],
                    receipt["seed"],
                    receipt["context_sha256"],
                    receipt["version"],
                    receipt["triggered"],
                    receipt["updates"],
                    receipt["first_stop_iteration"],
                    receipt["selection"],
                ) == (
                    cid,
                    int(seed),
                    context,
                    plan["preservation_version"],
                    trigger,
                    updates,
                    before["iterations"],
                    choice,
                )
                assert ending["trace"][: before["iterations"]] == original["trace"]
                assert len(ending["trace"]) == before["iterations"] + updates
                assert sha(canonical(ending)) == receipt["after_witness_sha256"]
                assert sha(canonical(chosen)) == receipt["selected_witness_sha256"]
                assert chosen == out["attempt"]["state"]
                assert trigger or original == ending
                guards += classify_guard(case, original, ref) + classify_guard(case, ending, ref)
                continued += trigger
                preserved += choice == "original"
            candidate = certificate(
                out["attempt"]["state"], ref, volume, trigger and choice == "endpoint"
            )
            fallback = (
                None
                if out["fallback"] is None
                else certificate(out["fallback"]["state"], ref, volume)
            )
            for a in (out["attempt"], out["fallback"]):
                if a is not None:
                    selected += classify(case, a, ref)
            assert (fallback is not None) == (method != "uniform" and not candidate["succeeded"])
            for c in ([candidate] if method == "uniform" else []) + (
                [fallback] if fallback else []
            ):
                assert c["succeeded"] and abs(c["compliance_ratio"] - 1) <= 1e-9
            rows.append(
                {
                    "case_id": cid,
                    "method": method,
                    "scale": "small" if nx == 12 else "large",
                    "direction": direction,
                    "volume": volume,
                    "load_node": problem["loads"][0]["node"],
                    "route": route,
                    "seconds": paid,
                    "uniform_seconds": uniform,
                    "fallback_seconds": 0
                    if fallback is None
                    else sum(out["fallback"]["timing"].values()),
                    "candidate": candidate,
                    "fallback": fallback,
                    "before": before,
                    "endpoint": endpoint,
                    "triggered": trigger,
                    "added_updates": updates,
                    "selection": choice,
                    "performed_iterations": candidate["iterations"]
                    if endpoint is None
                    else endpoint["iterations"],
                    "timing": t,
                    "callback": cb,
                    "route_seconds": out["route_seconds"],
                    "attempt_phases": out["attempt"]["timing"],
                    "fallback_phases": None if fallback is None else out["fallback"]["timing"],
                    "recording_seconds": recorded,
                }
            )
            panel[method] = packet
        if nx == 24 and direction == "y" and volume >= 0.55:
            for seed in (17, 29, 43):
                for a, b in combinations(("C", "P", "W"), 2):
                    left, right = (panel[f"{m}/{seed}"]["outcome"]["attempt"] for m in (a, b))
                    assert all(
                        left[k] == right[k]
                        for k in ("state", "metrics", "succeeded", "failure_code")
                    )
                    paid = {
                        f"{m}/{seed}": panel[f"{m}/{seed}"]["timing"]["wall_seconds"] + 1
                        for m in (a, b)
                    }
                    spread = max(paid.values()) / min(paid.values())
                    pairs.append(
                        {
                            "case_id": cid,
                            "left": f"{a}/{seed}",
                            "right": f"{b}/{seed}",
                            "charged_seconds": paid,
                            "spread": spread,
                            "flagged": spread >= 1.25,
                        }
                    )
    assert sum(a["audited_attempts"] for a in audited[2:]) == selected
    expected = {
        "cases": len(cases),
        "outcomes": len(rows),
        "terminal_classifications": selected + guards,
        "selected_terminal_classifications": selected,
        "guard_witness_classifications": guards,
        "continuations": continued,
        "added_updates": sum(r["added_updates"] for r in rows),
        "preserved_originals": preserved,
        "references": references,
        "rows": rows,
        "shared_specialist_pairs": pairs,
        "scientific_decision": read(root, name + "/independent_audit.json")["decision"],
        **summary(rows, report["plan"]["methods"], report["plan"]["bounds"]),
    }
    if name == "fresh":
        compact = [
            {
                "case_id": r["case_id"],
                "policy": r["method"],
                "timing": r["timing"],
                "outcome": {
                    "attempt": {"succeeded": r["candidate"]["succeeded"]},
                    "fallback": r["fallback"],
                    "route": r["route"],
                },
            }
            for r in rows
        ]
        close(fresh_decision(compact, cases), expected["scientific_decision"])
    else:
        packets = [
            {
                "case_id": r["case_id"],
                "policy": r["method"],
                "timing": r["timing"],
                "outcome": {
                    "attempt": {"succeeded": r["candidate"]["succeeded"]},
                    "route": r["route"],
                },
            }
            for r in rows
        ]
        originals = {
            (r["case_id"], r["method"]): {
                "outcome": {"attempt": {"succeeded": (r["before"] or r["candidate"])["succeeded"]}}
            }
            for r in rows
        }
        close(sentinel_decision(packets, originals, cases), expected["scientific_decision"])
        values = expected["fixed_primary_cost_scenarios"]["large_y_generalist"]["measured"]
        close(values["mean_paired_ratio"], expected["scientific_decision"]["large_y_primary_mean"])
        close(
            values["ratio_of_sums"], expected["scientific_decision"]["large_y_primary_total_ratio"]
        )
        assert all(r["candidate"]["succeeded"] for r in rows if r["method"] == "P/17")
    close(expected, report["cohorts"][name])
    return expected


def main(argv=None):
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    root, output = args.screen_root.resolve(), args.output_root.resolve()
    assert (
        root.name == "b4-12-terminal-preservation" and output.name == "b4-13-preservation-diagnosis"
    )
    assert root.parent == output.parent and not output.is_relative_to(
        Path(__file__).resolve().parents[1]
    )
    target = output / "independent_audit.json"
    assert not target.exists(), "refuses to overwrite independent audit"
    report = read(output, "diagnosis.json")
    frozen = report["plan"]
    assert frozen["version"] == VERSION and frozen["plan_sha256"] == PLAN_SHA
    assert sha(canonical({k: v for k, v in frozen.items() if k != "plan_sha256"})) == PLAN_SHA
    bound = {p: read(root, p, d) for p, d in frozen["bindings"].items()}
    assert len(bound) == 30
    assert not (root.parent / "b4-10-post-plateau-polish/fresh").exists()
    closed = bound["resource_close.json"]
    assert (
        closed["closed"] and not closed["preservation_gate_passed"] and not closed["fresh_sealed"]
    )
    for p, d in closed["protected_inputs"].items():
        path = (root.parent / p).resolve()
        assert path.is_relative_to(root.parent) and sha(path.read_bytes()) == d
    for p, d in bound["audit_receipts/closure_recovery_release.json"][
        "protected_receipt_sha256"
    ].items():
        path = (root / p).resolve()
        assert path.is_relative_to(root) and sha(path.read_bytes()) == d
    plan = bound["audit_receipts/plan.json"]
    assert plan["plan_sha256"] == frozen["source_plan_sha256"]
    assert plan["fixed_primary"] == 17 and not plan["final_access"]
    cohorts = {
        c: audit_cohort(root, c, plan, report, frozen["bindings"]["context.json"], started)
        for c in ("sentinel", "fresh")
    }
    assert recommendation(cohorts["fresh"]["rows"]) == report["next_mechanism"]
    assert report["prior_charge_seconds"] == closed["charged_seconds"]
    assert report["old_fresh_sealed"] and not report["final_access"] and not report["repaired_gate"]
    for p, d in frozen["bindings"].items():
        read(root, p, d)
    result = {
        "version": VERSION,
        "passed": True,
        "terminal_classifications": sum(c["terminal_classifications"] for c in cohorts.values()),
        "strata": sum(len(c["strata"]) for c in cohorts.values()),
        "same_specialist_pairs": sum(len(c["shared_specialist_pairs"]) for c in cohorts.values()),
        "next_mechanism": report["next_mechanism"],
        "repaired_gate": False,
        "final_access": False,
        "diagnosis_sha256": sha((output / "diagnosis.json").read_bytes()),
        "source_sha256": sha(Path(__file__).read_bytes()),
        "charged_seconds": perf_counter() - started + 10,
        "peak_rss_bytes": peak_rss(),
    }
    assert result["charged_seconds"] <= 120 and result["peak_rss_bytes"] <= 1073741824
    target.write_bytes(canonical(result))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
