"""Read-only FEM bottleneck and finite training-objective method review."""

import argparse
import math
from pathlib import Path
from time import perf_counter

from b4_14_generalist_method_review import canonical, execution_release, peak_rss, read, roots
from b4_15_offline_compliance_adjoint import safe_hash, sha
from b4_16_offline_adjoint_cost_review import stats
from b4_17_prepared_fem_probe import COST_NEXT
from b4_17_prepared_fem_probe import check_inputs as check_prior
from b4_17_prepared_fem_probe import plan_payload as prior_plan

VERSION = "topolab.b4_18.fem-objective-method-review.v1"
PROBE_SHA = "009478f60ba859c2ed4ad6072e09efe9d6a296650c73acc1cc31686e8cc4491b"
BINDINGS = {
    "audit_receipts/plan.json": "7844801266232c5d7637628167fe27979319bde9eba5cfa8701481f3d574b7c7",
    "audit_receipts/production_release.json": (
        "6ae265e7464293945220f7e395ca2a26655f88154d0253eca41537831c7c2889"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "61890b2b7ef2f9be76b26458da294d7c2330fd69a70885b4091169449c44c42b"
    ),
    "independent_audit.json": "ed1c8e4c7946639ca535094b26b707cbef75850f708d83c347e46c4872e3b413",
    "resource_close.json": "83c211164fffd693256d611f926f1128d8f0938174ea3bdee1ef6faf4bfbdf2d",
    "audit_receipts/execution_commands.json": (
        "a081f939cffc5bc6dcdabd2688afe14e1552538959971d2aa5a616035d4af529"
    ),
    "audit_receipts/plan_command.json": (
        "89194bc5d1bc94d4ea0e4b1fe13ce2d92b5fa75709033688a904a843521f371b"
    ),
    "audit_receipts/closure_command.json": (
        "fb02ee086b461601f4e971a7ed8c9c37bb1cc1654bf01fd45972707870073647"
    ),
    "audit_receipts/closure_profile_verification.json": (
        "65b9123f275ac6b370deb395187a43c1c14d3a8551d39f1f2653a6a14993244e"
    ),
    "audit_receipts/postexit_command.json": (
        "6a24b176e75896595a407ed8ca2e686a1d4b584ae3d2e8902675f7225fe526ab"
    ),
    "audit_receipts/postexit_controller_reservation.json": (
        "0fcd8a93abd37cd020eac9641b6e3f6b9a0edad23b0df1ef4da46d76a5ee9899"
    ),
    "audit_receipts/evidence_release.json": (
        "29fc8c9376bc794e6599aa1a8e5e29a0ce1fcd8069e6c71504e99ec15761c823"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "d9f60547f4086596ea8f2e100134037a2adeb7ad1d563d1e62b427ef06fba8bd"
    ),
}
SURROGATE_NEXT = "B4.19 bounded train-only local compliance-surrogate feasibility probe"
SOLVER_NEXT = "B4.19 bounded exact-FEM method preregistration"
METHODS = {
    "immutable_setup_reuse": "stopped_failed_B4_17_cost_gate",
    "startup_only_repair": "startup_descriptions_cannot_replace_frozen_gate",
    "stale_numeric_factorization": "incompatible_with_changing_density_and_exact_adjoint",
    "new_ordering_or_iterative_solver": "deferred_requires_separate_numerical_cost_contract",
    "fixed_terminal_weighted_mse": "prior_B4_6_confirmation_reliability_failure_preserved",
    "local_signed_compliance_tangent": "train_only_fidelity_gradient_cost_probe_before_any_fit",
}


def plan_payload():
    payload = {
        "version": VERSION,
        "bindings": BINDINGS,
        "probe_sha256": PROBE_SHA,
        "prior_plan_sha256": prior_plan()["plan_sha256"],
        "cases": 8,
        "states": 16,
        "paired_measurements": 96,
        "phase_intervals": 96,
        "methods": METHODS,
        "scenarios": [
            "prepared_maximum",
            "prepared_minimum",
            "zero_small",
            "zero_factorization_instrumented",
        ],
        "fit_population": [432, 76],
        "fit_seeds": 3,
        "fit_epochs": 200,
        "cost_factor": 1.25,
        "future_fit_seconds": 7200,
        "factorization_share_decision": 0.5,
        "max_seconds": 240,
        "process_seconds": 60,
        "closure_seconds": 60,
        "max_rss_bytes": 1073741824,
        "solver_calls": 0,
        "fits": 0,
        "label_model_byte_reads": 0,
        "final_access": False,
        "arithmetic_tolerance": 1e-12,
        "decision_order": [SURROGATE_NEXT, SOLVER_NEXT],
    }
    return {**payload, "plan_sha256": sha(canonical(payload))}


def check_inputs(root):
    bound = {p: read(root, p, d) for p, d in BINDINGS.items()}
    closed, audit, proof, control, evidence = (
        bound[p]
        for p in (
            "resource_close.json",
            "independent_audit.json",
            "audit_receipts/closure_profile_verification.json",
            "audit_receipts/postexit_controller_reservation.json",
            "audit_receipts/evidence_release.json",
        )
    )
    if (
        bound["audit_receipts/plan.json"] != prior_plan()
        or not audit["passed"]
        or not audit["numerical_passed"]
        or audit["measurements"] != 96
        or audit["phase_observations"] != 96
        or audit["total_solver_calls"] != 256
        or audit["probe_sha256"] != PROBE_SHA
        or not closed["closed"]
        or not closed["numerical_passed"]
        or closed["feasibility_passed"]
        or closed["fit_proxy"]["cost_feasible"]
        or closed["next_slice"] != COST_NEXT
        or closed["probe_sha256"] != PROBE_SHA
        or not math.isclose(closed["charged_seconds"], 112.34, rel_tol=1e-12, abs_tol=1e-12)
        or not proof["passed"]
        or not control["passed"]
        or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]
        or control["resource_close_sha256"] != BINDINGS["resource_close.json"]
        or control["combined_reserved_charge_seconds"] > 60
        or not evidence["all_applicable_ci_passed_before_merge"]
        or not evidence["merged_tree_equals_tested_tree"]
        or evidence["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
        or any(
            v["repaired_gate"] or v["final_access"] or not v["old_fresh_sealed"]
            for v in (closed, evidence)
        )
    ):
        raise ValueError("requires complete closed numerical-pass/cost-fail B4.17 evidence")
    for name, digest in closed["profile_sha256"].items():
        safe_hash(root, "profiles/" + name, digest)
    safe_hash(root, "profiles/closure.time", proof["closure_profile_sha256"])
    for name, key in (("plan", "plan_profile_sha256"), ("verification", "success_profile_sha256")):
        safe_hash(root, "profiles/" + name + ".time", control[key])
    check_prior(root.parent / "b4-16-offline-adjoint-cost-review")
    return bound


def timing_population(probe):
    plan = prior_plan()
    entries, phases = plan["entries"], plan["phases"]
    expected = [(e["case"]["case_id"], state) for e in entries for state in plan["states"]]
    if probe["plan"] != plan or [(r["case_id"], r["state"]) for r in probe["rows"]] != expected:
        raise ValueError("complete ordered fixture population differs")
    observations, phase_rows = [], []
    for i, row in enumerate(probe["rows"]):
        scale = (
            "small"
            if entries[i // 2]["case"]["problem"]["mesh"]["element_counts"][0] == 12
            else "large"
        )
        order = [
            (j, a)
            for j in range(3)
            for a in (("prepared", "original") if j % 2 == 0 else ("original", "prepared"))
        ]
        if row["scale"] != scale or [(m["repeat"], m["arm"]) for m in row["measurements"]] != order:
            raise ValueError("complete paired order or scale differs")
        if [p["phase"] for p in row["phases"]] != phases:
            raise ValueError("complete ordered phase population differs")
        for timer in [*row["measurements"], *row["phases"], row["phase_total"]]:
            if any(
                not math.isfinite(timer[k]) or timer[k] <= 0
                for k in ("wall_seconds", "cpu_seconds")
            ):
                raise ValueError("finite positive complete timer required")
        for k in ("wall_seconds", "cpu_seconds"):
            residual = row["phase_total"][k] - math.fsum(p[k] for p in row["phases"])
            if residual < -1e-12 or not math.isclose(
                residual, row["phase_residual"][k], rel_tol=1e-12, abs_tol=1e-12
            ):
                raise ValueError("exclusive phase sum or residual differs")
        identity = {"case_id": row["case_id"], "state": row["state"], "scale": scale}
        observations.extend(
            {**identity, **{k: m[k] for k in ("repeat", "arm", "wall_seconds", "cpu_seconds")}}
            for m in row["measurements"]
        )
        phase_rows.append(
            {**identity, **{k: row[k] for k in ("phases", "phase_total", "phase_residual")}}
        )
    setup = probe["setup"]
    if [(s["case_id"], s["arm"]) for s in setup] != [
        (e["case"]["case_id"], a) for e in entries for a in ("original", "prepared")
    ]:
        raise ValueError("complete ordered setup population differs")
    for s in setup:
        if any(not math.isfinite(s[k]) or s[k] <= 0 for k in ("wall_seconds", "cpu_seconds")):
            raise ValueError("finite positive setup required")
        if s["arm"] == "prepared" and (
            type(s["retained_array_bytes"]) is not int or s["retained_array_bytes"] <= 0
        ):
            raise ValueError("positive prepared retained bytes required")
    return observations, phase_rows


def review(probe, closed):
    observations, phase_rows = timing_population(probe)
    scales = ("small", "large")
    distributions, attribution, setup = {}, {}, {}
    for scale in scales:
        selected = [o for o in observations if o["scale"] == scale]
        distributions[scale] = {
            a: {
                k: stats([o[k] for o in selected if o["arm"] == a])
                for k in ("wall_seconds", "cpu_seconds")
            }
            for a in ("prepared", "original")
        }
        rows = [r for r in phase_rows if r["scale"] == scale]
        attribution[scale] = {}
        for metric in ("wall_seconds", "cpu_seconds"):
            sums = {
                p: math.fsum(t[metric] for r in rows for t in r["phases"] if t["phase"] == p)
                for p in prior_plan()["phases"]
            }
            total = math.fsum(r["phase_total"][metric] for r in rows)
            attribution[scale][metric] = {
                "phase_sums": sums,
                "outer_sum": total,
                "residual_sum": math.fsum(r["phase_residual"][metric] for r in rows),
                "factorization_share": sums["factorization"] / total,
            }
        ids = {o["case_id"] for o in selected}
        timers = [s for s in probe["setup"] if s["case_id"] in ids and s["arm"] == "prepared"]
        setup[scale] = {
            "wall": stats([s["wall_seconds"] for s in timers]),
            "cpu": stats([s["cpu_seconds"] for s in timers]),
            "retained_array_maximum_bytes": max(s["retained_array_bytes"] for s in timers),
        }
    prepare = 3.75 * sum(
        n * setup[s]["wall"]["maximum"] for n, s in zip((432, 76), scales, strict=True)
    )
    fixed = 3870.204341 + 84.33 + 55.99 + closed["charged_seconds"] + prepare
    units = {
        "prepared_maximum": [
            distributions[s]["prepared"]["wall_seconds"]["maximum"] for s in scales
        ],
        "prepared_minimum": [
            distributions[s]["prepared"]["wall_seconds"]["minimum"] for s in scales
        ],
        "zero_small": [0.0, distributions["large"]["prepared"]["wall_seconds"]["minimum"]],
        "zero_factorization_instrumented": [
            max(
                r["phase_total"]["wall_seconds"]
                - next(p["wall_seconds"] for p in r["phases"] if p["phase"] == "factorization")
                for r in phase_rows
                if r["scale"] == s
            )
            for s in scales
        ],
    }
    scenarios = {}
    for name, times in units.items():
        contribution = [750 * n * t for n, t in zip((432, 76), times, strict=True)]
        scenarios[name] = {
            "unit_seconds": times,
            "physics_seconds_by_scale": contribution,
            "additional_physics_seconds": math.fsum(contribution),
            "total_prospective_seconds": math.fsum(contribution) + fixed,
            "diagnostic_only": name != "prepared_maximum",
        }
    original = scenarios["prepared_maximum"]
    if any(
        not math.isclose(original[k], closed["fit_proxy"][k], rel_tol=1e-12, abs_tol=1e-12)
        for k in ("additional_physics_seconds", "total_prospective_seconds")
    ):
        raise ValueError("original prepared maximum proxy differs")
    array_bytes = sum(
        n * setup[s]["retained_array_maximum_bytes"] for n, s in zip((432, 76), scales, strict=True)
    )
    if array_bytes != closed["fit_proxy"]["population_retained_array_bytes_estimate"]:
        raise ValueError("original population array estimate differs")
    available = 7200 - fixed
    if available <= 0:
        raise ValueError("fixed costs leave no conditional budget")
    use_surrogate = (
        original["total_prospective_seconds"] > 7200
        and scenarios["zero_small"]["total_prospective_seconds"] > 7200
        and attribution["large"]["wall_seconds"]["factorization_share"] >= 0.5
    )
    return {
        "plan": plan_payload(),
        "observations": observations,
        "phase_rows": phase_rows,
        "distributions": distributions,
        "phase_attribution": attribution,
        "setup": setup,
        "scenarios": scenarios,
        "full_population_preparation_seconds": prepare,
        "budget_requirements": {
            "available_physics_seconds": available,
            "weighted_unit_target_seconds": available / (750 * 508),
            "isolated_scale_unit_ceiling_seconds": [available / (750 * n) for n in (432, 76)],
            "required_common_speedup": original["additional_physics_seconds"] / available,
        },
        "memory": {
            "population_static_array_bytes_estimate": array_bytes,
            "four_gib_minus_static_bytes": 4294967296 - array_bytes,
            "full_fit_feasibility_pending": True,
        },
        "method_dispositions": METHODS,
        "prior_charge_seconds_unchanged": closed["charged_seconds"],
        "prior_peak_rss_bytes_unchanged": closed["peak_rss_bytes"],
        "original_b4_15_proxy_seconds_unchanged": 60339.39413004646,
        "original_cost_gate_passed": False,
        "next_slice": SURROGATE_NEXT if use_surrogate else SOLVER_NEXT,
        "next_slice_started": False,
        "repaired_gate": False,
        "final_access": False,
        "old_fresh_sealed": True,
        "solver_calls": 0,
        "fits": 0,
        "claim": "method_review_only_not_revised_gate_or_acceleration",
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
        != ("b4-17-prepared-fem-probe", "b4-18-fem-objective-method-review")
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
        raise ValueError("refuses to overwrite method review")
    revision = execution_release(output)
    bound = check_inputs(root)
    result = review(read(root, "probe.json", PROBE_SHA), bound["resource_close.json"])
    check_inputs(root)
    result.update(
        source_revision=revision,
        input_sha256=PROBE_SHA,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
    )
    if result["charged_seconds"] > 60 or result["peak_rss_bytes"] > 1073741824:
        raise RuntimeError("method review exceeds cap")
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
