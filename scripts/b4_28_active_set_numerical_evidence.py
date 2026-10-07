"""One fixed v3 panel, full pointwise witnesses and exact interval certificates."""

import math
from dataclasses import asdict
from time import perf_counter

import numpy as np
import torch
from b4_28_common import (
    Journal,
    arguments,
    check_budget,
    digest,
    entries,
    failed,
    finish,
    label_index,
    legacy_inputs,
    plan_payload,
    release,
    sha,
    train_label,
)

from topolab.active_set_evidence import (
    PointWitness,
    certify_interval,
    certify_pointwise,
    check_interval,
    check_pointwise,
)
from topolab.active_set_trace import trace_interval
from topolab.baselines import _case_system
from topolab.local_compliance import torch_local_loss
from topolab.simp import apply_density_filter, build_density_filter, evaluate_compliance
from topolab.stable_projection import StableStoredNormalizerTangent


def direction(n, name):
    i = np.arange(1, n + 1)
    values = np.sin(0.37 * i) if name == "sine" else np.cos(0.13 * i)
    return values / np.max(abs(values))


def states(anchor, volume):
    for amplitude in (0.001, 0.05):
        for name in ("sine", "cosine"):
            for sign in (1, -1):
                yield np.clip(
                    anchor + sign * amplitude * direction(anchor.size, name), 0.0005, 0.9995
                )
    yield np.full(anchor.size, volume)


def root_payload(result, raw, settings):
    state = result.projection
    shifted = raw + state.offset
    return {
        "design": state.design.tolist(),
        "physical": state.physical.tolist(),
        "gradient": result.gradient.tolist(),
        "weights": state.weights.tolist(),
        "free": state.free.tolist(),
        "offset": state.offset,
        "kink_margin": float(
            np.min(np.minimum(abs(shifted - settings.minimum_density), abs(shifted - 1)))
        ),
        "weighted_residual": float(state.weights @ state.design) - settings.volume_fraction,
        "physical_residual": float(state.physical.mean()) - settings.volume_fraction,
        "value": result.value,
        "compliance": result.compliance,
    }


def torch_state(raw, kernel):
    tensor = torch.tensor(raw, dtype=torch.float64, requires_grad=True)
    value = torch_local_loss(tensor, kernel)
    value.backward()
    return {"value": value.item(), "gradient": tensor.grad.detach().numpy().copy().tolist()}


def solve(entry, physical, journal, kind):
    mesh, loads, constrained = _case_system(entry.case)
    p = entry.case.problem
    return journal.invoke(
        "fem",
        entry.case.case_id,
        {"state": kind, "physical_sha256": sha(np.asarray(physical, dtype="<f8").tobytes())},
        lambda: evaluate_compliance(
            mesh,
            physical,
            loads,
            constrained,
            solid_modulus=p.material.solid_modulus,
            minimum_modulus=p.material.minimum_modulus,
            poisson_ratio=p.material.poisson_ratio,
            penalty=p.optimization.penalty,
        ),
        lambda result: {
            "compliance": result.compliance,
            "sensitivity": result.sensitivity.tolist(),
        },
    )


def observe(kernel, raw, context, journal, started):
    check_budget(started)
    cid = kernel.case.case_id
    context = {**context, "raw_sha256": sha(np.asarray(raw, dtype="<f8").tobytes())}
    settings = kernel.case.problem.optimization
    direct = journal.invoke(
        "projection",
        cid,
        {**context, "kind": "direct"},
        lambda: kernel.evaluate(raw),
        lambda result: root_payload(result, raw, settings),
    )
    observed = root_payload(direct, raw, settings)
    bridge = journal.invoke(
        "projection",
        cid,
        {**context, "kind": "torch"},
        lambda: torch_state(raw, kernel),
        lambda result: result,
    )
    witness = PointWitness(
        *(tuple(observed[k]) for k in ("design", "physical", "gradient")),
        *(
            observed[k]
            for k in (
                "offset",
                "kink_margin",
                "weighted_residual",
                "physical_residual",
                "value",
                "compliance",
            )
        ),
        bridge["value"],
        tuple(bridge["gradient"]),
    )

    def certify():
        reference = certify_pointwise(
            raw,
            direct.projection.weights,
            kernel.design_gradient,
            settings.volume_fraction,
            settings.minimum_density,
            direct.projection.offset,
        )
        physical = apply_density_filter(kernel.filt, np.asarray(reference.design))
        value = kernel.anchor_compliance / kernel.normalizer + math.fsum(
            float(g) * (x - float(a))
            for g, x, a in zip(kernel.design_gradient, reference.design, kernel.anchor, strict=True)
        )
        conditions = check_pointwise(
            reference,
            witness,
            weights=direct.projection.weights,
            independent_physical=physical,
            independent_value=value,
            independent_compliance=value * kernel.normalizer,
            volume=settings.volume_fraction,
        )
        if not all(conditions):
            raise ValueError("new pointwise witness rejected: " + str(conditions))
        return {
            "predicates": list(conditions),
            "reference_offset": reference.offset,
            "reference_gradient": list(reference.gradient),
            "reference_kink_margin": reference.kink_margin,
        }

    proof = journal.invoke("pointwise", cid, context, certify, lambda result: result)
    row = {
        "case_id": cid,
        "context": context,
        "raw": raw.tolist(),
        "witness": asdict(witness),
        "weights": observed["weights"],
        "free": observed["free"],
        "proof": proof,
    }
    journal.emit("point", case_id=cid, result=row)
    return row


def fraction(value):
    return [value.numerator, value.denominator]


def interval_payload(reference, conditions):
    checks = asdict(conditions)
    checks["predicates"] = list(conditions.predicates)
    return {
        "step": reference.step,
        "pieces": [
            {
                "start": fraction(p.piece.start),
                "end": fraction(p.piece.end),
                "partition": list(p.piece.partition),
                "offset_start": fraction(p.offset_start),
                "offset_end": fraction(p.offset_end),
                "offset_slope": fraction(p.offset_slope),
                "value_slope": fraction(p.value_slope),
                "residuals": [fraction(v) for v in p.weighted_residuals],
            }
            for p in reference.pieces
        ],
        "transitions": [list(v) for v in reference.transitions],
        "signed_increment": fraction(reference.signed_increment),
        "secant": reference.secant,
        "checks": checks,
    }


def producer(data, legacy, index, journal, started):
    labels, points, intervals = [], [], []
    for ci, entry in enumerate(entries()):
        check_budget(started)
        cid = entry.case.case_id
        journal.emit("case_start", case_id=cid)
        record, artifact = journal.invoke(
            "label",
            cid,
            {"role": "train", "training_set": "expanded"},
            lambda entry=entry: train_label(data, index, entry),
            lambda item: {"artifact": item[1], "normalizer": item[0].stored.compliance},
        )
        anchor = np.asarray(record.stored.design_density, dtype=np.float64)
        normalizer = record.stored.compliance
        settings = entry.case.problem.optimization
        mesh, _, _ = _case_system(entry.case)
        filt = build_density_filter(mesh, settings.filter_radius)
        physical = apply_density_filter(filt, anchor)
        stored = physical.astype(np.float32).astype(np.float64)
        if not np.array_equal(stored, record.stored.physical_density):
            raise ValueError("serialized physical origin differs")
        cs = solve(entry, stored, journal, "stored")
        cc = solve(entry, physical, journal, "continuous")
        if not np.isclose(cs.compliance, normalizer, rtol=1e-9, atol=0):
            raise ValueError("stored compliance origin differs")
        kernel = StableStoredNormalizerTangent(entry.case, anchor, normalizer, cc)
        label = {
            "case_id": cid,
            "artifact": artifact,
            "anchor": anchor.tolist(),
            "normalizer": normalizer,
            "stored_physical": stored.tolist(),
            "continuous_physical": physical.tolist(),
            "stored_compliance": cs.compliance,
            "continuous_compliance": cc.compliance,
            "design_gradient": kernel.design_gradient.tolist(),
        }
        labels.append(label)
        journal.emit("anchor", case_id=cid, result=label)
        for number, raw in enumerate(states(anchor, settings.volume_fraction)):
            center = observe(kernel, raw, {"state": number, "sign": 0}, journal, started)
            points.append(center)
            old = legacy["rows"][ci * 9 + number]
            if not np.array_equal(raw, old["raw"]):
                raise ValueError("retained raw state differs")
            if number in (0, 4):
                for name in ("sine", "cosine"):
                    d = direction(raw.size, name)
                    for h in (1e-4, 2e-4):
                        check_budget(started)
                        context = {"state": number, "direction": name, "step": h}
                        for sign in (1, -1):
                            points.append(
                                observe(
                                    kernel,
                                    raw + sign * h * d,
                                    {**context, "sign": sign},
                                    journal,
                                    started,
                                )
                            )
                        retained = next(
                            item
                            for item in old["differences"]
                            if (item["direction"], item["step"]) == (name, h)
                        )

                        def certify(
                            raw=raw,
                            d=d,
                            h=h,
                            retained=retained,
                            center=center,
                            kernel=kernel,
                            settings=settings,
                        ):
                            pieces = trace_interval(
                                raw,
                                d,
                                center["weights"],
                                settings.volume_fraction,
                                settings.minimum_density,
                                h,
                            )
                            reference = certify_interval(
                                raw,
                                d,
                                center["weights"],
                                kernel.design_gradient,
                                settings.volume_fraction,
                                settings.minimum_density,
                                h,
                                pieces,
                            )
                            plus, minus = retained["sides"]
                            checks = check_interval(
                                reference,
                                d,
                                h,
                                minus["surrogate"],
                                plus["surrogate"],
                                retained["surrogate_derivative"],
                                legacy_mask_passed=retained["same_active_set"],
                                legacy_fd_passed=retained["surrogate_error"] <= 1e-4,
                            )
                            if not checks.passed:
                                raise ValueError(
                                    "retained interval rejected: " + str(checks.predicates)
                                )
                            return interval_payload(reference, checks)

                        proof = journal.invoke(
                            "interval", cid, context, certify, lambda result: result
                        )
                        item = {"case_id": cid, **context, "proof": proof}
                        intervals.append(item)
                        journal.emit("interval_result", case_id=cid, result=item)
        journal.emit("case_complete", case_id=cid)
    if len(points) != 200 or len(intervals) != 64:
        raise ValueError("full finite population required")
    return {
        "passed": True,
        "labels": labels,
        "points": points,
        "intervals": intervals,
        "prediction_timing": False,
        "legacy_gate_repaired": False,
        "fits": 0,
        "final_access": False,
        "old_fresh_sealed": True,
    }


def main(argv=None):
    started = perf_counter()
    args, old, data, output = arguments(argv)
    if not args.execute:
        from b4_28_common import canonical

        print(canonical(plan_payload()).decode(), end="")
        return 0
    if (output / "producer.json").exists() or (output / "producer.events.jsonl").exists():
        raise ValueError("refuses second producer attempt")
    revision = release(output)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    journal = Journal(output / "producer.events.jsonl", revision)
    try:
        legacy, prior = legacy_inputs(old)
        result = producer(data, legacy, label_index(data), journal, started)
        result["legacy_condition_results"] = prior["condition_results"]
        result["legacy_failed_positions"] = prior["failed_condition_indices"]
        result["legacy_probe_sha256"] = digest(old / "probe.json")
        finish(output, "producer", result, journal, started)
    except Exception as error:
        failed(journal, error)
        raise
    finally:
        journal.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
