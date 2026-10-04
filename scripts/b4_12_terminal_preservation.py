"""Metadata plan or explicit B4.12 sentinel/fresh execution with fixed inputs."""

import argparse
import json
from functools import partial
from pathlib import Path
from time import perf_counter
from typing import Any

from b4_8_rollback_confirmation import load_models as old_load_models

from topolab import b4_evidence as evidence
from topolab import b4_rollback_confirmation as previous
from topolab import b4_terminal_preservation as probe
from topolab.b3_artifacts import safe_path
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_queries import QueryOutcome, TerminalWitness, audit_witness, evaluate_query
from topolab.b3_screen_cli import screening_preflight
from topolab.b4_development import DevelopmentSpec, run_development
from topolab.b4_polish import polish, qualifies
from topolab.b4_telemetry import Journal, digest, durable_write
from topolab.b4_terminal_preservation import POLICY_VERSION, select_terminal
from topolab.b4_weighted_terminal import publish_blob, read_blob, read_units
from topolab.dataset_cli import validate_external_output_root


def original_packets(root: Path, cohort: str) -> dict[tuple[str, str], dict[str, Any]]:
    sha = digest(safe_path(root, "context.json").read_bytes())
    refs = read_units(root / "screen", sha, previous.units("screen"), caps=previous.CAPS)
    wanted = set(probe.assignments(cohort))
    return {
        (case, policy): evidence.read_packet(
            root / "screen", ref, sha, case, policy, previous.VERSION
        )
        for (case, policy), ref in zip(previous.assignments(), refs, strict=True)
        if (case, policy) in wanted
    }


def load_models(context, old, weighted):
    probe.upstream_fits(weighted)
    return old_load_models(context, old, weighted)


def recorded_refinement(root, sha, seed, case, before, checkpoint):
    witness = TerminalWitness.from_result(before)
    ref = publish_blob(root, "prepolish", canonical_metadata_bytes(witness.model_dump(mode="json")))
    after = polish(case, before, checkpoint)
    selection = select_terminal(case, before, after)
    chosen = before if selection == "original" else after
    endpoint = publish_blob(
        root,
        "endpoint",
        canonical_metadata_bytes(TerminalWitness.from_result(after).model_dump(mode="json")),
    )
    record = {
        "version": POLICY_VERSION,
        "endpoint": endpoint,
        "selection": selection,
        "selected_witness_sha256": digest(
            canonical_metadata_bytes(TerminalWitness.from_result(chosen).model_dump(mode="json"))
        ),
        "context_sha256": sha,
        "case_id": case.case_id,
        "seed": seed,
        "before": ref,
        "triggered": qualifies(case, before),
        "first_stop_iteration": len(before.history),
        "updates": len(after.history) - len(before.history),
        "after_witness_sha256": digest(
            canonical_metadata_bytes(TerminalWitness.from_result(after).model_dump(mode="json"))
        ),
    }
    path = safe_path(root, f"polish/{case.case_id}_{seed}.json")
    raw = canonical_metadata_bytes(record)
    if path.exists() and path.read_bytes() != raw:
        raise ValueError("retained polish witness changed on recovery")
    if not path.exists():
        durable_write(path, raw)
    return chosen


def evaluator(root, sha, case, method, seed, reference, models, neighbors, checkpoint):
    return evaluate_query(
        case,
        method,
        seed,
        reference,
        models,
        neighbors,
        checkpoint,
        refinement=partial(recorded_refinement, root, sha, seed),
    )


def require_sentinel(output: Path, sha: str) -> None:
    root = output / "sentinel"
    summary_raw = safe_path(root, "policy-audit/summary.json").read_bytes()
    summary = json.loads(summary_raw)
    audit_raw = safe_path(root, "independent_audit.json").read_bytes()
    audit = json.loads(audit_raw)
    if (
        summary_raw != canonical_metadata_bytes(summary)
        or audit_raw != canonical_metadata_bytes(audit)
        or summary["context_sha256"] != sha
        or not summary["passed"]
        or not summary["policy_integrity_passed"]
        or not audit["passed"]
        or not audit["gate_passed"]
        or audit["context_sha256"] != sha
        or audit["version"] != probe.VERSION
        or audit["cohort"] != "sentinel"
        or audit["decision"] != summary["decision"]
        or audit["source_sha256"]
        != digest(Path(__file__).with_name("b4_12_independent_audit.py").read_bytes())
        or audit["policy_summary_sha256"] != digest(summary_raw)
    ):
        raise ValueError(
            "fresh cohort remains sealed until the complete independent sentinel passes"
        )

    spec = DevelopmentSpec(
        probe.VERSION,
        probe.RECEIPT_VERSION,
        probe.CAPS,
        probe.sentinel_cases(),
        probe.assignments("sentinel"),
        lambda _: {},
        probe.upstream_fits,
    )
    for stage in ("reference", "screen", "audit", "policy-audit"):
        expected = (
            spec.units(stage)
            if stage != "policy-audit"
            else (
                *("reference:" + c for c in spec.units("reference")),
                *("policy:" + u for u in spec.units("screen")),
            )
        )
        read_units(root / stage, sha, expected, caps=probe.CAPS)


def reserve_fresh_budget(output: Path) -> None:
    from b4_10_resource_close import profile

    spent = 0.0
    for stage in (*probe.CAPS, "independent"):
        receipt = json.loads(
            (
                output
                / (
                    "sentinel/independent_audit.json"
                    if stage == "independent"
                    else f"sentinel/{stage}/progress.json"
                )
            ).read_bytes()
        )
        wall, rss = profile(output / "profiles" / f"sentinel_{stage}.time")
        extra = receipt["attempted"] if stage in ("reference", "screen") else 0
        charge = max(receipt["charged_seconds"], wall + extra + 10)
        cap = 1800 if stage == "independent" else probe.CAPS[stage][0]
        if charge > cap or rss > probe.plan()["whole_slice_rss_bytes"]:
            raise ValueError("sentinel whole-command resource cap failed")
        spent += charge
    reserved = sum(cap[0] for cap in probe.CAPS.values()) + 1800 + 180
    if spent + reserved > probe.plan()["whole_slice_cap_seconds"]:
        raise ValueError("remaining slice budget cannot reserve the frozen fresh stages")


def policy_audit(output, cohort, sha, spec, original, startup):
    root = output / cohort
    units = (
        *("reference:" + c for c in spec.units("reference")),
        *("policy:" + u for u in spec.units("screen")),
    )
    journal = Journal(
        root / "policy-audit", sha, units, *probe.CAPS["policy-audit"], opening_seconds=startup
    )
    by_id = {c.case_id: c for c in spec.cases}
    try:
        refs = {
            stage: read_units(root / stage, sha, spec.units(stage), caps=probe.CAPS)
            for stage in ("reference", "screen", "audit")
        }
        polished = {}
        if cohort == "sentinel":
            old_root = output.parent / "b4-10-post-plateau-polish/sentinel/screen"
            old_sha = digest(safe_path(old_root.parent.parent, "context.json").read_bytes())
            old_refs = read_units(old_root, old_sha, spec.units("screen"), caps=probe.CAPS)
            polished = {
                key: evidence.read_packet(
                    old_root, ref, old_sha, key[0], key[1], "topolab.b4_10.post-plateau-probe.v1"
                )
                for key, ref in zip(spec.assignments, old_refs, strict=True)
            }
        packets = {}
        for unit, ref in zip(spec.units("screen"), refs["screen"], strict=True):
            case, policy = unit.split(":")
            packets[(case, policy)] = evidence.read_packet(
                root / "screen", ref, sha, case, policy, probe.VERSION
            )
        for unit in units[journal.state.completed :]:
            journal.begin(unit)
            if unit.startswith("reference:"):
                case_id = unit.removeprefix("reference:")
                i = spec.units("reference").index(case_id)
                packet = evidence.read_packet(
                    root / "reference", refs["reference"][i], sha, case_id, "uniform", probe.VERSION
                )
                if cohort == "sentinel" and probe.identity(packet["outcome"]) != probe.identity(
                    original[(case_id, "uniform")]["outcome"]
                ):
                    raise ValueError("uniform reference numerical identity changed")
                result = {"reference_identity_checked": cohort == "sentinel"}
            else:
                case_id, policy = unit.removeprefix("policy:").split(":")
                packet = packets[(case_id, policy)]
                outcome = QueryOutcome.model_validate(packet["outcome"])
                case = by_id[case_id]
                result = {"unchanged_identity_checked": False, "prepolish_audited": False}
                if policy.startswith("P/") and outcome.route == "generalist":
                    assert outcome.attempt is not None and outcome.attempt.state is not None
                    seed = int(policy.split("/")[1])
                    raw = safe_path(root / "screen", f"polish/{case_id}_{seed}.json").read_bytes()
                    record = json.loads(raw)
                    before_raw = read_blob(root / "screen", record["before"], "prepolish")
                    before = TerminalWitness.model_validate_json(before_raw)
                    triggered = qualifies(case, before.result)
                    # The original terminal witness stores eleven states; its full
                    # scalar trace still gives the exact first-stop update count.
                    endpoint_raw = read_blob(root / "screen", record["endpoint"], "endpoint")
                    endpoint = TerminalWitness.model_validate_json(endpoint_raw)
                    selection = select_terminal(case, before.result, endpoint.result)
                    selected = before if selection == "original" else endpoint
                    n = len(before.trace)
                    expected_updates = (
                        min(20, case.problem.optimization.max_iterations - n) if triggered else 0
                    )
                    if (
                        raw != canonical_metadata_bytes(record)
                        or before_raw != canonical_metadata_bytes(before.model_dump(mode="json"))
                        or record["version"] != POLICY_VERSION
                        or record["context_sha256"] != sha
                        or record["case_id"] != case_id
                        or record["seed"] != seed
                        or record["triggered"] != triggered
                        or record["first_stop_iteration"] != n
                        or record["updates"] != expected_updates
                        or len(endpoint.trace) != n + expected_updates
                        or endpoint.trace[:n] != before.trace
                        or record["after_witness_sha256"]
                        != digest(canonical_metadata_bytes(endpoint.model_dump(mode="json")))
                        or endpoint_raw
                        != canonical_metadata_bytes(endpoint.model_dump(mode="json"))
                        or record["selection"] != selection
                        or selected != outcome.attempt.state
                        or record["selected_witness_sha256"]
                        != digest(canonical_metadata_bytes(selected.model_dump(mode="json")))
                        or not triggered
                        and before != endpoint
                    ):
                        raise ValueError(
                            "polish trigger, exact continuation or witness binding differs"
                        )
                    audit_witness(case, before, None, accepted=False)
                    audit_witness(case, endpoint, None, accepted=False)
                    if (
                        cohort == "sentinel"
                        and endpoint.model_dump(mode="json")
                        != polished[(case_id, policy)]["outcome"]["attempt"]["state"]
                    ):
                        raise ValueError("fixed polish endpoint differs from immutable B4.10")
                    if (
                        cohort == "sentinel"
                        and before.model_dump(mode="json")
                        != original[(case_id, policy)]["outcome"]["attempt"]["state"]
                    ):
                        raise ValueError("prepolish numerical identity differs from unchanged P")
                    result.update(
                        prepolish_audited=True,
                        endpoint_audited=True,
                        selection=selection,
                        triggered=triggered,
                        updates=expected_updates,
                    )
                    if not triggered and cohort == "sentinel":
                        if probe.identity(packet["outcome"]) != probe.identity(
                            original[(case_id, policy)]["outcome"]
                        ):
                            raise ValueError("untriggered candidate numerical identity changed")
                        result["unchanged_identity_checked"] = True
                elif cohort == "sentinel":
                    if probe.identity(packet["outcome"]) != probe.identity(
                        original[(case_id, policy)]["outcome"]
                    ):
                        raise ValueError("control numerical identity changed")
                    result["unchanged_identity_checked"] = True
            journal.publish(unit, result)
        decision = spec.gate(packets[key] for key in spec.assignments)
        journal.close()
        passed = decision["sentinel_gate_passed" if cohort == "sentinel" else "polish_gate_passed"]
        summary = {
            "version": probe.VERSION,
            "context_sha256": sha,
            "cohort": cohort,
            "decision": decision,
            "policy_integrity_passed": True,
            "passed": passed,
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
        print(json.dumps(probe.plan(), sort_keys=True))
        return
    if any(x is None for x in (args.data_root, args.fit_root, args.weighted_root, args.output)):
        parser.error("execution needs explicit immutable data/fit roots and external output")
    repository, context = screening_preflight(Path.cwd(), args.data_root, args.fit_root)
    if not Path(__file__).resolve().is_relative_to(repository):
        raise ValueError("polish execution must load its clean merged source")
    output = validate_external_output_root(repository, args.output)
    parent = args.data_root.resolve().parent
    if (
        output != parent / "b4-12-terminal-preservation"
        or args.weighted_root.resolve() != parent / "b4-5-weighted-terminal"
    ):
        raise ValueError("polish execution requires its fixed external siblings")
    probe.upstream_fits(args.weighted_root)
    payload = {
        "version": probe.VERSION,
        "plan_sha256": probe.plan()["plan_sha256"],
        "source": context.source.model_dump(mode="json"),
        "fixed_fits_sha256": context.training_index_sha256,
        "data_sha256": context.training_index.context.data_index_sha256,
        "protocol_sha256": digest(
            (repository / "docs/planning/b4_12_terminal_preservation_protocol.md").read_bytes()
        ),
    }
    raw = canonical_metadata_bytes(payload)
    output.mkdir(parents=True, exist_ok=True)
    path = safe_path(output, "context.json")
    if path.exists() and path.read_bytes() != raw:
        raise ValueError("polish source context changed")
    if not path.exists():
        durable_write(path, raw)
    sha = digest(raw)
    if args.cohort == "fresh":
        require_sentinel(output, sha)
        if args.stage == "reference" and not (output / "fresh/reference/progress.json").exists():
            reserve_fresh_budget(output)
    original = (
        original_packets(parent / "b4-8-rollback-confirmation", "sentinel")
        if args.cohort == "sentinel"
        else {}
    )
    gate = (
        partial(probe.sentinel_gate, original=original)
        if args.cohort == "sentinel"
        else probe.fresh_gate
    )
    spec = DevelopmentSpec(
        probe.VERSION,
        probe.RECEIPT_VERSION,
        probe.CAPS,
        probe.cases(args.cohort),
        probe.assignments(args.cohort),
        gate,
        probe.upstream_fits,
    )
    startup = perf_counter() - started
    if args.stage == "policy-audit":
        result = policy_audit(output, args.cohort, sha, spec, original, startup)
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
