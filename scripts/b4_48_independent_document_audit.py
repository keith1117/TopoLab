"""Separate B4.48 stdlib documentary audit; never read primary code or receipt."""

import ast
import hashlib
import json
import os
import sys
import traceback
from collections import Counter
from decimal import Decimal, localcontext
from pathlib import Path

ROOT_NAMES = frozenset(
    "version authority starting_main slice_limit scope source_inputs_at_starting_main_sha256 "
    "primary_only_source_text_sha256 external_text_metadata_sha256 role_access document_audits "
    "limitations real_certification_bridge stops b4_47_retained new_production_budget_or_reserve "
    "real_values_and_new_arithmetic_evaluated allowed_publish_paths software_cost_policy "
    "next_proposed next_authorized next_started boundaries future_criteria_unchanged "
    "preserved_failures preserved_cost full_training_memory real_prerequisites "
    "public_evidence_retained b4_44_retained b4_45_retained b4_46_retained".split()
)


def object_from(text):
    def unique(items):
        keys = [k for k, _ in items]
        if len(set(keys)) != len(keys):
            raise ValueError("repeated JSON name")
        return dict(items)

    def reject_constant(value):
        raise ValueError(value)

    result = json.loads(text, object_pairs_hook=unique, parse_constant=reject_constant)
    if not isinstance(result, dict):
        raise ValueError("JSON object required")
    return result


def contract_shape(value):
    if frozenset(value) != ROOT_NAMES:
        raise ValueError("root fields differ")
    if type(value["slice_limit"]) is not int or value["slice_limit"] != 1:
        raise ValueError("single slice")
    if any(
        value[k] is not False
        for k in ("next_started", "next_authorized", "real_values_and_new_arithmetic_evaluated")
    ):
        raise ValueError("scope expansion")
    if sorted(value["role_access"]) != ["independent", "primary"]:
        raise ValueError("role set")
    for name, count, letter, words in (
        ("limitations", 20, "L", "id text scope"),
        ("real_certification_bridge", 12, "R", "id name text status"),
        ("real_prerequisites", 24, "O", "id name text status"),
        ("stops", 16, "S", "id trigger disposition alternative_or_retry"),
    ):
        rows = value[name]
        if type(rows) is not list or len(rows) != count:
            raise ValueError("row count")
        if [x.get("id") for x in rows] != [letter + str(i).zfill(2) for i in range(1, count + 1)]:
            raise ValueError("row order")
        for row in rows:
            if set(row) != set(words.split()):
                raise ValueError("row fields")
            for k, v in row.items():
                if k == "alternative_or_retry":
                    if v is not False:
                        raise ValueError("no alternative")
                elif type(v) is not str or not v:
                    raise ValueError("nonempty text")
    for key, number in (
        ("source_inputs_at_starting_main_sha256", 30),
        ("external_text_metadata_sha256", 4),
        ("primary_only_source_text_sha256", 4),
    ):
        refs = value[key]
        if type(refs) is not dict or len(refs) != number:
            raise ValueError("bounded references")
        for path, digest in refs.items():
            if path.startswith("/") or any(p in ("", ".", "..") for p in path.split("/")):
                raise ValueError("relative literal path only")
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
            ):
                raise ValueError("digest spelling")


def run():
    bundle, contract_file, protocol_file, program_freeze, output = [Path(x) for x in sys.argv[1:]]
    assertions, opened = [], []
    input_size = 0

    def accept(label, value):
        assertions.append({"id": label, "passed": value is True})
        if value is not True or len(assertions) > 900:
            raise ValueError("independent condition " + label)

    def consume(path):
        nonlocal input_size
        if path.absolute() != path.resolve() or path.is_symlink():
            raise ValueError("redirect refused")
        with path.open("rb") as stream:
            content = stream.read(1048577)
        input_size += len(content)
        if input_size > 8388608 or len(content) > 1048576:
            raise ValueError("text size limit")
        opened.append(
            {
                "path": str(path),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
        return content.decode("utf-8")

    failure = None
    try:
        frozen = object_from(consume(program_freeze))
        text = consume(contract_file)
        accept(
            "contract preregistered",
            hashlib.sha256(text.encode()).hexdigest() == frozen["contract_sha256"],
        )
        c = object_from(text)
        contract_shape(c)
        accept("registered closed contract", True)
        protocol_text = consume(protocol_file)
        accept(
            "protocol preregistered",
            hashlib.sha256(protocol_text.encode()).hexdigest() == frozen["protocol_sha256"],
        )
        program = consume(Path(__file__).resolve())
        accept(
            "independent bytes frozen",
            hashlib.sha256(program.encode()).hexdigest() == frozen["programs"][Path(__file__).name],
        )
        accept(
            "independent runtime frozen",
            sys.executable == frozen["sys_executable"] and sys.version == frozen["sys_version"],
        )
        imports = []
        for node in ast.walk(ast.parse(program)):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        accept(
            "independent stdlib only",
            all(x.split(".")[0] in sys.stdlib_module_names for x in imports),
        )
        accept("no shared imports", not any("b4_" in x or x.startswith("topolab") for x in imports))
        texts = {}
        # The primary-only reference group is deliberately never materialized here.
        for group in ("source_inputs_at_starting_main_sha256", "external_text_metadata_sha256"):
            for name in sorted(c[group]):
                value = consume(bundle / name)
                accept(
                    "bound text " + name,
                    hashlib.sha256(value.encode()).hexdigest() == c[group][name],
                )
                texts[name] = value
        old = object_from(texts["docs/planning/b4_47_public_arithmetic_campaign_contract.json"])
        inherited = (
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
        )
        for key in inherited:
            accept("exact complete object " + key, c[key] == old[key])
        for key in sorted(old["boundaries"]):
            accept("exact boundary " + key, c["boundaries"][key] == old["boundaries"][key])
        expected_status = "TEXT_ONLY_OBLIGATION; UNKNOWN_STOP; UNIMPLEMENTED_UNEVALUATED"
        for table in ("real_certification_bridge", "real_prerequisites"):
            for row in c[table]:
                accept("unresolved " + row["id"], row["status"] == expected_status)
                accept("text " + row["id"], len(row["text"]) > 60)
        for row in c["limitations"]:
            accept(
                "public limitation " + row["id"],
                row["scope"] == "PUBLIC_ARITHMETIC_LIMITATION_TEXT_ONLY",
            )
        for row in c["stops"]:
            accept(
                "stop " + row["id"],
                row["alternative_or_retry"] is False
                and row["disposition"] == "STOP_PRESERVE_FAILURE_UNKNOWN_COST",
            )
        by_name = {r["name"]: r["text"] for r in c["real_certification_bridge"]}
        for name, terms in (
            ("accepted-identity", ("SAME", "bits", "free space", "cast")),
            ("intended-energy", ("Voigt", "PSD", "quadrature", "scatter")),
            ("representation-errors", ("BOTH", "complete delta", "no assumed")),
            ("actual-assembly-force", ("SIMP", "both triangles", "beta_G/beta_K/beta_f")),
            ("actual-residual-norm", ("SAME", "beta_eval/q_hat/u_plus", "rounded zero")),
            ("fixed-coercivity", ("eta_plus<1", "M_plus>0", "STOP", "no witness/precision/order")),
            ("anchor-normalizer", ("SAME stored C_s_minus", "diagnostics", "loss/gradient")),
            ("independent-fidelity", ("candidate-free", "two-step FD/LOCAL", "P17")),
            ("complete-paid-cost", ("all16", "200 FULL", "UNKNOWN", "7200")),
            ("simultaneous-memory", ("all8", "8*m*m", "4294967296", "through-exit")),
            ("real-release-authority", ("new owner", "clean locked merged", "no real execution")),
            ("future-public-only", ("B4.49", "first freeze", "no B4.47/B4.43 retry")),
        ):
            accept("bridge meaning " + name, all(word in by_name[name] for word in terms))
        release = object_from(texts["b4-47-software-validation/final_release_closure.json"])
        public = object_from(texts["b4-47-software-validation/closed_formal_public_resource.json"])
        controls = object_from(
            texts["b4-47-software-validation/closed_formal_controls_resource.json"]
        )
        lineage = object_from(texts["b4-47-software-validation/outer_pending_lineage_close.json"])
        accept(
            "actual prior release",
            release["closed"] is True and release["final_main"] == c["starting_main"],
        )
        accept(
            "closed once quotas",
            release["formal_quotas"] == [1, 1, 1] and release["formal_retry"] is False,
        )
        for key, value in {
            "formal_gate": "PASS_FRESH_PUBLIC_ARITHMETIC_ONLY",
            "scientific_gate": "FAIL",
            "case_audits": 10,
            "predicates": 4328,
            "RN_even_proofs": 104,
            "whole_software_cost_peak": "UNKNOWN_NOT_ZERO",
            "fixed_p17_repaired": False,
            "sealed_evidence_grant": False,
            "real_certificate_cost": "UNKNOWN_STOP",
        }.items():
            accept("old closure " + key, release[key] == value)
        accept("public panel complete", public["case_audits"] == len(public["case_results"]) == 10)
        accept(
            "proof counts",
            public["independent_predicates"] == 4328 and public["RN_even_proofs"] == 104,
        )
        panel_status = Counter(row["expected_status"] for row in old["catalog"])
        accept(
            "fixed public panel dispositions",
            panel_status == {"PASS": 5, "STOP_SIGN": 2, "STOP_ARITHMETIC": 3},
        )
        for key, expected in (
            ("cases", 10),
            ("enclosures", 5),
            ("sign_stops", 2),
            ("range_stops", 3),
            ("case_audits", 10),
            ("independent_predicates", 4328),
            ("RN_even_proofs", 104),
            ("formal_calls", [1, 1, 1]),
            ("formal_retry", False),
            ("explicit_producer_case_file_reads", 20),
        ):
            accept("B4.47 retained " + key, c["b4_47_retained"][key] == expected)
        accept(
            "retained control FAIL",
            controls["exact_exit7_observed"] is True and controls["formal_retry"] is False,
        )
        accept(
            "lineage not authentication",
            lineage["authenticated_provenance_or_hostile_concurrency_claim"] is False,
        )
        with localcontext() as context:
            context.prec = 50
            cost = c["preserved_cost"]
            amounts = [
                Decimal(cost["known_actual_stage_components_seconds"][k])
                for k in sorted(cost["known_actual_stage_components_seconds"])
            ]
            paid = sum(amounts, Decimal(0))
            accept("full paid Decimal recomputation", paid == Decimal("12721.16417100014444982"))
            accept(
                "infeasible without reset",
                paid > Decimal(cost["old_proxy_cap_seconds"]) == Decimal(7200),
            )
            accept(
                "old FULL reserves",
                sum(map(Decimal, cost["b4_30_full_reserves_seconds"])) == Decimal(360),
            )
            accept(
                "old failure charged",
                Decimal(cost["b4_30_failed_prefix_seconds"]) == Decimal("191.9666532080154866"),
            )
            accept(
                "Q31 separately once",
                Decimal(cost["b4_31_campaign_plus_review_seconds"])
                - Decimal(cost["b4_30_immutable_seconds"])
                == Decimal(cost["b4_31_seconds"]),
            )
            accept(
                "old public native cap only",
                Decimal(public["whole_formal_first_failure_inclusive_seconds"]) == Decimal("5.59"),
            )
        accept(
            "public RSS only", public["conservative_all_formal_profile_rss_sum_bytes"] == 417693696
        )
        accept(
            "complete symbolic storage",
            "8*m*m" in by_name["simultaneous-memory"]
            and "16*m*n" in by_name["simultaneous-memory"],
        )
        accept("no paid grant", c["new_production_budget_or_reserve"] == "NONE_TEXT_ONLY")
        accept(
            "once role caps",
            c["document_audits"]["invocations_per_role"] == 1
            and c["document_audits"]["formal_retry"] is False,
        )
        forbidden_paths = {str(bundle / n) for n in c["primary_only_source_text_sha256"]}
        accept(
            "independent role read set",
            not (forbidden_paths & {x["path"] for x in opened}) and len(texts) == 34,
        )
        for bad in ('{"x":0,"x":1}', '{"x":Infinity}', "[0]"):
            try:
                object_from(bad)
            except ValueError:
                accept("decoder rejects " + bad, True)
            else:
                accept("decoder rejects " + bad, False)
        for key in ("next_authorized", "slice_limit", "extra"):
            mutated = dict(c)
            mutated[key] = True
            try:
                contract_shape(mutated)
            except ValueError:
                accept("closed schema rejects " + key, True)
            else:
                accept("closed schema rejects " + key, False)
    except Exception as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    result = {
        "role": "independent",
        "passed": failure is None,
        "gate": "PASS_TEXT_ONLY" if failure is None else "FAIL_TEXT_AUDIT",
        "predicates": assertions,
        "reads": opened,
        "input_bytes": input_size,
        "failure": failure,
        "candidate_imports": 0,
        "numerical_calls": 0,
        "formal_retry": False,
    }
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(
        json.dumps(
            {
                "passed": failure is None,
                "predicates": len(assertions),
                "input_bytes": input_size,
                "failure": failure,
            }
        )
    )
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
