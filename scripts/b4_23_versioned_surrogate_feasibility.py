"""Fixed train-only v3 fidelity/cost panel with exclusive durable calls."""

import argparse
import json
import traceback
from pathlib import Path
from time import perf_counter, process_time

import numpy as np
import torch
from b4_14_generalist_method_review import (
    canonical,
    execution_release,
    peak_rss,
    read,
    roots,
    safe_hash,
    sha,
)
from b4_15_offline_compliance_adjoint import (
    INDEX_SHA,
    direction_vector,
    selected_entries,
    train_label,
)
from b4_19_local_compliance_surrogate import fidelity, fixture, local_pass, state_specs
from b4_20_surrogate_correctness import Journal as PriorJournal
from b4_20_surrogate_correctness import label_metadata, solve
from b4_22_stable_projection_correctness import PASS_NEXT
from b4_22_stable_projection_correctness import check_inputs as check_prior
from b4_22_stable_projection_correctness import plan_payload as prior_plan

from topolab.baselines import _case_system
from topolab.local_compliance import torch_local_loss
from topolab.offline_compliance import pullback
from topolab.simp import apply_density_filter, build_density_filter, evaluate_compliance
from topolab.stable_projection import VERSION as KERNEL_VERSION
from topolab.stable_projection import StableStoredNormalizerTangent, project_stable

VERSION = "topolab.b4_23.versioned-surrogate-feasibility.v1"
BINDINGS = {
    "audit_receipts/plan.json": "93ed2c7d54178e5027886b1c5b054da7f0fa45b73092b491486a67cb88918d24",
    "audit_receipts/production_release.json": (
        "b513159b5fd55916e74e4fe8d7d2b543332a00215f545564e84ddd6bc4e957c0"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "e331fb8050d111fef9c811fc313345faee13d90d16c223e05abb73e44b8bd21b"
    ),
    "audit_receipts/source_main_ci.json": (
        "a74231f07f3c684b24043a34b88aef1d7760bc6943cfacadd8f38caaec78a9cf"
    ),
    "probe.json": "59ff187b8cf5d213faa096422d13a3d30494b62b5bbc3204e5109a7f4116b53f",
    "probe.events.jsonl": "56738b53a9e79e857ff91ba9da34d67fce34425dbdb531964fa1bcfad1f20de1",
    "independent_audit.json": "ce65e6afd6eca33caf41c9f1c48189148b7db25ccb708782d95416118b867f58",
    "independent.events.jsonl": "bf04397318847359d39b766fb5f0125749b8050fef07e1164ceb0d4115cb1888",
    "resource_close.json": "d59dc118980f466bc0fe8d4d9a7f8f75b80847e7a4dd0cb38b8622e6f71cba64",
    "audit_receipts/execution_commands.json": (
        "16aceb13fb71969836ca1a996af163212b52d721023f48a765c2b3f68c350d06"
    ),
    "audit_receipts/closure_profile_verification.json": (
        "92907c07e8040110c49f1ee3e0b85bafdf512fdff90f896ff2772d22144305c1"
    ),
    "audit_receipts/postexit_controller_reservation.json": (
        "dcd52dec4b38d1e60c7bf701eb509480993b354d3f0d1e2db7728bd9629acfa3"
    ),
    "audit_receipts/evidence_release.json": (
        "186e35af2c5a9ece8dacde7bd44c98a4ea08d369652f51741770145d7d5abe50"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "b8c8ea978119fe00d154af2075b15224cb4b92a7657c0519bed93abcb88b7e96"
    ),
    "audit_receipts/evidence_main_ci.json": (
        "9cea9916b4d7e8740e8950781e650f8763cf559cefd94f3ac8adb4d97753a70d"
    ),
}
CORRECTNESS_NEXT = "B4.24 bounded versioned surrogate correctness failure review"
FIDELITY_NEXT = "B4.24 bounded local-surrogate fidelity and objective-method review"
COST_NEXT = "B4.24 bounded local-surrogate cost review"
FIT_NEXT = "B4.24 bounded training-objective integration preregistration"


def plan_payload():
    payload = {
        "version": VERSION,
        "kernel_version": KERNEL_VERSION,
        "bindings": BINDINGS,
        "prior_plan_sha256": prior_plan()["plan_sha256"],
        "b3_index_sha256": INDEX_SHA,
        "entries": [e.model_dump(mode="json") for e in selected_entries()],
        "states": state_specs(),
        "directions": ["sine", "cosine"],
        "steps": [1e-4, 2e-4],
        "repeats": 3,
        "cases": 8,
        "central_states": 72,
        "local_states": 32,
        "timings": 216,
        "directional_rows": 64,
        "probe_solves": 216,
        "audit_solves": 216,
        "probe_projections": 616,
        "audit_projections": 200,
        "numerical_conditions": 3976,
        "probe_events": 2050,
        "audit_events": 1146,
        "raw_margin": 5e-4,
        "local_value_tolerance": 1e-4,
        "increment_floor": 1e-5,
        "increment_error_tolerance": 0.25,
        "gradient_floor": 1e-8,
        "gradient_error_tolerance": 0.25,
        "fd_tolerance": 1e-4,
        "volume_tolerance": 1e-12,
        "kink_tolerance": 1e-10,
        "process_seconds": 600,
        "max_seconds": 1260,
        "closure_seconds": 60,
        "max_rss_bytes": 1073741824,
        "fit_population": [432, 76],
        "fit_seeds": 3,
        "fit_epochs": 200,
        "cost_factor": 1.25,
        "baseline_fit_seconds": 3870.204341,
        "prior_charged_seconds": [84.33, 55.99, 112.34, 86.13, 73.93, 100.30, 90.27, 104.62],
        "future_fit_seconds": 7200,
        "full_fit_memory_feasibility_pending": True,
        "fits": 0,
        "new_labels": 0,
        "screen_queries": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
    }
    payload = json.loads(canonical(payload))
    return {**payload, "plan_sha256": sha(canonical(payload))}


def check_inputs(root, data):
    for path, digest in BINDINGS.items():
        safe_hash(root, path, digest)
    closed, audit, evidence = [
        read(root, p)
        for p in (
            "resource_close.json",
            "independent_audit.json",
            "audit_receipts/evidence_release.json",
        )
    ]
    if (
        read(root, "audit_receipts/plan.json") != prior_plan()
        or not closed["closed"]
        or not closed["full_panel_complete"]
        or not closed["correctness_acceptance_passed"]
        or closed["charged_seconds"] != 104.62
        or closed["next_slice"] != PASS_NEXT
        or closed["local_fidelity_evaluated"]
        or closed["fit_proxy"] is not None
        or not audit["passed"]
        or not audit["correctness_passed"]
        or audit["numerical_conditions"] != 1704
        or audit["failed_numerical_conditions"] != 0
        or not evidence["all_applicable_ci_passed_before_merge"]
        or not evidence["merged_tree_equals_tested_tree"]
        or evidence["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
        or evidence["main_ci_sha256"] != BINDINGS["audit_receipts/evidence_main_ci.json"]
        or any(
            v["final_access"] or v["repaired_gate"] or not v["old_fresh_sealed"]
            for v in (closed, audit, evidence)
        )
    ):
        raise ValueError("requires closed B4.22 ordered correctness pass and unchanged seals")
    for p in ("closure_profile_verification", "postexit_controller_reservation"):
        proof = read(root, "audit_receipts/" + p + ".json")
        if not proof["passed"] or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]:
            raise ValueError("prior native resource verification differs")
    return check_prior(root.parent / "b4-21-correctness-failure-review", data)


def check_budget(started):
    if perf_counter() - started + 10 > 600 or peak_rss() > 1073741824:
        raise RuntimeError("frozen fidelity/cost process cap exceeded")


class Journal(PriorJournal):
    def __init__(self, path, revision):
        self.stream = path.open("xb")
        self.sequence = 0
        self.revision = revision
        self.plan_sha256 = plan_payload()["plan_sha256"]
        self.counts = {k: {"attempted": 0, "completed": 0} for k in ("label", "fem", "projection")}
        self.emit("start")


def root_metadata(state, raw, settings):
    shifted = raw + state.offset
    return {
        "offset": state.offset,
        "weighted_volume_residual": float(state.weights @ state.design) - settings.volume_fraction,
        "physical_volume_residual": float(state.physical.mean()) - settings.volume_fraction,
        "kink_margin": float(
            np.min(np.minimum(abs(shifted - settings.minimum_density), abs(shifted - 1)))
        ),
    }


def root_payload(state, raw, settings):
    return {
        "design": state.design.tolist(),
        "physical": state.physical.tolist(),
        "free": state.free.tolist(),
        "projection": root_metadata(state, raw, settings),
    }


def evaluate(kernel, raw, journal, cid, context):
    return journal.invoke(
        "projection",
        cid,
        {**context, "raw_sha256": sha(np.asarray(raw, dtype="<f8").tobytes())},
        lambda: kernel.evaluate(raw),
        lambda r: {
            "value": r.value,
            "gradient": r.gradient.tolist(),
            **root_payload(r.projection, raw, kernel.case.problem.optimization),
        },
    )


def torch_step(kernel, raw, repeat):
    wall, cpu = perf_counter(), process_time()
    tensor = torch.tensor(raw, dtype=torch.float64, requires_grad=True)
    loss = torch_local_loss(tensor, kernel)
    loss.backward()
    value, gradient = loss.item(), tensor.grad.detach().numpy().copy().tolist()
    return {
        "value": value,
        "gradient": gradient,
        "timing": {
            "repeat": repeat,
            "wall_seconds": perf_counter() - wall,
            "cpu_seconds": process_time() - cpu,
        },
    }


def exact_state(entry, kernel, raw, journal, context):
    settings = entry.case.problem.optimization
    cid = entry.case.case_id
    state = journal.invoke(
        "projection",
        cid,
        {
            **context,
            "kind": "exact_root",
            "raw_sha256": sha(np.asarray(raw, dtype="<f8").tobytes()),
        },
        lambda: project_stable(
            kernel.filt, raw, settings.volume_fraction, settings.minimum_density
        ),
        lambda r: root_payload(r, raw, settings),
    )
    mesh, loads, constrained = _case_system(entry.case)
    p = entry.case.problem
    analysis = journal.invoke(
        "fem",
        cid,
        {
            **context,
            "kind": "exact_fem",
            "normalizer": kernel.normalizer,
            "physical": state.physical.tolist(),
            "physical_sha256": sha(np.asarray(state.physical, dtype="<f8").tobytes()),
        },
        lambda: evaluate_compliance(
            mesh,
            state.physical,
            loads,
            constrained,
            solid_modulus=p.material.solid_modulus,
            minimum_modulus=p.material.minimum_modulus,
            poisson_ratio=p.material.poisson_ratio,
            penalty=p.optimization.penalty,
        ),
        lambda r: {"compliance": r.compliance, "sensitivity": r.sensitivity.tolist()},
    )
    operator = kernel.filt.matrix.multiply((1 / kernel.filt.row_sums)[:, None]).tocsr()
    gradient = pullback(state, np.asarray(operator.T @ analysis.sensitivity) / kernel.normalizer)
    return {
        "value": analysis.compliance / kernel.normalizer,
        "gradient": gradient,
        "physics": root_payload(state, raw, settings),
    }


def probe(data, index, journal, started):
    torch.set_num_threads(1)
    labels, setup, rows = [], [], []
    for entry in selected_entries():
        check_budget(started)
        cid = entry.case.case_id
        journal.emit("case_start", case_id=cid)
        wall, cpu = perf_counter(), process_time()
        item = journal.invoke(
            "label",
            cid,
            {"role": "train", "training_set": "expanded"},
            lambda entry=entry: train_label(data, index, entry),
            label_metadata,
        )
        record, _ = item
        label = label_metadata(item)
        anchor = np.asarray(record.stored.design_density)
        mesh, _, _ = _case_system(entry.case)
        filt = build_density_filter(mesh, entry.case.problem.optimization.filter_radius)
        continuous = apply_density_filter(filt, anchor)
        stored = continuous.astype(np.float32).astype(np.float64)
        if not np.array_equal(stored, record.stored.physical_density):
            raise ValueError("serialized physical representation differs")
        cs = solve(entry, stored, label["normalizer"], "stored", journal)
        cc = solve(entry, continuous, label["normalizer"], "continuous", journal)
        if not np.isclose(cs.compliance, label["normalizer"], rtol=1e-9, atol=0):
            raise ValueError("stored-state compliance differs from audited label")
        kernel = StableStoredNormalizerTangent(entry.case, anchor, label["normalizer"], cc)
        preparation = {
            "case_id": cid,
            "wall_seconds": perf_counter() - wall,
            "cpu_seconds": process_time() - cpu,
            "retained_array_bytes": sum(a.nbytes for a in kernel.retained_arrays()),
        }
        label.update(
            case_id=cid,
            continuous_physical=continuous.tolist(),
            stored_compliance=cs.compliance,
            continuous_compliance=cc.compliance,
            intercept=cc.compliance / label["normalizer"],
            old_equality_rejects_new_anchor=not bool(
                np.isclose(cc.compliance, label["normalizer"], rtol=1e-9, atol=0)
            ),
            design_gradient=kernel.design_gradient.tolist(),
        )
        labels.append(label)
        setup.append(preparation)
        journal.emit("anchor", case_id=cid, result={"label": label, "setup": preparation})
        for number, spec in enumerate(state_specs()):
            check_budget(started)
            journal.emit("state_start", case_id=cid, state=number)
            raw = fixture(anchor, entry.case.problem.optimization.volume_fraction, spec)
            result = evaluate(kernel, raw, journal, cid, {"state": number, "kind": "direct"})
            repeats = [
                journal.invoke(
                    "projection",
                    cid,
                    {
                        "state": number,
                        "kind": "torch",
                        "repeat": j,
                        "raw_sha256": sha(np.asarray(raw, dtype="<f8").tobytes()),
                    },
                    lambda j=j, kernel=kernel, raw=raw: torch_step(kernel, raw, j),
                    lambda r: r,
                )
                for j in range(3)
            ]
            exact = exact_state(entry, kernel, raw, journal, {"state": number})
            metrics = fidelity(result.value, exact["value"], result.gradient, exact["gradient"])
            row = {
                "case_id": cid,
                "state": number,
                "spec": list(spec),
                "scale": "small" if raw.size == 216 else "large",
                "raw": raw.tolist(),
                **root_payload(result.projection, raw, entry.case.problem.optimization),
                "surrogate": result.value,
                "gradient": result.gradient.tolist(),
                "exact": exact["value"],
                "exact_gradient": exact["gradient"].tolist(),
                "physics": exact["physics"],
                "timings": [r["timing"] for r in repeats],
                "repeat_values": [r["value"] for r in repeats],
                "repeat_gradient_max_difference": max(
                    float(np.max(abs(np.asarray(r["gradient"]) - result.gradient))) for r in repeats
                ),
                "fidelity": metrics,
                "local_pass": local_pass(metrics) if spec[0] == "local" else None,
                "maximum_design_distance": float(np.max(abs(result.projection.design - anchor))),
                "maximum_physical_distance": float(
                    np.max(abs(result.projection.physical - stored))
                ),
                "volume_error": abs(
                    float(result.projection.physical.mean())
                    - entry.case.problem.optimization.volume_fraction
                ),
                "gradient_shift_sum": float(result.gradient.sum()),
                "differences": [],
            }
            journal.emit("central", case_id=cid, result=row)
            if number in (0, 4):
                for name in ("sine", "cosine"):
                    d = direction_vector(raw.size, name)
                    for h in (1e-4, 2e-4):
                        check_budget(started)
                        journal.emit(
                            "direction_start", case_id=cid, state=number, direction=name, step=h
                        )
                        sides = []
                        for sign in (1, -1):
                            x = raw + sign * h * d
                            context = {"state": number, "direction": name, "step": h, "sign": sign}
                            side = evaluate(kernel, x, journal, cid, {**context, "kind": "side"})
                            side_exact = exact_state(entry, kernel, x, journal, context)
                            sides.append(
                                {
                                    "surrogate": side.value,
                                    "gradient": side.gradient.tolist(),
                                    "free": side.projection.free.tolist(),
                                    "projection": root_metadata(
                                        side.projection, x, entry.case.problem.optimization
                                    ),
                                    "exact": side_exact["value"],
                                    "physics": side_exact["physics"],
                                }
                            )
                        fd = (sides[0]["surrogate"] - sides[1]["surrogate"]) / (2 * h)
                        derivative = float(result.gradient @ d)
                        diff = {
                            "direction": name,
                            "step": h,
                            "sides": sides,
                            "surrogate_fd": fd,
                            "surrogate_derivative": derivative,
                            "surrogate_error": abs(fd - derivative)
                            / max(abs(fd), abs(derivative), 1e-8),
                            "same_active_set": all(
                                np.array_equal(s["free"], row["free"]) for s in sides
                            ),
                            "exact_fd": (sides[0]["exact"] - sides[1]["exact"]) / (2 * h),
                            "exact_derivative": float(exact["gradient"] @ d),
                        }
                        row["differences"].append(diff)
                        journal.emit("direction", case_id=cid, state=number, result=diff)
            rows.append(row)
            journal.emit("state", case_id=cid, result=row)
        journal.emit("case_complete", case_id=cid)
    check_budget(started)
    return {
        "plan": plan_payload(),
        "labels": labels,
        "setup": setup,
        "rows": rows,
        "counts": journal.counts,
        "fits": 0,
        "new_labels": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
    }


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("review", "data", "output"):
        parser.add_argument("--" + name + "-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    root, data, output = [p.resolve() for p in (args.review_root, args.data_root, args.output_root)]
    roots(root, output)
    roots(data, output)
    if args.execute and (
        (root.name, data.name, output.name)
        != (
            "b4-22-stable-projection-correctness",
            "b3-v1-data",
            "b4-23-versioned-surrogate-feasibility",
        )
        or not root.parent == data.parent == output.parent
    ):
        raise ValueError("requires frozen sibling external roots")
    return args, root, data, output


def main(argv=None):
    started = perf_counter()
    args, root, data, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    if (output / "probe.json").exists():
        raise ValueError("refuses to overwrite probe")
    revision = execution_release(output)
    journal = Journal(output / "probe.events.jsonl", revision)
    try:
        index = check_inputs(root, data)
        result = probe(data, index, journal, started)
        check_inputs(root, data)
        check_budget(started)
        result.update(
            source_revision=revision,
            charged_seconds=perf_counter() - started + 10,
            peak_rss_bytes=peak_rss(),
        )
        journal.emit("complete")
        result["journal_sha256"] = sha((output / "probe.events.jsonl").read_bytes())
        with (output / "probe.json").open("xb") as stream:
            stream.write(canonical(result))
        print(canonical({"counts": result["counts"]}).decode(), end="")
    except Exception as error:
        journal.emit(
            "abort",
            error_type=type(error).__name__,
            error=str(error),
            traceback=traceback.format_exc(),
        )
        raise
    finally:
        journal.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
