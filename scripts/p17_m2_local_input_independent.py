"""Independent local-version software checks; no source role or admission grant.

Uses only the existing independent reader/IEEE comparator. A manifest is content
identity, not proof of origins or permission to consume. This module never reads
an original source through a command-line entry.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_spec = importlib.util.spec_from_file_location(
    "local_input_base_independent", Path(__file__).with_name("p17_m2_input_export_independent.py")
)
assert _spec and _spec.loader
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

IDENTITY = "topolab.v2.p17-m2-local-input-version.v1"
MANIFEST_SCHEMA = "topolab.v2.m2-local-input-content.v1"
CONTENT_SCOPE_SHA256 = "f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad"
MIB = 1048576
CAPS = {
    "registry": 8 * MIB,
    "checkpoint": MIB,
    "models": MIB,
    "nn-producer": 128 * 1024,
    "nn-audit": 2 * MIB,
    "uniform-scalars": 65536,
}
EPOCHS = {"C": (168, 137, 92), "P": (123, 134, 169), "W": (93, 156, 142), "S": (65, 115, 127)}


def expected_members(registry: dict[str, Any]) -> dict[str, str]:
    """Derive the finite local namespace from the separately accepted registry."""
    models = registry["models"]
    expected = {
        (family, seed, epoch)
        for family, epochs in EPOCHS.items()
        for seed, epoch in zip((17, 29, 43), epochs, strict=True)
    }
    base.require(
        isinstance(models, list)
        and len(models) == 12
        and {(m["family"], m["seed"], m["epoch"]) for m in models} == expected,
        "local manifest fixed checkpoint population differs",
    )
    labels = registry["labels"]
    base.require(
        isinstance(labels, list) and len(labels) == 528, "local manifest requires exact528 labels"
    )
    names = [item["case_id"] for item in labels]
    base.require(
        len(set(names)) == 528
        and all(isinstance(n, str) and base.CASE.fullmatch(n) for n in names),
        "local manifest case IDs duplicate or invalid",
    )
    result = {
        "source_registry.json": "registry",
        "models.json": "models",
        "uniform-scalars.json": "uniform-scalars",
    }
    for model in models:
        result[f"checkpoints/{model['family']}-{model['seed']}.safetensors"] = "checkpoint"
    for name in names:
        for view in ("producer", "audit"):
            result[f"nn/{view}/{name}.json"] = "nn-" + view
    return result


def validate_manifest(
    manifest: dict[str, Any], registry: dict[str, Any], contract_sha256: str
) -> dict[str, Any]:
    """Check exact identity/scope; this does not accept content or an experiment."""
    base.require(
        isinstance(manifest, dict)
        and set(manifest)
        == {
            "schema",
            "frozen_contract_sha256",
            "content_scope_sha256",
            "source_registry_sha256",
            "members",
            "role_views",
        },
        "local manifest field set differs",
    )
    base.require(
        isinstance(contract_sha256, str)
        and base.SHA.fullmatch(contract_sha256)
        and manifest["schema"] == MANIFEST_SCHEMA
        and manifest["frozen_contract_sha256"] == contract_sha256
        and manifest["content_scope_sha256"] == CONTENT_SCOPE_SHA256
        and manifest["source_registry_sha256"] == base.digest(base.canonical(registry)),
        "local manifest contract, schema or registry identity differs",
    )
    expected = expected_members(registry)
    members = manifest["members"]
    base.require(
        isinstance(members, list) and len(members) == 1071,
        "local manifest requires exactly1071 members",
    )
    paths = []
    totals = dict.fromkeys(CAPS, 0)
    for row in members:
        base.require(
            isinstance(row, dict) and set(row) == {"path", "type", "byte_size", "sha256"},
            "local manifest member fields differ",
        )
        name = row["path"]
        base.require(
            isinstance(name, str) and name in expected and row["type"] == expected[name],
            "local manifest unregistered member or type",
        )
        kind = row["type"]
        base.require(
            type(row["byte_size"]) is int
            and 0 < row["byte_size"] <= CAPS[kind]
            and isinstance(row["sha256"], str)
            and base.SHA.fullmatch(row["sha256"]),
            "local manifest member bytes/hash invalid",
        )
        paths.append(name)
        totals[kind] += row["byte_size"]
    base.require(paths == sorted(expected), "local manifest member order/set differs")
    base.require(
        totals["checkpoint"] <= 12 * MIB
        and totals["nn-producer"] <= 32 * MIB
        and totals["nn-audit"] <= 256 * MIB,
        "local manifest output total cap",
    )
    producer = sorted(
        p for p in expected if p == "models.json" or p.startswith(("checkpoints/", "nn/producer/"))
    )
    auditor = sorted(producer + [p for p in expected if p.startswith("nn/audit/")])
    base.require(
        manifest["role_views"]
        == {
            "scientific-producer": producer,
            "scientific-auditor": auditor,
            "reference-compatibility": ["uniform-scalars.json"],
        },
        "local manifest proposed role views differ",
    )
    registry_member = next(row for row in members if row["path"] == "source_registry.json")
    base.require(
        registry_member["sha256"] == manifest["source_registry_sha256"]
        and registry_member["byte_size"] == len(base.canonical(registry)),
        "local manifest registry member differs",
    )
    raw = base.canonical(manifest)
    base.require(len(raw) <= 2 * MIB, "local manifest byte cap")
    return {
        "status": "MANIFEST_SHAPE_CHECKED_ONLY",
        "version_id": base.digest(raw),
        "member_count": 1071,
        "consumer_authorized": False,
    }


def identity_table(rows: list[dict[str, Any]], count: int) -> dict[str, dict[str, Any]]:
    """Check separately observed original OR local tuples, without mixing roots."""
    base.require(isinstance(rows, list) and len(rows) == count, "identity exact count differs")
    table = {}
    for row in rows:
        base.require(
            isinstance(row, dict)
            and set(row)
            == {"path", "byte_size", "sha256", "declared", "before", "after", "closing"},
            "identity row field set differs",
        )
        name = row["path"]
        pieces = base.PurePosixPath(name) if isinstance(name, str) else None
        base.require(
            pieces is not None
            and not pieces.is_absolute()
            and ".." not in pieces.parts
            and name == pieces.as_posix()
            and name not in ("", ".")
            and name not in table,
            "identity unsafe or duplicate path",
        )
        base.require(
            type(row["byte_size"]) is int
            and row["byte_size"] > 0
            and isinstance(row["sha256"], str)
            and base.SHA.fullmatch(row["sha256"]),
            "identity row bytes/hash invalid",
        )
        for stage in ("declared", "before", "after", "closing"):
            value = row[stage]
            base.require(
                isinstance(value, dict)
                and set(value) == {"st_dev", "st_ino", "st_size", "st_mtime_ns"}
                and all(type(v) is int and v >= 0 for v in value.values()),
                "identity row observation missing",
            )
            base.require(
                value == row["before"] and value["st_size"] == row["byte_size"],
                "identity changed within read",
            )
        table[name] = row
    return table


def audit_local_content(
    root: Path,
    manifest: dict[str, Any],
    registry: dict[str, Any],
    local_identity_rows: list[dict[str, Any]],
    contract_sha256: str,
) -> dict[str, Any]:
    """Read only NEW content. This cannot replace independent original comparison."""
    result = validate_manifest(manifest, registry, contract_sha256)
    literal = Path(base.os.path.abspath(root))
    base.require(
        not literal.is_relative_to(base.AUTHORIZED_DATA_ROOT),
        "local content verification cannot read original DATA",
    )
    expected = {row["path"]: row for row in manifest["members"]}
    recorded = identity_table(local_identity_rows, 1071)
    base.require(set(recorded) == set(expected), "local identity member set differs")
    for name, row in expected.items():
        base.require(
            all(recorded[name][key] == row[key] for key in ("byte_size", "sha256")),
            "local identity bytes/hash differ from manifest",
        )
    # Only a finite NEW tree may be inventoried; discoveries never enlarge the allowlist.
    directories = {base.PurePosixPath(name).parent.as_posix() for name in expected}
    directories |= {"nn"}

    def inventory():
        pending, actual, visited = [(base.nofollow_parent(literal / ".inventory"), "")], set(), 0
        try:
            while pending:
                directory, prefix = pending.pop()
                try:
                    info = base.os.fstat(directory)
                    base.require(
                        info.st_uid == base.os.geteuid()
                        and base.stat.S_IMODE(info.st_mode) == 0o700,
                        "new content directory is not private",
                    )
                    with base.os.scandir(directory) as entries:
                        for entry in entries:
                            visited += 1
                            base.require(visited <= 4096, "new content inventory cap")
                            name = prefix + entry.name
                            base.require(not entry.is_symlink(), "new content symlink refused")
                            if entry.is_dir(follow_symlinks=False):
                                base.require(
                                    name in directories, "new content unregistered directory"
                                )
                                child = base.os.open(
                                    entry.name,
                                    base.os.O_RDONLY | base.os.O_DIRECTORY | base.os.O_NOFOLLOW,
                                    dir_fd=directory,
                                )
                                pending.append((child, name + "/"))
                            else:
                                base.require(
                                    entry.is_file(follow_symlinks=False) and name in expected,
                                    "new content extra or nonregular member",
                                )
                                info = entry.stat(follow_symlinks=False)
                                base.require(
                                    info.st_uid == base.os.geteuid()
                                    and base.stat.S_IMODE(info.st_mode) == 0o600
                                    and info.st_nlink == 1,
                                    "new content file is not private or is a hardlink",
                                )
                                actual.add(name)
                finally:
                    base.os.close(directory)
        finally:
            for directory, _ in pending:
                base.os.close(directory)
        base.require(actual == set(expected), "new content missing member")

    inventory()
    reader = base.OnceReader(literal, 1071, 384 * MIB, source_identity_checks=True)
    for row in manifest["members"]:
        raw = reader.read(
            row["path"], CAPS[row["type"]], sha256=row["sha256"], byte_size=row["byte_size"]
        )
        base.compare_words(reader.observations[-1], recorded[row["path"]])
        if row["path"] == "source_registry.json":
            base.require(raw == base.canonical(registry), "local registry actual bytes differ")
    inventory()
    result.update(
        status="NEW_CONTENT_IDENTITIES_CHECKED_ONLY",
        new_member_reads=1071,
        old_source_reads=0,
        original_semantics_accepted=False,
        local_identity_rows=reader.observations,
    )
    return result


def compare_source_sets(
    producer: dict[str, Any], independent: dict[str, Any], stage: str
) -> dict[str, Any]:
    """Compare complete original-source observations from the same NEW identity."""
    base.require(stage in ("r0", "r1"), "source comparison stage differs")
    count = 40 if stage == "r0" else 558
    tables = []
    for sidecar in (producer, independent):
        base.require(
            isinstance(sidecar, dict)
            and set(sidecar) == {"schema", "execution_identity", "rows"}
            and sidecar["schema"] == "topolab.v2.m2-source-identity-sidecar.v1"
            and sidecar["execution_identity"] == IDENTITY,
            "source identity sidecar binding differs",
        )
        tables.append(identity_table(sidecar["rows"], count))
    base.compare_words(tables[0], tables[1])
    return {
        "status": "SOURCE_OBSERVATIONS_MATCHED_ONLY",
        "stage": stage,
        "source_count": count,
        "consumer_authorized": False,
    }


def assess_target_evidence(receipt: dict[str, Any], root: str, backup: str) -> dict[str, Any]:
    """Screen attributed evidence; a positive shape still needs independent raw review.

    Does not stat a target, follow a reference, infer negative coverage from flags,
    acquire a lease or grant original input/formal access.
    """
    gaps = []

    def check(condition, message):
        if not condition:
            gaps.append(message)

    def refs(value, *, custodian=False):
        if not isinstance(value, list) or not value:
            return False
        for item in value:
            if not (
                isinstance(item, dict)
                and set(item) == {"path", "sha256", "provenance"}
                and isinstance(item["path"], str)
                and item["path"].startswith("/")
                and isinstance(item["sha256"], str)
                and base.SHA.fullmatch(item["sha256"])
                and item["provenance"]
                in (
                    "trusted_outer_tool_return",
                    "native_configuration",
                    "responsible_custodian_statement",
                )
            ):
                return False
        return not custodian or any(
            item["provenance"] == "responsible_custodian_statement" for item in value
        )

    check(isinstance(receipt, dict), "target evidence missing")
    packet = receipt if isinstance(receipt, dict) else {}
    check(
        packet.get("schema") == "topolab.v2.m2-local-target-evidence.v1"
        and packet.get("execution_identity") == IDENTITY,
        "target identity/schema missing",
    )
    check(
        packet.get("root") == root and packet.get("backup") == backup,
        "literal root/backup evidence differs",
    )
    elapsed = packet.get("elapsed_seconds")
    valid_elapsed = (
        type(elapsed) in (int, float) and base.math.isfinite(elapsed) and 0 <= elapsed <= 600
    )
    check(valid_elapsed, "target check exceeds600s or elapsed unknown")
    try:
        started, finished = packet["started_utc"], packet["finished_utc"]
        base.require(
            isinstance(started, str)
            and started.endswith("Z")
            and isinstance(finished, str)
            and finished.endswith("Z"),
            "UTC timestamp missing",
        )
        span = (
            base.datetime.fromisoformat(finished) - base.datetime.fromisoformat(started)
        ).total_seconds()
        check(
            valid_elapsed and 0 <= span <= 600 and abs(span - elapsed) <= 0.00001,
            "target actual timestamp span differs",
        )
    except (KeyError, TypeError, ValueError):
        gaps.append("target actual timestamp span missing")
    physical = packet.get("physical") or {}
    check(
        physical.get("no_symlinks") is True
        and physical.get("local_filesystem") is True
        and refs(physical.get("evidence")),
        "physical local no-symlink evidence incomplete",
    )
    private = packet.get("private_fixture") or {}
    fixture_path = private.get("path")
    check(
        isinstance(fixture_path, str)
        and Path(fixture_path).parent == Path(root).parent
        and fixture_path not in (root, backup)
        and type(private.get("owner_uid")) is int
        and private.get("owner_uid") == private.get("expected_owner_uid")
        and private.get("directory_mode") == 0o700
        and private.get("file_mode") == 0o600
        and private.get("exclusive_create") is True
        and private.get("write_flush_fsync") is True
        and refs(private.get("evidence")),
        "private exclusive fixture evidence incomplete",
    )
    for section, status in (
        ("provider_coverage", "EXCLUDED"),
        ("backup_coverage", "EXCLUDED_OR_NONMUTATING_READONLY"),
    ):
        value = packet.get(section) or {}
        check(
            value.get("status") == status
            and value.get("covered_paths") == [root, backup]
            and value.get("sources_complete") is True
            and refs(value.get("evidence")),
            section + " incomplete; negative flags alone cannot admit",
        )
    custodian = packet.get("custodian") or {}
    writers = custodian.get("controlled_writers")
    check(
        isinstance(custodian.get("actor"), str)
        and bool(custodian["actor"])
        and custodian.get("complete_writer_inventory") is True
        and custodian.get("no_uncontrolled_writers") is True
        and custodian.get("lease_plan") == "LOCAL_GENERATION_WRITER_EXCLUSION_ONLY"
        and isinstance(writers, list)
        and bool(writers)
        and all(isinstance(w, str) and w and "*" not in w for w in writers)
        and len(set(writers)) == len(writers)
        and refs(custodian.get("evidence"), custodian=True),
        "responsible custodian complete writer/control evidence missing",
    )
    return {
        "status": "NO_LOCAL_ROOT_ADMISSION"
        if gaps
        else "TARGET_PLAN_EVIDENCE_COMPLETE_PENDING_INDEPENDENT_RAW_REVIEW",
        "gaps": gaps,
        "old_source_authorized": False,
        "formal_roles_authorized": False,
    }


def check_consumption_certificate(
    certificate: Any, expected_version: str, expected_contract: str, role: str
) -> None:
    """Keep consumption closed until an actual R-LOCAL finalization verifier exists.

    There is intentionally no positive certificate schema or guessed PASS-field
    interpreter in this preparation. Actual six-role resource/outer returns,
    filing return, target release and role grants are not implemented/admitted.
    """
    raise ValueError(
        "FORMAL_LAUNCH_BINDING_INCOMPLETE: actual independent R-LOCAL "
        "resource/outer-return/finalization verifier and consumer grant unavailable"
    )
