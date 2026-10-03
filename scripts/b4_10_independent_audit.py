"""Independent raw-JSON B4.10 completeness, continuation and charged Gate audit.

Imports no TopoLab numerical or experiment helper and opens no label/model bytes.
The separate production audit supplies FEM/filter numerical verification.
"""

import argparse
import hashlib
import json
import math
import platform
import resource
import statistics
from pathlib import Path
from time import perf_counter


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    value = json.loads(raw)
    assert raw == canonical(value), f"noncanonical {path}"
    return value


def blob(root, ref, kind):
    assert ref["path"] == f"artifacts/{kind}/{ref['sha256']}.json"
    raw = (root / ref["path"]).read_bytes()
    assert len(raw) == ref["byte_size"] and sha(raw) == ref["sha256"]
    value = json.loads(raw)
    assert raw == canonical(value)
    return value


def units(root, context_sha, expected):
    progress, summary = read(root / "progress.json"), read(root / "summary.json")
    assert progress["context_sha256"] == context_sha
    assert progress["units_sha256"] == sha(canonical(expected))
    assert progress["completed"] == len(expected) and progress["attempted"] >= len(expected)
    assert progress["pending"] is None and progress["active_at"] is None
    assert not progress["integrity_failed"] and not progress["resource_failed"]
    for name in ("completed", "attempted", "head_sha256", "charged_seconds", "peak_rss_bytes"):
        assert progress[name] == summary[name], name
    head, payloads = "0" * 64, []
    for i, unit in enumerate(expected):
        path = root / f"units/{i:04d}.json"
        value = read(path)
        assert value["unit"] == unit and value["context_sha256"] == context_sha
        assert value["previous_sha256"] == head
        head = sha(path.read_bytes())
        payloads.append(value["payload"])
    assert head == progress["head_sha256"]
    return payloads


def physical_plateau(witness):
    recent = witness["result"]["history"]
    if len(recent) != 11:
        return False
    change = max(
        abs(b - a)
        for x, y in zip(recent, recent[1:], strict=False)
        for a, b in zip(x["physical_density"], y["physical_density"], strict=True)
    )
    gain = (recent[0]["compliance"] - recent[-1]["compliance"]) / recent[0]["compliance"]
    return change <= 0.01 and 0 <= gain <= 0.0002


def qualifies(case, witness):
    p, r = case["problem"], witness["result"]
    return (
        p["mesh"]["element_counts"] == [24, 12, 6]
        and p["loads"][0]["direction"] == "y"
        and p["optimization"]["volume_fraction"] < 0.55
        and r["converged"]
        and r["history"][-1]["density_change"] > 0.01
        and physical_plateau(witness)
    )


def classify(case, attempt, reference):
    w, metrics = attempt["state"], attempt["metrics"]
    assert w is not None and metrics is not None
    r, trace = w["result"], w["trace"]
    assert all(
        math.isfinite(v)
        for key in ("design_density", "physical_density", "displacements", "reactions")
        for v in r[key]
    )
    assert all(
        math.isfinite(v)
        for point in trace
        for v in (point["compliance"], point["volume_fraction"], point["density_change"])
    )
    assert [t["iteration"] for t in trace] == list(range(1, len(trace) + 1))
    assert 1 <= len(trace) <= 360 and len(r["history"]) == min(11, len(trace))
    for state, point in zip(r["history"], trace[-11:], strict=True):
        for key in ("iteration", "compliance", "volume_fraction", "density_change"):
            assert state[key] == point[key]
    last = r["history"][-1]
    for key in ("design_density", "physical_density", "compliance"):
        assert r[key] == last[key]
    assert metrics["iterations"] == len(trace) and metrics["final_compliance"] == r["compliance"]
    volume = math.fsum(r["physical_density"]) / len(r["physical_density"])
    error = abs(volume - case["problem"]["optimization"]["volume_fraction"])
    assert math.isclose(error, metrics["physical_volume_error"], rel_tol=0, abs_tol=1e-12)
    terminal_stop = last["density_change"] <= 0.01 or physical_plateau(w)
    good = (
        r["converged"]
        and terminal_stop
        and error <= 0.005
        and (reference is None or r["compliance"] <= 1.001 * reference)
    )
    assert good == attempt["succeeded"]
    assert attempt["failure_code"] is None if good else attempt["failure_code"] == "quality_error"
    return 1


def identity(outcome):
    result = dict(outcome)
    result.pop("route_seconds")
    for key in ("attempt", "fallback"):
        if result[key] is not None:
            result[key] = {k: v for k, v in result[key].items() if k != "timing"}
    return result


def close(a, b):
    if isinstance(a, dict):
        assert set(a) == set(b)
        for key in a:
            close(a[key], b[key])
    elif isinstance(a, list):
        assert len(a) == len(b)
        for x, y in zip(a, b, strict=True):
            close(x, y)
    elif isinstance(a, float):
        assert math.isclose(a, b, rel_tol=1e-14, abs_tol=1e-14), (a, b)
    else:
        assert a == b, (a, b)


def sentinel_decision(packets, old, cases):
    uniform = {
        p["case_id"]: p["timing"]["wall_seconds"] + 1 for p in packets if p["policy"] == "uniform"
    }
    repaired, regressions, primary_failures, negative = [], [], [], []
    ratios, costs, denominators = [], [], []
    for p in packets:
        if not p["policy"].startswith("P/"):
            continue
        key = (p["case_id"], p["policy"])
        case = cases[key[0]]["problem"]
        now, before = p["outcome"], old[key]["outcome"]
        target = (
            case["mesh"]["element_counts"][0] == 24
            and case["loads"][0]["direction"] == "y"
            and now["route"] == "generalist"
        )
        if target and not before["attempt"]["succeeded"]:
            (repaired if now["attempt"]["succeeded"] else regressions).append(list(key))
        if before["attempt"]["succeeded"] and not now["attempt"]["succeeded"]:
            regressions.append(list(key))
        if not target and not before["attempt"]["succeeded"]:
            negative.append(list(key))
        if p["policy"] == "P/17":
            if not now["attempt"]["succeeded"]:
                primary_failures.append(p["case_id"])
            if target:
                cost = p["timing"]["wall_seconds"] + 1
                ratios.append(cost / uniform[key[0]])
                costs.append(cost)
                denominators.append(uniform[key[0]])
    mean, total = sum(ratios) / len(ratios), sum(costs) / sum(denominators)
    return {
        "sentinel_gate_passed": len(repaired) == 4
        and not regressions
        and not primary_failures
        and mean <= 1
        and total <= 1,
        "fixed_primary": 17,
        "repaired": repaired,
        "regressions": regressions,
        "primary_failures": primary_failures,
        "negative_controls": negative,
        "large_y_primary_mean": mean,
        "large_y_primary_total_ratio": total,
        "final_access": False,
    }


def fresh_decision(packets, cases):
    uniform = {
        p["case_id"]: p["timing"]["wall_seconds"] + 1 for p in packets if p["policy"] == "uniform"
    }
    by_method, totals = {}, {}
    for p in packets:
        c, o = cases[p["case_id"]]["problem"], p["outcome"]
        scale = "small" if c["mesh"]["element_counts"][0] == 12 else "large"
        cell = scale + "/" + c["loads"][0]["direction"]
        cost = p["timing"]["wall_seconds"] + 1
        by_method.setdefault(p["policy"], []).append(
            (
                cell,
                cost / uniform[p["case_id"]],
                not o["attempt"]["succeeded"],
                o["fallback"] is not None,
                o["route"],
                c["optimization"]["volume_fraction"],
            )
        )
        totals.setdefault(p["policy"], {"small": 0.0, "large": 0.0})[scale] += cost
    table = {}
    for name, rows in by_method.items():
        table[name] = {
            "overall_mean": statistics.mean(r[1] for r in rows),
            "scale_means": {
                s: statistics.mean(r[1] for r in rows if r[0].startswith(s))
                for s in ("small", "large")
            },
            "direction_means": {
                c: statistics.mean(r[1] for r in rows if r[0] == c)
                for c in ("small/y", "small/z", "large/y", "large/z")
            },
            "failures": sum(r[2] for r in rows),
            "fallbacks": sum(r[3] for r in rows),
            "non_specialist_y_failures": sum(
                r[2] for r in rows if r[0].endswith("y") and r[4] != "specialist"
            ),
        }
    passing, eligible = [], []
    for seed in (17, 29, 43):
        p, c, w = (table[f"{m}/{seed}"] for m in ("P", "C", "W"))
        passed = (
            max(p["scale_means"].values()) <= 0.9
            and max(p["direction_means"].values()) <= 1
            and p["failures"] <= min(2, c["failures"], w["failures"])
            and p["non_specialist_y_failures"]
            <= min(c["non_specialist_y_failures"], w["non_specialist_y_failures"])
            and p["overall_mean"]
            < min(table[m]["overall_mean"] for m in ("physics_heuristic", "nearest_neighbor"))
        )
        primary = (
            passed
            and p["failures"] == p["fallbacks"] == 0
            and p["overall_mean"] < c["overall_mean"]
            and (p["overall_mean"] < w["overall_mean"] or p["failures"] < w["failures"])
        )
        p.update(seed_gate_passed=passed, primary_eligible=primary)
        if passed:
            passing.append(seed)
        if primary:
            eligible.append(seed)
    cells = {
        str(v): sum(
            not r[2]
            for seed in (17, 29, 43)
            for r in by_method[f"P/{seed}"]
            if r[0] == "large/y" and r[5] == v
        )
        for v in (0.5427, 0.6027)
    }
    ratios = {s: totals["P/17"][s] / totals["uniform"][s] for s in ("small", "large")}
    passed = (
        len(passing) >= 2
        and bool(eligible)
        and min(cells.values()) >= 6
        and table["P/17"]["primary_eligible"]
        and max(ratios.values()) <= 0.9
    )
    return {
        "table": table,
        "passing_seeds": passing,
        "quality_cells": cells,
        "fixed_primary": 17,
        "primary_total_ratios": ratios,
        "polish_gate_passed": passed,
        "development_gate_passed": passed,
        "final_access": False,
    }


def main():
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cohort", choices=("sentinel", "fresh"), required=True)
    args = parser.parse_args()
    base, cohort = args.output.resolve(), args.cohort
    assert base.name == "b4-10-post-plateau-polish"
    plan = read(base / "audit_receipts/plan.json")
    context = read(base / "context.json")
    context_sha = sha((base / "context.json").read_bytes())
    assert (
        context["plan_sha256"]
        == plan["plan_sha256"]
        == sha(canonical({k: v for k, v in plan.items() if k != "plan_sha256"}))
    )
    source = base.parent / "b4-8-rollback-confirmation"
    for path, expected in plan["source_files"].items():
        assert sha((source / path).read_bytes()) == expected
    for path, expected in plan["diagnosis_files"].items():
        assert sha((base.parent / "b4-9-diagnosis" / path).read_bytes()) == expected
    root = base / cohort
    cases = {c["case_id"]: c for c in plan["cases"][cohort]}
    assignments = plan["assignments"][cohort]
    reference_ids = list(cases)
    ref_units = units(root / "reference", context_sha, reference_ids)
    screen_ids = [c + ":" + m for c, m in assignments]
    screen_units = units(root / "screen", context_sha, screen_ids)
    audited = units(
        root / "audit",
        context_sha,
        [
            "inputs",
            "nn_labels",
            *("reference:" + c for c in reference_ids),
            *("screen:" + s for s in screen_ids),
        ],
    )
    assert audited[0]["audited_checkpoints"] == 12 and audited[1]["audited_nn_labels"] == 528
    units(
        root / "policy-audit",
        context_sha,
        [*("reference:" + c for c in reference_ids), *("policy:" + s for s in screen_ids)],
    )
    references, checks = {}, 0
    for i, (case, ref) in enumerate(zip(reference_ids, ref_units, strict=True)):
        p = blob(root / "reference", ref, "outcome")
        checks += classify(cases[case], p["outcome"]["attempt"], None)
        references[case] = p["outcome"]["attempt"]["metrics"]["final_compliance"]
        r = read(root / "reference" / f"recording/{i:04d}.json")
        assert (
            r["outcome_sha256"] == ref["sha256"]
            and r["context_sha256"] == context_sha
            and 0 <= r["recording_seconds_before_receipt"] <= 1
        )
    old = {}
    if cohort == "sentinel":
        # Original journal completeness was independently closed in B4.8/B4.9;
        # exact frozen progress hashes bind its immutable head before reads.
        progress = read(source / "screen/progress.json")
        head = "0" * 64
        wanted = {tuple(x) for x in assignments}
        for i in range(progress["completed"]):
            path = source / "screen" / f"units/{i:04d}.json"
            unit = read(path)
            assert unit["previous_sha256"] == head
            head = sha(path.read_bytes())
            case, policy = unit["unit"].split(":")
            if (case, policy) in wanted:
                old[(case, policy)] = blob(source / "screen", unit["payload"], "outcome")
        assert head == progress["head_sha256"] and len(old) == len(assignments)
    packets, continuations, identities = [], 0, 0
    for i, ((case, policy), ref) in enumerate(zip(assignments, screen_units, strict=True)):
        p = blob(root / "screen", ref, "outcome")
        assert (
            p["case_id"] == case
            and p["policy"] == policy
            and p["context_sha256"] == context_sha
            and p["version"] == plan["version"]
        )
        o = p["outcome"]
        name, _, seed = policy.partition("/")
        assert o["method"] == ("P" if name == "W" else name) and o["seed"] == (
            int(seed) if seed else None
        )
        problem = cases[case]["problem"]
        route = (
            "baseline"
            if not seed
            else (
                "specialist"
                if problem["mesh"]["element_counts"] == [24, 12, 6]
                and problem["loads"][0]["direction"] == "y"
                and problem["optimization"]["volume_fraction"] >= 0.55
                else "generalist"
            )
        )
        assert o["route"] == route
        assert (
            math.isfinite(p["timing"]["wall_seconds"])
            and p["timing"]["wall_seconds"] > 0
            and p["timing"]["legacy_phase_seconds"] <= p["timing"]["wall_seconds"]
            and p["recording_allowance_seconds"] == 1
        )
        r = read(root / "screen" / f"recording/{i:04d}.json")
        assert (
            r["outcome_sha256"] == ref["sha256"]
            and r["context_sha256"] == context_sha
            and 0 <= r["recording_seconds_before_receipt"] <= 1
        )
        for attempt in (o["attempt"], o["fallback"]):
            if attempt is not None:
                checks += classify(cases[case], attempt, references[case])
                if attempt is o["fallback"] or name == "uniform":
                    assert attempt["succeeded"] and math.isclose(
                        attempt["metrics"]["final_compliance"],
                        references[case],
                        rel_tol=1e-9,
                        abs_tol=0,
                    )
        assert (o["fallback"] is not None) == (name != "uniform" and not o["attempt"]["succeeded"])
        if name == "P" and o["route"] == "generalist":
            record = read(root / "screen" / f"polish/{case}_{seed}.json")
            before = blob(root / "screen", record["before"], "prepolish")
            trigger = qualifies(cases[case], before)
            n = len(before["trace"])
            updates = min(20, 360 - n) if trigger else 0
            assert (
                record["context_sha256"] == context_sha
                and record["case_id"] == case
                and record["seed"] == int(seed)
            )
            assert (
                record["triggered"] == trigger
                and record["first_stop_iteration"] == n
                and record["updates"] == updates
            )
            assert (
                o["attempt"]["state"]["trace"][:n] == before["trace"]
                and len(o["attempt"]["state"]["trace"]) == n + updates
            )
            assert sha(canonical(o["attempt"]["state"])) == record["after_witness_sha256"]
            if cohort == "sentinel":
                assert before == old[(case, policy)]["outcome"]["attempt"]["state"]
            if not trigger:
                assert before == o["attempt"]["state"]
            else:
                continuations += 1
            if not trigger and cohort == "sentinel":
                assert identity(o) == identity(old[(case, policy)]["outcome"])
                identities += 1
        elif cohort == "sentinel":
            assert identity(o) == identity(old[(case, policy)]["outcome"])
            identities += 1
        packets.append(p)
    decision = (
        sentinel_decision(packets, old, cases)
        if cohort == "sentinel"
        else fresh_decision(packets, cases)
    )
    assert sum(p["audited_attempts"] for p in audited[2:]) == checks
    policy_summary = read(root / "policy-audit/summary.json")
    for stage in ("screen", "audit", "policy-audit"):
        close(decision, read(root / stage / "summary.json")["decision"])
    seconds = perf_counter() - started + 10
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if platform.system() == "Darwin" else 1024
    )
    assert seconds <= plan["independent_audit_cap_seconds"] and rss <= plan["whole_slice_rss_bytes"]
    result = {
        "version": plan["version"],
        "cohort": cohort,
        "passed": True,
        "decision": decision,
        "gate_passed": policy_summary["passed"],
        "context_sha256": context_sha,
        "policy_summary_sha256": sha((root / "policy-audit/summary.json").read_bytes()),
        "references": len(ref_units),
        "outcomes": len(packets),
        "terminal_classifications": checks,
        "continuations": continuations,
        "unchanged_outcome_identities": identities,
        "charged_seconds": seconds,
        "peak_rss_bytes": rss,
        "source_sha256": sha(Path(__file__).read_bytes()),
    }
    target = root / "independent_audit.json"
    assert not target.exists(), "independent receipt must not be overwritten"
    target.write_bytes(canonical(result))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
