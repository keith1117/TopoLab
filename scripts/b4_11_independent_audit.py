"""Independent raw-evidence arithmetic audit; imports no B4.11 diagnosis helper."""

import argparse
import math
import platform
import resource
from itertools import combinations
from pathlib import Path
from time import perf_counter

from b4_10_independent_audit import canonical, classify, close, sha

PLAN_SHA = "3c831763197e8e80f3295f8df085ed6339b23e5917ed69f96ca97fd6198b324f"
VERSION = "topolab.b4_11.polish-diagnosis.v1"


def read(root, relative, expected=None):
    path = (root / relative).resolve()
    assert path.is_relative_to(root.resolve()), "evidence path escapes root"
    raw = path.read_bytes()
    assert expected is None or sha(raw) == expected, "checksum differs"
    import json

    value = json.loads(raw)
    assert canonical(value) == raw, "noncanonical evidence"
    return value


def journal(root, stage, names, context):
    prefix = f"sentinel/{stage}"
    progress = read(root, prefix + "/progress.json")
    summary = read(root, prefix + "/summary.json")
    assert progress["context_sha256"] == context
    assert progress["units_sha256"] == sha(canonical(names))
    assert progress["attempted"] == progress["completed"] == len(names)
    assert progress["pending"] is None and progress["active_at"] is None
    assert not progress["integrity_failed"] and not progress["resource_failed"]
    for key in ("attempted", "completed", "head_sha256", "charged_seconds", "peak_rss_bytes"):
        assert progress[key] == summary[key]
    head, payloads = "0" * 64, []
    for ordinal, name in enumerate(names):
        item = read(root, f"{prefix}/units/{ordinal:04d}.json")
        assert (item["unit"], item["context_sha256"], item["previous_sha256"]) == (
            name,
            context,
            head,
        )
        head = sha(canonical(item))
        payloads.append(item["payload"])
    assert head == progress["head_sha256"]
    return payloads


def artifact(root, stage, reference, kind):
    assert reference["path"] == f"artifacts/{kind}/{reference['sha256']}.json"
    value = read(root, f"sentinel/{stage}/{reference['path']}", reference["sha256"])
    assert len(canonical(value)) == reference["byte_size"]
    return value


def certificate(witness, reference, volume, polished=False):
    result, trace = witness["result"], witness["trace"]
    recent = result["history"]
    n = len(trace)
    assert reference > 0 and math.isfinite(reference)
    assert 1 <= n <= 360 and len(recent) == min(11, n)
    assert [p["iteration"] for p in trace] == list(range(1, n + 1))
    assert all(
        math.isfinite(p[k])
        for p in trace
        for k in ("compliance", "volume_fraction", "density_change")
    )
    for state, point in zip(recent, trace[-11:], strict=True):
        for key in ("iteration", "compliance", "volume_fraction", "density_change"):
            assert state[key] == point[key]
    for key in ("design_density", "physical_density", "compliance"):
        assert result[key] == recent[-1][key]
    assert all(
        math.isfinite(v)
        for key in ("design_density", "physical_density", "displacements", "reactions")
        for v in result[key]
    )
    change = max(
        (
            abs(b - a)
            for x, y in zip(recent, recent[1:], strict=False)
            for a, b in zip(x["physical_density"], y["physical_density"], strict=True)
        ),
        default=0.0,
    )
    gain = 1 - recent[-1]["compliance"] / recent[0]["compliance"]
    design = recent[-1]["density_change"] <= 0.01
    plateau = len(recent) == 11 and change <= 0.01 and 0 <= gain <= 0.0002
    error = abs(math.fsum(result["physical_density"]) / len(result["physical_density"]) - volume)
    reasons = []
    if not result["converged"] or not (design or plateau):
        reasons.append("not_converged")
    if result["compliance"] > reference * 1.001:
        reasons.append("compliance_above_matched_uniform")
    if error > 0.005:
        reasons.append("physical_volume_error")
    assert not result["converged"] or design or plateau, "false convergence certificate"
    if design:
        stop = "design_change"
    elif plateau:
        stop = "physical_plateau"
    elif polished:
        stop = "post_polish_nonconvergence"
    elif n == 360:
        stop = "iteration_cap"
    else:
        stop = "nonconverged"
    return {
        "succeeded": not reasons,
        "converged": result["converged"],
        "stop": stop,
        "quality_reasons": reasons,
        "iterations": n,
        "compliance_ratio": result["compliance"] / reference,
        "physical_volume_error": error,
        "last_design_change": recent[-1]["density_change"],
        "last_ten_physical_change_max": change if len(recent) == 11 else None,
        "last_ten_compliance_improvement": gain if len(recent) == 11 else None,
        "design_certificate": design,
        "plateau_certificate": plateau,
    }


def costs(rows, scenario):
    assert scenario in ("measured", "fallback_free", "failed_to_uniform")
    paid, denominator = [], []
    for row in rows:
        value = row["seconds"]
        if scenario == "fallback_free":
            value -= row["fallback_seconds"]
        elif scenario == "failed_to_uniform" and not row["candidate"]["succeeded"]:
            value = row["uniform_seconds"]
        paid.append(value)
        denominator.append(row["uniform_seconds"])
    return {
        "cases": len(rows),
        "mean_paired_ratio": math.fsum(a / b for a, b in zip(paid, denominator, strict=True))
        / len(rows),
        "ratio_of_sums": math.fsum(paid) / math.fsum(denominator),
        "charged_seconds": math.fsum(paid),
        "uniform_seconds": math.fsum(denominator),
        "observed_failures": sum(not r["candidate"]["succeeded"] for r in rows),
        "diagnostic_only": scenario != "measured",
        "observed_statuses_preserved": True,
    }


def recommendation(rows, bound):
    regressions = []
    for row in rows:
        before = row["before"]
        if (
            row["method"] == "P/17"
            and before
            and before["succeeded"]
            and not row["candidate"]["succeeded"]
        ):
            regressions.append(row)
    possible = len(regressions) == 1
    if possible:
        row = regressions[0]
        possible = (
            row["triggered"]
            and row["candidate"]["stop"] == "post_polish_nonconvergence"
            and row["candidate"]["quality_reasons"] == ["not_converged"]
            and row["candidate"]["compliance_ratio"] <= row["before"]["compliance_ratio"]
            and bound["mean_paired_ratio"] < 1
            and bound["ratio_of_sums"] < 1
        )
    return (
        "bounded_candidate_terminal_witness_preservation_probe"
        if possible
        else "generalist_reliability_and_refinement_method_review"
    )


def audit(root, report):
    frozen = report["plan"]
    assert frozen["version"] == VERSION and frozen["plan_sha256"] == PLAN_SHA
    assert sha(canonical({k: v for k, v in frozen.items() if k != "plan_sha256"})) == PLAN_SHA
    bound = {p: read(root, p, digest) for p, digest in frozen["bindings"].items()}
    assert len(bound) == 14 and not (root / "fresh").exists()
    closure = bound["resource_close.json"]
    assert closure["closed"] and closure["fresh_sealed"] and not closure["polish_gate_passed"]
    assert len(closure["protected_inputs"]) == 18
    for path, digest in closure["protected_inputs"].items():
        target = (root.parent / path).resolve()
        assert target.is_relative_to(root.parent.resolve()) and sha(target.read_bytes()) == digest
    context = frozen["bindings"]["context.json"]
    plan = bound["audit_receipts/plan.json"]
    cases = {c["case_id"]: c for c in plan["cases"]["sentinel"]}
    assigned = plan["assignments"]["sentinel"]
    names = [c + ":" + m for c, m in assigned]
    assert len(cases) == 9 and len(assigned) == 108
    refs = journal(root, "reference", list(cases), context)
    screens = journal(root, "screen", names, context)
    audits = journal(
        root,
        "audit",
        [
            "inputs",
            "nn_labels",
            *("reference:" + c for c in cases),
            *("screen:" + n for n in names),
        ],
        context,
    )
    policies = journal(
        root,
        "policy-audit",
        [*("reference:" + c for c in cases), *("policy:" + n for n in names)],
        context,
    )
    assert audits[0]["audited_checkpoints"] == 12 and audits[1]["audited_nn_labels"] == 528
    rows, references, pairs, packets, old = [], [], [], [], {}
    classified = prechecks = continuations = unchanged = 0
    for index, (cid, case) in enumerate(cases.items()):
        problem = case["problem"]
        nx = problem["mesh"]["element_counts"][0]
        volume = problem["optimization"]["volume_fraction"]
        direction = problem["loads"][0]["direction"]
        reference_packet = artifact(root, "reference", refs[index], "outcome")
        attempt = reference_packet["outcome"]["attempt"]
        ref = attempt["metrics"]["final_compliance"]
        assert reference_packet["case_id"] == cid and reference_packet["policy"] == "uniform"
        assert reference_packet["context_sha256"] == context
        classified += classify(case, attempt, ref)
        references.append({"case_id": cid, **certificate(attempt["state"], ref, volume)})
        assert references[-1]["succeeded"] and policies[index]["reference_identity_checked"]
        reference_record = read(root, f"sentinel/reference/recording/{index:04d}.json")
        assert reference_record["outcome_sha256"] == refs[index]["sha256"]
        assert reference_record["context_sha256"] == context
        assert reference_record["version"] == "topolab.b4_10.recording.v1"
        assert 0 <= reference_record["recording_seconds_before_receipt"] <= 1
        panel, uniform = {}, None
        for ordinal in range(index * 12, index * 12 + 12):
            assigned_cid, method = assigned[ordinal]
            packet = artifact(root, "screen", screens[ordinal], "outcome")
            assert (assigned_cid, packet["case_id"], packet["policy"]) == (cid, cid, method)
            assert packet["version"] == "topolab.b4_10.post-plateau-probe.v1"
            assert (
                packet["context_sha256"] == context and packet["recording_allowance_seconds"] == 1
            )
            out, time, callback = packet["outcome"], packet["timing"], packet["callback"]
            arm, _, seed = method.partition("/")
            route = (
                "baseline"
                if not seed
                else (
                    "specialist"
                    if nx == 24 and direction == "y" and volume >= 0.55
                    else "generalist"
                )
            )
            assert (out["method"], out["seed"], out["route"]) == (
                "P" if arm == "W" else arm,
                int(seed) if seed else None,
                route,
            )
            phases = [out["attempt"]["timing"]]
            if out["fallback"]:
                phases.append(out["fallback"]["timing"])
            assert all(math.isfinite(v) and v >= 0 for p in phases for v in p.values())
            assert all(math.isfinite(v) and v >= 0 for v in time.values())
            assert time["wall_seconds"] >= time["legacy_phase_seconds"]
            close(
                time["legacy_phase_seconds"],
                out["route_seconds"] + sum(sum(p.values()) for p in phases),
            )
            assert all(
                math.isfinite(callback[k]) and callback[k] >= 0
                for k in ("wall_seconds", "cpu_seconds", "bytes_written")
            )
            assert callback["wall_seconds"] <= time["wall_seconds"]
            recording = read(root, f"sentinel/screen/recording/{ordinal:04d}.json")
            assert recording["context_sha256"] == context
            assert recording["version"] == "topolab.b4_10.recording.v1"
            assert recording["outcome_sha256"] == screens[ordinal]["sha256"]
            assert 0 <= recording["recording_seconds_before_receipt"] <= 1
            seconds = time["wall_seconds"] + 1
            if method == "uniform":
                uniform = seconds
            assert uniform is not None
            before, trigger, updates = None, False, 0
            if arm == "P" and route == "generalist":
                record = read(root, f"sentinel/screen/polish/{cid}_{seed}.json")
                witness = artifact(root, "screen", record["before"], "prepolish")
                before = certificate(witness, ref, volume)
                trigger = (
                    nx == 24
                    and direction == "y"
                    and volume < 0.55
                    and before["converged"]
                    and before["plateau_certificate"]
                    and not before["design_certificate"]
                )
                updates = 20 if trigger else 0
                assert (
                    record["context_sha256"],
                    record["case_id"],
                    record["seed"],
                    record["first_stop_iteration"],
                    record["triggered"],
                    record["updates"],
                ) == (context, cid, int(seed), before["iterations"], trigger, updates)
                state = out["attempt"]["state"]
                assert state["trace"][: before["iterations"]] == witness["trace"]
                assert len(state["trace"]) == before["iterations"] + updates
                assert sha(canonical(state)) == record["after_witness_sha256"]
                assert policies[9 + ordinal]["prepolish_audited"]
                assert trigger or witness == state
                prechecks += 1
                continuations += trigger
                old[(cid, method)] = {"outcome": {"attempt": {"succeeded": before["succeeded"]}}}
            else:
                old[(cid, method)] = {
                    "outcome": {"attempt": {"succeeded": out["attempt"]["succeeded"]}}
                }
            candidate = certificate(out["attempt"]["state"], ref, volume, trigger)
            classified += classify(case, out["attempt"], ref)
            fallback = None
            if out["fallback"]:
                fallback = certificate(out["fallback"]["state"], ref, volume)
                classified += classify(case, out["fallback"], ref)
                assert fallback["succeeded"] and abs(fallback["compliance_ratio"] - 1) <= 1e-9
            assert (fallback is not None) == (method != "uniform" and not candidate["succeeded"])
            if method == "uniform":
                assert candidate["succeeded"] and abs(candidate["compliance_ratio"] - 1) <= 1e-9
            if not trigger:
                assert policies[9 + ordinal]["unchanged_identity_checked"]
                unchanged += 1
            rows.append(
                {
                    "case_id": cid,
                    "method": method,
                    "scale": "small" if nx == 12 else "large",
                    "direction": direction,
                    "volume": volume,
                    "load_node": problem["loads"][0]["node"],
                    "route": route,
                    "seconds": seconds,
                    "uniform_seconds": uniform,
                    "fallback_seconds": sum(out["fallback"]["timing"].values()) if fallback else 0,
                    "candidate": candidate,
                    "fallback": fallback,
                    "before": before,
                    "triggered": trigger,
                    "added_updates": updates,
                    "timing": time,
                    "callback": callback,
                    "attempt_phases": out["attempt"]["timing"],
                    "route_seconds": out["route_seconds"],
                    "fallback_phases": out["fallback"]["timing"] if fallback else None,
                    "recording_seconds": recording["recording_seconds_before_receipt"],
                }
            )
            panel[method] = out
            packets.append(
                {
                    "case_id": cid,
                    "policy": method,
                    "timing": {"wall_seconds": time["wall_seconds"]},
                    "outcome": {"route": route, "attempt": {"succeeded": candidate["succeeded"]}},
                }
            )
        if nx == 24 and direction == "y" and volume >= 0.55:
            for seed in (17, 29, 43):
                for a, b in combinations(("C", "P", "W"), 2):
                    for key in ("state", "metrics", "succeeded", "failure_code"):
                        assert (
                            panel[f"{a}/{seed}"]["attempt"][key]
                            == panel[f"{b}/{seed}"]["attempt"][key]
                        )
                    paid = {
                        r["method"]: r["seconds"]
                        for r in rows[-12:]
                        if r["method"] in (f"{a}/{seed}", f"{b}/{seed}")
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
    assert (classified, prechecks, continuations, unchanged, len(pairs)) == (132, 24, 12, 96, 9)
    close(report["rows"], rows)
    close(report["references"], references)
    close(report["shared_specialist_pairs"], pairs)
    from b4_10_independent_audit import sentinel_decision

    decision = sentinel_decision(packets, old, cases)
    close(report["scientific_decision"], decision)
    close(bound["sentinel/policy-audit/summary.json"]["decision"], decision)
    assert not decision["sentinel_gate_passed"] and decision["fixed_primary"] == 17
    primary = [
        r
        for r in rows
        if r["method"] == "P/17"
        and r["scale"] == "large"
        and r["direction"] == "y"
        and r["route"] == "generalist"
    ]
    assert len(primary) == 4
    scenarios = {s: costs(primary, s) for s in ("measured", "fallback_free", "failed_to_uniform")}
    close(report["fixed_primary_cost_scenarios"], scenarios)
    strata = []
    for method in frozen["methods"]:
        for scale in ("small", "large"):
            for direction in ("y", "z"):
                group = [
                    r
                    for r in rows
                    if (r["method"], r["scale"], r["direction"]) == (method, scale, direction)
                ]
                strata.append(
                    {
                        "method": method,
                        "scale": scale,
                        "direction": direction,
                        **costs(group, "measured"),
                        "updates": sum(r["candidate"]["iterations"] for r in group),
                        "fallback_seconds": sum(r["fallback_seconds"] for r in group),
                    }
                )
    close(report["strata"], strata)
    ff = scenarios["fallback_free"]
    mean_slack = (
        (1 - ff["mean_paired_ratio"]) * 4 / math.fsum(1 / r["uniform_seconds"] for r in primary)
    )
    total_slack = (ff["uniform_seconds"] - ff["charged_seconds"]) / 4
    close(
        report["optimistic_constant_guard_budget_seconds_per_target_query"],
        max(0.0, min(mean_slack, total_slack)),
    )
    assert report["next_mechanism"] == recommendation(rows, ff)
    close(
        report["timing_totals"],
        {
            k: sum(r["timing"][k] for r in rows)
            for k in ("wall_seconds", "cpu_seconds", "legacy_phase_seconds")
        },
    )
    close(
        report["callback_totals"],
        {
            k: sum(r["callback"][k] for r in rows)
            for k in ("wall_seconds", "cpu_seconds", "bytes_written")
        },
    )
    for key, value in {
        "cases": 9,
        "outcomes": 108,
        "classified_attempts": 132,
        "prepolish_witnesses": 24,
        "continuations": 12,
        "added_updates": 240,
        "unchanged_identities": 96,
        "fresh_sealed": True,
        "claim": "read_only_diagnosis_not_a_repaired_gate",
        "source_resource_close": closure,
    }.items():
        close(report[key], value)
    for path, digest in frozen["bindings"].items():
        read(root, path, digest)
    return {
        "terminal_classifications": classified,
        "prepolish_checks": prechecks,
        "strata": len(strata),
        "specialist_pairs": len(pairs),
        "next_mechanism": recommendation(rows, ff),
    }


def main(argv=None):
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    root, output = args.screen_root.resolve(), args.output_root.resolve()
    assert root.name == "b4-10-post-plateau-polish" and output.name == "b4-11-polish-diagnosis"
    assert root.parent == output.parent and not output.is_relative_to(
        Path(__file__).resolve().parents[1]
    )
    target = output / "independent_audit.json"
    assert not target.exists(), "refuses to overwrite independent audit"
    report = read(output, "diagnosis.json")
    counts = audit(root, report)
    receipt = {
        "version": VERSION,
        "passed": True,
        **counts,
        "diagnosis_sha256": sha((output / "diagnosis.json").read_bytes()),
        "source_sha256": sha(Path(__file__).read_bytes()),
        "charged_seconds": perf_counter() - started + 10,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        * (1 if platform.system() == "Darwin" else 1024),
    }
    assert receipt["charged_seconds"] <= 120 and receipt["peak_rss_bytes"] <= 1_073_741_824
    target.write_bytes(canonical(receipt))
    print(canonical(receipt).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
