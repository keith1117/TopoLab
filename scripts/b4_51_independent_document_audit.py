"""Independent B4.51 document audit; no primary source, receipt or real input."""

import ast
import hashlib
import json
import os
import sys
import traceback
from decimal import Decimal, localcontext
from pathlib import Path

ROOT_FIELDS = frozenset(
    "version authority starting_main slice_limit scope source_inputs_at_starting_main_sha256 "
    "primary_only_source_text_sha256 external_text_metadata_sha256 role_access document_audits "
    "inherited_keys executable_registration supported_domain_registration "
    "future_role_path_registration "
    "full_resource_registration real_registration_slots real_release_admissible "
    "new_production_budget_or_reserve real_values_and_new_arithmetic_evaluated b4_50_retained "
    "stops allowed_publish_paths software_cost_policy next_proposed next_started next_authorized "
    "boundaries future_criteria_unchanged preserved_failures preserved_cost full_training_memory "
    "real_prerequisites real_certification_bridge public_evidence_retained b4_44_retained "
    "b4_45_retained b4_46_retained b4_47_retained b4_48_retained b4_49_retained limitations "
    "combined_real_prerequisites".split()
)
LEGACY = (
    "boundaries future_criteria_unchanged preserved_failures preserved_cost full_training_memory "
    "real_prerequisites real_certification_bridge public_evidence_retained b4_44_retained "
    "b4_45_retained b4_46_retained b4_47_retained b4_48_retained b4_49_retained limitations "
    "combined_real_prerequisites"
).split()
ROW_SPEC = (
    ("executable_registration", "E", 18),
    ("supported_domain_registration", "D", 10),
    ("future_role_path_registration", "A", 5),
    ("full_resource_registration", "F", 12),
)
UNRESOLVED = "TEXT_ONLY_REQUIREMENT; UNFROZEN; UNKNOWN_STOP; UNIMPLEMENTED_UNEVALUATED"


def parse_document(text):
    def unique(items):
        if len(items) != len({item[0] for item in items}):
            raise ValueError("duplicate field")
        return dict(items)

    def nonfinite(value):
        raise ValueError(value)

    data = json.loads(text, object_pairs_hook=unique, parse_constant=nonfinite)
    if not isinstance(data, dict):
        raise ValueError("expected document object")
    return data


def admit_document(data):
    if frozenset(data) != ROOT_FIELDS:
        raise ValueError("root fields")
    if type(data["slice_limit"]) is not int or data["slice_limit"] != 1:
        raise ValueError("finite one-slice authority")
    flags = (
        "real_release_admissible",
        "real_values_and_new_arithmetic_evaluated",
        "next_started",
        "next_authorized",
    )
    if [data[name] is False for name in flags] != [True] * 4:
        raise ValueError("no real or successor authority")
    if data["inherited_keys"] != LEGACY:
        raise ValueError("inherited identities")
    populations = {
        "source_inputs_at_starting_main_sha256": 39,
        "primary_only_source_text_sha256": 2,
        "external_text_metadata_sha256": 3,
    }
    for category in populations:
        mapping = data[category]
        if not isinstance(mapping, dict) or len(mapping) != populations[category]:
            raise ValueError("input group size")
        for name, digest in mapping.items():
            if (
                not isinstance(name, str)
                or Path(name).is_absolute()
                or set(name.split("/")) & {"", ".", ".."}
            ):
                raise ValueError("unlisted relative path form")
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
            ):
                raise ValueError("input digest form")
    for table, prefix, count in ROW_SPEC:
        rows = data[table]
        if not isinstance(rows, list) or len(rows) != count:
            raise ValueError("registration table size")
        if [row.get("id") for row in rows] != [
            prefix + str(i).zfill(2) for i in range(1, count + 1)
        ]:
            raise ValueError("ordered row identities")
        names = []
        for row in rows:
            fields = {"id", "name", "requirement", "maps_to", "status"}
            if prefix == "A":
                fields.update(
                    (
                        "literal_inputs",
                        "literal_outputs",
                        "invocation_quota",
                        "path_or_payload_access_granted",
                    )
                )
            if set(row) != fields or row["status"] != UNRESOLVED:
                raise ValueError("closed unresolved row")
            if (
                not isinstance(row["name"], str)
                or not row["name"]
                or not isinstance(row["requirement"], str)
                or len(row["requirement"]) < 60
            ):
                raise ValueError("named requirement text")
            names.append(row["name"])
            refs = row["maps_to"]
            if not isinstance(refs, list) or not refs or len(set(refs)) != len(refs):
                raise ValueError("unique reference list")
            if any(ref not in ["C" + str(i).zfill(2) for i in range(1, 15)] for ref in refs):
                raise ValueError("unknown requirement link")
            if prefix == "A":
                if (
                    row["literal_inputs"],
                    row["literal_outputs"],
                    row["invocation_quota"],
                    row["path_or_payload_access_granted"],
                ) != ("UNASSIGNED_DENY", "UNASSIGNED_DENY", "UNALLOCATED_NO_GRANT", False):
                    raise ValueError("future access remains unallocated")
                if row["path_or_payload_access_granted"] is not False:
                    raise ValueError("exact false access flag")
        if len(names) != len(set(names)):
            raise ValueError("unique role/requirement names")
    slots = data["real_registration_slots"]
    if len(slots) != 14 or any(value != "UNKNOWN_STOP_UNFROZEN" for value in slots.values()):
        raise ValueError("unfilled real registration")
    audit = data["document_audits"]
    if (
        audit["invocations_per_role"] != 1
        or audit["first_failure_consumes_quota"] is not True
        or audit["formal_retry"] is not False
    ):
        raise ValueError("once-only document roles")
    required = {
        "max_predicates_per_role": 1200,
        "decimal_precision": 50,
        "each_input_bytes_max": 2**20,
        "total_input_bytes_max": 8 * 2**20,
        "each_formal_native_wall_seconds_max": 60,
        "each_formal_native_rss_bytes_max": 256 * 2**20,
    }
    if any(type(audit[k]) is not int or audit[k] != value for k, value in required.items()):
        raise ValueError("fixed document resources")


def audit():
    input_root, contract_path, protocol_path, frozen_path, result_path = [
        Path(x) for x in sys.argv[1:]
    ]
    decisions, accesses = [], []
    byte_total, error = 0, None
    with result_path.open("x") as result_stream:

        def need(label, valid):
            decisions.append({"id": label, "passed": valid is True})
            if valid is not True or len(decisions) > 1200:
                raise ValueError("independent: " + label)

        def take(path):
            nonlocal byte_total
            if path.resolve() != path.absolute() or path.is_symlink():
                raise ValueError("redirected document")
            with path.open("rb") as stream:
                payload = stream.read(1 + 2**20)
            byte_total += len(payload)
            if len(payload) > 2**20 or byte_total > 8 * 2**20:
                raise ValueError("document byte limit")
            accesses.append(
                {
                    "path": str(path),
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
            return payload.decode("utf-8")

        try:
            frozen = parse_document(take(frozen_path))
            contract_text = take(contract_path)
            need(
                "frozen contract",
                hashlib.sha256(contract_text.encode()).hexdigest() == frozen["contract_sha256"],
            )
            c = parse_document(contract_text)
            admit_document(c)
            need("closed schema and all row types", True)
            protocol = take(protocol_path)
            need(
                "frozen protocol",
                hashlib.sha256(protocol.encode()).hexdigest() == frozen["protocol_sha256"],
            )
            own_text = take(Path(__file__).resolve())
            need(
                "independent source frozen",
                hashlib.sha256(own_text.encode()).hexdigest()
                == frozen["programs"][Path(__file__).name],
            )
            need(
                "isolated runtime",
                (sys.executable, sys.version, str(Path.cwd()), sys.flags.isolated)
                == (frozen["sys_executable"], frozen["sys_version"], frozen["cwd"], 1),
            )
            need("isolated input bundle", str(input_root) == frozen["independent_bundle"])
            documents = {}
            for category in (
                "external_text_metadata_sha256",
                "source_inputs_at_starting_main_sha256",
            ):
                for filename in sorted(c[category]):
                    text = take(input_root / filename)
                    need(
                        "identity " + filename,
                        hashlib.sha256(text.encode()).hexdigest() == c[category][filename],
                    )
                    documents[filename] = text
            need(
                "no primary-only reads",
                not (set(documents) & set(c["primary_only_source_text_sha256"])),
            )
            previous = parse_document(
                documents[
                    "docs/planning/"
                    "b4_50_combined_public_certificate_limitations_real_prerequisites_contract.json"
                ]
            )
            for key in sorted(LEGACY):
                need("entire inherited object " + key, c[key] == previous[key])
            for boundary in sorted(previous["boundaries"]):
                need(
                    "boundary " + boundary,
                    c["boundaries"][boundary] == previous["boundaries"][boundary],
                )
            need(
                "starting protected main",
                c["starting_main"] == "729a69ec6de4fb49c7b63ae3382d247b0409fd2b",
            )
            need(
                "TEXT scope only",
                c["scope"] == "BOUNDED_READ_ONLY_TEXT_AND_LITERAL_COMPACT_METADATA_ONLY"
                and c["new_production_budget_or_reserve"] == "NONE_TEXT_ONLY",
            )
            need("independent role policy", "NEVER primary-only" in c["role_access"]["independent"])
            refs = {link for name, _, _ in ROW_SPEC for row in c[name] for link in row["maps_to"]}
            need(
                "complete C requirement coverage",
                refs == {"C" + str(i).zfill(2) for i in range(1, 15)},
            )
            evidence = {}
            for table, prefix, _ in ROW_SPEC:
                for row in c[table]:
                    need("unimplemented " + row["id"], row["status"] == UNRESOLVED)
                    evidence[row["name"]] = row["requirement"]
                    if prefix == "A":
                        need(
                            "no path or quota " + row["id"],
                            row["literal_inputs"] == row["literal_outputs"] == "UNASSIGNED_DENY"
                            and row["invocation_quota"] == "UNALLOCATED_NO_GRANT",
                        )
            for name, phrase in (
                ("source-closure", "clean merged"),
                ("bootstrap", "transitive imports"),
                ("pending-before-start", "BEFORE interpreter"),
                ("factor-errors", "complete discrepancy"),
                ("actual-arrays", "BOTH triangles"),
                ("solution-residual", "direct intended residual"),
                ("norm-transfer", "rounded zero"),
                ("single-construction", "no witness"),
                ("directed-coercivity", "eta_plus<1,M_plus>0"),
                ("same-force-energy", "f+r"),
                ("stored-denominator", "no C_star"),
                ("diagnostic-bound", "original loss/gradient"),
                ("candidate-free-audit", "without candidate"),
                ("all-paid-admission", "UNKNOWN blocks"),
                ("density-power", "nonintegral"),
                ("scalar-range", "nonzero-to-zero"),
                ("interval-domain", "fixed80-bit"),
                ("strict-positivity", "C_s_minus"),
                ("first-maxima", "FIRST and FAILED"),
                ("full-Q-storage", "additional8*m*m"),
                ("lifetimes", "ownership/overlap/release"),
                ("all8-memory", "4294967296bytes"),
                ("unknown-memory", "PENDING4GiB"),
                ("no-budget-allocation", "no real paid"),
            ):
                need("required substance " + name, phrase in evidence[name])
            slots = c["real_registration_slots"]
            for slot in sorted(slots):
                need("unknown remains blocking " + slot, slots[slot] == "UNKNOWN_STOP_UNFROZEN")
            need(
                "twenty ordered stops",
                [r["id"] for r in c["stops"]] == ["S" + str(i).zfill(2) for i in range(1, 21)],
            )
            for row in c["stops"]:
                need(
                    "stop " + row["id"],
                    set(row) == {"id", "trigger", "disposition", "alternative_or_retry"}
                    and row["disposition"] == "STOP_PRESERVE_FAILURE_UNKNOWN_COST"
                    and row["alternative_or_retry"] is False,
                )
            prior_closed = parse_document(
                documents["b4-50-software-validation/final_release_closure.json"]
            )
            need(
                "predecessor completed",
                prior_closed["closed"] is True
                and prior_closed["final_main"] == c["starting_main"]
                and prior_closed["predicates"] == [250, 244],
            )
            need(
                "predecessor calls consumed",
                prior_closed["formal_calls"] == [1, 1] and prior_closed["formal_retry"] is False,
            )
            for flag in (
                "all_applicable_exact_head_main_CI_passed",
                "all_upload_and_actual_squash_guards_passed",
                "owned_branch_cleaned",
                "owner_nine_files_ten_refs_preserved",
            ):
                need("predecessor " + flag, prior_closed[flag] is True)
            need(
                "new authority distinct",
                prior_closed["next_started"] is False
                and prior_closed["next_authorized"] is False
                and prior_closed["next_slice"].startswith("B4.51 "),
            )
            prior_resource = parse_document(
                documents["b4-50-software-validation/closed_formal_document_resource.json"]
            )
            need(
                "prior TEXT resource gate",
                prior_resource["gate"] == "PASS_TEXT_ONLY_COMBINED_PUBLIC_LIMITATIONS",
            )
            annex = parse_document(
                documents["b4-50-software-validation/final_backup_annex_manifest.json"]
            )
            need(
                "five annex identities only",
                len(annex) == 5 and all(set(x) == {"copy", "sha256"} for x in annex.values()),
            )
            with localcontext() as ctx:
                ctx.prec = 50
                paid = c["preserved_cost"]
                numbers = [
                    Decimal(paid["known_actual_stage_components_seconds"][name])
                    for name in sorted(paid["known_actual_stage_components_seconds"])
                ]
                aggregate = Decimal(0)
                for value in numbers:
                    aggregate += value
                need(
                    "paid history exact",
                    aggregate
                    == Decimal(paid["cross_route_known_paid_floor_seconds"])
                    == Decimal("12721.16417100014444982"),
                )
                need(
                    "unchanged7200 infeasible",
                    aggregate - Decimal(paid["old_proxy_cap_seconds"]) > 0
                    and paid["current_all_paid_feasibility"] == "FAIL_KNOWN_PAID_FLOOR",
                )
                need(
                    "separate Q31 exact",
                    Decimal(paid["b4_31_campaign_plus_review_seconds"])
                    - Decimal(paid["b4_30_immutable_seconds"])
                    == Decimal(paid["b4_31_seconds"]),
                )
                need(
                    "failed prefix remains paid",
                    paid["b4_30_failed_prefix_seconds"] == "191.9666532080154866"
                    and paid["b4_30_full_reserves_seconds"] == ["180", "180"],
                )
                need(
                    "fixed seeds epochs population",
                    paid["future_full_seeds"] == [17, 29, 43]
                    and paid["future_full_epochs"] == 200
                    and paid["future_small_large_population"] == [432, 76],
                )
                base_coefficients = [Decimal(x) * Decimal("3.75") for x in (432, 76)]
                need(
                    "preparation coefficients",
                    base_coefficients == [Decimal(x) for x in paid["preparation_coefficients"]],
                )
                need(
                    "FULL200 coefficients",
                    [x * 200 for x in base_coefficients]
                    == [Decimal(x) for x in paid["forward_backward_coefficients"]],
                )
            need(
                "all16 paid categories",
                len(paid["full_cost_categories"]) == 16
                and paid["unknown_required_cost"] == "BLOCK_FEASIBILITY",
            )
            memory = c["full_training_memory"]
            need(
                "all8 simultaneous categories", len(memory["complete_simultaneous_categories"]) == 8
            )
            need(
                "unchanged4GiB and pending",
                memory["fit_cap_bytes"] == 4 * 1024**3
                and memory["full_training_status"] == "PENDING"
                and memory["new_memory_trial"] is False
                and memory["historical_gaps_filled"] is False,
            )
            need(
                "prefit and exit required",
                memory["independent_prefit_and_through_exit_fit_peak_required"] is True,
            )
            for token in (
                "14 explicit real registration slots",
                "UNASSIGNED_DENY",
                "UNALLOCATED_NO_GRANT",
                "UNKNOWN_STOP_UNFROZEN",
                "12721.16417100014444982>7200",
                "all8 inherited fit categories",
                "No B4.50/B4.49/B4.47/B4.43 formal replay/retry/reset",
                "not a real executable algorithm",
            ):
                need("protocol binding " + token, token.lower() in protocol.lower())
            for title, alteration in (
                ("unknown field", {"unregistered": 1}),
                ("bool authority", {"slice_limit": True}),
                ("real grant", {"real_release_admissible": True}),
                ("successor grant", {"next_authorized": True}),
            ):
                specimen = dict(c)
                specimen.update(alteration)
                blocked = False
                try:
                    admit_document(specimen)
                except ValueError:
                    blocked = True
                need("schema refuses " + title, blocked)
            for bad in ('{"a":0,"a":1}', '{"a":Infinity}', '{"a":NaN}', "[]"):
                blocked = False
                try:
                    parse_document(bad)
                except ValueError:
                    blocked = True
                need("JSON refuses " + bad, blocked)
            imports = []
            for node in ast.walk(ast.parse(own_text)):
                if isinstance(node, ast.Import):
                    imports.extend(item.name for item in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    need(
                        "no dynamic execution " + str(node.lineno),
                        node.func.id not in {"eval", "exec", "compile", "__import__"},
                    )
            need(
                "stdlib independent source",
                all(name and name.split(".")[0] in sys.stdlib_module_names for name in imports),
            )
            need(
                "next public guard only",
                c["next_proposed"]
                == "B4.52 bounded public executable-registration and full-resource guard software",
            )
        except Exception:
            error = traceback.format_exc()
        result = {
            "gate": "FAIL_INDEPENDENT_TEXT_AUDIT"
            if error
            else "PASS_TEXT_ONLY_EXECUTABLE_RESOURCE_PREREGISTRATION",
            "role": "independent",
            "passed": error is None,
            "predicates": len(decisions),
            "checks": decisions,
            "reads": accesses,
            "explicit_input_bytes": byte_total,
            "failure": error,
            "unknown_remainder": "UNKNOWN_ON_FAILURE" if error else None,
            "scope": "TEXT_HASH_AST_DECIMAL_ONLY",
            "formal_retry": False,
            "implicit_interpreter_stdlib_system_IO": "UNKNOWN_NOT_INSTRUMENTED",
            "real_release_admissible": False,
            "real_values_evaluated": False,
            "whole_software_cost_peak": "UNKNOWN_NOT_ZERO",
        }
        json.dump(result, result_stream, indent=2, allow_nan=False)
        result_stream.write("\n")
        result_stream.flush()
        os.fsync(result_stream.fileno())
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in ("checks", "reads", "failure")
            }
        )
    )
    if error:
        print(error, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    audit()
