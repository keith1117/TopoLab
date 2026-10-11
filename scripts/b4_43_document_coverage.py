"""New B4.43 document coverage only; never reruns the failed B4.42 checker."""

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


def _parse(raw):
    def reject(value):
        raise ValueError(value)

    return json.loads(raw, object_pairs_hook=_unique, parse_constant=reject)


def review(root, external):
    checks = {}

    def check(name, truth):
        assert name not in checks
        checks[name] = bool(truth)
        if not truth:
            raise ValueError(name)

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    try:
        c = _parse(
            (
                root / "docs/planning/b4_43_public_assembled_residual_enclosure_contract.json"
            ).read_bytes()
        )
        old = _parse(
            (
                root
                / "docs/planning/b4_42_public_enclosure_limitations_real_assembly_contract.json"
            ).read_bytes()
        )
        older = _parse(
            (
                root
                / (
                    "docs/planning/"
                    "b4_40_constructed_witness_limitations_real_representation_contract.json"
                )
            ).read_bytes()
        )
        f = _parse((external / "preregistration_freeze.json").read_bytes())
        d = c["document_coverage"]
        check(
            "new-single-public-slice",
            c["slice_limit"] == 1 and c["scope"] == "bounded-authored-public-software-only",
        )
        check(
            "freeze-before-checker-and-arithmetic",
            f["before_document_checker_implementation"]
            and f["before_new_arithmetic_implementation"]
            and f["before_all_formal_calls"],
        )
        check(
            "new-arithmetic-not-implemented",
            not (root / "src/topolab/assembled_residual.py").exists(),
        )
        for name, value in f["frozen"].items():
            check("frozen:" + name, digest(root / name) == value)
        for name, value in c["source_inputs_at_starting_main_sha256"].items():
            raw = subprocess.check_output(
                ["git", "show", c["starting_main"] + ":" + name], cwd=root
            )
            check("starting-text:" + name, hashlib.sha256(raw).hexdigest() == value)
        for name, value in c["closed_recovery_metadata_sha256"].items():
            check("literal-closure:" + name, digest(external.parent / name) == value)
        for name in (
            "future_criteria_unchanged",
            "preserved_failures",
            "preserved_cost",
            "full_training_memory",
        ):
            check("entire-inherited:" + name, c[name] == old[name] == older[name])
        check(
            "old-checker-immutable",
            digest(Path(d["primary_source_literal"])) == d["primary_source_sha256"],
        )
        check(
            "old-receipt-immutable",
            digest(Path(d["primary_receipt_literal"])) == d["primary_receipt_sha256"],
        )
        failed = _parse(Path(d["primary_receipt_literal"]).read_bytes())
        check(
            "old-FAIL-incomplete-no-retry",
            not failed["passed"]
            and failed["predicates"] == 196
            and sum(bool(row[1]) for row in failed["checks"]) == 195
            and failed["error"] == "ValueError('boundary:real_certificate_status')"
            and not d["prior_retry_authorized"]
            and d["prior_primary_incomplete"],
        )
        check(
            "FULL-status-unchanged",
            d["prior_full_status"]
            == old["real_certificate_status"]
            == older["real_certificate_status"]
            == c["real_certificate_status"],
        )
        for name, value in d["remaining_boundary_values"].items():
            check("remaining-boundary:" + name, old[name] == value)
        check(
            "remaining-static-caps",
            old["static_audits"] == d["remaining_static_audits"]
            and old["static_audits"]["primary_max_predicates"] == 380
            and old["static_audits"]["independent_max_predicates"] == 320,
        )
        check(
            "remaining-old11-paths",
            old["allowed_publish_paths"] == d["remaining_publish_paths"]
            and len(d["remaining_publish_paths"]) == 11,
        )
        check(
            "remaining-old-successor",
            old["next_proposed"]
            == (
                "B4.43 bounded public assembled-operator and "
                "intended-residual enclosure software evidence"
            )
            and not old["next_started"]
            and not old["next_authorized"],
        )
        text = " ".join(
            (root / "docs/planning/b4_42_public_enclosure_limitations_real_assembly_protocol.md")
            .read_text()
            .split()
        )
        for token in d["remaining_protocol_tokens"]:
            check("remaining-protocol:" + token, token in text)
        for name in d["remaining_source_imports"]:
            tree = ast.parse((root / name).read_text())
            for index, node in enumerate(ast.walk(tree)):
                modules = (
                    [node.module]
                    if isinstance(node, ast.ImportFrom)
                    else [item.name for item in node.names]
                    if isinstance(node, ast.Import)
                    else []
                )
                if modules:
                    check(
                        "remaining-stdlib:" + name + ":" + str(index),
                        all(m and m.split(".")[0] in sys.stdlib_module_names for m in modules),
                    )
        for raw in ('{"x":1,"x":2}', '{"x":{"y":1,"y":2}}', '{"x":NaN}', '{"x":Infinity}'):
            try:
                _parse(raw)
            except ValueError:
                check("remaining-JSON:" + raw, True)
            else:
                check("remaining-JSON:" + raw, False)
        check("old-closed-root", set(old) == set(older) | {"assembly_preregistration"})
        for field in d["remaining_schema_denials"]:
            target = old if field == "root" else old[field]
            altered = dict(target, unexpected=False)
            check("remaining-schema-denial:" + field, set(altered) != set(target))
        for name in (
            "production_execution",
            "real_payload_fem_projection_root_network_integration",
            "fit_profile_retime_search",
            "screen_final_fresh_unused_access",
            "software_peak_fills_old_gap",
            "fixed_p17_repaired",
            "next_started",
            "next_authorized",
        ):
            check("new-no-grant:" + name, c[name] is False)
        check(
            "new-once-caps",
            d["new_document_primary_invocations"] == d["new_document_independent_invocations"] == 1
            and d["each_document_max_predicates"] == 500
            and d["decimal_precision"] == 50,
        )
        check(
            "old-failure-not-replaced",
            d["new_coverage_does_not_change_old_gate"]
            and d["prior_gate"] == "FAIL_PRIMARY_CHECKER"
            and c["scientific_gate"] == "FAIL",
        )
        check("coverage-cap", len(checks) < 500)
        passed, error = True, None
    except Exception as exc:
        passed, error = False, repr(exc)
    return {
        "passed": passed,
        "checks": checks,
        "predicates": len(checks),
        "error": error,
        "scope": "B4.43 new documentary coverage; B4.42 FAIL retained; no arithmetic",
        "new_arithmetic_evaluated": False,
        "production_attempts": 0,
    }


if __name__ == "__main__":
    source, output = map(Path, sys.argv[1:3])
    receipt = review(source, output)
    with (output / "document_coverage_primary.json").open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "checks"}))
    sys.exit(0 if receipt["passed"] else 1)
