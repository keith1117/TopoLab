"""Frozen paired setup-reuse probe; metadata planning opens no artifacts."""

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
from b4_15_offline_compliance_adjoint import direction_vector, raw_fixture, selected_entries
from b4_15_offline_compliance_adjoint import plan_payload as original_plan
from b4_16_offline_adjoint_cost_review import PHASE_NEXT, PROBE_SHA
from b4_16_offline_adjoint_cost_review import check_inputs as check_original

from topolab.offline_compliance import OfflineCompliance, torch_loss
from topolab.prepared_compliance import PHASES, PreparedCompliance
from topolab.prepared_compliance import VERSION as KERNEL_VERSION

VERSION = "topolab.b4_17.prepared-fem-probe.v1"
BINDINGS = {
    "audit_receipts/plan.json": "2854d228df3455c7ff379a3a064f475619a8059325126ffefed12c0f73522fb3",
    "audit_receipts/production_release.json": (
        "bb68e581e10659c2124c6d4b485267dfc630d3e8eaff0fac500e3240fda39a62"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "e3f04801281809abdaf454bdb3a4fe8e411883ff3ac4d96683683132f8c068d2"
    ),
    "review.json": "7ebbe7570046c472e9ca77b417b6904940a34a792430f04f8bba143c5f850249",
    "independent_audit.json": "2769e9057ee38bad333a68925141a7a0999aca06177b702d5f5369c73e00843c",
    "resource_close.json": "2bf31e3b9495f65964c4ba015afd872f0270154e72a551ec10160f96596437cc",
    "audit_receipts/execution_commands.json": (
        "460ac132b92229662bc516fbc8a0fd3a91b691f02817ecc93cfaf33bb64c63ba"
    ),
    "audit_receipts/closure_command.json": (
        "41fc848c7c9f6785e4e41249524cefedc36b4df43eac6a694b1ced32790b1f1f"
    ),
    "audit_receipts/closure_profile_verification.json": (
        "b1de723d7f248b847e7f42d298bcfd4911dd5c51ec630ac599b2dd39106d8368"
    ),
    "audit_receipts/postexit_controller_reservation.json": (
        "9f1105badde9a20ab5721150f65014ca2c4967c7665ea573e83113d20fbad76f"
    ),
    "audit_receipts/evidence_release.json": (
        "1ec8d69561bc5f0554fb2b070a5bbf1317e0a854b557ca71d3bcce8d115e05c5"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "b99137a2e271842f5b9e6242865e5377160040f5502cbb92543271d688ea6ac4"
    ),
}
CORRECTNESS_NEXT = "B4.18 bounded prepared-adjoint correctness review"
COST_NEXT = "B4.18 bounded offline FEM bottleneck and training-objective method review"
FIT_NEXT = "B4.18 full-population setup-memory and objective-fit preregistration"


def plan_payload():
    payload = {
        "version": VERSION,
        "kernel_version": KERNEL_VERSION,
        "bindings": BINDINGS,
        "original_probe_sha256": PROBE_SHA,
        "entries": original_plan()["entries"],
        "states": ["interior", "clipped"],
        "directions": ["sine", "cosine"],
        "steps": [1e-4, 2e-4],
        "repeats": 3,
        "arms": ["prepared", "original"],
        "phases": list(PHASES),
        "probe_solves": 240,
        "audit_solves": 16,
        "max_seconds": 1260,
        "process_seconds": 600,
        "closure_seconds": 60,
        "max_rss_bytes": 1073741824,
        "fit_population": [432, 76],
        "fit_seeds": 3,
        "fit_epochs": 200,
        "cost_factor": 1.25,
        "baseline_fit_seconds": 3870.204341,
        "prior_probe_seconds": 84.33,
        "prior_review_seconds": 55.99,
        "future_fit_seconds": 7200,
        "arithmetic_tolerance": 1e-12,
        "fits": 0,
        "label_model_byte_reads": 0,
        "screen_queries": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
        "decision_order": [CORRECTNESS_NEXT, COST_NEXT, FIT_NEXT],
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
        not closed["closed"]
        or not closed["cost_review_acceptance_passed"]
        or closed["original_cost_gate_passed"]
        or closed["next_slice"] != PHASE_NEXT
        or not audit["passed"]
        or audit["observations"] != 48
        or not proof["passed"]
        or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]
        or not control["passed"]
        or control["combined_reserved_charge_seconds"] > 30
        or control["resource_close_sha256"] != BINDINGS["resource_close.json"]
        or not evidence["all_applicable_ci_passed_before_merge"]
        or not evidence["merged_tree_equals_tested_tree"]
        or evidence["repaired_gate"]
        or evidence["final_access"]
        or not evidence["old_fresh_sealed"]
        or evidence["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
    ):
        raise ValueError("requires complete closed B4.16 phase-probe recommendation")
    for name, digest in closed["profile_sha256"].items():
        safe_hash(root, "profiles/" + name, digest)
    safe_hash(root, "profiles/closure.time", proof["closure_profile_sha256"])
    for path, key in (
        ("profiles/verification.time", "success_profile_sha256"),
        ("audit_receipts/postexit_command.json", "success_command_sha256"),
        ("audit_receipts/controller_import_failure.json", "failed_record_sha256"),
        ("logs/controller_import_failure.log", "failed_log_sha256"),
    ):
        safe_hash(root, path, control[key])
    check_original(root.parent / "b4-15-offline-compliance-adjoint")
    return bound


def input_states(original):
    entries = selected_entries()
    ids = [e.case.case_id for e in entries]
    if (
        original["plan"] != original_plan()
        or [r["case_id"] for r in original["labels"]] != ids
        or [(r["case_id"], r["state"]) for r in original["rows"]]
        != [(cid, s) for cid in ids for s in ("interior", "clipped")]
    ):
        raise ValueError("exact training-only synthetic input population differs")
    labels = {r["case_id"]: r for r in original["labels"]}
    for e, pair in zip(
        entries, [original["rows"][i : i + 2] for i in range(0, 16, 2)], strict=True
    ):
        normalizer = labels[e.case.case_id]["normalizer"]
        if not np.isfinite(normalizer) or normalizer <= 0:
            raise ValueError("certified positive normalizer required")
        for row in pair:
            if not np.array_equal(row["raw"], raw_fixture(e.case, row["state"])):
                raise ValueError("metadata-defined raw fixture differs")
    return labels


def check_budget(started):
    if perf_counter() - started + 10 > 600 or peak_rss() > 1073741824:
        raise RuntimeError("bounded prepared probe process resource cap exceeded")


def state_row(result):
    return {
        "value": result.value,
        "compliance": result.compliance,
        "gradient": result.gradient.tolist(),
        "design": result.projection.design.tolist(),
        "physical": result.projection.physical.tolist(),
        "free": result.projection.free.tolist(),
    }


def probe(original, started):
    labels = input_states(original)
    torch.set_num_threads(1)
    rows, setup = [], []
    for entry in selected_entries():
        cid = entry.case.case_id
        kernels = {}
        for arm, cls in (("original", OfflineCompliance), ("prepared", PreparedCompliance)):
            check_budget(started)
            wall, cpu = perf_counter(), process_time()
            kernel = cls(entry.case, labels[cid]["normalizer"])
            timing = {"wall_seconds": perf_counter() - wall, "cpu_seconds": process_time() - cpu}
            kernels[arm] = kernel
            setup.append(
                {
                    "case_id": cid,
                    "arm": arm,
                    **timing,
                    "retained_array_bytes": kernel.retained_array_bytes
                    if arm == "prepared"
                    else None,
                }
            )
        for name in ("interior", "clipped"):
            raw = raw_fixture(entry.case, name)
            measurements = []
            for repeat in range(3):
                for arm in (
                    ("prepared", "original") if repeat % 2 == 0 else ("original", "prepared")
                ):
                    check_budget(started)
                    wall, cpu = perf_counter(), process_time()
                    tensor = torch.tensor(raw, dtype=torch.float64, requires_grad=True)
                    loss = torch_loss(tensor, kernels[arm])
                    loss.backward()
                    gradient = tensor.grad.detach().numpy().copy()
                    value = loss.item()
                    measurements.append(
                        {
                            "repeat": repeat,
                            "arm": arm,
                            "value": value,
                            "gradient": gradient.tolist(),
                            "wall_seconds": perf_counter() - wall,
                            "cpu_seconds": process_time() - cpu,
                        }
                    )
            phases = []
            check_budget(started)
            wall, cpu = perf_counter(), process_time()
            result = kernels["prepared"].evaluate(raw, phases)
            phase_total = {
                "wall_seconds": perf_counter() - wall,
                "cpu_seconds": process_time() - cpu,
            }
            differences = []
            for direction in ("sine", "cosine"):
                vector = direction_vector(raw.size, direction)
                adjoint = float(result.gradient @ vector)
                for step in (1e-4, 2e-4):
                    check_budget(started)
                    plus = kernels["prepared"].evaluate(raw + step * vector)
                    minus = kernels["prepared"].evaluate(raw - step * vector)
                    fd = (plus.value - minus.value) / (2 * step)
                    differences.append(
                        {
                            "direction": direction,
                            "step": step,
                            "plus": plus.value,
                            "minus": minus.value,
                            "fd": fd,
                            "adjoint": adjoint,
                            "error": abs(fd - adjoint) / max(abs(fd), abs(adjoint), 1e-8),
                            "same_active_set": bool(
                                np.array_equal(plus.projection.free, result.projection.free)
                                and np.array_equal(minus.projection.free, result.projection.free)
                            ),
                            "volume_errors": [
                                abs(
                                    float(s.physical.mean())
                                    - entry.case.problem.optimization.volume_fraction
                                )
                                for s in (plus.projection, minus.projection)
                            ],
                        }
                    )
            rows.append(
                {
                    "case_id": cid,
                    "state": name,
                    "raw": raw.tolist(),
                    "scale": "small" if raw.size == 216 else "large",
                    **state_row(result),
                    "measurements": measurements,
                    "phase_total": phase_total,
                    "phases": phases,
                    "phase_residual": {
                        k: phase_total[k] - sum(t[k] for t in phases) for k in phase_total
                    },
                    "differences": differences,
                }
            )
    return {
        "plan": plan_payload(),
        "labels": original["labels"],
        "setup": setup,
        "rows": rows,
        "solver_calls": 240,
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
        "input_sha256": PROBE_SHA,
    }


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    root, output = args.review_root.resolve(), args.output_root.resolve()
    roots(root, output)
    if args.execute and (
        (root.name, output.name)
        != ("b4-16-offline-adjoint-cost-review", "b4-17-prepared-fem-probe")
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
    target = output / "probe.json"
    if target.exists():
        raise ValueError("refuses to overwrite prepared probe")
    revision = execution_release(output)
    check_inputs(root)
    original = read(root.parent / "b4-15-offline-compliance-adjoint", "probe.json", PROBE_SHA)
    result = probe(original, started)
    check_inputs(root)
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
