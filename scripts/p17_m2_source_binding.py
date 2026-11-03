"""Fresh strict registration of the exact23 previously unbound metadata files.

Registration is a new observation, not proof of unpublished history. The source
read primitive keeps its original identity; no failed buffer establishes trust.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import shlex
import stat
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUTHORITY = REPO / "docs/planning/p17_m2_strict_source_binding_protocol.json"
IDENTITY = "topolab.v2.p17-source-binding-and-conditional-repair.20261103.v1"
PUBLIC_SCOPE = "PUBLIC_STRICT_BINDING_REGISTRATION_ONLY"
FORMAL_SCOPE = "FORMAL_STRICT_BINDING_REGISTRATION_ONLY"
READ_SCHEMA = "topolab.v2.m2-strict-source-binding.read.v1"
PLAN_SCHEMA = "topolab.v2.m2-strict-source-binding.plan.v1"
METADATA_SCHEMA = "topolab.v2.m2-strict-source-binding.metadata-plan.v1"
METADATA_SCOPE = "STRICT_BINDING_CERTIFICATE_METADATA_ONLY"
METADATA_ROLE = "binding-certificate-auditor"
ROLE_CAPS = {"producer-availability": 150, "independent-availability": 150,
             "binding-producer": 300, "binding-independent": 300, "binding-closeout": 180}
THREADS = {key: "1" for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                               "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")}


def need(ok, reason):
    if not ok:
        raise ValueError("STRICT_BINDING: " + reason)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name):
    path = REPO / "scripts" / (name + ".py")
    existing = sys.modules.get(name)
    if existing is not None and Path(existing.__file__).resolve() == path:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, "missing published helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def whitelist():
    draft = REPO / "docs/planning/p17_m2_source_acquisition_execution_authorization_draft.json"
    raw = draft.read_bytes()
    need(sha(raw) == "401c32618ef6fb964d0efc425dc2f792ce92baf7a7e483d8bdbafa1c08906786",
         "original whitelist contract changed")
    rows = [{"path": row["relative_path"], "max_bytes": row["max_bytes"]}
            for row in json.loads(raw)["source_whitelist"]["static_metadata_files"]
            if row["expected_sha256"] is None]
    need(len(rows) == 23 and sum(row["max_bytes"] for row in rows) == 2785280,
         "exact23 whitelist differs")
    return rows


def source_freeze():
    names = [
        "scripts/p17_m2_source_binding.py",
        "scripts/p17_m2_source_binding_independent.py",
        "scripts/p17_m2_source_binding_native.py",
        "scripts/p17_m2_input_export.py",
        "scripts/p17_m2_input_export_independent.py",
        "scripts/p17_m2_resource_control.py",
        "scripts/p17_m2_homotopy.py",
        "scripts/p17_m2_content_verified_control.py",
        "scripts/p17_m2_content_verified_independent.py",
        "scripts/p17_m2_content_verified_public_fixture.py",
        "docs/planning/p17_m2_strict_source_binding_protocol.json",
        "docs/planning/p17_m2_source_acquisition_execution_authorization_draft.json",
        "docs/planning/p17_m2_input_export_preparation_proposal.json",
        "uv.lock", "pyproject.toml",
    ]
    return {name: sha((REPO / name).read_bytes()) for name in names}


def put_new(path, value):
    raw = canonical(value)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        need(stream.write(raw) == len(raw), "metadata short write")
        stream.flush()
        os.fsync(stream.fileno())
    return sha(raw)


def runtime():
    return {
        "python": str(Path(sys.executable).absolute()),
        "python_sha256": sha(Path(sys.executable).resolve().read_bytes()),
        "isolated": sys.flags.isolated,
        "cwd": os.getcwd(), "platform": sys.platform, "os_release": platform.release(),
        "lock_sha256": sha((REPO / "uv.lock").read_bytes()),
        "threads": {key: os.environ.get(key) for key in THREADS},
    }


def role_argv(root, mode, expected_sha, role, python):
    script = "p17_m2_source_binding.py" if mode == "payload" else "p17_m2_source_binding_native.py"
    return [python, "-I", str(REPO / "scripts" / script), mode,
            "--plan", str(Path(root) / "plan.json"), "--plan-sha", expected_sha, "--role", role]


def literal_command(argv):
    return "exec " + shlex.join(["env", *(key + "=" + value for key, value in THREADS.items()),
                                 *argv])


def file_actual_event(plan, role, mode, packet_path, packet_sha):
    """Bind one real MCP request and every owned poll; preserve payload text verbatim.

    The trusted caller supplies original tool returns. This metadata function
    cannot establish a return from a PASS flag or issue source-read authority.
    """
    native = load("p17_m2_source_binding_native")
    need(mode in ("supervise", "record") and role in plan["roles"], "actual event role/mode")
    packet, _ = read_metadata(Path(packet_path), 16 * 1024**2, expected=packet_sha,
                              canonical_required=True)
    argv = native.argv_for(plan, mode, role)
    need(packet.get("schema") == "topolab.v2.m2-strict-source-binding.actual-call.v1"
         and packet.get("author") == plan["roles"][role]["author"]
         and packet.get("argv") == argv
         and packet.get("request", {}).get("cmd") == literal_command(argv)
         and packet["request"].get("workdir") == str(REPO),
         "original actual caller/request/argv differs")
    responses = packet.get("responses")
    need(isinstance(responses, list) and 1 <= len(responses) <= 17,
         "actual return/polls missing or frozen poll cap exceeded")
    session = None
    for index, item in enumerate(responses):
        need(type(item.get("requested_ms")) is int and type(item.get("returned_ms")) is int
             and item["requested_ms"] <= item["returned_ms"], "actual raw clock endpoints missing")
        result = item.get("result", {})
        if index == 0:
            need(item.get("tool") == "exec_command" and item.get("arguments") == packet["request"],
                 "initial original tool request differs")
        else:
            need(item.get("tool") == "write_stdin" and session is not None
                 and item.get("arguments", {}).get("session_id") == session
                 and item["arguments"].get("chars", "") == ""
                 and item["requested_ms"] >= responses[index - 1]["returned_ms"],
                 "unowned/nonempty/out-of-order actual poll")
        need(isinstance(result.get("output"), str), "actual output fragment missing")
        output_cap = item.get("arguments", {}).get("max_output_tokens", 10000)
        original_count = result.get("original_token_count")
        need(type(output_cap) is int and output_cap > 0
             and (original_count is None or (type(original_count) is int
                  and 0 <= original_count <= output_cap))
             and "Warning: truncated output" not in result["output"]
             and "tokens truncated" not in result["output"],
             "truncated actual output cannot establish an observed return")
        if index:
            need(0 < item["arguments"].get("yield_time_ms", 5000) <= 30000,
                 "actual poll exceeds frozen wait cap")
        if index < len(responses) - 1:
            need(result.get("exit_code") is None and type(result.get("session_id")) is int,
                 "intermediate session/exit differs")
            need(session is None or session == result["session_id"], "actual session changed")
            session = result["session_id"]
        else:
            need(type(result.get("exit_code")) is int and result.get("session_id") is None,
                 "terminal actual exit/return missing")
    first, last = responses[0]["requested_ms"], responses[-1]["returned_ms"]
    event = {"event_id": packet["event_id"], "author": packet["author"],
             "start_seconds": first / 1000, "end_seconds": last / 1000,
             "wall_seconds": (last - first) / 1000, "argv": argv,
             "clock_domain": "functions.exec.Date.now.UTC-seconds", "complete": True,
             "exit_code": responses[-1]["result"]["exit_code"], "raw_packet_sha256": packet_sha}
    root = Path(plan["root"])
    if mode == "supervise":
        pending, _ = read_metadata(root / "receipts" / (role + "-pending.json"),
                                   65536, canonical_required=True)
        event["observed_pending_sha256"] = sha(canonical(pending))
    else:
        previous, _ = read_metadata(root / (role + "-supervise-actual-event.json"),
                                    65536, canonical_required=True)
        pending, _ = read_metadata(root / "receipts" / (role + "-pending.json"),
                                   65536, canonical_required=True)
        pending_sha = sha(canonical(pending))
        need(previous["observed_pending_sha256"] == pending_sha,
             "observed pending changed before final actual return")
        wire, _ = read_metadata(root / "receipts" / (role + "-wire.json"),
                                65536, canonical_required=True)
        returned = "".join(item["result"]["output"] for item in responses).encode("utf-8")
        need(returned == canonical(wire),
             "actual record stdout differs from complete canonical pending/completion wire")
        event["observed_pending_sha256"] = pending_sha
        event["observed_completion_sha256"] = sha(canonical(wire["completion"]))
    path = root / (role + "-" + mode + "-actual-event.json")
    event_sha = put_new(path, event)
    pair_sha = None
    if mode == "record":
        pair_sha = put_new(root / (role + "-events.json"), [previous, event])
    return {"event_path": str(path), "event_sha256": event_sha, "events_sha256": pair_sha,
            "original_source_reads_this_command": 0}


def prepare_public(root):
    """Create one NEW public graph and a real exclusive cooperative reader lease."""
    root = Path(os.path.abspath(root))
    metadata_path_guard(root / "plan.json")
    need(root.name.startswith("topolab-public-strict-binding-"), "public root literal required")
    need(runtime()["isolated"] == 1 and runtime()["cwd"] == str(REPO)
         and runtime()["threads"] == THREADS, "isolated locked single-thread runtime required")
    directory = source_parent(root.parent, "unused")
    try:
        os.mkdir(root.name, mode=0o700, dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)
    source = root.with_name(root.name + "-source")
    fixture = load("p17_m2_content_verified_public_fixture")
    public_contract, public_identity = fixture.create_sources(
        source, load("p17_m2_input_export_independent"))
    public_contract_sha = put_new(root / "public-content-contract.json", public_contract)
    public_identity_sha = put_new(root / "public-source-identity.json", public_identity)
    return write_core_plan(root, source, PUBLIC_SCOPE, 1,
        {"scope": PUBLIC_SCOPE, "old_original_access": False,
         "public_content_contract_sha256": public_contract_sha,
         "public_source_identity_sha256": public_identity_sha}, time.time_ns())


def write_core_plan(root, source, scope, attempt, entry, started_ns):
    context = {
        "execution_identity": IDENTITY, "scope": scope, "attempt": attempt,
        "source_root": str(source), "authority_sha256": sha(AUTHORITY.read_bytes()),
        "source_tree": source_freeze(), "actors": json.loads(AUTHORITY.read_bytes())["actors"],
    }
    now = started_ns / 10**9
    deadline = datetime.fromtimestamp(now + 3600, UTC).isoformat().replace("+00:00", "Z")
    lease = {"schema": "topolab.v2.m2-strict-source-binding.lease.v1",
             "execution_identity": IDENTITY, "scope": "COOPERATIVE_REGISTERED_TOPOLAB_ONLY",
             "context_sha256": sha(canonical(context)), "state": "HELD",
             "registered_readers": list(ROLE_CAPS), "acquired_UTC_seconds": now}
    lease_path = root / "custody.cooperative-reader.lease"
    lease_sha = put_new(lease_path, lease)
    put_new(root / "custody-acquired.json", lease)
    plan = {
        "schema": PLAN_SCHEMA, "root": str(root), "context": context, "runtime": runtime(),
        "role_order": list(ROLE_CAPS),
        "roles": {role: {"author": context["actors"][
            "independent" if role.startswith("independent-") or role == "binding-independent"
            else "producer"], "FULL": full, "timeout": full - (20 if full == 180 else 10),
            "argv": role_argv(root, "payload", "@PLAN_SHA256@", role, runtime()["python"])}
            for role, full in ROLE_CAPS.items()},
        "actor_activation_UTC_seconds": now, "actor_window_seconds": 3600,
        "started_unix_ns": started_ns, "deadline_unix_ns": started_ns + 3600 * 10**9,
        "actor_deadlines_UTC": {key: deadline for key in ("exporter", "independent")},
        "lease": {"path": str(lease_path), "sha256": lease_sha,
                  "identity": physical(lease_path.stat())},
        "entry": entry,
    }
    return {"plan_sha256": put_new(root / "plan.json", plan), "root": str(root),
            "scope": scope, "old_original_reads": 0, "formal_admission": scope == FORMAL_SCOPE}


def publication_readiness():
    """Observe current remote main and its protected exact-head CI, never origin/main."""
    def command(argv):
        return subprocess.run(argv, cwd=REPO, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
                              check=True, capture_output=True, timeout=30).stdout

    need(not command(["git", "--no-optional-locks", "status", "--porcelain=v1", "-uall"]).strip(),
         "clean published main required")
    head = command(["git", "rev-parse", "HEAD"]).decode().strip()

    def github(endpoint):
        return json.loads(command(["gh", "api", "repos/keith1117/TopoLab/" + endpoint]))

    main = github("commits/main")
    need(main["sha"] == head, "latest actual remote main differs")
    protection = github("branches/main/protection")
    checks = protection["required_status_checks"]
    need(checks["strict"] is True and protection["enforce_admins"]["enabled"] is True
         and protection["allow_force_pushes"]["enabled"] is False
         and protection["allow_deletions"]["enabled"] is False
         and protection["required_conversation_resolution"]["enabled"] is True
         and {"quality", "frontend", "clean-linux-smoke"} <= set(checks["contexts"]),
         "protected main rules required")
    runs = github("actions/runs?head_sha=" + head + "&per_page=100")["workflow_runs"]
    for run in runs:
        if (run["head_sha"] == head and run["head_branch"] == "main"
                and run["status"] == "completed" and run["conclusion"] == "success"):
            jobs = github("actions/runs/" + str(run["id"]) + "/jobs?per_page=100")["jobs"]
            passed = {job["name"] for job in jobs if job["status"] == "completed"
                      and job["conclusion"] == "success"}
            if {"quality", "frontend", "clean-linux-smoke", "i1-native-software"} <= passed:
                return {"main": head, "tree": main["commit"]["tree"]["sha"],
                        "main_CI_run": run["id"], "jobs": jobs,
                        "protection": protection, "source_tree": source_freeze()}
    raise ValueError("STRICT_BINDING: all four exact-main CI jobs required")


def verify_result_envelope(envelope):
    """The independent result auditor's own actual return is part of acceptance."""
    need(envelope.get("schema") == "topolab.v2.m2-strict-source-binding.accepted-result.v1",
         "accepted result envelope required")
    certificate = replay_bundle(envelope["core_bundle"])
    native = load("p17_m2_source_binding_native")
    plan = envelope["metadata_plan"]
    evidence = load("p17_m2_content_verified_control").evidence_json(
        envelope["metadata_evidence"], decode=True)
    proof = native.audit_role(plan, METADATA_ROLE, evidence, envelope["metadata_events"])
    need(proof.get("full_role_evidence_accepted") is True
         and plan["bundle"]["sha256"] == sha(canonical(envelope["core_bundle"]))
         and evidence["inner_evidence"]["log"] == canonical(certificate),
         "independent metadata auditor actual native/return or payload differs")
    return certificate, proof


def preparation_readiness(certificate_sha, preflight_sha, preflight_return_sha):
    authority = json.loads(AUTHORITY.read_bytes())
    paths = authority["preparation_proofs"]
    packets = []
    identities = []
    for path in paths["public_certificate_paths"]:
        packet, raw = read_metadata(Path(path), 64 * 1024**2, expected=certificate_sha,
                                    canonical_required=True)
        packets.append((packet, raw))
        info = Path(path).lstat()
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
             and stat.S_IMODE(info.st_mode) == 0o600, "private ordinary certificate pair required")
        identities.append((info.st_dev, info.st_ino))
    need(packets[0][1] == packets[1][1] and identities[0] != identities[1],
         "independent certificate bytes/inodes differ")
    certificate, audit = verify_result_envelope(packets[0][0])
    need(certificate["scope"] == PUBLIC_SCOPE
         and certificate["registered_source_tree"] == source_freeze()
         and certificate["registered_context"]["authority_sha256"] == sha(AUTHORITY.read_bytes()),
         "current complete public binding evidence required")
    preflight, _ = read_metadata(Path(paths["independent_preflight_path"]), 2 * 1024**2,
                                 expected=preflight_sha, canonical_required=True)
    actual, _ = read_metadata(Path(paths["independent_preflight_actual_return_path"]),
                              2 * 1024**2, expected=preflight_return_sha, canonical_required=True)
    need(preflight.get("schema") == "topolab.v2.m2-strict-source-binding.preflight.v1"
         and preflight.get("author") == authority["actors"]["independent"]
         and preflight.get("execution_identity") == IDENTITY
         and preflight.get("source_tree") == source_freeze()
         and preflight.get("authority_sha256") == sha(AUTHORITY.read_bytes())
         and preflight.get("public_certificate_sha256") == certificate_sha
         and preflight.get("metadata_auditor_T1") == audit["T1"]
         and preflight.get("runtime") == runtime()
         and actual.get("author") == preflight["author"]
         and actual.get("preflight_sha256") == preflight_sha
         and actual.get("actual_tool_result", {}).get("exit_code") == 0
         and actual.get("actual_tool_result", {}).get("session_id") is None,
         "distinct actual preflight and final return required")
    return preflight


def prepare_formal(attempt, certificate_sha, preflight_sha, preflight_return_sha, caller_start_ms):
    authority = json.loads(AUTHORITY.read_bytes())
    need(type(attempt) is int and attempt in (1, 2)
         and type(caller_start_ms) is int and caller_start_ms > 0,
         "new finite formal attempt/caller start required")
    need(attempt == 1, "second formal attempt requires a separately published remedy admission")
    preflight = preparation_readiness(certificate_sha, preflight_sha, preflight_return_sha)
    publication = publication_readiness()
    need(preflight.get("main") == publication["main"]
         and preflight.get("main_CI_run") == publication["main_CI_run"],
         "independent preflight must observe the actual current main CI")
    budget, _ = read_metadata(Path(authority["budget_path"]), 32768,
                              expected=authority["budget_raw_sha256"])
    allocation, _ = read_metadata(Path(authority["budget_allocation_v2_path"]), 32768,
                                  expected=authority["budget_allocation_v2_sha256"])
    execution_ref = authority["unstarted_execution_registration_v3"]
    execution, _ = read_metadata(Path(execution_ref["path"]), 32768,
                                 expected=execution_ref["sha256"])
    need(execution["official_formal_attempts_started"] == 0
         and execution["other_caps"]["formal_binding_attempts"] == 2
         and allocation["stages_each_root_I"]["binding_result"] == 12240
         and caller_start_ms * 10**6 <= time.time_ns()
         <= caller_start_ms * 10**6 + 120 * 10**9
         and caller_start_ms + (3600 + 12240) * 1000 <= budget["root_independent_deadline_ms"],
         "complete source/result suffix or original author budget unavailable")
    root = Path(authority["evidence_root"]) / f"binding-formal-v{attempt}"
    directory = source_parent(root.parent, "unused")
    try:
        os.mkdir(root.name, mode=0o700, dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)
    entry = {"schema": "topolab.v2.m2-strict-source-binding.formal-entry.v1",
             "scope": FORMAL_SCOPE, "old_original_access": True,
             "public_certificate_sha256": certificate_sha, "preflight_sha256": preflight_sha,
             "preflight_actual_return_sha256": preflight_return_sha,
             "publication": publication, "budget_raw_sha256": authority["budget_raw_sha256"]}
    return write_core_plan(root, Path(authority["registration_source_root"]), FORMAL_SCOPE,
                           attempt, entry, caller_start_ms * 10**6)


def read_metadata(path, maximum, *, expected=None, canonical_required=False):
    """Check and parse a single NEW metadata buffer, never scientific source bytes."""
    path = Path(path)
    metadata_path_guard(path)
    producer = load("p17_m2_input_export")
    reader = producer.Reader(path.parent, execution_identity=producer.LOCAL_IDENTITY,
                             source_identity_checks=True,
                             source_identity_policy=producer.PREBOUND_SHA256_POLICY
                             if expected is not None else None)
    raw = reader.read(path.name, maximum, expected=expected)
    value = producer.parse(raw)
    need(not canonical_required or canonical(value) == raw, "metadata canonical JSON differs")
    return value, raw


def metadata_path_guard(path):
    """NEW metadata helpers cannot become a route into old inputs or failed custody."""
    evidence = Path(json.loads(AUTHORITY.read_bytes())["evidence_root"])
    data = Path("/Users/keith1117/Documents/TopoLab-data")
    library = Path("/Users/keith1117/Library")
    need(path.is_absolute() and ".." not in path.parts
         and library not in path.parents
         and not (data in path.parents and evidence not in path.parents),
         "original or historical namespace is not NEW metadata")


def load_plan(path, expected_sha):
    """Read one exact pinned plan. Historical replay does not re-admit sources."""
    path = Path(path)
    need(path.is_absolute() and path.name == "plan.json" and ".." not in path.parts
         and isinstance(expected_sha, str) and re.fullmatch(r"[0-9a-f]{64}", expected_sha),
         "literal pinned plan required")
    formal_roots = {str(Path(json.loads(AUTHORITY.read_bytes())["evidence_root"])
                        / f"binding-formal-v{attempt}") for attempt in (1, 2)}
    need(path.parent.name.startswith("topolab-public-strict-binding-")
         or str(path.parent) in formal_roots
         or str(path.parent) in {root + "-certificate-audit" for root in formal_roots},
         "unregistered metadata plan root")
    old_root = Path("/Users/keith1117/Documents/TopoLab-data")
    need(not any(old_root.joinpath(part) in path.parents for part in (
        "b3-v1-fits", "b4-5-weighted-terminal", "b3-v1-data", "b4-30-z-reflection-repair-v2")),
        "old source namespace is not a plan")
    plan, _ = read_metadata(path, 2 * 1024**2, expected=expected_sha, canonical_required=True)
    need(isinstance(plan, dict) and plan.get("schema") in (PLAN_SCHEMA, METADATA_SCHEMA)
         and plan.get("root") == str(path.parent), "plan schema/root differs")
    return plan


def prepare_metadata_audit(bundle_path, expected_sha):
    bundle_path = Path(bundle_path)
    need(bundle_path.is_absolute() and bundle_path.name == "certificate-bundle.json",
         "literal new certificate bundle required")
    bundle, _ = read_metadata(bundle_path, 32 * 1024**2, expected=expected_sha,
                              canonical_required=True)
    replay_bundle(bundle)
    core = bundle["plan"]
    need(bundle_path == Path(core["root"]) / "certificate-bundle.json",
         "metadata bundle is outside its registered core root")
    root = Path(core["root"] + "-certificate-audit")
    directory = source_parent(root.parent, "unused")
    try:
        os.mkdir(root.name, mode=0o700, dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)
    started = time.time_ns()
    now = started / 10**9
    context = dict(core["context"], scope=METADATA_SCOPE, source_root=str(bundle_path.parent),
                   source_tree=source_freeze(), authority_sha256=sha(AUTHORITY.read_bytes()))
    deadline = datetime.fromtimestamp(now + 300, UTC).isoformat().replace("+00:00", "Z")
    plan = {"schema": METADATA_SCHEMA, "root": str(root), "context": context,
            "runtime": runtime(), "role_order": [METADATA_ROLE],
            "roles": {METADATA_ROLE: {"author": context["actors"]["independent"],
                "FULL": 120, "timeout": 110,
                "argv": role_argv(root, "payload", "@PLAN_SHA256@", METADATA_ROLE,
                                  runtime()["python"])}},
            "started_unix_ns": started, "deadline_unix_ns": started + 300 * 10**9,
            "actor_activation_UTC_seconds": now, "actor_window_seconds": 300,
            "actor_deadlines_UTC": {key: deadline for key in ("exporter", "independent")},
            "bundle": {"path": str(bundle_path), "sha256": expected_sha},
            "entry": {"scope": METADATA_SCOPE, "old_original_access": False,
                      "core_plan_sha256": sha(canonical(core))}}
    return {"plan_sha256": put_new(root / "plan.json", plan), "root": str(root),
            "scope": METADATA_SCOPE, "original_source_reads": 0}


def admit_metadata_plan(plan, role):
    need(plan.get("schema") == METADATA_SCHEMA and role == METADATA_ROLE
         and plan.get("role_order") == [METADATA_ROLE]
         and plan.get("runtime") == runtime() and runtime()["isolated"] == 1
         and runtime()["cwd"] == str(REPO) and runtime()["threads"] == THREADS,
         "metadata-only native plan/runtime differs")
    context = plan["context"]
    need(set(context) == {"execution_identity", "scope", "attempt", "source_root",
                          "authority_sha256", "source_tree", "actors"}
         and context["execution_identity"] == IDENTITY and context["scope"] == METADATA_SCOPE
         and context["actors"] == json.loads(AUTHORITY.read_bytes())["actors"]
         and context["source_tree"] == source_freeze()
         and context["authority_sha256"] == sha(AUTHORITY.read_bytes()),
         "metadata-only context/frozen code differs")
    expected_role = {"author": context["actors"]["independent"], "FULL": 120, "timeout": 110,
                     "argv": role_argv(plan["root"], "payload", "@PLAN_SHA256@", role,
                                       plan["runtime"]["python"])}
    need(plan["roles"] == {role: expected_role}
         and type(plan["started_unix_ns"]) is int and type(plan["deadline_unix_ns"]) is int
         and plan["deadline_unix_ns"] - plan["started_unix_ns"] == 300 * 10**9
         and plan["actor_activation_UTC_seconds"] == plan["started_unix_ns"] / 10**9
         and type(plan["actor_window_seconds"]) is int and plan["actor_window_seconds"] == 300
         and plan["started_unix_ns"] <= time.time_ns() <= plan["deadline_unix_ns"],
         "bounded metadata-only role/window differs")
    bundle_path = Path(plan["bundle"]["path"])
    need(bundle_path.name == "certificate-bundle.json"
         and str(bundle_path.parent) == context["source_root"]
         and plan["root"] == str(bundle_path.parent) + "-certificate-audit"
         and plan["entry"]["scope"] == METADATA_SCOPE
         and plan["entry"]["old_original_access"] is False,
         "metadata-only literal bundle/entry differs")
    bundle, _ = read_metadata(bundle_path, 32 * 1024**2, expected=plan["bundle"]["sha256"],
                              canonical_required=True)
    need(sha(canonical(bundle["plan"])) == plan["entry"]["core_plan_sha256"],
         "metadata-only core plan differs")
    replay_bundle(bundle)


def accepted_role(plan, role):
    """Replay the completed native role against its caller-supplied actual returns."""
    native = load("p17_m2_source_binding_native")
    events, _ = read_metadata(Path(plan["root"]) / (role + "-events.json"), 2 * 1024**2,
                              canonical_required=True)
    evidence = native.role_evidence(Path(plan["root"]), sha(canonical(plan)), role)
    result = native.audit_role(plan, role, evidence, events)
    need(result.get("full_role_evidence_accepted") is True,
         "predecessor actual native/returns not accepted: " + str(result.get("reason")))
    return result, evidence, events


def role_result(plan, role):
    result, evidence, _ = accepted_role(plan, role)
    raw = evidence["inner_evidence"]["log"]
    value = load("p17_m2_input_export").parse(raw)
    need(canonical(value) == raw, "native-bound payload JSON differs")
    return value, result


def admit_plan(plan, role):
    """Dispatch-only checks; a replayed historical certificate grants no new read."""
    need(plan.get("schema") == PLAN_SCHEMA and role in ROLE_CAPS
         and plan.get("role_order") == list(ROLE_CAPS), "registered plan/role/order required")
    context = plan["context"]
    check_context(Path(context["source_root"]), context)
    need(plan.get("runtime") == runtime() and runtime()["isolated"] == 1
         and runtime()["cwd"] == str(REPO) and runtime()["threads"] == THREADS,
         "frozen isolated runtime differs")
    need(type(plan.get("started_unix_ns")) is int
         and type(plan.get("deadline_unix_ns")) is int
         and plan["deadline_unix_ns"] - plan["started_unix_ns"] == 3600 * 10**9
         and plan.get("actor_activation_UTC_seconds") == plan["started_unix_ns"] / 10**9
         and type(plan.get("actor_window_seconds")) is int and plan["actor_window_seconds"] == 3600
         and plan["started_unix_ns"] <= time.time_ns() <= plan["deadline_unix_ns"],
         "bounded immutable dispatch window unavailable")
    for name, full in ROLE_CAPS.items():
        expected_author = context["actors"]["independent" if name.startswith("independent-")
                                            or name == "binding-independent" else "producer"]
        expected = {"author": expected_author, "FULL": full,
                    "timeout": full - (20 if full == 180 else 10),
                    "argv": role_argv(plan["root"], "payload", "@PLAN_SHA256@", name,
                                      plan["runtime"]["python"])}
        need(plan.get("roles", {}).get(name) == expected, "exact role/cap/argv differs")
    root = Path(plan["root"])
    if context["scope"] == PUBLIC_SCOPE:
        need(root.name.startswith("topolab-public-strict-binding-")
             and set(plan.get("entry", {})) == {
                 "scope", "old_original_access", "public_content_contract_sha256",
                 "public_source_identity_sha256"}
             and plan["entry"]["scope"] == PUBLIC_SCOPE
             and plan["entry"]["old_original_access"] is False,
             "public plan cannot grant original source access")
    else:
        entry = plan.get("entry", {})
        authority = json.loads(AUTHORITY.read_bytes())
        need(entry.get("schema") == "topolab.v2.m2-strict-source-binding.formal-entry.v1"
             and entry.get("scope") == FORMAL_SCOPE and entry.get("old_original_access") is True
             and root == Path(authority["evidence_root"]) / f"binding-formal-v{context['attempt']}"
             and entry.get("budget_raw_sha256") == authority["budget_raw_sha256"]
             and entry.get("publication", {}).get("source_tree") == source_freeze()
             and sys.platform == "darwin" and platform.machine() == "arm64",
             "formal publication/public-preflight entry missing")
        preflight = preparation_readiness(entry["public_certificate_sha256"],
            entry["preflight_sha256"], entry["preflight_actual_return_sha256"])
        need(preflight["main"] == entry["publication"]["main"]
             and preflight["main_CI_run"] == entry["publication"]["main_CI_run"],
             "frozen main/independent preflight differs")
    lease = plan["lease"]
    need(lease["path"] == str(root / "custody.cooperative-reader.lease"),
         "literal cooperative lease differs")
    value, _ = read_metadata(Path(lease["path"]), 16384, expected=lease["sha256"],
                              canonical_required=True)
    parent = source_parent(root, Path(lease["path"]).name)
    try:
        current = os.stat(Path(lease["path"]).name, dir_fd=parent, follow_symlinks=False)
    finally:
        os.close(parent)
    need(physical(current) == lease["identity"] and stat.S_ISREG(current.st_mode)
         and current.st_nlink == 1 and stat.S_IMODE(current.st_mode) == 0o600
         and value.get("state") == "HELD" and value.get("execution_identity") == IDENTITY
         and value.get("context_sha256") == sha(canonical(context)),
         "real cooperative lease no longer held")
    need(not (root / "STOP.json").exists() or role == "binding-closeout", "STOP_NO_RETRY")
    index = plan["role_order"].index(role)
    if role == "binding-closeout" and (root / "STOP.json").exists():
        native = load("p17_m2_source_binding_native")
        attempted = [name for name in plan["role_order"][:-1]
                     if (root / "receipts" / (name + "-pending.json")).exists()]
        need(attempted and attempted == plan["role_order"][:len(attempted)],
             "failure closeout requires an actual attempted prefix")
        for name in attempted:
            events, _ = read_metadata(root / (name + "-events.json"), 2 * 1024**2)
            evidence = native.role_evidence(root, sha(canonical(plan)), name)
            proof = native.audit_role(plan, name, evidence, events)
            need(proof.get("closed_attempt_verified") is True,
                 "failure closeout requires complete actual native cleanup and returns")
    elif index:
        accepted_role(plan, plan["role_order"][index - 1])


def release_lease(plan):
    """Release only this successful attempt after both actual source readers returned."""
    _, producer_return = role_result(plan, "binding-producer")
    _, independent_return = role_result(plan, "binding-independent")
    lease = plan["lease"]
    read_metadata(Path(lease["path"]), 16384, expected=lease["sha256"], canonical_required=True)
    root = Path(plan["root"])
    parent = source_parent(root, "custody.cooperative-reader.lease")
    try:
        current = os.stat("custody.cooperative-reader.lease", dir_fd=parent, follow_symlinks=False)
        need(physical(current) == lease["identity"], "release lease ownership changed")
        os.unlink("custody.cooperative-reader.lease", dir_fd=parent)
        released = time.time_ns()
        before = os.fstat(parent)
        try:
            observed = os.stat("custody.cooperative-reader.lease", dir_fd=parent,
                               follow_symlinks=False)
        except FileNotFoundError as error:
            need(error.errno == 2, "lease absence errno differs")
            observed = None
        after = os.fstat(parent)
        observed_ns = time.time_ns()
        need(observed is None, "released lease still exists")
        absence = {"errno": 2, "observed_unix_ns": observed_ns, "path": lease["path"],
                   "parent_before": {key: getattr(before, key) for key in ("st_dev", "st_ino")},
                   "parent_after": {key: getattr(after, key) for key in ("st_dev", "st_ino")}}
        need(absence["parent_before"] == absence["parent_after"], "lease parent replaced")
        os.fsync(parent)
    finally:
        os.close(parent)
    release = {"schema": "topolab.v2.m2-strict-source-binding.lease-release.v1",
               "path": lease["path"], "sha256": lease["sha256"], "identity": lease["identity"],
               "state": "RELEASED_AFTER_SOURCE_READER_RETURNS",
               "released_unix_ns": released, "absence_observation": absence}
    put_new(root / "lease-release.json", release)
    return release, {"binding-producer": producer_return["T1"],
                     "binding-independent": independent_return["T1"]}


def closeout(plan):
    root = Path(plan["root"])
    if (root / "STOP.json").exists():
        stop, _ = read_metadata(root / "STOP.json", 16 * 1024**2)
        return {"schema": "topolab.v2.m2-strict-source-binding.failure-closeout.v1",
                "status": "FAILURE_PREFIX_RETAINED_NO_BINDING", "context": plan["context"],
                "original_STOP": stop, "lease_state": "HELD", "bindings": None,
                "own_future_return": "NOT_CLAIMED_REQUIRES_SEPARATE_ACTUAL_OBSERVATION"}
    primary, _ = role_result(plan, "binding-producer")
    independent, _ = role_result(plan, "binding-independent")
    bindings = load("p17_m2_source_binding_independent").validate_pair(
        primary, independent, plan["context"])
    release, returns = release_lease(plan)
    return {"schema": "topolab.v2.m2-strict-source-binding.closeout.v1",
            "context": plan["context"], "producer_wire_sha256": sha(canonical(primary)),
            "independent_wire_sha256": sha(canonical(independent)), "bindings": bindings,
            "lease_release": release, "reader_returns": returns,
            "own_future_return": "NOT_CLAIMED_REQUIRES_SEPARATE_ACTUAL_OBSERVATION"}


def replay_bundle(bundle):
    """Audit captured metadata buffers; never follow an original source path."""
    need(bundle.get("schema") == "topolab.v2.m2-strict-source-binding.evidence-bundle.v1",
         "binding evidence bundle schema differs")
    base = load("p17_m2_content_verified_control")
    evidence = base.evidence_json(bundle["evidence_by_role"], decode=True)
    result = load("p17_m2_source_binding_native").audit_certificate(
        bundle["plan"], evidence, bundle["trusted_events_by_role"],
        bundle["primary"], bundle["independent"])
    need(canonical(result) == canonical(bundle["certificate"]),
         "binding certificate differs from complete native replay")
    return result


def certify_core(plan):
    native = load("p17_m2_source_binding_native")
    evidence, events = {}, {}
    for role in ROLE_CAPS:
        _, evidence[role], events[role] = accepted_role(plan, role)
    primary, _ = role_result(plan, "binding-producer")
    independent, _ = role_result(plan, "binding-independent")
    certificate = native.audit_certificate(plan, evidence, events, primary, independent)
    bundle = {"schema": "topolab.v2.m2-strict-source-binding.evidence-bundle.v1",
              "plan": plan,
              "evidence_by_role": load("p17_m2_content_verified_control").evidence_json(evidence),
              "trusted_events_by_role": events, "primary": primary, "independent": independent,
              "certificate": certificate}
    replay_bundle(bundle)
    path = Path(plan["root"]) / "certificate-bundle.json"
    return {"status": "CORE_BINDING_NATIVE_CLOSED_RESULT_AUDITOR_REQUIRED",
            "bundle_path": str(path), "bundle_sha256": put_new(path, bundle),
            "original_source_reads_this_command": 0, "input_acceptance": False,
            "B_C_admission": False,
            "own_future_return": "NOT_CLAIMED_REQUIRES_SEPARATE_ACTUAL_OBSERVATION"}


def finalize_result(core_plan):
    """File two independent NEW copies after the auditor's actual native return."""
    root = Path(core_plan["root"])
    core, _ = read_metadata(root / "certificate-bundle.json", 32 * 1024**2,
                            canonical_required=True)
    native = load("p17_m2_source_binding_native")
    metadata_root = Path(str(root) + "-certificate-audit")
    metadata_plan, metadata_raw = read_metadata(metadata_root / "plan.json", 2 * 1024**2,
                                               canonical_required=True)
    metadata_events, _ = read_metadata(metadata_root / (METADATA_ROLE + "-events.json"),
                                       2 * 1024**2, canonical_required=True)
    metadata_evidence = native.role_evidence(metadata_root, sha(metadata_raw), METADATA_ROLE)
    envelope = {"schema": "topolab.v2.m2-strict-source-binding.accepted-result.v1",
                "core_bundle": core, "metadata_plan": metadata_plan,
                "metadata_events": metadata_events,
                "metadata_evidence": load("p17_m2_content_verified_control").evidence_json(
                    metadata_evidence),
                "own_future_return": "NOT_CLAIMED_REQUIRES_SEPARATE_ACTUAL_OBSERVATION"}
    certificate, audit = verify_result_envelope(envelope)
    need(core_plan == core["plan"] and audit["T1"] >= max(
        row["T1"] for row in certificate["native_role_audits"].values()),
        "result auditor must follow all source-role actual returns")
    authority = json.loads(AUTHORITY.read_bytes())
    if core_plan["context"]["scope"] == PUBLIC_SCOPE:
        paths = list(map(Path, authority["preparation_proofs"]["public_certificate_paths"]))
    else:
        prefix = Path(authority["evidence_root"]) / (
            "binding-formal-v" + str(core_plan["context"]["attempt"]) + "-accepted-result")
        paths = [Path(str(prefix) + ".json"), Path(str(prefix) + "-backup.json")]
    hashes = [put_new(path, envelope) for path in paths]
    need(hashes[0] == hashes[1]
         and (paths[0].stat().st_dev, paths[0].stat().st_ino)
         != (paths[1].stat().st_dev, paths[1].stat().st_ino),
         "independent result copies required")
    return {"status": "STRICT23_REGISTERED_NATIVE_AND_INDEPENDENT_RETURN_ACCEPTED",
            "scope": core_plan["context"]["scope"], "paths": list(map(str, paths)),
            "sha256": hashes[0], "bindings": 23, "input_acceptance": False,
            "B_C_admission": False,
            "own_future_return": "NOT_CLAIMED_REQUIRES_SEPARATE_ACTUAL_OBSERVATION"}


def accept_role(plan, role, events_sha):
    """After actual tool returns, retain the verdict and close only the owned active marker."""
    root = Path(plan["root"])
    events, _ = read_metadata(root / (role + "-events.json"), 2 * 1024**2,
                              expected=events_sha, canonical_required=True)
    native = load("p17_m2_source_binding_native")
    evidence = native.role_evidence(root, sha(canonical(plan)), role)
    result = native.audit_role(plan, role, evidence, events)
    need(time.time_ns() <= plan["deadline_unix_ns"], "acceptance outside fixed role window")
    record = {"native_verdict": result, "events_sha256": events_sha,
              "raw_tool_events": events, "plan_sha256": sha(canonical(plan)),
              "own_future_return": "NOT_CLAIMED_REQUIRES_SEPARATE_ACTUAL_OBSERVATION"}
    put_new(root / (role + "-accepted.json"), record)
    if result.get("closed_attempt_verified"):
        active, _ = read_metadata(root / "active.json", 16384, canonical_required=True)
        need(active == {"role": role, "plan_sha256": sha(canonical(plan)), "status": "ACTIVE"},
             "owned active marker differs")
        (root / "active.json").unlink()
    if not result.get("full_role_evidence_accepted") and not (root / "STOP.json").exists():
        put_new(root / "STOP.json", record | {
            "status": "STOP_NO_RETRY", "role": role,
            "full_native_evidence": load("p17_m2_content_verified_control").evidence_json(evidence),
        })
    return result


def payload(plan, role):
    stage = "payload_launch"
    try:
        if plan["schema"] == METADATA_SCHEMA:
            admit_metadata_plan(plan, role)
        else:
            admit_plan(plan, role)
        load("p17_m2_source_binding_native").assert_payload_launch(plan, role)
        stage = "source_read"
        if plan["schema"] == METADATA_SCHEMA:
            stage = "metadata_certificate_audit"
            bundle, _ = read_metadata(Path(plan["bundle"]["path"]), 32 * 1024**2,
                                      expected=plan["bundle"]["sha256"], canonical_required=True)
            result = replay_bundle(bundle)
        elif role.endswith("-availability"):
            result = availability(Path(plan["context"]["source_root"]), plan["context"])
        elif role == "binding-producer":
            result = register(Path(plan["context"]["source_root"]), plan["context"])
        elif role == "binding-independent":
            primary, _ = role_result(plan, "binding-producer")
            result = load("p17_m2_source_binding_independent").register(
                Path(plan["context"]["source_root"]), plan["context"], primary)
        elif role == "binding-closeout":
            result = closeout(plan)
        else:
            raise ValueError("STRICT_BINDING: unknown payload role")
        put_new(Path(plan["root"]) / (role + "-output.json"), result)
        return result
    except BaseException as error:
        source_failure = (getattr(error, "binding_failure", None)
                          or getattr(error, "strict_binding_failure", None))
        return {"schema": "topolab.v2.m2-strict-source-binding.failure.v1",
                "status": "STOP_NO_RETRY", "execution_identity": IDENTITY,
                "role": role, "stage": stage,
                "source_attempts": (source_failure or {}).get("attempts", []),
                "binding_failure": getattr(error, "binding_failure", None),
                "independent_failure": getattr(error, "strict_binding_failure", None),
                **error_context(error)}


def check_context(source, context):
    authority = json.loads(AUTHORITY.read_bytes())
    need(set(context) == {"execution_identity", "scope", "attempt", "source_root",
                          "authority_sha256", "source_tree", "actors"}, "context fields differ")
    need(context["execution_identity"] == IDENTITY
         and context["authority_sha256"] == sha(AUTHORITY.read_bytes())
         and context["source_tree"] == source_freeze()
         and context["actors"] == authority["actors"]
         and type(context["attempt"]) is int and context["attempt"] in (1, 2)
         and context["scope"] in (PUBLIC_SCOPE, FORMAL_SCOPE)
         and str(Path(source).absolute()) == context["source_root"],
         "source/context/freeze differs")
    if context["scope"] == FORMAL_SCOPE:
        need(context["source_root"] == authority["registration_source_root"],
             "formal literal source differs")
    else:
        need(Path(source).name.startswith("topolab-public-strict-binding-"),
             "new public source root required")
    need(authority["source_whitelist"] == whitelist(), "authority exact whitelist differs")


def error_context(error):
    chain, seen, current = [], set(), error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append({"type": type(current).__name__, "reason": str(current)})
        current = current.__cause__ if current.__cause__ is not None else current.__context__
    return {"primary_error": chain[-1], "raised_error": chain[0],
            "exception_chain_raised_to_origin": chain,
            "secondary_errors": list(reversed(chain[:-1]))}


def register(source, context):
    """Read and parse the same strictly stable buffer once for each literal path.

    Formal CLI admission is enforced by the frozen outer plan before this
    internal read seam is entered. This function itself grants no authority.
    """
    check_context(source, context)
    producer = load("p17_m2_input_export")
    reader = producer.Reader(source, execution_identity=producer.LOCAL_IDENTITY,
                             source_identity_checks=True, source_identity_policy=None)
    wire = dict(context, schema=READ_SCHEMA, role="producer",
                author=context["actors"]["producer"], rows=[], attempts=[], failures=[],
                helper_execution_identity=producer.LOCAL_IDENTITY,
                helper_identity_relabelled=False, source_identity_policy=None,
                pre_read_expected_sha256=None)
    try:
        for row in whitelist():
            reader.packet(row["path"], row["max_bytes"], total=2785280)
    except BaseException as error:
        wire.update(rows=reader.source_observations, attempts=reader.attempts,
                    failures=reader.failures,
                    source_facts=reader.source_facts, **error_context(error))
        error.binding_failure = wire
        raise
    wire.update(rows=reader.source_observations, attempts=reader.attempts,
                failures=reader.failures)
    return wire


def physical(value):
    return {key: getattr(value, key) for key in
            ("st_dev", "st_ino", "st_size", "st_mtime_ns")}


def source_parent(source, relative):
    """Rewalk the literal path without following any directory or leaf symlink."""
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in (*Path(source).parts[1:], *Path(relative).parts[:-1]):
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = child
        return parent
    except Exception:
        os.close(parent)
        raise


def availability(source, context):
    """Observe bounded no-content availability; never establish a trusted hash.

    A subsequent registration always makes its own original strict observations.
    Metadata changes here are recorded, without claiming their cause.
    """
    check_context(source, context)
    result = dict(context, schema="topolab.v2.m2-strict-source-binding.availability.v1",
                  content_read_bytes=0, rows=[])
    started = time.monotonic()
    try:
        for item in whitelist():
            row = {"path": item["path"], "hash": None, "observations": []}
            result["rows"].append(row)
            parent = source_parent(source, item["path"])
            fd = None
            try:
                declared = os.stat(Path(item["path"]).name, dir_fd=parent,
                                   follow_symlinks=False)
                row["mtime_differences_ns"] = []

                def observe(point, value, *, row=row, declared=declared):
                    row["observations"].append(dict(point=point, **physical(value)))
                    row["mtime_differences_ns"].append(value.st_mtime_ns - declared.st_mtime_ns)
                    need(all(getattr(value, key) == getattr(declared, key)
                             for key in ("st_dev", "st_ino", "st_size")),
                         "availability physical identity changed")

                observe("declared", declared)
                need(stat.S_ISREG(declared.st_mode)
                     and 0 < declared.st_size <= item["max_bytes"],
                     "availability file type/size differs")
                fd = os.open(Path(item["path"]).name, os.O_RDONLY | os.O_NOFOLLOW,
                             dir_fd=parent)
                observe("opened", os.fstat(fd))
                for n in range(3):
                    time.sleep(0.05)
                    observe(f"descriptor-{n}", os.fstat(fd))
                    closing_parent = source_parent(source, item["path"])
                    try:
                        latest = os.stat(Path(item["path"]).name, dir_fd=closing_parent,
                                         follow_symlinks=False)
                    finally:
                        os.close(closing_parent)
                    need(stat.S_ISREG(latest.st_mode), "availability path type differs")
                    observe(f"path-{n}", latest)
                keys = ("st_dev", "st_ino", "st_size")
                last = [{key: value[key] for key in (*keys, "st_mtime_ns")}
                        for value in row["observations"][-3:]]
                need(last[0] == last[1] == last[2], "availability terminal metadata unstable")
                need(time.monotonic() - started < 140, "availability bounded clock exceeded")
            finally:
                if fd is not None:
                    os.close(fd)
                os.close(parent)
    except BaseException as error:
        result.update(error_context(error))
        error.binding_failure = result
        raise
    return result


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(prog="STRICT_BINDING", description=__doc__)
    parser.add_argument("mode", choices=(
        "prepare-public", "prepare-formal", "prepare-audit", "payload", "accept-role",
        "certify-core", "finalize-result", "show-commands", "file-actual-event"))
    parser.add_argument("--root")
    parser.add_argument("--plan")
    parser.add_argument("--plan-sha")
    parser.add_argument("--role")
    parser.add_argument("--events-sha")
    parser.add_argument("--bundle")
    parser.add_argument("--bundle-sha")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--certificate-sha")
    parser.add_argument("--preflight-sha")
    parser.add_argument("--preflight-return-sha")
    parser.add_argument("--caller-start-ms", type=int)
    parser.add_argument("--packet")
    parser.add_argument("--packet-sha")
    parser.add_argument("--event-mode", choices=("supervise", "record"))
    args = parser.parse_args()
    if args.mode == "prepare-public":
        need(args.root is not None and args.plan is args.plan_sha is args.role is None,
             "public setup accepts only a new literal root")
        result = prepare_public(args.root)
    elif args.mode == "prepare-formal":
        need(args.root is args.plan is args.plan_sha is args.role is args.events_sha is None
             and sys.platform == "darwin" and platform.machine() == "arm64"
             and all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                     and value != "0" * 64 for value in (
                         args.certificate_sha, args.preflight_sha, args.preflight_return_sha)),
             "formal actual public evidence/main preflight SHA prerequisites required")
        result = prepare_formal(args.attempt, args.certificate_sha, args.preflight_sha,
                                args.preflight_return_sha, args.caller_start_ms)
    elif args.mode == "prepare-audit":
        need(args.root is args.plan is args.plan_sha is args.role is args.events_sha is None
             and args.bundle is not None and args.bundle_sha is not None,
             "metadata audit setup accepts only one exact new bundle")
        result = prepare_metadata_audit(args.bundle, args.bundle_sha)
    elif args.mode == "payload":
        need(args.root is None and args.plan is not None and args.plan_sha is not None
             and args.role in (*ROLE_CAPS, METADATA_ROLE),
             "literal frozen payload plan/role required")
        result = payload(load_plan(args.plan, args.plan_sha), args.role)
    elif args.mode == "accept-role":
        need(args.root is None and args.plan is not None and args.plan_sha is not None
             and args.role in (*ROLE_CAPS, METADATA_ROLE) and args.events_sha is not None,
             "actual-return acceptance requires the exact role and event SHA")
        result = accept_role(load_plan(args.plan, args.plan_sha), args.role, args.events_sha)
    elif args.mode == "certify-core":
        need(args.root is args.role is args.events_sha is None and args.plan is not None
             and args.plan_sha is not None, "certificate requires only one exact pinned plan")
        result = certify_core(load_plan(args.plan, args.plan_sha))
    elif args.mode == "finalize-result":
        need(args.root is args.role is args.events_sha is None and args.plan is not None
             and args.plan_sha is not None, "result filing requires one exact core plan")
        result = finalize_result(load_plan(args.plan, args.plan_sha))
    elif args.mode == "show-commands":
        plan = load_plan(args.plan, args.plan_sha)
        native = load("p17_m2_source_binding_native")
        result = {role: {mode: {"argv": native.argv_for(plan, mode, role),
                                "cmd": literal_command(native.argv_for(plan, mode, role))}
                         for mode in ("supervise", "record")} for role in plan["role_order"]}
    else:
        need(args.root is None and args.plan is not None and args.plan_sha is not None
             and args.role is not None and args.event_mode is not None
             and args.packet is not None and args.packet_sha is not None,
             "original actual tool packet and role/mode required")
        result = file_actual_event(load_plan(args.plan, args.plan_sha), args.role,
                                   args.event_mode, args.packet, args.packet_sha)
    print(canonical(result).decode(), end="")
    return 1 if result.get("status") == "STOP_NO_RETRY" else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(canonical({"status": "STOP_NO_RETRY", "stage": "control",
                         "source_attempts": [], **error_context(exc)}).decode(), end="")
        raise SystemExit(1) from exc
