"""Frozen read-only B4.12 two-witness preservation failure/cost diagnosis."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
from itertools import combinations
from pathlib import Path
from time import perf_counter

from b4_10_independent_audit import classify, close, qualifies
from b4_11_polish_diagnosis import (
    METHODS,
    canonical,
    costs,
    peak_rss,
    read,
    scientific_decision,
    sha,
    terminal,
)
from b4_12_independent_audit import classify_guard, fresh_decision, selection

VERSION = "topolab.b4_13.preservation-diagnosis.v1"
SOURCE_VERSION = "topolab.b4_12.terminal-preservation-probe.v1"
SOURCE_REVISION = "44cdb7e8b17692bc3b87300b383b478836d2fac8"
SOURCE_PLAN = "48171ac3beebf5abb19f59585bb6c387d4b72469e73a9fcaf749930b56bbae00"
BINDINGS = {
    "audit_receipts/plan.json": (
        "23e23ae9cebd5c36c0501f5c91f882299c1f107e0ec33c27ee73a43c758a756a"
    ),
    "context.json": ("9648919a924ce469df1cb5c9c970ceea91cff4714b7acfcaf0cbb69291a8da33"),
    "audit_receipts/production_release.json": (
        "27446ab4489284f9454349d40e2b28350f2cf22b4c5bd72488b3678a88e08bed"
    ),
    "audit_receipts/evidence_release.json": (
        "f5e9ec12fdb78a2921ee47876c5e10a2126db9a852ecb6b44f49c0d133f377b5"
    ),
    "audit_receipts/closure_recovery_release.json": (
        "125acceeda2918a28ea66031390c478552250ce4320243cbe724ecf7b181c91a"
    ),
    "audit_receipts/closure_profile_verification.json": (
        "c5f99d5228fc063152ac214919b0a624088ca2e61226f2c434347544732c80da"
    ),
    "resource_close.json": ("1e3422a85848be1b2ae964fdcf9cf0c456395ba78381e701fea801377bb9454e"),
    "audit_receipts/source_final_head_ci.json": (
        "e49d910eb6ae32962fb153919b3a07c8496517c7a1a430b4b0ed306e495e7c21"
    ),
    "audit_receipts/closure_repair_final_head_ci.json": (
        "381b5ad3cbc4e33ec21ca5311f512e2f869339ff95e2d175d54564acad1ab31a"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "d242fb9acf44df6f3eef74444e9d67b4e1ab194c51983195654ab76cd2540a3f"
    ),
    "audit_receipts/frozen_sources.json": (
        "e0519f61fb41821f6879176415b17851316d320c537dfcc892cec1eb99da91f6"
    ),
    "audit_receipts/execution_commands.json": (
        "14c349b4a60b64ea1ed47fb66cf49873b6d63d97e502ba88101e376b2500e71c"
    ),
    "sentinel/reference/progress.json": (
        "7d98c2195e28561bdf99e99f9373143bd0b0b0c78323104cee7db280889146a5"
    ),
    "sentinel/reference/summary.json": (
        "ef8a0d48c7e4681961e82d9249cd6085a2dd33305deb8c40b29bfd7239c1c530"
    ),
    "sentinel/screen/progress.json": (
        "47c9493011e2a786a168cb8a3ad7855125fb15dd8258e6df693ac7c9f711d4b0"
    ),
    "sentinel/screen/summary.json": (
        "0f35a459c378cd1f693e35eaf80be32f207295e28624366d710fd026d45f6ad6"
    ),
    "sentinel/audit/progress.json": (
        "b3ddb6f5595ea3d8c6acd6bd94dd6e77abc7974249c4537fe5bdaede82964a9c"
    ),
    "sentinel/audit/summary.json": (
        "ec855e1788d77dc2cb88f1554f853a4a0d9d689daff735db03021a98584e7b43"
    ),
    "sentinel/policy-audit/progress.json": (
        "04bb09b5ca80dea99646f9ca74cc1c8823808873536cab578537deac7f9708cc"
    ),
    "sentinel/policy-audit/summary.json": (
        "15a339700fb06cf966d72ac8fe79f23961d5bf1985f2bff693845fee22510eab"
    ),
    "sentinel/independent_audit.json": (
        "64c845239cffb6ab940dde2cc1edb444b63dc3791af1a1a82ae9db5444d7f77d"
    ),
    "fresh/reference/progress.json": (
        "f17781644b5cb85b4d271edc2110720143358c39b9652884354d54b8d52cd1a2"
    ),
    "fresh/reference/summary.json": (
        "ebc3a39245addbf582dfdff02a77789ecc4a30a660adcadc4e746341aab47b9e"
    ),
    "fresh/screen/progress.json": (
        "70350aaa82f72f1367ce22eb446defb33debd8a1cacf63cf414c1bf2faf8daf3"
    ),
    "fresh/screen/summary.json": (
        "e5fea2fa388aeced23988db9d6c018849d9ac924e10978bd3f1d38adcd3b1202"
    ),
    "fresh/audit/progress.json": (
        "c8cc799e6298360ede3bb11964f4376b38239b96139c55fbcfe97303ec515ef6"
    ),
    "fresh/audit/summary.json": (
        "45aa70484446eb486564309bb27e04f538940c74095e6a694a12bb79379bf7c5"
    ),
    "fresh/policy-audit/progress.json": (
        "621c5644e4a89adb83f59331cf5a70d33d7f76517a1b165142a4ec900e9e34fb"
    ),
    "fresh/policy-audit/summary.json": (
        "12828880fc9cbab12df2b8729d3e21e04f4ca08feef63e379c76acec2d477b74"
    ),
    "fresh/independent_audit.json": (
        "d4a53da311ad0aaad1dfb05155cc6802b388f8257dfdcc2476654bd35e5182d3"
    ),
}


def plan_payload():
    p = {
        "version": VERSION,
        "source_revision": SOURCE_REVISION,
        "source_plan_sha256": SOURCE_PLAN,
        "bindings": BINDINGS,
        "cohorts": {"sentinel": [9, 108, 179, 24, 12, 1], "fresh": [48, 576, 922, 135, 26, 0]},
        "methods": list(METHODS),
        "fixed_primary": 17,
        "analyses": [
            "both_terminal_certificates_and_quality",
            "paid_selected_and_performed_work",
            "all_method_scale_direction_strata",
            "same_specialist_timing_pairs",
            "fixed_primary_measured_fallback_free_failed_to_uniform",
        ],
        "bounds": ["measured", "fallback_free", "failed_to_uniform"],
        "decision_order": [
            "reject_changed_incomplete_or_unclosed_evidence",
            "generalist_reliability_refinement_method_review_for_converged_quality_gap",
            "terminal_certificate_and_cost_method_review_otherwise",
        ],
        "max_seconds": 360,
        "process_seconds": 120,
        "closure_seconds": 30,
        "max_rss_bytes": 1073741824,
        "close_allowance_per_process": 10,
        "solver_calls": 0,
        "label_model_byte_reads": 0,
        "final_artifact_reads": 0,
        "old_fresh_cases_sealed": 48,
        "length_or_threshold_search": False,
    }
    return {**p, "plan_sha256": sha(canonical(p))}


def check_inputs(root):
    bound = {p: read(root, p, d) for p, d in BINDINGS.items()}
    p, ctx, closed = (
        bound[k] for k in ("audit_receipts/plan.json", "context.json", "resource_close.json")
    )
    if (
        ctx["version"] != SOURCE_VERSION
        or ctx["plan_sha256"] != SOURCE_PLAN
        or ctx["source"]["source_revision"] != SOURCE_REVISION
        or p["plan_sha256"] != SOURCE_PLAN
        or sha(canonical({k: v for k, v in p.items() if k != "plan_sha256"})) != SOURCE_PLAN
        or p["fixed_primary"] != 17
        or p["final_access"]
        or not closed["closed"]
        or closed["preservation_gate_passed"]
        or closed["fresh_sealed"]
        or len(closed["protected_inputs"]) != 38
        or (root.parent / "b4-10-post-plateau-polish/fresh").exists()
    ):
        raise ValueError("requires complete failed fixed-primary evidence and old fresh seal")
    for path, digest in closed["protected_inputs"].items():
        safe_hash(root.parent, path, digest)
    recovery = bound["audit_receipts/closure_recovery_release.json"]
    for path, digest in recovery["protected_receipt_sha256"].items():
        safe_hash(root, path, digest)
    for path, digest in closed["profile_sha256"].items():
        safe_hash(root, "profiles/" + path, digest)
    verification = bound["audit_receipts/closure_profile_verification.json"]
    if not verification["passed"] or verification["numeric_retries"] != 0:
        raise ValueError("prior closure recovery is not independently closed")
    release = bound["audit_receipts/production_release.json"]
    if not (
        release["ci_before_merge"]
        and release["tree_identical_to_tested_head"]
        and release["clean_source"]
        and release["source_revision"] == SOURCE_REVISION
    ):
        raise ValueError("prior clean merged source release differs")
    evidence = bound["audit_receipts/evidence_release.json"]
    ci = bound["audit_receipts/evidence_final_head_ci.json"]
    if (
        not evidence["merged_tree_equals_tested_tree"]
        or evidence["gate_passed"]
        or evidence["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
    ):
        raise ValueError("prior evidence release differs")
    # The exact bound CI receipt retains all applicable success / intentional skip records.
    checks = ci["checks"]
    if len(checks) != 6 or any(
        c["status"] != "completed"
        or c["head_sha"] != evidence["tested_head"]
        or c["conclusion"] not in ("success", "skipped")
        or (c["conclusion"] == "skipped" and c["name"] != "clean-linux-smoke")
        for c in checks
    ):
        raise ValueError("prior exact-head CI differs")
    for cohort, (n, q, *_) in plan_payload()["cohorts"].items():
        if len(p["cases"][cohort]) != n or len(p["assignments"][cohort]) != q:
            raise ValueError("closed cohort population differs")
        policy = bound[f"{cohort}/policy-audit/summary.json"]
        audit = bound[f"{cohort}/independent_audit.json"]
        if (
            not policy["policy_integrity_passed"]
            or not audit["passed"]
            or policy["passed"] != (cohort == "sentinel")
            or audit["gate_passed"] != policy["passed"]
        ):
            raise ValueError("prior integrity or scientific Gate differs")
        for stage in ("screen", "audit"):
            close(policy["decision"], bound[f"{cohort}/{stage}/summary.json"]["decision"])
        close(policy["decision"], audit["decision"])
    return bound


def safe_hash(root, relative, expected):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("protected path escapes evidence root")
    if sha(path.read_bytes()) != expected:
        raise ValueError("protected input checksum differs: " + relative)


def chain(root, prefix, names, context):
    progress, summary = (read(root, f"{prefix}/{s}.json") for s in ("progress", "summary"))
    if (
        progress["context_sha256"] != context
        or progress["units_sha256"] != sha(canonical(names))
        or progress["attempted"] != len(names)
        or progress["completed"] != len(names)
        or progress["pending"] is not None
        or progress["active_at"] is not None
        or progress["integrity_failed"]
        or progress["resource_failed"]
        or any(
            progress[k] != summary[k]
            for k in ("attempted", "completed", "head_sha256", "charged_seconds", "peak_rss_bytes")
        )
    ):
        raise ValueError("closed assigned journal differs")
    head, items = "0" * 64, []
    for i, name in enumerate(names):
        item = read(root, f"{prefix}/units/{i:04d}.json")
        if (item["unit"], item["context_sha256"], item["previous_sha256"]) != (name, context, head):
            raise ValueError("journal assignment or chain differs")
        head = sha(canonical(item))
        items.append(item["payload"])
    if head != progress["head_sha256"]:
        raise ValueError("journal head differs")
    return items


def blob(root, prefix, ref, kind):
    if ref["path"] != f"artifacts/{kind}/{ref['sha256']}.json":
        raise ValueError("content-addressed path differs")
    value = read(root, prefix + "/" + ref["path"], ref["sha256"])
    if len(canonical(value)) != ref["byte_size"]:
        raise ValueError("content-addressed size differs")
    return value


def recording(root, prefix, index, ref, context):
    r = read(root, f"{prefix}/recording/{index:04d}.json")
    if (
        r["outcome_sha256"] != ref["sha256"]
        or r["context_sha256"] != context
        or r["version"] != "topolab.b4_12.recording.v1"
        or not 0 <= r["recording_seconds_before_receipt"] <= 1
    ):
        raise ValueError("complete recording receipt differs")
    return r["recording_seconds_before_receipt"]


def timing(packet):
    o, t, cb = packet["outcome"], packet["timing"], packet["callback"]
    phases = [o["attempt"]["timing"]]
    if o["fallback"] is not None:
        phases.append(o["fallback"]["timing"])
    if (
        packet["recording_allowance_seconds"] != 1
        or t["wall_seconds"] <= 0
        or not all(math.isfinite(v) and v >= 0 for v in t.values())
        or not all(math.isfinite(v) and v >= 0 for p in phases for v in p.values())
        or not math.isfinite(o["route_seconds"])
        or o["route_seconds"] < 0
        or t["legacy_phase_seconds"] > t["wall_seconds"]
        or not math.isclose(
            t["legacy_phase_seconds"],
            o["route_seconds"] + sum(sum(p.values()) for p in phases),
            rel_tol=1e-14,
        )
        or not all(math.isfinite(v) and v >= 0 for v in cb.values())
        or cb["wall_seconds"] > t["wall_seconds"]
    ):
        raise ValueError("complete charged timing differs")


def advice(rows):
    failed = [r for r in rows if r["method"] == "P/17" and not r["candidate"]["succeeded"]]
    if failed and all(
        r["triggered"]
        and r["selection"] == "endpoint"
        and r["added_updates"] == 20
        and r["candidate"]["converged"]
        and r["candidate"]["quality_reasons"] == ["compliance_above_matched_uniform"]
        and not r["before"]["succeeded"]
        and r["endpoint"]["compliance_ratio"] < r["before"]["compliance_ratio"]
        for r in failed
    ):
        return "generalist_reliability_refinement_method_review"
    return "terminal_certificate_and_cost_method_review"


def summarize(rows):
    strata = []
    for method in METHODS:
        for scale in ("small", "large"):
            for direction in ("y", "z"):
                group = [
                    r
                    for r in rows
                    if (r["method"], r["scale"], r["direction"]) == (method, scale, direction)
                ]
                strata.append(
                    {
                        "method": method,
                        "scale": scale,
                        "direction": direction,
                        **costs(group, "measured"),
                        "selected_updates": sum(r["candidate"]["iterations"] for r in group),
                        "performed_updates": sum(r["performed_iterations"] for r in group),
                        "fallback_seconds": sum(r["fallback_seconds"] for r in group),
                    }
                )
    primary = [r for r in rows if r["method"] == "P/17"]
    groups = {
        "all": primary,
        **{s: [r for r in primary if r["scale"] == s] for s in ("small", "large")},
        "large_y_generalist": [
            r
            for r in primary
            if r["scale"] == "large" and r["direction"] == "y" and r["route"] == "generalist"
        ],
    }
    return {
        "strata": strata,
        "fixed_primary_cost_scenarios": {
            name: {s: costs(group, s) for s in plan_payload()["bounds"]}
            for name, group in groups.items()
        },
        "timing_totals": {
            k: math.fsum(r["timing"][k] for r in rows)
            for k in ("wall_seconds", "cpu_seconds", "legacy_phase_seconds")
        },
        "callback_totals": {
            k: math.fsum(r["callback"][k] for r in rows)
            for k in ("wall_seconds", "cpu_seconds", "bytes_written")
        },
    }


def cohort_report(root, cohort, bound, started):
    p = bound["audit_receipts/plan.json"]
    context = BINDINGS["context.json"]
    cases = {c["case_id"]: c for c in p["cases"][cohort]}
    assignments = p["assignments"][cohort]
    names = [c + ":" + m for c, m in assignments]
    refs = chain(root, cohort + "/reference", list(cases), context)
    screens = chain(root, cohort + "/screen", names, context)
    audits = chain(
        root,
        cohort + "/audit",
        [
            "inputs",
            "nn_labels",
            *("reference:" + c for c in cases),
            *("screen:" + n for n in names),
        ],
        context,
    )
    chain(
        root,
        cohort + "/policy-audit",
        [*("reference:" + c for c in cases), *("policy:" + n for n in names)],
        context,
    )
    if audits[0]["audited_checkpoints"] != 12 or audits[1]["audited_nn_labels"] != 528:
        raise ValueError("prior complete input audit differs")
    rows, references, pairs = [], [], []
    selected_count = guard_count = continuations = preserved = 0
    # At most one twelve-method case retains full density state in memory.
    for i, (cid, case) in enumerate(cases.items()):
        if perf_counter() - started + 10 > 120 or peak_rss() > 1073741824:
            raise RuntimeError("diagnostic resource cap exceeded")
        problem = case["problem"]
        nx = problem["mesh"]["element_counts"][0]
        volume = problem["optimization"]["volume_fraction"]
        direction = problem["loads"][0]["direction"]
        prefix = cohort + "/reference"
        packet = blob(root, prefix, refs[i], "outcome")
        if (packet["case_id"], packet["policy"], packet["context_sha256"], packet["version"]) != (
            cid,
            "uniform",
            context,
            SOURCE_VERSION,
        ):
            raise ValueError("reference assignment differs")
        ref = packet["outcome"]["attempt"]["metrics"]["final_compliance"]
        c = terminal(packet["outcome"]["attempt"]["state"], ref, volume)
        classify(case, packet["outcome"]["attempt"], ref)
        if not c["succeeded"]:
            raise ValueError("mandatory reference failed")
        recording(root, prefix, i, refs[i], context)
        references.append({"case_id": cid, **c})
        selected_count += 1
        panel = {}
        uniform = None
        for j in range(i * 12, (i + 1) * 12):
            assigned, method = assignments[j]
            prefix = cohort + "/screen"
            packet = blob(root, prefix, screens[j], "outcome")
            o = packet["outcome"]
            if (
                assigned,
                packet["case_id"],
                packet["policy"],
                packet["context_sha256"],
                packet["version"],
            ) != (cid, cid, method, context, SOURCE_VERSION):
                raise ValueError("query assignment differs")
            arm, _, seed = method.partition("/")
            route = (
                "baseline"
                if not seed
                else "specialist"
                if nx == 24 and direction == "y" and volume >= 0.55
                else "generalist"
            )
            if (o["method"], o["seed"], o["route"]) != (
                "P" if arm == "W" else arm,
                int(seed) if seed else None,
                route,
            ):
                raise ValueError("method seed or route differs")
            timing(packet)
            recorded = recording(root, prefix, j, screens[j], context)
            paid = packet["timing"]["wall_seconds"] + 1
            if method == "uniform":
                uniform = paid
            if uniform is None:
                raise ValueError("uniform must precede all candidates")
            before = endpoint = None
            trigger = False
            updates = 0
            choice = "endpoint"
            if arm == "P" and route == "generalist":
                record = read(root, f"{prefix}/polish/{cid}_{seed}.json")
                original = blob(root, prefix, record["before"], "prepolish")
                ending = blob(root, prefix, record["endpoint"], "endpoint")
                before = terminal(original, ref, volume)
                trigger = qualifies(case, original)
                updates = min(20, 360 - before["iterations"]) if trigger else 0
                endpoint = terminal(ending, ref, volume, trigger)
                choice = selection(case, original, ending)
                chosen = original if choice == "original" else ending
                if (
                    record["case_id"],
                    record["seed"],
                    record["context_sha256"],
                    record["version"],
                    record["triggered"],
                    record["updates"],
                    record["first_stop_iteration"],
                    record["selection"],
                ) != (
                    cid,
                    int(seed),
                    context,
                    p["preservation_version"],
                    trigger,
                    updates,
                    before["iterations"],
                    choice,
                ):
                    raise ValueError("two-witness choice identity differs")
                if (
                    ending["trace"][: before["iterations"]] != original["trace"]
                    or len(ending["trace"]) != before["iterations"] + updates
                    or sha(canonical(ending)) != record["after_witness_sha256"]
                    or sha(canonical(chosen)) != record["selected_witness_sha256"]
                    or chosen != o["attempt"]["state"]
                    or (not trigger and original != ending)
                ):
                    raise ValueError("paid continuation or retained witness differs")
                classify_guard(case, original, ref)
                classify_guard(case, ending, ref)
                guard_count += 2
                continuations += trigger
                preserved += choice == "original"
            candidate = terminal(
                o["attempt"]["state"], ref, volume, trigger and choice == "endpoint"
            )
            fallback = (
                None if o["fallback"] is None else terminal(o["fallback"]["state"], ref, volume)
            )
            for a in (o["attempt"], o["fallback"]):
                if a is not None:
                    selected_count += classify(case, a, ref)
            if (fallback is not None) != (method != "uniform" and not candidate["succeeded"]):
                raise ValueError("paid fallback status differs")
            if (
                method == "uniform"
                and (not candidate["succeeded"] or abs(candidate["compliance_ratio"] - 1) > 1e-9)
            ) or (
                fallback is not None
                and (not fallback["succeeded"] or abs(fallback["compliance_ratio"] - 1) > 1e-9)
            ):
                raise ValueError("uniform or fallback differs from reference")
            row = {
                "case_id": cid,
                "method": method,
                "scale": "small" if nx == 12 else "large",
                "direction": direction,
                "volume": volume,
                "load_node": problem["loads"][0]["node"],
                "route": route,
                "seconds": paid,
                "uniform_seconds": uniform,
                "fallback_seconds": 0
                if fallback is None
                else sum(o["fallback"]["timing"].values()),
                "candidate": candidate,
                "fallback": fallback,
                "before": before,
                "endpoint": endpoint,
                "triggered": trigger,
                "added_updates": updates,
                "selection": choice,
                "performed_iterations": candidate["iterations"]
                if endpoint is None
                else endpoint["iterations"],
                "timing": packet["timing"],
                "callback": packet["callback"],
                "route_seconds": o["route_seconds"],
                "attempt_phases": o["attempt"]["timing"],
                "fallback_phases": None if fallback is None else o["fallback"]["timing"],
                "recording_seconds": recorded,
            }
            rows.append(row)
            panel[method] = packet
        if nx == 24 and direction == "y" and volume >= 0.55:
            for seed in (17, 29, 43):
                for a, b in combinations(("C", "P", "W"), 2):
                    left, right = (panel[f"{m}/{seed}"]["outcome"]["attempt"] for m in (a, b))
                    if any(
                        left[k] != right[k]
                        for k in ("state", "metrics", "succeeded", "failure_code")
                    ):
                        raise ValueError("same specialist identity differs")
                    paid = {
                        f"{m}/{seed}": panel[f"{m}/{seed}"]["timing"]["wall_seconds"] + 1
                        for m in (a, b)
                    }
                    spread = max(paid.values()) / min(paid.values())
                    pairs.append(
                        {
                            "case_id": cid,
                            "left": f"{a}/{seed}",
                            "right": f"{b}/{seed}",
                            "charged_seconds": paid,
                            "spread": spread,
                            "flagged": spread >= 1.25,
                        }
                    )
    expected = plan_payload()["cohorts"][cohort]
    if [
        len(cases),
        len(rows),
        selected_count + guard_count,
        guard_count // 2,
        continuations,
        preserved,
    ] != expected:
        raise ValueError("complete two-witness population differs")
    if sum(a["audited_attempts"] for a in audits[2:]) != selected_count:
        raise ValueError("prior terminal audit population differs")
    # The prior independent Gate arithmetic remains unchanged and hash-bound.
    retained = bound[f"{cohort}/independent_audit.json"]["decision"]
    table = summarize(rows)
    if cohort == "fresh":
        compact = [
            {
                "case_id": r["case_id"],
                "policy": r["method"],
                "timing": r["timing"],
                "outcome": {
                    "attempt": {"succeeded": r["candidate"]["succeeded"]},
                    "fallback": r["fallback"],
                    "route": r["route"],
                },
            }
            for r in rows
        ]
        close(fresh_decision(compact, cases), retained)
    else:
        close(scientific_decision(rows), retained)
        primary = table["fixed_primary_cost_scenarios"]["large_y_generalist"]["measured"]
        close(primary["mean_paired_ratio"], retained["large_y_primary_mean"])
        close(primary["ratio_of_sums"], retained["large_y_primary_total_ratio"])
        if any(not r["candidate"]["succeeded"] for r in rows if r["method"] == "P/17"):
            raise ValueError("closed sentinel primary success differs")
    return {
        "cases": len(cases),
        "outcomes": len(rows),
        "terminal_classifications": selected_count + guard_count,
        "selected_terminal_classifications": selected_count,
        "guard_witness_classifications": guard_count,
        "continuations": continuations,
        "added_updates": sum(r["added_updates"] for r in rows),
        "preserved_originals": preserved,
        "references": references,
        "rows": rows,
        "shared_specialist_pairs": pairs,
        "scientific_decision": retained,
        **table,
    }


def diagnose(root):
    started = perf_counter()
    bound = check_inputs(root)
    reports = {c: cohort_report(root, c, bound, started) for c in ("sentinel", "fresh")}
    check_inputs(root)
    return {
        "plan": plan_payload(),
        "cohorts": reports,
        "next_mechanism": advice(reports["fresh"]["rows"]),
        "prior_charge_seconds": bound["resource_close.json"]["charged_seconds"],
        "old_fresh_sealed": True,
        "final_access": False,
        "repaired_gate": False,
        "claim": "read_only_diagnosis_not_a_repaired_gate",
    }


def main(argv=None):
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    root, output = args.screen_root.resolve(), args.output_root.resolve()
    repository = Path(__file__).resolve().parents[1]
    if root.is_relative_to(repository) or output.is_relative_to(repository):
        raise ValueError("evidence roots must be outside repository")
    if root.is_relative_to(output) or output.is_relative_to(root):
        raise ValueError("output must be separate from immutable input")
    if not args.execute:
        print(json.dumps(plan_payload(), sort_keys=True))
        return 0
    if (
        root.name != "b4-12-terminal-preservation"
        or output.name != "b4-13-preservation-diagnosis"
        or root.parent != output.parent
    ):
        raise ValueError("execution requires fixed sibling evidence roots")
    if (output / "diagnosis.json").exists():
        raise ValueError("refuses to overwrite diagnosis")
    if any(
        subprocess.run(c, cwd=repository, check=False).returncode
        for c in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"])
    ):
        raise ValueError("requires clean committed source")
    if any(
        os.environ.get(k) != "1"
        for k in (
            "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
        )
    ):
        raise ValueError("requires one BLAS/OpenMP thread")
    release = read(output, "audit_receipts/production_release.json")
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    if (
        release["source_revision"] != revision
        or not release["all_applicable_ci_passed_before_merge"]
    ):
        raise ValueError("requires CI-passed merged source release")
    for path, digest in release["source_sha256"].items():
        safe_hash(repository, path, digest)
    report = diagnose(root)
    report.update(
        diagnostic_source_revision=revision,
        source_sha256=sha(Path(__file__).read_bytes()),
        protocol_sha256=sha(
            (repository / "docs/planning/b4_13_preservation_diagnosis_protocol.md").read_bytes()
        ),
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
    )
    if report["charged_seconds"] > 120 or report["peak_rss_bytes"] > 1073741824:
        raise RuntimeError("complete diagnostic resource cap exceeded")
    (output / "diagnosis.json").write_bytes(canonical(report))
    print(
        json.dumps(
            {
                k: report[k]
                for k in ("next_mechanism", "charged_seconds", "peak_rss_bytes", "claim")
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
