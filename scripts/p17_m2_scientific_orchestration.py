"""Finite native adapter for the separately granted M2 scientific identity.

Published helper schemas retain their original identity. This adapter registers
new actual commands; a helper's consistent public record grants no B/C access.
"""

import argparse
import hashlib
import importlib.machinery
import importlib.metadata
import importlib.util
import json
import math
import os
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IDENTITY = "topolab.v2.p17-m2-native-homotopy.rss.v1"
LIMIT = 4294967296


def load(name):
    path = Path(__file__).with_name(name + ".py")
    existing = sys.modules.get(name)
    if existing is not None and Path(existing.__file__).resolve() == path:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("frozen scientific helper unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def native_helpers():
    load("p17_m2_homotopy")  # Existing resource helper's disclosed direct import.
    return load("p17_m2_resource_control"), load("p17_m2_independent_audit")


def private_mkdir(path):
    """Create one exclusive private child through a no-follow parent FD."""
    helper = load("p17_m2_content_verified_control")
    directory = helper.nofollow_directory(path.parent)
    try:
        os.mkdir(path.name, 0o700, dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_native_log(path, cap=4 * 1024**2):
    """Read only NEW native stdout, including zero bytes, with strict identity."""
    path = Path(os.path.abspath(path))
    helper = load("p17_m2_input_export_independent")
    facts = {
        "path": str(path),
        "declared": None,
        "before": None,
        "after": None,
        "closing": None,
        "returned_bytes": None,
    }

    def observed(info):
        return {
            key: getattr(info, key)
            for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_mode", "st_nlink")
        }

    try:
        directory = helper.nofollow_parent(path)
        try:
            declared = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            facts["declared"] = observed(declared)
            if (
                not stat.S_ISREG(declared.st_mode)
                or declared.st_nlink != 1
                or not 0 <= declared.st_size <= cap
            ):
                raise ValueError("NEW_NATIVE_LOG_KIND_OR_CAP_REFUSED")
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            try:
                facts["before"] = observed(os.fstat(fd))
                if facts["before"] != facts["declared"]:
                    raise ValueError("NATIVE_LOG_IDENTITY_CHANGED")
                chunks, remaining = [], cap + 1
                while remaining:
                    chunk = os.read(fd, min(remaining, 1024**2))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                raw = b"".join(chunks)
                facts["returned_bytes"] = len(raw)
                facts["after"] = observed(os.fstat(fd))
            finally:
                os.close(fd)
        finally:
            os.close(directory)
        closing_parent = helper.nofollow_parent(path)
        try:
            facts["closing"] = observed(
                os.stat(path.name, dir_fd=closing_parent, follow_symlinks=False)
            )
        finally:
            os.close(closing_parent)
        if (
            not facts["declared"] == facts["before"] == facts["after"] == facts["closing"]
            or len(raw) != declared.st_size
        ):
            raise ValueError("NATIVE_LOG_IDENTITY_CHANGED")
        return raw, facts
    except BaseException as error:
        error.native_log_facts = facts
        raise


def observe_native(contract, contract_sha, role, label):
    """Close one registered native timer; caller closes this dispatcher's exit."""
    resource, _ = native_helpers()
    role_spec = contract["roles"][role]
    if label in ("reservation", "reader-ack"):
        spec = contract["shared_helpers"][role][label]
        argv = resolved_argv(spec["argv"], contract_sha)
    else:
        spec = role_spec["native_dispatch"][label]
        argv = resolved_argv(role_spec["exit_argv"][label], contract_sha)
    dispatch_argv = resolved_argv(spec["dispatch_argv"], contract_sha)
    if sys.orig_argv != startup_argv(spec["dispatch_argv"], contract_sha, contract["runtime"]):
        raise ValueError("ACTUAL_NATIVE_DISPATCH_ARGV_CHANGED")
    profile, log, destination = (
        Path(spec[key]) for key in ("profile_path", "log_path", "dispatch_path")
    )
    timeout = spec["timeout_seconds"]
    if (
        type(timeout) not in (int, float)
        or not math.isfinite(timeout)
        or not 0 < timeout <= role_spec["FULL_seconds"]
    ):
        raise ValueError("FINITE_NATIVE_DISPATCH_TIMEOUT_REQUIRED")
    offset = 4 if sys.platform == "darwin" else 5
    if len(argv) <= offset or argv != resource._timed(argv[offset:], profile):
        raise ValueError("REGISTERED_NATIVE_TIMER_REQUIRED")
    for path in (profile, log, destination):
        fd = load("p17_m2_input_export_independent").nofollow_parent(path)
        try:
            try:
                os.stat(path.name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise FileExistsError(path)
        finally:
            os.close(fd)
    began, started = time.monotonic(), time.time_ns()
    errors, descendant_groups, watchdog = [], [], None
    child, cleanup, timed_out, captured = None, None, False, 0

    def failed(stage, error):
        item = {"stage": stage, "type": type(error).__name__, "reason": str(error)}
        for attribute in (
            "native_log_facts",
            "scientific_stop_context",
            "scientific_payload_failure",
        ):
            if hasattr(error, attribute):
                item[attribute] = getattr(error, attribute)
        errors.append(item)

    try:
        fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            child = subprocess.Popen(
                argv,
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            child.native_started = began
            try:
                os.set_blocking(child.stdout.fileno(), False)
                captured = 0
                while True:
                    try:
                        chunk = os.read(child.stdout.fileno(), 65536)
                    except BlockingIOError:
                        chunk = b""
                    if chunk:
                        remaining = 4 * 1024**2 - captured
                        stream.write(chunk[: max(0, remaining)])
                        captured += len(chunk)
                        if captured > 4 * 1024**2:
                            failed("native stdout cap", ValueError("NEW_NATIVE_LOG4MIB_CAP"))
                            break
                    if resource._native_poll(child) is not None and not chunk:
                        break
                    if time.monotonic() - began >= timeout:
                        timed_out = True
                        break
                    if not chunk:
                        time.sleep(0.01)
            except BaseException as error:
                failed("native wait", error)
            finally:
                # A still-owned outer controller can own separately sessioned
                # resource children. Snapshot actual descendants before killing
                # their parent; PID files alone are never a cleanup registry.
                try:
                    if resource._native_poll(child) is None:
                        try:
                            rows, watchdog = resource._snapshot(
                                destination.parent, destination.stem + "-watchdog", child.pid
                            )
                            child.registered_command_pids = tuple(
                                r["pid"]
                                for r in rows
                                if r["parent"] == child.pid and r["pgid"] == child.pid
                            )
                            if watchdog.get("problem"):
                                failed("watchdog sampler", ValueError(watchdog["problem"]))
                            for pgid in sorted({r["pgid"] for r in rows} - {child.pid}):
                                members = [r for r in rows if r["pgid"] == pgid]
                                fact = {
                                    "pgid": pgid,
                                    "observed_pids": [r["pid"] for r in members],
                                    "signals": [],
                                    "group_gone": None,
                                }
                                for sig in (signal.SIGTERM, signal.SIGKILL):
                                    if resource._native_poll(child) is not None:
                                        break
                                    for row in members:
                                        if row["pid"] != pgid:
                                            try:
                                                os.kill(row["pid"], sig)
                                                fact["signals"].append(
                                                    sig.name + "_OBSERVED_COMMAND"
                                                )
                                            except ProcessLookupError:
                                                pass
                                            except OSError as error:
                                                failed("observed command signal", error)
                                    time.sleep(0.05)
                                    try:
                                        os.killpg(pgid, sig)
                                        fact["signals"].append(sig.name)
                                    except ProcessLookupError:
                                        break
                                    except OSError as error:
                                        failed("observed group signal", error)
                                deadline = time.monotonic() + 4.9
                                while True:
                                    try:
                                        os.killpg(pgid, 0)
                                    except ProcessLookupError:
                                        fact["group_gone"] = True
                                        break
                                    except OSError as error:
                                        failed("observed group closeout", error)
                                        break
                                    if time.monotonic() >= deadline:
                                        fact["group_gone"] = False
                                        break
                                    time.sleep(0.01)
                                descendant_groups.append(fact)
                        except BaseException as error:
                            failed("observed descendant cleanup", error)
                except BaseException as error:
                    failed("cleanup observation", error)
                try:
                    cleanup = resource._terminate(child.pid, child)
                except BaseException as error:
                    failed("owned timer cleanup", error)
                child.stdout.close()
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException as error:
        failed("native dispatch", error)
    timer = None if child is None else getattr(child, "timer_native_exit", None)
    log_raw, log_facts, profile_raw = None, None, None
    try:
        log_raw, log_facts = read_native_log(log)
        profile_raw = load("p17_m2_source_acquisition_independent").native._software_bytes(profile)
        resource.native(profile_raw.decode(), sys.platform)
    except BaseException as error:
        log_facts = getattr(error, "native_log_facts", log_facts)
        failed("native evidence read", error)
    gone = (
        cleanup is not None
        and cleanup["group_gone"] is True
        and all(v["group_gone"] is True for v in descendant_groups)
    )
    result = {
        "schema": "topolab.v2.m2-native-dispatch.v1",
        "execution_identity": IDENTITY,
        "contract_sha256": contract_sha,
        "role": role,
        "label": label,
        "argv": argv,
        "dispatch_argv": dispatch_argv,
        "startup_orig_argv": list(sys.orig_argv),
        "python_entry": sys.executable,
        "pid": os.getpid(),
        "native_pid": None if child is None else child.pid,
        "started_unix_ns": started,
        "returned_unix_ns": time.time_ns(),
        "elapsed_seconds": time.monotonic() - began,
        "exit_code": None if child is None else child.returncode,
        "log_sha256": None if log_raw is None else sha(log_raw),
        "profile_sha256": None if profile_raw is None else sha(profile_raw),
        "native_log_facts": log_facts,
        "stdout_observed_bytes": captured,
        "stdout_retained_bytes": None if log_raw is None else len(log_raw),
        "stdout_observed_truncated_bytes": max(0, captured - 4 * 1024**2),
        "unobserved_stdout_after_cap": "UNKNOWN" if captured > 4 * 1024**2 else "NOT_TRUNCATED",
        "timer_native_exit": timer,
        "self_rss_bytes_before_flush": resource._rss_self(),
        "self_rss_bytes_after_flush": None,
        "group_gone": gone,
        "cleanup": cleanup,
        "descendant_groups": descendant_groups,
        "watchdog_helper": watchdog,
        "cleanup_errors": errors,
        "own_future_exit": "UNKNOWN_PENDING_ACTUAL_EXTERNAL_TOOL_RETURN",
        "self_rss_scope": (
            "empirical before/after retained preflush packet; final serializer closed externally"
        ),
        "self_rss_phases": ["pre_preview_write", "post_preview_write_pre_final_serialization"],
        "status": "STOP_OUTER_TIMEOUT"
        if timed_out
        else (
            "COMPLETED_WITH_NATIVE_RETURN"
            if timer is not None and gone and not errors
            else "STOP_NATIVE_DISPATCH"
        ),
    }
    helper = load("p17_m2_content_verified_control")
    preflush = destination.with_name(destination.stem + "-preflush.json")
    try:
        helper.put(preflush, result)
        result["self_rss_bytes_after_flush"] = resource._rss_self()
        result["preflush_sha256"] = sha(canonical({**result, "self_rss_bytes_after_flush": None}))
        helper.put(destination, result)
    except BaseException as error:
        failed("dispatcher packet filing", error)
        result["status"] = "STOP_NATIVE_DISPATCH"
        result["self_rss_bytes_after_flush"] = resource._rss_self()
    return result


def resolved_argv(words, contract_sha):
    return [word.replace("@SCIENTIFIC_CONTRACT_SHA256@", contract_sha) for word in words]


def startup_argv(words, contract_sha, runtime):
    """Command entry and actual framework startup entry are separately frozen."""
    command = resolved_argv(words, contract_sha)
    if command[0] != runtime["python_entry"]:
        raise ValueError("FROZEN_LOGICAL_PYTHON_ENTRY_REQUIRED")
    return [runtime["python_startup_entry"], *command[1:]]


def import_origins():
    """Resolve package/native origins without running package initializers."""
    packages, native = {}, {}
    prefix = Path(sys.executable).absolute().parent.parent

    def observed(name, spec):
        if spec is None or not spec.origin:
            raise ValueError("ACTUAL_IMPORT_ORIGIN_UNAVAILABLE: " + name)
        path = Path(spec.origin).absolute()
        if name == "topolab":
            if path != REPO / "src/topolab/__init__.py":
                raise ValueError("TOPOLOGY_PACKAGE_ORIGIN_CHANGED")
        elif prefix not in path.parents:
            raise ValueError("LOCKED_VENV_IMPORT_ORIGIN_CHANGED: " + name)
        loaded = sys.modules.get(name)
        if loaded is not None and Path(loaded.__file__).absolute() != path:
            raise ValueError("LOADED_IMPORT_ORIGIN_CHANGED: " + name)
        return {"origin": str(path), "sha256": sha(path.read_bytes())}

    for name in ("topolab", "numpy", "scipy", "torch", "safetensors"):
        packages[name] = observed(name, importlib.util.find_spec(name))
    for name in (
        "numpy._core._multiarray_umath",
        "scipy.sparse.linalg._dsolve._superlu",
        "torch._C",
        "safetensors._safetensors_rust",
    ):
        parts = name.split(".")
        spec = importlib.util.find_spec(parts[0])
        for index in range(1, len(parts)):
            if spec is None or not spec.submodule_search_locations:
                raise ValueError("NATIVE_IMPORT_PARENT_UNAVAILABLE: " + name)
            spec = importlib.machinery.PathFinder.find_spec(
                ".".join(parts[: index + 1]), spec.submodule_search_locations
            )
        native[name] = observed(name, spec)
    return packages, native


def scientific_runtime():
    """Freeze logical venv entry and physical interpreter separately."""
    entry = Path(sys.executable).absolute()
    cfg = entry.parent.parent / "pyvenv.cfg"
    packages, native = import_origins()
    return {
        "python_entry": str(entry),
        "python_startup_entry": str(Path(sys.orig_argv[0]).absolute()),
        "python_startup_sha256": sha(Path(sys.orig_argv[0]).read_bytes()),
        "python_physical": str(entry.resolve()),
        "python_sha256": sha(entry.read_bytes()),
        "python_version": sys.version,
        "pyvenv_cfg_sha256": sha(cfg.read_bytes()),
        "platform": sys.platform,
        "cwd": str(REPO),
        "lock_sha256": sha((REPO / "uv.lock").read_bytes()),
        "threads": {
            key: os.environ.get(key)
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
        "distributions": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "scipy", "torch", "safetensors")
        },
        "import_origins": packages,
        "native_origins": native,
        "torch_threads_policy": {"intraop": 1, "interop": 8},
    }


def source_manifest():
    names = subprocess.run(
        ["git", "ls-files", "-z", "src", "scripts", "uv.lock"],
        cwd=REPO,
        capture_output=True,
        check=True,
        timeout=15,
    ).stdout
    return {name: sha((REPO / name).read_bytes()) for name in names.decode().split("\0") if name}


def read_contract(path, expected_sha, *, payload_role=None, publication_check=False):
    """Recheck SHA-bound bytes; Git eligibility belongs to publication metadata."""
    allowed = {
        REPO / "docs/planning/p17_m2_scientific_execution_protocol.json",
        REPO / "docs/planning/p17_m2_scientific_remedy_execution_protocol.json",
    }
    path = Path(os.path.abspath(path))
    if path not in allowed:
        raise ValueError("UNREGISTERED_SCIENTIFIC_CONTRACT")
    checker = load("p17_m2_source_acquisition_independent")
    raw = checker.native._software_bytes(path)
    if sha(raw) != expected_sha:
        raise ValueError("SCIENTIFIC_CONTRACT_HASH_CHANGED")
    value = checker.native.base.parse(raw)
    if publication_check:
        committed = subprocess.run(
            ["git", "show", "HEAD:" + str(path.relative_to(REPO))],
            cwd=REPO,
            capture_output=True,
            check=True,
            timeout=15,
        ).stdout
        if raw != committed or value.get("source_freeze") != source_manifest():
            raise ValueError("COMMITTED_SCIENTIFIC_FREEZE_REQUIRED")
    elif payload_role is not None:
        # Parent checked the committed inventory before native entry. The child
        # rechecks every byte without spawning unregistered Git descendants.
        check_payload_start(value, expected_sha, payload_role)
    load("p17_m2_scientific_independent").check_contract(value)
    if (
        raw != canonical(value)
        or value.get("schema") != "topolab.v2.m2-scientific-contract.v1"
        or value.get("execution_identity") != IDENTITY
        or value.get("runtime") != scientific_runtime()
        or value["runtime"]["threads"]
        != dict.fromkeys(
            (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            ),
            "1",
        )
        or canonical(value.get("permissions")) != canonical({"B": True, "C": True})
        or type(value.get("resource_limit_bytes")) is not int
        or value["resource_limit_bytes"] != LIMIT
    ):
        raise ValueError("FROZEN_SCIENTIFIC_SOURCE_RUNTIME_AUTHORITY_REQUIRED")
    return value


def check_payload_start(contract, contract_sha, role):
    spec = contract["roles"][role]
    start = spec["inner_starts"][0]
    root = Path(spec["root"]) / "native" / start["name"]
    read = load("p17_m2_content_verified_control").read_json
    pending = read(root / "pending.json")
    until = time.monotonic() + 1
    while True:
        try:
            started = read(root / "started.json")
            break
        except FileNotFoundError:
            if time.monotonic() >= until:
                raise
            time.sleep(0.01)
    argv = resolved_argv(start["argv"], contract_sha)
    if (
        sys.orig_argv != startup_argv(start["argv"], contract_sha, contract["runtime"])
        or pending.get("argv") != argv
        or started.get("argv") != argv
        or started.get("status") != "STARTED"
        or started.get("pid") != os.getppid()
        or started.get("pgid") != os.getpgrp()
        or pending.get("controller_pid") != started.get("controller_pid")
    ):
        raise ValueError("REGISTERED_NATIVE_PAYLOAD_PARENT_REQUIRED")


def retain_payload_failure(root, role, contract_sha, error, *, certificate, lease, consumer, began):
    packet = {
        "schema": "topolab.v2.m2-scientific-payload-failure.v1",
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": contract_sha,
        "role": role,
        "status": "STOP_NO_RETRY",
        "error_type": type(error).__name__,
        "reason": str(error),
        "wall_seconds": time.monotonic() - began,
        "own_future_exit": "UNKNOWN_PENDING_ACTUAL_NATIVE_RETURN",
        "retained_context": {
            key: getattr(error, key)
            for key in ("scientific_stop_context", "scientific_failure")
            if hasattr(error, key)
        },
        "input_failure": getattr(consumer, "failure", None),
        "input_source_facts": getattr(getattr(consumer, "reader", None), "source_facts", None),
        "input_source_identities": getattr(
            getattr(consumer, "reader", None), "source_observations", None
        ),
        "certificate_acquired": certificate is not None,
        "reader_lease_acquired": lease is not None,
        "lease_disposition": "NOT_ACQUIRED" if lease is None else "HELD_NO_MANUAL_RELEASE",
        "lease_context": {
            key: getattr(lease, key, None) for key in ("_record", "_identity", "_handed_off")
        },
        "secondary_errors": [],
    }
    try:
        load("p17_m2_content_verified_control").put(root / "payload-failure.json", packet)
    except BaseException as secondary:
        packet["secondary_errors"].append(
            {
                "stage": "payload context filing",
                "type": type(secondary).__name__,
                "reason": str(secondary),
            }
        )
    try:
        if not getattr(error, "scientific_failure_stderr_written", False):
            raw = canonical(packet)
            if len(raw) > 64 * 1024**2:
                raise ValueError("SCIENTIFIC_FAILURE_LOG_CAP_EXCEEDED")
            sys.stderr.buffer.write(raw)
            sys.stderr.buffer.flush()
    except BaseException as secondary:
        packet["secondary_errors"].append(
            {
                "stage": "payload stderr fallback",
                "type": type(secondary).__name__,
                "reason": str(secondary),
            }
        )
    error.scientific_payload_failure = packet
    return packet


def bind_exit(root, label, role, contract_sha, observed_exit):
    """Append NEW scientific native facts only after the prior command returned."""
    if label not in ("controller", "binder", "verifier") or type(observed_exit) is not int:
        raise ValueError("REGISTERED_ACTUAL_EXIT_REQUIRED")
    root = Path(os.path.abspath(root))
    checker = load("p17_m2_source_acquisition_independent")
    read = checker.native._software_bytes
    previous = {
        "controller": "controller-summary.json",
        "binder": "controller-exit.json",
        "verifier": "binder-exit.json",
    }[label]
    prior_raw = read(root / previous)
    prior = checker.native.base.parse(prior_raw)
    expected = (
        "PENDING_POSTEXIT"
        if label == "controller"
        else ("PENDING_BINDER_EXIT" if label == "binder" else "PENDING_VERIFIER_EXIT")
    )
    if (
        prior.get("execution_identity") != IDENTITY
        or prior.get("role") != role
        or prior.get("scientific_contract_sha256") != contract_sha
        or prior.get("status") != expected
    ):
        raise ValueError("SCIENTIFIC_EXIT_CHAIN_CHANGED")
    profile_raw, log_raw = read(root / (label + ".time")), read(root / (label + ".log"))
    resource, _ = native_helpers()
    measured = resource.native(profile_raw.decode(), sys.platform)
    result = {
        "schema": "topolab.v2.m2-scientific-native-exit-binding.v1",
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": contract_sha,
        "role": role,
        "bound_role": label,
        "prior_status": expected,
        "status": "PENDING_BINDER_EXIT" if label == "controller" else "PENDING_VERIFIER_EXIT",
        "record_sha256": sha(prior_raw),
        "profile_sha256": sha(profile_raw),
        "log_sha256": sha(log_raw),
        "native": measured,
        "exit_code": observed_exit,
        "resource_cap_exceeded": measured["rss_bytes"] > LIMIT,
        "own_future_exit": "UNKNOWN_PENDING_ACTUAL_OUTER_RETURN",
    }
    load("p17_m2_content_verified_control").put(root / (label + "-exit.json"), result)
    return result


def load_role_evidence(contract, role):
    """Replay only finite NEW registered role files; never original sources."""
    root = Path(contract["roles"][role]["root"])
    reader = load("p17_m2_input_export_independent").OnceReader(
        root, 65536, 512 * 1024**2, source_identity_checks=True
    )
    cache = {}
    log_facts = {}

    def read(relative, cap=1024**2):
        if relative not in cache:
            if relative.endswith(".log"):
                raw, log_facts[relative] = read_native_log(root / relative, cap)
                cache[relative] = raw
            else:
                cache[relative] = reader.read(relative, cap)
            if len(cache) > 65536 or sum(map(len, cache.values())) > 512 * 1024**2:
                raise ValueError("NEW_NATIVE_EVIDENCE_TOTAL_CAP")
        return cache[relative]

    def parsed(relative, cap=1024**2):
        return load("p17_m2_input_export").parse(read(relative, cap))

    cases = []
    for spec in contract["roles"][role]["inner_starts"]:
        directory = (
            "controls/" + spec["name"] if role == "resource-preflight" else "native/" + spec["name"]
        )
        record = parsed(directory + "/command.json", 128 * 1024**2)
        profiles = {
            item["profile"]: read(directory + "/" + item["profile"])
            for item in record["helpers"]
            if item.get("profile")
        }
        cases.append(
            {
                "name": spec["name"],
                "record": record,
                "profile": read(directory + "/command.time"),
                "log": read(directory + "/command.log", 4 * 1024**2),
                "helper_profiles": profiles,
            }
        )
    links = []
    for label, previous in (
        ("controller", "controller-summary.json"),
        ("binder", "controller-exit.json"),
        ("verifier", "binder-exit.json"),
    ):
        links.append(
            {
                "label": label,
                "binding": parsed(label + "-exit.json"),
                "prior": read(previous),
                "profile": read(label + ".time"),
                "log": read(label + ".log", 4 * 1024**2),
                "dispatch": read(label + ".dispatch.json"),
                "preflush": read(label + ".dispatch-preflush.json"),
                "observed_exit_code": 0,
            }
        )
    events = parsed("trusted-returns.json")
    last_log = read("final-observer.log", 4 * 1024**2)
    rows, inner_charge = 0, sum(case["record"]["observed_outer_wall_seconds"] for case in cases)
    if role != "resource-preflight":
        payload = load("p17_m2_input_export").parse(cases[0]["log"])
        rows = payload["result"]["attempted_rows"]
        inner_charge = payload["result"]["internal_row_charge_seconds"]
    return {
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": sha(canonical(contract)),
        "role": role,
        "platform": sys.platform,
        "cases": cases,
        "case_spans": parsed("case-spans.json"),
        "exit_bindings": links,
        "raw_tool_events": events,
        "last_observer_profile": read("final-observer.time"),
        "last_observer_log": last_log,
        "last_observer_dispatch": read("final-observer.dispatch.json"),
        "last_observer_preflush": read("final-observer.dispatch-preflush.json"),
        "last_observer_exit_code": events[-1]["exit_code"],
        "whole_wall_seconds": events[-1]["end_seconds"] - events[0]["start_seconds"],
        "attempted_rows": rows,
        "inner_charge_seconds": inner_charge,
        "reservation_helper": load_shared_helper_evidence(contract, role, "reservation"),
        "native_log_facts": log_facts,
    }


def load_shared_helper_evidence(contract, role, action):
    root = Path(contract["roles"][role]["root"])
    stem = "reservation" if action == "reservation" else "reader-ack"
    read = load("p17_m2_source_acquisition_independent").native._software_bytes
    event = json.loads(read(root / (stem + "-return.json")))
    helper = contract["shared_helpers"][role][action]
    result = {
        "event": event,
        "profile": read(Path(helper["profile_path"])),
        "log": read_native_log(Path(helper["log_path"]))[0],
        "dispatch": read(Path(helper["dispatch_path"])),
        "preflush": read(
            Path(helper["dispatch_path"]).with_name(
                Path(helper["dispatch_path"]).stem + "-preflush.json"
            )
        ),
    }
    if action == "reservation":
        result["pending"] = json.loads(read(root / "quota-pending.json"))
    return result


def check_reader_ack_return(contract, role):
    independent = load("p17_m2_scientific_independent")
    return independent.check_shared_helper_return(
        contract, role, "reader-ack", load_shared_helper_evidence(contract, role, "reader-ack")
    )


def publication_metadata(contract, contract_sha, role):
    """Separately billed repository eligibility; no scientific inputs or leases."""
    began = time.time()
    control = load("p17_m2_source_acquisition_control")
    authority_raw = control.FUNDED_AUTHORITY_RAW
    if "acquisition" in contract:
        acquisition = contract["acquisition"]
        content = acquisition.get("content_root") if type(acquisition) is dict else None
        if type(content) is not str:
            raise ValueError("REGISTERED_SCIENTIFIC_ACQUISITION_REQUIRED")
        path = Path(content)
        if (not path.is_absolute() or str(path) != content or path.name != "content"
                or any(part in (".", "..") for part in path.parts)):
            raise ValueError("REGISTERED_SCIENTIFIC_ACQUISITION_REQUIRED")
        authority_raw, attempt = control.authority_for_root(path.parent)
        if (authority_raw is None
                or (attempt == 2 and authority_raw is not control.REMEDY_AUTHORITY_RAW)):
            raise ValueError("REGISTERED_SCIENTIFIC_ACQUISITION_AUTHORITY_REQUIRED")
        declared = control.formal_plan(authority_raw, attempt=attempt)
        if (declared["root"] != str(path.parent)
                or declared["content_root"] != content):
            raise ValueError("REGISTERED_SCIENTIFIC_ACQUISITION_REQUIRED")
    authority = control.load("p17_m2_input_export").parse(authority_raw)
    readiness = control.activation_readiness(authority)
    return {
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": contract_sha,
        "role": role,
        "metadata_only": True,
        "publication_readiness": readiness,
        "source_freeze_sha256": sha(canonical(contract["source_freeze"])),
        "runtime_sha256": sha(canonical(scientific_runtime())),
        "start_seconds": began,
        "end_seconds": time.time(),
        "own_future_exit": "UNKNOWN_PENDING_ACTUAL_PUBLICATION_TOOL_RETURN",
    }


def checked_publication_metadata(contract, contract_sha, role):
    spec = contract["roles"][role]
    read = load("p17_m2_source_acquisition_independent").native._software_bytes
    raw = read(Path(spec["publication_readiness_path"]))
    proof = json.loads(raw)
    event = json.loads(read(Path(spec["publication_return_path"])))
    head = read(REPO / ".git/HEAD").decode().strip()
    if head.startswith("ref: refs/heads/"):
        ref = head.removeprefix("ref: ")
        try:
            head = read(REPO / ".git" / ref).decode().strip()
        except FileNotFoundError:
            packed = read(REPO / ".git/packed-refs").decode().splitlines()
            matches = [line.split()[0] for line in packed if line.endswith(" " + ref)]
            if len(matches) != 1:
                raise ValueError("ACTUAL_PUBLICATION_HEAD_UNAVAILABLE") from None
            head = matches[0]
    if (
        proof.get("execution_identity") != IDENTITY
        or proof.get("role") != role
        or proof.get("scientific_contract_sha256") != contract_sha
        or proof.get("metadata_only") is not True
        or proof.get("publication_readiness", {}).get("main") != head
        or proof.get("source_freeze_sha256") != sha(canonical(contract["source_freeze"]))
        or proof.get("runtime_sha256") != sha(canonical(scientific_runtime()))
        or event.get("argv") != resolved_argv(spec["publication_argv"], contract_sha)
        or event.get("complete") is not True
        or event.get("exit_code") != 0
        or type(event.get("exit_code")) is not int
        or event.get("stdout_sha256") != sha(raw)
        or not event["start_seconds"]
        <= proof["start_seconds"]
        <= proof["end_seconds"]
        <= event["end_seconds"]
        <= time.time()
        <= event["end_seconds"] + 30
    ):
        raise ValueError("FRESH_ACTUAL_PUBLICATION_METADATA_RETURN_REQUIRED")
    return proof


def acquisition_certificate(contract):
    control = load("p17_m2_source_acquisition_control")
    root = Path(contract["acquisition"]["content_root"]).parent
    raw = control.base().read_json(root / "accepted-acquisition-bundle.json")
    facts = control.base().evidence_json(raw, decode=True)
    return control.load("p17_m2_source_acquisition_independent").audit_certificate(
        facts["bundle"], trusted_tool_events=facts["events"]
    )


def scientific_payload(contract, contract_sha, role):
    """The actual paid child: independently grant a real lease before decoding."""
    began = time.monotonic()
    certificate = lease = consumer = None
    root = Path(contract["roles"][role]["root"])
    try:
        independent = load("p17_m2_scientific_independent")
        import torch

        torch.set_num_threads(1)
        torch.set_num_interop_threads(8)
        actual_torch = {
            "intraop": torch.get_num_threads(),
            "interop": torch.get_num_interop_threads(),
        }
        if actual_torch != contract["runtime"]["torch_threads_policy"]:
            raise ValueError("ACTUAL_TORCH_THREADS_CHANGED")
        admission = independent.check_b_preflight(
            contract, load_role_evidence(contract, "resource-preflight")
        )
        certificate = independent.grant_scientific_input(
            acquisition_certificate(contract), contract, role, admission
        )
        lease = certificate.acquire_reader(role)
        consumer = load("p17_m2_source_verified_input").VerifiedAcquisitionInput(
            certificate, role, reader_lease=lease
        )
        root = Path(contract["roles"][role]["root"])
        private_mkdir(root / "rows")
        helper = load("p17_m2_content_verified_control")
        limits = contract["output_caps"][role]
        written_bytes, written_files = 0, 0

        def writer(relative, packet):
            nonlocal written_bytes, written_files
            raw = canonical(packet)
            path = Path(relative)
            if (
                path.is_absolute()
                or any(part in (".", "..") for part in path.parts)
                or len(raw) > limits["single_member_bytes_max"]
                or written_files + 1 > limits["files_max"]
                or written_bytes + len(raw) > limits["total_bytes_max"]
            ):
                raise RuntimeError("STOP_SCOPE_OR_WORK_CAP: scientific output bound")
            helper.put(root / "rows" / relative, packet)
            written_bytes += len(raw)
            written_files += 1
            return {"path": relative, "byte_size": len(raw), "sha256": sha(raw)}

        deadline = contract["roles"][role]["inner_starts"][0]["timeout_seconds"]

        def checkpoint():
            if time.monotonic() - began >= deadline - 2:
                raise TimeoutError("STOP_SCOPE_OR_WORK_CAP: scientific payload deadline")

        if role == "scientific-producer":
            result = load("p17_m2_scientific_control").produce(
                contract,
                consumer,
                contract_sha256=contract_sha,
                checkpoint=checkpoint,
                writer=writer,
            )
        else:
            producer_return = independent.check_scientific_role(
                contract, "scientific-producer", load_role_evidence(contract, "scientific-producer")
            )
            result = independent.audit_panel(
                contract,
                consumer,
                contract_sha256=contract_sha,
                producer_root=Path(contract["roles"]["scientific-producer"]["root"]) / "rows",
                producer_return=producer_return,
                checkpoint=checkpoint,
                writer=writer,
            )
        result["actual_numerical_runtime"] = {
            "torch_threads": actual_torch,
            "startup_orig_argv": sys.orig_argv,
            "python_entry": sys.executable,
        }
        return result
    except BaseException as error:
        retain_payload_failure(
            root,
            role,
            contract_sha,
            error,
            certificate=certificate,
            lease=lease,
            consumer=consumer,
            began=began,
        )
        raise


def run_registered_role(contract, contract_sha, role):
    independent = load("p17_m2_scientific_independent")
    independent.check_contract(contract)
    spec = contract["roles"][role]
    if sys.orig_argv != startup_argv(spec["argv"], contract_sha, contract["runtime"]):
        raise ValueError("ACTUAL_SCIENTIFIC_CONTROLLER_ARGV_CHANGED")
    root = Path(spec["root"])
    helper = load("p17_m2_content_verified_control")
    pending = helper.read_json(root / "quota-pending.json")
    returned = helper.read_json(root / "reservation-return.json")
    if (
        pending.get("role") != role
        or pending.get("scientific_contract_sha256") != contract_sha
        or pending.get("FULL_seconds") != spec["FULL_seconds"]
        or pending.get("status") != "CONSUMED_BEFORE_CONTROLLER_INTERPRETER"
        or returned.get("pending_sha256") != sha(canonical(pending))
        or returned.get("argv")
        != resolved_argv(contract["shared_helpers"][role]["reservation"]["argv"], contract_sha)
        or returned.get("complete") is not True
        or returned.get("exit_code") != 0
        or not pending["began_UTC_seconds"] <= returned["end_seconds"] <= time.time()
        or helper.sha(helper.canonical(pending["publication_readiness"]))
        != returned.get("publication_readiness_sha256")
    ):
        raise ValueError("ACTUAL_PREINTERPRETER_RESERVATION_RETURN_REQUIRED")
    independent.check_shared_helper_return(
        contract, role, "reservation", load_shared_helper_evidence(contract, role, "reservation")
    )
    cases = []
    spans = []
    began = time.monotonic()
    try:
        if role == "resource-preflight":
            controls = public_preflight(root / "controls")
            cases = [row["record"] for row in controls["cases"]]
            spans = controls["case_spans"]
        else:
            independent.check_b_preflight(
                contract, load_role_evidence(contract, "resource-preflight")
            )
            if role == "scientific-auditor":
                independent.check_scientific_role(
                    contract,
                    "scientific-producer",
                    load_role_evidence(contract, "scientific-producer"),
                )
            start = spec["inner_starts"][0]
            resource, _ = native_helpers()
            case_start = time.time()
            cases = [
                resource.invoke(
                    root / "native",
                    start["name"],
                    resolved_argv(start["argv"], contract_sha),
                    timeout=start["timeout_seconds"],
                )
            ]
            spans = [
                {
                    "name": start["name"],
                    "start_seconds": case_start,
                    "end_seconds": time.time(),
                    "group_gone": cases[0]["cleanup"]["group_gone"],
                }
            ]
            if cases[0]["exit_code"] != 0 or cases[0]["cleanup"]["group_gone"] is not True:
                raise RuntimeError(
                    "SCIENTIFIC_CHILD_STOP: inspect retained complete child record/log"
                )
    except BaseException as error:
        failure = retain_controller_failure(
            root, role, contract_sha, spec, error, began=began, cases=cases
        )
        error.scientific_controller_failure = failure
        raise
    summary = {
        "schema": "topolab.v2.m2-scientific-native-exit-binding.v1",
        "status": "PENDING_POSTEXIT",
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": contract_sha,
        "role": role,
        "case_records_sha256": sha(canonical(cases)),
        "case_spans_sha256": sha(canonical(spans)),
        "own_future_exit": "UNKNOWN_PENDING_ACTUAL_OUTER_RETURN",
    }
    helper.put(root / "case-spans.json", spans)
    helper.put(root / "controller-summary.json", summary)
    return summary


def retain_controller_failure(root, role, contract_sha, spec, error, *, began, cases):
    """Keep the primary failure even when context reads or filing also fail."""
    helper = load("p17_m2_content_verified_control")
    elapsed = time.monotonic() - began
    packet = {
        "schema": "topolab.v2.m2-scientific-controller-failure.v1",
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": contract_sha,
        "role": role,
        "status": "STOP_NO_RETRY",
        "error_type": type(error).__name__,
        "reason": str(error),
        "registered_role": spec,
        "completed_native_cases": cases,
        "valid_observed_wall_seconds": elapsed,
        "known_charge_lower_bound_seconds": max(spec["FULL_seconds"], elapsed + 10),
        "actual_own_return": "UNKNOWN_PENDING_ACTUAL_OUTER_TOOL_RETURN",
        "retained_context": [],
        "secondary_errors": [],
    }
    for relative in (
        "payload-failure.json",
        "rows/producer-failure.json",
        "rows/producer-stop-context.json",
        "rows/auditor-failure.json",
    ):
        try:
            raw = load("p17_m2_source_acquisition_independent").native._software_bytes(
                root / relative
            )
            packet["retained_context"].append(
                {"path": relative, "raw_sha256": sha(raw), "packet": json.loads(raw)}
            )
        except FileNotFoundError:
            pass
        except BaseException as secondary:
            packet["secondary_errors"].append(
                {"stage": relative, "type": type(secondary).__name__, "reason": str(secondary)}
            )
    try:
        if hasattr(error, "public_preflight_context"):
            packet["retained_context"].append({"public_preflight": error.public_preflight_context})
        helper.put(root / "controller-failure.json", packet)
    except BaseException as secondary:
        packet["secondary_errors"].append(
            {
                "stage": "controller failure filing",
                "type": type(secondary).__name__,
                "reason": str(secondary),
            }
        )
    # The complete object reaches the externally observed log even after filing fails.
    sys.stderr.buffer.write(canonical(packet))
    sys.stderr.buffer.flush()
    return packet


def reserve_role(contract, contract_sha, role):
    """Prerequisites first; exclusive quota exists before the outer run starts."""
    independent = load("p17_m2_scientific_independent")
    independent.check_contract(contract)
    control = load("p17_m2_source_acquisition_control")
    # Fresh publication work returned before native entry and is billed separately.
    readiness = checked_publication_metadata(contract, contract_sha, role)
    certificate = acquisition_certificate(contract)
    if certificate._binding["version_id"] != contract["acquisition"]["version_id"]:
        raise ValueError("ACCEPTED_ACQUISITION_VERSION_CHANGED")
    if role != "resource-preflight":
        independent.check_b_preflight(contract, load_role_evidence(contract, "resource-preflight"))
    if role == "scientific-auditor":
        independent.check_scientific_role(
            contract, "scientific-producer", load_role_evidence(contract, "scientific-producer")
        )
        check_reader_ack_return(contract, "scientific-producer")
    spec = contract["roles"][role]
    if sys.orig_argv != startup_argv(spec["reserve_argv"], contract_sha, contract["runtime"]):
        raise ValueError("ACTUAL_RESERVATION_ARGV_CHANGED")
    root = Path(spec["root"])
    if role != "resource-preflight":
        parent = control.base().nofollow_directory(root.parent)
        try:
            capacity = os.fstatvfs(parent)
            if capacity.f_bavail * capacity.f_frsize < contract["scientific_available_bytes_min"]:
                raise ValueError("SCIENTIFIC_DISK_CAPACITY_UNAVAILABLE")
        finally:
            os.close(parent)
    private_mkdir(root)
    record = {
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": contract_sha,
        "role": role,
        "FULL_seconds": spec["FULL_seconds"],
        "status": "CONSUMED_BEFORE_CONTROLLER_INTERPRETER",
        "began_UTC_seconds": time.time(),
        "publication_readiness": readiness,
        "own_future_exit": "UNKNOWN_PENDING_ACTUAL_RESERVATION_TOOL_RETURN",
    }
    load("p17_m2_content_verified_control").put(root / "quota-pending.json", record)
    return record


def public_preflight(output):
    """Actual NEW public starts, including observed nonzero/timeout cleanup.

    Invoke this controller directly, never inside another invoke: the three
    declared child groups run sequentially and cannot become hidden descendants.
    The controller's own eventual native exit must be checked by its caller.
    """
    output = Path(os.path.abspath(output))
    allowed = ("/private/tmp/", "/tmp/", "/private/var/folders/")
    if not str(output).startswith(allowed) or REPO in output.parents:
        raise ValueError("NEW_PUBLIC_PREFLIGHT_ROOT_REQUIRED")
    private_mkdir(output)
    resource, independent = native_helpers()
    # Retain the locked venv entry: resolving its symlink discards pyvenv.cfg
    # discovery and launches a different import environment under -I.
    python = str(Path(sys.executable).absolute())
    program = str(Path(__file__).resolve())
    specifications = [
        (
            "success",
            [
                python,
                "-I",
                str(REPO / "scripts/p17_m2_homotopy.py"),
                "--public-fixture",
                "tiny-prefix",
                "--output",
                str(output / "public-success.json"),
            ],
            30,
        ),
        ("exit-seven", [python, "-I", program, "public-fixture", "--case", "exit-seven"], 10),
        ("timeout", [python, "-I", program, "public-fixture", "--case", "timeout"], 1),
    ]
    cases, spans = [], []
    try:
        for name, argv, maximum in specifications:
            record = None
            case_start = time.time()
            record = resource.invoke(output, name, argv, timeout=maximum)
            spans.append(
                {
                    "name": name,
                    "start_seconds": case_start,
                    "end_seconds": time.time(),
                    "group_gone": record["cleanup"]["group_gone"],
                }
            )
            directory = output / name
            profiles = {
                row["profile"]: (directory / row["profile"]).read_bytes()
                for row in record["helpers"]
                if row.get("profile")
            }
            checked = independent.audit_resource_record(
                record,
                profile=(directory / "command.time").read_bytes(),
                log=(directory / "command.log").read_bytes(),
                helper_profiles=profiles,
                expected_role=name,
                expected_argv=argv,
                platform=sys.platform,
                require_success=name == "success",
            )
            if (
                record["cleanup"]["group_gone"] is not True
                or (name == "exit-seven" and record["exit_code"] != 7)
                or (
                    name == "timeout"
                    and not (record["exit_code"] != 0 and record["cleanup"]["signals"])
                )
            ):
                raise ValueError("PUBLIC_PREFLIGHT_CONTROL_FAILED")
            cases.append(
                {
                    "name": name,
                    "argv": argv,
                    "timeout_seconds": maximum,
                    "record": record,
                    "independent_audit": checked,
                }
            )
    except BaseException as error:
        packet = {
            "status": "STOP_NO_RETRY",
            "error_type": type(error).__name__,
            "reason": str(error),
            "completed_cases": cases,
            "case_spans": spans,
            "current_case": name,
            "current_argv": argv,
            "current_record": record,
            "outer_return": "UNKNOWN_PENDING_ACTUAL_OUTER_RETURN",
            "secondary_errors": [],
        }
        try:
            load("p17_m2_content_verified_control").put(
                output / "public-preflight-failure.json", packet
            )
        except BaseException as secondary:
            packet["secondary_errors"].append(
                {
                    "stage": "preflight failure filing",
                    "type": type(secondary).__name__,
                    "reason": str(secondary),
                }
            )
        error.public_preflight_context = packet
        raise
    proof = {
        "status": "PUBLIC_PREFLIGHT_CONTROLS_OBSERVED",
        "old_input_reads": 0,
        "cases": cases,
        "case_spans": spans,
        "scientific_execution_identity": IDENTITY,
        "resource_admission": "PENDING_COMPLETE_CONTROLLER_BINDER_VERIFIER_EXITS",
        "helper_identity": resource.VERSION,
        "helper_scope_disclosure": "existing native recording algorithm; actual new starts",
        "controller_own_future_exit": "UNKNOWN_PENDING_ACTUAL_OUTER_RETURN",
    }
    resource.atomic_new(output / "public-preflight.json", proof)
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=(
            "public-preflight",
            "public-fixture",
            "publication-check",
            "reserve",
            "run",
            "payload",
            "bind-exit",
            "ack",
            "observe-native",
        ),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case", choices=("exit-seven", "timeout"))
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--contract-sha")
    parser.add_argument(
        "--role", choices=("resource-preflight", "scientific-producer", "scientific-auditor")
    )
    parser.add_argument(
        "--label",
        choices=("controller", "binder", "verifier", "final-observer", "reservation", "reader-ack"),
    )
    parser.add_argument("--observed-exit", type=int)
    args = parser.parse_args()
    os.umask(0o077)
    if args.mode in (
        "publication-check",
        "reserve",
        "run",
        "payload",
        "bind-exit",
        "ack",
        "observe-native",
    ):
        if (
            not args.contract
            or not args.contract_sha
            or not args.role
            or args.case is not None
            or sys.flags.isolated != 1
            or Path.cwd() != REPO
        ):
            parser.error("frozen isolated scientific role required")
        contract = read_contract(
            args.contract,
            args.contract_sha,
            payload_role=args.role if args.mode == "payload" else None,
            publication_check=args.mode == "publication-check",
        )
        spec = contract["roles"][args.role]
        if args.mode == "observe-native":
            result = observe_native(contract, args.contract_sha, args.role, args.label)
            sys.stdout.buffer.write(canonical(result))
            sys.stdout.buffer.flush()
            return 0 if result["status"] == "COMPLETED_WITH_NATIVE_RETURN" else 1
        if args.mode == "publication-check":
            result = publication_metadata(contract, args.contract_sha, args.role)
        elif args.mode == "reserve":
            result = reserve_role(contract, args.contract_sha, args.role)
        elif args.mode == "run":
            if args.output != Path(spec["root"]):
                parser.error("literal registered scientific output required")
            result = run_registered_role(contract, args.contract_sha, args.role)
        elif args.mode == "payload":
            if sys.orig_argv != startup_argv(
                spec["inner_starts"][0]["argv"], args.contract_sha, contract["runtime"]
            ):
                parser.error("actual scientific payload argv differs")
            result = scientific_payload(contract, args.contract_sha, args.role)
        elif args.mode == "bind-exit":
            result = bind_exit(
                Path(spec["root"]), args.label, args.role, args.contract_sha, args.observed_exit
            )
        else:
            independent = load("p17_m2_scientific_independent")
            evidence = load_role_evidence(contract, args.role)
            checked = independent.check_scientific_role(contract, args.role, evidence)
            admission = independent.check_b_preflight(
                contract, load_role_evidence(contract, "resource-preflight")
            )
            certificate = independent.grant_scientific_input(
                acquisition_certificate(contract), contract, args.role, admission
            )
            payload = load("p17_m2_input_export").parse(evidence["cases"][0]["log"])
            result = independent.acknowledge_scientific_reader(
                certificate, payload["reader_pending"], checked
            )
        sys.stdout.buffer.write(canonical(result))
        return 0
    if args.mode == "public-fixture":
        if args.output is not None or args.case is None:
            parser.error("literal public control required")
        print(json.dumps({"new_public_control": args.case}), flush=True)
        if args.case == "exit-seven":
            return 7
        time.sleep(5)
        return 0
    if args.output is None or args.case is not None:
        parser.error("new public output required")
    result = public_preflight(args.output)
    raw = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    print(json.dumps({"status": result["status"], "proof_sha256": hashlib.sha256(raw).hexdigest()}))
    return 0


if __name__ == "__main__":
    try:
        status = main()
    except BaseException as error:
        # Early reserve/bind/load failures precede scientific payload closeout.
        # Preserve NEW read observations in the actual native command log too.
        if hasattr(error, "native_log_facts"):
            sys.stderr.buffer.write(
                canonical(
                    {
                        "status": "STOP_NEW_NATIVE_LOG_READ",
                        "type": type(error).__name__,
                        "reason": str(error),
                        "native_log_facts": error.native_log_facts,
                        "own_future_exit": "UNKNOWN_PENDING_ACTUAL_EXTERNAL_TOOL_RETURN",
                    }
                )
            )
            sys.stderr.buffer.flush()
        raise
    raise SystemExit(status)
