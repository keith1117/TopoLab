"""Finite private local content writer; receives buffers, never original paths.

This preparation interface grants no source access or formal activation. Existing
R transcription supplies admitted buffers; independent comparison supplies truth.
"""

import hashlib
import importlib.util
import json
import os
import re
import stat
from pathlib import Path

CONTENT_SHA = "f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad"
IDENTITY = "topolab.v2.p17-m2-local-input-version.v1"
MIB = 1024 * 1024


def need(ok, reason):
    if not ok:
        raise ValueError("LOCAL_STOP: " + reason)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(info):
    return {key: getattr(info, key) for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")}


def members_for(registry):
    models = [(row["family"], row["seed"]) for row in registry["models"]]
    ids = [row["case_id"] for row in registry["labels"]]
    need(len(models) == 12 and set(models) == {
        (family, seed) for family in ("C", "P", "W", "S") for seed in (17, 29, 43)},
        "exact checkpoint whitelist")
    need(len(ids) == 528 and ids == sorted(set(ids))
         and all(re.fullmatch(r"tlcase-v1-[0-9a-f]{64}", case_id) for case_id in ids),
         "exact label whitelist")
    result = {"source_registry.json": ("registry", 8 * MIB, 8 * MIB),
              "models.json": ("models", MIB, MIB),
              "uniform-scalars.json": ("uniform-scalars", 65536, 65536)}
    result.update({f"checkpoints/{family}-{seed}.safetensors": (
        "checkpoint", MIB, 12 * MIB) for family, seed in models})
    for case_id in ids:
        result[f"nn/producer/{case_id}.json"] = ("nn-producer", 128 * 1024, 32 * MIB)
        result[f"nn/audit/{case_id}.json"] = ("nn-audit", 2 * MIB, 256 * MIB)
    return result


def open_directory(path):
    need(path.is_absolute() and path == Path(os.path.normpath(path)), "literal absolute directory")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def exporter():
    path = Path(__file__).with_name("p17_m2_input_export.py")
    spec = importlib.util.spec_from_file_location("local_transcription", path)
    need(spec is not None and spec.loader is not None, "existing field transcriber")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LocalContent:
    """One new generation with a finite member set and recorded local identities."""

    def __init__(self, root, registry, contract_sha256):
        self.root = Path(root).absolute()
        need(not self.root.is_relative_to(Path("/Users/keith1117/Documents/TopoLab-data")),
             "local content cannot stat/write original namespace")
        need(re.fullmatch(r"[0-9a-f]{64}", contract_sha256) is not None, "contract SHA")
        self.contract_sha256 = contract_sha256
        self.allowed = members_for(registry)
        self.registry_raw = canonical(registry)
        self.rows, self.totals = {}, {}
        self.finished = False
        self.failed = False
        parent = open_directory(self.root.parent)
        try:
            os.mkdir(self.root.name, 0o700, dir_fd=parent)
            info = os.stat(self.root.name, dir_fd=parent, follow_symlinks=False)
            need(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o700
                 and info.st_uid == os.geteuid(), "private new content directory")
            self.root_identity = (info.st_dev, info.st_ino)
            os.fsync(parent)
        finally:
            os.close(parent)

    def write(self, relative, raw):
        need(not self.finished, "content already sealed")
        need(not self.failed, "content STOP_NO_RETRY")
        try:
            return self._write(relative, raw)
        except Exception:
            self.failed = True
            raise

    def _write(self, relative, raw):
        need(relative in self.allowed, "member outside whitelist")
        need(relative not in self.rows, "duplicate member")
        kind, each, total = self.allowed[relative]
        need(type(raw) is bytes and 0 < len(raw) <= each
             and self.totals.get(kind, 0) + len(raw) <= total, "content byte cap")
        need(relative != "source_registry.json" or raw == self.registry_raw,
             "registry bytes differ")
        fd = open_directory(self.root)
        try:
            info = os.fstat(fd)
            need((info.st_dev, info.st_ino) == self.root_identity, "content root replaced")
            need(stat.S_IMODE(info.st_mode) == 0o700 and info.st_uid == os.geteuid(),
                 "private content root")
            parts = Path(relative).parts
            for part in parts[:-1]:
                try:
                    os.mkdir(part, 0o700, dir_fd=fd)
                    os.fsync(fd)
                except FileExistsError:
                    pass
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                info = os.fstat(child)
                if stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.geteuid():
                    os.close(child)
                    raise ValueError("LOCAL_STOP: private content subdirectory")
                os.close(fd)
                fd = child
            leaf = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                           0o600, dir_fd=fd)
            with os.fdopen(leaf, "wb") as stream:
                written = stream.write(raw)
                need(written == len(raw), "incomplete content write")
                stream.flush()
                os.fsync(stream.fileno())
                info = os.fstat(stream.fileno())
                need(stat.S_IMODE(info.st_mode) == 0o600 and info.st_uid == os.geteuid()
                     and info.st_size == len(raw), "private complete content file")
                observed = identity(info)
            os.fsync(fd)
            closing_parent = open_directory(self.root.joinpath(*parts[:-1]))
            try:
                closing = identity(os.stat(parts[-1], dir_fd=closing_parent, follow_symlinks=False))
                need(closing == observed, "new content replaced during write")
            finally:
                os.close(closing_parent)
        finally:
            os.close(fd)
        self.rows[relative] = {
            "path": relative, "byte_size": len(raw), "sha256": digest(raw),
            **{key: observed for key in ("declared", "before", "after", "closing")}}
        self.totals[kind] = self.totals.get(kind, 0) + len(raw)

    def finish(self):
        need(not self.failed and not self.finished, "content STOP_NO_RETRY or already sealed")
        try:
            need(set(self.rows) == set(self.allowed), "incomplete content whitelist")
            self.inventory()
            reader = exporter().Reader(self.root, execution_identity=IDENTITY,
                                       source_identity_checks=True)
            for path in sorted(self.allowed):
                row = self.rows[path]
                kind, each, total = self.allowed[path]
                reader.read(path, each, expected=row["sha256"], size=row["byte_size"],
                            group=kind, total=total)
                need(reader.source_observations[-1] == row, "recorded local identity changed")
            self.inventory()
            producer = sorted(path for path, (kind, *_) in self.allowed.items()
                              if kind in ("checkpoint", "models", "nn-producer"))
            auditor = sorted(set(producer) | {path for path, (kind, *_) in self.allowed.items()
                                             if kind == "nn-audit"})
            manifest = {
                "schema": "topolab.v2.m2-local-input-content.v1",
                "frozen_contract_sha256": self.contract_sha256,
                "content_scope_sha256": CONTENT_SHA,
                "source_registry_sha256": digest(self.registry_raw),
                "members": [{key: self.rows[path][key] for key in ("path", "byte_size", "sha256")}
                            | {"type": self.allowed[path][0]} for path in sorted(self.rows)],
                "role_views": {"scientific-producer": producer, "scientific-auditor": auditor,
                               "reference-compatibility": ["uniform-scalars.json"]},
            }
            need(len(canonical(manifest)) <= 2 * MIB, "content manifest byte cap")
            self.finished = True
            return {"manifest": manifest, "version_id": digest(canonical(manifest)),
                    "local_identity_rows": [self.rows[path] for path in sorted(self.rows)]}
        except Exception:
            self.failed = True
            raise

    def inventory(self):
        """Bounded inventory of NEW content only; discoveries never extend scope."""
        directories = {"checkpoints", "nn", "nn/producer", "nn/audit"}
        found, entries = set(), 0

        def walk(fd, prefix=""):
            nonlocal entries
            with os.scandir(fd) as scan:
                for item in scan:
                    entries += 1
                    need(entries <= 4096, "new namespace entry cap")
                    relative = prefix + item.name
                    info = item.stat(follow_symlinks=False)
                    need(info.st_uid == os.geteuid(), "new member ownership")
                    if stat.S_ISDIR(info.st_mode):
                        need(relative in directories and stat.S_IMODE(info.st_mode) == 0o700,
                             "unlisted or nonprivate content directory")
                        child = os.open(item.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                        dir_fd=fd)
                        try:
                            walk(child, relative + "/")
                        finally:
                            os.close(child)
                    else:
                        need(stat.S_ISREG(info.st_mode) and relative in self.allowed
                             and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1,
                             "unlisted/nonprivate/linked member")
                        found.add(relative)
        fd = open_directory(self.root)
        try:
            info = os.fstat(fd)
            need((info.st_dev, info.st_ino) == self.root_identity, "content root replaced")
            need(stat.S_IMODE(info.st_mode) == 0o700 and info.st_uid == os.geteuid(),
                 "private content root")
            walk(fd)
        finally:
            os.close(fd)
        need(found == set(self.allowed), "new inventory differs from whitelist")
