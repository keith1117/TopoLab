"""Independent standard-library raw-JSON witness, reflection and charged Gate audit."""

import argparse
import math
import platform
import resource
import statistics
import struct
from pathlib import Path
from time import perf_counter

from b4_10_independent_audit import classify, close, identity, qualifies, units
from b4_12_independent_audit import classify_guard, selection
from b4_30_common import (
    canonical,
    contained,
    contract,
    digest,
    guard_inputs,
    read,
    release,
    save,
    sha,
)


def blob(root, ref, kind):
    if ref["path"] != f"artifacts/{kind}/{ref['sha256']}.json":
        raise ValueError("content-addressed evidence required")
    path = contained(root, ref["path"])
    if path.stat().st_size != ref["byte_size"]:
        raise ValueError("artifact size differs")
    return read(path, ref["sha256"])


def target(case):
    p = case["problem"]
    return (
        p["mesh"]["element_counts"] == [24, 12, 6]
        and p["loads"][0]["direction"] == "y"
        and p["optimization"]["volume_fraction"] < 0.55
    )


def old_references(parent, wanted):
    root = parent / "b4-12-terminal-preservation"
    plan = read(root / "audit_receipts/plan.json")
    context_sha = digest(root / "context.json")
    result = {}
    for cohort in ("sentinel", "fresh"):
        order = plan["assignments"][cohort]
        refs = units(root / cohort / "screen", context_sha, [c + ":" + m for c, m in order])
        result.update(
            {
                (c, m): (root / cohort / "screen", ref)
                for (c, m), ref in zip(order, refs, strict=True)
                if c in wanted
            }
        )
    assert len(result) == 216
    return result


def float32(x):
    return struct.unpack("f", struct.pack("f", x))[0]


def reflection_record(root, context_sha, case, seed):
    record_path = contained(root, f"prediction/{case['case_id']}_{seed}.json")
    v = read(record_path)
    p, mirrored = case["problem"], v["mirror_case"]["problem"]
    nx, ny, nz = p["mesh"]["element_counts"]
    plane = (nx + 1) * (ny + 1)
    node = p["loads"][0]["node"]
    assert mirrored["loads"][0]["node"] == node % plane + plane * (nz - node // plane)
    for key in p:
        if key != "loads":
            assert p[key] == mirrored[key]
    assert {k: x for k, x in p["loads"][0].items() if k != "node"} == {
        k: x for k, x in mirrored["loads"][0].items() if k != "node"
    }
    assert v["version"] == "topolab.b4_30.z-reflection-average.v1"
    assert (
        v["context_sha256"] == context_sha and v["case_id"] == case["case_id"] and v["seed"] == seed
    )
    assert v["same_checkpoint_calls"] == 2 and v["recipe"] == "P" and v["weights"] == [0.5, 0.5]
    assert (
        v["fixed_fits_index_sha256"]
        == "229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7"
    )
    assert v["shape"] == [1, 1, nz, ny, nx] and v["device"] == "cpu" and v["dtype"] == "float32"
    assert all(len(v[k]) == nx * ny * nz for k in ("first", "second", "average"))
    assert all(
        math.isfinite(x) and 0 <= x <= 1 and float32(x) == x
        for k in ("first", "second", "average")
        for x in v[k]
    )
    for i, actual in enumerate(v["average"]):
        j = (nz - 1 - i // (nx * ny)) * nx * ny + i % (nx * ny)
        assert actual == float32(float32(v["first"][i] + v["second"][j]) * 0.5)
    return digest(record_path)


def decision(rows, cohort, spec):
    uniform = {r["case_id"]: r["cost"] for r in rows if r["policy"] == "uniform"}
    by_key = {(r["case_id"], r["policy"]): r for r in rows}
    result = {"cohort": cohort, "fixed_primary": 17, "final_access": False}
    if cohort == "sentinel":
        repaired, unrepaired = [], []
        for unit in spec["sentinel_gate"]["all_known_failed_target_units_repaired"]:
            key = (unit["case_id"], unit["policy"])
            (unrepaired if by_key[key]["failed"] else repaired).append(list(key))
        r_rows = [r for r in rows if r["policy"].startswith("R/")]

        def previous(r):
            return by_key[(r["case_id"], "P/" + r["policy"].split("/")[1])]

        regressions = [
            [r["case_id"], r["policy"]] for r in r_rows if r["failed"] and not previous(r)["failed"]
        ]
        negatives = [r for r in r_rows if not r["target"] and previous(r)["failed"]]
        primary = [r for r in r_rows if r["policy"] == "R/17"]
        failures = [r["case_id"] for r in primary if r["failed"] or r["fallback"]]
        targets = [r for r in primary if r["target"]]
        mean = statistics.mean(r["cost"] / uniform[r["case_id"]] for r in targets)
        total = math.fsum(r["cost"] for r in targets) / math.fsum(
            uniform[r["case_id"]] for r in targets
        )
        identities = all(
            (r["failed"], r["fallback"]) == (previous(r)["failed"], previous(r)["fallback"])
            for r in r_rows
            if not r["target"]
        )
        passed = (
            not unrepaired
            and not regressions
            and not failures
            and identities
            and len(negatives) == 2
            and all(r["failed"] for r in negatives)
            and len(targets) == 13
            and mean <= 1
            and total <= 1
        )
        result.update(
            repaired=repaired,
            unrepaired=unrepaired,
            regressions=regressions,
            primary_failures=failures,
            negative_controls=[[r["case_id"], r["policy"]] for r in negatives],
            non_target_status_identity=identities,
            target_cases=len(targets),
            large_y_primary_mean=mean,
            large_y_primary_total_ratio=total,
            sentinel_gate_passed=bool(passed),
            repair_gate_passed=bool(passed),
        )
        return result
    table, sums = {}, {}
    for method in spec["methods"]:
        selected = [r for r in rows if r["policy"] == method]

        def mean(group):
            return statistics.mean(r["cost"] / uniform[r["case_id"]] for r in group)

        table[method] = {
            "overall_mean": mean(selected),
            "scale_means": {
                s: mean([r for r in selected if r["scale"] == s]) for s in ("small", "large")
            },
            "direction_means": {
                s + "/" + d: mean([r for r in selected if r["scale"] == s and r["direction"] == d])
                for s in ("small", "large")
                for d in ("y", "z")
            },
            "failures": sum(r["failed"] for r in selected),
            "fallbacks": sum(r["fallback"] for r in selected),
            "non_specialist_y_failures": sum(
                r["failed"]
                for r in selected
                if r["direction"] == "y" and r["route"] != "specialist"
            ),
        }
        sums[method] = {
            s: math.fsum(r["cost"] for r in selected if r["scale"] == s) for s in ("small", "large")
        }
    passing = []
    for seed in (17, 29, 43):
        r, c, w = [table[f"{m}/{seed}"] for m in ("R", "C", "W")]
        passed = (
            max(r["scale_means"].values()) <= 0.9
            and max(r["direction_means"].values()) <= 1
            and r["failures"] <= min(2, c["failures"], w["failures"])
            and r["non_specialist_y_failures"]
            <= min(c["non_specialist_y_failures"], w["non_specialist_y_failures"])
            and r["overall_mean"]
            < min(table[m]["overall_mean"] for m in ("physics_heuristic", "nearest_neighbor"))
        )
        r["seed_gate_passed"] = bool(passed)
        r["primary_eligible"] = bool(
            passed
            and r["failures"] == r["fallbacks"] == 0
            and r["overall_mean"] < c["overall_mean"]
            and (r["overall_mean"] < w["overall_mean"] or r["failures"] < w["failures"])
        )
        if passed:
            passing.append(seed)
    cells = {
        str(v): sum(
            not r["failed"]
            for r in rows
            if r["policy"].startswith("R/")
            and r["scale"] == "large"
            and r["direction"] == "y"
            and r["volume"] == v
        )
        for v in (0.5457, 0.6057)
    }
    ratios = {s: sums["R/17"][s] / sums["uniform"][s] for s in ("small", "large")}
    passed = (
        len(passing) >= 2
        and table["R/17"]["primary_eligible"]
        and min(cells.values()) >= 6
        and max(ratios.values()) <= 0.9
    )
    result.update(
        table=table,
        passing_seeds=passing,
        quality_cells=cells,
        primary_total_ratios=ratios,
        development_gate_passed=bool(passed),
        repair_gate_passed=bool(passed),
    )
    return result


def audit(output, cohort):
    started = perf_counter()
    release(output)
    guard_inputs(output.parent, output, cohort + "_independent")
    spec = contract()
    plan = read(output / "audit_receipts/plan.json")
    attempt = read(output / "audit_receipts/one_attempt.json")
    assert attempt["campaigns"] == 2 and attempt["previous_failed_campaigns"] == 1
    assert attempt["completed_numerical_campaigns_maximum"] == 1 and attempt["no_third_campaign"]
    assert plan["scientific_contract_sha256"] == spec["continuation"]["original_contract_sha256"]
    assert plan["plan_sha256"] == sha(
        canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
    )
    assert plan["contract_sha256"] == spec_hash()
    context_sha = digest(output / "context.json")
    assert read(output / "context.json")["plan_sha256"] == plan["plan_sha256"]
    root = output / cohort
    cases = {c["case_id"]: c for c in plan["cases"][cohort]}
    order = plan["assignments"][cohort]
    assert list(cases) == spec["population"][cohort]["case_ids"]
    assert (
        sha(canonical(list(cases.values())))
        == spec["population"][cohort]["case_definitions_sha256"]
    )
    assert sha(canonical(order)) == spec["population"][cohort]["assignments_sha256"]
    screen_ids = [c + ":" + m for c, m in order]
    references = units(root / "reference", context_sha, list(cases))
    screen = units(root / "screen", context_sha, screen_ids)
    numerical = units(
        root / "audit",
        context_sha,
        [
            "inputs",
            "nn_labels",
            *("reference:" + c for c in cases),
            *("screen:" + s for s in screen_ids),
        ],
    )
    policy_units = units(
        root / "policy-audit",
        context_sha,
        [*("reference:" + c for c in cases), *("policy:" + s for s in screen_ids)],
    )
    assert numerical[0]["audited_checkpoints"] == 12 and numerical[1]["audited_nn_labels"] == 528
    old = old_references(output.parent, set(cases)) if cohort == "sentinel" else {}
    baseline, checks, guards, replays, identities = {}, 0, 0, 0, 0
    for i, (case_id, ref) in enumerate(zip(cases, references, strict=True)):
        p = blob(root / "reference", ref, "outcome")
        checks += classify(cases[case_id], p["outcome"]["attempt"], None)
        baseline[case_id] = p["outcome"]["attempt"]["metrics"]["final_compliance"]
        recording(root / "reference", i, ref, context_sha, plan)
        if old:
            old_root, old_ref = old[(case_id, "uniform")]
            assert identity(p["outcome"]) == identity(blob(old_root, old_ref, "outcome")["outcome"])
            identities += 1
    indices = {tuple(key): i for i, key in enumerate(order)}
    rows = []
    for i, ((case_id, policy), ref) in enumerate(zip(order, screen, strict=True)):
        p = blob(root / "screen", ref, "outcome")
        case, o = cases[case_id], p["outcome"]
        assert (
            p["case_id"] == case_id
            and p["policy"] == policy
            and p["version"] == plan["version"]
            and p["context_sha256"] == context_sha
        )
        family, _, seed = policy.partition("/")
        assert o["method"] == ("P" if family in ("W", "R") else family) and o["seed"] == (
            int(seed) if seed else None
        )
        problem = case["problem"]
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
        recording(root / "screen", i, ref, context_sha, plan)
        for attempt in (o["attempt"], o["fallback"]):
            if attempt is not None:
                checks += classify(case, attempt, baseline[case_id])
                if attempt is o["fallback"] or family == "uniform":
                    assert attempt["succeeded"] and math.isclose(
                        attempt["metrics"]["final_compliance"],
                        baseline[case_id],
                        rel_tol=1e-9,
                        abs_tol=0,
                    )
        assert (o["fallback"] is not None) == (
            family != "uniform" and not o["attempt"]["succeeded"]
        )
        policy_row = policy_units[len(cases) + i]
        if old and family != "R":
            old_root, old_ref = old[(case_id, policy)]
            assert identity(o) == identity(blob(old_root, old_ref, "outcome")["outcome"])
            assert policy_row["unchanged_identity_checked"]
            identities += 1
        if family == "R":
            if target(case):
                prediction_sha = reflection_record(root / "screen", context_sha, case, int(seed))
                assert (
                    policy_row["prediction_sha256"] == prediction_sha
                    and policy_row["prediction_replays"] == 2
                )
                replays += 2
            else:
                pp = blob(root / "screen", screen[indices[(case_id, f"P/{seed}")]], "outcome")
                assert (
                    identity(o) == identity(pp["outcome"])
                    and policy_row["unchanged_identity_checked"]
                )
                identities += 1
        if family in ("P", "R") and route == "generalist":
            record_path = contained(root / "screen", f"polish/{family}/{case_id}_{seed}.json")
            record = read(record_path)
            before = blob(root / "screen", record["before"], "prepolish")
            endpoint = blob(root / "screen", record["endpoint"], "endpoint")
            guards += classify_guard(case, before, baseline[case_id])
            guards += classify_guard(case, endpoint, baseline[case_id])
            choice = selection(case, before, endpoint)
            selected = before if choice == "original" else endpoint
            trigger, n = qualifies(case, before), len(before["trace"])
            updates = min(20, 360 - n) if trigger else 0
            assert record["version"] == "topolab.b4_12.candidate-terminal-preservation.v1"
            assert (
                record["context_sha256"] == context_sha
                and record["case_id"] == case_id
                and record["policy"] == policy
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
            assert record["after_witness_sha256"] == sha(canonical(endpoint))
            assert (
                selected == o["attempt"]["state"]
                and record["selection"] == choice
                and record["selected_witness_sha256"] == sha(canonical(selected))
            )
            assert policy_row["guard_witnesses"] == 2 and policy_row[
                "polish_record_sha256"
            ] == digest(record_path)
            if not trigger:
                assert before == endpoint
        rows.append(
            {
                "case_id": case_id,
                "policy": policy,
                "cost": p["timing"]["wall_seconds"] + 1,
                "failed": not o["attempt"]["succeeded"],
                "fallback": o["fallback"] is not None,
                "route": route,
                "scale": "small" if problem["mesh"]["element_counts"][0] == 12 else "large",
                "direction": problem["loads"][0]["direction"],
                "volume": problem["optimization"]["volume_fraction"],
                "target": target(case),
            }
        )
    result = decision(rows, cohort, spec)
    for stage in ("screen", "audit", "policy-audit"):
        close(result, read(root / stage / "summary.json")["decision"])
    assert sum(x["audited_attempts"] for x in numerical[2:]) == checks
    assert sum(x["guard_witnesses"] for x in policy_units) == guards
    assert sum(x["prediction_replays"] for x in policy_units) == replays
    policy_summary = read(root / "policy-audit/summary.json")
    seconds = perf_counter() - started + 10
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if platform.system() == "Darwin" else 1024
    )
    assert seconds <= 1800 and rss <= 2147483648
    record = {
        "version": plan["version"],
        "cohort": cohort,
        "passed": True,
        "gate_passed": result["repair_gate_passed"],
        "decision": result,
        "context_sha256": context_sha,
        "policy_summary_sha256": digest(root / "policy-audit/summary.json"),
        "references": len(references),
        "outcomes": len(rows),
        "selected_terminal_classifications": checks,
        "guard_witness_classifications": guards,
        "prediction_replays": replays,
        "unchanged_outcome_identities": identities,
        "charged_seconds": seconds,
        "peak_rss_bytes": rss,
        "source_sha256": digest(Path(__file__)),
        "administrative_campaigns": 2,
        "retained_failed_charge_decimal": spec["continuation"]["original_failed_charge_decimal"],
    }
    assert record["gate_passed"] == policy_summary["passed"]
    save(root / "independent_audit.json", record)
    return record


def spec_hash():
    from b4_30_common import CONTRACT_SHA

    return CONTRACT_SHA


def recording(root, index, ref, context_sha, plan):
    value = read(contained(root, f"recording/{index:04d}.json"))
    assert value["version"] == plan["receipt_version"] and value["context_sha256"] == context_sha
    assert (
        value["outcome_sha256"] == ref["sha256"]
        and 0 <= value["recording_seconds_before_receipt"] <= 1
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cohort", required=True, choices=("sentinel", "fresh"))
    args = parser.parse_args()
    print(canonical(audit(args.output.resolve(), args.cohort)).decode(), end="")


if __name__ == "__main__":
    main()
