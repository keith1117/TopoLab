"""Independently reconstruct B4.14 arithmetic from certified B4.13 compact rows."""

import argparse
import math
from pathlib import Path
from time import perf_counter

from b4_10_independent_audit import close
from b4_11_polish_diagnosis import canonical, peak_rss, read, sha
from b4_14_generalist_method_review import (
    DIAGNOSIS_SHA,
    check_inputs,
    execution_release,
    roots,
)


def reconstruct(diagnosis, report):
    """No B4.14 review, cost, margin or decision function is shared."""
    count = pairs = 0
    cohorts = {}
    for name, n, q, classifications, p in (
        ("sentinel", 9, 108, 179, 24),
        ("fresh", 48, 576, 922, 135),
    ):
        source = diagnosis["cohorts"][name]
        rows = source["rows"]
        assert source["cases"] == n and len(rows) == q
        assert source["terminal_classifications"] == classifications
        assert len({r["case_id"] for r in rows}) == n
        assert len({(r["case_id"], r["method"]) for r in rows}) == q
        assert sum(r["before"] is not None for r in rows) == p
        count += q
        pairs += p
        methods = diagnosis["plan"]["methods"]
        assert len(methods) == 12 and set(methods) == set(report["plan"]["methods"])
        for cid in {r["case_id"] for r in rows}:
            assert {r["method"] for r in rows if r["case_id"] == cid} == set(methods)
        for r in rows:
            assert r["seconds"] > 0 and r["uniform_seconds"] > 0
            assert 0 <= r["fallback_seconds"] < r["seconds"]
            assert all(
                math.isfinite(r[k]) for k in ("seconds", "uniform_seconds", "fallback_seconds")
            )
            assert (r["fallback"] is None) == r["candidate"]["succeeded"]
        primary = [r for r in rows if r["method"] == "P/17"]
        targets = [
            r
            for r in primary
            if r["scale"] == "large" and r["direction"] == "y" and r["route"] == "generalist"
        ]
        groups = {
            "all": primary,
            "small": [r for r in primary if r["scale"] == "small"],
            "large": [r for r in primary if r["scale"] == "large"],
            "large_y_generalist": targets,
        }
        scenarios, shadow = {}, {}
        for group_name, group in groups.items():
            scenarios[group_name] = {}
            uniform = math.fsum(r["uniform_seconds"] for r in group)
            denominator = math.fsum(1 / r["uniform_seconds"] for r in group)
            cap = 0.9 if group_name in ("small", "large") else 1.0
            for scenario in ("measured", "fallback_free", "failed_to_uniform"):
                times = []
                for row in group:
                    paid = row["seconds"]
                    if scenario == "fallback_free":
                        paid -= row["fallback_seconds"]
                    elif scenario == "failed_to_uniform" and not row["candidate"]["succeeded"]:
                        paid = row["uniform_seconds"]
                    times.append(paid)
                ratio_sum = math.fsum(
                    t / r["uniform_seconds"] for t, r in zip(times, group, strict=True)
                )
                average = ratio_sum / len(group)
                scenarios[group_name][scenario] = {
                    "cases": len(group),
                    "mean_paired_ratio": average,
                    "ratio_of_sums": math.fsum(times) / uniform,
                    "charged_seconds": math.fsum(times),
                    "uniform_seconds": uniform,
                    "observed_failures": sum(not r["candidate"]["succeeded"] for r in group),
                    "diagnostic_only": scenario != "measured",
                    "observed_statuses_preserved": True,
                    "mean_limit": cap,
                    "signed_constant_overhead_seconds": (cap * len(group) - ratio_sum)
                    / denominator,
                    "required_mean_ratio_reduction": max(0.0, average - cap),
                }
            shadow[group_name] = {
                "cases": len(group),
                "mean_ratio_floor": 1
                + math.fsum(
                    (r["seconds"] - r["fallback_seconds"]) / r["uniform_seconds"] for r in group
                )
                / len(group),
                "every_query_floor_above_uniform": all(
                    r["seconds"] > r["fallback_seconds"] for r in group
                ),
                "diagnostic_only": True,
            }
        slow = []
        for r in targets:
            if r["candidate"]["succeeded"] and r["seconds"] > r["uniform_seconds"]:
                uniform_row = [
                    u for u in rows if u["case_id"] == r["case_id"] and u["method"] == "uniform"
                ]
                assert len(uniform_row) == 1
                slow.append(
                    {
                        "case_id": r["case_id"],
                        "ratio": r["seconds"] / r["uniform_seconds"],
                        "performed_updates": r["performed_iterations"],
                        "uniform_updates": uniform_row[0]["performed_iterations"],
                    }
                )
        cohorts[name] = {
            "cases": n,
            "rows": q,
            "prior_terminal_classifications": classifications,
            "retained_strata": source["strata"],
            "scientific_decision": source["scientific_decision"],
            "failures": {
                m: sum(not r["candidate"]["succeeded"] for r in rows if r["method"] == m)
                for m in methods
            },
            "fixed_primary": {
                "scenarios": scenarios,
                "complete_uniform_shadow": shadow,
                "target_rows": targets,
                "slow_accepted_targets": slow,
            },
        }
    close(cohorts, report["cohorts"])
    failures = [
        r
        for r in diagnosis["cohorts"]["fresh"]["rows"]
        if r["method"] == "P/17" and not r["candidate"]["succeeded"]
    ]
    assert failures
    for r in failures:
        assert r["triggered"] and r["added_updates"] == 20
        assert r["candidate"]["converged"] and not r["before"]["succeeded"]
        assert r["candidate"]["quality_reasons"] == ["compliance_above_matched_uniform"]
        assert r["endpoint"]["compliance_ratio"] < r["before"]["compliance_ratio"]
    assert report["mechanism_dispositions"] == {
        "additional_fixed_continuation": "no_length_search_or_repair_evidence",
        "own_terminal_certificate_only": (
            "observed_own_certificates_do_not_establish_reference_quality"
        ),
        "perfect_failure_rejection": "optimistic_failure_rejection_leaves_accepted_refinement_cost",
        "complete_uniform_shadow": "full_uniform_plus_candidate_cannot_accelerate",
        "paid_uniform_energy_input": "prior_B2_19_failure_no_retest_without_new_mechanism",
        "offline_direct_compliance_objective": (
            "one_separately_registered_offline_adjoint_feasibility_probe"
        ),
    }
    assert report["next_slice"] == "B4.15 bounded offline compliance-adjoint feasibility probe"
    assert (
        not report["next_slice_started"]
        and not report["repaired_gate"]
        and not report["final_access"]
    )
    assert report["old_fresh_sealed"]
    assert report["claim"] == "method_review_only_not_repair_or_acceleration"
    assert report["prior_b4_13_charge_seconds_unchanged"] == 107.78
    return {
        "compact_rows": count,
        "prior_witness_pairs": pairs,
        "retained_strata": 96,
        "method_dispositions": 6,
        "next_slice": report["next_slice"],
    }


def main(argv=None):
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnosis-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    root, output = args.diagnosis_root.resolve(), args.output_root.resolve()
    roots(root, output)
    assert (root.name, output.name) == (
        "b4-13-preservation-diagnosis",
        "b4-14-generalist-method-review",
    )
    assert root.parent == output.parent
    target = output / "independent_audit.json"
    assert not target.exists(), "refuses to overwrite independent audit"
    revision = execution_release(output)
    check_inputs(root)
    diagnosis = read(root, "diagnosis.json", DIAGNOSIS_SHA)
    report = read(output, "review.json")
    assert report["source_revision"] == revision and report["input_sha256"] == DIAGNOSIS_SHA
    value = reconstruct(diagnosis, report)
    check_inputs(root)
    value.update(
        passed=True,
        source_revision=revision,
        review_sha256=sha(canonical(report)),
        source_sha256=sha(Path(__file__).read_bytes()),
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
    )
    assert value["charged_seconds"] <= 60 and value["peak_rss_bytes"] <= 1073741824
    with target.open("xb") as stream:
        stream.write(canonical(value))
    print(canonical(value).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
