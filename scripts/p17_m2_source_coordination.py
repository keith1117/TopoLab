"""A bounded Foundation read claim around the existing strict source primitive.

Only control records cross the helper pipes. Source bytes are read and parsed by
the original Python reader while its exact-file claim remains held.
"""

import hashlib
import json
import os
import select
import signal
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import unquote, urlsplit

IDENTITY = "topolab.source-read.foundation-coordination.v1"
CONFIG_KEYS = {"identity", "binary", "sha256", "request_timeout_seconds",
               "release_timeout_seconds", "reading_options", "source_swift_sha256",
               "compiler_sha256"}


def need(ok, reason):
    if not ok:
        raise ValueError("SOURCE_COORDINATION: " + reason)


def physical(value):
    return {key: getattr(value, key) for key in
            ("st_dev", "st_ino", "st_size", "st_mtime_ns")}


def open_regular(path):
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parent.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = child
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
    finally:
        os.close(parent)
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(descriptor)
        raise ValueError("SOURCE_COORDINATION: ordinary single-link file required")
    return descriptor, info


class Coordinator:
    def __init__(self, config, source):
        need(set(config) == CONFIG_KEYS and config["identity"] == IDENTITY
             and config["reading_options"] == 0, "frozen content-capable configuration required")
        for key in ("sha256", "source_swift_sha256", "compiler_sha256"):
            need(isinstance(config[key], str) and len(config[key]) == 64
                 and set(config[key]) <= set("0123456789abcdef"), "helper provenance missing")
        need(0 < config["request_timeout_seconds"] <= 10
             and 0 < config["release_timeout_seconds"] <= 5, "bounded helper deadlines required")
        self.config = config
        self.source = Path(source)
        need(self.source.is_absolute() and ".." not in self.source.parts,
             "literal absolute source root required")
        self.records = []

    def _helper(self):
        binary = Path(self.config["binary"])
        need(binary.is_absolute() and ".." not in binary.parts, "literal helper required")
        descriptor, before = open_regular(binary)
        with os.fdopen(descriptor, "rb") as stream:
            raw = stream.read(4 * 1024**2 + 1)
            after = os.fstat(stream.fileno())
        need(len(raw) <= 4 * 1024**2 and len(raw) == before.st_size
             and physical(before) == physical(after) == physical(binary.lstat())
             and before.st_mode & 0o111 and not before.st_mode & 0o022
             and hashlib.sha256(raw).hexdigest() == self.config["sha256"],
             "exact private executable helper hash/identity required")
        return str(binary)

    @staticmethod
    def _wait(process, row, timeout):
        deadline = time.monotonic() + timeout
        while process.returncode is None:
            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                process.returncode = os.waitstatus_to_exitcode(status)
                row['helper_native_exit'] = {
                    'pid': pid, 'exit_code': process.returncode,
                    'statistics_source': 'os.wait4', 'platform': sys.platform,
                    'rss_unit': 'bytes' if sys.platform == 'darwin' else 'KiB*1024',
                    'native': {'rss_bytes': int(usage.ru_maxrss) *
                               (1024 if sys.platform == 'linux' else 1),
                               'user_seconds': usage.ru_utime,
                               'system_seconds': usage.ru_stime},
                    'wait_finished_ns': time.time_ns(),
                }
                break
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(process.args, timeout)
            time.sleep(0.002)

    @staticmethod
    def _line(process, timeout, pending):
        deadline = time.monotonic() + timeout
        while b"\n" not in pending:
            remaining = deadline - time.monotonic()
            need(remaining > 0 and select.select([process.stdout], [], [], remaining)[0],
                 "helper control timeout")
            chunk = os.read(process.stdout.fileno(), 4096)
            need(chunk and len(pending) + len(chunk) <= 65536, "helper control EOF/size")
            pending += chunk
        line, pending = pending.split(b"\n", 1)
        return json.loads(line), pending

    @contextmanager
    def claim(self, relative):
        need(isinstance(relative, str) and relative and not relative.startswith("/")
             and os.path.normpath(relative) == relative and ".." not in Path(relative).parts,
             "literal relative source required")
        path = self.source / relative
        row = {"path": relative, "requested_url": path.as_uri(), "accessor_url": None,
               "strategy_identity": IDENTITY, "helper_sha256": self.config["sha256"],
               "helper_pid": None, "helper_exit_code": None, "namespace_before": None,
               "ready": None, "reader_start_ns": None, "reader_end_ns": None,
               "release_requested_ns": None, "release": None, "failure": None,
               "secondary_errors": [], "helper_native_exit": None}
        self.records.append(row)
        process = None
        descriptor = None
        primary = None
        pending = b""
        try:
            descriptor, info = open_regular(path)
            row["namespace_before"] = physical(info)
            binary = self._helper()
            process = subprocess.Popen([binary, str(path)], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
            row["helper_pid"] = process.pid
            ready, pending = self._line(process, self.config["request_timeout_seconds"], pending)
            row["ready"] = ready
            need(ready.get("event") == "accessor_entered" and ready.get("pid") == process.pid
                 and ready.get("requested_url") == ready.get("accessor_url") == path.as_uri()
                 and type(ready.get("entered_ns")) is int,
                 "exact live accessor URL/owned helper required")
            row["accessor_url"] = ready["accessor_url"]
            row["reader_start_ns"] = time.time_ns()
            yield Path(unquote(urlsplit(ready["accessor_url"]).path))
        except BaseException as error:
            primary = error
            row["failure"] = {"type": type(error).__name__, "reason": str(error)}
            error.source_coordination_failure = row
            raise
        finally:
            row["reader_end_ns"] = time.time_ns()
            cleanup_error = None
            if process is not None:
                try:
                    if row["ready"] is not None:
                        row["release_requested_ns"] = time.time_ns()
                        process.stdin.write(b"DONE\n")
                        process.stdin.flush()
                        release, pending = self._line(
                            process, self.config["release_timeout_seconds"], pending)
                        row["release"] = release
                        need(release.get("event") == "accessor_returned"
                             and release.get("pid") == process.pid
                             and type(release.get("left_ns")) is int
                             and row["release_requested_ns"] <= release["left_ns"]
                             and not pending, "complete claim release after reader required")
                    self._wait(process, row, self.config["release_timeout_seconds"])
                    _, stderr = process.communicate(timeout=self.config["release_timeout_seconds"])
                    need(process.returncode == 0 and len(stderr) <= 65536,
                         "helper exit/stderr boundary")
                except BaseException as error:
                    cleanup_error = error
                    row["secondary_errors"].append(
                        {"type": type(error).__name__, "reason": str(error)})
                    if process.returncode is None:
                        try:
                            os.kill(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    try:
                        self._wait(process, row, self.config["release_timeout_seconds"])
                        _, stderr = process.communicate(
                            timeout=self.config["release_timeout_seconds"])
                        row["helper_stderr"] = stderr.decode("utf-8", errors="replace")
                    except BaseException as final_error:
                        row["secondary_errors"].append(
                            {"type": type(final_error).__name__, "reason": str(final_error)})
                finally:
                    row["helper_exit_code"] = process.returncode
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except BaseException as error:
                    row['secondary_errors'].append(
                        {'type': type(error).__name__, 'reason': str(error)})
                    cleanup_error = cleanup_error or error
            if cleanup_error is not None and primary is None:
                row["failure"] = {"type": type(cleanup_error).__name__,
                                  "reason": str(cleanup_error)}
                cleanup_error.source_coordination_failure = row
                raise cleanup_error
            if primary is None and cleanup_error is None:
                row.pop("failure")
                row.pop("secondary_errors")
