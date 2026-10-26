"""Independent source-acquisition binding, exercised only with NEW public data.

No prepared plan, raw native reconciliation, or rehearsal capability grants
access to the original source or proposed custody target.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

IDENTITY = "topolab.v2.p17-m2-content-verified-source-acquisition.v1"
HASH_BOUND_IDENTITY = "topolab.v2.p17-m2-hash-bound-source-acquisition.v1"
HASH_BOUND_POLICY = "topolab.source-identity.prebound-sha256.v1"
HASH_BOUND_PROTOCOL = "docs/planning/p17_m2_hash_bound_acquisition_protocol.json"
FUNDED_IDENTITY = "topolab.v2.p17-m2-hash-bound-source-acquisition.v2"
FUNDED_PROTOCOL = "docs/planning/p17_m2_funded_acquisition_protocol.json"
REHEARSAL_SCOPE = "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
FORMAL_SCOPE = "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
REPO = Path(__file__).resolve().parents[1]
PROPOSAL = "docs/planning/p17_m2_content_verified_source_acquisition_proposal.json"
PREPARATION_PROTOCOL = "docs/planning/p17_m2_source_acquisition_adapter_preparation_protocol.json"
EXECUTION_PROTOCOL = "docs/planning/p17_m2_source_acquisition_execution_protocol.json"
CONTENT_CONTRACT = "docs/planning/p17_m2_input_export_preparation_proposal.json"
PROPOSAL_SHA256 = "2c7d0e9243b3ab6beda9344b06c7e88cfbf03910f7104fa43f91c54670a32304"
CONTENT_CONTRACT_SHA256 = "f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad"
ROLE_ORDER = [
    "independent-public-check",
    "exporter-r0",
    "independent-r0",
    "exporter-r1",
    "independent-r1",
    "shared-closeout",
]


def require(ok: Any, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def helper(name: str, filename: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    require(spec and spec.loader, "independent source helper unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


native = helper("acquisition_raw_independent", "p17_m2_content_verified_independent.py")


def sampler_profiles(folder: Path, record: dict[str, Any]) -> dict[str, bytes]:
    """Independently reconcile every durable sample with native command helpers."""
    raw = native._software_bytes(folder / "sampler-evidence.jsonl")
    require(raw.endswith(b"\n"), "sampler journal final newline missing")
    require(record.get("sampler_evidence_storage") == "topolab.source-sampler-evidence.v1"
            and record.get("sampler_journal_sha256") == digest(raw),
            "sampler journal complete-byte binding differs")
    rows = [native.base.parse(line + b"\n", canonical_required=True)
            for line in raw.splitlines()]
    helpers = record["helpers"]
    require(isinstance(helpers, list) and len(rows) == len(helpers),
            "sampler journal helper count differs")
    profiles = {}
    for index, (row, expected) in enumerate(zip(rows, helpers, strict=True)):
        require(isinstance(row, dict) and isinstance(expected, dict),
                "sampler journal/helper structure differs")
        require(
            set(row) == {"schema", "index", "helper", "profile_base64", "profile_identity"}
            and row.get("schema") == "topolab.source-sampler-evidence.v1"
            and type(row.get("index")) is int and row["index"] == index
            and canonical(row["helper"]) == canonical(expected)
            and expected.get("profile") == f"sampler-{index}.time"
            and expected.get("role") == f"rss-sampler-{index}",
            "sampler journal ordering/helper metadata differs",
        )
        require(isinstance(row.get("profile_base64"), str)
                and isinstance(row.get("profile_identity"), dict),
                "sampler journal raw profile/observations absent")
        profile = base64.b64decode(row["profile_base64"], validate=True)
        require(
            0 < len(profile) <= 4 * 1024**2
            and digest(profile) == expected["profile_sha256"]
            and set(row["profile_identity"]) == {"st_dev", "st_ino", "st_size", "st_mtime_ns"}
            and all(type(value) is int for value in row["profile_identity"].values())
            and row["profile_identity"]["st_size"] == len(profile),
            "sampler journal raw profile hash/observations differ",
        )
        profiles[expected["profile"]] = profile
    return profiles


def _source_policy(plan: dict[str, Any]) -> str | None:
    if plan.get("execution_identity") in (HASH_BOUND_IDENTITY, FUNDED_IDENTITY):
        require(plan.get("source_identity_policy") == HASH_BOUND_POLICY
                and plan.get("binding", {}).get("source_identity_policy") == HASH_BOUND_POLICY,
                "hash-bound source policy differs")
        return HASH_BOUND_POLICY
    require(plan.get("execution_identity") == IDENTITY
            and plan.get("source_identity_policy") is None,
            "source acquisition execution identity/policy differs")
    return None


def _protocol_path(plan: dict[str, Any]) -> str:
    if plan.get("execution_identity") == FUNDED_IDENTITY:
        _source_policy(plan)
        return FUNDED_PROTOCOL
    return HASH_BOUND_PROTOCOL if _source_policy(plan) else EXECUTION_PROTOCOL


def _hash_bound_authority(plan: dict[str, Any]) -> dict[str, Any]:
    protocol = _protocol_path(plan)
    funded = plan.get("execution_identity") == FUNDED_IDENTITY
    raw = native._software_bytes(REPO / protocol)
    require(digest(raw) == plan["source_tree"][protocol]
            == plan["binding"]["preparation_protocol_sha256"]
            == plan["preparation_contract_sha256"], "hash-bound authority freeze differs")
    authority = native.base.parse(raw)
    require(
        authority.get("schema") == ("topolab.v2.m2-funded-acquisition-authority.v1" if funded
                                   else "topolab.v2.m2-hash-bound-acquisition-authority.v1")
        and authority.get("execution_identity") == plan["execution_identity"]
        and authority.get("source_identity_policy") == HASH_BOUND_POLICY
        and isinstance(authority.get("owner_approval_reference"), str)
        and bool(authority["owner_approval_reference"].strip())
        and canonical(authority.get("permissions")) == canonical({
            "formal_activation": True, "old_original_access": True,
            "target_access": True, "B_C": False,
        })
        and type(authority.get("formal_seconds")) is int
        and authority["formal_seconds"] == 4500
        and canonical(authority.get("result_seconds")) == canonical(
            {"exporter": 7200, "independent": 7200} if funded
            else {"exporter": 1200, "independent": 1200})
        and type(authority.get("outer_wall_seconds")) is int
        and authority["outer_wall_seconds"] == (129600 if funded else 14400)
        and type(authority.get("total_new_author_charged_seconds_cap")) is int
        and authority["total_new_author_charged_seconds_cap"] == (194400 if funded else 18000),
        "hash-bound authority identity/permissions/budget differs",
    )
    actors = authority.get("actors", {})
    require(isinstance(actors, dict) and set(actors) == {"executor", "independent"}
            and all(isinstance(v, str) and v.strip() and "UNAPPOINTED" not in v
                    for v in actors.values())
            and actors["executor"] != actors["independent"],
            "hash-bound authority requires distinct actual authors")
    if funded:
        _validate_funded_authority(authority, plan)
    return authority


def _validate_funded_authority(authority: dict[str, Any], plan: dict[str, Any]) -> None:
    require(authority.get("formal_admission") == "CONDITIONAL_ON_FROZEN_READINESS"
            and authority["actors"] == {"executor": "/root",
                                      "independent": "/root/acquisition_funded_audit"}
            and authority.get("role_order") == ROLE_ORDER
            and canonical(authority.get("FULL_by_role")) == canonical({
                "independent-public-check": 300, "exporter-r0": 300,
                "independent-r0": 300, "exporter-r1": 1200,
                "independent-r1": 1200, "shared-closeout": 300}),
            "funded authority admission/authors/FULL roles differ")
    whitelist = authority.get("source_whitelist", {})
    expected = {"original_contract": CONTENT_CONTRACT,
                "raw_sha256": CONTENT_CONTRACT_SHA256,
                "per_author_per_file_reads": 1, "r0_metadata": 40, "r1_payload": 558,
                "version_members": 1071, "total_old_source_reads_per_attempt_max": 1196,
                "metadata_acceptance_before_payload_stat_open": True}
    require(isinstance(whitelist, dict)
            and canonical({key: whitelist.get(key) for key in expected}) == canonical(expected),
            "funded authority exact source whitelist/read quota differs")
    parent = "/Users/keith1117/Library/Application Support/TopoLab-custody"
    targets = {"parent": parent, "attempts": {}}
    for index in (1, 2):
        generation = parent + f"/p17-m2-local-input-version-v{index+4}-hash-bound-20261026"
        targets["attempts"][str(index)] = {
            "generation": generation, "backup": generation + "-independent-backup"}
    require(authority.get("fixed_target") == targets,
            "funded authority fresh target inventory differs")
    if plan.get("scope") == FORMAL_SCOPE:
        require(plan.get("binding", {}).get("formal_attempt") != 2,
                "NEW_FROZEN_REMEDY_REQUIRED")
        require(authority.get("preparation_closure_paths") == [
                    "/Users/keith1117/Documents/TopoLab-data/"
                    "p17-m2-hash-bound-custody-20261026-results/publication-closure.json",
                    "/private/tmp/topolab-hash-bound-custody-20261026-results-backup/"
                    "publication-closure.json",
                ] and authority.get("preparation_closure_sha256")
                == "0636d0713cfa15840516b8aff20d904ec09be7577cfdfdafcb416c375a97e314",
                "funded preparation closure literal anchors differ")
        require(authority.get("readiness_freeze_state") == "REVIEWED_FROZEN"
                and authority.get("implementation_base_commit")
                == "2f67feee4d89c94b36196122a5930a56d5b8433f"
                and authority.get("published_source_sha256")
                == {key: value for key, value in plan["source_tree"].items()
                    if key != FUNDED_PROTOCOL}
                and isinstance(authority.get("independent_preflight_path"), str)
                and authority["independent_preflight_path"]
                == "/private/tmp/topolab-funded-continuation-20261026/independent/"
                "preflight-remedy2.json",
                "funded authority actual source freeze/preflight binding differs")


def _validate_hash_bound_binding(plan: dict[str, Any]) -> dict[str, Any]:
    _source_policy(plan)
    binding = plan.get("binding", {})
    formal = plan.get("scope") == FORMAL_SCOPE
    require(plan.get("scope") in (FORMAL_SCOPE, REHEARSAL_SCOPE)
            and plan.get("formal_authority") is formal
            and all(binding.get(k) is formal for k in (
                "formal_authority", "old_original_access", "target_access"))
            and binding.get("B_C") is False,
            "hash-bound scope/permission differs")
    fields = {"proposal_sha256", "content_contract_sha256", "preparation_protocol_sha256",
              "intended_formal_scope", "formal_authority", "old_original_access",
              "target_access", "B_C", "source_identity_policy"}
    funded = plan.get("execution_identity") == FUNDED_IDENTITY
    if funded:
        fields.add("authority_protocol_path")
        if formal:
            fields.add("formal_attempt")
        elif "public_source_plan" in binding:
            fields.update(("public_source_plan", "public_source_plan_sha256"))
        require(binding.get("authority_protocol_path") == FUNDED_PROTOCOL,
                "funded authority protocol path differs")
    if formal:
        fields.add("execution_protocol_sha256")
    require(plan.get("schema") == "topolab.v2.m2-source-acquisition-plan.v1"
            and set(binding) == fields and binding["intended_formal_scope"] == FORMAL_SCOPE
            and plan.get("role_order") == ROLE_ORDER
            and set(plan.get("roles", {})) == set(ROLE_ORDER),
            "hash-bound plan/role/binding schema differs")
    authority = _hash_bound_authority(plan)
    protocol_sha = digest(native._software_bytes(REPO / _protocol_path(plan)))
    require(plan["contract_sha256"] == protocol_sha
            and (not formal or binding["execution_protocol_sha256"] == protocol_sha),
            "hash-bound execution authority freeze differs")
    proposal_raw = native._software_bytes(REPO / PROPOSAL)
    require(digest(proposal_raw) == PROPOSAL_SHA256 == plan["proposal_sha256"]
            == binding["proposal_sha256"] == plan["source_tree"][PROPOSAL],
            "hash-bound inherited acquisition proposal differs")
    if formal:
        require(all(isinstance(authority.get(k), str) and native.base.SHA.fullmatch(authority[k])
                    for k in ("preparation_closure_sha256", "independent_preflight_sha256"))
                and (funded or (isinstance(authority.get("implementation_commit"), str)
                               and re.fullmatch("[0-9a-f]{40}",
                                                authority["implementation_commit"]))),
                "hash-bound formal readiness references missing")
        original = native._software_bytes(REPO / CONTENT_CONTRACT)
        require(digest(original) == CONTENT_CONTRACT_SHA256
                == plan["source_tree"][CONTENT_CONTRACT]
                and canonical(plan["content_contract"]) == canonical(json.loads(original))
                and binding["content_contract_sha256"]
                == digest(canonical(plan["content_contract"]))
                and "public_source_identity" not in plan
                and plan.get("source_identity") == {
                    "B3_DATA_HASH": native.base.B3_DATA_HASH,
                    "CATALOG_HASH": native.base.CATALOG_HASH},
                "hash-bound original content/identity differs")
    else:
        _content_projection(plan)
    for name in ("source_root", "content_root", "backup_root"):
        _member_root(plan, name, Path(plan[name]))
    return binding


def _content_projection(plan: dict[str, Any]) -> None:
    original = native._software_bytes(REPO / CONTENT_CONTRACT)
    require(digest(original) == CONTENT_CONTRACT_SHA256, "frozen content contract differs")
    expected = json.loads(original)
    actual = plan["content_contract"]
    require(
        plan["binding"]["content_contract_sha256"] == digest(canonical(actual)),
        "content projection digest differs",
    )
    identity = plan["public_source_identity"]
    require(
        set(identity) == {"B3_DATA_HASH", "CATALOG_HASH"}
        and all(isinstance(v, str) and native.base.SHA.fullmatch(v) for v in identity.values())
        and identity["B3_DATA_HASH"] != expected["R0"]["embedded_B3_data_index_sha256"],
        "new public source identity missing or reused original identity",
    )
    require(len(actual["R0"]["literal_bootstrap_files"]) == 7, "fixed bootstrap count differs")
    for declared, projected in zip(
        expected["R0"]["literal_bootstrap_files"],
        actual["R0"]["literal_bootstrap_files"],
        strict=True,
    ):
        value = projected["expected_sha256"]
        require(isinstance(value, str) and native.base.SHA.fullmatch(value), "fixture hash missing")
        declared["expected_sha256"] = value
    expected["R0"]["embedded_B3_data_index_sha256"] = identity["B3_DATA_HASH"]
    require(
        canonical(expected) == canonical(actual),
        "fixed content projection or permitted source closure differs",
    )


def public_prepare_suffix(plan: dict[str, Any]) -> tuple[str, ...]:
    """Bind NEW public data reuse to its real controller CLI; never formal access."""
    binding = plan.get("binding", {})
    fields = {"public_source_plan", "public_source_plan_sha256"}
    present = fields & set(binding)
    if not present:
        return ()
    require(present == fields and plan.get("execution_identity") == FUNDED_IDENTITY
            and plan.get("scope") == REHEARSAL_SCOPE and plan.get("formal_authority") is False,
            "public source plan is restricted to new funded rehearsal")
    name, expected_sha = binding["public_source_plan"], binding["public_source_plan_sha256"]
    require(isinstance(name, str) and isinstance(expected_sha, str)
            and native.base.SHA.fullmatch(expected_sha), "public source plan path/hash missing")
    path = Path(name)
    require(path.is_absolute() and ".." not in path.parts and path.name == "plan.json"
            and path.parent.name.startswith("topolab-public-funded-acquisition-")
            and str(path) == name and str(path.parent) != plan.get("root"),
            "public source plan literal path differs")
    try:
        rehearsal_root(path.parent)
    except ValueError as error:
        raise ValueError("public source plan root differs") from error
    raw = native._software_bytes(path)  # no-follow ancestors/file and strict same-buffer identity
    require(digest(raw) == expected_sha, "public source plan SHA256 differs")
    source = native.base.parse(raw)
    require(isinstance(source, dict), "public source plan object missing")
    permissions = source.get("binding", {})
    require(isinstance(permissions, dict), "public source plan permissions missing")
    require(source.get("schema") == "topolab.v2.m2-source-acquisition-plan.v1"
            and source.get("execution_identity") == FUNDED_IDENTITY
            and source.get("source_identity_policy") == HASH_BOUND_POLICY
            and source.get("scope") == REHEARSAL_SCOPE
            and source.get("formal_authority") is False
            and source.get("root") == str(path.parent)
            and source.get("source_root") == str(path.parent / "public-source")
            and all(permissions.get(key) is False for key in (
                "formal_authority", "old_original_access", "target_access", "B_C"))
            and not (fields & set(permissions)),
            "public source plan origin/permissions differ")
    try:
        _content_projection(source)
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError("public source plan content projection differs") from error
    require(canonical(source["content_contract"]) == canonical(plan["content_contract"])
            and canonical(source["public_source_identity"])
            == canonical(plan["public_source_identity"]),
            "public source plan copied content/identity differs")
    return ("--public-source-plan", name, "--public-source-plan-sha", expected_sha)


def validate_binding(plan: dict[str, Any]) -> dict[str, Any]:
    """Check authority and optional NEW public plan before payload/target IO."""
    public_prepare_suffix(plan)
    if plan.get("execution_identity") in (HASH_BOUND_IDENTITY, FUNDED_IDENTITY):
        return _validate_hash_bound_binding(plan)
    binding = plan.get("binding", {})
    formal = plan.get("scope") == FORMAL_SCOPE
    require(
        plan.get("scope") in (REHEARSAL_SCOPE, FORMAL_SCOPE)
        and plan.get("formal_authority") is formal
        and all(
            binding.get(name) is formal
            for name in ("formal_authority", "old_original_access", "target_access")
        )
        and binding.get("B_C") is False,
        "preparation authority does not grant formal/source/target permissions",
    )
    expected_keys = {
        "proposal_sha256",
        "content_contract_sha256",
        "preparation_protocol_sha256",
        "intended_formal_scope",
        "formal_authority",
        "old_original_access",
        "target_access",
        "B_C",
    } | ({"execution_protocol_sha256"} if formal else set())
    require(
        plan.get("schema") == "topolab.v2.m2-source-acquisition-plan.v1"
        and plan.get("execution_identity") == IDENTITY
        and set(binding) == expected_keys
        and binding["intended_formal_scope"] == FORMAL_SCOPE,
        "source acquisition identity/scope/binding schema differs",
    )
    require(
        plan.get("role_order") == ROLE_ORDER and set(plan.get("roles", {})) == set(ROLE_ORDER),
        "source acquisition role order or inventory differs",
    )
    if formal:
        # The only authority input is the separately published reserved Git-local file.
        # Never discover a grant or inspect its scientific source/target while looking for it.
        try:
            raw = native._software_bytes(REPO / EXECUTION_PROTOCOL)
        except OSError as error:
            raise ValueError("separate frozen execution authority protocol not granted") from error
        require(
            digest(raw)
            == binding["execution_protocol_sha256"]
            == plan["contract_sha256"]
            == plan["source_tree"][EXECUTION_PROTOCOL],
            "execution authority protocol freeze differs",
        )
        authority = native.base.parse(raw)
        require(
            authority.get("schema") == "topolab.v2.m2-source-acquisition-execution-authority.v1"
            and authority.get("execution_identity") == IDENTITY
            and authority.get("proposal_sha256") == PROPOSAL_SHA256
            and isinstance(authority.get("owner_approval_reference"), str)
            and bool(authority["owner_approval_reference"].strip())
            and canonical(authority.get("permissions"))
            == canonical(
                {
                    "formal_activation": True,
                    "old_original_access": True,
                    "target_access": True,
                    "B_C": False,
                }
            )
            and type(authority.get("formal_seconds")) is int
            and authority["formal_seconds"] == 4500
            and authority.get("result_seconds") == {"exporter": 7200, "independent": 7200},
            "separate execution authority grant/identity/budget differs",
        )
        actors = authority.get("actors", {})
        require(
            isinstance(actors, dict)
            and set(actors) == {"executor", "independent"}
            and all(
                isinstance(actor, str) and bool(actor.strip()) and "UNAPPOINTED" not in actor
                for actor in actors.values()
            )
            and actors["executor"] != actors["independent"]
            and all(
                isinstance(authority.get(name), str) and native.base.SHA.fullmatch(authority[name])
                for name in ("preparation_closure_sha256", "independent_preflight_sha256")
            )
            and isinstance(authority.get("implementation_commit"), str)
            and re.fullmatch("[0-9a-f]{40}", authority["implementation_commit"]),
            "execution authority requires distinct appointed authors "
            "and published preparation references",
        )

    for name in ("source_root", "content_root", "backup_root"):
        _member_root(plan, name, Path(plan[name]))
    proposal_raw = native._software_bytes(REPO / PROPOSAL)
    preparation_raw = native._software_bytes(REPO / PREPARATION_PROTOCOL)
    protocol_sha = digest(preparation_raw)
    require(
        digest(proposal_raw)
        == PROPOSAL_SHA256
        == binding["proposal_sha256"]
        == plan["proposal_sha256"]
        == plan["source_tree"][PROPOSAL],
        "frozen source acquisition proposal differs",
    )
    require(
        protocol_sha
        == binding["preparation_protocol_sha256"]
        == plan["preparation_contract_sha256"]
        == plan["source_tree"][PREPARATION_PROTOCOL]
        and (formal or protocol_sha == plan["contract_sha256"]),
        "actual frozen preparation protocol binding differs",
    )
    protocol = json.loads(preparation_raw)
    require(
        protocol["execution_identity"] == IDENTITY
        and protocol["preparation_scope"] == REHEARSAL_SCOPE
        and protocol["authority"]["public_implementation_tests_independent_review_publication"]
        is True
        and protocol["authority"]["new_public_fixtures"] is True
        and all(
            protocol["authority"][name] is False
            for name in (
                "formal_activation",
                "old_original_access",
                "target_access",
                "B_C",
                "global_sync_change",
                "new_installation_purchase",
                "old_quota_reset",
            )
        )
        and protocol["budgets"]["executor"]["cap_seconds"] == 14400
        and protocol["budgets"]["independent"]["cap_seconds"] == 10800,
        "effective preparation authority/budgets differ; no formal grant",
    )
    if formal:
        original = native._software_bytes(REPO / CONTENT_CONTRACT)
        require(
            digest(original) == CONTENT_CONTRACT_SHA256 == plan["source_tree"][CONTENT_CONTRACT]
            and canonical(plan["content_contract"]) == canonical(json.loads(original))
            and binding["content_contract_sha256"] == digest(canonical(plan["content_contract"]))
            and "public_source_identity" not in plan
            and plan.get("source_identity")
            == {"B3_DATA_HASH": native.base.B3_DATA_HASH, "CATALOG_HASH": native.base.CATALOG_HASH},
            "formal original fixed content/identity differs",
        )
    else:
        _content_projection(plan)
    return binding


def check_funded_preflight(plan: dict[str, Any], raw: bytes) -> dict[str, Any]:
    """Replay separately authored metadata against its frozen digest/source/runtime."""
    validate_binding(plan)
    require(plan.get("execution_identity") == FUNDED_IDENTITY
            and plan.get("scope") == FORMAL_SCOPE, "funded preflight requires formal metadata")
    authority = _hash_bound_authority(plan)
    require(digest(raw) == authority["independent_preflight_sha256"],
            "funded independent preflight digest differs")
    preflight = native.base.parse(raw)
    runtime = {key: value for key, value in plan["runtime"].items() if key != "orig_argv"}
    supplied = preflight.get("runtime", {})
    whitelist = {"raw_sha256": CONTENT_CONTRACT_SHA256, "r0_metadata": 40,
                 "r1_payload": 558, "version_members": 1071,
                 "total_old_source_reads_per_attempt_max": 1196,
                 "per_author_per_file_reads": 1}
    require(preflight.get("status") == "PASS_PUBLIC_METADATA_LAUNCH_PREFLIGHT"
            and preflight.get("execution_identity") == FUNDED_IDENTITY
            and preflight.get("actors") == authority["actors"]
            and preflight.get("published_source_sha256") == authority["published_source_sha256"]
            and isinstance(supplied, dict)
            and canonical({key: supplied.get(key) for key in runtime}) == canonical(runtime)
            and canonical(preflight.get("expected_white_list_contract")) == canonical(whitelist),
            "funded independent preflight source/runtime/whitelist differs")
    return preflight


def result_window_seconds(plan: dict[str, Any]) -> tuple[int, int]:
    """Return the independently authority-checked result clocks, without target IO."""
    validate_binding(plan)
    if plan.get("execution_identity") == HASH_BOUND_IDENTITY and plan["scope"] == FORMAL_SCOPE:
        return (1200, 1200)
    return (7200, 7200)


def rehearsal_root(root: Path) -> Path:
    literal = Path(os.path.abspath(root))
    require(
        literal.name.startswith(("topolab-public-formal-binding-", "topolab-public-hash-bound-",
                                     "topolab-public-funded-acquisition-"))
        and any(
            literal.is_relative_to(parent) and literal != Path(parent)
            for parent in ("/private/tmp", "/tmp", "/private/var/folders")
        ),
        "source acquisition requires a new public rehearsal root",
    )
    return literal


def _member_root(plan: dict[str, Any], name: str, root: Path) -> Path:
    if plan.get("scope") == FORMAL_SCOPE:
        if _source_policy(plan):
            funded = plan.get("execution_identity") == FUNDED_IDENTITY
            index = (plan.get("binding", {}).get("formal_attempt") if funded
                     else plan.get("attempt_index"))
            require(type(index) is int and index in (1, 2), "hash-bound attempt index differs")
            targets = _hash_bound_authority(plan)["fixed_target"]
            parent = Path("/Users/keith1117/Library/Application Support/TopoLab-custody")
            require(targets["parent"] == str(parent), "hash-bound custody parent differs")
            target = targets["attempts"][str(index)]
            version = index + (4 if funded else 2)
            parent /= f"p17-m2-local-input-version-v{version}-hash-bound-20261026"
            require(target["generation"] == str(parent)
                    and target["backup"] == str(parent) + "-independent-backup",
                    "hash-bound frozen target differs")
        else:
            parent = Path(
                "/Users/keith1117/Library/Application Support/TopoLab-custody/"
                "p17-m2-local-input-version-v2"
            )
        expected = {
            "source_root": Path("/Users/keith1117/Documents/TopoLab-data"),
            "content_root": parent / "content",
            "backup_root": parent.with_name(parent.name + "-independent-backup"),
        }[name]
        require(plan["root"] == str(parent), "formal generation literal differs")
    else:
        parent = rehearsal_root(Path(plan["root"]))
        expected = (
            parent
            / {
                "source_root": "public-source",
                "content_root": "content",
                "backup_root": "backup-content",
            }[name]
        )
    require(
        plan[name] == str(expected) and Path(os.path.abspath(root)) == expected,
        "source/content/backup literal root differs",
    )
    return expected


def _source_identity(plan: dict[str, Any]) -> dict[str, str]:
    return plan["source_identity" if plan["scope"] == FORMAL_SCOPE else "public_source_identity"]


def check_expected_source_hashes(rows, registry, contract, stage):
    """Bind each pre-read hash to independently accepted lineage, never its own row."""
    require(stage in ("r0", "r1"), "source hash binding stage differs")
    if stage == "r0":
        expected = {row["relative_path"]: row["expected_sha256"]
                    for row in contract["R0"]["literal_bootstrap_files"]}
        expected.update({row["selection"]["path"]: row["selection"]["sha256"]
                         for row in registry["models"]})
        sources = {row["path"]: row for row in registry["metadata"]}
        count = 40
    else:
        references = ([row["checkpoint"] for row in registry["models"]]
                      + [row["artifact"] for row in registry["labels"]]
                      + [row["packet"] for row in registry["scalars"]])
        sources = {row["path"]: row for row in references}
        expected = {name: row["sha256"] for name, row in sources.items()}
        count = 558
    local = helper("acquisition_hash_binding_local", "p17_m2_local_input_independent.py")
    observed = local.identity_table(rows, count, source_identity_policy=HASH_BOUND_POLICY)
    require(len(sources) == count and observed.keys() == sources.keys(),
            "source hash binding exact member set differs")
    for name, row in observed.items():
        require(row["expected_sha256"] == expected.get(name)
                and row["sha256"] == sources[name]["sha256"]
                and row["byte_size"] == sources[name]["byte_size"],
                "source prebound hash differs from accepted lineage")


def independent_r0(
    source: Path,
    contract: dict[str, Any],
    producer_registry: dict[str, Any],
    producer_rows: list[dict[str, Any]],
    source_binding: dict[str, str],
    *,
    plan: dict[str, Any],
) -> dict[str, Any]:
    """Build the source closure using independent source algorithms, not the producer."""
    readers: dict[str, Any] = {}
    try:
        validate_binding(plan)
        source = _member_root(plan, "source_root", source)
        require(
            contract == plan["content_contract"] and source_binding == _source_identity(plan),
            "independent source contract/binding differs",
        )
        checker = helper("acquisition_r0_source_independent", "p17_m2_input_export_independent.py")
        checker.B3_DATA_HASH = source_binding["B3_DATA_HASH"]
        checker.CATALOG_HASH = source_binding["CATALOG_HASH"]
        policy = _source_policy(plan)
        reader = checker.OnceReader(source, 40, 32 * checker.MIB, source_identity_checks=True,
                                    source_identity_policy=policy)
        readers["source"] = reader
        registry = checker.build_registry(reader, contract)
        checker.check_registry_shape(registry, contract)
        compared = checker.compare_words(registry, producer_registry)
        local = helper("acquisition_r0_local_independent", "p17_m2_local_input_independent.py")
        local.compare_identity_tables(reader.observations, producer_rows, 40,
                                      source_identity_policy=policy)
        if policy:
            for rows in (reader.observations, producer_rows):
                check_expected_source_hashes(rows, registry, contract, "r0")
        return {
            "status": "SOURCE_ACQUISITION_R0_CHECKED",
            "execution_identity": plan["execution_identity"],
            "scope": plan["scope"],
            "root": str(source),
            "source_count": 40,
            "source_rows": reader.observations,
            "source_registry_sha256": digest(canonical(registry)),
            "source_contract_sha256": digest(canonical(contract)),
            "source_identity": source_binding,
            **(
                {"public_source_identity": source_binding}
                if plan["scope"] == REHEARSAL_SCOPE
                else {}
            ),
            "compared_fields": compared,
            "source_comparison": (
                "PREBOUND_HASH_AND_PHYSICAL_IDENTITY_MATCHED_TIMESTAMPS_RETAINED" if policy
                else "ALL_FIELDS_AND_PHYSICAL_TUPLES_MATCHED"),
            "helper_identity_relabelled": False,
            "helper_native_execution_identity": checker.EXECUTION_STABLE,
            "formal_or_scientific_admission": False,
            "B_C_admission": False,
        }
    except BaseException as error:
        native._capture_read_failure(
            error,
            readers,
            "independent_source_acquisition_r0",
            {"producer_source_rows": producer_rows},
        )
        raise


def independent_r1(
    source: Path,
    content: Path,
    registry: dict[str, Any],
    producer_rows: list[dict[str, Any]],
    closed: dict[str, Any],
    contract_sha: str,
    source_binding: dict[str, str],
    *,
    plan: dict[str, Any],
) -> dict[str, Any]:
    """Compare every original payload and every restricted member independently."""
    readers: dict[str, Any] = {}
    root_observations: dict[str, Any] = {
        "declared": closed.get("root_identity"),
        "before": None,
        "after": None,
        "closing": None,
    }
    try:
        validate_binding(plan)
        source = _member_root(plan, "source_root", source)
        content = _member_root(plan, "content_root", content)
        require(
            source_binding == _source_identity(plan) and contract_sha == plan["contract_sha256"],
            "independent source/contract binding differs",
        )
        root_observations["before"] = native._checked_root(
            content, root_guard=lambda path: _member_root(plan, "content_root", path)
        )
        require(
            root_observations["before"] == native._root_tuple(closed.get("root_identity")),
            "frozen content root identity changed",
        )
        checker = helper("acquisition_r1_source_independent", "p17_m2_input_export_independent.py")
        checker.B3_DATA_HASH = source_binding["B3_DATA_HASH"]
        checker.CATALOG_HASH = source_binding["CATALOG_HASH"]
        policy = _source_policy(plan)
        original = checker.OnceReader(source, 558, 852 * checker.MIB, source_identity_checks=True,
                                      source_identity_policy=policy)
        exported = checker.OnceReader(content, 1070, 301 * checker.MIB)
        readers.update(source=original, exports=exported)
        compared = checker.audit_exports(original, exported, registry)
        local = helper("acquisition_r1_local_independent", "p17_m2_local_input_independent.py")
        local.compare_identity_tables(original.observations, producer_rows, 558,
                                      source_identity_policy=policy)
        if policy:
            for rows in (original.observations, producer_rows):
                check_expected_source_hashes(rows, registry, plan["content_contract"], "r1")
        constructor = local.base.OnceReader

        def observe(*args: Any, **kwargs: Any) -> Any:
            reader = constructor(*args, **kwargs)
            readers["local_content"] = reader
            return reader

        local.base.OnceReader = observe
        checked = local.audit_local_content(
            content, closed["manifest"], registry, closed["local_identity_rows"], contract_sha
        )
        root_observations["after"] = native._checked_root(
            content, root_guard=lambda path: _member_root(plan, "content_root", path)
        )
        root_observations["closing"] = native._checked_root(
            content, root_guard=lambda path: _member_root(plan, "content_root", path)
        )
        require(
            root_observations["declared"]
            == root_observations["after"]
            == root_observations["closing"],
            "content root identity changed during independent comparison",
        )
        require(closed["version_id"] == checked["version_id"], "content version differs")
        return {
            "status": "SOURCE_ACQUISITION_R1_CHECKED",
            "execution_identity": plan["execution_identity"],
            "scope": plan["scope"],
            "source_root": str(source),
            "root": str(content),
            "root_identity": root_observations["closing"],
            "source_count": 558,
            "source_rows": original.observations,
            "local_identity_rows": checked["local_identity_rows"],
            "source_registry_sha256": digest(canonical(registry)),
            "manifest_sha256": digest(canonical(closed["manifest"])),
            "version_id": checked["version_id"],
            "contract_sha256": contract_sha,
            "source_identity": source_binding,
            **(
                {"public_source_identity": source_binding}
                if plan["scope"] == REHEARSAL_SCOPE
                else {}
            ),
            "compared_fields": compared["compared_scalar_fields"],
            "source_comparison": (
                "PREBOUND_HASH_AND_PHYSICAL_IDENTITY_MATCHED_TIMESTAMPS_RETAINED" if policy
                else "ALL_FIELDS_AND_PHYSICAL_TUPLES_MATCHED"),
            "helper_identity_relabelled": False,
            "helper_native_execution_identity": checker.EXECUTION_STABLE,
            "formal_or_scientific_admission": False,
            "B_C_admission": False,
        }
    except BaseException as error:
        native._capture_read_failure(
            error,
            readers,
            "independent_source_acquisition_r1",
            {
                "producer_source_rows": producer_rows,
                "expected_local_rows": closed.get("local_identity_rows"),
                "expected_root_identity": closed.get("root_identity"),
                "root_observations": root_observations,
            },
        )
        raise


def _target_guard(plan: dict[str, Any], path: Path) -> Path:
    for name in ("content_root", "backup_root"):
        if str(path) == plan[name]:
            return _member_root(plan, name, path)
    raise ValueError("unregistered source acquisition target root")


def independent_backup(
    content: Path,
    backup: Path,
    closed: dict[str, Any],
    registry: dict[str, Any],
    contract_sha: str,
    *,
    plan: dict[str, Any],
) -> dict[str, Any]:
    _member_root(plan, "content_root", content)
    _member_root(plan, "backup_root", backup)
    validate_binding(plan)
    require(contract_sha == plan["contract_sha256"], "backup contract differs")
    return native.independent_backup(
        content,
        backup,
        closed,
        registry,
        contract_sha,
        expected_identity=plan["execution_identity"],
        expected_scope=plan["scope"],
        checked_status="SOURCE_ACQUISITION_BACKUP_CHECKED",
        root_guard=lambda path: _target_guard(plan, path),
    )


def independent_prefix_backup(
    root: Path,
    backup: Path,
    rows: list[dict[str, Any]],
    *,
    plan: dict[str, Any],
) -> dict[str, Any]:
    validate_binding(plan)
    if plan["scope"] == FORMAL_SCOPE:
        require(str(root) == plan["root"], "failed formal prefix generation differs")
        expected_backup = _member_root(plan, "backup_root", backup)
    else:
        root = rehearsal_root(root)
        expected_backup = root / "backup-prefix"
        require(
            str(root) == plan["root"] and backup == expected_backup, "failed prefix root differs"
        )

    def guard(path: Path) -> Path:
        require(path in (root, expected_backup), "failed prefix root outside frozen namespace")
        return path

    return native.independent_prefix_backup(
        root,
        backup,
        rows,
        expected_identity=plan["execution_identity"],
        expected_scope=plan["scope"],
        checked_status="SOURCE_ACQUISITION_FAILED_PREFIX_BACKUP_CHECKED",
        root_guard=guard,
        expected_backup=expected_backup,
    )


_ACQUISITION_AUTHORITY = object()


class CheckedAcquisitionInput(native.CheckedPublicInput):
    """Opaque checked source version; rehearsal never authorizes formal execution."""

    __slots__ = ()

    def __init__(self, binding: dict[str, Any], *, _authority: Any = None):
        require(
            _authority is _ACQUISITION_AUTHORITY,
            "source certificate requires independent authority",
        )
        super().__init__(binding, _authority=native._CHECKED_AUTHORITY)

    def _reader_identity(self) -> str:
        return self._binding["verified_plan"]["execution_identity"]

    def _reader_scope(self) -> str:
        return self._binding["scope"]

    def _reader_result_seconds(self) -> tuple[int, int]:
        plan = self._binding["verified_plan"]
        return result_window_seconds(plan)

    def _reader_schema(self) -> str:
        return "topolab.v2.m2-source-acquisition-reader-lease.v1"

    def _reader_ack_status(self) -> str:
        return "SOURCE_ACQUISITION_READER_RETURN_ACKNOWLEDGED"

    def _reader_source_digest(self) -> str:
        require(
            digest(Path(native.__file__).read_bytes())
            == self._binding["supporting_verifier_sha256"],
            "supporting reader verifier source freeze changed",
        )
        return digest(Path(__file__).read_bytes())

    def _reader_root(self, root: Path) -> Path:
        return _member_root(self._binding["verified_plan"], "content_root", root)

    def _reader_root_identity(self, root: Path) -> dict[str, int]:
        return native._checked_root(root, root_guard=self._reader_root)

    def _reader_argv(self, action: str, role: str) -> list[str]:
        require(
            self._binding["scope"] == REHEARSAL_SCOPE,
            "source version certificate does not grant formal/scientific/B/C reader execution",
        )
        return super()._reader_argv(action, role)


MODULE_SOURCE_SHA256 = digest(Path(__file__).read_bytes())


def _check_software(plan: dict[str, Any]) -> None:
    validate_binding(plan)
    execution = _protocol_path(plan)
    contracts = (*native.SOFTWARE_CONTRACTS, PROPOSAL, PREPARATION_PROTOCOL)
    formal = plan["scope"] == FORMAL_SCOPE
    for path in (EXECUTION_PROTOCOL, HASH_BOUND_PROTOCOL, FUNDED_PROTOCOL):
        try:
            native._software_bytes(REPO / path)
        except FileNotFoundError:
            require(not formal or path != execution,
                    "separate frozen execution authority protocol not granted")
        else:
            contracts = tuple(dict.fromkeys((*contracts, path)))
    native._check_software(
        plan,
        contracts=contracts,
        verifier_path="scripts/p17_m2_source_acquisition_independent.py",
        verifier_sha256=MODULE_SOURCE_SHA256,
        controller="p17_m2_source_acquisition_control.py",
        prepare_mode="activate-formal" if formal else "prepare-rehearsal",
        repo_guard=rehearsal_root,
        prepare_suffix=public_prepare_suffix(plan),
    )
    python = plan["runtime"]["python"]
    script = str(Path(plan["runtime"]["cwd"]) / "scripts/p17_m2_source_acquisition_control.py")
    for role in ("public-consumer", "reader-ack"):
        require(
            plan["metadata_actions"][role]["argv"]
            == [
                python,
                "-I",
                script,
                "payload",
                "--root",
                plan["root"],
                "--plan-sha",
                "@PLAN_SHA256@",
                "--role",
                role,
                "--reader-role",
                "@READER_ROLE@",
            ],
            "frozen source reader/ack argv differs",
        )
    require(
        plan.get("result_window_projection_seconds") == dict(
            zip(("exporter", "independent"), result_window_seconds(plan), strict=True)),
        "source result window projection differs",
    )


class _AcquisitionCertificatePolicy:
    """Private independently validated immutable context for the shared evidence engine."""

    identity = IDENTITY
    schema = "topolab.v2.m2-source-acquisition-bundle.v1"
    source_identity_key = "source_identity"
    r0_status = "SOURCE_ACQUISITION_R0_CHECKED"
    r1_status = "SOURCE_ACQUISITION_R1_CHECKED"
    backup_status = "SOURCE_ACQUISITION_BACKUP_CHECKED"
    filing_status = "SOURCE_ACQUISITION_FILING_SNAPSHOT_WRITTEN"
    verifier_path = "scripts/p17_m2_source_acquisition_independent.py"
    result_seconds = (7200, 7200)
    precheck_status = "PASS_PUBLIC_IO_ONLY"

    def check_precheck(
        self, proof: dict[str, Any], bundle: dict[str, Any], actual: dict[str, Any]
    ) -> None:
        validate_setup(bundle, proof, actual)

    def __init__(self, plan: dict[str, Any]):
        validate_binding(plan)
        self.plan = deepcopy(plan)
        self.identity = plan["execution_identity"]
        self.source_identity_policy = _source_policy(plan)
        self.source_comparison = (
            "PREBOUND_HASH_AND_PHYSICAL_IDENTITY_MATCHED_TIMESTAMPS_RETAINED"
            if self.source_identity_policy else "ALL_FIELDS_AND_PHYSICAL_TUPLES_MATCHED")
        self.result_seconds = result_window_seconds(plan)
        self.scope = plan["scope"]
        self.formal_authority = plan["formal_authority"]
        self.contract_path = (
            _protocol_path(plan) if self.source_identity_policy
            else EXECUTION_PROTOCOL if self.formal_authority else PREPARATION_PROTOCOL)
        self.result_start = None

    def guard(self, root: Path) -> Path:
        if str(root) == self.plan["root"]:
            if self.scope == REHEARSAL_SCOPE:
                return rehearsal_root(root)
            # Pure literal check after validate_binding established the separate authority.
            _member_root(self.plan, "content_root", Path(self.plan["content_root"]))
            return root
        return _target_guard(self.plan, root)

    def check_software(self, plan: dict[str, Any]) -> None:
        require(plan == self.plan, "independent plan context changed")
        _check_software(plan)

    def content_root(self, plan: dict[str, Any]) -> Path:
        return _member_root(plan, "content_root", Path(plan["content_root"]))

    def source_root(self, plan: dict[str, Any]) -> Path:
        return _member_root(plan, "source_root", Path(plan["source_root"]))

    def backup_root(self, plan: dict[str, Any]) -> Path:
        return _member_root(plan, "backup_root", Path(plan["backup_root"]))

    def source_identity(self, plan: dict[str, Any]) -> dict[str, str]:
        return _source_identity(plan)

    def check_source_rows(self, proof, count, registry):
        if self.source_identity_policy:
            check_expected_source_hashes(proof["source_rows"], registry,
                                        self.plan["content_contract"],
                                        "r0" if count == 40 else "r1")

    def check_filing(self, result: dict[str, Any], wire: dict[str, Any]) -> None:
        start = native.number(wire["pending"]["result_start_UTC_seconds"], positive=True)
        self.result_start = start
        require(
            start <= result["T0"] <= result["T1"] <= start + min(self.result_seconds),
            "actual filing exceeds both source result windows",
        )

    def check_release(self, result: dict[str, Any], filing: dict[str, Any]) -> None:
        require(
            self.result_start is not None
            and filing["T1"] <= result["T0"] <= result["T1"]
            <= self.result_start + min(self.result_seconds),
            "actual release exceeds source result window",
        )

    def certificate(self, binding: dict[str, Any]) -> CheckedAcquisitionInput:
        binding["verified_plan"] = self.plan
        binding["supporting_verifier_sha256"] = self.plan["source_tree"][
            "scripts/p17_m2_content_verified_independent.py"
        ]
        binding["source_input_accepted"] = self.formal_authority
        binding["formal_authority"] = self.formal_authority
        binding["B_C_admission"] = False
        return CheckedAcquisitionInput(binding, _authority=_ACQUISITION_AUTHORITY)


def audit_certificate(
    bundle: dict[str, Any], *, trusted_tool_events: dict[str, list[dict[str, Any]]]
) -> CheckedAcquisitionInput:
    """Replay new native/source/backup/lease/charges; a rehearsal stays nonformal."""
    require(
        isinstance(bundle, dict) and isinstance(bundle.get("plan"), dict),
        "independent source certificate requires complete actual evidence",
    )
    policy = _AcquisitionCertificatePolicy(bundle["plan"])
    return native._audit_certificate(bundle, trusted_tool_events=trusted_tool_events, policy=policy)


audit_source_certificate = audit_certificate


def validate_setup(
    bundle: dict[str, Any], proof: dict[str, Any], actual_precheck: dict[str, Any]
) -> None:
    """Bind deferred setup facts to the first actual native check and frozen plan."""
    plan = bundle["plan"]
    validate_binding(plan)
    setup, initial = bundle["setup"], bundle["initial_lease"]
    plan_sha = digest(canonical(plan))
    tree_sha = digest(canonical(plan["source_tree"]))
    require(
        proof["setup_proof_sha256"] == digest(canonical(setup))
        and setup["plan_sha256"] == bundle["plan_sha256"] == plan_sha
        and setup["execution_identity"] == plan["execution_identity"]
        and setup["scope"] == plan["scope"]
        and setup["contract_sha256"] == plan["contract_sha256"]
        and setup["source_tree_sha256"] == initial["source_tree_sha256"] == tree_sha
        and initial["plan_sha256"] == plan_sha
        and setup["lease_record_sha256"] == digest(canonical(initial))
        and setup["lease_identity"] == bundle["initial_lease_identity"],
        "setup plan/source/contract/lease binding differs",
    )
    physical = native._root_tuple(setup["lease_identity"])
    require(
        physical["st_size"] == len(canonical(initial))
        and initial["scope"] == "COOPERATIVE_REGISTERED_TOPOLAB_ONLY"
        and initial["execution_identity"] == plan["execution_identity"]
        and initial["root"] == plan["content_root"]
        and initial["version_id"] is None
        and initial["state"] == "HELD"
        and initial["registered_readers"] == [*ROLE_ORDER, "final-filing"]
        and bundle["backup"]["custody_log"][0] == initial
        and all(
            lease[key] == initial[key]
            for lease in (bundle["backup"]["custody_lease"], bundle["lease"])
            for key in ("plan_sha256", "source_tree_sha256")
        ),
        "setup initial lease identity/reader binding differs",
    )
    start = native.number(setup["setup_start_UTC_seconds"], positive=True)
    end = native.number(setup["setup_end_UTC_seconds"], positive=True)
    seconds = native.number(setup["setup_seconds"])
    acquired = native.number(initial["acquired_UTC_seconds"], positive=True)
    native.number(initial["acquired_monotonic"], positive=True)
    require(
        start == plan["actor_activation_UTC_seconds"]
        and start <= acquired <= end <= actual_precheck["T0"]
        and 0 <= end - start <= 300
        and 0 <= seconds <= 300,
        "setup exceeds fixed window or first actual native precheck",
    )
    if plan["scope"] == FORMAL_SCOPE:
        authority = native.base.parse(native._software_bytes(REPO / _protocol_path(plan)))
        if plan["execution_identity"] == FUNDED_IDENTITY:
            check_funded_preflight(plan, native._software_bytes(
                Path(authority["independent_preflight_path"])))
            for closure in authority["preparation_closure_paths"]:
                require(digest(native._software_bytes(Path(closure)))
                        == authority["preparation_closure_sha256"],
                        "funded preparation closure metadata changed")
        ready = setup["readiness"]
        filesystem = setup["filesystem"]
        require(
            ready["actors"] == authority["actors"]
            and ready["preparation_closure_sha256"] == authority["preparation_closure_sha256"]
            and ready["independent_preflight_sha256"] == authority["independent_preflight_sha256"]
            and isinstance(ready["main"], str)
            and re.fullmatch("[0-9a-f]{40}", ready["main"])
            and type(ready["main_CI_run"]) is int
            and ready["main_CI_run"] > 0
            and filesystem["local_filesystem"] is True
            and filesystem["basis"] == "DARWIN_FSTATFS64_MNT_LOCAL"
            and type(filesystem["available_bytes"]) is int
            and filesystem["available_bytes"] >= 2 * 1024**3
            and plan["actor_activation_UTC_seconds"]
            <= start
            <= end
            <= plan["actor_activation_UTC_seconds"] + 300,
            "formal setup lacks separately bound readiness/locality/capacity facts",
        )
