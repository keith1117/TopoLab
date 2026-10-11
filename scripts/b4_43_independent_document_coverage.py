"""Independent B4.43 text/Decimal audit; no primary source/receipt imports/reads."""

import ast
import hashlib
import json
import subprocess
import sys
from decimal import Decimal, localcontext
from pathlib import Path


def audit(root, output):
    evidence = {}

    def require(name, predicate):
        assert name not in evidence
        evidence[name] = bool(predicate)
        if not predicate:
            raise RuntimeError(name)

    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise RuntimeError("duplicate")
            result[key] = value
        return result

    def invalid(value):
        raise RuntimeError(value)

    def parse(raw):
        return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)

    def read(path):
        return parse(path.read_bytes())

    try:
        c = read(root / "docs/planning/b4_43_public_assembled_residual_enclosure_contract.json")
        old = read(
            root / "docs/planning/b4_42_public_enclosure_limitations_real_assembly_contract.json"
        )
        prior = read(
            root
            / (
                "docs/planning/"
                "b4_40_constructed_witness_limitations_real_representation_contract.json"
            )
        )
        frozen = read(output / "preregistration_freeze.json")
        d = c["document_coverage"]
        require(
            "new-single-public-slice",
            c["slice_limit"] == 1 and c["scope"] == "bounded-authored-public-software-only",
        )
        require(
            "before-any-new-arithmetic",
            not (root / "src/topolab/assembled_residual.py").exists()
            and frozen["before_document_checker_implementation"]
            and frozen["before_new_arithmetic_implementation"],
        )
        for name, digest in frozen["frozen"].items():
            require(
                "frozen:" + name, hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
            )
        for name, digest in c["source_inputs_at_starting_main_sha256"].items():
            committed = subprocess.check_output(
                ["git", "show", c["starting_main"] + ":" + name], cwd=root
            )
            require("starting-text:" + name, hashlib.sha256(committed).hexdigest() == digest)
        for name in (
            "future_criteria_unchanged",
            "preserved_failures",
            "preserved_cost",
            "full_training_memory",
        ):
            require("full-inherited:" + name, c[name] == old[name] == prior[name])
        require(
            "retain-incomplete-FAIL",
            d["prior_gate"] == "FAIL_PRIMARY_CHECKER"
            and d["prior_primary_evaluated"] == 196
            and d["prior_primary_pass"] == 195
            and d["prior_primary_fail"] == 1
            and d["prior_primary_incomplete"]
            and not d["prior_retry_authorized"],
        )
        require(
            "entire-certificate-status",
            c["real_certificate_status"]
            == d["prior_full_status"]
            == old["real_certificate_status"]
            == prior["real_certificate_status"],
        )
        for name, expected in d["remaining_boundary_values"].items():
            require(
                "remaining-boundary:" + name,
                old[name] == expected and type(old[name]) is type(expected),
            )
        require("remaining-old-static", old["static_audits"] == d["remaining_static_audits"])
        require(
            "remaining-old11-paths",
            old["allowed_publish_paths"] == d["remaining_publish_paths"]
            and len(old["allowed_publish_paths"]) == 11,
        )
        require(
            "remaining-successor",
            old["next_proposed"]
            == (
                "B4.43 bounded public assembled-operator and "
                "intended-residual enclosure software evidence"
            )
            and not old["next_authorized"]
            and not old["next_started"],
        )
        text = " ".join(
            (root / "docs/planning/b4_42_public_enclosure_limitations_real_assembly_protocol.md")
            .read_text()
            .split()
        )
        for token in d["remaining_protocol_tokens"]:
            require("remaining-text:" + token, token in text)
        for name in d["remaining_source_imports"]:
            nodes = ast.walk(ast.parse((root / name).read_text()))
            modules = []
            for node in nodes:
                if isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    modules.append(node.module)
            require(
                "remaining-imports:" + name,
                all(m and m.split(".")[0] in sys.stdlib_module_names for m in modules),
            )
        for raw in ('{"a":0,"a":1}', '{"a":{"b":0,"b":1}}', '{"a":NaN}', '{"a":Infinity}'):
            try:
                parse(raw)
            except RuntimeError:
                require("remaining-JSON:" + raw, True)
            else:
                require("remaining-JSON:" + raw, False)
        require("old-closed-root", set(old) == set(prior) | {"assembly_preregistration"})
        for field in d["remaining_schema_denials"]:
            obj = old if field == "root" else old[field]
            require("remaining-closed-denial:" + field, set(dict(obj, unexpected=None)) != set(obj))
        with localcontext() as ctx:
            ctx.prec = 50
            paid = c["preserved_cost"]
            require(
                "immutable-cost-addition",
                Decimal(paid["b4_30_immutable_seconds"]) + Decimal(paid["b4_31_seconds"])
                == Decimal(paid["b4_31_campaign_plus_review_seconds"]),
            )
            require(
                "known-paid-FAIL-no-reset",
                Decimal(paid["cross_route_known_paid_floor_seconds"])
                > Decimal(paid["old_proxy_cap_seconds"])
                and not paid["new_production_budget_granted"],
            )
            require("old-full-reserves", paid["b4_30_full_reserves_seconds"] == ["180", "180"])
        require(
            "all16-cost-all8-memory",
            len(paid["full_cost_categories"]) == 16
            and len(c["full_training_memory"]["complete_simultaneous_categories"]) == 8
            and c["full_training_memory"]["full_training_status"] == "PENDING",
        )
        require(
            "new-finite-doc-calls",
            d["new_document_primary_invocations"] == d["new_document_independent_invocations"] == 1
            and d["each_document_max_predicates"] == 500
            and d["decimal_precision"] == 50,
        )
        require(
            "old-FAIL-not-overwritten",
            d["new_coverage_does_not_change_old_gate"]
            and c["scientific_gate"] == "FAIL"
            and not c["fixed_p17_repaired"]
            and c["uniform_default"]
            and c["final_evidence_sealed"],
        )
        require("coverage-cap", len(evidence) < 500)
        passed, error = True, None
    except Exception as exc:
        passed, error = False, repr(exc)
    return {
        "passed": passed,
        "predicates": len(evidence),
        "checks": evidence,
        "error": error,
        "primary_source_or_receipt_read": False,
        "imports_candidate_or_shared_helpers": False,
        "scope": "independent text/Decimal premises only",
        "new_arithmetic_evaluated": False,
        "production_attempts": 0,
    }


if __name__ == "__main__":
    source, external = map(Path, sys.argv[1:3])
    result = audit(source, external)
    with (external / "document_coverage_independent.json").open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "checks"}))
    sys.exit(0 if result["passed"] else 1)
