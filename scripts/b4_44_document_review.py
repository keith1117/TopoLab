"""One finite B4.44 TEXT/hash/AST/metadata review; no candidate execution."""

import ast
import copy
import hashlib
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from pathlib import Path

ROOT_KEYS = {
    "version",
    "authority",
    "starting_main",
    "slice_limit",
    "scope",
    "source_inputs_at_starting_main_sha256",
    "external_text_metadata_sha256",
    "primary_only_static_text_sha256",
    "absence_checks",
    "role_access",
    "document_audits",
    "public_evidence_retained",
    "limitations",
    "real_prerequisites",
    "stops",
    "allowed_publish_paths",
    "boundaries",
    "new_production_budget_or_reserve",
    "real_values_and_new_arithmetic_evaluated",
    "future_criteria_unchanged",
    "preserved_failures",
    "preserved_cost",
    "full_training_memory",
    "software_failure_policy",
    "software_cost_policy",
    "next_proposed",
    "next_authorized",
    "next_started",
}
AUDIT_KEYS = {
    "primary_invocations",
    "primary_max_predicates",
    "independent_invocations",
    "independent_max_predicates",
    "decimal_precision",
    "formal_retry",
    "public_texts",
    "compact_metadata",
    "primary_static_texts",
    "each_input_bytes_max",
    "total_input_bytes_max",
    "each_formal_native_wall_seconds_max",
    "each_formal_native_rss_bytes_max",
    "software_bookkeeping_caps_only_not_paid_production_grant",
    "source_access",
    "duplicate_missing_unknown_nonfinite_fields",
}
BOUNDARY_KEYS = {
    "production_execution",
    "real_payload_fem_projection_root_network_integration",
    "fit_profile_retime_search",
    "screen_final_fresh_unused_access",
    "previous_backup_member_dereference",
    "software_peak_fills_old_gap",
    "real_certificate_status",
    "real_executable_frozen",
    "scientific_gate",
    "fixed_p17_repaired",
    "uniform_default",
    "residual_bound_and_original_loss_gradient_unchanged",
    "final_evidence_sealed",
    "old_b4_27_29_quota_closed",
    "b4_30_paid_invocations_numerical_campaigns",
    "b4_30_conditional_cases_sealed",
    "unused_b4_10_cases_sealed",
}
PUBLIC_KEYS = {
    "b4_43_focused_tests",
    "public_systems",
    "regression_enclosures_stops",
    "formal_public_gate",
    "independent_formal_gate",
    "formal_quota_consumed",
    "formal_case_audits",
    "formal_RN_even_proofs",
    "independent_metadata_predicates",
    "producer_original_receipt",
    "producer_original_counts",
    "formal_case_loop_reached",
    "runtime_sys_path_sys_executable",
    "detailed_import_resolution_cause",
    "formal_retry",
    "document_coverage",
    "b4_42_primary_evaluated_pass_fail",
    "b4_42_primary_incomplete",
    "b4_42_gate",
    "b4_42_independent_predicates",
    "b4_41_tests_predicates_RN",
    "b4_39_tests_predicates_RN",
}


def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate " + key)
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError("nonfinite " + value)


def load(raw: bytes | str) -> dict:
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    if type(value) is not dict:
        raise ValueError("root is not an object")
    return value


def closed(value: dict) -> None:
    for item, keys in (
        (value, ROOT_KEYS),
        (value["document_audits"], AUDIT_KEYS),
        (value["boundaries"], BOUNDARY_KEYS),
        (value["public_evidence_retained"], PUBLIC_KEYS),
        (value["role_access"], {"primary", "independent"}),
    ):
        if type(item) is not dict or set(item) != keys:
            raise ValueError("unknown/missing schema field")
    for name, keys in (
        ("limitations", {"id", "text", "scope"}),
        ("real_prerequisites", {"id", "name", "text", "status"}),
        ("stops", {"id", "trigger", "disposition", "alternative_or_retry"}),
    ):
        if type(value[name]) is not list:
            raise ValueError("not a list")
        for item in value[name]:
            if type(item) is not dict or set(item) != keys:
                raise ValueError("unknown/missing row")


def main() -> None:
    base, contract_path, protocol_path, output = map(Path, sys.argv[1:5])
    assert output.parent.resolve() == base.resolve() and not output.exists()
    pending = output.with_suffix(".pending.json")
    pending.write_text(json.dumps({"phase": "BEFORE_TEXT_REVIEW", "production_attempts": 0}) + "\n")
    checks = []
    reads = []
    byte_count = 0

    def require(name: str, passed: bool) -> None:
        assert len(checks) < 500
        checks.append({"predicate": name, "passed": bool(passed)})
        if not passed:
            raise ValueError(name)

    def read(path: Path, expected: str | None = None) -> bytes:
        nonlocal byte_count
        raw = path.read_bytes()
        byte_count += len(raw)
        require("bytes:" + path.name, len(raw) <= 1048576 and byte_count <= 8388608)
        raw.decode("utf-8")
        if expected is not None:
            require(
                "hash:" + str(path.relative_to(base)), hashlib.sha256(raw).hexdigest() == expected
            )
        reads.append(str(path))
        return raw

    error = None
    try:
        c = load(read(contract_path))
        closed(c)
        require("closed-schema", True)
        protocol = read(protocol_path).decode()
        public = {
            n: read(base / "bound_starting_text" / n, d)
            for n, d in c["source_inputs_at_starting_main_sha256"].items()
        }
        old = load(public["docs/planning/b4_43_public_assembled_residual_enclosure_contract.json"])
        expected_paths = (
            set(old["source_inputs_at_starting_main_sha256"])
            | set(old["allowed_publish_paths"])
            | {"pyproject.toml", "uv.lock", "README.md"}
        )
        require("exact-public72", set(public) == expected_paths and len(public) == 72)
        meta = {
            n: load(read(base / "bound_metadata" / n, d))
            for n, d in c["external_text_metadata_sha256"].items()
        }
        require("metadata14", len(meta) == 14)
        source = {
            n: read(base / "primary_only_static_text" / n, d).decode()
            for n, d in c["primary_only_static_text_sha256"].items()
        }
        require("primary-only4", len(source) == 4)
        for key in (
            "future_criteria_unchanged",
            "preserved_failures",
            "preserved_cost",
            "full_training_memory",
        ):
            require("whole-inherited:" + key, c[key] == old[key])
        for key in BOUNDARY_KEYS:
            require("boundary:" + key, c["boundaries"][key] == old[key])
        for name, expected in (("limitations", 18), ("real_prerequisites", 24), ("stops", 20)):
            require("population:" + name, len(c[name]) == expected)
            prefix = {"limitations": "L", "real_prerequisites": "O", "stops": "S"}[name]
            for i, row in enumerate(c[name], 1):
                require("id:" + row["id"], row["id"] == f"{prefix}{i:02d}")
                if name == "limitations":
                    require(
                        "scope:" + row["id"],
                        row["scope"] == "PUBLIC_OR_STATIC_ONLY_NO_REAL_CERTIFICATION"
                        and len(row["text"]) > 30,
                    )
                elif name == "real_prerequisites":
                    require(
                        "text-only:" + row["id"],
                        row["status"]
                        == "TEXT_ONLY_OBLIGATION; UNKNOWN_STOP; UNIMPLEMENTED_UNEVALUATED"
                        and len(row["text"]) > 30,
                    )
                else:
                    require(
                        "stop:" + row["id"],
                        row["alternative_or_retry"] is False
                        and row["disposition"]
                        == "STOP_PRESERVE_FAILURE_AND_UNKNOWN; NO_ALTERNATIVE_OR_RETRY",
                    )
        audits = c["document_audits"]
        for key, expected in {
            "primary_invocations": 1,
            "independent_invocations": 1,
            "primary_max_predicates": 500,
            "independent_max_predicates": 420,
            "decimal_precision": 50,
            "formal_retry": False,
            "public_texts": 72,
            "compact_metadata": 14,
            "primary_static_texts": 4,
            "each_input_bytes_max": 1048576,
            "total_input_bytes_max": 8388608,
            "each_formal_native_wall_seconds_max": 60,
            "each_formal_native_rss_bytes_max": 268435456,
        }.items():
            require(
                "audit-cap:" + key, type(audits[key]) is type(expected) and audits[key] == expected
            )
        b = "b4-43-software-validation/"
        closed_old = meta[b + "closed_main_release.json"]
        final = meta[b + "final_recovery_verification.json"]
        annotation = meta[b + "formal_failure_annotation.json"]
        unknown = meta[b + "formal_launch_unknowns.json"]
        independent = meta[b + "public_independent_audit.json"]
        retained = c["public_evidence_retained"]
        for key in (
            "formal_public_gate",
            "independent_formal_gate",
            "formal_quota_consumed",
            "formal_case_audits",
            "formal_RN_even_proofs",
        ):
            require("old-formal:" + key, retained[key] == closed_old[key])
        require(
            "technical-closure-only",
            closed_old["passed"]
            and final["passed"]
            and closed_old["main"] == final["main"] == c["starting_main"],
        )
        require(
            "old-science-stays-failed",
            closed_old["scientific_gate"] == "FAIL" and not closed_old["fixed_p17_repaired"],
        )
        require("no-old-retry", not closed_old["formal_retry"] and not retained["formal_retry"])
        require(
            "unknown-count-not-zero",
            retained["producer_original_counts"]
            == annotation["original_native_counts"]
            == "UNKNOWN_NOT_INSTRUMENTED",
        )
        require(
            "receipt-not-written",
            retained["producer_original_receipt"]
            == annotation["original_producer_receipt"]
            == "NOT_WRITTEN",
        )
        require(
            "ten-unexecuted",
            not annotation["case_loop_reached"]
            and len(annotation["prescribed_cases_not_executed"]) == 10,
        )
        require(
            "actual-environment-unknown",
            unknown["formal_producer_actual_sys_path"]
            == unknown["formal_producer_selected_sys_executable"]
            == retained["runtime_sys_path_sys_executable"]
            == "UNKNOWN_NOT_RECORDED",
        )
        require(
            "detailed-cause-unknown",
            unknown["package_resolution_root_cause_beyond_import_failure"]
            == retained["detailed_import_resolution_cause"]
            == "UNKNOWN_NOT_DIAGNOSED",
        )
        require(
            "independent-incomplete8",
            not independent["passed"]
            and independent["predicates"] == 8
            and independent["RN_even_operations"] == 0
            and not independent["rows"],
        )
        require(
            "prior-regression94-not-formal",
            retained["b4_43_focused_tests"] == closed_old["focused_regression_tests"] == 94
            and retained["document_coverage"] == [131, 109],
        )
        require(
            "b4-42-failure",
            retained["b4_42_primary_evaluated_pass_fail"] == [196, 195, 1]
            and retained["b4_42_gate"]
            == closed_old["old_b4_42_document_gate"]
            == "FAIL_PRIMARY_CHECKER",
        )
        for name in c["absence_checks"]:
            require("absence:" + name, not (base.parent / name).exists())
        producer = source[
            b + "public_producer/source_snapshot/controllers/b4_43_public_producer.py"
        ]
        tree = ast.parse(producer)
        imports = [n for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == "topolab"]
        require(
            "static-import-before-case",
            len(imports) == 1
            and imports[0].lineno == 5
            and producer.index("from topolab") < producer.index("public_producer_pending.json"),
        )
        require(
            "original-trace-only",
            "ModuleNotFoundError: No module named 'topolab'"
            in source[b + "public_producer/command.log"],
        )
        require(
            "original-argv",
            meta[b + "public_producer/before.json"]["argv"]
            == [
                "uv",
                "run",
                "python",
                "/Users/keith1117/Documents/TopoLab/local/b4_43_public_producer.py",
            ],
        )
        require(
            "pytest-context-not-runtime-proof",
            'pythonpath = ["src"]' in public["pyproject.toml"].decode(),
        )
        resources = meta[b + "closed_software_native_resource_metadata.json"]
        require(
            "old-cost-failures-retained",
            resources["command_count"] == 42
            and len(resources["native_failures"]) == 3
            and resources["administrative_failures"] == 3
            and resources["observed_wall_seconds"]["whole_sum"] == "UNKNOWN_NOT_ZERO",
        )
        require(
            "old-CI-unknown-retained",
            meta[b + "closed_ci_wall_metadata.json"]["unknown_job_wall_count"] == 1,
        )
        for token in (
            "UNKNOWN_NOT_DIAGNOSED",
            "NOT_WRITTEN",
            "intended interval FIRST",
            "BOTH actual triangles",
            "beta_eval",
            "q_eval=up(q_hat+beta_eval)",
            "r_plus=up(with_operator+beta_f)",
            "Tiny nonzero residual never",
            "all8",
            "All16",
            "Real executable UNFROZEN",
            "NOT STARTED/AUTHORIZED",
            "no B4.43 retry",
            "Close B4.44 only and stop",
        ):
            require("protocol:" + token, token in protocol)
        for name in ("scripts/b4_41_representation_oracle.py", "scripts/b4_43_residual_oracle.py"):
            imports = [
                n
                for n in ast.walk(ast.parse(public[name].decode()))
                if isinstance(n, ast.Import | ast.ImportFrom)
            ]
            modules = [
                n.module if isinstance(n, ast.ImportFrom) else a.name
                for n in imports
                for a in (n.names if isinstance(n, ast.Import) else [None])
            ]
            require(
                "separate-oracle-static:" + name,
                all(x and x.split(".")[0] in sys.stdlib_module_names for x in modules),
            )
        with localcontext() as ctx:
            ctx.prec = 50
            paid = c["preserved_cost"]
            require(
                "immutable-paid-floor-fails",
                Decimal(paid["cross_route_known_paid_floor_seconds"])
                > Decimal(paid["old_proxy_cap_seconds"]),
            )
            require(
                "failed-mean-not-sum",
                Decimal(c["preserved_failures"]["target_mean"]) > Decimal("1.0")
                and not c["preserved_failures"]["mean_replaced_by_sum"],
            )
            require("old-full-reserves", paid["b4_30_full_reserves_seconds"] == ["180", "180"])
        for raw in ('{"a":1,"a":2}', '{"a":{"b":1,"b":2}}', '{"a":NaN}', '{"a":Infinity}'):
            try:
                load(raw)
            except ValueError:
                require("JSON-denial:" + raw, True)
            else:
                require("JSON-denial:" + raw, False)
        for key in (
            None,
            "document_audits",
            "public_evidence_retained",
            "boundaries",
            "role_access",
        ):
            for change in ("unknown", "missing"):
                bad = copy.deepcopy(c)
                target = bad if key is None else bad[key]
                if change == "unknown":
                    target["unexpected"] = True
                else:
                    target.pop(next(iter(target)))
                try:
                    closed(bad)
                except (ValueError, KeyError):
                    require(f"schema-denial:{key}:{change}", True)
                else:
                    require(f"schema-denial:{key}:{change}", False)
        require(
            "no-real-numerical-evaluation",
            c["real_values_and_new_arithmetic_evaluated"] is False
            and c["new_production_budget_or_reserve"] == "NONE_TEXT_ONLY",
        )
        require("publish13", len(c["allowed_publish_paths"]) == 13)
        require(
            "exact-successor",
            c["next_proposed"]
            == "B4.45 bounded public launch-context and immutable-receipt preflight software"
            and not c["next_authorized"]
            and not c["next_started"],
        )
    except (ValueError, KeyError, OSError, AssertionError, TypeError) as exc:
        error = repr(exc)
    result = {
        "passed": error is None,
        "predicates": len(checks),
        "checks": checks,
        "error": error,
        "remaining_if_failed": "UNKNOWN_NOT_EVALUATED" if error else None,
        "read_paths": reads,
        "input_bytes": byte_count,
        "at_utc": datetime.now(UTC).isoformat(),
        "scope": "TEXT_HASH_AST_AND_COMPACT_METADATA_ONLY",
        "candidate_or_shared_helper_imported": False,
        "numerical_value_evaluated": False,
        "production_attempts": 0,
        "formal_retry": False,
    }
    with output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("checks", "read_paths")}))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
