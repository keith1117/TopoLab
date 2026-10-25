"""Source-acquisition binding; actual formal authority remains separately closed."""

import argparse
import ctypes
import importlib.util
import json
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


def source_freeze():
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
    return {str(p.relative_to(REPO)): base().sha(p.read_bytes()) for p in sorted(paths)}


def rehearsal_root(root):
    root = Path(os.path.abspath(root))
    need(root.name.startswith("topolab-public-formal-binding-"), "REHEARSAL_ROOT_REQUIRED")
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
    protocol_sha = helper.sha((REPO / PROTOCOL).read_bytes())
    proposal_sha = helper.sha((REPO / PROPOSAL).read_bytes())
    return {
        "schema": "topolab.v2.m2-source-acquisition-plan.v1",
        "execution_identity": IDENTITY,
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
        },
        "source_tree": source_freeze(),
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
        "result_window_projection_seconds": {"exporter": 7200, "independent": 7200},
    }


def prepare_rehearsal(root):
    root = rehearsal_root(root)
    helper = base()
    parent = helper.nofollow_directory(root.parent)
    try:
        os.mkdir(root.name, mode=0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    contract, source_identity = load("p17_m2_content_verified_public_fixture").create_sources(
        root / "public-source", load("p17_m2_input_export_independent")
    )
    plan = make_plan(root, contract, source_identity)
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
        "execution_identity": IDENTITY,
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
    need(EXECUTION_AUTHORITY_RAW is not None, "FORMAL_AUTHORITY_NOT_GRANTED")
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
        execution_identity=IDENTITY,
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
        and proof["execution_identity"] == IDENTITY
        and proof["setup_start_UTC_seconds"] == plan["actor_activation_UTC_seconds"]
        and 0 <= proof["setup_seconds"] <= 300
        and proof["setup_start_UTC_seconds"] <= proof["setup_end_UTC_seconds"] <= time.time()
        and proof["formal_readiness_verified"] is plan["formal_authority"],
        "SETUP_BINDING_CHANGED",
    )
    if plan["formal_authority"]:
        need(EXECUTION_AUTHORITY_RAW is not None, "FORMAL_AUTHORITY_NOT_GRANTED")
        authority = load("p17_m2_input_export").parse(EXECUTION_AUTHORITY_RAW)
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


def formal_plan(authority_raw):
    """Pure, software-only formal metadata. Constructing it grants no target access."""
    helper = base()
    authority = load("p17_m2_input_export").parse(authority_raw)
    proposal_raw = (REPO / PROPOSAL).read_bytes()
    proposal = json.loads(proposal_raw)
    need(
        authority["schema"] == "topolab.v2.m2-source-acquisition-execution-authority.v1"
        and authority["execution_identity"] == IDENTITY
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
        and authority["result_seconds"] == {"exporter": 7200, "independent": 7200},
        "FORMAL_EXECUTION_AUTHORITY_INVALID",
    )
    root = Path(proposal["target_proposal_only"]["generation"])
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
        backup_root=proposal["target_proposal_only"]["backup"],
        source_identity=identity,
        contract_sha256=execution_sha,
    )
    plan["binding"].update(
        formal_authority=True,
        old_original_access=True,
        target_access=True,
        execution_protocol_sha256=execution_sha,
    )
    plan["source_tree"][EXECUTION_PROTOCOL] = execution_sha
    return plan


def activation_readiness(authority):
    """Before target IO: distinct appointments, immutable evidence refs and actual clean-main CI."""
    actors = authority.get("actors", {})
    need(
        set(actors) == {"executor", "independent"}
        and all(isinstance(v, str) and v.strip() for v in actors.values())
        and actors["executor"] != actors["independent"]
        and all(
            isinstance(authority.get(k), str) and re.fullmatch(r"[0-9a-f]{64}", authority[k])
            for k in ("preparation_closure_sha256", "independent_preflight_sha256")
        )
        and isinstance(authority.get("implementation_commit"), str)
        and re.fullmatch(r"[0-9a-f]{40}", authority["implementation_commit"]),
        "FROZEN_ACTIVATION_READINESS_REQUIRED",
    )

    def command(words):
        return subprocess.run(words, cwd=REPO, check=True, capture_output=True, timeout=30).stdout

    need(not command(["git", "status", "--porcelain=v1"]).strip(), "CLEAN_MAIN_REQUIRED")
    head = command(["git", "rev-parse", "HEAD"]).decode().strip()

    def github(endpoint):
        return json.loads(command(["gh", "api", "repos/keith1117/TopoLab/" + endpoint]))

    need(github("commits/main")["sha"] == head, "EXACT_MERGED_MAIN_REQUIRED")
    for name, expected in source_freeze().items():
        if name != EXECUTION_PROTOCOL:
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
    # An approved preparation/public PASS is never a scientific access grant.
    need(EXECUTION_AUTHORITY_RAW is not None, "FORMAL_AUTHORITY_NOT_GRANTED")
    authority = load("p17_m2_input_export").parse(EXECUTION_AUTHORITY_RAW)
    readiness = activation_readiness(authority)
    plan = formal_plan(EXECUTION_AUTHORITY_RAW)
    need(str(root) == plan["root"], "FORMAL_LITERAL_ROOT_REQUIRED")
    load("p17_m2_source_acquisition_independent").validate_binding(plan)
    return setup_formal(plan, readiness)


def checked(root, expected):
    helper = base()
    literal = Path(os.path.abspath(root))
    if literal.name.startswith("topolab-public-formal-binding-"):
        root = rehearsal_root(literal)
        scope = REHEARSAL_SCOPE
    else:
        need(EXECUTION_AUTHORITY_RAW is not None, "FORMAL_AUTHORITY_NOT_GRANTED")
        declared = formal_plan(EXECUTION_AUTHORITY_RAW)
        load("p17_m2_source_acquisition_independent").validate_binding(declared)
        need(str(literal) == declared["root"], "FORMAL_LITERAL_ROOT_REQUIRED")
        root, scope = literal, FORMAL_SCOPE
    plan = helper.read_json(root / "plan.json")
    need(helper.sha(helper.canonical(plan)) == expected, "PLAN_SHA_CHANGED")
    need(
        plan["root"] == str(root)
        and plan["scope"] == scope
        and plan["execution_identity"] == IDENTITY
        and plan["formal_authority"] is (scope == FORMAL_SCOPE),
        "ACQUISITION_BINDING_CHANGED",
    )
    need(plan["source_tree"] == source_freeze(), "SOURCE_FREEZE_CHANGED")
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

    identity = IDENTITY
    result_windows = (("exporter", 7200), ("independent", 7200))

    def argv_for(self, root, mode, plan_sha, role):
        return argv_for(root, mode, plan_sha, role, reader_role=self.reader_role)

    def put(self, path, value):
        self.namespace_check(
            self.root, additional_bytes=len(base().canonical(value)), additional_files=1
        )
        return base().put(path, value)

    def native_module(self, root=None):
        native = base().native_module()
        if root is not None:
            snapshot = native._snapshot

            def bounded(*args, **kwargs):
                self.namespace_check(root, additional_bytes=4 * 1024**2, additional_files=16)
                return snapshot(*args, **kwargs)

            native._snapshot = bounded
            native.atomic_new = self.put
        return native

    def namespace_check(
        self, root, *, additional_bytes=0, additional_files=0, additional_evidence=True
    ):
        if self.scope == REHEARSAL_SCOPE:
            return base().namespace_check(
                root, additional_bytes=additional_bytes, additional_files=additional_files
            )
        need(EXECUTION_AUTHORITY_RAW is not None, "FORMAL_AUTHORITY_NOT_GRANTED")
        proposal = json.loads((REPO / PROPOSAL).read_bytes())
        need(
            str(root) == proposal["target_proposal_only"]["generation"],
            "FORMAL_LITERAL_ROOT_REQUIRED",
        )
        backup = Path(proposal["target_proposal_only"]["backup"])
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

    def audit_saved(self, root, role, events):
        packet = base().read_json(root / "receipts" / (role + "-wire.json"))
        resources = self.resource_evidence(root, self.plan_sha, role, tolerate_missing=True)
        failures = resources.pop("resource_read_failures")
        checker = self.independent().native
        if role in base().METADATA_CAPS and role != "final-filing":
            result = checker.audit_metadata(
                dict(packet, **resources),
                raw_tool_events=events,
                plan_sha256=self.plan_sha,
                expected_argv=self.argv_for(root, "payload", self.plan_sha, role),
                expected_role=role,
                expected_identity=IDENTITY,
                result_seconds=(7200, 7200),
            )
        else:
            result = checker.audit_role(
                packet["pending"],
                packet["completion"],
                raw_tool_events=events,
                expected_role=role,
                expected_plan_sha256=self.plan_sha,
                expected_identity=IDENTITY,
                result_seconds=(7200, 7200),
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
            expected_identity=IDENTITY,
            result_seconds=(7200, 7200),
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
            execution_identity=IDENTITY,
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
                execution_identity=IDENTITY,
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
            "execution_identity": IDENTITY,
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
        "execution_identity": IDENTITY,
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
    args = parser.parse_args()
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
        result = prepare_rehearsal(args.root)
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
