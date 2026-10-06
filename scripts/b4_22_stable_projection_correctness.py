"""One stable-root candidate; complete train-only correctness and durable calls."""

import argparse
import traceback
from pathlib import Path
from time import perf_counter

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
    raw_fixture,
    selected_entries,
    train_label,
)
from b4_20_surrogate_correctness import Journal as PriorJournal
from b4_20_surrogate_correctness import check_inputs as check_train
from b4_20_surrogate_correctness import label_metadata, solve
from b4_21_correctness_failure_review import NUMERICAL_NEXT
from b4_21_correctness_failure_review import check_inputs as check_prior
from b4_21_correctness_failure_review import plan_payload as prior_plan

from topolab.baselines import _case_system
from topolab.local_compliance import torch_local_loss
from topolab.simp import apply_density_filter, build_density_filter
from topolab.stable_projection import VERSION as KERNEL_VERSION
from topolab.stable_projection import StableStoredNormalizerTangent

VERSION = "topolab.b4_22.stable-projection-correctness.v1"
BINDINGS = {
    "audit_receipts/plan.json": "a100ac8bdb224d0937181bc687191e26f67edcb3d6316504803174d55dacdd1e",
    "audit_receipts/production_release.json": (
        "d80a983672d9e2d7efcb9408b200c66bab4acd5932e4debdecdf4a0d9a172f57"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "ed5dcfc10b052046b14a7abd4c43bbe6de4f7d4937e01c8acf4d0297c59fde84"
    ),
    "review.json": "22d698eb38d9e6dda2410e8fe4594de1a71134f059cfafa8848fb78a1b8b9819",
    "independent_audit.json": "b4a4401870d53f824bb905e3426c0b562df58734eace7b07d4a4455dab566f17",
    "resource_close.json": "8b8fb36eca3285eb1f845da26b8886a404e04765f8c8cd0750fc63bec39b8d1d",
    "audit_receipts/execution_commands.json": (
        "cb2ddced8835cd8007c304a64c3871cddfd66e94712c97e6e709aefa44843703"
    ),
    "audit_receipts/closure_profile_verification.json": (
        "287903096f0096d99686135c20b3e1ca822102c4fa82dbb917b23d4c6cae2712"
    ),
    "audit_receipts/postexit_controller_reservation.json": (
        "a966f1b6d33643a0fa29474cd6341318f23348d2b1c7921d2d043d495bc4364f"
    ),
    "audit_receipts/evidence_release.json": (
        "5cb5bb25422a03cc921cdede8bad4a8c4d8c00930ae12d8b21e43736511fbfd5"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "00b4c2f998e8ca2180161370105f6783d734ee9eb0a879337272090f72214fe4"
    ),
    "audit_receipts/evidence_main_ci.json": (
        "76cf230a5a3ec0985fbd0bd994e540c925e74c0a30948f947e7d45a15b20238e"
    ),
}
PASS_NEXT = "B4.23 bounded versioned local-surrogate fidelity and cost probe"
FAIL_NEXT = "B4.23 bounded stable-projection correctness failure review"


def plan_payload():
    payload = {
        "version": VERSION,
        "kernel_version": KERNEL_VERSION,
        "bindings": BINDINGS,
        "prior_plan_sha256": prior_plan()["plan_sha256"],
        "b3_index_sha256": INDEX_SHA,
        "entries": [e.model_dump(mode="json") for e in selected_entries()],
        "states": ["interior", "clipped"],
        "directions": ["sine", "cosine"],
        "steps": [1e-4, 2e-4],
        "cases": 8,
        "fixtures": 16,
        "directional_rows": 64,
        "probe_solves": 16,
        "audit_solves": 16,
        "probe_projections": 160,
        "audit_projections": 144,
        "numerical_conditions": 1704,
        "volume_tolerance": 1e-12,
        "kink_tolerance": 1e-10,
        "fd_tolerance": 1e-4,
        "density_tolerance": 2e-11,
        "process_seconds": 300,
        "max_seconds": 660,
        "closure_seconds": 60,
        "max_rss_bytes": 1073741824,
        "fits": 0,
        "new_labels": 0,
        "screen_queries": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
        "local_fidelity_evaluated": False,
        "fit_proxy": None,
        "full_fit_memory_feasibility_pending": True,
        "prior_b4_19_charge_unchanged": 73.93,
    }
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
        or not closed["full_panel_review_complete"]
        or not closed["review_acceptance_passed"]
        or abs(closed["charged_seconds"] - 90.27) > 1e-10
        or closed["original_correctness_gate_passed"]
        or closed["next_slice"] != NUMERICAL_NEXT
        or not audit["passed"]
        or audit["independent_scalar_conditions"] != 1152
        or not evidence["all_applicable_ci_passed_before_merge"]
        or not evidence["merged_tree_equals_tested_tree"]
        or evidence["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
        or any(
            v["final_access"] or v["repaired_gate"] or not v["old_fresh_sealed"]
            for v in (closed, audit, evidence)
        )
    ):
        raise ValueError("requires closed B4.21 ordered decision and unchanged failed Gate/seals")
    for p in ("closure_profile_verification", "postexit_controller_reservation"):
        proof = read(root, "audit_receipts/" + p + ".json")
        if not proof["passed"] or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]:
            raise ValueError("prior native resource verification differs")
    check_prior(root.parent / "b4-20-surrogate-correctness")
    return check_train(root.parent / "b4-19-local-compliance-surrogate", data)


def check_budget(started):
    if perf_counter() - started + 10 > 300 or peak_rss() > 1073741824:
        raise RuntimeError("frozen correctness process cap exceeded")


class Journal(PriorJournal):
    """Reuse durable writes with a new bound plan and all root-call counters."""

    def __init__(self, path, revision):
        self.stream = path.open("xb")
        self.sequence = 0
        self.revision = revision
        self.plan_sha256 = plan_payload()["plan_sha256"]
        self.counts = {k: {"attempted": 0, "completed": 0} for k in ("label", "fem", "projection")}
        self.emit("start")


def projection_metadata(result, raw, settings):
    state = result.projection
    shifted = raw + state.offset
    return {
        "offset": state.offset,
        "weighted_volume_residual": float(state.weights @ state.design) - settings.volume_fraction,
        "physical_volume_residual": float(state.physical.mean()) - settings.volume_fraction,
        "kink_margin": float(
            np.min(np.minimum(abs(shifted - settings.minimum_density), abs(shifted - 1)))
        ),
    }


def evaluate(kernel, raw, journal, cid, context):
    return journal.invoke(
        "projection",
        cid,
        {**context, "raw_sha256": sha(np.asarray(raw, dtype="<f8").tobytes())},
        lambda: kernel.evaluate(raw),
        lambda result: {
            "value": result.value,
            "projection": projection_metadata(result, raw, kernel.case.problem.optimization),
        },
    )


def torch_step(kernel, raw):
    tensor = torch.tensor(raw, dtype=torch.float64, requires_grad=True)
    loss = torch_local_loss(tensor, kernel)
    loss.backward()
    return {"value": loss.item(), "gradient": tensor.grad.detach().numpy().tolist()}


def probe(data, index, journal, started):
    torch.set_num_threads(1)
    cases = []
    for entry in selected_entries():
        check_budget(started)
        cid = entry.case.case_id
        journal.emit("case_start", case_id=cid)
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
        case = {
            "case_id": cid,
            **label,
            "continuous_physical": continuous.tolist(),
            "stored_compliance": cs.compliance,
            "continuous_compliance": cc.compliance,
            "intercept": cc.compliance / label["normalizer"],
            "old_equality_rejects_new_anchor": not bool(
                np.isclose(
                    cc.compliance,
                    label["normalizer"],
                    rtol=1e-9,
                    atol=0,
                )
            ),
            "design_gradient": kernel.design_gradient.tolist(),
            "rows": [],
        }
        journal.emit("anchor", case_id=cid, result=case)
        for state in ("interior", "clipped"):
            check_budget(started)
            journal.emit("fixture_start", case_id=cid, state=state)
            raw = raw_fixture(entry.case, state)
            result = evaluate(kernel, raw, journal, cid, {"state": state, "kind": "direct"})
            bridge = journal.invoke(
                "projection",
                cid,
                {
                    "state": state,
                    "kind": "torch",
                    "raw_sha256": sha(np.asarray(raw, dtype="<f8").tobytes()),
                },
                lambda kernel=kernel, raw=raw: torch_step(kernel, raw),
                lambda result: result,
            )
            row = {
                "state": state,
                "raw": raw.tolist(),
                "design": result.projection.design.tolist(),
                "physical": result.projection.physical.tolist(),
                "free": result.projection.free.tolist(),
                "value": result.value,
                "gradient": result.gradient.tolist(),
                "torch_value": bridge["value"],
                "torch_gradient": bridge["gradient"],
                "projection": projection_metadata(result, raw, entry.case.problem.optimization),
                "differences": [],
            }
            for name in ("sine", "cosine"):
                d = direction_vector(raw.size, name)
                for h in (1e-4, 2e-4):
                    journal.emit(
                        "direction_start", case_id=cid, state=state, direction=name, step=h
                    )
                    sides = [
                        evaluate(
                            kernel,
                            raw + sign * h * d,
                            journal,
                            cid,
                            {
                                "state": state,
                                "kind": "side",
                                "direction": name,
                                "step": h,
                                "sign": sign,
                            },
                        )
                        for sign in (1, -1)
                    ]
                    fd = (sides[0].value - sides[1].value) / (2 * h)
                    derivative = float(result.gradient @ d)
                    diff = {
                        "direction": name,
                        "step": h,
                        "values": [s.value for s in sides],
                        "free": [s.projection.free.tolist() for s in sides],
                        "projections": [
                            projection_metadata(
                                s, raw + sign * h * d, entry.case.problem.optimization
                            )
                            for s, sign in zip(sides, (1, -1), strict=True)
                        ],
                        "fd": fd,
                        "derivative": derivative,
                        "error": abs(fd - derivative) / max(abs(fd), abs(derivative), 1e-8),
                    }
                    row["differences"].append(diff)
                    journal.emit("direction", case_id=cid, state=state, result=diff)
            case["rows"].append(row)
            journal.emit("fixture", case_id=cid, result=row)
        cases.append(case)
        journal.emit("case_complete", case_id=cid)
    return {
        "plan": plan_payload(),
        "cases": cases,
        "counts": journal.counts,
        "fits": 0,
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
            "b4-21-correctness-failure-review",
            "b3-v1-data",
            "b4-22-stable-projection-correctness",
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
        journal.emit("complete", counts=result["counts"])
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
