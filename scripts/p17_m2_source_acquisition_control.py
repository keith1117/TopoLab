"""Source-acquisition binding; actual formal authority remains separately closed."""

import argparse
import base64
import ctypes
import importlib.util
import json
import math
import os
import re
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IDENTITY = "topolab.v2.p17-m2-content-verified-source-acquisition.v1"
COMPAT_IDENTITY = "topolab.v2.p17-m2-hash-bound-source-acquisition.v1"
COMPAT_PROTOCOL = "docs/planning/p17_m2_hash_bound_acquisition_protocol.json"
FUNDED_IDENTITY = "topolab.v2.p17-m2-hash-bound-source-acquisition.v2"
FUNDED_PROTOCOL = "docs/planning/p17_m2_funded_acquisition_protocol.json"
REMEDY_PROTOCOL = "docs/planning/p17_m2_funded_acquisition_remedy2_protocol.json"
REMEDY_SCHEMA = "topolab.v2.m2-funded-acquisition-remedy-authority.v1"
NEW_IDENTITY = "topolab.v2.p17-m2-hash-bound-source-acquisition.v3"
NEW_PROTOCOL = "docs/planning/p17_m2_new_source_acquisition_protocol.json"
NEW_SCHEMA = "topolab.v2.m2-new-source-acquisition-authority.v1"
NEW_PUBLIC_PREFIX = "topolab-public-new-source-acquisition-"
NEW_GENERATION = (
    "/Users/keith1117/Library/Application Support/TopoLab-custody/"
    "p17-m2-local-input-version-v7-hash-bound-20261028"
)
SOURCE_IDENTITY_POLICY = "topolab.source-identity.prebound-sha256.v1"
REHEARSAL_SCOPE = "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
FORMAL_SCOPE = "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
PROTOCOL = "docs/planning/p17_m2_source_acquisition_adapter_preparation_protocol.json"
PROPOSAL = "docs/planning/p17_m2_content_verified_source_acquisition_proposal.json"
EXECUTION_PROTOCOL = "docs/planning/p17_m2_source_acquisition_execution_protocol.json"


def load(name):
    path = Path(__file__).with_name(name + ".py")
    existing = sys.modules.get(name)
    if existing is not None and Path(existing.__file__).resolve() == path.resolve():
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("missing frozen helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def base():
    return load("p17_m2_content_verified_control")


# An authority name is never permission to follow its final link or read another path.
try:
    EXECUTION_AUTHORITY_RAW = load("p17_m2_source_acquisition_independent").native._software_bytes(
        REPO / EXECUTION_PROTOCOL
    )
except FileNotFoundError:
    EXECUTION_AUTHORITY_RAW = None


try:
    FUNDED_AUTHORITY_RAW = load("p17_m2_source_acquisition_independent").native._software_bytes(
        REPO / FUNDED_PROTOCOL
    )
except FileNotFoundError:
    FUNDED_AUTHORITY_RAW = None


try:
    REMEDY_AUTHORITY_RAW = load("p17_m2_source_acquisition_independent").native._software_bytes(
        REPO / REMEDY_PROTOCOL
    )
except FileNotFoundError:
    REMEDY_AUTHORITY_RAW = None


try:
    NEW_AUTHORITY_RAW = load("p17_m2_source_acquisition_independent").native._software_bytes(
        REPO / NEW_PROTOCOL
    )
except FileNotFoundError:
    NEW_AUTHORITY_RAW = None


def is_funded_authority(raw):
    return raw is not None and (
        raw is FUNDED_AUTHORITY_RAW or raw is REMEDY_AUTHORITY_RAW or raw is NEW_AUTHORITY_RAW
    )


def authority_for_root(root):
    """Select only registered literals before any source or custody traversal."""
    literal = str(Path(os.path.abspath(root)))
    if literal == NEW_GENERATION:
        return NEW_AUTHORITY_RAW, 1
    need(Path(literal).name != Path(NEW_GENERATION).name, "FORMAL_LITERAL_ROOT_REQUIRED")
    if (REMEDY_AUTHORITY_RAW is not None and literal ==
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-local-input-version-v6-hash-bound-20261026"):
        return REMEDY_AUTHORITY_RAW, 2
    if FUNDED_AUTHORITY_RAW is not None:
        # Literal routing is memory-only; full strict parsing precedes any setup.
        authority = json.loads(FUNDED_AUTHORITY_RAW)
        for attempt, target in authority["fixed_target"]["attempts"].items():
            if literal == target["generation"]:
                return FUNDED_AUTHORITY_RAW, int(attempt)
        need(
            Path(literal).name
            not in {
                Path(t["generation"]).name for t in authority["fixed_target"]["attempts"].values()
            },
            "FORMAL_LITERAL_ROOT_REQUIRED",
        )
    return EXECUTION_AUTHORITY_RAW, 1


def source_freeze(execution_identity=None):
    paths = {
        *REPO.joinpath("scripts").glob("p17_m2_*.py"),
        *REPO.joinpath("scripts").glob("p17_m2_*.js"),
        REPO / PROTOCOL,
        REPO / PROPOSAL,
        REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json",
        REPO / "docs/planning/p17_m2_content_verified_custody_protocol.json",
        REPO / "docs/planning/p17_m2_content_verified_custody_proposal.json",
    }
    if EXECUTION_AUTHORITY_RAW is not None:
        paths.add(REPO / EXECUTION_PROTOCOL)
    if (REPO / COMPAT_PROTOCOL).is_file():
        paths.add(REPO / COMPAT_PROTOCOL)
    if (REPO / FUNDED_PROTOCOL).is_file():
        paths.add(REPO / FUNDED_PROTOCOL)
    if (REPO / REMEDY_PROTOCOL).is_file():
        paths.add(REPO / REMEDY_PROTOCOL)
    if execution_identity == NEW_IDENTITY:
        paths.add(REPO / NEW_PROTOCOL)
        paths.update(REPO.joinpath("scripts").glob("p17_m2_*.mjs"))
    return {str(p.relative_to(REPO)): base().sha(p.read_bytes()) for p in sorted(paths)}


def rehearsal_root(root):
    root = Path(os.path.abspath(root))
    need(
        root.name.startswith(
            (
                "topolab-public-formal-binding-",
                "topolab-public-hash-bound-",
                "topolab-public-funded-acquisition-",
                NEW_PUBLIC_PREFIX,
            )
        ),
        "REHEARSAL_ROOT_REQUIRED",
    )
    return base().public_root(root)


def argv_for(root, mode, plan_sha, role, *, reader_role="scientific-producer"):
    argv = [
        str(Path(sys.orig_argv[0]).resolve()),
        "-I",
        str(Path(__file__).resolve()),
        mode,
        "--root",
        str(root),
        "--plan-sha",
        plan_sha,
        "--role",
        role,
    ]
    if role in ("public-consumer", "reader-ack"):
        argv += ["--reader-role", reader_role]
    return argv


def make_plan(root, contract, source_identity):
    """Build the public projection; formal_plan replaces only declared authority inputs."""
    helper = base()
    now = round(time.time(), 3)
    end = datetime.fromtimestamp(now + 4500, UTC).isoformat(timespec="milliseconds")
    new = root.name.startswith(NEW_PUBLIC_PREFIX) or str(root) == NEW_GENERATION
    funded = new or root.name.startswith("topolab-public-funded-acquisition-")
    compat = funded or root.name.startswith("topolab-public-hash-bound-")
    remedy = root.name.startswith("topolab-public-funded-acquisition-remedy2-")
    protocol_path = (NEW_PROTOCOL if new else REMEDY_PROTOCOL if remedy
                     else FUNDED_PROTOCOL if funded else COMPAT_PROTOCOL if compat else PROTOCOL)
    protocol_sha = helper.sha((REPO / protocol_path).read_bytes())
    proposal_sha = helper.sha((REPO / PROPOSAL).read_bytes())
    return {
        "schema": "topolab.v2.m2-source-acquisition-plan.v1",
        "execution_identity": (
            NEW_IDENTITY if new else FUNDED_IDENTITY if funded else COMPAT_IDENTITY if compat
            else IDENTITY
        ),
        **({"source_identity_policy": SOURCE_IDENTITY_POLICY} if compat else {}),
        "scope": REHEARSAL_SCOPE,
        "formal_authority": False,
        "root": str(root),
        "source_root": str(root / "public-source"),
        "content_root": str(root / "content"),
        "backup_root": str(root / "backup-content"),
        "content_contract": contract,
        "public_source_identity": source_identity,
        "proposal_sha256": proposal_sha,
        "preparation_contract_sha256": protocol_sha,
        "contract_sha256": protocol_sha,
        "binding": {
            "proposal_sha256": proposal_sha,
            "content_contract_sha256": helper.sha(helper.canonical(contract)),
            "preparation_protocol_sha256": protocol_sha,
            "intended_formal_scope": FORMAL_SCOPE,
            "formal_authority": False,
            "old_original_access": False,
            "target_access": False,
            "B_C": False,
            **({"source_identity_policy": SOURCE_IDENTITY_POLICY} if compat else {}),
            **({"authority_protocol_path": protocol_path} if funded else {}),
        },
        "source_tree": source_freeze(NEW_IDENTITY if new else None),
        "runtime": helper.runtime(),
        "role_order": list(helper.CAPS),
        "roles": {r: {"argv": argv_for(root, "payload", "@PLAN_SHA256@", r)} for r in helper.CAPS},
        "metadata_actions": {
            r: {"argv": argv_for(root, "payload", "@PLAN_SHA256@", r, reader_role="@READER_ROLE@")}
            for r in helper.METADATA_CAPS
        },
        "registered_reader_lease_sibling": "content.cooperative-reader.lease",
        "actor_activation_UTC_seconds": now,
        "actor_window_seconds": 4500,
        "actor_deadlines_UTC": {k: end.replace("+00:00", "Z") for k in ("exporter", "independent")},
        "result_window_projection_seconds": {
            "exporter": 9000 if new else 7200, "independent": 9000 if new else 7200,
        },
    }


def public_source_plan_context(path, expected):
    """Only an explicitly named NEW funded public graph can feed this fixture."""
    path = Path(os.path.abspath(path))
    need(
        path.name == "plan.json"
        and path.parent.name.startswith("topolab-public-funded-acquisition-"),
        "PUBLIC_FUNDED_SOURCE_PLAN_REQUIRED",
    )
    rehearsal_root(path.parent)
    checker = load("p17_m2_source_acquisition_independent")
    raw = checker.native._software_bytes(path)
    need(base().sha(raw) == expected, "PUBLIC_SOURCE_PLAN_HASH_CHANGED")
    old = checker.native.base.parse(raw)
    need(
        old.get("schema") == "topolab.v2.m2-source-acquisition-plan.v1"
        and old.get("execution_identity") == FUNDED_IDENTITY
        and old.get("source_identity_policy") == SOURCE_IDENTITY_POLICY
        and old.get("scope") == REHEARSAL_SCOPE
        and old.get("formal_authority") is False
        and old.get("root") == str(path.parent)
        and old.get("source_root") == str(path.parent / "public-source"),
        "PUBLIC_FUNDED_SOURCE_GRAPH_REQUIRED",
    )
    permissions = old.get("binding", {})
    need(
        isinstance(permissions, dict)
        and all(
            permissions.get(key) is False
            for key in ("formal_authority", "old_original_access", "target_access", "B_C")
        ),
        "PUBLIC_SOURCE_PLAN_PERMISSIONS_REFUSED",
    )
    need(
        not {"public_source_plan", "public_source_plan_sha256"} & set(permissions),
        "PUBLIC_SOURCE_COPY_CHAIN_REFUSED",
    )
    # This prebound historical plan supplies NEW public data provenance only.
    # The newly prepared plan separately validates the current full authority.
    checker._content_projection(old)
    return path, old


def copy_public_source(root, source, *, began):
    helper = base()
    checker = load("p17_m2_input_export_independent")
    reader = checker.OnceReader(source, 598, 1024**3, source_identity_checks=True)
    proof = []
    relative = None
    inventory_cursor = None
    try:
        paths = []
        entries_seen = 0

        def inventory(directory, prefix=""):
            nonlocal entries_seen, inventory_cursor
            with os.scandir(directory) as entries:
                for entry in entries:
                    entries_seen += 1
                    relative = prefix + entry.name
                    inventory_cursor = {"path": relative, "raw_stat": None}
                    need(entries_seen <= 4096, "PUBLIC_SOURCE_NAMESPACE_CAP")
                    info = entry.stat(follow_symlinks=False)
                    inventory_cursor["raw_stat"] = {
                        key: getattr(info, key)
                        for key in (
                            "st_dev",
                            "st_ino",
                            "st_size",
                            "st_mtime_ns",
                            "st_mode",
                            "st_nlink",
                        )
                    }
                    if stat.S_ISDIR(info.st_mode):
                        child = os.open(
                            entry.name,
                            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory,
                        )
                        try:
                            inventory(child, relative + "/")
                        finally:
                            os.close(child)
                    else:
                        need(
                            stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                            "PUBLIC_SOURCE_FILE_KIND_REFUSED",
                        )
                        paths.append(relative)
                        need(len(paths) <= 598, "EXACT_PUBLIC598_SOURCE_GRAPH_REQUIRED")

        directory = helper.nofollow_directory(source)
        try:
            inventory(directory)
        finally:
            os.close(directory)
        need(len(paths) == 598, "EXACT_PUBLIC598_SOURCE_GRAPH_REQUIRED")
        destination = root / "public-source"
        destination.mkdir(mode=0o700)
        for relative in sorted(paths):
            need(time.monotonic() - began <= 300, "PUBLIC_SOURCE_COPY300_EXHAUSTED")
            raw = reader.read(relative, 128 * 1024**2)
            target = destination / relative
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                view = memoryview(raw)
                while view:
                    wrote = os.write(fd, view)
                    need(wrote > 0, "PUBLIC_SOURCE_COPY_SHORT_WRITE")
                    view = view[wrote:]
                os.fsync(fd)
            finally:
                os.close(fd)
            physical = target.stat()
            original = reader.source_facts[relative]["before"]
            need(
                (physical.st_dev, physical.st_ino) != (original["st_dev"], original["st_ino"]),
                "PUBLIC_SOURCE_COPY_INODE_NOT_INDEPENDENT",
            )
            need(
                helper.sha(target.read_bytes()) == helper.sha(raw),
                "PUBLIC_SOURCE_COPY_HASH_CHANGED",
            )
            proof.append(
                {
                    "path": relative,
                    "sha256": helper.sha(raw),
                    "byte_size": len(raw),
                    "destination_identity": checker.source_identity(physical),
                }
            )
        helper.put(
            root / "public-source-copy.json",
            {
                "source_root": str(source),
                "destination_root": str(destination),
                "source_observations": reader.observations,
                "source_facts": reader.source_facts,
                "copies": proof,
                "old_original_reads": 0,
                "formal_authority": False,
                "wall_seconds": time.monotonic() - began,
            },
        )
    except BaseException as error:
        failure = {
            "status": "STOP_PUBLIC_COPY",
            "error_type": type(error).__name__,
            "reason": str(error),
            "source_root": str(source),
            "current": relative,
            "inventory_cursor": inventory_cursor,
            "source_facts": reader.source_facts,
            "source_observations": reader.observations,
            "copies": proof,
            "wall_seconds": time.monotonic() - began,
            "byte_cap": 1024**3,
            "file_cap": 598,
            "old_original_reads": 0,
            "own_future_exit": "UNKNOWN_PENDING_ACTUAL_OUTER_RETURN",
            "secondary_errors": [],
        }
        try:
            helper.put(root / "public-source-copy-failure.json", failure)
        except BaseException as secondary:
            failure["secondary_errors"].append(
                {
                    "stage": "copy failure filing",
                    "type": type(secondary).__name__,
                    "reason": str(secondary),
                }
            )
        error.public_copy_failure = failure
        sys.stderr.buffer.write(helper.canonical(failure))
        sys.stderr.buffer.flush()
        raise


def prepare_rehearsal(root, *, public_source_plan=None, public_source_plan_sha=None):
    root = rehearsal_root(root)
    context = None
    if public_source_plan is not None or public_source_plan_sha is not None:
        need(
            root.name.startswith("topolab-public-funded-acquisition-")
            and public_source_plan is not None
            and public_source_plan_sha is not None,
            "PUBLIC_FUNDED_FIXTURE_REUSE_ONLY",
        )
        path, context = public_source_plan_context(public_source_plan, public_source_plan_sha)
    helper = base()
    parent = helper.nofollow_directory(root.parent)
    try:
        os.mkdir(root.name, mode=0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    if context is None:
        contract, source_identity = load("p17_m2_content_verified_public_fixture").create_sources(
            root / "public-source", load("p17_m2_input_export_independent")
        )
    else:
        copy_public_source(root, Path(context["source_root"]), began=time.monotonic())
        contract, source_identity = context["content_contract"], context["public_source_identity"]
    plan = make_plan(root, contract, source_identity)
    if context is not None:
        plan["binding"].update(
            public_source_plan=str(path), public_source_plan_sha256=public_source_plan_sha
        )
    helper.put(root / "plan.json", plan)
    began = time.monotonic()
    initial_lease(root, plan)
    finish_setup(root, plan, began=began)
    return {
        "plan_sha256": helper.sha(helper.canonical(plan)),
        "scope": REHEARSAL_SCOPE,
        "formal_authority": False,
    }


def initial_lease(root, plan):
    helper = base()
    acquired = {
        "scope": "COOPERATIVE_REGISTERED_TOPOLAB_ONLY",
        "execution_identity": plan["execution_identity"],
        "plan_sha256": helper.sha(helper.canonical(plan)),
        "source_tree_sha256": helper.sha(helper.canonical(plan["source_tree"])),
        "root": plan["content_root"],
        "state": "HELD",
        "version_id": None,
        "registered_readers": list(helper.CAPS) + ["final-filing"],
        "acquired_UTC_seconds": time.time(),
        "acquired_monotonic": time.monotonic(),
    }
    helper.put(root / "custody-acquired.json", acquired)
    lock = helper.put(root / "content.cooperative-reader.lease", acquired)
    helper.put(root / "custody-lock-identity.json", lock)


def local_filesystem(descriptor):
    """Darwin SDK sys/mount.h statfs64 layout and MNT_LOCAL; no provider inference."""
    need(sys.platform == "darwin", "UNSUPPORTED_LOCAL_FILESYSTEM_ADMISSION")

    class StatFS64(ctypes.Structure):
        _fields_ = [
            ("bsize", ctypes.c_uint32),
            ("iosize", ctypes.c_int32),
            ("blocks", ctypes.c_uint64),
            ("bfree", ctypes.c_uint64),
            ("bavail", ctypes.c_uint64),
            ("files", ctypes.c_uint64),
            ("ffree", ctypes.c_uint64),
            ("fsid", ctypes.c_int32 * 2),
            ("owner", ctypes.c_uint32),
            ("type", ctypes.c_uint32),
            ("flags", ctypes.c_uint32),
            ("subtype", ctypes.c_uint32),
            ("fstypename", ctypes.c_char * 16),
            ("mntonname", ctypes.c_char * 1024),
            ("mntfromname", ctypes.c_char * 1024),
            ("flags_ext", ctypes.c_uint32),
            ("reserved", ctypes.c_uint32 * 7),
        ]

    info = StatFS64()
    call = ctypes.CDLL(None, use_errno=True).fstatfs64
    call.argtypes, call.restype = [ctypes.c_int, ctypes.POINTER(StatFS64)], ctypes.c_int
    if call(descriptor, ctypes.byref(info)) != 0:
        raise OSError(ctypes.get_errno(), "fstatfs64 failed")
    need(info.flags & 0x00001000 and not info.flags & 1, "WRITABLE_LOCAL_FILESYSTEM_REQUIRED")
    return dict(
        local_filesystem=True,
        filesystem=info.fstypename.decode("ascii"),
        available_bytes=info.bavail * info.bsize,
        basis="DARWIN_FSTATFS64_MNT_LOCAL",
    )


def setup_formal(plan, readiness):
    """Future-only unique setup; authority has already passed before target traversal."""
    need(authority_for_root(plan["root"])[0] is not None, "FORMAL_AUTHORITY_NOT_GRANTED")
    helper = base()
    root, backup = Path(plan["root"]), Path(plan["backup_root"])
    parent = root.parent
    began = time.monotonic()
    ancestor = helper.nofollow_directory(parent.parent)
    try:
        try:
            os.mkdir(parent.name, mode=0o700, dir_fd=ancestor)
            os.fsync(ancestor)
        except FileExistsError:
            pass
        directory = os.open(
            parent.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=ancestor
        )
    finally:
        os.close(ancestor)
    try:
        info = os.fstat(directory)
        need(
            info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700,
            "PRIVATE_CUSTODY_PARENT_REQUIRED",
        )
        locality = local_filesystem(directory)
        need(locality["available_bytes"] >= 2 * 1024**3, "TARGET_CAPACITY_UNAVAILABLE")
        for name in (root.name, backup.name):
            try:
                os.stat(name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise ValueError("GENERATION_OR_BACKUP_ALREADY_EXISTS_STOP_NO_RETRY")
        os.mkdir(root.name, mode=0o700, dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)
    helper.put(root / "plan.json", plan)
    initial_lease(root, plan)
    need(time.monotonic() - began <= 300, "SETUP_WINDOW_EXCEEDED_STOP_NO_RETRY")
    need(
        plan["actor_activation_UTC_seconds"] + 4500 - time.time() >= 4200,
        "FIRST_ROLE_FULL_SUFFIX_UNAVAILABLE",
    )
    finish_setup(root, plan, began=began, readiness=readiness, locality=locality)
    return dict(
        plan_sha256=helper.sha(helper.canonical(plan)),
        scope=FORMAL_SCOPE,
        formal_authority=True,
        source_stat_reads=0,
    )


def finish_setup(root, plan, *, began, readiness=None, locality=None):
    helper = base()
    proof = dict(
        status="TARGET_AND_INITIAL_COOPERATIVE_LEASE_ACQUIRED",
        execution_identity=plan["execution_identity"],
        scope=plan["scope"],
        plan_sha256=helper.sha(helper.canonical(plan)),
        contract_sha256=plan["contract_sha256"],
        source_tree_sha256=helper.sha(helper.canonical(plan["source_tree"])),
        lease_record_sha256=helper.sha(
            helper.canonical(helper.read_json(root / "custody-acquired.json"))
        ),
        lease_identity=helper.read_json(root / "custody-lock-identity.json"),
        setup_start_UTC_seconds=plan["actor_activation_UTC_seconds"],
        setup_end_UTC_seconds=time.time(),
        setup_seconds=max(
            time.monotonic() - began, time.time() - plan["actor_activation_UTC_seconds"]
        ),
        readiness=readiness,
        formal_readiness_verified=plan["formal_authority"],
        filesystem=locality,
        source_stat_reads=0,
        backup_created=False,
        no_never_sync_or_external_writer_guarantee=True,
    )
    need(0 <= proof["setup_seconds"] <= 300, "SETUP_WINDOW_EXCEEDED_STOP_NO_RETRY")
    helper.put(root / "setup-proof.json", proof)
    return proof


def checked_setup(root, plan):
    helper = base()
    proof = helper.read_json(root / "setup-proof.json")
    acquired = helper.read_json(root / "custody-acquired.json")
    plan_sha, source_sha = (
        helper.sha(helper.canonical(plan)),
        helper.sha(helper.canonical(plan["source_tree"])),
    )
    need(
        proof["plan_sha256"] == acquired["plan_sha256"] == plan_sha
        and proof["contract_sha256"] == plan["contract_sha256"]
        and proof["source_tree_sha256"] == acquired["source_tree_sha256"] == source_sha
        and proof["lease_record_sha256"] == helper.sha(helper.canonical(acquired))
        and proof["lease_identity"] == helper.read_json(root / "custody-lock-identity.json")
        and proof["scope"] == plan["scope"]
        and proof["execution_identity"] == plan["execution_identity"]
        and proof["setup_start_UTC_seconds"] == plan["actor_activation_UTC_seconds"]
        and 0 <= proof["setup_seconds"] <= 300
        and proof["setup_start_UTC_seconds"] <= proof["setup_end_UTC_seconds"] <= time.time()
        and proof["formal_readiness_verified"] is plan["formal_authority"],
        "SETUP_BINDING_CHANGED",
    )
    if plan["formal_authority"]:
        authority_raw, _ = authority_for_root(root)
        need(authority_raw is not None, "FORMAL_AUTHORITY_NOT_GRANTED")
        authority = load("p17_m2_input_export").parse(authority_raw)
        readiness = proof["readiness"]
        need(
            readiness["actors"] == authority["actors"]
            and all(
                readiness[k] == authority[k]
                for k in ("preparation_closure_sha256", "independent_preflight_sha256")
            )
            and isinstance(readiness["main_CI_run"], int)
            and readiness["main_CI_run"] > 0
            and isinstance(readiness["main"], str)
            and re.fullmatch(r"[0-9a-f]{40}", readiness["main"])
            and proof["filesystem"]["local_filesystem"] is True,
            "FROZEN_ACTIVATION_READINESS_REQUIRED",
        )
    return proof


def new_source_parameters(authority):
    """The NEW owner grant is a single literal route, never an old-quota extension."""
    parent = "/Users/keith1117/Library/Application Support/TopoLab-custody"
    expected_budget = {
        "clock_start_utc": "2026-10-28T06:39:14Z",
        "clock_start_unix_ms": 1793169554000,
        "outer_wall_seconds": 129600,
        "total_author_seconds_cap": 201600,
        "executor_author_seconds_cap": 82800,
        "independent_author_seconds_cap": 82800,
        "all_review_and_new_adapter_author_seconds_cap": 36000,
        "conditional_executor_seconds_cap": 39600,
        "conditional_independent_seconds_cap": 39600,
        "source_attempts": 1,
        "source_CLI_max": 26,
        "source_FULL_max": 3780,
        "source_common_each": 4500,
        "source_result_each_author_each_attempt": 9000,
        "source_each_author_once_per_original_per_attempt": 1,
        "source_max_reads_each_attempt": 1196,
        "source_metadata_payload_output_members": [40, 558, 1071],
        "resource_RSS_bytes": 4294967296,
        "old_allocations": "CLOSED_NO_TRANSFER",
        "external_paid_commitments": 0,
    }
    budget = authority.get("budget", {})
    need(
        authority.get("schema") == NEW_SCHEMA
        and authority.get("execution_identity") == NEW_IDENTITY
        and type(authority.get("total_new_author_charged_seconds_cap")) is int
        and authority["total_new_author_charged_seconds_cap"] == 201600
        and type(authority.get("outer_wall_seconds")) is int
        and authority["outer_wall_seconds"] == 129600
        and authority.get("source_identity_policy") == SOURCE_IDENTITY_POLICY
        and authority.get("actors") == {
            "executor": "/root", "independent": "/root/ci_recovery_independent",
        }
        and authority.get("fixed_target") == {
            "parent": parent,
            "attempts": {"1": {
                "generation": NEW_GENERATION,
                "backup": NEW_GENERATION + "-independent-backup",
            }},
        }
        and isinstance(budget, dict)
        and base().canonical({key: budget.get(key) for key in expected_budget})
        == base().canonical(expected_budget),
        "NEW_SOURCE_AUTHORITY_PARAMETERS_DIFFER",
    )


def formal_plan(authority_raw, *, attempt=1):
    """Pure, software-only formal metadata. Constructing it grants no target access."""
    helper = base()
    authority = load("p17_m2_input_export").parse(authority_raw)
    proposal_raw = (REPO / PROPOSAL).read_bytes()
    proposal = json.loads(proposal_raw)
    new = authority.get("schema") == NEW_SCHEMA
    if new:
        new_source_parameters(authority)
    remedy = authority.get("schema") == REMEDY_SCHEMA
    funded = new or remedy or authority.get("schema") == (
        "topolab.v2.m2-funded-acquisition-authority.v1"
    )
    need(
        (funded or authority["schema"] == "topolab.v2.m2-source-acquisition-execution-authority.v1")
        and authority["execution_identity"] == (
            NEW_IDENTITY if new else FUNDED_IDENTITY if funded else IDENTITY
        )
        and authority["proposal_sha256"] == helper.sha(proposal_raw)
        and isinstance(authority["owner_approval_reference"], str)
        and bool(authority["owner_approval_reference"].strip())
        and helper.canonical(authority["permissions"])
        == helper.canonical(
            {
                "formal_activation": True,
                "old_original_access": True,
                "target_access": True,
                "B_C": False,
            }
        )
        and authority["formal_seconds"] == 4500
        and authority["result_seconds"] == {
            "exporter": 9000 if new else 7200, "independent": 9000 if new else 7200,
        },
        "FORMAL_EXECUTION_AUTHORITY_INVALID",
    )
    need(
        type(attempt) is int and attempt in (
            (1,) if new else (2,) if remedy else (1, 2) if funded else (1,)
        ),
        "UNREGISTERED_FORMAL_ATTEMPT",
    )
    target = (
        authority["fixed_target"]["attempts"][str(attempt)]
        if funded
        else proposal["target_proposal_only"]
    )
    root = Path(target["generation"])
    contract = json.loads(
        (REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json").read_bytes()
    )
    known = load("p17_m2_input_export_independent")
    identity = {"B3_DATA_HASH": known.B3_DATA_HASH, "CATALOG_HASH": known.CATALOG_HASH}
    plan = make_plan(root, contract, identity)
    del plan["public_source_identity"]
    execution_sha = helper.sha(authority_raw)
    plan.update(
        scope=FORMAL_SCOPE,
        formal_authority=True,
        source_root=proposal["source_whitelist"]["original_root_literal"],
        backup_root=target["backup"],
        source_identity=identity,
        contract_sha256=execution_sha,
    )
    plan["binding"].update(
        formal_authority=True,
        old_original_access=True,
        target_access=True,
        execution_protocol_sha256=execution_sha,
    )
    protocol_path = (NEW_PROTOCOL if new else REMEDY_PROTOCOL if remedy else FUNDED_PROTOCOL
                     if funded else EXECUTION_PROTOCOL)
    plan["source_tree"][protocol_path] = execution_sha
    if funded:
        plan.update(
            execution_identity=NEW_IDENTITY if new else FUNDED_IDENTITY,
            source_identity_policy=SOURCE_IDENTITY_POLICY,
            preparation_contract_sha256=execution_sha,
        )
        plan["binding"].update(
            authority_protocol_path=protocol_path,
            formal_attempt=attempt,
            source_identity_policy=SOURCE_IDENTITY_POLICY,
            preparation_protocol_sha256=execution_sha,
        )
    return plan


def source_role_windows(authority, caller_start, native_start, observed, minimum_remaining=4200):
    """Check supplied actual clocks; this arithmetic grants no execution admission."""
    new = authority.get("execution_identity") == NEW_IDENTITY
    need(new or authority.get("execution_identity") == FUNDED_IDENTITY,
         "SOURCE_FUNDED_CLOCK_IDENTITY_REQUIRED")
    remedy = authority.get("schema") == REMEDY_SCHEMA
    if new:
        new_source_parameters(authority)
        need(type(minimum_remaining) is int and minimum_remaining == 4200,
             "NEW_SOURCE_SUFFIX_RESERVATION_REQUIRED")
    elif remedy:
        load("p17_m2_source_acquisition_independent").validate_remedy_authority(
            authority, formal=False
        )
    else:
        need(authority.get("schema") == "topolab.v2.m2-funded-acquisition-authority.v1",
             "SOURCE_FUNDED_CLOCK_AUTHORITY_REQUIRED")
    need(all(type(v) in (int, float) and math.isfinite(v)
             for v in (caller_start, native_start, observed, minimum_remaining))
         and 0 <= caller_start <= native_start <= observed and minimum_remaining > 0,
         "SOURCE_ACTUAL_CLOCKS_REQUIRED")
    caller_deadline = caller_start + (5400 if remedy else 4500)
    native_deadline = native_start + 4500
    need(caller_deadline - observed >= minimum_remaining, "SOURCE_CALLER_SUFFIX_UNAVAILABLE")
    need(native_deadline - observed >= minimum_remaining, "SOURCE_NATIVE_SUFFIX_UNAVAILABLE")
    return dict(caller_start=caller_start, native_start=native_start, observed=observed,
                caller_deadline=caller_deadline, native_deadline=native_deadline,
                caller_remaining=caller_deadline-observed,
                native_remaining=native_deadline-observed,
                minimum_remaining=minimum_remaining)


def new_source_readiness(authority):
    """Read only the NEW literal metadata proof paths before common main checks."""
    new_source_parameters(authority)
    closures = [
        "/private/tmp/topolab-ci-recovery-result-primary-v1-20261028/publication-closure-v1.json",
        "/private/tmp/topolab-ci-recovery-result-backup-v1-20261028/publication-closure-v1.json",
    ]
    preflight_path = (
        "/private/tmp/topolab-new-source-science-20261028/independent/preflight-source-v3.json"
    )
    need(authority.get("preparation_closure_paths") == closures
         and authority.get("independent_preflight_path") == preflight_path
         and all(isinstance(authority.get(key), str)
                 and re.fullmatch(r"[0-9a-f]{64}", authority[key])
                 and authority[key] != "0" * 64
                 for key in ("preparation_closure_sha256", "independent_preflight_sha256")),
         "NEW_LITERAL_READINESS_PROOFS_REQUIRED")
    need(0 <= time.time() - 1793169554 <= 129600 - 4500 - 9000,
         "NEW_COMPLETE_SOURCE_AND_RESULT_SUFFIX_UNAVAILABLE")
    frozen = {key: value for key, value in source_freeze(NEW_IDENTITY).items()
              if key != NEW_PROTOCOL}
    need(authority.get("published_source_sha256") == frozen,
         "PUBLISHED_IMPLEMENTATION_SOURCE_CHANGED")
    checker = load("p17_m2_source_acquisition_independent")
    protocol_raw = checker.native._software_bytes(REPO / NEW_PROTOCOL)
    need(base().canonical(json.loads(protocol_raw)) == base().canonical(authority),
         "NEW_AUTHORITY_BYTES_CHANGED")
    preflight_raw = checker.native._software_bytes(Path(preflight_path))
    need(base().sha(preflight_raw) == authority["independent_preflight_sha256"],
         "INDEPENDENT_PREFLIGHT_HASH_CHANGED")
    checker.check_funded_preflight(formal_plan(protocol_raw), preflight_raw)
    for path in closures:
        need(base().sha(checker.native._software_bytes(Path(path)))
             == authority["preparation_closure_sha256"], "PREPARATION_CLOSURE_CHANGED")


def activation_readiness(authority):
    """Before target IO: distinct appointments, immutable evidence refs and actual clean-main CI."""
    new = authority.get("execution_identity") == NEW_IDENTITY
    if new:
        need(authority.get("readiness_freeze_state") == "REVIEWED_FROZEN",
             "NEW_READINESS_NOT_FROZEN")
        new_source_readiness(authority)
    funded = new or authority.get("execution_identity") == FUNDED_IDENTITY
    remedy = authority.get("schema") == REMEDY_SCHEMA
    if funded and not new:
        need(
            authority.get("readiness_freeze_state") == "REVIEWED_FROZEN",
            "FUNDED_READINESS_NOT_FROZEN",
        )
        need(
            authority.get("preparation_closure_paths")
            == [
                "/Users/keith1117/Documents/TopoLab-data/"
                "p17-m2-hash-bound-custody-20261026-results/publication-closure.json",
                "/private/tmp/topolab-hash-bound-custody-20261026-results-backup/"
                "publication-closure.json",
            ]
            and authority.get("preparation_closure_sha256")
            == "0636d0713cfa15840516b8aff20d904ec09be7577cfdfdafcb416c375a97e314",
            "EXACT_PREPARATION_CLOSURES_REQUIRED",
        )
        need(
            authority.get("independent_preflight_path")
            == "/private/tmp/topolab-funded-continuation-20261026/independent/"
            + ("preflight-source2-remedy.json" if remedy else "preflight-remedy3.json"),
            "EXACT_INDEPENDENT_PREFLIGHT_PATH_REQUIRED",
        )
        began = datetime.fromisoformat(
            authority["budget"]["clock_start_utc"].replace("Z", "+00:00")
        )
        need(
            0 <= time.time() - began.timestamp()
            <= authority["outer_wall_seconds"] - (5400 if remedy else 4500) - 7200,
            "FUNDED_COMPLETE_SOURCE_AND_RESULT_SUFFIX_UNAVAILABLE",
        )
        checker = load("p17_m2_source_acquisition_independent")
        if remedy:
            checker.validate_remedy_authority(authority, formal=True)
        protocol = REMEDY_PROTOCOL if remedy else FUNDED_PROTOCOL
        frozen = {k: v for k, v in source_freeze().items() if k != protocol}
        need(
            authority.get("published_source_sha256") == frozen,
            "PUBLISHED_IMPLEMENTATION_SOURCE_CHANGED",
        )
        preflight_raw = checker.native._software_bytes(
            Path(authority["independent_preflight_path"])
        )
        need(
            base().sha(preflight_raw) == authority["independent_preflight_sha256"],
            "INDEPENDENT_PREFLIGHT_HASH_CHANGED",
        )
        preflight = checker.native.base.parse(preflight_raw)
        actual_runtime = base().runtime()
        need(
            preflight.get("status") == "PASS_PUBLIC_METADATA_LAUNCH_PREFLIGHT"
            and preflight.get("execution_identity") == FUNDED_IDENTITY
            and preflight.get("actors") == authority["actors"]
            and preflight.get("published_source_sha256") == frozen
            and all(
                preflight.get("runtime", {}).get(k) == v
                for k, v in actual_runtime.items()
                if k != "orig_argv"
            ),
            "INDEPENDENT_ACTUAL_PREFLIGHT_REQUIRED",
        )
        if remedy:
            need(preflight.get("authority_protocol_path") == REMEDY_PROTOCOL
                 and type(preflight.get("remedy_formal_attempt")) is int
                 and preflight["remedy_formal_attempt"] == 2
                 and preflight.get("remedy_projection_sha256")
                 == checker.remedy_projection_sha256(authority),
                 "SOURCE2_REMEDY_PREFLIGHT_PROTOCOL_REQUIRED")
        paths = authority.get("preparation_closure_paths", [])
        need(len(paths) == 2 and len(set(paths)) == 2, "INDEPENDENT_PREPARATION_CLOSURES_REQUIRED")
        for path in paths:
            need(
                base().sha(checker.native._software_bytes(Path(path)))
                == authority["preparation_closure_sha256"],
                "PREPARATION_CLOSURE_CHANGED",
            )
    actors = authority.get("actors", {})
    implementation_key = "implementation_base_commit" if funded else "implementation_commit"
    need(
        set(actors) == {"executor", "independent"}
        and all(isinstance(v, str) and v.strip() for v in actors.values())
        and actors["executor"] != actors["independent"]
        and all(
            isinstance(authority.get(k), str) and re.fullmatch(r"[0-9a-f]{64}", authority[k])
            for k in ("preparation_closure_sha256", "independent_preflight_sha256")
        )
        and isinstance(authority.get(implementation_key), str)
        and re.fullmatch(r"[0-9a-f]{40}", authority[implementation_key]),
        "FROZEN_ACTIVATION_READINESS_REQUIRED",
    )

    def command(words):
        return subprocess.run(words, cwd=REPO, check=True, capture_output=True, timeout=30).stdout

    need(not command(["git", "status", "--porcelain=v1"]).strip(), "CLEAN_MAIN_REQUIRED")
    head = command(["git", "rev-parse", "HEAD"]).decode().strip()

    def github(endpoint):
        return json.loads(command(["gh", "api", "repos/keith1117/TopoLab/" + endpoint]))

    need(github("commits/main")["sha"] == head, "EXACT_MERGED_MAIN_REQUIRED")
    for name, expected in source_freeze(authority["execution_identity"]).items():
        if not funded and name != EXECUTION_PROTOCOL:
            need(
                base().sha(
                    command(["git", "show", authority["implementation_commit"] + ":" + name])
                )
                == expected,
                "PUBLISHED_IMPLEMENTATION_SOURCE_CHANGED",
            )
    protection = github("branches/main/protection")
    required = protection["required_status_checks"]
    need(
        required["strict"] is True
        and protection["enforce_admins"]["enabled"] is True
        and protection["allow_force_pushes"]["enabled"] is False
        and protection["allow_deletions"]["enabled"] is False
        and protection["required_conversation_resolution"]["enabled"] is True
        and {"quality", "frontend", "clean-linux-smoke"} <= set(required["contexts"]),
        "PROTECTED_MAIN_RULES_REQUIRED",
    )
    runs = github("actions/runs?head_sha=" + head + "&per_page=100")["workflow_runs"]
    passed = None
    for run in runs:
        if (
            run["head_sha"] == head
            and run["head_branch"] == "main"
            and run["status"] == "completed"
            and run["conclusion"] == "success"
        ):
            jobs = github("actions/runs/" + str(run["id"]) + "/jobs?per_page=100")["jobs"]
            if {"quality", "frontend", "clean-linux-smoke", "i1-native-software"} <= {
                j["name"]
                for j in jobs
                if j["status"] == "completed" and j["conclusion"] == "success"
            }:
                passed = run["id"]
                break
    need(passed is not None, "ALL_FOUR_EXACT_MAIN_CI_REQUIRED")
    return dict(
        main=head,
        main_CI_run=passed,
        actors=actors,
        preparation_closure_sha256=authority["preparation_closure_sha256"],
        independent_preflight_sha256=authority["independent_preflight_sha256"],
    )


def activate_formal(root):
    # Earlier preparation-only grants closed without a funded complete suffix.
    if Path(root).name in (
        "p17-m2-local-input-version-v3-hash-bound-20261026",
        "p17-m2-local-input-version-v4-hash-bound-20261026",
    ):
        raise ValueError("FORMAL_CLOSED_RESULT_RESERVE_UNFUNDED")
    # An approved preparation/public PASS is never a scientific access grant.
    authority_raw, attempt = authority_for_root(root)
    need(authority_raw is not None, "FORMAL_AUTHORITY_NOT_GRANTED")
    authority = load("p17_m2_input_export").parse(authority_raw)
    need(
        not (authority.get("execution_identity") == FUNDED_IDENTITY and attempt == 2)
        or authority.get("schema") == REMEDY_SCHEMA,
        "NEW_FROZEN_REMEDY_REQUIRED",
    )
    readiness = None
    if authority.get("schema") == REMEDY_SCHEMA:
        need(authority.get("readiness_freeze_state") == "REVIEWED_FROZEN",
             "FUNDED_READINESS_NOT_FROZEN")
    if authority.get("execution_identity") != FUNDED_IDENTITY:
        # Preserve the legacy readiness refusal before constructing a plan.
        readiness = activation_readiness(authority)
    plan = formal_plan(authority_raw, attempt=attempt)
    need(str(root) == plan["root"], "FORMAL_LITERAL_ROOT_REQUIRED")
    load("p17_m2_source_acquisition_independent").validate_binding(plan)
    if readiness is None:
        readiness = activation_readiness(authority)
    # The metadata draft has performed no formal IO. T0 follows completed gates.
    plan = formal_plan(authority_raw, attempt=attempt)
    load("p17_m2_source_acquisition_independent").validate_binding(plan)
    return setup_formal(plan, readiness)


def checked(root, expected):
    helper = base()
    literal = Path(os.path.abspath(root))
    if literal.name.startswith(
        (
            "topolab-public-formal-binding-",
            "topolab-public-hash-bound-",
            "topolab-public-funded-acquisition-",
            NEW_PUBLIC_PREFIX,
        )
    ):
        root = rehearsal_root(literal)
        scope = REHEARSAL_SCOPE
    else:
        authority_raw, attempt = authority_for_root(literal)
        need(authority_raw is not None, "FORMAL_AUTHORITY_NOT_GRANTED")
        declared = formal_plan(authority_raw, attempt=attempt)
        load("p17_m2_source_acquisition_independent").validate_binding(declared)
        need(str(literal) == declared["root"], "FORMAL_LITERAL_ROOT_REQUIRED")
        root, scope = literal, FORMAL_SCOPE
    plan = helper.read_json(root / "plan.json")
    need(helper.sha(helper.canonical(plan)) == expected, "PLAN_SHA_CHANGED")
    need(
        plan["root"] == str(root)
        and plan["scope"] == scope
        and plan["execution_identity"]
        == (
            declared["execution_identity"]
            if scope == FORMAL_SCOPE
            else NEW_IDENTITY
            if literal.name.startswith(NEW_PUBLIC_PREFIX)
            else FUNDED_IDENTITY
            if literal.name.startswith("topolab-public-funded-acquisition-")
            else COMPAT_IDENTITY
            if literal.name.startswith("topolab-public-hash-bound-")
            else IDENTITY
        )
        and plan["formal_authority"] is (scope == FORMAL_SCOPE),
        "ACQUISITION_BINDING_CHANGED",
    )
    need(plan["source_tree"] == source_freeze(plan["execution_identity"]), "SOURCE_FREEZE_CHANGED")
    actual = helper.runtime()
    need(
        all(plan["runtime"][k] == v for k, v in actual.items() if k != "orig_argv"),
        "RUNTIME_BINDING_CHANGED",
    )
    load("p17_m2_source_acquisition_independent").validate_binding(plan)
    checked_setup(root, plan)
    AcquisitionTransport(root, expected, scope=scope).namespace_check(root)
    return root, plan


@dataclass(frozen=True)
class AcquisitionTransport:
    root: Path
    plan_sha: str
    reader_role: str = "scientific-producer"
    scope: str = REHEARSAL_SCOPE

    @property
    def identity(self):
        if self.root.name.startswith(NEW_PUBLIC_PREFIX) or (
            self.scope == FORMAL_SCOPE and str(self.root) == NEW_GENERATION
        ):
            return NEW_IDENTITY
        if self.root.name.startswith("topolab-public-funded-acquisition-"):
            return FUNDED_IDENTITY
        if (
            self.scope == FORMAL_SCOPE
            and is_funded_authority(authority_for_root(self.root)[0])
        ):
            return FUNDED_IDENTITY
        return (
            COMPAT_IDENTITY if self.root.name.startswith("topolab-public-hash-bound-") else IDENTITY
        )

    @property
    def result_windows(self):
        if self.identity == NEW_IDENTITY:
            return (("exporter", 9000), ("independent", 9000))
        return (("exporter", 7200), ("independent", 7200))

    @property
    def source_identity_policy(self):
        return (
            SOURCE_IDENTITY_POLICY
            if self.identity in (COMPAT_IDENTITY, FUNDED_IDENTITY, NEW_IDENTITY) else None
        )

    def argv_for(self, root, mode, plan_sha, role):
        return argv_for(root, mode, plan_sha, role, reader_role=self.reader_role)

    def put(self, path, value):
        self.namespace_check(
            self.root, additional_bytes=len(base().canonical(value)), additional_files=1
        )
        return base().put(path, value)

    def sampler_put(self, path, helper):
        """Compact only completed NEW native sampler outputs, retaining every byte."""
        match = re.fullmatch(r"sampler-(\d+)\.json", path.name)
        if match is None:
            if path.name == "command.json":
                helper["sampler_evidence_storage"] = "topolab.source-sampler-evidence.v1"
                try:
                    raw = self.independent().native._software_bytes(
                        path.parent / "sampler-evidence.jsonl"
                    )
                    helper["sampler_journal_sha256"] = base().sha(raw)
                except Exception as error:
                    # A missing or unsafe journal cannot admit resources. Keep
                    # the actual primary command result and every failure field.
                    helper["sampler_journal_sha256"] = None
                    helper["sampler_journal_binding_failure"] = {
                        "type": type(error).__name__, "reason": str(error),
                    }
                    if helper.get("software_result") == "PUBLIC_COMMAND_EXIT_OBSERVED":
                        helper["software_result"] = "RESOURCE_UNKNOWN_STOP"
            return self.put(path, helper)
        index = int(match[1])
        profile = path.parent / f"sampler-{index}.time"
        parent = base().nofollow_directory(path.parent)
        descriptor = journal_fd = -1
        try:
            descriptor = os.open(
                profile.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
            )
            before = os.fstat(descriptor)
            need(
                stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and 0 < before.st_size <= 4 * 1024**2,
                "SAMPLER_PROFILE_REGULAR_BOUNDED_REQUIRED",
            )
            chunks = bytearray()
            while len(chunks) <= before.st_size:
                chunk = os.read(descriptor, min(65536, before.st_size + 1 - len(chunks)))
                if not chunk:
                    break
                chunks.extend(chunk)
            raw = bytes(chunks)
            need(
                len(raw) == before.st_size
                and base().physical(before) == base().physical(os.fstat(descriptor))
                == base().physical(os.stat(profile.name, dir_fd=parent, follow_symlinks=False)),
                "SAMPLER_PROFILE_IDENTITY_OR_LENGTH_CHANGED",
            )
            need(
                helper.get("profile") == profile.name
                and helper.get("role") == f"rss-sampler-{index}"
                and helper.get("profile_sha256") == base().sha(raw),
                "SAMPLER_PROFILE_HASH_OR_IDENTITY_CHANGED",
            )
            row = {
                "schema": "topolab.source-sampler-evidence.v1", "index": index,
                "helper": helper, "profile_base64": base64.b64encode(raw).decode("ascii"),
                "profile_identity": base().physical(before),
            }
            encoded = base().canonical(row)
            self.namespace_check(self.root, additional_bytes=len(encoded), additional_files=1)
            journal_fd = os.open(
                "sampler-evidence.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT
                | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=parent,
            )
            journal_before = os.fstat(journal_fd)
            need(
                stat.S_ISREG(journal_before.st_mode) and journal_before.st_nlink == 1
                and stat.S_IMODE(journal_before.st_mode) == 0o600,
                "SAMPLER_JOURNAL_PRIVATE_REGULAR_REQUIRED",
            )
            need(os.write(journal_fd, encoded) == len(encoded), "SAMPLER_JOURNAL_SHORT_APPEND")
            os.fsync(journal_fd)
            journal_after = os.fstat(journal_fd)
            need(
                journal_after.st_size == journal_before.st_size + len(encoded)
                and (journal_after.st_dev, journal_after.st_ino)
                == (journal_before.st_dev, journal_before.st_ino)
                and base().physical(journal_after)
                == base().physical(os.stat(
                    "sampler-evidence.jsonl", dir_fd=parent, follow_symlinks=False)),
                "SAMPLER_JOURNAL_CLOSING_OBSERVATION_CHANGED",
            )
            os.fsync(parent)
            need(
                base().physical(before)
                == base().physical(os.stat(profile.name, dir_fd=parent, follow_symlinks=False)),
                "SAMPLER_PROFILE_CLOSING_OBSERVATION_CHANGED",
            )
            # The exact native profile is durably retained above before this owned
            # transient is removed. A failure leaves it and the completed prefix.
            os.unlink(profile.name, dir_fd=parent)
            os.fsync(parent)
            return base().physical(journal_after)
        except BaseException as error:
            try:
                self.put(path, dict(helper, sampler_journal_failure={
                    "type": type(error).__name__, "reason": str(error),
                }))
            except BaseException as secondary:
                error.add_note("sampler fallback retention failed: " + repr(secondary))
            raise
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if journal_fd >= 0:
                os.close(journal_fd)
            os.close(parent)

    def helper_profiles_reader(self, folder, record):
        return self.independent().sampler_profiles(folder, record)

    def native_module(self, root=None):
        native = base().native_module()
        if root is not None:
            snapshot = native._snapshot

            def bounded(*args, **kwargs):
                self.namespace_check(root, additional_bytes=4 * 1024**2, additional_files=16)
                return snapshot(*args, **kwargs)

            native._snapshot = bounded
            native.atomic_new = self.sampler_put
        return native

    def namespace_check(
        self, root, *, additional_bytes=0, additional_files=0, additional_evidence=True
    ):
        if self.scope == REHEARSAL_SCOPE:
            return base().namespace_check(
                root, additional_bytes=additional_bytes, additional_files=additional_files
            )
        authority_raw, attempt = authority_for_root(root)
        need(authority_raw is not None, "FORMAL_AUTHORITY_NOT_GRANTED")
        if is_funded_authority(authority_raw):
            declared = formal_plan(authority_raw, attempt=attempt)
            generation, backup_name = declared["root"], declared["backup_root"]
        else:
            proposal = json.loads((REPO / PROPOSAL).read_bytes())["target_proposal_only"]
            generation, backup_name = proposal["generation"], proposal["backup"]
        need(str(root) == generation, "FORMAL_LITERAL_ROOT_REQUIRED")
        backup = Path(backup_name)
        main = base().namespace_check(root)
        directory = base().nofollow_directory(backup.parent)
        try:
            try:
                entry = os.stat(backup.name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                entry = None
            need(entry is None or stat.S_ISDIR(entry.st_mode), "BACKUP_DIRECTORY_NOFOLLOW_REQUIRED")
        finally:
            os.close(directory)
        copied = (
            base().namespace_check(backup, evidence=False)
            if entry is not None
            else dict(count=0, size=0)
        )
        need(main["count"] + copied["count"] + additional_files <= 4096, "NAMESPACE_FILE_CAP")
        need(main["size"] + copied["size"] + additional_bytes <= 2 * 1024**3, "NAMESPACE_BYTE_CAP")
        if additional_evidence:
            need(main["evidence_count"] + additional_files <= 512, "EVIDENCE_FILE_CAP")
            need(main["evidence_size"] + additional_bytes <= 256 * 1024**2, "EVIDENCE_BYTE_CAP")
        return main

    def new_content(self, path, registry, contract_sha):
        transport = self

        class BoundedContent(load("p17_m2_local_input_version").LocalContent):
            def write(self, relative, raw):
                transport.namespace_check(
                    transport.root,
                    additional_bytes=len(raw),
                    additional_files=1,
                    additional_evidence=False,
                )
                return super().write(relative, raw)

        return BoundedContent(path, registry, contract_sha)

    def backup_prefix_root(self, plan):
        return (
            Path(plan["backup_root"]) if self.scope == FORMAL_SCOPE else self.root / "backup-prefix"
        )

    def read_registry(self, root, plan, role):
        """Bind the R1 buffer before any payload IO; keep legacy routing unchanged."""
        if self.identity != NEW_IDENTITY or role not in ("exporter-r1", "independent-r1"):
            return base().read_json(root / "registry.json")
        checker = self.independent()
        reader = None
        context = {"stage": "accepted R0 registry before R1", "role": role,
                   "metadata_root": str(root), "original_payload_reads": 0}
        try:
            producer = load("p17_m2_input_export")
            local = load("p17_m2_local_input_version")
            reader = producer.Reader(root, execution_identity=local.IDENTITY,
                                     source_identity_checks=True)
            accepted_raw = reader.read("independent-r0-accepted.json", 16 * 1024**2,
                                       group="accepted_metadata", total=32 * 1024**2)
            accepted = checker.native.base.parse(accepted_raw, canonical_required=True)
            wire_raw = reader.read("receipts/independent-r0-wire.json", 16 * 1024**2,
                                   group="accepted_metadata", total=32 * 1024**2)
            wire = dict(checker.native.base.parse(wire_raw, canonical_required=True),
                        **self.resource_evidence(root, self.plan_sha, "independent-r0"))
            proof = self.audit_saved(root, "independent-r0", accepted["raw_tool_events"], wire=wire)
            need(proof.get("full_role_evidence_accepted") is True,
                 "R0_REGISTRY_NATIVE_ACCEPTANCE_REQUIRED")
            r0 = checker.native._proof(
                wire, "SOURCE_ACQUISITION_R0_CHECKED",
                expected_identity=self.identity, expected_scope=self.scope,
            )
            context.update(accepted_record_sha256=base().sha(accepted_raw),
                           accepted_registry_sha256=r0["source_registry_sha256"])
            raw = reader.read("registry.json", 8 * 1024**2,
                              expected=r0["source_registry_sha256"],
                              group="accepted_registry", total=8 * 1024**2)
            return checker.accepted_r0_registry(raw, wire, plan=plan)
        except Exception as error:
            context.update(primary_error={"type": type(error).__name__, "reason": str(error)},
                           metadata_reader=(None if reader is None else {
                               "attempts": reader.attempts, "rows": reader.rows,
                               "source_identities": reader.source_observations,
                               "failures": reader.failures,
                           }))
            error.independent_read_failure = context
            raise

    def predecessor(self, root, plan, role):
        need(role in plan["roles"] or role in plan["metadata_actions"], "UNREGISTERED_ROLE")
        order = plan["role_order"] + list(base().METADATA_CAPS)
        if role == "shared-closeout":
            attempted = [
                r
                for r in plan["role_order"][:-1]
                if (root / "receipts" / (r + "-pending.json")).exists()
            ]
            need(
                not (root / "active.json").exists()
                or base().read_json(root / "active.json").get("role") == "shared-closeout",
                "SHARED_REQUIRES_CLOSED_PREFIX",
            )
            need(
                attempted and attempted == plan["role_order"][: len(attempted)],
                "SHARED_REQUIRES_REAL_PREFIX",
            )
            for prior in attempted:
                proof = self.closed_saved(
                    root, self.plan_sha, prior, base().read_json(root / (prior + "-events.json"))
                )
                need(
                    proof.get("closed_attempt_verified") is True,
                    "SHARED_PREFIX_CLEANUP_UNKNOWN: " + str(proof.get("reason")),
                )
            return
        index = order.index(role)
        if index:
            previous = order[index - 1]
            need(
                (root / (previous + "-accepted.json")).is_file(),
                "PREDECESSOR_EXTERNAL_ACCEPTANCE_MISSING",
            )
            prior = base().read_json(root / (previous + "-accepted.json"))
            try:
                proof = self.audit_saved(root, previous, prior["raw_tool_events"])
                need(
                    proof.get("full_role_evidence_accepted")
                    or proof.get("metadata_evidence_accepted"),
                    "PREDECESSOR_NOT_ACCEPTED",
                )
            except (KeyError, ValueError, OSError) as error:
                raise ValueError("PREDECESSOR_ACCEPTANCE_INVALID") from error

    def resource_evidence(self, root, plan_sha, role, **kwargs):
        return base().resource_evidence(root, plan_sha, role, adapter=self, **kwargs)

    def independent(self):
        return load("p17_m2_source_acquisition_independent")

    def custody_hold(self, root):
        return base().custody_hold(root)

    def payload_body(self, root, plan, role):
        return payload_body(root, plan, role, self)

    def backup_content(self, root, plan, context):
        return base().backup_content(root, plan, context, adapter=self)

    def backup_failed_prefix(self, root, plan, context):
        return base().backup_failed_prefix(root, plan, context, adapter=self)

    def wire(self, root, role):
        packet = base().read_json(root / "receipts" / (role + "-wire.json"))
        return dict(packet, **self.resource_evidence(root, self.plan_sha, role))

    def audit_saved(self, root, role, events, *, wire=None):
        if wire is None:
            packet = base().read_json(root / "receipts" / (role + "-wire.json"))
            resources = self.resource_evidence(root, self.plan_sha, role, tolerate_missing=True)
            failures = resources.pop("resource_read_failures")
        else:
            packet = wire
            resources = {key: wire[key] for key in ("inner_evidence", "native_profiles")}
            failures = []
        checker = self.independent().native
        if role in base().METADATA_CAPS and role != "final-filing":
            result = checker.audit_metadata(
                dict(packet, **resources),
                raw_tool_events=events,
                plan_sha256=self.plan_sha,
                expected_argv=self.argv_for(root, "payload", self.plan_sha, role),
                expected_role=role,
                expected_identity=self.identity,
                result_seconds=tuple(value for _, value in self.result_windows),
            )
        else:
            result = checker.audit_role(
                packet["pending"],
                packet["completion"],
                raw_tool_events=events,
                expected_role=role,
                expected_plan_sha256=self.plan_sha,
                expected_identity=self.identity,
                result_seconds=tuple(value for _, value in self.result_windows),
                **resources,
            )
        result.setdefault("secondary_failures", []).extend(failures)
        return result

    def closed_saved(self, root, plan_sha, role, events):
        return self.independent().native.check_closed_attempt(
            self.wire(root, role),
            raw_tool_events=events,
            expected_role=role,
            expected_plan_sha256=plan_sha,
            expected_argv=self.argv_for(root, "payload", plan_sha, role),
            expected_identity=self.identity,
            result_seconds=tuple(value for _, value in self.result_windows),
        )


def payload(root, plan, role, transport):
    return base().payload(root, plan, role, adapter=transport)


def role_results(root, plan, transport):
    return {
        role: transport.audit_saved(root, role, base().read_json(root / (role + "-events.json")))
        for role in plan["role_order"]
    }


def payload_body(root, plan, role, transport):
    helper = base()
    if role == "independent-public-check":
        result = load("p17_m2_input_export_independent").public_check(
            root / "independent-public-fixture"
        )
        return dict(
            result,
            execution_identity=plan["execution_identity"],
            scope=transport.scope,
            formal_authority=False,
            B_C_admission=False,
            setup_proof_sha256=helper.sha(helper.canonical(checked_setup(root, plan))),
        )
    if role == "shared-closeout":
        return helper.shared_payload(root, plan, adapter=transport)
    if role in ("public-consumer", "reader-ack"):
        facts = helper.evidence_json(
            helper.read_json(root / "accepted-acquisition-bundle.json"), decode=True
        )
        certificate = transport.independent().audit_certificate(
            facts["bundle"], trusted_tool_events=facts["events"]
        )
        if role == "reader-ack":
            wire = transport.wire(root, "public-consumer")
            receipt = json.loads(wire["inner_evidence"]["log"])
            return certificate.acknowledge_returned_reader(
                receipt,
                {
                    "wire": wire,
                    "raw_tool_events": helper.read_json(root / "public-consumer-events.json"),
                },
            )
        lease = certificate.acquire_reader(transport.reader_role)
        consumer = load("p17_m2_source_verified_input").VerifiedAcquisitionInput(
            certificate, transport.reader_role, reader_lease=lease
        )
        count = total = 0
        for name in consumer.binding["role_views"][transport.reader_role]:
            consumer.consume(name, consumer.helper.parse if name.endswith(".json") else len)
            count += 1
            total += consumer.members[name]["byte_size"]
        transport.put(
            root / "public-consumption.json",
            dict(
                scope=transport.scope,
                execution_identity=plan["execution_identity"],
                role=transport.reader_role,
                member_count=count,
                total_bytes=total,
                formal_authority=False,
                same_read_buffer=True,
            ),
        )
        return lease.pending_return()
    if role == "final-filing":
        closed = helper.read_json(root / "closed.json")
        packet = role_results(root, plan, transport)
        need(all(v["full_role_evidence_accepted"] for v in packet.values()), "SHARED_FRONTIER")
        proof = {
            "status": "SOURCE_ACQUISITION_FILING_SNAPSHOT_WRITTEN",
            "scope": transport.scope,
            "execution_identity": plan["execution_identity"],
            "plan_sha256": transport.plan_sha,
            "version_id": closed["version_id"],
            "manifest_sha256": helper.sha(helper.canonical(closed["manifest"])),
            "shared_packet_sha256": helper.sha(helper.canonical(packet)),
            "endpoint": "FINITE_SNAPSHOT_EXCLUDES_OWN_FUTURE_RETURN",
            "billing_charge": helper.read_json(root / "final-filing-dispatch-charge.json"),
        }
        helper.put(root / "filing-snapshot.json", proof)
        return proof
    if role == "lease-release":
        # Existing release only reads NEW lock/filing facts; no content/old source.
        return helper.payload_body(root, plan, role)
    return helper.content_step(root, plan, role, adapter=transport)


def bundle(root, plan, transport):
    helper = base()
    closed = helper.read_json(root / "closed.json")
    return {
        "schema": "topolab.v2.m2-source-acquisition-bundle.v1",
        "execution_identity": plan["execution_identity"],
        "scope": transport.scope,
        "plan": plan,
        "plan_sha256": transport.plan_sha,
        "contract_sha256": plan["contract_sha256"],
        "root": plan["content_root"],
        "registry": helper.read_json(root / "registry.json"),
        "manifest": closed["manifest"],
        "version_id": closed["version_id"],
        "local_identity_rows": closed["local_identity_rows"],
        "root_identity": closed["root_identity"],
        "role_views": closed["manifest"]["role_views"],
        "roles": {r: transport.wire(root, r) for r in plan["role_order"]},
        "shared_packet_sha256": helper.sha(helper.canonical(role_results(root, plan, transport))),
        "filing": transport.wire(root, "final-filing"),
        "lease_release_evidence": transport.wire(root, "lease-release"),
        "backup": helper.read_json(root / "backup-proof.json"),
        "setup": checked_setup(root, plan),
        "initial_lease": helper.read_json(root / "custody-acquired.json"),
        "initial_lease_identity": helper.read_json(root / "custody-lock-identity.json"),
        "lease": helper.read_json(root / "lease-release.json"),
    }


def verify_retained_evidence(root, manifest_raw, expected_manifest_sha256):
    """Verify this finite evidence set against an anchor held outside its custody directory.

    Directory modes are observations, never a promise of permanent immutability.
    This does not acquire a lease or authorize any old-original access.
    """
    helper = base()
    need(
        len(manifest_raw) <= 2 * 1024**2
        and re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha256) is not None
        and helper.sha(manifest_raw) == expected_manifest_sha256,
        "CUSTODY_MANIFEST_SHA",
    )
    manifest = load("p17_m2_input_export").parse(manifest_raw)
    need(
        set(manifest) == {"members"}
        and isinstance(manifest["members"], list)
        and 0 < len(manifest["members"]) <= 4096,
        "CUSTODY_MANIFEST_MEMBERS",
    )
    rows = manifest["members"]
    need(
        all(set(row) == {"path", "byte_size", "sha256"} for row in rows), "CUSTODY_MANIFEST_FIELDS"
    )
    expected, directories = set(), set()
    for row in rows:
        name = row["path"]
        need(isinstance(name, str) and len(name) <= 1024, "CUSTODY_LITERAL_PATH")
        parts = Path(name)
        need(
            not parts.is_absolute()
            and name == parts.as_posix()
            and name not in ("", ".")
            and ".." not in parts.parts,
            "CUSTODY_LITERAL_PATH",
        )
        expected.add(name)
        directories.update(str(parent) for parent in parts.parents if str(parent) != ".")
    need(len(expected) == len(rows), "CUSTODY_DUPLICATE_MEMBER")
    root = Path(os.path.abspath(root))
    modes = {}

    def inventory():
        names = set()
        directory = helper.nofollow_directory(root)

        def visit(fd, prefix):
            info = os.fstat(fd)
            need(
                info.st_uid == os.geteuid() and not info.st_mode & 0o022,
                "CUSTODY_UNTRUSTED_DIRECTORY",
            )
            modes[prefix or "."] = stat.S_IMODE(info.st_mode)
            with os.scandir(fd) as entries:
                for entry_name in entries:
                    name = entry_name.name
                    relative = prefix + name
                    entry = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    if stat.S_ISDIR(entry.st_mode):
                        need(relative in directories, "CUSTODY_EXACT_WHITELIST_DIRECTORY")
                        child = os.open(
                            name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                        )
                        try:
                            visit(child, relative + "/")
                        finally:
                            os.close(child)
                    else:
                        need(
                            relative in expected and len(names) < len(rows),
                            "CUSTODY_EXACT_WHITELIST",
                        )
                        need(
                            stat.S_ISREG(entry.st_mode)
                            and entry.st_nlink == 1
                            and entry.st_uid == os.geteuid()
                            and not entry.st_mode & 0o022,
                            "CUSTODY_UNTRUSTED_MEMBER",
                        )
                        names.add(relative)

        try:
            before = os.fstat(directory)
            visit(directory, "")
            return names, (before.st_dev, before.st_ino)
        finally:
            os.close(directory)

    names, identity = inventory()
    need(names == expected, "CUSTODY_EXACT_WHITELIST")
    reader = load("p17_m2_input_export_independent").OnceReader(
        root,
        len(rows),
        2 * 1024**3,
        source_identity_checks=True,
        source_identity_policy=SOURCE_IDENTITY_POLICY,
    )
    for row in rows:
        need(
            type(row["byte_size"]) is int and 0 < row["byte_size"] <= 1024**3,
            "CUSTODY_MEMBER_BYTE_CAP",
        )
        reader.read(row["path"], row["byte_size"], sha256=row["sha256"], byte_size=row["byte_size"])
    need(inventory() == (expected, identity), "CUSTODY_INVENTORY_CHANGED")
    return {
        "manifest_sha256": expected_manifest_sha256,
        "members": reader.table,
        "observations": reader.observations,
        "directory_modes": modes,
        "continuous_immutability_claim": False,
    }


def main():
    modes = (
        "prepare-rehearsal",
        "activate-formal",
        "supervise",
        "record",
        "run",
        "payload",
        "bind",
        "certify-rehearsal",
        "certify-input-version",
    )
    if len(sys.argv) < 2 or sys.argv[1] not in modes:
        print("FORMAL_AUTHORITY_NOT_GRANTED", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=modes)
    parser.add_argument("--root", required=True)
    parser.add_argument("--plan-sha")
    parser.add_argument("--role")
    parser.add_argument("--reader-role", default="scientific-producer")
    parser.add_argument("--public-source-plan", type=Path)
    parser.add_argument("--public-source-plan-sha")
    args = parser.parse_args()
    need(
        args.mode == "prepare-rehearsal"
        or (args.public_source_plan is None and args.public_source_plan_sha is None),
        "PUBLIC_PREPARE_ARGUMENTS_ONLY",
    )
    need(Path.cwd() == REPO, "ACTUAL_WORKING_DIRECTORY_CHANGED")
    os.umask(0o077)
    if args.mode == "activate-formal":
        need(
            args.plan_sha is None and args.role is None and sys.flags.isolated == 1,
            "FORMAL_ISOLATED_SETUP_REQUIRED",
        )
        need(
            sys.orig_argv
            == [
                str(Path(sys.orig_argv[0]).resolve()),
                "-I",
                str(Path(__file__).resolve()),
                "activate-formal",
                "--root",
                args.root,
            ],
            "ACTUAL_ARGV_CHANGED",
        )
        result = activate_formal(args.root)
    elif args.mode == "prepare-rehearsal":
        need(args.plan_sha is None and args.role is None, "SETUP_ROLE_FORBIDDEN")
        result = prepare_rehearsal(
            args.root,
            public_source_plan=args.public_source_plan,
            public_source_plan_sha=args.public_source_plan_sha,
        )
    else:
        root, plan = checked(args.root, args.plan_sha)
        transport = AcquisitionTransport(root, args.plan_sha, args.reader_role, plan["scope"])
        need(
            sys.flags.isolated == 1 and base().runtime()["threads"] == base().THREADS,
            "ISOLATED_SINGLE_THREAD_RUNTIME_REQUIRED",
        )
        need(
            sys.orig_argv == transport.argv_for(root, args.mode, args.plan_sha, args.role),
            "ACTUAL_ARGV_CHANGED",
        )
        if args.mode == "supervise":
            result = base().supervise(root, plan, args.plan_sha, args.role, adapter=transport)
        elif args.mode == "record":
            result = base().collect(root, args.plan_sha, args.role, adapter=transport)
        elif args.mode == "bind":
            result = base().bind(root, plan, args.plan_sha, args.role, adapter=transport)
        elif args.mode in ("certify-rehearsal", "certify-input-version"):
            need(
                (args.mode == "certify-rehearsal" and transport.scope == REHEARSAL_SCOPE)
                or (args.mode == "certify-input-version" and transport.scope == FORMAL_SCOPE),
                "CERTIFICATE_SCOPE_CHANGED",
            )
            facts = bundle(root, plan, transport)
            events = {
                r: base().read_json(root / (r + "-events.json"))
                for r in [*plan["role_order"], "final-filing", "lease-release"]
            }
            transport.independent().audit_certificate(facts, trusted_tool_events=events)
            base().put(
                root / "accepted-acquisition-bundle.json",
                base().evidence_json({"bundle": facts, "events": events}),
            )
            result = {
                "scope": transport.scope,
                "formal_authority": plan["formal_authority"],
                "source_input_accepted": plan["formal_authority"],
                "formal_or_scientific_admission": False,
                "B_C_admission": False,
                "member_count": len(facts["manifest"]["members"]),
                "version_id": facts["version_id"],
            }
        elif args.mode == "run":
            result = transport.native_module(root).invoke(
                root / "receipts" / args.role,
                args.role,
                transport.argv_for(root, "payload", args.plan_sha, args.role),
                timeout=(
                    160
                    if args.role in ("final-filing", "lease-release")
                    else base().role_cap(args.role) - 10
                ),
            )
        else:
            result = payload(root, plan, args.role, transport)
    print(base().canonical(result).decode(), end="")
    return 1 if result.get("status") in ("STOP_NO_RETRY", "FAILED_INTERNAL_COMPLETION") else 0


if __name__ == "__main__":
    raise SystemExit(main())
