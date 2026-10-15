"""B4.50 primary TEXT/hash/AST review; never import or evaluate a candidate."""

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
    "limitations combined_real_prerequisites stops b4_49_retained new_production_budget_or_reserve "
    "real_values_and_new_arithmetic_evaluated allowed_publish_paths software_cost_policy "
    "next_proposed next_started next_authorized boundaries future_criteria_unchanged "
    "preserved_failures preserved_cost full_training_memory real_prerequisites "
    "real_certification_bridge public_evidence_retained b4_44_retained b4_45_retained "
    "b4_46_retained b4_47_retained b4_48_retained".split()
)


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def constant(value):
        raise ValueError("nonfinite " + value)

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    if type(value) is not dict:
        raise ValueError("object required")
    return value


def shape(c):
    if set(c) != FIELDS or type(c["slice_limit"]) is not int or c["slice_limit"] != 1:
        raise ValueError("closed single-slice contract")
    if any(
        c[k] is not False
        for k in ("next_started", "next_authorized", "real_values_and_new_arithmetic_evaluated")
    ):
        raise ValueError("scope expansion")
    for key, count in (
        ("source_inputs_at_starting_main_sha256", 36),
        ("primary_only_source_text_sha256", 4),
        ("external_text_metadata_sha256", 3),
    ):
        if type(c[key]) is not dict or len(c[key]) != count:
            raise ValueError("bounded path population")
        for name, digest in c[key].items():
            if name.startswith("/") or any(x in ("", ".", "..") for x in name.split("/")):
                raise ValueError("literal relative paths")
            if (
                type(digest) is not str
                or len(digest) != 64
                or set(digest) - set("0123456789abcdef")
            ):
                raise ValueError("SHA256 spelling")
    for table, count, letter, keys in (
        ("limitations", 22, "L", "id text scope"),
        ("combined_real_prerequisites", 14, "C", "id name text status"),
        ("real_prerequisites", 24, "O", "id name text status"),
        ("real_certification_bridge", 12, "R", "id name text status"),
        ("stops", 16, "S", "id trigger disposition alternative_or_retry"),
    ):
        rows = c[table]
        if type(rows) is not list or len(rows) != count:
            raise ValueError("row population")
        for i, row in enumerate(rows, 1):
            if set(row) != set(keys.split()) or row["id"] != f"{letter}{i:02}":
                raise ValueError("row schema or identity")
            for key, value in row.items():
                if key == "alternative_or_retry":
                    if value is not False:
                        raise ValueError("no alternatives")
                elif type(value) is not str or not value:
                    raise ValueError("nonempty text")


def main():
    bundle, contract, protocol, freeze, output = map(Path, sys.argv[1:])
    # Reserve before input reads; existing destinations never get overwritten.
    with output.open("x") as stream:
        checks, reads, total = [], [], 0

        def check(label, condition):
            checks.append({"id": label, "passed": condition is True})
            if condition is not True or len(checks) > 900:
                raise ValueError(label)

        def read(path):
            nonlocal total
            if path.is_symlink() or path.absolute() != path.resolve():
                raise ValueError("redirected input")
            with path.open("rb") as source:
                raw = source.read(1048577)
            total += len(raw)
            if len(raw) > 1048576 or total > 8388608:
                raise ValueError("input cap")
            reads.append(
                {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            )
            return raw

        failure = None
        try:
            f = decode(read(freeze))
            raw = read(contract)
            check("contract frozen first", hashlib.sha256(raw).hexdigest() == f["contract_sha256"])
            c = decode(raw)
            shape(c)
            check("closed contract shape", True)
            prose = read(protocol).decode()
            check(
                "protocol frozen first",
                hashlib.sha256(prose.encode()).hexdigest() == f["protocol_sha256"],
            )
            program = read(Path(__file__).resolve()).decode()
            check(
                "own source frozen",
                hashlib.sha256(program.encode()).hexdigest() == f["programs"][Path(__file__).name],
            )
            check(
                "declared runtime",
                sys.executable == f["sys_executable"]
                and sys.version == f["sys_version"]
                and str(Path.cwd()) == f["cwd"]
                and sys.flags.isolated == 1,
            )
            check("declared bundle", str(bundle) == f["bundle"])
            texts = {}
            for group in (
                "source_inputs_at_starting_main_sha256",
                "external_text_metadata_sha256",
                "primary_only_source_text_sha256",
            ):
                for name, digest in c[group].items():
                    value = read(bundle / name)
                    check("bound " + name, hashlib.sha256(value).hexdigest() == digest)
                    texts[name] = value.decode()
            old = decode(
                texts["docs/planning/b4_49_public_combined_diagnostic_certificate_contract.json"]
            )
            for key in (
                "future_criteria_unchanged",
                "preserved_failures",
                "preserved_cost",
                "full_training_memory",
                "boundaries",
                "real_prerequisites",
                "real_certification_bridge",
                "public_evidence_retained",
                "b4_44_retained",
                "b4_45_retained",
                "b4_46_retained",
                "b4_47_retained",
                "b4_48_retained",
            ):
                check("entire inherited " + key, c[key] == old[key])
            for name, value in old["boundaries"].items():
                check("boundary " + name, c["boundaries"][name] == value)
            check(
                "exact authority",
                c["starting_main"] == "a375c111b70ebfff5281dfb1262859014034316d"
                and c["scope"] == "BOUNDED_READ_ONLY_TEXT_AND_LITERAL_COMPACT_METADATA_ONLY",
            )
            check(
                "role separation",
                set(c["role_access"]) == {"primary", "independent"}
                and "NEVER primary-only" in c["role_access"]["independent"],
            )
            for row in c["limitations"]:
                check(
                    row["id"],
                    row["scope"] == "PUBLIC_COMBINED_CERTIFICATE_LIMITATION_TEXT_ONLY"
                    and len(row["text"]) > 80,
                )
            for table in (
                "combined_real_prerequisites",
                "real_prerequisites",
                "real_certification_bridge",
            ):
                for row in c[table]:
                    check(
                        row["id"] + " unresolved",
                        row["status"]
                        == "TEXT_ONLY_OBLIGATION; UNKNOWN_STOP; UNIMPLEMENTED_UNEVALUATED",
                    )
            for row in c["stops"]:
                check(
                    row["id"],
                    row["disposition"] == "STOP_PRESERVE_FAILURE_UNKNOWN_COST"
                    and row["alternative_or_retry"] is False,
                )
            conditions = {row["name"]: row["text"] for row in c["combined_real_prerequisites"]}
            for name, terms in (
                ("accepted-identity", ("SAME", "bits", "free space", "cast")),
                ("intended-energy", ("Voigt", "each element PSD", "quadrature", "24-DOF")),
                ("both-factor-errors", ("BOTH", "complete", "cross/square", "no assumed")),
                (
                    "actual-assembly-load",
                    ("SIMP", "CSR-CSC", "BOTH", "beta_G/beta_K/beta_f", "DISTINCT"),
                ),
                ("solver-residual-norm", ("beta_eval/q_hat/u_plus", "EVERY", "direct intended")),
                (
                    "one-construction",
                    ("ONE", "eta_plus<1", "M_plus>0", "STOP", "no witness/precision/order"),
                ),
                ("force-energy", ("SAME-force", "f+r", "tiny nonzero", "unmodified U")),
                ("same-normalizer", ("SAME stored C_s_minus", "continuous", "never replace")),
                (
                    "diagnostic-and-fidelity",
                    ("diagnostics only", "loss/gradient/intercept", "two-step FD/LOCAL", "P17"),
                ),
                (
                    "independent-proof",
                    ("candidate-free", "once-only", "never discharges", "quotas"),
                ),
                ("real-release", ("new owner", "clean locked merged", "no real execution")),
                (
                    "all-paid-cost",
                    ("all16", "BOTH FULL180", "200 FULL", "UNKNOWN", "7200", "no cap/ledger reset"),
                ),
                (
                    "simultaneous-memory",
                    ("all8", "through-exit", "16*m*n", "8*m*m", "4294967296", "PENDING"),
                ),
                ("fixed-stops", ("before outcomes", "UNKNOWN", "STOP", "without fallback")),
            ):
                check("meaning " + name, all(t in conditions[name] for t in terms))
            closure = decode(texts["b4-49-software-validation/final_release_closure.json"])
            resource = decode(
                texts["b4-49-software-validation/closed_formal_combined_resource.json"]
            )
            annex = decode(texts["b4-49-software-validation/final_backup_annex_manifest.json"])
            for key, value in {
                "closed": True,
                "final_main": c["starting_main"],
                "formal_calls": [1, 1],
                "formal_retry": False,
                "scientific_gate": "FAIL",
                "fixed_p17_repaired": False,
                "formal_gate": "PASS_PUBLIC_COMBINED_DIAGNOSTIC_ONLY",
                "formal_case_audits": 12,
                "formal_predicates": 6059,
                "RN_even_proofs": 455,
                "fixed80_root_proofs": 143,
                "full_pytest_source": 1951,
                "all_applicable_exact_head_main_CI_passed": True,
                "whole_software_cost_peak": "UNKNOWN_NOT_ZERO",
                "real_certificate_cost": "UNKNOWN_STOP",
                "real_executable": "UNFROZEN",
                "full_fit_memory": "PENDING4GiB",
                "sealed_grant": False,
            }.items():
                check("literal closure " + key, closure[key] == value)
            check(
                "metadata source identity",
                resource["source"] == closure["source_main"]
                and resource["formal_calls"] == [1, 1]
                and resource["retry"] is False,
            )
            check(
                "closed proof counters",
                resource["cases_completed"] == resource["case_audits"] == 12
                and resource["predicates"] == 6059
                and resource["RN_even_proofs"] == 455
                and resource["fixed80_root_proofs"] == 143,
            )
            for key, value in (
                ("cases", 12),
                ("certificates", 5),
                ("prescribed_stops", 7),
                ("case_audits", 12),
                ("independent_predicates", 6059),
                ("RN_even_proofs", 455),
                ("fixed80_root_proofs", 143),
                ("formal_calls", [1, 1]),
                ("formal_retry", False),
                ("focused_tests", 51),
                ("source_full_tests", 1951),
            ):
                check("retained " + key, c["b4_49_retained"][key] == value)
            expected = Counter(
                {
                    "PASS": 5,
                    "STOP_PSD": 1,
                    "STOP_ETA": 1,
                    "STOP_COERCIVITY": 1,
                    "STOP_NORMALIZER": 1,
                    "STOP_NORMALIZER_IDENTITY": 1,
                    "STOP_RANGE": 2,
                }
            )
            check(
                "full frozen public dispositions",
                Counter(x["expected_status"] for x in old["catalog"]) == expected,
            )
            for original, entry in annex.items():
                check(
                    "annex literal " + original,
                    set(entry) == {"copy", "sha256"}
                    and len(entry["sha256"]) == 64
                    and entry["copy"].startswith(closure["backup_root"] + "/"),
                )
            check(
                "annex closure bytes",
                annex[
                    "/Users/keith1117/Documents/TopoLab-data/b4-49-software-validation/final_release_closure.json"
                ]["sha256"]
                == c["external_text_metadata_sha256"][
                    "b4-49-software-validation/final_release_closure.json"
                ],
            )
            with localcontext() as context:
                context.prec = 50
                cost = c["preserved_cost"]
                paid = sum(
                    (Decimal(x) for x in cost["known_actual_stage_components_seconds"].values()),
                    Decimal(0),
                )
                check(
                    "paid exact sum",
                    paid
                    == Decimal(cost["cross_route_known_paid_floor_seconds"])
                    == Decimal("12721.16417100014444982"),
                )
                check(
                    "paid infeasible",
                    paid > Decimal(cost["old_proxy_cap_seconds"]) == Decimal(7200),
                )
                check(
                    "Q31 once",
                    Decimal(cost["b4_30_immutable_seconds"]) + Decimal(cost["b4_31_seconds"])
                    == Decimal(cost["b4_31_campaign_plus_review_seconds"]),
                )
                check(
                    "both FULL reserves",
                    list(map(Decimal, cost["b4_30_full_reserves_seconds"])) == [Decimal(180)] * 2,
                )
                check(
                    "old failed prefix",
                    Decimal(cost["b4_30_failed_prefix_seconds"]) == Decimal("191.9666532080154866"),
                )
                check(
                    "preparation full coefficients",
                    [3 * Decimal("1.25") * n for n in (432, 76)]
                    == list(map(Decimal, cost["preparation_coefficients"])),
                )
                check(
                    "epochs full coefficients",
                    [3 * 200 * Decimal("1.25") * n for n in (432, 76)]
                    == list(map(Decimal, cost["forward_backward_coefficients"])),
                )
                profiles = resource["profiles"]
                check(
                    "native outer sum only",
                    sum(
                        (
                            Decimal(profiles[n]["real"])
                            for n in ("primary_outer", "independent_outer")
                        ),
                        Decimal(0),
                    )
                    == Decimal(resource["outer_native_wall_sum_seconds"])
                    == Decimal("1.14"),
                )
            check(
                "public conservative RSS only",
                sum(x["rss_bytes"] for x in profiles.values())
                == resource["conservative_all_profile_rss_sum_bytes"]
                == 105283584,
            )
            check(
                "complete categories",
                len(cost["full_cost_categories"]) == 16
                and len(c["full_training_memory"]["complete_simultaneous_categories"]) == 8
                and c["full_training_memory"]["fit_cap_bytes"] == 4294967296,
            )
            for name in c["primary_only_source_text_sha256"]:
                tree = ast.parse(texts[name])
                imports = [
                    a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
                ]
                imports += [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
                check(
                    "static stdlib imports " + name,
                    all(x and x.split(".")[0] in sys.stdlib_module_names for x in imports),
                )
            candidate = texts["src/topolab/combined_certificate.py"]
            for words in (
                ("A_hat_bits", "Y_bits", "u_bits"),
                ("d0_plus", "d1_plus", "complete_delta_plus"),
                ("beta_G", "beta_K", "beta_f", "beta_eval", "q_hat", "u_plus"),
                ("q_eval", "operator_solution", "with_operator", "r_plus"),
                ("C_s_minus", "normalized_B_plus", "unmodified_U_certified"),
            ):
                check(
                    "static retained fields " + words[0], all(word in candidate for word in words)
                )
            check(
                "document caps once",
                c["document_audits"]["invocations_per_role"] == 1
                and c["document_audits"]["formal_retry"] is False
                and c["document_audits"]["each_formal_native_wall_seconds_max"] == 60
                and c["document_audits"]["each_formal_native_rss_bytes_max"] == 268435456,
            )
            check("no production grant", c["new_production_budget_or_reserve"] == "NONE_TEXT_ONLY")
            check(
                "next text only",
                c["next_proposed"].startswith("B4.51 bounded read-only")
                and "full-resource preregistration" in c["next_proposed"],
            )
            check("exact primary read population", len(reads) == 47 and len(texts) == 43)
            for bad in ('{"a":0,"a":1}', '{"a":NaN}', "[]"):
                try:
                    decode(bad)
                except ValueError:
                    check("decoder denial " + bad, True)
                else:
                    check("decoder denial " + bad, False)
            for key in ("slice_limit", "next_started", "unknown"):
                bad = dict(c)
                bad[key] = True
                try:
                    shape(bad)
                except ValueError:
                    check("schema denial " + key, True)
                else:
                    check("schema denial " + key, False)
        except Exception as exc:
            failure = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        result = {
            "role": "primary",
            "passed": failure is None,
            "predicates": checks,
            "reads": reads,
            "input_bytes": total,
            "failure": failure,
            "candidate_imports": 0,
            "numerical_calls": 0,
            "formal_retry": False,
            "gate": "PASS_TEXT_ONLY" if failure is None else "FAIL_TEXT_REVIEW",
        }
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(
        json.dumps(
            {
                "passed": failure is None,
                "predicates": len(checks),
                "reads": len(reads),
                "input_bytes": total,
                "failure": failure,
            }
        )
    )
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
