"""Independent uncached physics, numerical roots and exact piece inequalities."""

import math
from fractions import Fraction
from functools import partial
from time import perf_counter

import numpy as np
from b4_28_common import (
    Journal,
    arguments,
    canonical,
    check_budget,
    digest,
    entries,
    event_prefix,
    failed,
    finish,
    label_index,
    legacy_inputs,
    plan_payload,
    read,
    release,
    sha,
    train_label,
)
from scipy.optimize import brentq
from scipy.sparse import coo_matrix

from topolab.baselines import _case_system
from topolab.fem import assemble_global_stiffness, hex8_element_stiffness, solve_linear_static


def independent_filter(mesh, radius):
    nx, ny, nz = mesh.element_counts
    dx, dy, dz = [
        length / count for length, count in zip(mesh.lengths, mesh.element_counts, strict=True)
    ]
    indices = np.arange(nx * ny * nz)
    xx, yy, zz = indices % nx, indices // nx % ny, indices // (nx * ny)
    rows, columns, values = [], [], []
    for i in indices:
        near = (
            (abs(xx - xx[i]) <= math.ceil(radius / dx))
            & (abs(yy - yy[i]) <= math.ceil(radius / dy))
            & (abs(zz - zz[i]) <= math.ceil(radius / dz))
        )
        for j in indices[near]:
            distance = math.sqrt(
                (int(xx[i] - xx[j]) * dx) ** 2
                + (int(yy[i] - yy[j]) * dy) ** 2
                + (int(zz[i] - zz[j]) * dz) ** 2
            )
            if radius > distance:
                rows.append(i)
                columns.append(j)
                values.append(radius - distance)
    matrix = coo_matrix((values, (rows, columns)), shape=(indices.size, indices.size)).tocsr()
    sums = np.asarray(matrix.sum(axis=1)).ravel()
    operator = matrix.multiply((1 / sums)[:, None]).tocsr()
    weights = np.asarray(matrix.T @ (1 / sums)).ravel() / indices.size
    return matrix, sums, operator, weights


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
    density_energy = np.einsum("ij,jk,ik->i", ue, unit, ue)
    sensitivity = (
        -p.optimization.penalty
        * contrast
        * physical ** (p.optimization.penalty - 1)
        * density_energy
    )
    return float(loads @ displacement), sensitivity


def root(raw, operator, weights, volume, minimum):
    offset = brentq(
        lambda s: float(weights @ np.clip(raw + s, minimum, 1)) - volume, -1, 1, xtol=1e-14
    )
    shifted = raw + offset
    margin = float(np.min(np.minimum(abs(shifted - minimum), abs(shifted - 1))))
    free = (shifted > minimum) & (shifted < 1)
    if margin <= 1e-10 or weights[free].sum() <= 0:
        raise ValueError("independent root has no unique kink-free derivative")
    design = np.clip(shifted, minimum, 1)
    physical = np.asarray(operator @ design)
    info = {
        "offset": offset,
        "weighted_volume_residual": float(weights @ design) - volume,
        "physical_volume_residual": float(physical.mean()) - volume,
        "kink_margin": margin,
    }
    if max(abs(info["weighted_volume_residual"]), abs(info["physical_volume_residual"])) > 1e-12:
        raise ValueError("independent volume differs")
    return design, physical, free, info


def close(a, b, rtol=0.0, atol=0.0):
    return (
        math.isfinite(float(a))
        and math.isfinite(float(b))
        and abs(float(a) - float(b)) <= atol + rtol * abs(float(b))
    )


def projection_checks(actual, expected):
    if set(actual) != set(expected):
        raise ValueError("complete retained projection fields required")
    return [
        close(actual["offset"], expected["offset"], atol=2e-11),
        close(actual["weighted_volume_residual"], expected["weighted_volume_residual"], atol=1e-12),
        close(actual["physical_volume_residual"], expected["physical_volume_residual"], atol=1e-12),
        close(actual["kink_margin"], expected["kink_margin"], atol=2e-11),
        abs(actual["weighted_volume_residual"]) <= 1e-12
        and abs(actual["physical_volume_residual"]) <= 1e-12
        and actual["kink_margin"] > 1e-10,
    ]


def physics_checks(actual, design, physical, free, info):
    return projection_checks(actual["projection"], info) + [
        bool(np.allclose(actual["design"], design, rtol=0, atol=2e-11)),
        bool(np.allclose(actual["physical"], physical, rtol=0, atol=2e-11)),
        bool(np.array_equal(actual["free"], free)),
    ]


def cotangent(gradient, weights, free):
    denominator = float(sum(weights[free]))
    if denominator <= 0:
        raise ValueError("no free denominator")
    return np.where(free, gradient - weights * float(sum(gradient[free])) / denominator, 0)


def fidelity(value, exact, gradient, exact_gradient):
    residual, delta = abs(value - exact), exact - 1
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


def arithmetic(expected, actual):
    if set(expected) != set(actual):
        raise ValueError("retained arithmetic fields differ")
    for key, value in expected.items():
        if type(value) is bool:
            valid = type(actual[key]) is bool and value == actual[key]
        else:
            valid = close(actual[key], value, 1e-12, 1e-12)
        if not valid:
            raise ValueError("retained arithmetic differs: " + key)
    return len(expected)


def pair(value):
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(type(v) is not int for v in value)
        or value[1] <= 0
    ):
        raise ValueError("canonical exact rational pair required")
    result = Fraction(*value)
    if [result.numerator, result.denominator] != value:
        raise ValueError("reduced rational pair required")
    return result


def prove_interval(raw, direction, weights, signed, volume, minimum, step, payload, retained):
    """Unique affine constraints prove all points, independently of the tracer."""
    z, d, w, g = [
        tuple(Fraction(float(v)) for v in vector) for vector in (raw, direction, weights, signed)
    ]
    v, m, h = [Fraction(float(x)) for x in (volume, minimum, step)]
    pieces = payload["pieces"]
    if payload["step"] != step or step not in (1e-4, 2e-4) or not 0 < len(pieces) <= 256:
        raise ValueError("original whole interval and piece bound required")
    cursor, increment, prior, transitions, center = -h, Fraction(), None, [], None
    for piece in pieces:
        left, right, labels = pair(piece["start"]), pair(piece["end"]), piece["partition"]
        if (
            left != cursor
            or not left < right <= h
            or len(labels) != len(z)
            or any(type(k) is not int or k not in (-1, 0, 1) for k in labels)
        ):
            raise ValueError("incomplete or invalid exact partition")
        active = [i for i, k in enumerate(labels) if k == 0]
        mass = sum((w[i] for i in active), Fraction())
        if mass <= 0:
            raise ValueError("no positive independent free mass")
        fixed = sum(
            (w[i] * (m if k == -1 else 1) for i, k in enumerate(labels) if k != 0), Fraction()
        )
        a = (v - fixed - sum((w[i] * z[i] for i in active), Fraction())) / mass
        b = -sum((w[i] * d[i] for i in active), Fraction()) / mass
        slope = sum((g[i] * (d[i] + b) for i in active), Fraction())
        endpoints = []
        for t in (left, right, (left + right) / 2):
            q = [zi + di * t + a + b * t for zi, di in zip(z, d, strict=True)]
            for qi, k in zip(q, labels, strict=True):
                if not (qi <= m if k == -1 else qi >= 1 if k == 1 else m <= qi <= 1) or (
                    left < t < right and qi in (m, 1)
                ):
                    raise ValueError("piece inequalities fail inside entire interval")
            x = tuple(
                m if k == -1 else Fraction(1) if k == 1 else qi
                for qi, k in zip(q, labels, strict=True)
            )
            if sum((wi * xi for wi, xi in zip(w, x, strict=True)), Fraction()) != v:
                raise ValueError("independent volume identity differs")
            endpoints.append(x)
        if any(
            pair(piece[key]) != expected
            for key, expected in [
                ("offset_start", a + b * left),
                ("offset_end", a + b * right),
                ("offset_slope", b),
                ("value_slope", slope),
            ]
        ) or [pair(x) for x in piece["residuals"]] != [Fraction(), Fraction()]:
            raise ValueError("retained affine scalar proof differs")
        if prior:
            old_labels, old_end, old_offset = prior
            changed = [
                i for i, (old, new) in enumerate(zip(old_labels, labels, strict=True)) if old != new
            ]
            if (
                not changed
                or old_end != endpoints[0]
                or old_offset != a + b * left
                or any(endpoints[0][i] not in (m, 1) for i in changed)
            ):
                raise ValueError("transition contact or exact continuity differs")
            transitions.append(changed)
        if left < 0 < right:
            center = (labels, a, b)
        if cursor == -h:
            first = endpoints[0]
        last = endpoints[1]
        increment += slope * (right - left)
        prior, cursor = (labels, endpoints[1], a + b * right), right
    if cursor != h or center is None:
        raise ValueError("missing coverage or undefined central derivative")
    if (
        increment
        != sum((gi * (b - a) for gi, a, b in zip(g, first, last, strict=True)), Fraction())
        or pair(payload["signed_increment"]) != increment
        or payload["transitions"] != transitions
    ):
        raise ValueError("whole signed integral or transitions differ")
    labels, a, _ = center
    if any(min(abs(x + a - m), abs(x + a - 1)) <= Fraction(1e-10) for x in z):
        raise ValueError("central kink has no selected derivative")
    secant = float(increment / (2 * h))
    plus, minus = retained["sides"]
    actual = (plus["surrogate"] - minus["surrogate"]) / (2 * step)
    stable = not transitions
    predicates = [
        abs(actual - secant) / max(abs(actual), abs(secant), 1e-8) <= 1e-4,
        close(plus["surrogate"] - minus["surrogate"], float(increment), 1e-12, 1e-12),
        not stable or close(retained["surrogate_derivative"], secant, 1e-9, 1e-10),
    ]
    expected = {
        "passed": all(predicates),
        "crossing": not stable,
        "predicates": predicates,
        "legacy_mask_passed": retained["same_active_set"],
        "legacy_fd_passed": retained["surrogate_error"] <= 1e-4,
    }
    if payload["checks"] != expected or not close(payload["secant"], secant, 0, 0):
        raise ValueError("retained new classification or secant differs")
    return {
        "passed": all(predicates),
        "crossing": not stable,
        "pieces": len(pieces),
        "predicates": predicates,
    }


def new_point(row, raw, weights, design, physical, free, info, signed, value, normalizer):
    witness = row["witness"]
    if (
        not np.array_equal(row["raw"], raw)
        or not np.array_equal(row["weights"], weights)
        or not np.array_equal(row["free"], free)
    ):
        raise ValueError("independent raw/filter/partition origin differs")
    gradient = cotangent(signed, weights, free)
    conditions = [
        bool(np.allclose(witness["design"], design, rtol=0, atol=2e-11)),
        bool(np.allclose(witness["physical"], physical, rtol=0, atol=2e-11)),
        bool(np.allclose(witness["gradient"], gradient, rtol=1e-9, atol=1e-10)),
        close(witness["offset"], info["offset"], atol=2e-11),
        close(witness["kink_margin"], info["kink_margin"], atol=2e-11),
        abs(float(weights @ np.asarray(witness["design"])) - value["volume"]) <= 1e-12,
        abs(float(np.mean(witness["physical"])) - value["volume"]) <= 1e-12,
        close(
            witness["weighted_residual"],
            float(weights @ np.asarray(witness["design"])) - value["volume"],
            atol=1e-12,
        ),
        close(
            witness["physical_residual"],
            float(np.mean(witness["physical"])) - value["volume"],
            atol=1e-12,
        ),
        abs(math.fsum(witness["gradient"])) <= 1e-10,
        witness["kink_margin"] > 1e-10,
        close(witness["value"], value["surrogate"], 1e-9, 1e-10),
        close(witness["compliance"], value["surrogate"] * normalizer, 1e-9),
        witness["torch_value"] == witness["value"],
        witness["torch_gradient"] == witness["gradient"],
    ]
    if len(witness["physical"]) != raw.size or not all(
        math.isfinite(x) for x in witness["gradient"]
    ):
        raise ValueError("complete finite point witness required")
    return conditions


def audit(produced, legacy, prior, data, index, journal, started):
    ids = [e.case.case_id for e in entries()]
    if (
        produced["plan"] != plan_payload()
        or [r["case_id"] for r in produced["labels"]] != ids
        or len(produced["points"]) != 200
        or len(produced["intervals"]) != 64
    ):
        raise ValueError("complete produced population required")
    point_rows, interval_rows = iter(produced["points"]), iter(produced["intervals"])
    old_flags, new_flags, local, interval_results, diagnostics = [], [], [], [], []
    arithmetic_count = 0
    for ci, entry in enumerate(entries()):
        check_budget(started)
        cid = entry.case.case_id
        settings = entry.case.problem.optimization
        record, artifact = journal.invoke(
            "label",
            cid,
            {"role": "train", "training_set": "expanded"},
            lambda entry=entry: train_label(data, index, entry),
            lambda item: {"artifact": item[1], "normalizer": item[0].stored.compliance},
        )
        anchor, normalizer = np.asarray(record.stored.design_density), record.stored.compliance
        label, new_label = legacy["labels"][ci], produced["labels"][ci]
        if any(
            r["artifact"] != artifact
            or r["normalizer"] != normalizer
            or not np.array_equal(r["anchor"], anchor)
            for r in (label, new_label)
        ):
            raise ValueError("guarded training anchor origin differs")
        mesh, loads, constrained = _case_system(entry.case)
        matrix, sums, operator, weights = independent_filter(mesh, settings.filter_radius)
        physical = np.asarray(operator @ anchor)
        stored = physical.astype(np.float32).astype(np.float64)

        def solve(
            physical, context, cid=cid, entry=entry, mesh=mesh, loads=loads, constrained=constrained
        ):
            check_budget(started)
            return journal.invoke(
                "fem",
                cid,
                {**context, "physical_sha256": sha(np.asarray(physical, dtype="<f8").tobytes())},
                lambda: energy(entry.case, physical, mesh, loads, constrained),
                lambda solved: {"compliance": solved[0], "sensitivity": solved[1].tolist()},
            )

        cs, cc = solve(stored, {"state": "stored"}), solve(physical, {"state": "continuous"})
        signed = np.asarray(matrix.T @ (cc[1] / sums)) / normalizer
        intercept = cc[0] / normalizer
        old_flags.extend(
            [
                np.array_equal(stored, record.stored.physical_density),
                np.array_equal(label["stored_physical"], stored),
                np.allclose(label["continuous_physical"], physical, rtol=0, atol=2e-11),
                np.isclose(cs[0], normalizer, rtol=1e-9, atol=0),
                np.isclose(cs[0], label["stored_compliance"], rtol=1e-9, atol=0),
                np.isclose(cc[0], label["continuous_compliance"], rtol=1e-9, atol=0),
                np.isclose(intercept, label["intercept"], rtol=1e-9, atol=1e-10),
                np.allclose(signed, label["design_gradient"], rtol=1e-9, atol=1e-10),
                (not bool(np.isclose(cc[0], normalizer, rtol=1e-9, atol=0)))
                == label["old_equality_rejects_new_anchor"],
            ]
        )
        new_flags.extend(
            [
                np.array_equal(new_label["stored_physical"], stored),
                np.allclose(new_label["continuous_physical"], physical, rtol=0, atol=2e-11),
                np.isclose(new_label["stored_compliance"], cs[0], rtol=1e-9, atol=0),
                np.isclose(new_label["continuous_compliance"], cc[0], rtol=1e-9, atol=0),
                np.allclose(new_label["design_gradient"], signed, rtol=1e-9, atol=1e-10),
            ]
        )
        setup = legacy["setup"][ci]
        arrays = (anchor, signed, sums, matrix.data, matrix.indices, matrix.indptr)
        if (
            setup["case_id"] != cid
            or setup["retained_array_bytes"] != sum(a.nbytes for a in arrays)
            or any(
                not math.isfinite(setup[k]) or setup[k] <= 0
                for k in ("wall_seconds", "cpu_seconds")
            )
        ):
            raise ValueError("legacy preparation/timer identity differs")
        i = np.arange(1, anchor.size + 1)

        def sample(
            raw,
            context,
            cid=cid,
            settings=settings,
            operator=operator,
            weights=weights,
            solve=solve,
            signed=signed,
            normalizer=normalizer,
            intercept=intercept,
            anchor=anchor,
            matrix=matrix,
            sums=sums,
        ):
            check_budget(started)
            design, rho, free, info = journal.invoke(
                "projection",
                cid,
                {**context, "raw_sha256": sha(np.asarray(raw, dtype="<f8").tobytes())},
                lambda: root(
                    raw, operator, weights, settings.volume_fraction, settings.minimum_density
                ),
                lambda projected: {"projection": projected[-1]},
            )
            exact = solve(rho, context)
            gradient = cotangent(signed, weights, free)
            exact_gradient = cotangent(
                np.asarray(matrix.T @ (exact[1] / sums)) / normalizer, weights, free
            )
            value = intercept + float(signed @ (design - anchor))
            produced_row = next(point_rows)
            if produced_row["case_id"] != cid or any(
                produced_row["context"].get(k) != val for k, val in context.items()
            ):
                raise ValueError("point identity/order differs")
            conditions = journal.invoke(
                "pointwise",
                cid,
                context,
                lambda: new_point(
                    produced_row,
                    raw,
                    weights,
                    design,
                    rho,
                    free,
                    info,
                    signed,
                    {"surrogate": value, "volume": settings.volume_fraction},
                    normalizer,
                ),
                lambda checked: [bool(v) for v in checked],
            )
            new_flags.extend(conditions)
            return (
                design,
                rho,
                free,
                info,
                gradient,
                exact[0] / normalizer,
                exact_gradient,
                value,
                produced_row,
            )

        for number in range(9):
            row = legacy["rows"][ci * 9 + number]
            if number == 8:
                raw, region = np.full(anchor.size, settings.volume_fraction), "uniform"
                spec = ["uniform", 0.0, "none", 0]
            else:
                amplitude = 0.001 if number < 4 else 0.05
                name = "sine" if number % 4 < 2 else "cosine"
                sign = 1 if number % 2 == 0 else -1
                region = "local" if number < 4 else "outside"
                values = np.sin(0.37 * i) if name == "sine" else np.cos(0.13 * i)
                values /= max(abs(values))
                raw = np.clip(anchor + sign * amplitude * values, 0.0005, 0.9995)
                spec = [region, amplitude, name, sign]
            if (
                not np.array_equal(row["raw"], raw)
                or row["spec"] != spec
                or row["scale"] != ("small" if raw.size == 216 else "large")
            ):
                raise ValueError("full original fixture construction differs")
            design, rho, free, info, gradient, exact, exact_gradient, value, fresh = sample(
                raw, {"state": number, "sign": 0}
            )
            old_flags.extend(projection_checks(row["projection"], info))
            old_flags.extend(physics_checks(row["physics"], design, rho, free, info))
            old_flags.extend(
                [
                    np.allclose(row["design"], design, rtol=0, atol=2e-11),
                    np.allclose(row["physical"], rho, rtol=0, atol=2e-11),
                    np.array_equal(row["free"], free),
                    np.isclose(row["surrogate"], value, rtol=1e-9, atol=1e-10),
                    np.isclose(row["exact"], exact, rtol=1e-9, atol=0),
                    np.allclose(row["gradient"], gradient, rtol=1e-9, atol=1e-10),
                    np.allclose(row["exact_gradient"], exact_gradient, rtol=1e-9, atol=1e-10),
                    row["volume_error"] <= 1e-12,
                    abs(row["gradient_shift_sum"]) <= 1e-10,
                    row["repeat_values"] == [row["surrogate"]] * 3,
                    row["repeat_gradient_max_difference"] == 0,
                ]
            )
            arithmetic_count += arithmetic(
                {
                    "maximum_design_distance": float(
                        np.max(abs(np.asarray(row["design"]) - anchor))
                    ),
                    "maximum_physical_distance": float(
                        np.max(abs(np.asarray(row["physical"]) - stored))
                    ),
                },
                {k: row[k] for k in ("maximum_design_distance", "maximum_physical_distance")},
            )
            if [t["repeat"] for t in row["timings"]] != [0, 1, 2] or any(
                not math.isfinite(t[k]) or t[k] <= 0
                for t in row["timings"]
                for k in ("wall_seconds", "cpu_seconds")
            ):
                raise ValueError("all216 first-inclusive timings required")
            metrics = fidelity(
                row["surrogate"],
                row["exact"],
                np.asarray(row["gradient"]),
                np.asarray(row["exact_gradient"]),
            )
            arithmetic_count += arithmetic(metrics, row["fidelity"])
            if row["local_pass"] != (
                (
                    metrics["normalized_value_error"] <= 1e-4
                    and metrics["increment_relative_error"] <= 0.25
                    and metrics["gradient_relative_error"] <= 0.25
                    and metrics["increment_sign_agrees"]
                )
                if region == "local"
                else None
            ):
                raise ValueError("saved LOCAL decision differs")
            current = fidelity(
                fresh["witness"]["value"],
                exact,
                np.asarray(fresh["witness"]["gradient"]),
                exact_gradient,
            )
            diagnostics.append(
                {
                    "case_id": cid,
                    "state": number,
                    "region": region,
                    "metrics": current,
                    "surrogate_value": fresh["witness"]["value"],
                    "exact_value": exact,
                    "negative_surrogate": fresh["witness"]["value"] < 0,
                    "maximum_design_distance": float(np.max(abs(design - anchor))),
                    "maximum_physical_distance": float(np.max(abs(rho - stored))),
                }
            )
            if region == "local":
                local.append(
                    {
                        "case_id": cid,
                        "state": number,
                        "metrics": current,
                        "passed": current["normalized_value_error"] <= 1e-4
                        and current["increment_relative_error"] <= 0.25
                        and current["gradient_relative_error"] <= 0.25
                        and current["increment_sign_agrees"],
                    }
                )
            expected = (
                [(name, h) for name in ("sine", "cosine") for h in (1e-4, 2e-4)]
                if number in (0, 4)
                else []
            )
            if [(item["direction"], item["step"]) for item in row["differences"]] != expected:
                raise ValueError("all64 original intervals required")
            for item in row["differences"]:
                name, h = item["direction"], item["step"]
                d = np.sin(0.37 * i) if name == "sine" else np.cos(0.13 * i)
                d /= max(abs(d))
                for sign, side in zip((1, -1), item["sides"], strict=True):
                    xd, xr, xf, side_info, sg, sexact, _, sv, _ = sample(
                        raw + sign * h * d,
                        {"state": number, "direction": name, "step": h, "sign": sign},
                    )
                    old_flags.extend(projection_checks(side["projection"], side_info))
                    old_flags.extend(physics_checks(side["physics"], xd, xr, xf, side_info))
                    old_flags.extend(
                        [
                            np.isclose(side["surrogate"], sv, rtol=1e-9, atol=1e-10)
                            and np.allclose(side["gradient"], sg, rtol=1e-9, atol=1e-10),
                            np.isclose(side["exact"], sexact, rtol=1e-9, atol=0),
                            np.array_equal(side["free"], xf),
                        ]
                    )
                plus, minus = item["sides"]
                fd = (plus["surrogate"] - minus["surrogate"]) / (2 * h)
                derivative = float(np.asarray(row["gradient"]) @ d)
                error = abs(fd - derivative) / max(abs(fd), abs(derivative), 1e-8)
                stable = all(np.array_equal(side["free"], row["free"]) for side in item["sides"])
                reconstructed = {
                    "surrogate_fd": fd,
                    "surrogate_derivative": derivative,
                    "surrogate_error": error,
                    "same_active_set": stable,
                    "exact_fd": (plus["exact"] - minus["exact"]) / (2 * h),
                    "exact_derivative": float(np.asarray(row["exact_gradient"]) @ d),
                }
                arithmetic_count += arithmetic(
                    reconstructed, {key: item[key] for key in reconstructed}
                )
                old_flags.extend([stable, error <= 1e-4])
                proposed = next(interval_rows)
                if (
                    proposed["case_id"],
                    proposed["state"],
                    proposed["direction"],
                    proposed["step"],
                ) != (cid, number, name, h):
                    raise ValueError("interval identity/order differs")
                # These literal candidate coefficients already passed fresh independent
                # FEM/adjoint provenance at the frozen tolerance above. The exact proof
                # verifies their binary-number map, rather than changing the objective.
                result = journal.invoke(
                    "interval",
                    cid,
                    {"state": number, "direction": name, "step": h},
                    partial(
                        prove_interval,
                        raw,
                        d,
                        weights,
                        new_label["design_gradient"],
                        settings.volume_fraction,
                        settings.minimum_density,
                        h,
                        proposed["proof"],
                        item,
                    ),
                    lambda result: result,
                )
                interval_results.append(
                    {"case_id": cid, "state": number, "direction": name, "step": h, **result}
                )
                new_flags.extend(result["predicates"])
        journal.emit("case_complete", case_id=cid)
    if (
        next(point_rows, None) is not None
        or next(interval_rows, None) is not None
        or len(old_flags) != 3976
        or arithmetic_count != 960
        or len(local) != 32
        or len(interval_results) != 64
        or len(diagnostics) != 72
        or len(new_flags) != 3232
        or journal.counts
        != {
            kind: {"attempted": n, "completed": n}
            for kind, n in {
                "label": 8,
                "fem": 216,
                "projection": 200,
                "pointwise": 200,
                "interval": 64,
            }.items()
        }
    ):
        raise ValueError("full independent population/count differs")
    old_flags = [bool(v) for v in old_flags]
    if (
        old_flags != prior["condition_results"]
        or produced["legacy_condition_results"] != old_flags
        or produced["legacy_failed_positions"] != prior["failed_condition_indices"]
    ):
        raise ValueError("all old predicates and69 failure positions must remain identical")
    integrity = all(new_flags)
    units = {
        scale: max(
            t["wall_seconds"]
            for row in legacy["rows"]
            if row["scale"] == scale
            for t in row["timings"]
        )
        for scale in ("small", "large")
    }
    scales = {row["case_id"]: row["scale"] for row in legacy["rows"]}
    setup = {
        scale: max(
            row["wall_seconds"] for row in legacy["setup"] if scales[row["case_id"]] == scale
        )
        for scale in ("small", "large")
    }
    fixed = (
        3870.204341
        + 851.38
        + 200.98
        + 80.34
        + 3 * 1.25 * (432 * setup["small"] + 76 * setup["large"])
        + 3 * 200 * 1.25 * (432 * units["small"] + 76 * units["large"])
    )
    return {
        "passed": True,
        "metadata_only": False,
        "integrity_passed": bool(integrity),
        "pointwise_states": 200,
        "intervals": interval_results,
        "new_predicates": [bool(v) for v in new_flags],
        "legacy_condition_results": old_flags,
        "legacy_failed_positions": prior["failed_condition_indices"],
        "legacy_numerical_conditions": 3976,
        "legacy_arithmetic_conditions": 960,
        "local_states": local,
        "central_diagnostics": diagnostics,
        "local_fidelity_passed": bool(integrity and all(row["passed"] for row in local)),
        "inherited_prediction_maxima": units,
        "inherited_preparation_maxima": setup,
        "fixed_cost_without_new_charges": fixed,
        "cost_feasible": False,
        "full_training_memory": "PENDING",
        "producer_sha256": sha(canonical(produced)),
        "fits": 0,
        "final_access": False,
        "old_fresh_sealed": True,
    }


def main(argv=None):
    started = perf_counter()
    args, old, data, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    revision = release(output)
    # The original guarded label reader imports Torch. Freeze both pools before
    # any reader or numerical call, including the metadata-only abort path.
    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    threads = {"intra_op": torch.get_num_threads(), "inter_op": torch.get_num_interop_threads()}
    if threads != {"intra_op": 1, "inter_op": 1}:
        raise ValueError("frozen Torch one-thread runtime required")
    if (output / "independent.json").exists() or (output / "independent.events.jsonl").exists():
        raise ValueError("refuses second independent attempt")
    journal = Journal(output / "independent.events.jsonl", revision)
    journal.emit("runtime_threads", torch=threads)
    try:
        command = read(output / "audit_receipts/producer_command.json")
        path = output / "producer.events.jsonl"
        events, counts, pending = (
            event_prefix(path, revision, allow_incomplete=command["exit_code"] != 0)
            if path.exists()
            else ([], {k: {"attempted": 0, "completed": 0} for k in journal.counts}, [])
        )
        if command["exit_code"] != 0 or not (output / "producer.json").exists():
            if command["exit_code"] == 0:
                raise ValueError("missing result after success")
            result = {
                "passed": True,
                "metadata_only": True,
                "integrity_passed": False,
                "producer_counts": counts,
                "producer_pending": [item[0] for item in pending],
                "producer_event_count": len(events),
                "producer_journal_sha256": digest(path) if path.exists() else None,
                "local_fidelity_passed": False,
                "cost_feasible": False,
                "full_training_memory": "PENDING",
                "fits": 0,
                "final_access": False,
                "old_fresh_sealed": True,
            }
        else:
            expected = {"label": 8, "fem": 16, "projection": 400, "pointwise": 200, "interval": 64}
            produced = read(output / "producer.json")
            if (
                pending
                or events[-1]["event"] != "complete"
                or counts != {k: {"attempted": n, "completed": n} for k, n in expected.items()}
                or produced["counts"] != counts
                or produced["journal_sha256"] != digest(output / "producer.events.jsonl")
            ):
                raise ValueError("complete durable producer calls required")
            if (
                [e["result"] for e in events if e["event"] == "point"] != produced["points"]
                or [e["result"] for e in events if e["event"] == "interval_result"]
                != produced["intervals"]
                or [e["result"] for e in events if e["event"] == "anchor"] != produced["labels"]
            ):
                raise ValueError("durable original numerical prefix differs from final panel")
            legacy, prior = legacy_inputs(old)
            result = audit(produced, legacy, prior, data, label_index(data), journal, started)
        result["torch_threads"] = threads
        finish(output, "independent", result, journal, started)
    except Exception as error:
        failed(journal, error)
        raise
    finally:
        journal.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
