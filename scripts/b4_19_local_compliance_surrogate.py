"""Frozen train-only signed tangent probe; default mode never reads label bytes."""

import argparse
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
from b4_15_offline_compliance_adjoint import check_inputs as check_data
from b4_18_fem_objective_method_review import SURROGATE_NEXT
from b4_18_fem_objective_method_review import check_inputs as check_prior
from b4_18_fem_objective_method_review import plan_payload as prior_plan

from topolab.local_compliance import VERSION as KERNEL_VERSION
from topolab.local_compliance import LocalCompliance, torch_local_loss
from topolab.offline_compliance import OfflineCompliance

VERSION = "topolab.b4_19.local-compliance-surrogate.v1"
BINDINGS = {
    "audit_receipts/plan.json": (
        "f45b7a00add45c49b99dabbf5d6aba06f88fce797e58fe0e290f588c992b6eca"
    ),
    "audit_receipts/production_release.json": (
        "eb09a3b1e7a03babc141718743a4714caa98927d12c9e25d79d688a85fc29bdf"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "8964ec0c46504d02311e907dff27a7bf0a38dc750381335d6f66c979dfa6da87"
    ),
    "review.json": ("7670ef8f70c230133d27fdc6966e25aa86723aa12e616b3a5ce8eb600ab0f093"),
    "independent_audit.json": ("435fdcbe5a3d5ae7b88fd8bf1f1ae92f9a4d879743ea2ef5249540aa7a2f4e7d"),
    "resource_close.json": ("5b0bc27f242981fdd147c928b0832a0968b3e196c58d47ec3db1064079ed81ca"),
    "audit_receipts/execution_commands.json": (
        "5c4b46ce97b727364396283f18c329c3b2f40df5e454891e2374dc9ddd09b918"
    ),
    "audit_receipts/plan_command.json": (
        "ddfd9387794d1fc79b4361ab09091210fb1dff1855f19a52e80fb3147fe142bb"
    ),
    "audit_receipts/closure_command.json": (
        "8d53822742ec1c0284c8fd2e0d26cb001e5c71fc42d2f465e4dc00d07ea530c2"
    ),
    "audit_receipts/closure_profile_verification.json": (
        "863baa2e59a80456aff836d629c407cd8e040982760af3db2ba9a30e2c4cebff"
    ),
    "audit_receipts/postexit_command.json": (
        "feb29c764cb5768580f8e22428d4915c9b40a54fab8b044c6051440546431f3f"
    ),
    "audit_receipts/postexit_controller_reservation.json": (
        "5c82a1a261138c4a6958646cc8cb6cae72cc466e29908757b7d11a126bb7a2b2"
    ),
    "audit_receipts/plan_sandbox_denied_original_command.json": (
        "610757ccb4450b5d54b6783763165aad49a328ee00182f1fd9cdb5e35a80c73d"
    ),
    "audit_receipts/plan_sandbox_denied.json": (
        "4fbb2352fa7e2339c96f813cc01a3b6a550569963d6f4c29917a4c792a83d9c5"
    ),
    "profiles/plan_sandbox_denied.time": (
        "cc90577949e766553c99e40e5e357edef5d70f6f6dabff0d95d03024e0862683"
    ),
    "logs/plan_sandbox_denied.log": (
        "f45b7a00add45c49b99dabbf5d6aba06f88fce797e58fe0e290f588c992b6eca"
    ),
    "audit_receipts/evidence_release.json": (
        "473f4a867d381e4710d0ad7b1b7439032b38dfa0175aa0a812452681aeff2b0f"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "13e068e5092ee4fe3ecc60c2b24286bb443451462c9609824ba20e1d12008a19"
    ),
}
CORRECTNESS_NEXT = "B4.20 bounded surrogate correctness review"
FIDELITY_NEXT = "B4.20 bounded local-surrogate fidelity and objective-method review"
COST_NEXT = "B4.20 bounded local-surrogate cost review"
FIT_NEXT = "B4.20 bounded training-objective integration preregistration"


def state_specs():
    return [
        (region, amplitude, direction, sign)
        for region, amplitude in (("local", 0.001), ("outside", 0.05))
        for direction in ("sine", "cosine")
        for sign in (1, -1)
    ] + [("uniform", 0.0, "none", 0)]


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
        "timings": 216,
        "directional_rows": 64,
        "probe_solves": 208,
        "audit_solves": 208,
        "raw_margin": 5e-4,
        "local_value_tolerance": 1e-4,
        "increment_floor": 1e-5,
        "increment_error_tolerance": 0.25,
        "gradient_floor": 1e-8,
        "gradient_error_tolerance": 0.25,
        "fd_tolerance": 1e-4,
        "process_seconds": 600,
        "max_seconds": 1260,
        "closure_seconds": 60,
        "max_rss_bytes": 1073741824,
        "fit_population": [432, 76],
        "fit_seeds": 3,
        "fit_epochs": 200,
        "cost_factor": 1.25,
        "baseline_fit_seconds": 3870.204341,
        "prior_charged_seconds": [84.33, 55.99, 112.34, 86.13],
        "future_fit_seconds": 7200,
        "full_fit_memory_feasibility_pending": True,
        "fits": 0,
        "new_labels": 0,
        "screen_queries": 0,
        "final_access": False,
    }
    # JSON lists at this boundary make the printed plan equal the parsed receipt.
    import json

    payload = json.loads(canonical(payload))
    return {**payload, "plan_sha256": sha(canonical(payload))}


def check_inputs(root, data_root):
    bound = {
        p: read(root, p, h) for p, h in BINDINGS.items() if not p.startswith(("profiles/", "logs/"))
    }
    for p, h in BINDINGS.items():
        safe_hash(root, p, h)
    closed, audit, evidence, proof, control = (
        bound[p]
        for p in (
            "resource_close.json",
            "independent_audit.json",
            "audit_receipts/evidence_release.json",
            "audit_receipts/closure_profile_verification.json",
            "audit_receipts/postexit_controller_reservation.json",
        )
    )
    if (
        bound["audit_receipts/plan.json"] != prior_plan()
        or not audit["passed"]
        or audit["arithmetic_conditions"] != 1286
        or not closed["closed"]
        or not closed["cost_review_acceptance_passed"]
        or closed["original_cost_gate_passed"]
        or closed["charged_seconds"] != 86.13
        or closed["next_slice"] != SURROGATE_NEXT
        or not proof["passed"]
        or not control["passed"]
        or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]
        or control["resource_close_sha256"] != BINDINGS["resource_close.json"]
        or not evidence["all_applicable_ci_passed_before_merge"]
        or not evidence["merged_tree_equals_tested_tree"]
        or evidence["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
        or not evidence["failed_metadata_plan_attempts"] == 1
        or evidence["failed_metadata_plan_rss_available"]
        or any(
            v["final_access"] or v["repaired_gate"] or not v["old_fresh_sealed"]
            for v in (closed, evidence)
        )
    ):
        raise ValueError("requires closed B4.18 decision and preserved failed profiling attempt")
    for p, h in closed["profile_sha256"].items():
        safe_hash(root, "profiles/" + p, h)
    safe_hash(root, "profiles/closure.time", proof["closure_profile_sha256"])
    for name, key in (("plan", "plan_profile_sha256"), ("verification", "success_profile_sha256")):
        safe_hash(root, "profiles/" + name + ".time", control[key])
    check_prior(root.parent / "b4-17-prepared-fem-probe")
    return check_data(root.parent / "b4-14-generalist-method-review", data_root)


def check_budget(started):
    if perf_counter() - started + 10 > 600 or peak_rss() > 1073741824:
        raise RuntimeError("frozen surrogate process resource cap exceeded")


def fixture(anchor, volume, spec):
    region, amplitude, name, sign = spec
    return (
        np.full(anchor.size, volume)
        if region == "uniform"
        else np.clip(
            anchor + sign * amplitude * direction_vector(anchor.size, name), 5e-4, 1 - 5e-4
        )
    )


def fidelity(approx, exact, gradient, exact_gradient):
    error = abs(approx - exact)
    delta = exact - 1
    return {
        "normalized_value_error": error,
        "increment_relative_error": error / max(abs(delta), 1e-5),
        "gradient_relative_error": float(
            np.linalg.norm(gradient - exact_gradient) / max(np.linalg.norm(exact_gradient), 1e-8)
        ),
        "increment_sign_agrees": abs(delta) <= 1e-5 or bool(np.sign(approx - 1) == np.sign(delta)),
        "surrogate_gradient_norm": float(np.linalg.norm(gradient)),
        "exact_gradient_norm": float(np.linalg.norm(exact_gradient)),
    }


def local_pass(metrics):
    return (
        metrics["normalized_value_error"] <= 1e-4
        and metrics["increment_relative_error"] <= 0.25
        and metrics["gradient_relative_error"] <= 0.25
        and metrics["increment_sign_agrees"]
    )


def probe(data_root, index, started):
    torch.set_num_threads(1)
    labels, setup, rows = [], [], []
    for entry in selected_entries():
        check_budget(started)
        wall, cpu = perf_counter(), process_time()
        record, artifact = train_label(data_root, index, entry)
        anchor = np.asarray(record.stored.design_density)
        kernel = LocalCompliance(entry.case, anchor, record.stored.compliance)
        setup.append(
            {
                "case_id": entry.case.case_id,
                "wall_seconds": perf_counter() - wall,
                "cpu_seconds": process_time() - cpu,
                "retained_array_bytes": sum(a.nbytes for a in kernel.retained_arrays()),
            }
        )
        labels.append(
            {
                "case_id": entry.case.case_id,
                "artifact": artifact,
                "anchor": anchor.tolist(),
                "normalizer": record.stored.compliance,
                "anchor_compliance": kernel.anchor_compliance,
                "design_gradient": kernel.design_gradient.tolist(),
                "stored_volume": float(np.mean(record.stored.physical_density)),
            }
        )
        exact_kernel = OfflineCompliance(entry.case, record.stored.compliance)
        for number, spec in enumerate(state_specs()):
            check_budget(started)
            raw = fixture(anchor, entry.case.problem.optimization.volume_fraction, spec)
            values, gradients, timings = [], [], []
            for repeat in range(3):
                wall, cpu = perf_counter(), process_time()
                tensor = torch.tensor(raw, dtype=torch.float64, requires_grad=True)
                loss = torch_local_loss(tensor, kernel)
                loss.backward()
                gradient = tensor.grad.detach().numpy().copy()
                timings.append(
                    {
                        "repeat": repeat,
                        "wall_seconds": perf_counter() - wall,
                        "cpu_seconds": process_time() - cpu,
                    }
                )
                values.append(loss.item())
                gradients.append(gradient)
            candidate = kernel.evaluate(raw)
            exact = exact_kernel.evaluate(raw)
            differences = []
            if number in (0, 4):
                for direction in ("sine", "cosine"):
                    vector = direction_vector(raw.size, direction)
                    for step in (1e-4, 2e-4):
                        check_budget(started)
                        sides = []
                        for sign in (1, -1):
                            side = kernel.evaluate(raw + sign * step * vector)
                            exact_side = exact_kernel.evaluate(raw + sign * step * vector)
                            sides.append(
                                {
                                    "surrogate": side.value,
                                    "exact": exact_side.value,
                                    "free": side.projection.free.tolist(),
                                }
                            )
                        fd = (sides[0]["surrogate"] - sides[1]["surrogate"]) / (2 * step)
                        derivative = float(candidate.gradient @ vector)
                        differences.append(
                            {
                                "direction": direction,
                                "step": step,
                                "sides": sides,
                                "surrogate_fd": fd,
                                "surrogate_derivative": derivative,
                                "surrogate_error": abs(fd - derivative)
                                / max(abs(fd), abs(derivative), 1e-8),
                                "same_active_set": all(
                                    np.array_equal(s["free"], candidate.projection.free)
                                    for s in sides
                                ),
                                "exact_fd": (sides[0]["exact"] - sides[1]["exact"]) / (2 * step),
                                "exact_derivative": float(exact.gradient @ vector),
                            }
                        )
            metrics = fidelity(candidate.value, exact.value, candidate.gradient, exact.gradient)
            rows.append(
                {
                    "case_id": entry.case.case_id,
                    "state": number,
                    "spec": list(spec),
                    "scale": "small" if raw.size == 216 else "large",
                    "raw": raw.tolist(),
                    "design": candidate.projection.design.tolist(),
                    "physical": candidate.projection.physical.tolist(),
                    "free": candidate.projection.free.tolist(),
                    "surrogate": candidate.value,
                    "exact": exact.value,
                    "gradient": candidate.gradient.tolist(),
                    "exact_gradient": exact.gradient.tolist(),
                    "repeat_values": values,
                    "repeat_gradient_max_difference": max(
                        float(np.max(abs(g - candidate.gradient))) for g in gradients
                    ),
                    "timings": timings,
                    "differences": differences,
                    "fidelity": metrics,
                    "local_pass": local_pass(metrics) if spec[0] == "local" else None,
                    "maximum_design_distance": float(
                        np.max(abs(candidate.projection.design - anchor))
                    ),
                    "maximum_physical_distance": float(
                        np.max(
                            abs(
                                candidate.projection.physical
                                - np.asarray(record.stored.physical_density)
                            )
                        )
                    ),
                    "volume_error": abs(
                        float(candidate.projection.physical.mean())
                        - entry.case.problem.optimization.volume_fraction
                    ),
                    "gradient_shift_sum": float(candidate.gradient.sum()),
                }
            )
    check_budget(started)
    return {
        "plan": plan_payload(),
        "labels": labels,
        "setup": setup,
        "rows": rows,
        "solver_calls": 208,
        "fits": 0,
        "new_labels": 0,
        "final_access": False,
        "old_fresh_sealed": True,
        "repaired_gate": False,
    }


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("review", "data", "output"):
        parser.add_argument("--" + name + "-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    root, data, output = (p.resolve() for p in (args.review_root, args.data_root, args.output_root))
    roots(root, output)
    roots(data, output)
    if args.execute and (
        (root.name, data.name, output.name)
        != ("b4-18-fem-objective-method-review", "b3-v1-data", "b4-19-local-compliance-surrogate")
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
    target = output / "probe.json"
    if target.exists():
        raise ValueError("refuses to overwrite probe")
    revision = execution_release(output)
    index = check_inputs(root, data)
    result = probe(data, index, started)
    check_inputs(root, data)
    result.update(
        source_revision=revision,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
    )
    check_budget(started)
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(
        canonical(
            {k: result[k] for k in ("solver_calls", "charged_seconds", "peak_rss_bytes")}
        ).decode(),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
