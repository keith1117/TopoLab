"""Source-only plan or one frozen B4.30 reference/query/numerical/policy stage."""

import argparse
import json
from functools import partial
from pathlib import Path
from time import perf_counter

import numpy as np
from b4_8_rollback_confirmation import load_models as legacy_models
from b4_30_common import (
    CONTRACT_SHA,
    contract,
    fresh_admissible,
    guard_inputs,
    release,
    save,
    stage_cap,
)

from topolab import b4_evidence as evidence
from topolab import b4_reflection_repair as probe
from topolab.b2_5_evaluation import _predict
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b3_artifacts import safe_path
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_queries import QueryOutcome, TerminalWitness, audit_witness, evaluate_query
from topolab.b3_screen_cli import screening_preflight
from topolab.b4_development import DevelopmentSpec, run_development
from topolab.b4_polish import polish, qualifies
from topolab.b4_reflection import POLICY_VERSION, ReflectionAverage, reflection_target
from topolab.b4_telemetry import Journal, digest, durable_write
from topolab.b4_terminal_preservation import POLICY_VERSION as PRESERVATION_VERSION
from topolab.b4_terminal_preservation import VERSION as PREVIOUS_VERSION
from topolab.b4_terminal_preservation import identity, select_terminal
from topolab.b4_weighted_terminal import publish_blob, read_blob, read_units
from topolab.dataset_cli import validate_external_output_root
from topolab.experiment import ExperimentCase
from topolab.problem import TopologyProblem

EXECUTION_VERSION = contract()["version"]


def cohort_caps(cohort):
    return {stage: (float(stage_cap(cohort, stage)), rss) for stage, (_, rss) in probe.CAPS.items()}


def execution_plan():
    """Bind the unchanged scientific v1 recipe to the paid v2 execution boundary."""
    value = {k: v for k, v in probe.plan().items() if k != "plan_sha256"}
    value.update(
        version=EXECUTION_VERSION,
        scientific_contract_sha256=probe.CONTRACT_SHA256,
        contract_sha256=CONTRACT_SHA,
        resources=contract()["resources"],
        continuation=contract()["continuation"],
        caps_by_cohort={name: cohort_caps(name) for name in ("sentinel", "fresh")},
    )
    return {**value, "plan_sha256": digest(canonical_metadata_bytes(value))}


def load_models(context, old, weighted):
    probe.upstream_fits(weighted)
    return legacy_models(context, old, weighted)


def record_prediction(root, sha, seed, case, mirrored, first, second, average):
    value = {
        "version": POLICY_VERSION,
        "context_sha256": sha,
        "case_id": case.case_id,
        "seed": seed,
        "recipe": "P",
        "same_checkpoint_calls": 2,
        "fixed_fits_index_sha256": (
            "229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7"
        ),
        "mirror_case": mirrored.model_dump(mode="json"),
        "shape": list(first.shape),
        "dtype": "float32",
        "device": "cpu",
        "weights": [0.5, 0.5],
        "first": first.detach().numpy().reshape(-1).tolist(),
        "second": second.detach().numpy().reshape(-1).tolist(),
        "average": average.detach().numpy().reshape(-1).tolist(),
    }
    save(root / "prediction" / f"{case.case_id}_{seed}.json", value)


def recorded_refinement(root, sha, family, seed, case, before, checkpoint):
    original = TerminalWitness.from_result(before)
    original_ref = publish_blob(
        root, "prepolish", canonical_metadata_bytes(original.model_dump(mode="json"))
    )
    after = polish(case, before, checkpoint)
    choice = select_terminal(case, before, after)
    chosen = before if choice == "original" else after
    endpoint = TerminalWitness.from_result(after)
    endpoint_ref = publish_blob(
        root, "endpoint", canonical_metadata_bytes(endpoint.model_dump(mode="json"))
    )
    save(
        root / "polish" / family / f"{case.case_id}_{seed}.json",
        {
            "version": PRESERVATION_VERSION,
            "context_sha256": sha,
            "case_id": case.case_id,
            "policy": f"{family}/{seed}",
            "seed": seed,
            "before": original_ref,
            "endpoint": endpoint_ref,
            "selection": choice,
            "triggered": qualifies(case, before),
            "first_stop_iteration": len(original.trace),
            "updates": len(after.history) - len(before.history),
            "after_witness_sha256": digest(
                canonical_metadata_bytes(endpoint.model_dump(mode="json"))
            ),
            "selected_witness_sha256": digest(
                canonical_metadata_bytes(
                    TerminalWitness.from_result(chosen).model_dump(mode="json")
                )
            ),
        },
    )
    return chosen


def evaluator(root, sha, case, method, seed, reference, models, neighbors, checkpoint):
    family = method
    if method == "R":
        method = "P"
        if reflection_target(case):
            models = dict(models)
            models[("P", seed)] = ReflectionAverage(
                case,
                models[("P", seed)],
                checkpoint,
                partial(record_prediction, root, sha, seed, case),
            )
    return evaluate_query(
        case,
        method,
        seed,
        reference,
        models,
        neighbors,
        checkpoint,
        refinement=partial(recorded_refinement, root, sha, family, seed),
    )


def original_references(parent):
    root = parent / "b4-12-terminal-preservation"
    context_sha = digest(safe_path(root, "context.json").read_bytes())
    old_plan = json.loads(safe_path(root, "audit_receipts/plan.json").read_bytes())
    wanted = {c.case_id for c in probe.cases("sentinel")}
    result = {}
    for cohort in ("sentinel", "fresh"):
        order = tuple(tuple(x) for x in old_plan["assignments"][cohort])
        refs = read_units(
            root / cohort / "screen",
            context_sha,
            tuple(f"{c}:{m}" for c, m in order),
            caps=probe.CAPS,
        )
        result.update(
            {
                (c, m): (root / cohort / "screen", ref, context_sha)
                for (c, m), ref in zip(order, refs, strict=True)
                if c in wanted
            }
        )
    if len(result) != 18 * 12:
        raise ValueError("sentinel requires every previous twelve-method identity")
    return result


def old_packet(mapping, key):
    root, ref, sha = mapping[key]
    return evidence.read_packet(root, ref, sha, key[0], key[1], PREVIOUS_VERSION)


def packets(root, sha, spec):
    refs = read_units(root / "screen", sha, spec.units("screen"), caps=spec.caps)
    return (
        evidence.read_packet(root / "screen", ref, sha, c, m, EXECUTION_VERSION)
        for (c, m), ref in zip(spec.assignments, refs, strict=True)
    )


def prediction_audit(root, sha, seed, case, model):
    path = safe_path(root, f"prediction/{case.case_id}_{seed}.json")
    raw = path.read_bytes()
    record = json.loads(raw)
    payload = case.problem.model_dump(mode="json")
    nx, ny, nz = case.problem.mesh.element_counts
    node = payload["loads"][0]["node"]
    iz, rem = divmod(node, (nx + 1) * (ny + 1))
    payload["loads"][0]["node"] = rem + (nx + 1) * (ny + 1) * (nz - iz)
    mirrored = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
    first = _predict(case, model, encoder=encode_vector_load_case)
    second = _predict(mirrored, model, encoder=encode_vector_load_case)
    average = np.multiply(
        np.add(first, second[:, ::-1, :, :], dtype=np.float32), np.float32(0.5), dtype=np.float32
    )
    if (
        raw != canonical_metadata_bytes(record)
        or record["version"] != POLICY_VERSION
        or record["context_sha256"] != sha
        or record["case_id"] != case.case_id
        or record["seed"] != seed
        or record["recipe"] != "P"
        or record["same_checkpoint_calls"] != 2
        or record["fixed_fits_index_sha256"]
        != "229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7"
        or record["mirror_case"] != mirrored.model_dump(mode="json")
        or record["shape"] != [1, 1, nz, ny, nx]
        or record["dtype"] != "float32"
        or record["device"] != "cpu"
        or record["weights"] != [0.5, 0.5]
        or not all(
            record[k] == a.reshape(-1).tolist()
            for k, a in (("first", first), ("second", second), ("average", average))
        )
    ):
        raise ValueError("independent same-weight prediction replay or float32 mean differs")
    return digest(raw)


def policy_audit(output, cohort, sha, spec, context, old, weighted, startup):
    root = output / cohort
    units = (
        *("reference:" + c for c in spec.units("reference")),
        *("policy:" + u for u in spec.units("screen")),
    )
    journal = Journal(
        root / "policy-audit", sha, units, *spec.caps["policy-audit"], opening_seconds=startup
    )
    try:
        refs = {
            stage: read_units(root / stage, sha, spec.units(stage), caps=spec.caps)
            for stage in ("reference", "screen", "audit")
        }
        original = original_references(output.parent) if cohort == "sentinel" else {}
        models, _ = load_models(context, old, weighted)
        by_id = {c.case_id: c for c in spec.cases}
        indices = {key: i for i, key in enumerate(spec.assignments)}
        for unit in units:
            journal.begin(unit)
            result = {
                "unchanged_identity_checked": False,
                "guard_witnesses": 0,
                "prediction_replays": 0,
            }
            if unit.startswith("reference:"):
                case_id = unit.removeprefix("reference:")
                i = spec.units("reference").index(case_id)
                packet = evidence.read_packet(
                    root / "reference",
                    refs["reference"][i],
                    sha,
                    case_id,
                    "uniform",
                    EXECUTION_VERSION,
                )
                if original and identity(packet["outcome"]) != identity(
                    old_packet(original, (case_id, "uniform"))["outcome"]
                ):
                    raise ValueError("sentinel uniform numerical identity changed")
                result["unchanged_identity_checked"] = bool(original)
            else:
                case_id, policy = unit.removeprefix("policy:").split(":")
                case = by_id[case_id]
                packet = evidence.read_packet(
                    root / "screen",
                    refs["screen"][indices[(case_id, policy)]],
                    sha,
                    case_id,
                    policy,
                    EXECUTION_VERSION,
                )
                outcome = QueryOutcome.model_validate(packet["outcome"])
                family, _, seed_text = policy.partition("/")
                if original and family != "R":
                    if identity(packet["outcome"]) != identity(
                        old_packet(original, (case_id, policy))["outcome"]
                    ):
                        raise ValueError("sentinel legacy control numerical identity changed")
                    result["unchanged_identity_checked"] = True
                if family == "R":
                    seed = int(seed_text)
                    if reflection_target(case):
                        result["prediction_sha256"] = prediction_audit(
                            root / "screen", sha, seed, case, models[("P", seed)]
                        )
                        result["prediction_replays"] = 2
                    else:
                        p_ref = refs["screen"][indices[(case_id, f"P/{seed}")]]
                        p = evidence.read_packet(
                            root / "screen", p_ref, sha, case_id, f"P/{seed}", EXECUTION_VERSION
                        )
                        if identity(packet["outcome"]) != identity(p["outcome"]):
                            raise ValueError("non-target R differs from same-seed P")
                        result["unchanged_identity_checked"] = True
                if family in ("P", "R") and outcome.route == "generalist":
                    raw = safe_path(
                        root / "screen", f"polish/{family}/{case_id}_{seed_text}.json"
                    ).read_bytes()
                    record = json.loads(raw)
                    before_raw = read_blob(root / "screen", record["before"], "prepolish")
                    endpoint_raw = read_blob(root / "screen", record["endpoint"], "endpoint")
                    before, endpoint = (
                        TerminalWitness.model_validate_json(x) for x in (before_raw, endpoint_raw)
                    )
                    trigger = qualifies(case, before.result)
                    n = len(before.trace)
                    updates = (
                        min(20, case.problem.optimization.max_iterations - n) if trigger else 0
                    )
                    choice = select_terminal(case, before.result, endpoint.result)
                    chosen = before if choice == "original" else endpoint
                    if (
                        raw != canonical_metadata_bytes(record)
                        or record["version"] != PRESERVATION_VERSION
                        or record["context_sha256"] != sha
                        or record["case_id"] != case_id
                        or record["policy"] != policy
                        or record["seed"] != int(seed_text)
                        or record["triggered"] != trigger
                        or record["first_stop_iteration"] != n
                        or record["updates"] != updates
                        or len(endpoint.trace) != n + updates
                        or endpoint.trace[:n] != before.trace
                        or record["selection"] != choice
                        or chosen != outcome.attempt.state
                        or record["after_witness_sha256"] != digest(endpoint_raw)
                        or record["selected_witness_sha256"]
                        != digest(canonical_metadata_bytes(chosen.model_dump(mode="json")))
                        or not trigger
                        and before != endpoint
                    ):
                        raise ValueError(
                            "unchanged continuation/own-certificate witness choice differs"
                        )
                    audit_witness(case, before, None, accepted=False)
                    audit_witness(case, endpoint, None, accepted=False)
                    result.update(
                        guard_witnesses=2,
                        selection=choice,
                        triggered=trigger,
                        updates=updates,
                        polish_record_sha256=digest(raw),
                    )
            journal.publish(unit, result)
        gate = spec.gate(packets(root, sha, spec))
        journal.close()
        summary = {
            "version": EXECUTION_VERSION,
            "cohort": cohort,
            "context_sha256": sha,
            "passed": gate["repair_gate_passed"],
            "policy_integrity_passed": True,
            "decision": gate,
            "completed": journal.state.completed,
            "attempted": journal.state.attempted,
            "head_sha256": journal.state.head_sha256,
            "charged_seconds": journal.state.charged_seconds,
            "peak_rss_bytes": journal.state.peak_rss_bytes,
        }
        durable_write(root / "policy-audit/summary.json", canonical_metadata_bytes(summary))
        return summary
    except BaseException:
        if not journal.lock.closed:
            journal.close(integrity_failed=True)
        raise


def require_sentinel(output):
    policy = json.loads((output / "sentinel/policy-audit/summary.json").read_bytes())
    independent = json.loads((output / "sentinel/independent_audit.json").read_bytes())
    if not (
        policy["passed"]
        and policy["policy_integrity_passed"]
        and independent["passed"]
        and independent["gate_passed"]
        and independent["policy_summary_sha256"]
        == digest((output / "sentinel/policy-audit/summary.json").read_bytes())
    ):
        raise ValueError("fresh remains sealed until all sentinel audits pass")
    from b4_30_native_execution import stage_charges

    _, complete, rows = stage_charges(output, "sentinel")
    if not fresh_admissible(rows, complete):
        raise ValueError("sentinel native floors cannot reserve the full fresh budget")


def main():
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--stage", choices=probe.CAPS, default="reference")
    parser.add_argument("--cohort", choices=("sentinel", "fresh"), default="sentinel")
    for name in ("data-root", "fit-root", "weighted-root", "output"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(execution_plan(), sort_keys=True))
        return
    if any(x is None for x in (args.data_root, args.fit_root, args.weighted_root, args.output)):
        parser.error("execution requires the fixed external data/fit/weighted/output roots")
    output = args.output.resolve()
    release(output)
    parent = output.parent
    if tuple(x.resolve() for x in (args.data_root, args.fit_root, args.weighted_root)) != tuple(
        parent / n for n in ("b3-v1-data", "b3-v1-fits", "b4-5-weighted-terminal")
    ):
        raise ValueError("fixed separate immutable external input roots required")
    save(output / "audit_receipts" / f"{args.cohort}_{args.stage}.started.json", {"attempts": 1})
    guard_inputs(parent, output, args.cohort + "_" + args.stage)
    repository, context = screening_preflight(Path.cwd(), args.data_root, args.fit_root)
    if not Path(__file__).resolve().is_relative_to(repository):
        raise ValueError("execution source must be inside its clean merged checkout")
    validate_external_output_root(repository, output)
    probe.upstream_fits(args.weighted_root)
    payload = {
        "version": EXECUTION_VERSION,
        "plan_sha256": execution_plan()["plan_sha256"],
        "source": context.source.model_dump(mode="json"),
        "fixed_fits_sha256": context.training_index_sha256,
        "data_sha256": context.training_index.context.data_index_sha256,
        "contract_sha256": CONTRACT_SHA,
        "scientific_contract_sha256": probe.CONTRACT_SHA256,
    }
    raw = canonical_metadata_bytes(payload)
    path = output / "context.json"
    if path.exists() and path.read_bytes() != raw:
        raise ValueError("existing reflection execution context changed")
    if not path.exists():
        save(path, payload)
    sha = digest(raw)
    if args.cohort == "fresh":
        require_sentinel(output)
    spec = DevelopmentSpec(
        EXECUTION_VERSION,
        probe.RECEIPT_VERSION,
        cohort_caps(args.cohort),
        probe.cases(args.cohort),
        probe.assignments(args.cohort),
        partial(probe.decision, cohort=args.cohort),
        probe.upstream_fits,
    )
    startup = perf_counter() - started
    if args.stage == "policy-audit":
        result = policy_audit(
            output, args.cohort, sha, spec, context, args.fit_root, args.weighted_root, startup
        )
    else:
        result = run_development(
            args.stage,
            output / args.cohort,
            args.data_root,
            args.fit_root,
            args.weighted_root,
            context,
            sha,
            startup,
            spec=spec,
            load_models=load_models,
            evaluate_query=partial(evaluator, output / args.cohort / "screen", sha),
            evaluate_weighted_query=evaluate_query,
        )
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
