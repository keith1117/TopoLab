"""Read-only review of the complete closed B4.15 timing population."""

import argparse
import math
import re
from pathlib import Path
from statistics import median
from time import perf_counter

from b4_14_generalist_method_review import canonical, execution_release, peak_rss, read, roots
from b4_15_offline_compliance_adjoint import check_inputs as check_prior
from b4_15_offline_compliance_adjoint import plan_payload as prior_plan
from b4_15_offline_compliance_adjoint import safe_hash, sha

VERSION = "topolab.b4_16.offline-adjoint-cost-review.v1"
PROBE_SHA = "e34e5f652a048e07bc0f1a732ff93d63e566699f45c11017007858f003761ace"
BINDINGS = {
    "audit_receipts/plan.json": "7c1e6f8cb8b6e39ae8367b9fab02d176abbbf9b9e629d0cad6b832cfa59e7692",
    "audit_receipts/production_release.json": (
        "d054d6a75efed2783ba5ef3926cf7f9b25041dc6c1a7eaf0a6b4258acb48fb83"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "4cd38750af814673fb4f97b4cd2104b84d69babc84f1a7250b17d6c5605eb295"
    ),
    "independent_audit.json": "ea6cfc01551d53f9bf4243fd6929b53a7a2a2a83e82bddcbcfe6e31d082dfcc5",
    "resource_close.json": "39a49c229c5cf9e1bce04bea2446086522b9ad76dfb354363718d26b6d5a1154",
    "audit_receipts/execution_commands.json": (
        "d5cbd15425ab9d96a1aa4f49a86e80f614e737f096695e9d0ef0e42dd722cf42"
    ),
    "audit_receipts/closure_command.json": (
        "34e6fb3f7ab477846645f040063530c6a1ed43adf5fe9e8db22f892ff46e4487"
    ),
    "audit_receipts/closure_profile_verification.json": (
        "f61eb572680bbcd46f1a2b02bbb5cad458aa8b149f24facd8c2b193a3fb4000d"
    ),
    "audit_receipts/evidence_release.json": (
        "b48e579d891627084d337daed564a344f2851f11b4b2587c7648395ae55db0ff"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "0d0a158cfeb2020490d8f6ba80e97a2cbf3efbae76eb1dbadd12faad4d94178d"
    ),
}
PHASE_NEXT = "B4.17 bounded offline FEM phase-cost and setup-reuse feasibility probe"
STABILITY_NEXT = "B4.17 bounded offline adjoint timing-stability probe"


def plan_payload():
    payload = {
        "version": VERSION,
        "bindings": BINDINGS,
        "probe_sha256": PROBE_SHA,
        "prior_plan_sha256": prior_plan()["plan_sha256"],
        "cases": 8,
        "states": 16,
        "observations": 48,
        "scenarios": [
            "original_maximum",
            "wall_minimum",
            "wall_median",
            "cpu_minimum",
            "zero_small",
        ],
        "max_seconds": 180,
        "process_seconds": 60,
        "closure_seconds": 30,
        "max_rss_bytes": 1073741824,
        "solver_calls": 0,
        "fits": 0,
        "label_model_byte_reads": 0,
        "final_access": False,
        "arithmetic_tolerance": 1e-12,
        "decision_order": [PHASE_NEXT, STABILITY_NEXT],
    }
    return {**payload, "plan_sha256": sha(canonical(payload))}


def check_inputs(root):
    bound = {p: read(root, p, d) for p, d in BINDINGS.items()}
    audit, closed, proof, evidence = (
        bound[p]
        for p in (
            "independent_audit.json",
            "resource_close.json",
            "audit_receipts/closure_profile_verification.json",
            "audit_receipts/evidence_release.json",
        )
    )
    if (
        bound["audit_receipts/plan.json"] != prior_plan()
        or not audit["passed"]
        or not audit["numerical_passed"]
        or audit["probe_sha256"] != PROBE_SHA
        or audit["directional_checks"] != 64
        or audit["total_solver_calls"] != 200
        or not closed["closed"]
        or closed["feasibility_passed"]
        or closed["fit_proxy"]["cost_feasible"]
        or closed["repaired_gate"]
        or not math.isclose(closed["charged_seconds"], 84.33, rel_tol=1e-12, abs_tol=1e-12)
        or closed["probe_sha256"] != PROBE_SHA
        or not proof["passed"]
        or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]
        or not evidence["all_applicable_ci_passed_before_merge"]
        or not evidence["merged_tree_equals_tested_tree"]
        or evidence["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
        or evidence["final_access"]
        or evidence["repaired_gate"]
        or not evidence["old_fresh_sealed"]
    ):
        raise ValueError("requires closed numerical-pass/cost-fail B4.15 evidence")
    for name, digest in closed["profile_sha256"].items():
        safe_hash(root, "profiles/" + name, digest)
    safe_hash(root, "profiles/closure.time", proof["closure_profile_sha256"])
    check_prior(root.parent / "b4-14-generalist-method-review", root.parent / "b3-v1-data")
    return bound


def stats(values):
    return {
        "count": len(values),
        "minimum": min(values),
        "median": median(values),
        "mean": math.fsum(values) / len(values),
        "maximum": max(values),
        "sum": math.fsum(values),
    }


def native_profiles(root):
    result = {}
    for name in ("probe", "independent", "closure"):
        text = (root / "profiles" / (name + ".time")).read_text()
        timer = re.search(r"([\d.]+)\s+real\s+([\d.]+)\s+user\s+([\d.]+)\s+sys", text)
        rss = re.search(r"(\d+)\s+maximum resident set size", text)
        if timer is None or rss is None:
            raise ValueError("complete native CPU/wall/RSS required")
        result[name] = dict(
            zip(
                ("wall_seconds", "user_seconds", "system_seconds"),
                map(float, timer.groups()),
                strict=True,
            )
        )
        result[name]["peak_rss_bytes"] = int(rss[1])
    return result


def timing_rows(probe):
    plan = prior_plan()
    expected = [(e["case"]["case_id"], s) for e in plan["entries"] for s in plan["states"]]
    rows = probe["rows"]
    if probe["plan"] != plan or [(r["case_id"], r["state"]) for r in rows] != expected:
        raise ValueError("complete ordered case/state population differs")
    observations = []
    for row, entry in zip(rows, [e for e in plan["entries"] for _ in plan["states"]], strict=True):
        scale = "small" if entry["case"]["problem"]["mesh"]["element_counts"][0] == 12 else "large"
        if row["scale"] != scale or len(row["timings"]) != 3:
            raise ValueError("complete scale/repeat population differs")
        for repeat, timing in enumerate(row["timings"]):
            if any(
                not math.isfinite(timing[k]) or timing[k] <= 0
                for k in ("wall_seconds", "cpu_seconds")
            ):
                raise ValueError("finite positive complete timing required")
            observations.append(
                {
                    "case_id": row["case_id"],
                    "state": row["state"],
                    "scale": scale,
                    "repeat": repeat,
                    **timing,
                    "wall_minus_cpu_seconds": timing["wall_seconds"] - timing["cpu_seconds"],
                }
            )
    return observations


def review(probe, closed):
    observations = timing_rows(probe)
    plan = prior_plan()
    setups = probe["setup"]
    if [s["case_id"] for s in setups] != [e["case"]["case_id"] for e in plan["entries"]]:
        raise ValueError("complete ordered setup population differs")
    if any(
        not math.isfinite(s[k]) or s[k] <= 0
        for s in setups
        for k in ("wall_seconds", "cpu_seconds")
    ):
        raise ValueError("finite positive setup timing required")
    groups = {
        "all": observations,
        **{scale: [o for o in observations if o["scale"] == scale] for scale in ("small", "large")},
        **{f"repeat_{i}": [o for o in observations if o["repeat"] == i] for i in range(3)},
        **{
            f"{r['case_id']}/{r['state']}": [
                o for o in observations if (o["case_id"], o["state"]) == (r["case_id"], r["state"])
            ]
            for r in probe["rows"]
        },
    }
    distributions = {
        name: {
            metric: stats([o[metric] for o in group])
            for metric in ("wall_seconds", "cpu_seconds", "wall_minus_cpu_seconds")
        }
        for name, group in groups.items()
    }
    units = {
        "original_maximum": [
            distributions[s]["wall_seconds"]["maximum"] for s in ("small", "large")
        ],
        "wall_minimum": [distributions[s]["wall_seconds"]["minimum"] for s in ("small", "large")],
        "wall_median": [distributions[s]["wall_seconds"]["median"] for s in ("small", "large")],
        "cpu_minimum": [distributions[s]["cpu_seconds"]["minimum"] for s in ("small", "large")],
        "zero_small": [0.0, distributions["large"]["wall_seconds"]["minimum"]],
    }
    multiplier = plan["fit_seeds"] * plan["fit_epochs"] * plan["cost_factor"]
    fixed = plan["baseline_fit_seconds"] + closed["charged_seconds"]
    scenarios = {}
    for name, times in units.items():
        contributions = [
            multiplier * n * t for n, t in zip(plan["fit_population"], times, strict=True)
        ]
        scenarios[name] = {
            "unit_seconds": times,
            "physics_seconds_by_scale": contributions,
            "additional_physics_seconds": sum(contributions),
            "total_prospective_seconds": sum(contributions) + fixed,
            "diagnostic_only": name != "original_maximum",
        }
    original = scenarios["original_maximum"]
    for k in ("additional_physics_seconds", "total_prospective_seconds"):
        if not math.isclose(original[k], closed["fit_proxy"][k], rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("unchanged original maximum-time proxy differs")
    available = 7200 - fixed
    phase_needed = (
        original["total_prospective_seconds"] > 7200
        and scenarios["zero_small"]["total_prospective_seconds"] > 7200
    )
    return {
        "plan": plan_payload(),
        "observations": observations,
        "distributions": distributions,
        "setup": {k: stats([s[k] for s in setups]) for k in ("wall_seconds", "cpu_seconds")},
        "scenarios": scenarios,
        "budget_requirements": {
            "available_physics_seconds": available,
            "weighted_unit_target_seconds": available / multiplier / sum(plan["fit_population"]),
            "isolated_scale_unit_ceiling_seconds": [
                available / multiplier / n for n in plan["fit_population"]
            ],
            "required_common_speedup": original["additional_physics_seconds"] / available,
            "required_fractional_physics_reduction": 1
            - available / original["additional_physics_seconds"],
        },
        "prior_processes": closed["processes"],
        "prior_charge_seconds_unchanged": closed["charged_seconds"],
        "prior_peak_rss_bytes_unchanged": closed["peak_rss_bytes"],
        "original_cost_gate_passed": False,
        "phase_costs_available": False,
        "full_fit_memory_feasibility_pending": True,
        "next_slice": PHASE_NEXT if phase_needed else STABILITY_NEXT,
        "next_slice_started": False,
        "repaired_gate": False,
        "final_access": False,
        "old_fresh_sealed": True,
        "solver_calls": 0,
        "fits": 0,
        "claim": "cost_review_only_not_revised_gate_or_acceleration",
    }


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    root, output = args.probe_root.resolve(), args.output_root.resolve()
    roots(root, output)
    if args.execute and (
        (root.name, output.name)
        != ("b4-15-offline-compliance-adjoint", "b4-16-offline-adjoint-cost-review")
        or root.parent != output.parent
    ):
        raise ValueError("requires fixed sibling external roots")
    return args, root, output


def main(argv=None):
    started = perf_counter()
    args, root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    target = output / "review.json"
    if target.exists():
        raise ValueError("refuses to overwrite cost review")
    revision = execution_release(output)
    bound = check_inputs(root)
    result = review(read(root, "probe.json", PROBE_SHA), bound["resource_close.json"])
    result["prior_native_profiles"] = native_profiles(root)
    check_inputs(root)
    result.update(
        source_revision=revision,
        input_sha256=PROBE_SHA,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
    )
    if result["charged_seconds"] > 60 or result["peak_rss_bytes"] > 1073741824:
        raise RuntimeError("cost review exceeds cap")
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(
        canonical(
            {k: result[k] for k in ("next_slice", "charged_seconds", "peak_rss_bytes")}
        ).decode(),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
