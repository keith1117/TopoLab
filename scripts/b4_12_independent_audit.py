"""Independent raw-JSON B4.12 selection, witness and fully charged Gate audit.

Reuses only previous independent JSON/quality arithmetic, never the new policy.
Separate production audits independently re-solve both candidate witnesses.
"""

import argparse
import json
import math
import platform
import resource
import statistics
from pathlib import Path
from time import perf_counter

from b4_10_independent_audit import (
    blob as previous_blob,
)
from b4_10_independent_audit import (
    canonical,
    classify,
    close,
    identity,
    physical_plateau,
    qualifies,
    sentinel_decision,
    sha,
    units,
)
from b4_10_independent_audit import (
    read as previous_read,
)


def read(path):
    root = path
    while (
        root.name
        not in (
            "b4-12-terminal-preservation",
            "b4-10-post-plateau-polish",
            "b4-11-polish-diagnosis",
            "b4-8-rollback-confirmation",
            "b4-9-diagnosis",
        )
        and root != root.parent
    ):
        root = root.parent
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("evidence path escapes its permitted root")
    return previous_read(path)


def blob(root, ref, kind):
    if not (root / ref["path"]).resolve().is_relative_to(root.resolve()):
        raise ValueError("blob escapes its permitted root")
    return previous_blob(root, ref, kind)


def selection(case, before, endpoint):
    if not qualifies(case, before):
        return "endpoint"
    n, total = len(before["trace"]), len(endpoint["trace"])
    if total - n != 20:
        return "endpoint"
    assert total <= 360
    r = endpoint["result"]
    certificate = r["history"][-1]["density_change"] <= 0.01 or physical_plateau(endpoint)
    assert certificate == r["converged"]
    if certificate:
        return "endpoint"
    r = before["result"]
    assert math.isfinite(r["compliance"])
    assert all(
        math.isfinite(v) and case["problem"]["optimization"]["minimum_density"] <= v <= 1
        for v in r["design_density"]
    )
    assert all(math.isfinite(v) for v in r["physical_density"])
    volume = math.fsum(r["physical_density"]) / len(r["physical_density"])
    assert abs(volume - case["problem"]["optimization"]["volume_fraction"]) <= 0.005
    return "original"


def classify_guard(case, witness, reference):
    r = witness["result"]
    error = abs(
        math.fsum(r["physical_density"]) / len(r["physical_density"])
        - case["problem"]["optimization"]["volume_fraction"]
    )
    good = bool(
        r["converged"]
        and (r["history"][-1]["density_change"] <= 0.01 or physical_plateau(witness))
        and error <= 0.005
        and r["compliance"] <= 1.001 * reference
    )
    attempt = {
        "state": witness,
        "metrics": {
            "iterations": len(witness["trace"]),
            "final_compliance": r["compliance"],
            "physical_volume_error": error,
        },
        "succeeded": good,
        "failure_code": None if good else "quality_error",
    }
    return classify(case, attempt, reference)


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
        for v in tuple(
            sorted({c["problem"]["optimization"]["volume_fraction"] for c in cases.values()})
        )[-2:]
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
    assert base.name == "b4-12-terminal-preservation"
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
    for sibling, bindings in (
        ("b4-10-post-plateau-polish", plan["polish_files"]),
        ("b4-11-polish-diagnosis", plan["review_files"]),
    ):
        for path, expected in bindings.items():
            assert sha((base.parent / sibling / path).read_bytes()) == expected
    assert not (base.parent / "b4-10-post-plateau-polish/fresh").exists()
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
            and r["version"] == plan["version"].replace("terminal-preservation-probe", "recording")
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
    polished = {}
    if cohort == "sentinel":
        old_root = base.parent / "b4-10-post-plateau-polish"
        old_sha = sha((old_root / "context.json").read_bytes())
        old_refs = units(old_root / "sentinel/screen", old_sha, screen_ids)
        polished = {
            tuple(key): blob(old_root / "sentinel/screen", ref, "outcome")
            for key, ref in zip(assignments, old_refs, strict=True)
        }
    packets, continuations, identities = [], 0, 0
    guard_checks, preserved = 0, []
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
            and r["version"] == plan["version"].replace("terminal-preservation-probe", "recording")
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
            endpoint = blob(root / "screen", record["endpoint"], "endpoint")
            chosen = selection(cases[case], before, endpoint)
            selected = before if chosen == "original" else endpoint
            guard_checks += classify_guard(cases[case], before, references[case])
            guard_checks += classify_guard(cases[case], endpoint, references[case])
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
                endpoint["trace"][:n] == before["trace"] and len(endpoint["trace"]) == n + updates
            )
            assert sha(canonical(endpoint)) == record["after_witness_sha256"]
            assert record["version"] == plan["preservation_version"]
            assert chosen == record["selection"] and selected == o["attempt"]["state"]
            assert sha(canonical(selected)) == record["selected_witness_sha256"]
            if chosen == "original":
                preserved.append([case, policy])
            if cohort == "sentinel":
                assert endpoint == polished[(case, policy)]["outcome"]["attempt"]["state"]
            if cohort == "sentinel":
                assert before == old[(case, policy)]["outcome"]["attempt"]["state"]
            if not trigger:
                assert before == endpoint
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
        "terminal_classifications": checks + guard_checks,
        "selected_terminal_classifications": checks,
        "guard_witness_classifications": guard_checks,
        "preserved_originals": preserved,
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
