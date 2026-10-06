"""Frozen representation/correctness review; durable train-only numerical prefix."""

import argparse
import os
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
from b4_19_local_compliance_surrogate import check_inputs as check_prior
from b4_19_local_compliance_surrogate import plan_payload as prior_plan

from topolab.baselines import _case_system
from topolab.local_compliance import (
    STORED_NORMALIZER_VERSION,
    StoredNormalizerTangent,
    torch_local_loss,
)
from topolab.simp import apply_density_filter, build_density_filter, evaluate_compliance

VERSION = "topolab.b4_20.surrogate-correctness.v1"
BINDINGS = {
    "audit_receipts/plan.json": "b2058c3441e869395c0038f09b6eeeaa3c71d3f120438ec95b81cb7d1c723194",
    "audit_receipts/production_release.json": (
        "c87f98ab245f16b1d3f597413de235c1542d695275417baa4971c5543ed986e9"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "eb132aa3b78ec08fe9de0cf2890417edaea388ee34ba34c6ff3d1d1d2da3e199"
    ),
    "audit_receipts/execution_commands.json": (
        "9cfb7f2cdd7c9cedb260c0a005d127debc0b6520f40c3ae3492893d08cc2dd27"
    ),
    "profiles/probe.time": "97cf94ebddc4169602be27ca4aba4d3b7483cd24ead2564e3ccb37de1a88e186",
    "independent_abort_audit.json": (
        "d70531a11edda20271002eb4f4f3085fe5a9e47e3581cf42cf8aa48b2d94f118"
    ),
    "resource_close.json": "c666b76ea79c4b58df5d774e5197fe71d73118476bd8e659a2406ff4fd455c95",
    "audit_receipts/closure_profile_verification.json": (
        "9d6e91bbac52d46a3c50b520fab555888965ee2ea97095277bfb49daff5d49ed"
    ),
    "audit_receipts/postexit_controller_reservation.json": (
        "4888448836b129ff6297a564625f4f4f443b3247f201f7058ed2379f50bf7e9b"
    ),
    "audit_receipts/evidence_release.json": (
        "d66ff9e678c65b5a6ef37a477b40d9c40a386bbd6f2630dad85ab69c4c5c3ea0"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "e4ccc1df959f5ac0464aa49adca7c1f48cd99f2f8b5ffa593bf625d10bcaa8d0"
    ),
}
PASS_NEXT = "B4.21 bounded versioned local-surrogate fidelity and cost probe"
FAIL_NEXT = "B4.21 bounded surrogate correctness failure review"


def plan_payload():
    payload = {
        "version": VERSION,
        "kernel_version": STORED_NORMALIZER_VERSION,
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
    closed, audit, evidence = (
        read(root, p)
        for p in (
            "resource_close.json",
            "independent_abort_audit.json",
            "audit_receipts/evidence_release.json",
        )
    )
    if (
        read(root, "audit_receipts/plan.json") != prior_plan()
        or not closed["closed"]
        or closed["charged_seconds"] != 73.93
        or closed["integrity_passed"]
        or closed["full_probe_complete"]
        or not audit["passed"]
        or not audit["metadata_only"]
        or not evidence["all_applicable_ci_passed_before_merge"]
        or not evidence["merged_tree_equals_tested_tree"]
        or not evidence["no_numerical_rerun"]
        or closed["next_slice"] != "B4.20 bounded surrogate correctness review"
        or any(
            v[k] is not None
            for v in (closed, evidence)
            for k in (
                "actual_failed_case_id",
                "actual_solver_calls",
                "known_normalizer_gap",
                "fit_proxy",
            )
        )
        or any(
            v["final_access"] or v["repaired_gate"] or not v["old_fresh_sealed"]
            for v in (closed, audit, evidence)
        )
    ):
        raise ValueError("requires preserved B4.19 early stop, unknown fields and failed Gate")
    for name, digest in closed["profile_sha256"].items():
        safe_hash(root, "profiles/" + name, digest)
    for p in ("closure_profile_verification", "postexit_controller_reservation"):
        proof = read(root, "audit_receipts/" + p + ".json")
        if not proof["passed"] or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]:
            raise ValueError("prior native resource verification differs")
    return check_prior(root.parent / "b4-18-fem-objective-method-review", data)


def check_budget(started):
    if perf_counter() - started + 10 > 300 or peak_rss() > 1073741824:
        raise RuntimeError("frozen correctness process cap exceeded")


class Journal:
    """Exclusive durable attempt: before-call counters survive exceptions/kills."""

    def __init__(self, path, revision):
        self.stream = path.open("xb")
        self.sequence = 0
        self.revision = revision
        self.plan_sha256 = plan_payload()["plan_sha256"]
        self.counts = {kind: {"attempted": 0, "completed": 0} for kind in ("label", "fem")}
        self.emit("start", source_revision=revision, plan_sha256=plan_payload()["plan_sha256"])

    def emit(self, event, **payload):
        self.stream.write(
            canonical(
                {
                    "sequence": self.sequence,
                    "event": event,
                    "source_revision": self.revision,
                    "plan_sha256": self.plan_sha256,
                    "counts": self.counts,
                    **payload,
                }
            )
        )
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.sequence += 1

    def invoke(self, kind, case_id, context, call, encode):
        self.counts[kind]["attempted"] += 1
        self.emit("before_" + kind, case_id=case_id, context=context)
        try:
            result = call()
        except Exception as error:
            self.emit(
                "failure",
                case_id=case_id,
                context=context,
                error_type=type(error).__name__,
                error=str(error),
                traceback=traceback.format_exc(),
            )
            raise
        self.counts[kind]["completed"] += 1
        self.emit("after_" + kind, case_id=case_id, context=context, result=encode(result))
        return result

    def close(self):
        self.stream.close()


def label_metadata(item):
    record, artifact = item
    return {
        "artifact": artifact,
        "normalizer": record.stored.compliance,
        "anchor": list(record.stored.design_density),
        "stored_physical": list(record.stored.physical_density),
    }


def solve(entry, physical, normalizer, name, journal):
    mesh, loads, constrained = _case_system(entry.case)
    p = entry.case.problem
    return journal.invoke(
        "fem",
        entry.case.case_id,
        {
            "state": name,
            "normalizer": normalizer,
            "physical": physical.tolist(),
            "physical_sha256": sha(np.asarray(physical, dtype="<f8").tobytes()),
        },
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
        kernel = StoredNormalizerTangent(entry.case, anchor, label["normalizer"], cc)
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
            result = kernel.evaluate(raw)
            tensor = torch.tensor(raw, dtype=torch.float64, requires_grad=True)
            loss = torch_local_loss(tensor, kernel)
            loss.backward()
            row = {
                "state": state,
                "raw": raw.tolist(),
                "design": result.projection.design.tolist(),
                "physical": result.projection.physical.tolist(),
                "free": result.projection.free.tolist(),
                "value": result.value,
                "gradient": result.gradient.tolist(),
                "torch_value": loss.item(),
                "torch_gradient": tensor.grad.detach().numpy().tolist(),
                "differences": [],
            }
            for name in ("sine", "cosine"):
                d = direction_vector(raw.size, name)
                for h in (1e-4, 2e-4):
                    sides = [kernel.evaluate(raw + sign * h * d) for sign in (1, -1)]
                    fd = (sides[0].value - sides[1].value) / (2 * h)
                    derivative = float(result.gradient @ d)
                    diff = {
                        "direction": name,
                        "step": h,
                        "values": [s.value for s in sides],
                        "free": [s.projection.free.tolist() for s in sides],
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
            "b4-19-local-compliance-surrogate",
            "b3-v1-data",
            "b4-20-surrogate-correctness",
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
