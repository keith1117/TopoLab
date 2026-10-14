"""First-only B4.48 TEXT/AST review; no arithmetic or candidate imports."""

import ast
import hashlib
import json
import os
import sys
import traceback
from decimal import Decimal, localcontext
from pathlib import Path

FIELDS = set(
    "version authority starting_main slice_limit scope source_inputs_at_starting_main_sha256 "
    "primary_only_source_text_sha256 external_text_metadata_sha256 role_access document_audits "
    "limitations real_certification_bridge stops b4_47_retained new_production_budget_or_reserve "
    "real_values_and_new_arithmetic_evaluated allowed_publish_paths software_cost_policy "
    "next_proposed next_authorized next_started boundaries future_criteria_unchanged "
    "preserved_failures preserved_cost full_training_memory real_prerequisites "
    "public_evidence_retained b4_44_retained b4_45_retained b4_46_retained".split()
)


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate field")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("nonfinite " + value)

    obj = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    if type(obj) is not dict:
        raise ValueError("object required")
    return obj


def schema(doc):
    if set(doc) != FIELDS or type(doc["slice_limit"]) is not int or doc["slice_limit"] != 1:
        raise ValueError("closed contract schema")
    if set(doc["role_access"]) != {"primary", "independent"}:
        raise ValueError("closed roles")
    for key in ("next_started", "next_authorized", "real_values_and_new_arithmetic_evaluated"):
        if doc[key] is not False:
            raise ValueError("no new execution")
    for key, count, prefix, keys in (
        ("limitations", 20, "L", {"id", "text", "scope"}),
        ("real_certification_bridge", 12, "R", {"id", "name", "text", "status"}),
        ("real_prerequisites", 24, "O", {"id", "name", "text", "status"}),
        ("stops", 16, "S", {"id", "trigger", "disposition", "alternative_or_retry"}),
    ):
        if type(doc[key]) is not list or len(doc[key]) != count:
            raise ValueError("finite table")
        for i, row in enumerate(doc[key], 1):
            if type(row) is not dict or set(row) != keys or row["id"] != f"{prefix}{i:02}":
                raise ValueError("ordered closed row")
            for name, value in row.items():
                if name == "alternative_or_retry":
                    if value is not False:
                        raise ValueError("retry")
                elif type(value) is not str or not value:
                    raise ValueError("text required")
    for group, count in (
        ("source_inputs_at_starting_main_sha256", 30),
        ("primary_only_source_text_sha256", 4),
        ("external_text_metadata_sha256", 4),
    ):
        if type(doc[group]) is not dict or len(doc[group]) != count:
            raise ValueError("closed paths")
        for name, digest in doc[group].items():
            parts = Path(name).parts
            if Path(name).is_absolute() or ".." in parts or not parts:
                raise ValueError("path escape")
            if (
                type(digest) is not str
                or len(digest) != 64
                or set(digest) - set("0123456789abcdef")
            ):
                raise ValueError("sha256")


def emit(path, obj):
    with path.open("x") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def main():
    bound, contract, protocol, freeze_file, receipt = map(Path, sys.argv[1:])
    findings, reads = [], []
    total = 0

    def check(name, passed):
        findings.append({"id": name, "passed": passed is True})
        if len(findings) > 900 or passed is not True:
            raise ValueError("predicate: " + name)

    def read(path):
        nonlocal total
        if path.is_symlink() or path.absolute() != path.resolve():
            raise ValueError("redirected path")
        with path.open("rb") as f:
            raw = f.read(1048577)
        total += len(raw)
        if len(raw) > 1048576 or total > 8388608:
            raise ValueError("byte cap")
        reads.append(
            {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        )
        return raw

    error = None
    try:
        freeze = decode(read(freeze_file))
        raw = read(contract)
        check("contract frozen", hashlib.sha256(raw).hexdigest() == freeze["contract_sha256"])
        doc = decode(raw)
        schema(doc)
        check("closed schema", True)
        raw_protocol = read(protocol)
        check(
            "protocol frozen", hashlib.sha256(raw_protocol).hexdigest() == freeze["protocol_sha256"]
        )
        own = read(Path(__file__).resolve())
        check(
            "own source frozen",
            hashlib.sha256(own).hexdigest() == freeze["programs"][Path(__file__).name],
        )
        check(
            "runtime frozen",
            sys.version == freeze["sys_version"] and sys.executable == freeze["sys_executable"],
        )
        check(
            "source scope",
            doc["scope"] == "BOUNDED_READ_ONLY_TEXT_AND_LITERAL_COMPACT_METADATA_ONLY",
        )
        check("formal quota", doc["document_audits"]["invocations_per_role"] == 1)
        check("no retry", doc["document_audits"]["formal_retry"] is False)
        check(
            "first failure consumes", doc["document_audits"]["first_failure_consumes_quota"] is True
        )
        texts = {}
        for group in (
            "source_inputs_at_starting_main_sha256",
            "external_text_metadata_sha256",
            "primary_only_source_text_sha256",
        ):
            for name, digest in doc[group].items():
                value = read(bound / name)
                check("input hash " + name, hashlib.sha256(value).hexdigest() == digest)
                texts[name] = value.decode("utf-8")
        old = decode(texts["docs/planning/b4_47_public_arithmetic_campaign_contract.json"])
        for key in (
            "future_criteria_unchanged",
            "preserved_failures",
            "preserved_cost",
            "full_training_memory",
            "boundaries",
            "real_prerequisites",
            "public_evidence_retained",
            "b4_44_retained",
            "b4_45_retained",
            "b4_46_retained",
        ):
            check("entire inherited " + key, doc[key] == old[key])
        for key, value in old["boundaries"].items():
            check("boundary " + key, doc["boundaries"][key] == value)
        for table in ("limitations", "real_certification_bridge", "real_prerequisites", "stops"):
            for row in doc[table]:
                check(table + " " + row["id"], bool(row.get("text", row.get("trigger"))))
                if "status" in row:
                    check(
                        "TEXT unresolved " + row["id"],
                        row["status"]
                        == "TEXT_ONLY_OBLIGATION; UNKNOWN_STOP; UNIMPLEMENTED_UNEVALUATED",
                    )
        for i, tokens in {
            8: ("fixed80-bit", "conservative"),
            9: ("completed", "domain rejection", "unexecuted suffix"),
            10: ("UNKNOWN_NOT_INSTRUMENTED", "reads20"),
            11: ("BOTH", "not Gram"),
            12: ("rounded residual zero", "beta_eval"),
            13: ("r_arrays", "r_hat", "r_plus"),
            15: ("PSD/coercivity", "SAME stored", "nonzero"),
            16: ("UNKNOWN_NOT_DIAGNOSED", "quota1/1"),
            18: ("UNKNOWN_NOT_ZERO", "full-fit"),
            20: ("UNFROZEN", "PENDING4GiB"),
        }.items():
            check(
                "limitation meaning " + str(i),
                all(t in doc["limitations"][i - 1]["text"] for t in tokens),
            )
        closure = decode(texts["b4-47-software-validation/final_release_closure.json"])
        public = decode(texts["b4-47-software-validation/closed_formal_public_resource.json"])
        controls = decode(texts["b4-47-software-validation/closed_formal_controls_resource.json"])
        lineage = decode(texts["b4-47-software-validation/outer_pending_lineage_close.json"])
        check(
            "B4.47 closed",
            closure["closed"] is True and closure["final_main"] == doc["starting_main"],
        )
        for key, expected in (
            ("formal_gate", "PASS_FRESH_PUBLIC_ARITHMETIC_ONLY"),
            ("scientific_gate", "FAIL"),
            ("formal_quotas", [1, 1, 1]),
            ("case_audits", 10),
            ("predicates", 4328),
            ("RN_even_proofs", 104),
            ("formal_retry", False),
            ("whole_software_cost_peak", "UNKNOWN_NOT_ZERO"),
            ("real_certificate_cost", "UNKNOWN_STOP"),
            ("real_executable", "UNFROZEN"),
            ("fixed_p17_repaired", False),
            ("sealed_evidence_grant", False),
        ):
            check("closure " + key, closure[key] == expected)
        for key, expected in (
            ("reported_gate", "PASS_FRESH_PUBLIC_ARITHMETIC_ONLY"),
            ("independent_predicates", 4328),
            ("RN_even_proofs", 104),
            ("case_audits", 10),
            ("whole_formal_first_failure_inclusive_seconds", "5.59"),
            ("conservative_all_formal_profile_rss_sum_bytes", 417693696),
            ("old_b4_43_retry_or_runtime_reconstruction", False),
        ):
            check("public compact " + key, public[key] == expected)
        case_rows = public["case_results"]
        check("complete case list", len(case_rows) == 10)
        check(
            "controls negative retained",
            controls["passed"] is True and controls["exact_exit7_observed"] is True,
        )
        check(
            "lineage local only",
            lineage["passed"] is True
            and lineage["authenticated_provenance_or_hostile_concurrency_claim"] is False,
        )
        for name in doc["primary_only_source_text_sha256"]:
            tree = ast.parse(texts[name])
            check("static AST " + name, isinstance(tree, ast.Module))
        with localcontext() as ctx:
            ctx.prec = 50
            costs = doc["preserved_cost"]
            subtotal = sum(
                Decimal(v) for v in costs["known_actual_stage_components_seconds"].values()
            )
            check(
                "paid Decimal subtotal",
                subtotal == Decimal(costs["cross_route_known_paid_floor_seconds"]),
            )
            check("all-paid still FAIL", subtotal > Decimal(costs["old_proxy_cap_seconds"]))
            check(
                "immutable Q31 once",
                Decimal(costs["b4_30_immutable_seconds"]) + Decimal(costs["b4_31_seconds"])
                == Decimal(costs["b4_31_campaign_plus_review_seconds"]),
            )
            check(
                "B4.47 native remains scoped",
                Decimal(public["whole_formal_first_failure_inclusive_seconds"]) <= 240,
            )
        check("all cost categories", len(doc["preserved_cost"]["full_cost_categories"]) == 16)
        check(
            "all memory categories",
            len(doc["full_training_memory"]["complete_simultaneous_categories"]) == 8,
        )
        check("fit cap unchanged", doc["full_training_memory"]["fit_cap_bytes"] == 4294967296)
        check("no production grant", doc["new_production_budget_or_reserve"] == "NONE_TEXT_ONLY")
        for corrupt in ('{"a":1,"a":2}', '{"a":NaN}', "[]"):
            try:
                decode(corrupt)
            except ValueError:
                check("JSON denial " + corrupt, True)
            else:
                check("JSON denial " + corrupt, False)
        for key, value in (("slice_limit", True), ("next_started", True), ("extra", 0)):
            changed = dict(doc)
            changed[key] = value
            try:
                schema(changed)
            except ValueError:
                check("schema denial " + key, True)
            else:
                check("schema denial " + key, False)
    except Exception as exc:
        error = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    emit(
        receipt,
        {
            "role": "primary",
            "passed": error is None,
            "gate": "PASS_TEXT_ONLY" if error is None else "FAIL_TEXT_REVIEW",
            "predicates": findings,
            "reads": reads,
            "input_bytes": total,
            "failure": error,
            "numerical_calls": 0,
            "candidate_imports": 0,
            "formal_retry": False,
        },
    )
    print(
        json.dumps(
            {
                "passed": error is None,
                "predicates": len(findings),
                "input_bytes": total,
                "failure": error,
            }
        )
    )
    if error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
