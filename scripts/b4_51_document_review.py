"""Primary B4.51 TEXT/hash/AST/Decimal review; no real implementation or input."""

import ast
import hashlib
import json
import os
import sys
import traceback
from decimal import Decimal, localcontext
from pathlib import Path

KEYS = set(
    "version authority starting_main slice_limit scope source_inputs_at_starting_main_sha256 "
    "primary_only_source_text_sha256 external_text_metadata_sha256 role_access document_audits "
    "inherited_keys executable_registration supported_domain_registration "
    "future_role_path_registration full_resource_registration real_registration_slots "
    "real_release_admissible new_production_budget_or_reserve "
    "real_values_and_new_arithmetic_evaluated b4_50_retained stops allowed_publish_paths "
    "software_cost_policy next_proposed next_started next_authorized boundaries "
    "future_criteria_unchanged preserved_failures preserved_cost full_training_memory "
    "real_prerequisites real_certification_bridge public_evidence_retained b4_44_retained "
    "b4_45_retained b4_46_retained b4_47_retained b4_48_retained b4_49_retained limitations "
    "combined_real_prerequisites".split()
)
TABLES = {
    "executable_registration": ("E", 18),
    "supported_domain_registration": ("D", 10),
    "future_role_path_registration": ("A", 5),
    "full_resource_registration": ("F", 12),
}
STATUS = "TEXT_ONLY_REQUIREMENT; UNFROZEN; UNKNOWN_STOP; UNIMPLEMENTED_UNEVALUATED"
INHERITED = (
    "boundaries future_criteria_unchanged preserved_failures preserved_cost full_training_memory "
    "real_prerequisites real_certification_bridge public_evidence_retained b4_44_retained "
    "b4_45_retained b4_46_retained b4_47_retained b4_48_retained b4_49_retained limitations "
    "combined_real_prerequisites"
).split()


def decode(raw):
    def pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise ValueError("duplicate JSON name")
            result[name] = value
        return result

    def reject(word):
        raise ValueError("nonfinite " + word)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    if type(result) is not dict:
        raise ValueError("object required")
    return result


def schema(c):
    if set(c) != KEYS or type(c["slice_limit"]) is not int or c["slice_limit"] != 1:
        raise ValueError("closed single-slice schema")
    for key in (
        "real_release_admissible",
        "real_values_and_new_arithmetic_evaluated",
        "next_started",
        "next_authorized",
    ):
        if c[key] is not False:
            raise ValueError("no real or successor grant")
    if c["inherited_keys"] != INHERITED:
        raise ValueError("complete inherited population")
    for group, count in (
        ("source_inputs_at_starting_main_sha256", 39),
        ("primary_only_source_text_sha256", 2),
        ("external_text_metadata_sha256", 3),
    ):
        if type(c[group]) is not dict or len(c[group]) != count:
            raise ValueError("finite literal paths")
        for name, digest in c[group].items():
            if type(name) is not str or any(x in ("", ".", "..") for x in name.split("/")):
                raise ValueError("relative literal path")
            if (
                type(digest) is not str
                or len(digest) != 64
                or set(digest) - set("0123456789abcdef")
            ):
                raise ValueError("SHA256 spelling")
    for table, (prefix, count) in TABLES.items():
        if type(c[table]) is not list or len(c[table]) != count:
            raise ValueError("finite registration rows")
        for i, row in enumerate(c[table], 1):
            fields = {"id", "name", "requirement", "maps_to", "status"}
            if prefix == "A":
                fields |= {
                    "literal_inputs",
                    "literal_outputs",
                    "invocation_quota",
                    "path_or_payload_access_granted",
                }
            if set(row) != fields or row["id"] != f"{prefix}{i:02}":
                raise ValueError("registration row fields/order")
            if row["status"] != STATUS or type(row["requirement"]) is not str:
                raise ValueError("unresolved text requirement")
            if len(row["requirement"]) < 60 or type(row["name"]) is not str or not row["name"]:
                raise ValueError("nonempty named requirement")
            refs = row["maps_to"]
            if type(refs) is not list or not refs or len(refs) != len(set(refs)):
                raise ValueError("nonempty unique C references")
            if set(refs) - {f"C{i:02}" for i in range(1, 15)}:
                raise ValueError("unknown C reference")
            if prefix == "A" and (
                row["literal_inputs"] != "UNASSIGNED_DENY"
                or row["literal_outputs"] != "UNASSIGNED_DENY"
                or row["invocation_quota"] != "UNALLOCATED_NO_GRANT"
                or row["path_or_payload_access_granted"] is not False
            ):
                raise ValueError("no prospective role access")
    slots = c["real_registration_slots"]
    if type(slots) is not dict or len(slots) != 14:
        raise ValueError("fourteen unfrozen slots")
    if set(slots.values()) != {"UNKNOWN_STOP_UNFROZEN"}:
        raise ValueError("no fabricated executable/resource value")
    if c["document_audits"] != {
        "invocations_per_role": 1,
        "first_failure_consumes_quota": True,
        "formal_retry": False,
        "max_predicates_per_role": 1200,
        "decimal_precision": 50,
        "each_input_bytes_max": 1048576,
        "total_input_bytes_max": 8388608,
        "each_formal_native_wall_seconds_max": 60,
        "each_formal_native_rss_bytes_max": 268435456,
        "software_source_condition": "frozen declared document working-tree ONLY; no production; "
        "future arithmetic/real execution requires clean locked merged all-CI-passed source",
        "source_access": "TEXT_HASH_AST_ONLY_NO_IMPORT_EXEC_OR_NUMERICAL_EVALUATION",
    }:
        raise ValueError("fixed document caps and source condition")


def main():
    bundle, contract, protocol, frozen, output = map(Path, sys.argv[1:])
    checks, reads, total = [], [], 0
    failure = None
    with output.open("x") as stream:

        def check(label, passed):
            checks.append({"id": label, "passed": passed is True})
            if passed is not True or len(checks) > 1200:
                raise ValueError(label)

        def read(path):
            nonlocal total
            if path.is_symlink() or path.absolute() != path.resolve():
                raise ValueError("input redirect")
            with path.open("rb") as source:
                raw = source.read(1048577)
            total += len(raw)
            if len(raw) > 1048576 or total > 8388608:
                raise ValueError("input cap")
            reads.append(
                {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            )
            return raw

        try:
            f = decode(read(frozen))
            raw = read(contract)
            check("contract frozen first", hashlib.sha256(raw).hexdigest() == f["contract_sha256"])
            c = decode(raw)
            schema(c)
            check("closed contract", True)
            prose = read(protocol).decode()
            check(
                "protocol frozen first",
                hashlib.sha256(prose.encode()).hexdigest() == f["protocol_sha256"],
            )
            own = read(Path(__file__).resolve())
            check(
                "own source", hashlib.sha256(own).hexdigest() == f["programs"][Path(__file__).name]
            )
            check(
                "locked isolated runtime",
                sys.executable == f["sys_executable"]
                and sys.version == f["sys_version"]
                and str(Path.cwd()) == f["cwd"]
                and sys.flags.isolated == 1,
            )
            check("primary bundle", str(bundle) == f["bundle"])
            texts = {}
            for group in (
                "source_inputs_at_starting_main_sha256",
                "external_text_metadata_sha256",
                "primary_only_source_text_sha256",
            ):
                for name, digest in c[group].items():
                    content = read(bundle / name)
                    check("bound " + name, hashlib.sha256(content).hexdigest() == digest)
                    texts[name] = content.decode()
            old = decode(
                texts[
                    "docs/planning/"
                    "b4_50_combined_public_certificate_limitations_real_prerequisites_contract.json"
                ]
            )
            for name in INHERITED:
                check("entire " + name, c[name] == old[name])
            for name, value in old["boundaries"].items():
                check("boundary " + name, c["boundaries"][name] == value)
            check(
                "authority main",
                c["starting_main"] == "729a69ec6de4fb49c7b63ae3382d247b0409fd2b"
                and c["scope"] == "BOUNDED_READ_ONLY_TEXT_AND_LITERAL_COMPACT_METADATA_ONLY",
            )
            check("independent separation", "NEVER primary-only" in c["role_access"]["independent"])
            check("no real budget", c["new_production_budget_or_reserve"] == "NONE_TEXT_ONLY")
            covered = set()
            all_requirements = {}
            for table in TABLES:
                for row in c[table]:
                    check(row["id"] + " unresolved", row["status"] == STATUS)
                    covered.update(row["maps_to"])
                    all_requirements[row["id"]] = row["requirement"]
            check("all fourteen C mapped", covered == {f"C{i:02}" for i in range(1, 15)})
            for key, token in {
                "E04": "BEFORE interpreter",
                "E07": "BOTH G-Gram(A0)",
                "E08": "beta_G/beta_K/beta_f",
                "E09": "r_arrays,r_hat",
                "E10": "EVERY upward",
                "E11": "ONE declared",
                "E12": "strictly positive",
                "E13": "f+r",
                "E14": "SAME stored",
                "E15": "diagnostics",
                "E16": "without candidate",
                "E17": "12721.16417100014444982>7200",
                "E18": "all8 simultaneous",
                "D03": "nonintegral",
                "D04": "sparse",
                "D06": "nonzero-to-zero",
                "D07": "fixed80-bit",
                "D10": "sealed",
                "F03": "FIRST and FAILED",
                "F07": "additional8*m*m",
                "F08": "overlap/release",
                "F09": "4294967296bytes",
                "F10": "PENDING4GiB",
                "F12": "no real paid",
            }.items():
                check("substance " + key, token in all_requirements[key])
            for row in c["stops"]:
                check(
                    row["id"],
                    row["disposition"] == "STOP_PRESERVE_FAILURE_UNKNOWN_COST"
                    and row["alternative_or_retry"] is False,
                )
            check(
                "twenty stops", [x["id"] for x in c["stops"]] == [f"S{i:02}" for i in range(1, 21)]
            )
            check(
                "unfrozen real",
                c["boundaries"]["real_executable_frozen"] is False
                and not c["real_release_admissible"],
            )
            closure = decode(texts["b4-50-software-validation/final_release_closure.json"])
            check(
                "closed predecessor",
                closure["closed"] is True
                and closure["final_main"] == c["starting_main"]
                and closure["predicates"] == [250, 244],
            )
            check(
                "no predecessor retry",
                closure["formal_calls"] == [1, 1] and closure["formal_retry"] is False,
            )
            check(
                "predecessor technical closure",
                closure["all_applicable_exact_head_main_CI_passed"]
                and closure["all_upload_and_actual_squash_guards_passed"]
                and closure["owner_nine_files_ten_refs_preserved"],
            )
            check(
                "fresh authority",
                closure["next_started"] is False
                and closure["next_authorized"] is False
                and closure["next_slice"].startswith("B4.51 "),
            )
            resource = decode(
                texts["b4-50-software-validation/closed_formal_document_resource.json"]
            )
            check("predecessor TEXT resource", resource["gate"] == c["b4_50_retained"]["gate"])
            annex = decode(texts["b4-50-software-validation/final_backup_annex_manifest.json"])
            check(
                "annex identities only",
                len(annex) == 5 and all(len(x["sha256"]) == 64 for x in annex.values()),
            )
            for name in c["primary_only_source_text_sha256"]:
                tree = ast.parse(texts[name])
                check(
                    "source AST only " + name,
                    any(isinstance(n, ast.FunctionDef) for n in ast.walk(tree)),
                )
            tree = ast.parse(own)
            modules = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.extend(a.name for a in node.names)
                elif isinstance(node, ast.ImportFrom):
                    modules.append(node.module)
            check(
                "stdlib imports only",
                all(m and m.split(".")[0] in sys.stdlib_module_names for m in modules),
            )
            with localcontext() as context:
                context.prec = 50
                paid = c["preserved_cost"]
                subtotal = sum(
                    (Decimal(v) for v in paid["known_actual_stage_components_seconds"].values()),
                    Decimal(0),
                )
                check(
                    "unchanged known paid",
                    subtotal
                    == Decimal("12721.16417100014444982")
                    == Decimal(paid["cross_route_known_paid_floor_seconds"]),
                )
                check(
                    "all-paid infeasible at zero new cost",
                    subtotal > Decimal(paid["old_proxy_cap_seconds"]) == Decimal(7200),
                )
                check(
                    "failed-inclusive immutable history",
                    Decimal(paid["b4_30_immutable_seconds"]) + Decimal(paid["b4_31_seconds"])
                    == Decimal(paid["b4_31_campaign_plus_review_seconds"]),
                )
                check("BOTH FULL reserves", paid["b4_30_full_reserves_seconds"] == ["180", "180"])
                for population, preparation, forward in zip(
                    (432, 76), (1620, 285), (324000, 57000), strict=True
                ):
                    check(
                        "preparation coefficient " + str(population),
                        Decimal(3) * Decimal("1.25") * population == preparation,
                    )
                    check(
                        "FULL coefficient " + str(population),
                        Decimal(3) * 200 * Decimal("1.25") * population == forward,
                    )
            check("sixteen cost categories", len(c["preserved_cost"]["full_cost_categories"]) == 16)
            check(
                "UNKNOWN cost blocks",
                c["preserved_cost"]["unknown_required_cost"] == "BLOCK_FEASIBILITY",
            )
            check(
                "all8 simultaneous",
                len(c["full_training_memory"]["complete_simultaneous_categories"]) == 8
                and c["full_training_memory"]["fit_cap_bytes"] == 2**32
                and c["full_training_memory"][
                    "independent_prefit_and_through_exit_fit_peak_required"
                ]
                is True,
            )
            for word in (
                "UNASSIGNED_DENY",
                "UNALLOCATED_NO_GRANT",
                "UNKNOWN_STOP_UNFROZEN",
                "PENDING4GiB",
                "12721.16417100014444982>7200",
                "BOTH FULL180",
                "EVERY outward",
                "original loss/gradient/intercept/normalizer",
                "No B4.50/B4.49/B4.47/B4.43 formal replay/retry/reset",
            ):
                check("protocol " + word, word in prose)
            for mutation in ("extra", "boolean", "grant", "slot", "mapping", "quota"):
                changed = json.loads(json.dumps(c))
                if mutation == "extra":
                    changed["unregistered"] = None
                elif mutation == "boolean":
                    changed["slice_limit"] = True
                elif mutation == "grant":
                    changed["real_release_admissible"] = True
                elif mutation == "slot":
                    changed["real_registration_slots"]["real_source_revision"] = "invented"
                elif mutation == "mapping":
                    changed["executable_registration"][0]["maps_to"] = ["C99"]
                else:
                    changed["future_role_path_registration"][0]["invocation_quota"] = 1
                denied = False
                try:
                    schema(changed)
                except ValueError:
                    denied = True
                check("closed-schema denial " + mutation, denied)
            for sample in ('{"x":1,"x":2}', '{"x":NaN}', "[]"):
                denied = False
                try:
                    decode(sample)
                except ValueError:
                    denied = True
                check("JSON denial " + sample, denied)
            check(
                "next is public guard only",
                c["next_proposed"]
                == "B4.52 bounded public executable-registration and full-resource guard software",
            )
        except Exception:
            failure = traceback.format_exc()
        result = {
            "gate": "FAIL_TEXT_REVIEW"
            if failure
            else "PASS_TEXT_ONLY_EXECUTABLE_RESOURCE_PREREGISTRATION",
            "role": "primary",
            "passed": failure is None,
            "predicates": len(checks),
            "checks": checks,
            "reads": reads,
            "explicit_input_bytes": total,
            "failure": failure,
            "unknown_remainder": "UNKNOWN_ON_FAILURE" if failure else None,
            "scope": "TEXT_HASH_AST_DECIMAL_ONLY",
            "formal_retry": False,
            "implicit_interpreter_stdlib_system_IO": "UNKNOWN_NOT_INSTRUMENTED",
            "real_release_admissible": False,
            "real_values_evaluated": False,
            "whole_software_cost_peak": "UNKNOWN_NOT_ZERO",
        }
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({k: v for k, v in result.items() if k not in ("checks", "reads", "failure")}))
    if failure:
        print(failure, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
