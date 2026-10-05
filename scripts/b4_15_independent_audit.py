"""Independent assembly, energy adjoint and active-set arithmetic for B4.15."""

from pathlib import Path
from time import perf_counter

import numpy as np
from b4_15_offline_compliance_adjoint import (
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
    train_label,
)
from scipy.optimize import brentq

from topolab.baselines import _case_system
from topolab.fem import assemble_global_stiffness, hex8_element_stiffness, solve_linear_static
from topolab.simp import build_density_filter


def energy(case, physical, mesh, loads, constrained):
    p = case.problem
    unit = hex8_element_stiffness(
        1.0,
        p.material.poisson_ratio,
        dimensions=tuple(
            length / count for length, count in zip(mesh.lengths, mesh.element_counts, strict=True)
        ),
    )
    contrast = p.material.solid_modulus - p.material.minimum_modulus
    factors = p.material.minimum_modulus + contrast * physical**p.optimization.penalty
    stiffness = assemble_global_stiffness(mesh, unit, element_factors=factors)
    displacement = solve_linear_static(stiffness, loads, constrained).displacements
    ue = displacement[mesh.element_dofs]
    energies = np.einsum("ij,jk,ik->i", ue, unit, ue)
    sensitivity = (
        -p.optimization.penalty * contrast * physical ** (p.optimization.penalty - 1) * energies
    )
    return float(loads @ displacement), sensitivity


def independent_state(case, raw, normalizer):
    mesh, loads, constrained = _case_system(case)
    filt = build_density_filter(mesh, case.problem.optimization.filter_radius)
    operator = filt.matrix.multiply((1 / filt.row_sums)[:, None]).tocsr()
    weights = np.asarray(operator.sum(axis=0)).ravel() / raw.size
    minimum = case.problem.optimization.minimum_density
    volume = case.problem.optimization.volume_fraction
    offset = brentq(
        lambda s: float(weights @ np.clip(raw + s, minimum, 1)) - volume, -1.0, 1.0, xtol=1e-14
    )
    design = np.clip(raw + offset, minimum, 1.0)
    physical = np.asarray(operator @ design)
    free = (raw + offset > minimum) & (raw + offset < 1)
    compliance, physical_gradient = energy(case, physical, mesh, loads, constrained)
    filtered_gradient = np.asarray(operator.T @ physical_gradient) / normalizer
    free_gradient = filtered_gradient[free].sum()
    free_weights = weights[free].sum()
    gradient = np.where(free, filtered_gradient - weights * free_gradient / free_weights, 0.0)
    return design, physical, free, gradient, compliance / normalizer


def audit(probe, data_root, index, started):
    if probe["plan"] != plan_payload() or probe["solver_calls"] != 176 or probe["fits"]:
        raise ValueError("complete frozen probe differs")
    if probe["final_access"] or probe["repaired_gate"] or not probe["old_fresh_sealed"]:
        raise ValueError("sealed/failed repair boundary differs")
    entries = {e.case.case_id: e for e in selected_entries()}
    expected = [(cid, state) for cid in entries for state in ("interior", "clipped")]
    if [(r["case_id"], r["state"]) for r in probe["rows"]] != expected:
        raise ValueError("missing, duplicated or reordered probe state")
    if [r["case_id"] for r in probe["labels"]] != list(entries):
        raise ValueError("training label population differs")
    checks, normalizers = [], {}
    for row in probe["labels"]:
        check_budget(started)
        entry = entries[row["case_id"]]
        record, artifact = train_label(data_root, index, entry)
        if row["artifact"] != artifact or row["normalizer"] != record.stored.compliance:
            raise ValueError("training artifact/normalizer binding differs")
        mesh, loads, constrained = _case_system(entry.case)
        value, _ = energy(
            entry.case, np.asarray(record.stored.physical_density), mesh, loads, constrained
        )
        checks.append(bool(np.isclose(value, row["normalizer"], rtol=1e-9, atol=0)))
        normalizers[row["case_id"]] = row["normalizer"]
    errors, clipped, free_count = [], 0, 0
    for row in probe["rows"]:
        check_budget(started)
        case = entries[row["case_id"]].case
        raw = np.asarray(row["raw"])
        i = np.arange(1, int(np.prod(case.problem.mesh.element_counts)) + 1)
        fixed = (
            case.problem.optimization.volume_fraction
            + 0.02 * np.sin(0.37 * i)
            + 0.01 * np.cos(0.13 * i)
            if row["state"] == "interior"
            else np.resize(np.array([0.02, 0.5, 0.98]), i.size)
        )
        if not np.array_equal(raw, fixed):
            raise ValueError("raw fixture differs before independent solve")
        design, physical, free, gradient, value = independent_state(
            case, raw, normalizers[row["case_id"]]
        )
        checks.extend(
            [
                bool(np.allclose(row["design"], design, rtol=0, atol=2e-11)),
                bool(np.allclose(row["physical"], physical, rtol=0, atol=2e-11)),
                bool(np.array_equal(row["free"], free)),
                bool(np.isclose(row["value"], value, rtol=1e-9, atol=0)),
                bool(np.allclose(row["gradient"], gradient, rtol=1e-9, atol=1e-10)),
                row["volume_error"] <= 1e-12,
                bool(np.isclose(abs(float(gradient.sum())), 0, rtol=0, atol=1e-10)),
                row["repeat_gradient_max_difference"] == 0,
                row["repeat_values"] == [row["value"]] * 3,
            ]
        )
        clipped += int((~free).sum())
        free_count += int(free.sum())
        if len(row["timings"]) != 3 or not all(
            np.isfinite(t[k]) and t[k] > 0
            for t in row["timings"]
            for k in ("wall_seconds", "cpu_seconds")
        ):
            raise ValueError("complete timing population differs")
        if [(d["direction"], d["step"]) for d in row["differences"]] != [
            (name, h) for name in ("sine", "cosine") for h in (1e-4, 2e-4)
        ]:
            raise ValueError("difference direction/step population differs")
        for item in row["differences"]:
            direction = np.sin(0.37 * i) if item["direction"] == "sine" else np.cos(0.13 * i)
            direction /= np.max(np.abs(direction))
            fd = (item["plus"] - item["minus"]) / (2 * item["step"])
            adjoint = float(np.asarray(row["gradient"]) @ direction)
            error = abs(fd - adjoint) / max(abs(fd), abs(adjoint), 1e-8)
            if item["fd"] != fd or item["adjoint"] != adjoint or item["error"] != error:
                raise ValueError("retained directional arithmetic differs")
            checks.extend(
                [
                    bool(np.isfinite(error)),
                    error <= 1e-4,
                    item["same_active_set"],
                    max(item["volume_errors"]) <= 1e-12,
                ]
            )
            errors.append(error)
    numerical = all(checks) and clipped > 0 and free_count > 0
    return {
        "passed": True,
        "numerical_passed": numerical,
        "numerical_checks": len(checks),
        "failed_numerical_checks": sum(not c for c in checks),
        "directional_checks": len(errors),
        "maximum_directional_error": max(errors),
        "independent_solver_calls": 24,
        "total_solver_calls": 200,
        "clipped_entries": clipped,
        "free_entries": free_count,
        "probe_sha256": sha(canonical(probe)),
        "plan_sha256": plan_payload()["plan_sha256"],
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
    }


def main(argv=None):
    started = perf_counter()
    args, review_root, data_root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    target = output / "independent_audit.json"
    if target.exists():
        raise ValueError("refuses to overwrite independent audit")
    revision = execution_release(output)
    index = check_inputs(review_root, data_root)
    probe = read(output, "probe.json")
    if probe["source_revision"] != revision:
        raise ValueError("probe revision differs")
    result = audit(probe, data_root, index, started)
    check_inputs(review_root, data_root)
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


if __name__ == "__main__":
    raise SystemExit(main())
