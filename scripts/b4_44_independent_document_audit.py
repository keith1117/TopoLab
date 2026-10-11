"""Independent finite text audit; never read the primary program or receipt."""

import ast
import hashlib
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from pathlib import Path

FIELDS = {
    "": "version authority starting_main slice_limit scope source_inputs_at_starting_main_sha256 "
    "external_text_metadata_sha256 primary_only_static_text_sha256 absence_checks role_access "
    "document_audits public_evidence_retained limitations real_prerequisites stops "
    "allowed_publish_paths boundaries new_production_budget_or_reserve "
    "real_values_and_new_arithmetic_evaluated future_criteria_unchanged preserved_failures "
    "preserved_cost full_training_memory software_failure_policy software_cost_policy "
    "next_proposed next_authorized next_started",
    "document_audits": "primary_invocations primary_max_predicates independent_invocations "
    "independent_max_predicates decimal_precision formal_retry public_texts compact_metadata "
    "primary_static_texts each_input_bytes_max total_input_bytes_max "
    "each_formal_native_wall_seconds_max each_formal_native_rss_bytes_max "
    "software_bookkeeping_caps_only_not_paid_production_grant source_access "
    "duplicate_missing_unknown_nonfinite_fields",
    "role_access": "primary independent",
    "boundaries": "production_execution real_payload_fem_projection_root_network_integration "
    "fit_profile_retime_search screen_final_fresh_unused_access previous_backup_member_dereference "
    "software_peak_fills_old_gap real_certificate_status real_executable_frozen scientific_gate "
    "fixed_p17_repaired uniform_default residual_bound_and_original_loss_gradient_unchanged "
    "final_evidence_sealed old_b4_27_29_quota_closed b4_30_paid_invocations_numerical_campaigns "
    "b4_30_conditional_cases_sealed unused_b4_10_cases_sealed",
    "public_evidence_retained": "b4_43_focused_tests public_systems regression_enclosures_stops "
    "formal_public_gate independent_formal_gate formal_quota_consumed formal_case_audits "
    "formal_RN_even_proofs independent_metadata_predicates producer_original_receipt "
    "producer_original_counts formal_case_loop_reached runtime_sys_path_sys_executable "
    "detailed_import_resolution_cause formal_retry document_coverage "
    "b4_42_primary_evaluated_pass_fail b4_42_primary_incomplete b4_42_gate "
    "b4_42_independent_predicates b4_41_tests_predicates_RN b4_39_tests_predicates_RN",
}
ROWS = {
    "limitations": (18, "L", "id text scope"),
    "real_prerequisites": (24, "O", "id name text status"),
    "stops": (20, "S", "id trigger disposition alternative_or_retry"),
}
OBLIGATIONS = (
    ("locked interpreter", "before candidate"),
    ("before imports", "NOT_WRITTEN/UNKNOWN"),
    ("all10", "no shared"),
    ("bits", "zero-Dirichlet"),
    ("engineering-Voigt", "no half-factor"),
    ("each intended element PSD", "cannot replace"),
    ("canonical24-DOF", "degree3"),
    ("G-Gram(A0)", "Gram(A0)-Gram(A_hat)"),
    ("BOTH triangles", "beta_G/beta_K"),
    ("exactly one distribution", "beta_f"),
    ("SAME", "not exact intended equilibrium"),
    ("multiply", "beta_eval"),
    ("q_hat", "r_plus"),
    ("freeze one", "no adaptive"),
    ("eta_plus<1", "M_plus>0"),
    ("lower_G", "m_minus=down(E_min_lower*lower_G)>0"),
    ("SAME-force U_plus", "positive SAME stored C_s_minus"),
    ("B_plus=up((sqrt_up(U_plus)", "diagnostics only"),
    ("two-step FD/LOCAL", "fixed P17"),
    ("16*m*n", "8*m*m"),
    ("all16", "UNKNOWN required maxima BLOCK"),
    ("all8", "4294967296-byte"),
    ("clean merged source", "grants none"),
    ("old failures/unknowns", "never a retry"),
)


def pairs_unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    names = [name for name, _ in pairs]
    if len(set(names)) != len(names):
        raise ValueError("duplicate JSON field")
    return dict(pairs)


def nonfinite(token: str) -> None:
    raise ValueError("nonfinite JSON: " + token)


def parse(text: str) -> dict:
    value = json.loads(text, object_pairs_hook=pairs_unique, parse_constant=nonfinite)
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def schema(c: dict) -> None:
    for name, words in FIELDS.items():
        value = c[name] if name else c
        if type(value) is not dict or set(value) != set(words.split()):
            raise ValueError("closed keys: " + name)
    for name, (count, prefix, words) in ROWS.items():
        rows = c[name]
        if type(rows) is not list or len(rows) != count:
            raise ValueError("closed population: " + name)
        for index, row in enumerate(rows, 1):
            if set(row) != set(words.split()) or row["id"] != f"{prefix}{index:02d}":
                raise ValueError("closed row: " + name)


def main() -> None:
    evidence_root, contract, protocol, destination = [Path(p) for p in sys.argv[1:5]]
    assert destination.parent.resolve() == evidence_root.resolve() and not destination.exists()
    destination.with_suffix(".pending.json").write_text(
        '{"phase":"BEFORE_INDEPENDENT_TEXT_AUDIT","production_attempts":0}\n'
    )
    facts = []
    accessed = []
    total_bytes = 0

    def record(label: str, truth: bool) -> None:
        if len(facts) >= 420:
            raise ValueError("independent predicate cap")
        facts.append({"predicate": label, "passed": bool(truth)})
        if not truth:
            raise ValueError(label)

    def text_file(file: Path, digest: str | None = None) -> str:
        nonlocal total_bytes
        raw = file.read_bytes()
        total_bytes += len(raw)
        record("bounded-text:" + file.name, len(raw) <= 1048576 and total_bytes <= 8388608)
        if digest is not None:
            record(
                "immutable:" + str(file.relative_to(evidence_root)),
                hashlib.sha256(raw).hexdigest() == digest,
            )
        accessed.append(str(file))
        return raw.decode("utf-8")

    failure = None
    try:
        c = parse(text_file(contract))
        schema(c)
        record("closed-contract", True)
        prose = text_file(protocol)
        public = {}
        for relative, digest in c["source_inputs_at_starting_main_sha256"].items():
            public[relative] = text_file(evidence_root / "bound_starting_text" / relative, digest)
        old = parse(public["docs/planning/b4_43_public_assembled_residual_enclosure_contract.json"])
        inputs = set(old["source_inputs_at_starting_main_sha256"])
        inputs.update(old["allowed_publish_paths"])
        inputs.update(["README.md", "pyproject.toml", "uv.lock"])
        record("public72-exact", set(public) == inputs and len(public) == 72)
        metadata = {}
        for relative, digest in c["external_text_metadata_sha256"].items():
            raw = text_file(evidence_root / "bound_metadata" / relative, digest)
            metadata[relative] = parse(raw)
        record("metadata14-exact", len(metadata) == 14)
        record(
            "independent-role",
            "reads no primary reviewer/receipt" in c["role_access"]["independent"],
        )
        for name in [
            "future_criteria_unchanged",
            "preserved_failures",
            "preserved_cost",
            "full_training_memory",
        ]:
            record("entire-historical-object:" + name, c[name] == old[name])
        for field, actual in c["boundaries"].items():
            record("entire-boundary-value:" + field, actual == old[field])
        for row in c["limitations"]:
            record(
                "public-limitation:" + row["id"],
                row["scope"] == "PUBLIC_OR_STATIC_ONLY_NO_REAL_CERTIFICATION"
                and len(row["text"]) > 30,
            )
        for row, required in zip(c["real_prerequisites"], OBLIGATIONS, strict=True):
            record(
                "real-obligation:" + row["id"],
                row["status"] == "TEXT_ONLY_OBLIGATION; UNKNOWN_STOP; UNIMPLEMENTED_UNEVALUATED"
                and all(word in row["text"] for word in required),
            )
        for row in c["stops"]:
            record(
                "mandatory-stop:" + row["id"],
                row["alternative_or_retry"] is False
                and len(row["trigger"]) > 20
                and row["disposition"]
                == "STOP_PRESERVE_FAILURE_AND_UNKNOWN; NO_ALTERNATIVE_OR_RETRY",
            )
        audits = c["document_audits"]
        for field, expected in {
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
            "software_bookkeeping_caps_only_not_paid_production_grant": True,
        }.items():
            record(
                "fixed-cap:" + field,
                type(audits[field]) is type(expected) and audits[field] == expected,
            )
        prefix = "b4-43-software-validation/"
        release = metadata[prefix + "closed_main_release.json"]
        verification = metadata[prefix + "final_recovery_verification.json"]
        note = metadata[prefix + "formal_failure_annotation.json"]
        missing = metadata[prefix + "formal_launch_unknowns.json"]
        audit = metadata[prefix + "public_independent_audit.json"]
        retained = c["public_evidence_retained"]
        record(
            "starting-technical-main",
            release["passed"]
            and verification["passed"]
            and release["main"] == verification["main"] == c["starting_main"],
        )
        for field in [
            "formal_public_gate",
            "independent_formal_gate",
            "formal_quota_consumed",
            "formal_case_audits",
            "formal_RN_even_proofs",
        ]:
            record("failed-formal-preserved:" + field, release[field] == retained[field])
        record(
            "failed-quota",
            retained["formal_quota_consumed"] == [1, 1]
            and not retained["formal_retry"]
            and not release["formal_retry"],
        )
        record(
            "receipt-original-absence",
            note["original_producer_receipt"]
            == note["original_pending_receipt"]
            == retained["producer_original_receipt"]
            == "NOT_WRITTEN",
        )
        record(
            "unknown-not-zero",
            note["original_native_counts"]
            == retained["producer_original_counts"]
            == "UNKNOWN_NOT_INSTRUMENTED",
        )
        record(
            "no-formal-case-loop",
            not note["case_loop_reached"] and len(note["prescribed_cases_not_executed"]) == 10,
        )
        record(
            "original-runtime-not-recovered",
            missing["formal_producer_actual_sys_path"]
            == missing["formal_producer_selected_sys_executable"]
            == retained["runtime_sys_path_sys_executable"]
            == "UNKNOWN_NOT_RECORDED",
        )
        record(
            "root-cause-unproved",
            missing["package_resolution_root_cause_beyond_import_failure"]
            == retained["detailed_import_resolution_cause"]
            == "UNKNOWN_NOT_DIAGNOSED",
        )
        record(
            "old-independent-incomplete",
            audit["passed"] is False
            and audit["predicates"] == 8
            and audit["RN_even_operations"] == 0
            and audit["rows"] == []
            and not audit["producer_script_read"],
        )
        record(
            "regression-not-formal",
            retained["b4_43_focused_tests"] == release["focused_regression_tests"] == 94
            and retained["regression_enclosures_stops"] == [6, 4],
        )
        record(
            "document-coverage-only",
            retained["document_coverage"] == [131, 109]
            and retained["b4_42_primary_evaluated_pass_fail"] == [196, 195, 1]
            and retained["b4_42_primary_incomplete"]
            and retained["b4_42_gate"] == "FAIL_PRIMARY_CHECKER",
        )
        for relative in c["absence_checks"]:
            record("existence-only:" + relative, not (evidence_root.parent / relative).exists())
        resources = metadata[prefix + "closed_software_native_resource_metadata.json"]
        record(
            "failure-inclusive-software-history",
            resources["command_count"] == 42
            and len(resources["native_failures"]) == 3
            and resources["administrative_failures"] == 3
            and resources["observed_wall_seconds"]["unknown_commands"] == 1
            and resources["observed_wall_seconds"]["whole_sum"] == "UNKNOWN_NOT_ZERO",
        )
        record(
            "old-CI-unknown",
            metadata[prefix + "closed_ci_wall_metadata.json"]["unknown_job_wall_count"] == 1,
        )
        for name in ["scripts/b4_41_representation_oracle.py", "scripts/b4_43_residual_oracle.py"]:
            tree = ast.parse(public[name])
            modules = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.extend(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    modules.append((node.module or "").split(".")[0])
            record(
                "AST-only-independent-modules:" + name,
                all(module in sys.stdlib_module_names for module in modules),
            )
        for token in [
            "BOTH actual triangles",
            "beta_eval",
            "q_eval=up(q_hat+beta_eval)",
            "operator_solution=up(beta_K*u_plus)",
            "r_plus=up(with_operator+beta_f)",
            "m_minus=down(E_min_lower*lower_G)>0",
            "Tiny nonzero residual never",
            "SAME stored",
            "full Q_transpose additional8*m*m",
            "all8",
            "All16",
            "UNKNOWN_NOT_DIAGNOSED",
            "Real executable UNFROZEN",
            "no B4.43 retry",
            "Close B4.44 only and stop",
        ]:
            record("conditional-prose:" + token, token in prose)
        with localcontext() as decimal_context:
            decimal_context.prec = 50
            costs = c["preserved_cost"]
            record(
                "unchanged-paid-floor-failure",
                Decimal(costs["cross_route_known_paid_floor_seconds"])
                > Decimal(costs["old_proxy_cap_seconds"]),
            )
            record(
                "mean-still-fails",
                Decimal(c["preserved_failures"]["target_mean"])
                > Decimal(c["preserved_failures"]["target_mean_limit"]),
            )
            record(
                "two-reserves-not-reset",
                costs["b4_30_full_reserves_seconds"] == ["180", "180"]
                and len(costs["full_cost_categories"]) == 16,
            )
        record(
            "fit-not-measured",
            c["full_training_memory"]["full_training_status"] == "PENDING"
            and c["full_training_memory"]["fit_cap_bytes"] == 4294967296
            and len(c["full_training_memory"]["complete_simultaneous_categories"]) == 8,
        )
        for invalid in ['{"x":1,"x":2}', '{"x":{"a":1,"a":2}}', '{"x":NaN}', '{"x":-Infinity}']:
            try:
                parse(invalid)
            except ValueError:
                record("JSON-rejection:" + invalid, True)
            else:
                record("JSON-rejection:" + invalid, False)
        for name in FIELDS:
            for alteration in ["extra", "removed"]:
                changed = json.loads(json.dumps(c))
                target = changed[name] if name else changed
                if alteration == "extra":
                    target["unregistered"] = None
                else:
                    del target[next(iter(target))]
                try:
                    schema(changed)
                except (KeyError, ValueError):
                    record("schema-rejection:" + name + ":" + alteration, True)
                else:
                    record("schema-rejection:" + name + ":" + alteration, False)
        record(
            "no-real-budget",
            c["real_values_and_new_arithmetic_evaluated"] is False
            and c["new_production_budget_or_reserve"] == "NONE_TEXT_ONLY",
        )
        record("publish13", len(c["allowed_publish_paths"]) == 13)
        record(
            "successor-unstarted",
            c["next_proposed"]
            == "B4.45 bounded public launch-context and immutable-receipt preflight software"
            and not c["next_authorized"]
            and not c["next_started"],
        )
    except (ValueError, KeyError, OSError, AssertionError, TypeError) as exc:
        failure = repr(exc)
    result = {
        "passed": failure is None,
        "predicates": len(facts),
        "checks": facts,
        "error": failure,
        "read_paths": accessed,
        "input_bytes": total_bytes,
        "remaining_if_failed": "UNKNOWN_NOT_EVALUATED" if failure else None,
        "at_utc": datetime.now(UTC).isoformat(),
        "scope": "TEXT_HASH_AST_AND_COMPACT_METADATA_ONLY",
        "primary_program_or_receipt_read": False,
        "old_producer_controller_failure_log_read": False,
        "candidate_or_shared_helper_imported": False,
        "numerical_value_evaluated": False,
        "production_attempts": 0,
        "formal_retry": False,
    }
    with destination.open("x") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(
        json.dumps(
            {name: value for name, value in result.items() if name not in ["checks", "read_paths"]}
        )
    )
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
