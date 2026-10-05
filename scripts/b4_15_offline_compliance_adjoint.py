"""Frozen eight-train-case offline adjoint probe; default mode is metadata-only."""

from __future__ import annotations

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
from b4_14_generalist_method_review import (
    check_inputs as check_prior,
)

from topolab.b3_access import B3Access
from topolab.b3_artifacts import read_b3_record
from topolab.b3_catalog import build_b3_case_catalog
from topolab.b3_dataset import B3LabelRecord
from topolab.b3_materialization import B3MaterializationIndex
from topolab.experiment import project_design_density
from topolab.offline_compliance import VERSION as KERNEL_VERSION
from topolab.offline_compliance import OfflineCompliance, project, torch_loss

VERSION = "topolab.b4_15.offline-compliance-adjoint.v1"
INDEX_SHA = "b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26"
BINDINGS = {
    "review.json": "87a4df2a8ac7997d2946553fb97b657a98baa582e54439a2dc9abd21858237a3",
    "independent_audit.json": "ebfec07894421cacd25d81af7f9e9e1450f267d8db1e1c4051e1979e8f2d42ad",
    "resource_close.json": "4c8dbb77432bd090a28e66ac461ae94f5edf084b0708f7bedd9b643fabcdd7fe",
    "audit_receipts/closure_profile_verification.json": (
        "34e94244a09cf58c7af4db4e74b78007bedce6080feb6cd47658c32cafcff1c5"
    ),
    "audit_receipts/evidence_release.json": (
        "f91e0813ceb16a7c44a22f7d4c2cb005f6fa4bcc787e78acb356705c17a26489"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "28a7e11baeb835fe5cf49cebede85e76b45c15f7f6a7f74ceb89713b44ecfea1"
    ),
}


def selected_entries():
    catalog = build_b3_case_catalog()
    return tuple(
        e
        for nx in (12, 24)
        for direction in ("y", "z")
        for e in [
            x
            for x in catalog.entries
            if x.role == "train"
            and "expanded" in x.training_sets
            and x.case.problem.mesh.element_counts[0] == nx
            and x.case.problem.loads[0].direction == direction
        ][:2]
    )


def plan_payload():
    payload = {
        "version": VERSION,
        "kernel_version": KERNEL_VERSION,
        "entries": [e.model_dump(mode="json") for e in selected_entries()],
        "bindings": BINDINGS,
        "b3_index_sha256": INDEX_SHA,
        "states": ["interior", "clipped"],
        "directions": ["sine", "cosine"],
        "steps": [1e-4, 2e-4],
        "repeats": 3,
        "probe_solves": 176,
        "audit_solves": 24,
        "max_seconds": 1260,
        "process_seconds": 600,
        "closure_seconds": 30,
        "max_rss_bytes": 1073741824,
        "future_fit_seconds": 7200,
        "fit_population": [432, 76],
        "fit_seeds": 3,
        "fit_epochs": 200,
        "cost_factor": 1.25,
        "baseline_fit_seconds": 3870.204341,
        "fd_tolerance": 1e-4,
        "volume_tolerance": 1e-12,
        "final_access": False,
        "new_labels": 0,
        "fits": 0,
        "screen_queries": 0,
    }
    return {**payload, "plan_sha256": sha(canonical(payload))}


def check_inputs(review_root, data_root):
    bound = {p: read(review_root, p, h) for p, h in BINDINGS.items()}
    audit = bound["independent_audit.json"]
    closed = bound["resource_close.json"]
    evidence = bound["audit_receipts/evidence_release.json"]
    proof = bound["audit_receipts/closure_profile_verification.json"]
    if (
        not audit["passed"]
        or audit["compact_rows"] != 684
        or not closed["closed"]
        or not closed["method_review_acceptance_passed"]
        or closed["repaired_gate"]
        or closed["charged_seconds"] != 50.39
        or not proof["passed"]
        or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]
        or not evidence["all_applicable_ci_passed_before_merge"]
        or not evidence["merged_tree_equals_tested_tree"]
        or evidence["final_access"]
        or evidence["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
    ):
        raise ValueError("requires closed B4.14 review and unchanged failed repair")
    for name, digest in closed["profile_sha256"].items():
        safe_hash(review_root, "profiles/" + name, digest)
    safe_hash(review_root, "profiles/closure.time", proof["closure_profile_sha256"])
    check_prior(review_root.parent / "b4-13-preservation-diagnosis")
    safe_hash(data_root, "b3_materialization.json", INDEX_SHA)
    index = B3MaterializationIndex.model_validate_json(
        (data_root / "b3_materialization.json").read_bytes()
    )
    if not index.data_gate_passed:
        raise ValueError("requires complete audited B3 data")
    return index


def train_label(data_root, index, entry):
    # Exact role/subset rejection precedes even looking up a label artifact.
    if (
        entry not in selected_entries()
        or entry.role != "train"
        or "expanded" not in entry.training_sets
    ):
        raise ValueError("only frozen eight expanded train labels may be opened")
    outcome = next(o for o in index.entries if o.entry == entry)
    if outcome.status != "succeeded":
        raise ValueError("frozen training label unavailable")
    record = read_b3_record(
        data_root,
        index.manifest,
        outcome.artifact,
        B3Access(consumer="fitting", training_set="expanded"),
    )
    if not isinstance(record, B3LabelRecord):
        raise ValueError("requires matching train label")
    return record, outcome.artifact.model_dump(mode="json")


def raw_fixture(case, name):
    n = int(np.prod(case.problem.mesh.element_counts))
    i = np.arange(1, n + 1)
    if name == "interior":
        return (
            case.problem.optimization.volume_fraction
            + 0.02 * np.sin(0.37 * i)
            + 0.01 * np.cos(0.13 * i)
        )
    if name == "clipped":
        return np.resize(np.array([0.02, 0.5, 0.98]), n)
    raise ValueError("unknown fixed fixture")


def direction_vector(n, name):
    i = np.arange(1, n + 1)
    value = np.sin(0.37 * i) if name == "sine" else np.cos(0.13 * i)
    return value / np.max(np.abs(value))


def check_budget(started):
    if perf_counter() - started + 10 > 600 or peak_rss() > 1073741824:
        raise RuntimeError("frozen offline probe process resource cap exceeded")


def probe(data_root, index, started):
    torch.set_num_threads(1)
    rows, labels, setup = [], [], []
    for entry in selected_entries():
        check_budget(started)
        wall, cpu = perf_counter(), process_time()
        record, artifact = train_label(data_root, index, entry)
        kernel = OfflineCompliance(entry.case, record.stored.compliance)
        setup.append(
            {
                "case_id": entry.case.case_id,
                "wall_seconds": perf_counter() - wall,
                "cpu_seconds": process_time() - cpu,
            }
        )
        labels.append(
            {
                "case_id": entry.case.case_id,
                "artifact": artifact,
                "normalizer": record.stored.compliance,
            }
        )
        for name in plan_payload()["states"]:
            raw = raw_fixture(entry.case, name)
            timings, values, gradients = [], [], []
            for _ in range(3):
                check_budget(started)
                wall, cpu = perf_counter(), process_time()
                tensor = torch.tensor(raw, dtype=torch.float64, requires_grad=True)
                loss = torch_loss(tensor, kernel)
                loss.backward()
                gradient = tensor.grad.detach().numpy().copy()
                values.append(loss.item())
                gradients.append(gradient)
                timings.append(
                    {"wall_seconds": perf_counter() - wall, "cpu_seconds": process_time() - cpu}
                )
            state = project(
                kernel.filt,
                raw,
                entry.case.problem.optimization.volume_fraction,
                entry.case.problem.optimization.minimum_density,
            )
            legacy = project_design_density(
                entry.case, raw.reshape((1, *reversed(entry.case.problem.mesh.element_counts)))
            )
            differences = []
            for direction in plan_payload()["directions"]:
                vector = direction_vector(raw.size, direction)
                adjoint = float(gradients[0] @ vector)
                for step in plan_payload()["steps"]:
                    check_budget(started)
                    plus = kernel.evaluate(raw + step * vector)
                    minus = kernel.evaluate(raw - step * vector)
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
                                np.array_equal(plus.projection.free, state.free)
                                and np.array_equal(minus.projection.free, state.free)
                            ),
                            "volume_errors": [
                                abs(
                                    float(p.physical.mean())
                                    - entry.case.problem.optimization.volume_fraction
                                )
                                for p in (plus.projection, minus.projection)
                            ],
                        }
                    )
            rows.append(
                {
                    "case_id": entry.case.case_id,
                    "state": name,
                    "scale": "small" if raw.size == 216 else "large",
                    "raw": raw.tolist(),
                    "design": state.design.tolist(),
                    "physical": state.physical.tolist(),
                    "free": state.free.tolist(),
                    "value": values[0],
                    "gradient": gradients[0].tolist(),
                    "repeat_values": values,
                    "repeat_gradient_max_difference": max(
                        float(np.max(np.abs(g - gradients[0]))) for g in gradients
                    ),
                    "timings": timings,
                    "differences": differences,
                    "volume_error": abs(
                        float(state.physical.mean())
                        - entry.case.problem.optimization.volume_fraction
                    ),
                    "gradient_shift_sum": float(gradients[0].sum()),
                    "legacy_max_density_difference": float(
                        np.max(np.abs(state.design - legacy.design_density))
                    ),
                    "legacy_volume_error": abs(
                        float(legacy.physical_density.mean())
                        - entry.case.problem.optimization.volume_fraction
                    ),
                }
            )
    check_budget(started)
    return {
        "plan": plan_payload(),
        "labels": labels,
        "setup": setup,
        "rows": rows,
        "solver_calls": 176,
        "fits": 0,
        "final_access": False,
        "old_fresh_sealed": True,
        "repaired_gate": False,
    }


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    review_root, data_root, output = (
        p.resolve() for p in (args.review_root, args.data_root, args.output_root)
    )
    roots(review_root, output)
    roots(data_root, output)
    if args.execute and (review_root.name, data_root.name, output.name) != (
        "b4-14-generalist-method-review",
        "b3-v1-data",
        "b4-15-offline-compliance-adjoint",
    ):
        raise ValueError("requires fixed external roots")
    if args.execute and not review_root.parent == data_root.parent == output.parent:
        raise ValueError("requires sibling immutable inputs")
    return args, review_root, data_root, output


def main(argv=None):
    started = perf_counter()
    args, review_root, data_root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    target = output / "probe.json"
    if target.exists():
        raise ValueError("refuses to overwrite probe")
    revision = execution_release(output)
    index = check_inputs(review_root, data_root)
    result = probe(data_root, index, started)
    check_inputs(review_root, data_root)
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
