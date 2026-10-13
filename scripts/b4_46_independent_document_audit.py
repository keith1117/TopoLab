"""Independent B4.46 documentary audit; no primary code/receipt or candidate imports."""

import ast
import hashlib
import json
import os
import sys
import traceback
from collections import Counter
from decimal import Decimal, localcontext
from pathlib import Path

FIELDS = frozenset(
    "version authority starting_main slice_limit scope source_inputs_at_starting_main_sha256 "
    "primary_only_source_text_sha256 external_text_metadata_sha256 role_access document_audits "
    "b4_45_retained public_evidence_retained b4_44_retained limitations "
    "fresh_arithmetic_prerequisites "
    "real_prerequisites stops boundaries future_criteria_unchanged preserved_failures "
    "preserved_cost "
    "full_training_memory new_production_budget_or_reserve "
    "real_values_and_new_arithmetic_evaluated "
    "allowed_publish_paths software_failure_policy software_cost_policy next_proposed "
    "next_authorized next_started".split()
)
TABLES = {
    "limitations": (18, "L", "id text scope"),
    "fresh_arithmetic_prerequisites": (20, "A", "id name text status"),
    "real_prerequisites": (24, "O", "id name text status"),
    "stops": (20, "S", "id trigger disposition alternative_or_retry"),
}
REQUIREMENTS = (
    ("new-authority", "fresh destinations", "quota reset"),
    ("finite-panel", "authored public", "BEFORE"),
    ("release-source", "clean locked merged", "launcher/controller/oracle"),
    ("actual-bootstrap", "ACTUAL", "candidate and dependencies"),
    ("preimport-parent", "pending BEFORE", "consumes"),
    ("immutable-inputs", "exact request/source/fixture", "races"),
    ("closed-schema", "before protected bytes", "finite path"),
    ("durable-case-journal", "BEFORE each", "attempted/completed/pending"),
    ("through-exit-terminal", "observed process exit", "absent results"),
    ("negative-launch-controls", "wrong interpreter", "arithmetic acceptance"),
    ("fixed-program", "ascending +0", "no FMA"),
    ("independent-origin", "before calls", "rounding helpers"),
    ("full-RN-proof", "squared-midpoint", "unit tests alone"),
    ("separate-errors", "symmetry defects", "EVERY outward"),
    ("complete-case-audit", "ALL cases", "incomplete output"),
    ("once-no-retry", "before-loop", "separate owner decision"),
    ("paid-resource-proof", "first/failure-inclusive", "no production budget"),
    ("immutable-history", "fresh evidence", "retrospective acceptance"),
    ("real-boundary", "diagnostic only", "P17"),
    ("publication-stop", "ALL upload", "independent backup"),
)


def decode(text):
    def pairs(items):
        keys = [key for key, _ in items]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate JSON keys")
        return dict(items)

    def forbidden(token):
        raise ValueError("nonfinite constant " + token)

    parsed = json.loads(text, object_pairs_hook=pairs, parse_constant=forbidden)
    if not isinstance(parsed, dict):
        raise ValueError("object required")
    return parsed


def contract_schema(doc):
    if not isinstance(doc, dict) or frozenset(doc) != FIELDS:
        raise ValueError("registered root fields required")
    if type(doc["slice_limit"]) is not int or doc["slice_limit"] != 1:
        raise ValueError("slice type/count")
    for key in ("next_authorized", "next_started", "real_values_and_new_arithmetic_evaluated"):
        if doc[key] is not False:
            raise ValueError("unauthorized next action")
    for key, (number, letter, words) in TABLES.items():
        rows = doc[key]
        if type(rows) is not list or len(rows) != number:
            raise ValueError("table count")
        if [row.get("id") for row in rows] != [f"{letter}{i:02}" for i in range(1, number + 1)]:
            raise ValueError("table IDs/order")
        for row in rows:
            if type(row) is not dict or set(row) != set(words.split()):
                raise ValueError("table fields")
            for key0, val in row.items():
                if key0 == "alternative_or_retry":
                    if val is not False:
                        raise ValueError("retry refused")
                elif type(val) is not str:
                    raise ValueError("text field required")


def emit(path, record):
    with path.open("x") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def main():
    root, contract_file, protocol_file, output_file = (Path(arg) for arg in sys.argv[1:])
    findings, accessed, input_bytes, failure = [], [], 0, None

    def accept(label, condition):
        findings.append({"id": label, "passed": condition is True})
        if len(findings) > 900 or condition is not True:
            raise ValueError("independent failed predicate: " + label)

    def text_of(path):
        nonlocal input_bytes
        if path.is_symlink() or path.absolute() != path.resolve():
            raise ValueError("redirected file refused")
        with path.open("rb") as stream:
            value = stream.read(1048577)
        input_bytes += len(value)
        if len(value) > 1048576 or input_bytes > 8388608:
            raise ValueError("registered byte cap")
        accessed.append(str(path))
        return value

    def sha(value):
        return hashlib.sha256(value).hexdigest()

    emit(
        output_file.with_suffix(".pending.json"),
        {"role": "independent", "phase": "BEFORE_TEXT_INPUTS"},
    )
    try:
        frozen = decode(text_of(root / "reviewer_program_freeze.json"))
        raw_contract, raw_protocol = text_of(contract_file), text_of(protocol_file)
        accept("new-contract-frozen", sha(raw_contract) == frozen["contract_sha256"])
        accept("new-protocol-frozen", sha(raw_protocol) == frozen["protocol_sha256"])
        own_bytes = text_of(Path(__file__))
        accept(
            "own-program-frozen", sha(own_bytes) == frozen["program_sha256"][Path(__file__).name]
        )
        d = decode(raw_contract)
        contract_schema(d)
        accept("closed-text-contract", True)
        corpus = {}
        for kind, mapping in (
            ("common", d["source_inputs_at_starting_main_sha256"]),
            ("metadata", d["external_text_metadata_sha256"]),
        ):
            for identity, hash_value in sorted(mapping.items()):
                if Path(identity).is_absolute() or ".." in Path(identity).parts:
                    raise ValueError("absolute or parent path refused")
                contents = text_of(root / "bound_text" / kind / identity)
                accept("identity-" + identity, sha(contents) == hash_value)
                corpus[identity] = contents
        accept("exact-independent-input-population", len(corpus) == 32)
        accept(
            "no-primary-only-text-access", not any("/bound_text/primary/" in p for p in accessed)
        )
        previous = decode(
            corpus["docs/planning/b4_45_public_launch_context_immutable_receipts_contract.json"]
        )
        for section in (
            "future_criteria_unchanged",
            "preserved_failures",
            "preserved_cost",
            "full_training_memory",
            "boundaries",
            "public_evidence_retained",
            "b4_44_retained",
            "real_prerequisites",
        ):

            def encoded(obj):
                return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)

            accept(
                "retained-complete-" + section, encoded(d[section]) == encoded(previous[section])
            )
        for key in sorted(previous["boundaries"]):
            accept(
                "retained-boundary-" + key,
                d["boundaries"][key] == previous["boundaries"][key]
                and type(d["boundaries"][key]) is type(previous["boundaries"][key]),
            )
        limitation_terms = (
            "no numerical candidate",
            "NEVER execute",
            "concurrency",
            "entire working tree",
            "not a general",
            "four-hash",
            "FAIL controls",
            "authenticated provenance",
            "multi-writer",
            "bootstrap",
            "UNKNOWN_NOT_WRITTEN",
            "UNKNOWN_NOT_DIAGNOSED",
            "all10",
            "94 regression",
            "no scientific repair",
            "administrative10",
            "PENDING/4GiB",
            "UNFROZEN",
        )
        for row, term in zip(d["limitations"], limitation_terms, strict=True):
            accept(row["id"] + "-independent-limit", term in row["text"])
            accept(
                row["id"] + "-limited-scope",
                row["scope"] == "PUBLIC_OR_STATIC_ONLY_NO_NEW_EXECUTION",
            )
        for row, (name, word1, word2) in zip(
            d["fresh_arithmetic_prerequisites"], REQUIREMENTS, strict=True
        ):
            accept(row["id"] + "-named-requirement", row["name"] == name)
            accept(row["id"] + "-premises", word1 in row["text"] and word2 in row["text"])
            accept(
                row["id"] + "-unexecuted",
                row["status"]
                == "TEXT_ONLY_FRESH_PUBLIC_CAMPAIGN_PREREQUISITE; NOT_AUTHORIZED_NOT_STARTED",
            )
        for row in d["real_prerequisites"]:
            accept(
                row["id"] + "-still-real-obligation",
                row["status"] == "TEXT_ONLY_OBLIGATION; UNKNOWN_STOP; UNIMPLEMENTED_UNEVALUATED",
            )
        for row in d["stops"]:
            accept(
                row["id"] + "-mandatory-stop",
                bool(row["trigger"])
                and row["disposition"]
                == "STOP_PRESERVE_FAILURE_AND_UNKNOWN; NO_ALTERNATIVE_OR_RETRY"
                and row["alternative_or_retry"] is False,
            )
        metadata = {
            Path(path).name: decode(contents)
            for path, contents in corpus.items()
            if path.startswith("b4-45-software-validation/")
        }
        closed, verified = (
            metadata["closed_main_release.json"],
            metadata["final_recovery_verification.json"],
        )
        formal = metadata["closed_formal_public_resource.json"]
        cost_meta, ci_meta = (
            metadata["closed_software_resource_metadata.json"],
            metadata["closed_ci_wall_metadata.json"],
        )
        for name, val in metadata.items():
            accept("old-metadata-success-" + name, val["passed"] is True)
        accept(
            "same-main-at-closure",
            closed["main"] == verified["main"] == d["starting_main"]
            and closed["slice_closed"] is True
            and verified["all_original_copy_streamed_sha256_verified"] is True,
        )
        accept(
            "no-original-arithmetic-acceptance",
            closed["prior_b4_43_case_audits"] == closed["prior_b4_43_RN_proofs"] == 0
            and closed["prior_b4_43_quota"] == [1, 1]
            and closed["prior_b4_43_receipt"] == "NOT_WRITTEN",
        )
        accept(
            "old-runtime-and-cause-still-unknown",
            closed["prior_b4_43_runtime"] == "UNKNOWN_NOT_RECORDED"
            and closed["prior_b4_43_cause"] == "UNKNOWN_NOT_DIAGNOSED",
        )
        launch = d["b4_45_retained"]
        accept(
            "launch-formal-once",
            closed["formal_calls"]
            == formal["formal_invocations"]
            == launch["formal_calls"]
            == [1, 1]
            and closed["formal_retry"] is formal["formal_retry"] is launch["formal_retry"] is False,
        )
        accept(
            "public-software-counts",
            closed["cases"] == formal["public_cases"] == launch["cases"] == 12
            and closed["independent_predicates"] == launch["independent_predicates"] == 277
            and closed["focused_tests"] == launch["focused_tests"] == 32,
        )
        fixture = decode(corpus["tests/fixtures/b4_45_launch_preflight.json"])
        accept(
            "four-original-inert-sources",
            len(fixture["source_texts"]) == launch["public_sources"] == 4,
        )
        for name, contents in fixture["source_texts"].items():
            accept(
                "inert-text-sha-" + name, sha(contents.encode()) == fixture["source_sha256"][name]
            )
        status_counts = dict(Counter(case["expected_status"] for case in fixture["cases"]))
        accept(
            "all-original-launch-dispositions",
            status_counts == formal["dispositions"]
            and fixture["cases"] == previous["public_cases"],
        )
        accept(
            "launch-negative-status-split",
            status_counts.get("PASS_PUBLIC_PREFLIGHT") == launch["launch_successes"] == 1
            and sum(v for k, v in status_counts.items() if k.startswith("STOP_"))
            == launch["prescribed_stops"]
            == 8
            and sum(v for k, v in status_counts.items() if k.startswith("FAIL_"))
            == launch["failure_controls"]
            == 2
            and status_counts.get("REFUSED_EXISTING_OUTPUT")
            == launch["existing_output_refusals"]
            == 1,
        )
        accept(
            "no-eager-import-or-new-campaign",
            launch["actual_topolab_imported"] is launch["new_arithmetic_campaign"] is False
            and launch["missing_completion"] == "UNKNOWN_NOT_WRITTEN"
            and launch["runtime_scope"] == "B4.45_NEW_OBSERVATIONS_ONLY",
        )
        accept(
            "full-old-failure-counts",
            len(cost_meta["native_failures"])
            == closed["native_failures"]
            == launch["closed_native_failures"]
            == 3
            and len(cost_meta["sandbox_failures"])
            == closed["sandbox_coordination_failures"]
            == launch["closed_sandbox_failures"]
            == 2
            and len(cost_meta["administrative_failures"])
            == closed["administrative_failures"]
            == launch["closed_administrative_failures"]
            == 10
            and launch["premerge_report_administrative_failures"] == 5,
        )
        accept(
            "old-cost-unknowns-not-zero",
            cost_meta["complete_all_software_cost"]
            == launch["complete_software_cost"]
            == "UNKNOWN_NOT_ZERO"
            and cost_meta["whole_chain_peak"] == "UNKNOWN_NOT_ZERO"
            and cost_meta["software_RSS_fills_historical_gap"] is False,
        )
        accept(
            "old-CI-unknown-span-retained",
            ci_meta["unknown_job_wall_count"] == 1
            and ci_meta["known_separate_job_wall_sum_seconds"] == "3442.0"
            and ci_meta["complete_whole_CI_controller_elapsed_CPU_RSS"] == "UNKNOWN_NOT_ZERO",
        )
        a = d["document_audits"]
        accept(
            "finite-document-quota",
            a["primary_invocations"] == a["independent_invocations"] == 1
            and a["formal_retry"] is False,
        )
        accept(
            "software-caps-only",
            a["each_formal_native_wall_seconds_max"] == 60
            and a["each_formal_native_rss_bytes_max"] == 268435456
            and a["decimal_precision"] == 50
            and a["software_bookkeeping_caps_only_not_paid_production_grant"] is True,
        )
        accept(
            "new-arithmetic-unauthorized",
            d["scope"] == "BOUNDED_READ_ONLY_TEXT_AND_LITERAL_COMPACT_METADATA_ONLY"
            and d["new_production_budget_or_reserve"] == "NONE_TEXT_ONLY"
            and not d["next_started"]
            and not d["next_authorized"],
        )
        with localcontext() as context:
            context.prec = 50
            c = d["preserved_cost"]
            total = Decimal(0)
            for name in sorted(c["known_actual_stage_components_seconds"]):
                total += Decimal(c["known_actual_stage_components_seconds"][name])
            accept(
                "known-paid-retained-and-failed",
                total == Decimal("12721.16417100014444982") > Decimal("7200")
                and total == Decimal(c["cross_route_known_paid_floor_seconds"]),
            )
            accept(
                "Q31-added-once",
                Decimal(c["b4_31_campaign_plus_review_seconds"])
                - Decimal(c["b4_30_immutable_seconds"])
                == Decimal(c["b4_31_seconds"]),
            )
            accept(
                "R17-quality-fail-retained",
                Decimal(d["preserved_failures"]["r17_quality"]) > Decimal("1.001"),
            )
            accept(
                "target-mean-fail-retained",
                Decimal(d["preserved_failures"]["target_mean"]) > Decimal("1.0"),
            )
            accept(
                "formal-native-public-only",
                all(
                    Decimal(p["native_real_user_sys"][0]) <= 60
                    and p["maximum_rss_bytes"] <= 268435456
                    for p in formal["profiles"].values()
                ),
            )
        memory = d["full_training_memory"]
        accept(
            "full-fit-not-certified",
            memory["full_training_status"] == "PENDING"
            and memory["fit_cap_bytes"] == 4294967296
            and len(memory["complete_simultaneous_categories"]) == 8
            and memory["historical_gaps_filled"] is False,
        )
        accept(
            "full-cost-categories-retained",
            len(d["preserved_cost"]["full_cost_categories"]) == 16
            and d["preserved_cost"]["real_certification_cost_seconds"] == "UNKNOWN",
        )
        protocol = raw_protocol.decode()
        for phrase in (
            "NOT STARTED/AUTHORIZED",
            "NEVER executed",
            "UNKNOWN_NOT_WRITTEN",
            "B4.43 runtime remains",
            "clean locked merged",
            "all17 boundary",
            "all24 TEXT",
            "PENDING/4GiB",
        ):
            accept("document-coverage-" + phrase, phrase in protocol)
        for text in (own_bytes, corpus["scripts/b4_45_launch_audit.py"]):
            imports = []
            for node in ast.walk(ast.parse(text.decode())):
                if isinstance(node, ast.Import):
                    imports.extend(n.name.partition(".")[0] for n in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append((node.module or "").partition(".")[0])
            accept(
                "stdlib-source-import-boundary-" + sha(text),
                all(name in sys.stdlib_module_names for name in imports),
            )
        for sample in (
            '{"k":0,"k":1}',
            '{"nested":{"z":0,"z":1}}',
            '{"k":NaN}',
            '{"k":-Infinity}',
            "[0]",
        ):
            rejected = False
            try:
                decode(sample)
            except ValueError:
                rejected = True
            accept("JSON-negative-" + sample, rejected)
        for mutation in (
            "extra",
            "lost",
            "boolean",
            "role-next",
            "short-table",
            "row-extra",
            "row-type",
        ):
            modified = json.loads(json.dumps(d))
            if mutation == "extra":
                modified["other"] = None
            elif mutation == "lost":
                modified.pop("scope")
            elif mutation == "boolean":
                modified["slice_limit"] = True
            elif mutation == "role-next":
                modified["next_started"] = True
            elif mutation == "short-table":
                modified["fresh_arithmetic_prerequisites"] = modified[
                    "fresh_arithmetic_prerequisites"
                ][:-1]
            elif mutation == "row-extra":
                modified["stops"][0]["extra"] = 0
            else:
                modified["limitations"][0]["text"] = False
            denied = False
            try:
                contract_schema(modified)
            except ValueError:
                denied = True
            accept("schema-negative-" + mutation, denied)
        accept(
            "no-primary-or-raw-member-read",
            not any(
                "/bound_text/primary/" in p or p.endswith("primary_document_review.json")
                for p in accessed
            ),
        )
    except Exception as error:
        failure = {
            "type": type(error).__name__,
            "detail": str(error),
            "traceback": traceback.format_exc(),
        }
    result = {
        "version": "topolab.b4_46.independent-document-audit.v1",
        "role": "independent",
        "passed": failure is None,
        "formal_calls": 1,
        "formal_retry": False,
        "checks": findings,
        "read_paths": accessed,
        "input_bytes": input_bytes,
        "failure": failure,
        "remaining": [] if failure is None else "NOT_EVALUATED_UNKNOWN",
        "new_arithmetic_campaigns": 0,
        "real_payload_reads": 0,
        "fits": 0,
        "scope": "TEXT_ONLY",
    }
    emit(output_file, result)
    print(json.dumps({"passed": result["passed"], "predicates": len(findings), "failure": failure}))
    return int(not result["passed"])


if __name__ == "__main__":
    sys.exit(main())
