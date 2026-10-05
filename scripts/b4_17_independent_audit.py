"""Independent uncached FEM, Brent projection and complete B4.17 cost arithmetic."""

import math
from pathlib import Path
from time import perf_counter

import numpy as np
from b4_15_independent_audit import independent_state
from b4_17_prepared_fem_probe import (
    arguments,
    canonical,
    check_budget,
    check_inputs,
    direction_vector,
    execution_release,
    input_states,
    peak_rss,
    plan_payload,
    raw_fixture,
    read,
    selected_entries,
    sha,
)


def population(probe):
    plan = plan_payload()
    ids = [e["case"]["case_id"] for e in plan["entries"]]
    if (
        probe["plan"] != plan
        or probe["solver_calls"] != 240
        or probe["fits"]
        or probe["final_access"]
        or probe["repaired_gate"]
        or not probe["old_fresh_sealed"]
    ):
        raise ValueError("frozen complete prepared probe boundary differs")
    if [(r["case_id"], r["state"]) for r in probe["rows"]] != [
        (cid, s) for cid in ids for s in plan["states"]
    ] or [(s["case_id"], s["arm"]) for s in probe["setup"]] != [
        (cid, a) for cid in ids for a in ("original", "prepared")
    ]:
        raise ValueError("ordered complete state/setup population differs")
    for row in probe["rows"]:
        if [(m["repeat"], m["arm"]) for m in row["measurements"]] != [
            (i, a)
            for i in range(3)
            for a in (("prepared", "original") if i % 2 == 0 else ("original", "prepared"))
        ] or [p["phase"] for p in row["phases"]] != plan["phases"]:
            raise ValueError("complete paired or phase timing population differs")
        if [(d["direction"], d["step"]) for d in row["differences"]] != [
            (d, h) for d in plan["directions"] for h in plan["steps"]
        ]:
            raise ValueError("complete directional population differs")
        for m in [*row["measurements"], *row["phases"], row["phase_total"]]:
            if any(not math.isfinite(m[k]) or m[k] <= 0 for k in ("wall_seconds", "cpu_seconds")):
                raise ValueError("finite positive complete timing required")
        for k in ("wall_seconds", "cpu_seconds"):
            residual = row["phase_total"][k] - math.fsum(p[k] for p in row["phases"])
            if residual < -1e-12 or not math.isclose(
                row["phase_residual"][k], residual, rel_tol=1e-12, abs_tol=1e-12
            ):
                raise ValueError("exclusive phase total/residual differs")
    for setup in probe["setup"]:
        if any(
            not math.isfinite(setup[k]) or setup[k] <= 0 for k in ("wall_seconds", "cpu_seconds")
        ):
            raise ValueError("finite positive complete setup timing required")
        if setup["arm"] == "prepared" and (
            not isinstance(setup["retained_array_bytes"], int) or setup["retained_array_bytes"] <= 0
        ):
            raise ValueError("prepared retained byte population differs")


def cost_basis(probe):
    population(probe)
    ids = {e["case"]["case_id"]: e for e in plan_payload()["entries"]}
    result = {}
    for scale, nx in (("small", 12), ("large", 24)):
        rows = [
            r
            for r in probe["rows"]
            if ids[r["case_id"]]["case"]["problem"]["mesh"]["element_counts"][0] == nx
        ]
        if any(r["scale"] != scale for r in rows):
            raise ValueError("case scale differs")
        timings = {
            a: [m for r in rows for m in r["measurements"] if m["arm"] == a]
            for a in ("prepared", "original")
        }
        setups = [
            s
            for s in probe["setup"]
            if s["arm"] == "prepared"
            and ids[s["case_id"]]["case"]["problem"]["mesh"]["element_counts"][0] == nx
        ]
        result[scale] = {
            "prepared_maximum_wall": max(m["wall_seconds"] for m in timings["prepared"]),
            "original_maximum_wall": max(m["wall_seconds"] for m in timings["original"]),
            "prepared_setup_maximum_wall": max(s["wall_seconds"] for s in setups),
            "retained_array_maximum_bytes": max(s["retained_array_bytes"] for s in setups),
            "wall_sums": {a: math.fsum(m["wall_seconds"] for m in t) for a, t in timings.items()},
            "cpu_sums": {a: math.fsum(m["cpu_seconds"] for m in t) for a, t in timings.items()},
            "phase_wall_sums": {
                p: math.fsum(
                    t["wall_seconds"] for r in rows for t in r["phases"] if t["phase"] == p
                )
                for p in plan_payload()["phases"]
            },
            "phase_cpu_sums": {
                p: math.fsum(t["cpu_seconds"] for r in rows for t in r["phases"] if t["phase"] == p)
                for p in plan_payload()["phases"]
            },
            "instrumented_wall_sum": math.fsum(r["phase_total"]["wall_seconds"] for r in rows),
            "instrumented_cpu_sum": math.fsum(r["phase_total"]["cpu_seconds"] for r in rows),
        }
    return result


def independent_proxy(probe, charge):
    basis = cost_basis(probe)
    physics = 750 * math.fsum(
        n * basis[s]["prepared_maximum_wall"] for s, n in (("small", 432), ("large", 76))
    )
    setup = (
        3
        * 1.25
        * math.fsum(
            n * basis[s]["prepared_setup_maximum_wall"] for s, n in (("small", 432), ("large", 76))
        )
    )
    total = physics + setup + 3870.204341 + 84.33 + 55.99 + charge
    return {
        "additional_physics_seconds": physics,
        "full_population_preparation_seconds": setup,
        "total_prospective_seconds": total,
        "cost_feasible": total <= 7200,
        "population_retained_array_bytes_estimate": sum(
            n * basis[s]["retained_array_maximum_bytes"] for s, n in (("small", 432), ("large", 76))
        ),
    }


def audit(probe, original, started):
    labels = input_states(original)
    if (
        probe["labels"] != original["labels"]
        or probe["input_sha256"] != plan_payload()["original_probe_sha256"]
    ):
        raise ValueError("certified normalizer/input identity differs")
    basis = cost_basis(probe)
    entries = {e.case.case_id: e for e in selected_entries()}
    checks, errors = [], []
    for row in probe["rows"]:
        check_budget(started)
        case = entries[row["case_id"]].case
        raw = raw_fixture(case, row["state"])
        if not np.array_equal(row["raw"], raw):
            raise ValueError("metadata fixture differs before independent solve")
        design, physical, free, gradient, value = independent_state(
            case, raw, labels[row["case_id"]]["normalizer"]
        )
        checks.extend(
            [
                bool(np.allclose(row["design"], design, rtol=0, atol=2e-11)),
                bool(np.allclose(row["physical"], physical, rtol=0, atol=2e-11)),
                bool(np.array_equal(row["free"], free)),
                bool(np.isclose(row["value"], value, rtol=1e-9, atol=0)),
                bool(
                    np.isclose(
                        row["compliance"],
                        value * labels[row["case_id"]]["normalizer"],
                        rtol=1e-9,
                        atol=0,
                    )
                ),
                bool(np.allclose(row["gradient"], gradient, rtol=1e-9, atol=1e-10)),
                abs(float(np.mean(row["physical"])) - case.problem.optimization.volume_fraction)
                <= 1e-12,
                abs(float(np.sum(row["gradient"]))) <= 1e-10,
            ]
        )
        for m in row["measurements"]:
            checks.extend(
                [
                    bool(np.isclose(m["value"], value, rtol=1e-9, atol=0)),
                    bool(np.allclose(m["gradient"], gradient, rtol=1e-9, atol=1e-10)),
                    bool(np.isclose(m["value"], row["value"], rtol=1e-9, atol=0)),
                    bool(np.allclose(m["gradient"], row["gradient"], rtol=1e-9, atol=1e-10)),
                ]
            )
        for d in row["differences"]:
            vector = direction_vector(raw.size, d["direction"])
            fd = (d["plus"] - d["minus"]) / (2 * d["step"])
            adjoint = float(np.asarray(row["gradient"]) @ vector)
            error = abs(fd - adjoint) / max(abs(fd), abs(adjoint), 1e-8)
            if not all(
                math.isclose(d[k], v, rel_tol=1e-12, abs_tol=1e-12)
                for k, v in (("fd", fd), ("adjoint", adjoint), ("error", error))
            ):
                raise ValueError("retained directional arithmetic differs")
            checks.extend(
                [
                    math.isfinite(error),
                    error <= 1e-4,
                    d["same_active_set"],
                    max(d["volume_errors"]) <= 1e-12,
                ]
            )
            errors.append(error)
    return {
        "passed": True,
        "numerical_passed": all(checks),
        "numerical_checks": len(checks),
        "failed_numerical_checks": sum(not x for x in checks),
        "directional_checks": len(errors),
        "maximum_directional_error": max(errors),
        "independent_solver_calls": 16,
        "total_solver_calls": 256,
        "measurements": 96,
        "phase_observations": 96,
        "cost_basis": basis,
        "probe_sha256": sha(canonical(probe)),
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
    }


def main(argv=None):
    started = perf_counter()
    args, root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    target = output / "independent_audit.json"
    if target.exists():
        raise ValueError("refuses to overwrite independent audit")
    revision = execution_release(output)
    check_inputs(root)
    probe = read(output, "probe.json")
    if probe["source_revision"] != revision:
        raise ValueError("source revision differs")
    original = read(
        root.parent / "b4-15-offline-compliance-adjoint",
        "probe.json",
        plan_payload()["original_probe_sha256"],
    )
    result = audit(probe, original, started)
    check_inputs(root)
    result.update(
        source_revision=revision,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
        source_sha256=sha(Path(__file__).read_bytes()),
    )
    check_budget(started)
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(
        canonical(
            {k: result[k] for k in ("numerical_passed", "numerical_checks", "total_solver_calls")}
        ).decode(),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
