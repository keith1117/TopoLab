"""Uncached FEM/Brent reconstruction of every B4.19 anchor, center and side."""

from pathlib import Path
from time import perf_counter

import numpy as np
from b4_15_independent_audit import energy, independent_state
from b4_19_local_compliance_surrogate import (
    arguments,
    canonical,
    check_budget,
    check_inputs,
    execution_release,
    peak_rss,
    plan_payload,
    read,
    selected_entries,
    sha,
    state_specs,
    train_label,
)

from topolab.baselines import _case_system
from topolab.simp import build_density_filter


def relative_metrics(value, exact, gradient, exact_gradient):
    delta = exact - 1
    residual = abs(value - exact)
    return {
        "normalized_value_error": residual,
        "increment_relative_error": residual / max(abs(delta), 1e-5),
        "gradient_relative_error": float(
            np.linalg.norm(gradient - exact_gradient) / max(np.linalg.norm(exact_gradient), 1e-8)
        ),
        "increment_sign_agrees": abs(delta) <= 1e-5 or bool(np.sign(value - 1) == np.sign(delta)),
        "surrogate_gradient_norm": float(np.linalg.norm(gradient)),
        "exact_gradient_norm": float(np.linalg.norm(exact_gradient)),
    }


def audit(probe, data, index, started):
    from b4_16_independent_audit import agree

    entries = list(selected_entries())
    if (
        probe["plan"] != plan_payload()
        or probe["solver_calls"] != 208
        or probe["fits"]
        or probe["new_labels"]
        or probe["final_access"]
        or probe["repaired_gate"]
        or not probe["old_fresh_sealed"]
    ):
        raise ValueError("frozen probe boundary differs")
    ids = [e.case.case_id for e in entries]
    if [r["case_id"] for r in probe["labels"]] != ids or [
        r["case_id"] for r in probe["setup"]
    ] != ids:
        raise ValueError("anchor/setup population differs")
    if [(r["case_id"], r["state"]) for r in probe["rows"]] != [
        (cid, j) for cid in ids for j in range(9)
    ]:
        raise ValueError("complete ordered state population differs")
    checks, conditions, local, errors = [], 0, [], []
    exact_fd_errors = []
    side_rows = 0
    for entry, label, setup in zip(entries, probe["labels"], probe["setup"], strict=True):
        check_budget(started)
        record, artifact = train_label(data, index, entry)
        anchor = np.asarray(record.stored.design_density)
        normalizer = record.stored.compliance
        if (
            label["artifact"] != artifact
            or label["normalizer"] != normalizer
            or not np.array_equal(label["anchor"], anchor)
        ):
            raise ValueError("anchor artifact or origin differs")
        mesh, loads, constrained = _case_system(entry.case)
        filt = build_density_filter(mesh, entry.case.problem.optimization.filter_radius)
        operator = filt.matrix.multiply((1 / filt.row_sums)[:, None]).tocsr()
        physical = np.asarray(operator @ anchor)
        compliance, sensitivity = energy(entry.case, physical, mesh, loads, constrained)
        signed = np.asarray(operator.T @ sensitivity) / normalizer
        weights = np.asarray(operator.sum(axis=0)).ravel() / anchor.size
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
            raise ValueError("preparation bytes/timer differs")
        checks.extend(
            [
                bool(np.isclose(compliance, normalizer, rtol=1e-9, atol=0)),
                bool(np.isclose(label["anchor_compliance"], compliance, rtol=1e-9, atol=0)),
                bool(np.allclose(label["design_gradient"], signed, rtol=1e-9, atol=1e-10)),
                bool(np.isclose(label["stored_volume"], physical.mean(), rtol=0, atol=1e-12)),
            ]
        )
        i = np.arange(1, anchor.size + 1)
        for j, spec in enumerate(state_specs()):
            check_budget(started)
            row = probe["rows"][ids.index(entry.case.case_id) * 9 + j]
            region, amplitude, direction, sign = spec
            d = np.sin(0.37 * i) if direction == "sine" else np.cos(0.13 * i)
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
                raise ValueError("fixed fixture/scale differs")
            design, rho, free, exact_gradient, exact = independent_state(
                entry.case, raw, normalizer
            )
            gradient = np.where(
                free, signed - weights * np.sum(signed[free]) / np.sum(weights[free]), 0.0
            )
            value = 1 + float(signed @ (design - anchor))
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
                        np.max(
                            abs(
                                np.asarray(row["physical"])
                                - np.asarray(record.stored.physical_density)
                            )
                        )
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
            # Reconstruct arithmetic from retained candidate numbers exactly, then
            # check the independent physics separately above at frozen tolerances.
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
                [(d, h) for d in ("sine", "cosine") for h in (1e-4, 2e-4)] if j in (0, 4) else []
            )
            if [(x["direction"], x["step"]) for x in row["differences"]] != expected:
                raise ValueError("complete directional population differs")
            for item in row["differences"]:
                d = np.sin(0.37 * i) if item["direction"] == "sine" else np.cos(0.13 * i)
                d /= max(abs(d))
                h = item["step"]
                for sign, side in zip((1, -1), item["sides"], strict=True):
                    side_design, _, side_free, _, side_exact = independent_state(
                        entry.case, raw + sign * h * d, normalizer
                    )
                    side_value = 1 + float(signed @ (side_design - anchor))
                    checks.extend(
                        [
                            bool(np.isclose(side["surrogate"], side_value, rtol=1e-9, atol=1e-10)),
                            bool(np.isclose(side["exact"], side_exact, rtol=1e-9, atol=0)),
                            bool(np.array_equal(side["free"], side_free)),
                        ]
                    )
                plus, minus = item["sides"]
                fd = (plus["surrogate"] - minus["surrogate"]) / (2 * h)
                adjoint = float(np.asarray(row["gradient"]) @ d)
                error = abs(fd - adjoint) / max(abs(fd), abs(adjoint), 1e-8)
                stable = all(np.array_equal(s["free"], row["free"]) for s in item["sides"])
                reconstructed = {
                    "surrogate_fd": fd,
                    "surrogate_derivative": adjoint,
                    "surrogate_error": error,
                    "same_active_set": stable,
                    "exact_fd": (plus["exact"] - minus["exact"]) / (2 * h),
                    "exact_derivative": float(np.asarray(row["exact_gradient"]) @ d),
                }
                conditions += agree(reconstructed, {k: item[k] for k in reconstructed})
                checks.extend([stable, error <= 1e-4])
                errors.append(error)
                side_rows += 1
                exact_fd_errors.append(
                    abs(reconstructed["exact_fd"] - reconstructed["exact_derivative"])
                    / max(
                        abs(reconstructed["exact_fd"]), abs(reconstructed["exact_derivative"]), 1e-8
                    )
                )
    return {
        "passed": True,
        "integrity_passed": all(checks),
        "numerical_conditions": len(checks),
        "arithmetic_conditions": conditions,
        "failed_numerical_conditions": sum(not c for c in checks),
        "local_states": len(local),
        "local_states_passed": sum(local),
        "local_fidelity_passed": all(local),
        "directional_rows": side_rows,
        "maximum_surrogate_directional_error": max(errors),
        "maximum_exact_directional_error_diagnostic": max(exact_fd_errors),
        "measurements": 216,
        "central_states": 72,
        "cases": 8,
        "independent_solver_calls": 208,
        "total_solver_calls": 416,
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
    target = output / "independent_audit.json"
    if target.exists():
        raise ValueError("refuses to overwrite independent audit")
    revision = execution_release(output)
    index = check_inputs(root, data)
    probe = read(output, "probe.json")
    if probe["source_revision"] != revision:
        raise ValueError("source revision differs")
    result = audit(probe, data, index, started)
    check_inputs(root, data)
    result.update(
        source_revision=revision,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
        source_sha256=sha(Path(__file__).read_bytes()),
    )
    check_budget(started)
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


def independent_proxy(probe, charge):
    scales = ("small", "large")
    maximum = [
        max(t["wall_seconds"] for r in probe["rows"] if r["scale"] == s for t in r["timings"])
        for s in scales
    ]
    by_id = {r["case_id"]: r["scale"] for r in probe["rows"]}
    preparation = [
        max(r["wall_seconds"] for r in probe["setup"] if by_id[r["case_id"]] == s) for s in scales
    ]
    byte_counts = [
        max(r["retained_array_bytes"] for r in probe["setup"] if by_id[r["case_id"]] == s)
        for s in scales
    ]
    forward = 750 * (432 * maximum[0] + 76 * maximum[1])
    setup = 3.75 * (432 * preparation[0] + 76 * preparation[1])
    return {
        "additional_surrogate_seconds": forward,
        "full_population_preparation_seconds": setup,
        "population_retained_array_bytes_estimate": 432 * byte_counts[0] + 76 * byte_counts[1],
        "total_prospective_seconds": forward
        + setup
        + 3870.204341
        + 84.33
        + 55.99
        + 112.34
        + 86.13
        + charge,
    }


if __name__ == "__main__":
    raise SystemExit(main())
