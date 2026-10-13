"""First-only B4.46 text/hash/AST review; never import or execute a candidate."""

import ast
import copy
import hashlib
import json
import os
import sys
import traceback
from decimal import Decimal, localcontext
from pathlib import Path

ROOT_FIELDS = set(
    "version authority starting_main slice_limit scope source_inputs_at_starting_main_sha256 "
    "primary_only_source_text_sha256 external_text_metadata_sha256 role_access document_audits "
    "b4_45_retained public_evidence_retained b4_44_retained limitations "
    "fresh_arithmetic_prerequisites real_prerequisites stops boundaries future_criteria_unchanged "
    "preserved_failures preserved_cost full_training_memory new_production_budget_or_reserve "
    "real_values_and_new_arithmetic_evaluated allowed_publish_paths software_failure_policy "
    "software_cost_policy next_proposed next_authorized next_started".split()
)
ROW_FIELDS = {
    "limitations": (18, "L", {"id", "text", "scope"}),
    "fresh_arithmetic_prerequisites": (20, "A", {"id", "name", "text", "status"}),
    "real_prerequisites": (24, "O", {"id", "name", "text", "status"}),
    "stops": (20, "S", {"id", "trigger", "disposition", "alternative_or_retry"}),
}
AUDIT_FIELDS = set(
    "primary_invocations independent_invocations formal_retry primary_max_predicates "
    "independent_max_predicates decimal_precision public_texts compact_metadata "
    "primary_static_texts "
    "each_input_bytes_max total_input_bytes_max each_formal_native_wall_seconds_max "
    "each_formal_native_rss_bytes_max source_access software_source_condition "
    "software_bookkeeping_caps_only_not_paid_production_grant "
    "duplicate_missing_unknown_nonfinite_fields".split()
)
LIMIT_TOKENS = (
    ("Four inert", "no numerical"),
    ("NEVER execute", "import readiness"),
    ("B4.45 only", "concurrency"),
    ("entire working tree", "dependency binaries"),
    ("pycache", "not a general"),
    ("four-hash", "another module"),
    ("eight STOP", "FAIL controls"),
    ("authenticated provenance", "mutation protection"),
    ("before request", "multi-writer"),
    ("Pending precedes", "bootstrap"),
    ("UNKNOWN_NOT_WRITTEN", "not a completed"),
    ("UNKNOWN_NOT_RECORDED", "UNKNOWN_NOT_DIAGNOSED"),
    ("quota1/1", "all10"),
    ("94 regression", "B4.42"),
    ("12/277/32", "no scientific repair"),
    ("administrative10", "UNKNOWN_NOT_ZERO"),
    ("PENDING/4GiB", "historical"),
    ("UNFROZEN", "every seal"),
)
FRESH_TOKENS = (
    ("NEW owner", "never a B4.43 retry"),
    ("BEFORE", "complete case list"),
    ("clean locked merged", "exact-head and main"),
    ("ACTUAL", "inert marker"),
    ("BEFORE", "consumes its quota"),
    ("snapshot", "races"),
    ("duplicate/missing/unknown/nonfinite", "before protected bytes"),
    ("BEFORE each", "never inferred zero"),
    ("observed process exit", "absent results"),
    ("actual-candidate", "stay separate"),
    ("interval FIRST", "fixed80-bit"),
    ("freeze", "no candidate/producer/TopoLab/shared"),
    ("every retained operation", "RN-even"),
    ("beta_G/beta_K/beta_f/beta_eval/q_hat/u_plus", "both actual triangles"),
    ("ALL cases", "no omission"),
    ("first failure", "no rerun/resume"),
    ("through-exit", "UNKNOWN_NOT_ZERO"),
    ("new evidence", "old cause"),
    ("ALL24", "all16 cost categories/all8"),
    ("ALL upload commits", "blocks publication"),
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON field: " + key)
            result[key] = value
        return result

    def deny(token):
        raise ValueError("nonfinite JSON: " + token)

    value = json.loads(raw, object_pairs_hook=unique, parse_constant=deny)
    if type(value) is not dict:
        raise ValueError("root must be a JSON object")
    return value


def validate(value):
    if type(value) is not dict or set(value) != ROOT_FIELDS:
        raise ValueError("closed root schema differs")
    if type(value["slice_limit"]) is not int or value["slice_limit"] != 1:
        raise ValueError("one slice required")
    if set(value["document_audits"]) != AUDIT_FIELDS:
        raise ValueError("closed audit schema differs")
    if set(value["role_access"]) != {"primary", "independent"}:
        raise ValueError("closed roles differ")
    for name, (count, prefix, fields) in ROW_FIELDS.items():
        rows = value[name]
        if type(rows) is not list or len(rows) != count:
            raise ValueError("closed row population: " + name)
        for index, row in enumerate(rows, 1):
            if type(row) is not dict or set(row) != fields or row["id"] != f"{prefix}{index:02}":
                raise ValueError("closed row schema/order: " + name)
            if any(type(v) is not str for k, v in row.items() if k != "alternative_or_retry"):
                raise ValueError("row text type: " + name)
            if name == "stops" and row["alternative_or_retry"] is not False:
                raise ValueError("no alternative or retry")
    for name in ("next_authorized", "next_started", "real_values_and_new_arithmetic_evaluated"):
        if value[name] is not False:
            raise ValueError("new execution or successor authority")


def write_once(path, value):
    with path.open("xb") as stream:
        stream.write((json.dumps(value, indent=2, allow_nan=False) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


def main():
    evidence, contract_path, protocol_path, destination = map(Path, sys.argv[1:])
    checks, reads, byte_count, failure = [], [], 0, None

    def read(path):
        nonlocal byte_count
        if path.is_symlink() or path.resolve() != path.absolute():
            raise ValueError("symlink or redirected input")
        with path.open("rb") as stream:
            raw = stream.read(1048577)
        if len(raw) > 1048576:
            raise ValueError("single text byte cap")
        byte_count += len(raw)
        if byte_count > 8388608:
            raise ValueError("total text byte cap")
        reads.append(str(path))
        return raw

    def check(name, passed):
        checks.append({"id": name, "passed": bool(passed)})
        if len(checks) > 900 or not passed:
            raise ValueError("document predicate failed: " + name)

    write_once(
        destination.with_suffix(".pending.json"), {"phase": "BEFORE_TEXT_INPUTS", "role": "primary"}
    )
    try:
        freeze = parse(read(evidence / "reviewer_program_freeze.json"))
        check("contract-freeze", digest(read(contract_path)) == freeze["contract_sha256"])
        check("protocol-freeze", digest(read(protocol_path)) == freeze["protocol_sha256"])
        check(
            "own-source-freeze",
            digest(read(Path(__file__))) == freeze["program_sha256"][str(Path(__file__).name)],
        )
        c = parse(read(contract_path))
        validate(c)
        check("closed-contract-and-rows", True)
        protocol = read(protocol_path).decode()
        bound = {}
        for category, key in (
            ("common", "source_inputs_at_starting_main_sha256"),
            ("primary", "primary_only_source_text_sha256"),
            ("metadata", "external_text_metadata_sha256"),
        ):
            for name, expected in c[key].items():
                if Path(name).is_absolute() or ".." in Path(name).parts:
                    raise ValueError("unlisted text identity")
                raw = read(evidence / "bound_text" / category / name)
                check("bound-" + name, digest(raw) == expected)
                bound[name] = raw
        check("finite-role-paths", len(bound) == 35)
        prior_name = "docs/planning/b4_45_public_launch_context_immutable_receipts_contract.json"
        old = parse(bound[prior_name])
        for key in (
            "future_criteria_unchanged",
            "preserved_failures",
            "preserved_cost",
            "full_training_memory",
            "boundaries",
            "public_evidence_retained",
            "b4_44_retained",
            "real_prerequisites",
        ):
            check(
                "entire-inherited-" + key,
                json.dumps(c[key], sort_keys=True) == json.dumps(old[key], sort_keys=True),
            )
        for key, value in old["boundaries"].items():
            check(
                "full-boundary-" + key,
                type(c["boundaries"][key]) is type(value) and c["boundaries"][key] == value,
            )
        a = c["document_audits"]
        check(
            "once-and-bookkeeping-caps",
            a["primary_invocations"] == a["independent_invocations"] == 1
            and a["formal_retry"] is False
            and a["each_formal_native_wall_seconds_max"] == 60
            and a["each_formal_native_rss_bytes_max"] == 268435456
            and a["software_bookkeeping_caps_only_not_paid_production_grant"] is True,
        )
        check(
            "text-source-condition",
            "working-tree" in a["software_source_condition"]
            and "clean locked merged" in a["software_source_condition"],
        )
        check(
            "scope-and-successor",
            c["scope"] == "BOUNDED_READ_ONLY_TEXT_AND_LITERAL_COMPACT_METADATA_ONLY"
            and c["new_production_budget_or_reserve"] == "NONE_TEXT_ONLY"
            and c["next_proposed"].startswith("B4.47 "),
        )
        for rows, tokens, expected_status in (
            (c["limitations"], LIMIT_TOKENS, "PUBLIC_OR_STATIC_ONLY_NO_NEW_EXECUTION"),
            (
                c["fresh_arithmetic_prerequisites"],
                FRESH_TOKENS,
                "TEXT_ONLY_FRESH_PUBLIC_CAMPAIGN_PREREQUISITE; NOT_AUTHORIZED_NOT_STARTED",
            ),
        ):
            for row, words in zip(rows, tokens, strict=True):
                check(row["id"] + "-meaning", all(word in row["text"] for word in words))
                check(row["id"] + "-scope", row.get("scope", row.get("status")) == expected_status)
        for row in c["real_prerequisites"]:
            check(
                row["id"] + "-real-status",
                row["status"] == "TEXT_ONLY_OBLIGATION; UNKNOWN_STOP; UNIMPLEMENTED_UNEVALUATED",
            )
        for row in c["stops"]:
            check(
                row["id"] + "-stop",
                row["disposition"] == "STOP_PRESERVE_FAILURE_AND_UNKNOWN; NO_ALTERNATIVE_OR_RETRY"
                and row["alternative_or_retry"] is False,
            )
        release = parse(bound["b4-45-software-validation/closed_main_release.json"])
        final = parse(bound["b4-45-software-validation/final_recovery_verification.json"])
        formal = parse(bound["b4-45-software-validation/closed_formal_public_resource.json"])
        resource = parse(bound["b4-45-software-validation/closed_software_resource_metadata.json"])
        ci = parse(bound["b4-45-software-validation/closed_ci_wall_metadata.json"])
        for name, value in (
            ("release", release),
            ("final", final),
            ("formal", formal),
            ("resource", resource),
            ("ci", ci),
        ):
            check("prior-" + name + "-accepted-metadata", value["passed"] is True)
        retained = c["b4_45_retained"]
        for key in (
            "software_gate",
            "cases",
            "independent_predicates",
            "focused_tests",
            "formal_calls",
            "formal_retry",
        ):
            check("launch-retained-" + key, retained[key] == release[key])
        check(
            "old-main-and-closure",
            release["slice_closed"] and release["main"] == final["main"] == c["starting_main"],
        )
        check(
            "no-old-formal-retry",
            release["prior_b4_43_quota"] == [1, 1]
            and release["prior_b4_43_formal_gate"] == "FAIL_FORMAL_PRODUCER"
            and release["prior_b4_43_independent_gate"] == "FAIL_INCOMPLETE",
        )
        check(
            "prior-native-sandbox-administration",
            release["native_failures"] == len(resource["native_failures"]) == 3
            and release["sandbox_coordination_failures"] == len(resource["sandbox_failures"]) == 2
            and release["administrative_failures"]
            == len(resource["administrative_failures"])
            == 10,
        )
        check(
            "cost-unknown-and-no-reset",
            resource["complete_all_software_cost"] == "UNKNOWN_NOT_ZERO"
            and resource["whole_chain_peak"] == "UNKNOWN_NOT_ZERO"
            and resource["historic_paid_ledger_reset"] is False,
        )
        fixture = parse(bound["tests/fixtures/b4_45_launch_preflight.json"])
        check(
            "four-inert-texts-only",
            len(fixture["source_texts"]) == 4
            and all(
                digest(t.encode()) == fixture["source_sha256"][n]
                for n, t in fixture["source_texts"].items()
            ),
        )
        check(
            "twelve-unmodified-controls",
            fixture["cases"] == old["public_cases"] and len(fixture["cases"]) == 12,
        )
        for case in fixture["cases"]:
            check(
                "retained-control-" + case["id"],
                formal["dispositions"][case["expected_status"]] == 1,
            )
        with localcontext() as ctx:
            ctx.prec = 50
            cost, failed = c["preserved_cost"], c["preserved_failures"]
            check(
                "scientific-quality-fail",
                Decimal(failed["r17_quality"]) > Decimal(failed["quality_limit"]),
            )
            check(
                "scientific-mean-fail",
                Decimal(failed["target_mean"]) > Decimal(failed["target_mean_limit"]),
            )
            check(
                "old-ledger-Q31-once",
                Decimal(cost["b4_30_immutable_seconds"]) + Decimal(cost["b4_31_seconds"])
                == Decimal(cost["b4_31_campaign_plus_review_seconds"]),
            )
            check(
                "known-paid-floor-fails",
                sum(map(Decimal, cost["known_actual_stage_components_seconds"].values()))
                == Decimal(cost["cross_route_known_paid_floor_seconds"])
                > Decimal(cost["old_proxy_cap_seconds"]),
            )
            check(
                "old-native-sandbox-separate",
                resource["native_wall"]["known_subtotal_seconds"] == "65.30"
                and resource["sandbox_observed_wall"]["known_subtotal_seconds"]
                == "2630.145373876672287103",
            )
            check(
                "CI-unknown-preserved",
                ci["known_separate_job_wall_sum_seconds"] == "3442.0"
                and ci["unknown_job_wall_count"] == 1,
            )
            for name, row in formal["profiles"].items():
                check(
                    "old-formal-native-" + name,
                    Decimal(row["native_real_user_sys"][0]) <= 60
                    and row["maximum_rss_bytes"] <= 268435456,
                )
        launch = bound["src/topolab/launch_preflight.py"].decode()
        tree = ast.parse(launch)
        functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        child_text = ast.get_source_segment(launch, functions["child"])
        parent_text = ast.get_source_segment(launch, functions["run_preflight"])
        check(
            "origin-only-no-eager-import",
            'PathFinder.find_spec("topolab", sys.path)' in child_text
            and not any(
                isinstance(n, ast.ImportFrom) and (n.module or "").startswith("topolab")
                for n in ast.walk(tree)
            ),
        )
        check(
            "started-before-checked-byte-exec",
            child_text.index('output / "started.json"') < child_text.index("exec(compile(raw"),
        )
        check(
            "pending-before-parent-launch",
            parent_text.index('output / "pending.json"') < parent_text.index("subprocess.run("),
        )
        check(
            "output-refusal-before-request",
            parent_text.index("output.mkdir(") < parent_text.index("read_bounded(request_path"),
        )
        check(
            "terminal-after-observed-exit",
            parent_text.index("subprocess.run(") < parent_text.index('output / "terminal.json"'),
        )
        check(
            "missing-counts-unknown",
            '"UNKNOWN_NOT_WRITTEN"' in parent_text and '"NOT_WRITTEN"' in parent_text,
        )
        for name in (
            "src/topolab/launch_preflight.py",
            "scripts/b4_45_launch_evidence.py",
            "scripts/b4_45_launch_audit.py",
        ):
            modules = []
            for n in ast.walk(ast.parse(bound[name].decode())):
                if isinstance(n, ast.Import):
                    modules.extend(alias.name.split(".")[0] for alias in n.names)
                if isinstance(n, ast.ImportFrom):
                    modules.append((n.module or "").split(".")[0])
            check(
                "old-public-stdlib-" + name,
                all(module in sys.stdlib_module_names for module in modules),
            )
        for word in (
            "18 limitations",
            "20 fresh public",
            "unchanged24 real",
            "UNKNOWN_NOT_RECORDED",
            "UNKNOWN_NOT_DIAGNOSED",
            "PENDING/4GiB",
            "B4.47",
            "NOT STARTED/AUTHORIZED",
        ):
            check("protocol-" + word, word in protocol)
        for raw in (
            b'{"x":1,"x":2}',
            b'{"x":{"a":1,"a":2}}',
            b'{"x":NaN}',
            b'{"x":Infinity}',
            b"[]",
        ):
            try:
                parse(raw)
            except ValueError:
                check("closed-json-denial-" + raw.decode(), True)
            else:
                check("closed-json-denial", False)
        for kind in ("unknown", "missing", "bool-slice", "missing-row", "unknown-row", "successor"):
            bad = copy.deepcopy(c)
            if kind == "unknown":
                bad["unregistered"] = 1
            elif kind == "missing":
                del bad["scope"]
            elif kind == "bool-slice":
                bad["slice_limit"] = True
            elif kind == "missing-row":
                bad["limitations"].pop()
            elif kind == "unknown-row":
                bad["stops"][0]["ignored"] = True
            else:
                bad["next_authorized"] = True
            try:
                validate(bad)
            except ValueError:
                check("schema-denial-" + kind, True)
            else:
                check("schema-denial-" + kind, False)
    except Exception as exc:
        failure = {
            "type": type(exc).__name__,
            "detail": str(exc),
            "traceback": traceback.format_exc(),
        }
    receipt = {
        "version": "topolab.b4_46.document-review.v1",
        "role": "primary",
        "passed": failure is None,
        "formal_calls": 1,
        "formal_retry": False,
        "checks": checks,
        "read_paths": reads,
        "input_bytes": byte_count,
        "failure": failure,
        "remaining": "NOT_EVALUATED_UNKNOWN" if failure else [],
        "new_arithmetic_campaigns": 0,
        "real_payload_reads": 0,
        "fits": 0,
        "scope": "TEXT_ONLY",
    }
    write_once(destination, receipt)
    print(json.dumps({"passed": receipt["passed"], "predicates": len(checks), "failure": failure}))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
