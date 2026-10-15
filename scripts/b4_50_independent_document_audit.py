"""Independent B4.50 document reconstruction; no primary source/result access."""

import ast
import hashlib
import json
import os
import sys
import traceback
from decimal import Decimal, localcontext
from pathlib import Path

ROOT_KEYS = set(
    "version authority starting_main slice_limit scope source_inputs_at_starting_main_sha256 "
    "primary_only_source_text_sha256 external_text_metadata_sha256 role_access document_audits "
    "limitations combined_real_prerequisites stops b4_49_retained new_production_budget_or_reserve "
    "real_values_and_new_arithmetic_evaluated allowed_publish_paths software_cost_policy "
    "next_proposed next_started next_authorized boundaries future_criteria_unchanged "
    "preserved_failures preserved_cost full_training_memory real_prerequisites "
    "real_certification_bridge public_evidence_retained "
    "b4_44_retained b4_45_retained b4_46_retained b4_47_retained b4_48_retained".split()
)


def object_text(text):
    def unique(pairs):
        names = [key for key, _ in pairs]
        if len(set(names)) != len(names):
            raise ValueError("repeated JSON name")
        return dict(pairs)

    def refuse(word):
        raise ValueError(word)

    obj = json.loads(text, object_pairs_hook=unique, parse_constant=refuse)
    if not isinstance(obj, dict):
        raise ValueError("document object required")
    return obj


def closed_contract(obj):
    if set(obj) != ROOT_KEYS:
        raise ValueError("root field set")
    if type(obj["slice_limit"]) is not int or obj["slice_limit"] != 1:
        raise ValueError("one slice")
    if [
        obj[k] is False
        for k in ("next_started", "next_authorized", "real_values_and_new_arithmetic_evaluated")
    ] != [True, True, True]:
        raise ValueError("scope flag")
    for label, count in {
        "source_inputs_at_starting_main_sha256": 36,
        "primary_only_source_text_sha256": 4,
        "external_text_metadata_sha256": 3,
    }.items():
        paths = obj[label]
        if not isinstance(paths, dict) or len(paths) != count:
            raise ValueError("bounded literal group")
        for name in paths:
            if Path(name).is_absolute() or any(x in (".", "..", "") for x in name.split("/")):
                raise ValueError("literal path")
            if len(paths[name]) != 64 or any(x not in "0123456789abcdef" for x in paths[name]):
                raise ValueError("hash")
    for label, count, prefix, fields in [
        ("limitations", 22, "L", {"id", "text", "scope"}),
        ("combined_real_prerequisites", 14, "C", {"id", "name", "text", "status"}),
        ("real_prerequisites", 24, "O", {"id", "name", "text", "status"}),
        ("real_certification_bridge", 12, "R", {"id", "name", "text", "status"}),
        ("stops", 16, "S", {"id", "trigger", "disposition", "alternative_or_retry"}),
    ]:
        if not isinstance(obj[label], list) or len(obj[label]) != count:
            raise ValueError("row total")
        ids = [prefix + str(i).zfill(2) for i in range(1, count + 1)]
        if [row.get("id") for row in obj[label]] != ids:
            raise ValueError("row identity order")
        for row in obj[label]:
            if set(row) != fields:
                raise ValueError("row fields")
            for field in fields:
                if field == "alternative_or_retry":
                    if row[field] is not False:
                        raise ValueError("no automatic alternatives")
                elif not isinstance(row[field], str) or len(row[field]) == 0:
                    raise ValueError("text field")


def run():
    bundle, contract_path, protocol_path, frozen_path, destination = [Path(s) for s in sys.argv[1:]]
    assertions, opened = [], []
    size = 0
    problem = None
    # Exclusive reservation also refuses a duplicate invocation before reading input.
    with destination.open("x") as report:

        def require(name, truth):
            assertions.append({"id": name, "passed": truth is True})
            if truth is not True or len(assertions) > 900:
                raise ValueError("independent: " + name)

        def take(path):
            nonlocal size
            if path.resolve() != path.absolute() or path.is_symlink():
                raise ValueError("input redirect")
            with path.open("rb") as source:
                content = source.read(1 + 2**20)
            size += len(content)
            if len(content) > 2**20 or size > 8 * 2**20:
                raise ValueError("text byte cap")
            opened.append(
                {
                    "path": str(path),
                    "bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
            return content.decode("utf-8")

        try:
            frozen = object_text(take(frozen_path))
            text = take(contract_path)
            require(
                "preregistered contract",
                hashlib.sha256(text.encode()).hexdigest() == frozen["contract_sha256"],
            )
            c = object_text(text)
            closed_contract(c)
            require("complete schema", True)
            protocol = take(protocol_path)
            require(
                "preregistered protocol",
                hashlib.sha256(protocol.encode()).hexdigest() == frozen["protocol_sha256"],
            )
            own = take(Path(__file__).resolve())
            require(
                "independent source identity",
                hashlib.sha256(own.encode()).hexdigest() == frozen["programs"][Path(__file__).name],
            )
            require(
                "isolated interpreter",
                (sys.executable, sys.version, str(Path.cwd()), sys.flags.isolated)
                == (frozen["sys_executable"], frozen["sys_version"], frozen["cwd"], 1),
            )
            require("separate bundle", str(bundle) == frozen["independent_bundle"])
            modules = []
            for item in ast.walk(ast.parse(own)):
                if isinstance(item, ast.ImportFrom):
                    modules.append(item.module)
                elif isinstance(item, ast.Import):
                    modules.extend(x.name for x in item.names)
            require(
                "stdlib only independent",
                all(x and x.split(".")[0] in sys.stdlib_module_names for x in modules),
            )
            require("no shared imports", not any(x.startswith(("topolab", "b4_")) for x in modules))
            public = {}
            # No primary-only source names are opened, even for hashing or AST.
            for group in ("source_inputs_at_starting_main_sha256", "external_text_metadata_sha256"):
                for name in sorted(c[group]):
                    value = take(bundle / name)
                    require(
                        "literal identity " + name,
                        hashlib.sha256(value.encode()).hexdigest() == c[group][name],
                    )
                    public[name] = value
            before = object_text(
                public["docs/planning/b4_49_public_combined_diagnostic_certificate_contract.json"]
            )
            preserved = [
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
            ]
            for field in preserved:
                require("unchanged whole object " + field, before[field] == c[field])
            for field in sorted(before["boundaries"]):
                require(
                    "unchanged boundary " + field,
                    before["boundaries"][field] == c["boundaries"][field],
                )
            require(
                "starting source", c["starting_main"] == "a375c111b70ebfff5281dfb1262859014034316d"
            )
            require(
                "TEXT only",
                c["scope"] == "BOUNDED_READ_ONLY_TEXT_AND_LITERAL_COMPACT_METADATA_ONLY"
                and c["new_production_budget_or_reserve"] == "NONE_TEXT_ONLY",
            )
            for row in c["limitations"]:
                require(
                    row["id"] + " public limitation",
                    row["scope"] == "PUBLIC_COMBINED_CERTIFICATE_LIMITATION_TEXT_ONLY"
                    and len(row["text"]) >= 80,
                )
            for field in (
                "combined_real_prerequisites",
                "real_prerequisites",
                "real_certification_bridge",
            ):
                for row in c[field]:
                    require(
                        row["id"] + " no real proof",
                        row["status"]
                        == "TEXT_ONLY_OBLIGATION; UNKNOWN_STOP; UNIMPLEMENTED_UNEVALUATED",
                    )
            for row in c["stops"]:
                require(
                    row["id"] + " preserves stop",
                    row["alternative_or_retry"] is False
                    and row["disposition"] == "STOP_PRESERVE_FAILURE_UNKNOWN_COST",
                )
            needs = {row["id"]: row["text"] for row in c["combined_real_prerequisites"]}
            terms = {
                "C01": ["accepted", "zero-Dirichlet", "BEFORE real access"],
                "C02": ["engineering-Voigt", "each element PSD", "gamma has no half-factor"],
                "C03": ["BOTH G-Gram(A0)", "Gram(A0)-Gram(A_hat)", "fixed outward"],
                "C04": ["duplicate sparse", "BOTH triangles", "DISTINCT from Gram delta"],
                "C05": [
                    "SAME accepted solver",
                    "beta_eval/q_hat/u_plus",
                    "EVERY",
                    "direct intended residual",
                ],
                "C06": [
                    "ONE real",
                    "before outcomes",
                    "eta_plus<1",
                    "M_plus>0",
                    "strictly positive",
                    "STOP",
                ],
                "C07": ["SAME-force", "energy arithmetic", "f+r", "approximate-anchor equality"],
                "C08": ["SAME stored C_s_minus", "stored versus continuous", "never replace"],
                "C09": [
                    "diagnostics only",
                    "original loss/gradient/intercept",
                    "full-interval",
                    "P17",
                ],
                "C10": ["candidate-free", "complete failures/prefixes", "never discharges"],
                "C11": [
                    "new owner",
                    "finite executable",
                    "all exact-head/main CI",
                    "no real execution",
                ],
                "C12": [
                    "all16",
                    "BOTH FULL180",
                    "3 seeds/200 FULL",
                    "UNKNOWN",
                    "12721.16417100014444982>7200",
                ],
                "C13": [
                    "all8 simultaneous",
                    "prefit",
                    "through-exit",
                    "16*m*n",
                    "8*m*m",
                    "4294967296",
                ],
                "C14": [
                    "before outcomes",
                    "UNKNOWN",
                    "STOP",
                    "without fallback or automatic retry",
                ],
            }
            for name in sorted(terms):
                require(
                    "conditional meaning " + name, all(word in needs[name] for word in terms[name])
                )
            release = object_text(public["b4-49-software-validation/final_release_closure.json"])
            native = object_text(
                public["b4-49-software-validation/closed_formal_combined_resource.json"]
            )
            annex = object_text(
                public["b4-49-software-validation/final_backup_annex_manifest.json"]
            )
            wanted = {
                "closed": True,
                "slice": "B4.49",
                "final_main": c["starting_main"],
                "formal_calls": [1, 1],
                "formal_retry": False,
                "formal_gate": "PASS_PUBLIC_COMBINED_DIAGNOSTIC_ONLY",
                "scientific_gate": "FAIL",
                "formal_case_audits": 12,
                "formal_predicates": 6059,
                "RN_even_proofs": 455,
                "fixed80_root_proofs": 143,
                "fixed_p17_repaired": False,
                "real_certificate_cost": "UNKNOWN_STOP",
                "real_executable": "UNFROZEN",
                "full_fit_memory": "PENDING4GiB",
                "whole_software_cost_peak": "UNKNOWN_NOT_ZERO",
                "sealed_grant": False,
                "all_applicable_exact_head_main_CI_passed": True,
                "owner_nine_files_ten_refs_preserved": True,
            }
            for name, value in wanted.items():
                require("closed prior " + name, release[name] == value)
            counts = {
                status: sum(row["expected_status"] == status for row in before["catalog"])
                for status in {row["expected_status"] for row in before["catalog"]}
            }
            require(
                "all prescribed public dispositions",
                counts
                == {
                    "PASS": 5,
                    "STOP_RANGE": 2,
                    "STOP_PSD": 1,
                    "STOP_ETA": 1,
                    "STOP_COERCIVITY": 1,
                    "STOP_NORMALIZER": 1,
                    "STOP_NORMALIZER_IDENTITY": 1,
                },
            )
            retained = c["b4_49_retained"]
            for name, value in {
                "cases": 12,
                "certificates": 5,
                "prescribed_stops": 7,
                "case_audits": 12,
                "independent_predicates": 6059,
                "RN_even_proofs": 455,
                "fixed80_root_proofs": 143,
                "formal_calls": [1, 1],
                "formal_retry": False,
                "focused_tests": 51,
                "source_full_tests": 1951,
                "supplied_public_factor_and_witness": True,
                "new_real_proof": False,
            }.items():
                require("retained public " + name, retained[name] == value)
            require(
                "resource closure counters",
                (
                    native["cases_completed"],
                    native["case_audits"],
                    native["predicates"],
                    native["RN_even_proofs"],
                    native["fixed80_root_proofs"],
                )
                == (12, 12, 6059, 455, 143),
            )
            require(
                "source and roles linked",
                native["source"] == release["source_main"]
                and native["formal_calls"] == [1, 1]
                and native["retry"] is False,
            )
            with localcontext() as ctx:
                ctx.prec = 50
                paid = c["preserved_cost"]
                values = [
                    Decimal(paid["known_actual_stage_components_seconds"][name])
                    for name in sorted(paid["known_actual_stage_components_seconds"])
                ]
                total_paid = sum(values, Decimal("0"))
                require(
                    "independent paid sum",
                    total_paid
                    == Decimal("12721.16417100014444982")
                    == Decimal(paid["cross_route_known_paid_floor_seconds"]),
                )
                require(
                    "unchanged infeasible cap",
                    total_paid > Decimal(paid["old_proxy_cap_seconds"]) == Decimal("7200"),
                )
                require(
                    "Q31 counted once",
                    Decimal(paid["b4_31_campaign_plus_review_seconds"])
                    - Decimal(paid["b4_30_immutable_seconds"])
                    == Decimal(paid["b4_31_seconds"]),
                )
                require(
                    "failed prefix retained",
                    Decimal(paid["b4_30_failed_prefix_seconds"]) == Decimal("191.9666532080154866"),
                )
                require(
                    "two full reserves",
                    sum(map(Decimal, paid["b4_30_full_reserves_seconds"])) == Decimal("360"),
                )
                require(
                    "preparation complete",
                    list(map(Decimal, paid["preparation_coefficients"]))
                    == [Decimal(432) * Decimal("3.75"), Decimal(76) * Decimal("3.75")],
                )
                require(
                    "epoch population complete",
                    list(map(Decimal, paid["forward_backward_coefficients"]))
                    == [Decimal(432) * Decimal("750"), Decimal(76) * Decimal("750")],
                )
                outer = Decimal(native["profiles"]["primary_outer"]["real"]) + Decimal(
                    native["profiles"]["independent_outer"]["real"]
                )
                require(
                    "nested times not double added",
                    outer == Decimal("1.14") == Decimal(retained["outer_native_wall_seconds"]),
                )
            require(
                "conservative public RSS sum",
                sum(x["rss_bytes"] for x in native["profiles"].values())
                == 105283584
                == retained["conservative_all_profile_rss_sum_bytes"],
            )
            require(
                "complete cost categories",
                len(paid["full_cost_categories"]) == 16
                and paid["unknown_required_cost"] == "BLOCK_FEASIBILITY",
            )
            require(
                "complete memory still pending",
                len(c["full_training_memory"]["complete_simultaneous_categories"]) == 8
                and c["full_training_memory"]["full_training_status"] == "PENDING"
                and c["full_training_memory"]["fit_cap_bytes"] == 4294967296,
            )
            require("annex text only population", len(annex) == 5)
            for name, entry in annex.items():
                require(
                    "annex identity " + name,
                    set(entry) == {"copy", "sha256"}
                    and entry["copy"].startswith(release["backup_root"] + "/")
                    and len(entry["sha256"]) == 64,
                )
            closure_name = (
                "/Users/keith1117/Documents/TopoLab-data/b4-49-software-validation/"
                "final_release_closure.json"
            )
            require(
                "closed annex content identity",
                annex[closure_name]["sha256"]
                == hashlib.sha256(
                    public["b4-49-software-validation/final_release_closure.json"].encode()
                ).hexdigest(),
            )
            require(
                "software native caps once",
                c["document_audits"]["invocations_per_role"] == 1
                and c["document_audits"]["formal_retry"] is False
                and c["document_audits"]["each_formal_native_wall_seconds_max"] == 60
                and c["document_audits"]["each_formal_native_rss_bytes_max"] == 268435456,
            )
            require(
                "no primary-only read",
                not any((bundle / name).exists() for name in c["primary_only_source_text_sha256"]),
            )
            require("exact independent population", len(opened) == 43 and len(public) == 39)
            require(
                "next prospective text contract",
                c["next_proposed"]
                == "B4.51 bounded read-only real-certification executable "
                "and full-resource preregistration",
            )
            for sample in ('{"k":1,"k":2}', '{"k":Infinity}', "[1]"):
                try:
                    object_text(sample)
                except ValueError:
                    require("bad JSON refusal " + sample, True)
                else:
                    require("bad JSON refusal " + sample, False)
            for field in ("next_authorized", "slice_limit", "additional_field"):
                altered = {**c, field: True}
                try:
                    closed_contract(altered)
                except ValueError:
                    require("schema mutation refusal " + field, True)
                else:
                    require("schema mutation refusal " + field, False)
        except Exception as exc:
            problem = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        result = {
            "role": "independent",
            "passed": problem is None,
            "predicates": assertions,
            "reads": opened,
            "input_bytes": size,
            "failure": problem,
            "candidate_imports": 0,
            "numerical_calls": 0,
            "formal_retry": False,
            "gate": "PASS_TEXT_ONLY" if problem is None else "FAIL_TEXT_AUDIT",
        }
        json.dump(result, report, indent=2, allow_nan=False)
        report.write("\n")
        report.flush()
        os.fsync(report.fileno())
    print(
        json.dumps(
            {
                "passed": problem is None,
                "predicates": len(assertions),
                "reads": len(opened),
                "input_bytes": size,
                "failure": problem,
            }
        )
    )
    if problem:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
