"""Separately authored, stdlib-only R source/field comparator; never runs science.

The launcher must bind owner authority, clean merged source, precheck, role caps
and observed exits. The explicit CLI acknowledgement is not that admission.
This module imports no exporter, TopoLab loader, numerical code or shared oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import stat
import struct
import sys
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

MIB = 1024 * 1024
AUTHORIZED_DATA_ROOT = Path("/Users/keith1117/Documents/TopoLab-data")
AUTHORIZED_R_ROOT = AUTHORIZED_DATA_ROOT / "p17-m2-input-export-preparation-v3"
AUTHORIZED_STABLE_ROOT = AUTHORIZED_DATA_ROOT / "p17-m2-source-stable-export-v1"
# v2 names below identify the reused wire/evidence algorithm, not old authority.
EXECUTION_V2 = "topolab.v2.p17-m2-input-export-preparation.v3"
EXECUTION_F = "topolab.v2.p17-m2-input-failure-diagnostic-repair.v1"
EXECUTION_STABLE = "topolab.v2.p17-m2-source-stable-export.v1"
CONTENT_CONTRACT_SHA256 = "f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad"
CLOCK_V2 = "functions.exec.Date.now.UTC-seconds"
FULL_V2 = {
    "independent-public-check": 120,
    "exporter-r0": 120,
    "independent-r0": 120,
    "exporter-r1": 780,
    "independent-r1": 660,
    "shared-closeout": 60,
}
FULL_STABLE = {
    "independent-public-check": 300,
    "exporter-r0": 300,
    "independent-r0": 300,
    "exporter-r1": 1200,
    "independent-r1": 1200,
    "shared-closeout": 300,
}
SOURCE_NAMESPACES = {
    "b3-v1-fits", "b4-5-weighted-terminal/fit", "b3-v1-data",
    "b4-30-z-reflection-repair-v2",
}
REGISTRY_SCHEMA = "topolab.v2.m2-input-source-registry.v1"
CASE = re.compile(r"tlcase-v1-[0-9a-f]{64}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
B3_DATA_HASH = "b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26"
CATALOG_HASH = "441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c"
STORED_FIELDS = (
    "volume",
    "tensor_dtype",
    "tensor_axis_order",
    "tensor_shape",
    "design_density",
    "physical_density",
    "sensitivity_weight",
    "compliance",
    "physical_volume_fraction",
    "iterations",
    "terminal_density_change",
    "stop_reason",
)
RECENT_FIELDS = (
    "iteration",
    "compliance",
    "volume_fraction",
    "density_change",
    "design_density",
    "physical_density",
)
TENSOR_SHAPES = {
    "network.0.weight": [16, 13, 3, 3, 3],
    "network.0.bias": [16],
    "network.2.weight": [16, 16, 3, 3, 3],
    "network.2.bias": [16],
    "network.4.weight": [16, 16, 3, 3, 3],
    "network.4.bias": [16],
    "network.6.weight": [16, 16, 3, 3, 3],
    "network.6.bias": [16],
    "network.8.weight": [1, 16, 1, 1, 1],
    "network.8.bias": [1],
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(obj: Any) -> bytes:
    return (
        json.dumps(obj, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def parse(raw: bytes, *, canonical_required: bool = False) -> Any:
    def bad_constant(_: str) -> None:
        raise ValueError("nonfinite JSON constant")

    obj = json.loads(raw, object_pairs_hook=_pairs, parse_constant=bad_constant)
    stack = [(obj, 0)]
    while stack:
        value, depth = stack.pop()
        require(depth <= 64, "JSON depth exceeds 64")
        if isinstance(value, dict):
            stack.extend((v, depth + 1) for v in value.values())
        elif isinstance(value, list):
            stack.extend((v, depth + 1) for v in value)
        elif type(value) is float:
            require(math.isfinite(value), "nonfinite JSON number")
    if canonical_required:
        require(canonical(obj) == raw, "source metadata is not canonical JSON")
    return obj


def compare_words(expected: Any, actual: Any, pointer: str = "") -> int:
    """Compare all fields, including signed zero; return compared scalar count."""
    require(type(expected) is type(actual), f"field type differs at {pointer}")
    if type(expected) is float:
        require(
            struct.pack("<d", expected) == struct.pack("<d", actual),
            f"IEEE binary64 field differs at {pointer}",
        )
        return 1
    if isinstance(expected, dict):
        require(expected.keys() == actual.keys(), f"field set differs at {pointer}")
        return sum(
            compare_words(value, actual[key], pointer + "/" + key)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        require(len(expected) == len(actual), f"array length differs at {pointer}")
        return sum(
            compare_words(left, right, pointer + "/" + str(i))
            for i, (left, right) in enumerate(zip(expected, actual, strict=True))
        )
    require(expected == actual, f"field differs at {pointer}")
    return 1


def source_identity(info: os.stat_result) -> dict[str, int]:
    return {key: getattr(info, key) for key in
            ("st_dev", "st_ino", "st_size", "st_mtime_ns")}


def nofollow_parent(target: Path) -> int:
    """Resolve a literal absolute parent afresh from /, without symlinks."""
    directory = os.open(target.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in target.parts[1:-1]:
            next_directory = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
            )
            os.close(directory)
            directory = next_directory
        return directory
    except BaseException:
        os.close(directory)
        raise


class OnceReader:
    """Bounded descriptor reads; each literal source is opened at most once."""

    def __init__(
        self, root: Path, max_files: int, total_bytes: int, *,
        source_identity_checks: bool = False, journal: Path | None = None,
    ):
        self.root = Path(os.path.abspath(root))
        self.max_files = max_files
        self.total_bytes = total_bytes
        self.table: list[dict[str, Any]] = []
        self.seen: set[str] = set()
        self.used = 0
        self.source_identity_checks = source_identity_checks
        self.journal = journal
        self.observations: list[dict[str, Any]] = []
        self.failures: list[dict[str, Any]] = []
        self.source_facts: dict[str, dict[str, Any]] = {}

    def read(
        self,
        relative: str,
        maximum: int,
        *,
        sha256: str | None = None,
        byte_size: int | None = None,
    ) -> bytes:
        facts: dict[str, Any] = {
            "schema": "topolab.v2.m2-input-read-failure.v1",
            "execution_identity": EXECUTION_STABLE if self.source_identity_checks else EXECUTION_F,
            "attempt_ordinal": len(self.seen) + 1, "path": relative,
            "stage": "path_validation", "declared": None, "before": None,
            "after": None, "closing": None, "returned_bytes": None, "changed_fields": [],
        }
        if isinstance(relative, str):
            self.source_facts[relative] = facts
        try:
            return self._read(relative, maximum, sha256=sha256, byte_size=byte_size, facts=facts)
        except (ValueError, OSError, TypeError) as error:
            self.record_failure(facts, error)
            raise

    @contextmanager
    def validation(self, relative, stage="source_validation"):
        """Attach a downstream rejection to facts from the original single read."""
        facts = self.source_facts[relative]
        facts["stage"] = stage
        try:
            yield
        except Exception as error:
            self.record_failure(facts, error)
            raise

    def record_failure(self, facts, error):
        if facts.get("status") == "STOP_NO_RETRY":
            return
        facts.update(status="STOP_NO_RETRY", exception_type=type(error).__name__,
                     primary_reason=str(error), unavailable="UNKNOWN_NOT_ZERO")
        identities = [facts[key] for key in ("declared", "before", "after", "closing")]
        for left, right in zip(identities, identities[1:], strict=False):
            if left is not None and right is not None:
                changed = [key for key in left if left[key] != right[key]]
                if changed:
                    facts["changed_fields"] = changed
                    break
        self.failures.append(facts)
        if self.journal is not None:
            try:
                with self.journal.open("ab") as stream:
                    stream.write(canonical(facts))
                    stream.flush()
                    os.fsync(stream.fileno())
            except OSError as secondary:
                facts["recording_error"] = f"{type(secondary).__name__}: {secondary}"
                error.add_note(facts["recording_error"])

    def _read(
        self, relative: str, maximum: int, *, sha256: str | None,
        byte_size: int | None, facts: dict[str, Any],
    ) -> bytes:
        require(isinstance(relative, str), "unsafe literal path")
        pieces = PurePosixPath(relative)
        require(
            isinstance(relative, str)
            and relative == pieces.as_posix()
            and not pieces.is_absolute()
            and ".." not in pieces.parts
            and relative not in ("", "."),
            "unsafe literal path",
        )
        require(relative not in self.seen, "repeat source read refused")
        require(len(self.seen) < self.max_files, "source file count cap")
        self.seen.add(relative)
        target = self.root / relative
        facts["stage"] = "declared_stat"
        current = Path(target.anchor)
        for component in target.parts[1:]:
            current /= component
            info = current.lstat()
            require(not stat.S_ISLNK(info.st_mode), "source symlink refused")
        require(stat.S_ISREG(info.st_mode), "source is not regular")
        facts["declared"] = source_identity(info)
        require(
            0 < info.st_size <= maximum and self.used + info.st_size <= self.total_bytes,
            "source byte cap",
        )
        if byte_size is not None:
            require(type(byte_size) is int and info.st_size == byte_size, "declared bytes differ")
        # Resolve every ancestor through a no-follow descriptor, so a parent
        # replaced after lstat cannot redirect the actual file open.
        facts["stage"] = "open_nofollow"
        directory = nofollow_parent(target)
        fd = None
        try:
            fd = os.open(target.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
            facts["stage"] = "before_read_identity"
            opened = os.fstat(fd)
            facts["before"] = source_identity(opened)
            require(
                (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
                == (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns),
                "source changed before descriptor read",
            )
            chunks = []
            remaining = maximum + 1
            facts["stage"] = "bounded_read"
            facts["returned_bytes"] = 0
            while remaining:
                chunk = os.read(fd, min(1024 * 1024, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                facts["returned_bytes"] += len(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
            facts["stage"] = "after_read_identity"
            after = os.fstat(fd)
            facts["after"] = source_identity(after)
            require(
                (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
                == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
                "source changed during descriptor read",
            )
            facts["stage"] = "read_size_consistency"
            require(len(raw) == opened.st_size, "source read length differs from descriptor size")
            if self.source_identity_checks:
                facts["stage"] = "closing_path_identity"
                closing_parent = nofollow_parent(target)
                try:
                    closing = os.stat(target.name, dir_fd=closing_parent, follow_symlinks=False)
                finally:
                    os.close(closing_parent)
                facts["closing"] = source_identity(closing)
                require(stat.S_ISREG(closing.st_mode)
                        and source_identity(after) == source_identity(closing),
                        "source changed at closing literal path")
        finally:
            if fd is not None:
                os.close(fd)
            os.close(directory)
        facts["stage"] = "read_size_hash_caps"
        actual_sha = digest(raw)
        self.used += len(raw)
        facts["source"] = {"path": relative, "byte_size": len(raw), "sha256": actual_sha}
        self.table.append(facts["source"])
        if self.source_identity_checks:
            self.observations.append(dict(self.table[-1], **{
                key: facts[key] for key in ("declared", "before", "after", "closing")
            }))
        require(sha256 is None or actual_sha == sha256, "source SHA differs")
        return raw

    def packet(self, relative, maximum, **kwargs):
        raw = self.read(relative, maximum, **kwargs)
        with self.validation(relative, "json_parse"):
            packet = parse(raw)
        with self.validation(relative, "canonical_json"):
            require(canonical(packet) == raw, "source metadata is not canonical JSON")
        return packet


def reference(path: str, raw: bytes) -> dict[str, Any]:
    return {"path": path, "byte_size": len(raw), "sha256": digest(raw)}


def fit_reference(root: str, ref: dict[str, Any], kind: str) -> dict[str, Any]:
    require(
        SHA.fullmatch(ref["sha256"]) is not None
        and type(ref["byte_size"]) is int
        and ref["byte_size"] > 0,
        "invalid artifact reference",
    )
    suffix = "safetensors" if kind == "checkpoint" else "json"
    expected = f"artifacts/{kind}/{ref['sha256']}.{suffix}"
    require(
        ref.get("kind", kind) == kind and ref.get("path", expected) == expected,
        "content-addressed reference path differs",
    )
    return {"path": root + "/" + expected, "byte_size": ref["byte_size"], "sha256": ref["sha256"]}


def closed_units(
    reader: OnceReader,
    folder: str,
    context_sha: str,
    units: list[str],
    progress: dict[str, Any],
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    with reader.validation(folder + "/progress.json"):
        require(
            progress["version"] == "topolab.b4.progress.v1"
            and progress["context_sha256"] == context_sha
            and progress["units_sha256"] == digest(canonical(units))
            and progress["completed"] == len(units)
            and progress["attempted"] == len(units)
            and progress["pending"] is None
            and progress["active_at"] is None
            and progress["resource_failed"] is False
            and progress["integrity_failed"] is False,
            "source journal is not complete and closed",
        )
    with reader.validation(folder + "/summary.json"):
        for key in ("context_sha256", "completed", "attempted", "head_sha256"):
            require(summary[key] == progress[key], "source summary/journal binding differs")
    head = "0" * 64
    payloads = []
    for ordinal, unit in enumerate(units):
        path = f"{folder}/units/{ordinal:04d}.json"
        record = reader.packet(path, 32768)
        with reader.validation(path):
            require(
                record["version"] == "topolab.b4.unit.v1"
                and record["context_sha256"] == context_sha
                and record["unit"] == unit
                and record["previous_sha256"] == head,
                "source unit chain differs",
            )
            head = reader.table[-1]["sha256"]
            payloads.append(record["payload"])
    with reader.validation(folder + "/progress.json"):
        require(head == progress["head_sha256"], "source unit head differs")
    return payloads


def build_registry(reader: OnceReader, contract: dict[str, Any]) -> dict[str, Any]:
    """Derive the finite registry independently; no payload stat or open here."""
    old = {}
    for spec in contract["R0"]["literal_bootstrap_files"]:
        old[spec["relative_path"]] = reader.packet(
            spec["relative_path"], spec["max_bytes"], sha256=spec["expected_sha256"])
    with reader.validation("b3-v1-fits/b3_training.json"):
        fits = old["b3-v1-fits/b3_training.json"]
        context = fits["context"]
        require(
            fits["index_version"] == "topolab.b3.training-index.v1"
            and fits["context_sha256"] == digest(canonical(context)),
            "B3 fitting context differs",
        )
        data = context["data_index"]
        require(
            context["data_index_sha256"] == B3_DATA_HASH
            and digest(canonical(data)) == B3_DATA_HASH,
            "embedded B3 index binding differs",
        )
        manifest = data["manifest"]
        manifest_sha = digest(canonical(manifest))
        require(
            manifest_sha == data["manifest_sha256"]
            and digest(canonical(manifest["catalog"])) == CATALOG_HASH,
            "embedded manifest/catalog differs",
        )
        train = [entry for entry in manifest["catalog"]["entries"] if entry["role"] == "train"]
        require(len(train) == 528, "train set is not complete528")
        outcomes = {outcome["entry"]["case"]["case_id"]: outcome for outcome in data["entries"]}
        labels = []
        for entry in sorted(train, key=lambda e: e["case"]["case_id"]):
            case_id = entry["case"]["case_id"]
            require(CASE.fullmatch(case_id) is not None, "invalid train case identity")
            outcome = outcomes[case_id]
            compare_words(entry, outcome["entry"])
            require(outcome["status"] == "succeeded", "original train outcome is not successful")
            artifact = outcome["artifact"]
            access = artifact["access"]
            compare_words(entry, access["entry"])
            require(
                access["kind"] == "label"
                and artifact["manifest_sha256"] == manifest_sha
                and artifact["source_revision"] == manifest["context"]["source_revision"],
                "label source identity differs",
            )
            relative = f"artifacts/label/{case_id}/{access['artifact_sha256']}.json"
            require(
                artifact["relative_path"] == relative
                and SHA.fullmatch(access["artifact_sha256"]) is not None,
                "label artifact path differs",
            )
            labels.append(
                {
                    "case_id": case_id,
                    "entry": entry,
                    "manifest_sha256": manifest_sha,
                    "context_sha256": digest(canonical(manifest["context"])),
                    "source_revision": artifact["source_revision"],
                    "artifact": {
                        "path": "b3-v1-data/" + relative,
                        "byte_size": artifact["byte_size"],
                        "sha256": access["artifact_sha256"],
                    },
                }
            )
        require(
            len({row["case_id"] for row in labels}) == 528
            and Counter(
                tuple(row["entry"]["case"]["problem"]["mesh"]["element_counts"]) for row in labels
            )
            == {(12, 6, 3): 432, (24, 12, 6): 96},
            "train uniqueness/scale membership differs",
        )
    wroot = "b4-5-weighted-terminal/fit"
    weighted = closed_units(
        reader,
        wroot,
        contract["R0"]["W_context_sha256"],
        ["W/17", "W/29", "W/43"],
        old[wroot + "/progress.json"],
        old[wroot + "/summary.json"],
    )
    refroot = "b4-30-z-reflection-repair-v2/sentinel/reference"
    context_path = "b4-30-z-reflection-repair-v2/context.json"
    context_sha = next(
        spec["expected_sha256"]
        for spec in contract["R0"]["literal_bootstrap_files"]
        if spec["relative_path"] == context_path
    )
    units = contract["scalars"]["case_ids"]
    uniform_refs = closed_units(
        reader,
        refroot,
        context_sha,
        units,
        old[refroot + "/progress.json"],
        old[refroot + "/summary.json"],
    )
    scalars = []
    for ordinal, (case_id, ref) in enumerate(zip(units, uniform_refs, strict=True)):
        path = f"{refroot}/units/{ordinal:04d}.json"
        with reader.validation(path):
            scalars.append({
                "case_id": case_id,
                "context_sha256": context_sha,
                "unit": next(row for row in reader.table if row["path"] == path),
                "packet": fit_reference(refroot, ref, "outcome"),
            })
    models = []
    for spec in contract["checkpoints"]["fixed_rows"]:
        family, seed = spec["family"], spec["seed"]
        source_path = (f"{wroot}/units/{[17, 29, 43].index(seed):04d}.json"
                       if family == "W" else "b3-v1-fits/b3_training.json")
        with reader.validation(source_path):
            if family == "W":
                selection_ref = fit_reference(
                    wroot, weighted[[17, 29, 43].index(seed)], "selection")
                source_context = contract["R0"]["W_context_sha256"]
            else:
                matched = [o for o in fits["outcomes"]
                           if (o["recipe"], o["seed"]) == (family, seed)]
                require(len(matched) == 1, "selected model outcome is missing/duplicated")
                selection_ref = fit_reference("b3-v1-fits", matched[0]["selection"], "selection")
                source_context = fits["context_sha256"]
        selection = reader.packet(
            selection_ref["path"], 262144,
            sha256=selection_ref["sha256"], byte_size=selection_ref["byte_size"],
        )
        with reader.validation(selection_ref["path"]):
            if family == "W":
                require(
                    selection["version"] == "topolab.b4_5.selection.v1"
                    and selection["objective"] == "topolab.b4_5.weighted-terminal.v1",
                    "W wrapper/objective differs",
                )
                history = selection["history_schema"]
                checkpoint = fit_reference(wroot, selection["checkpoint"], "checkpoint")
                require(
                    history["checkpoint"]["sha256"] == checkpoint["sha256"]
                    and history["checkpoint"]["byte_size"] == checkpoint["byte_size"],
                    "W inner/outer checkpoint differs",
                )
            else:
                history = selection
                checkpoint = fit_reference("b3-v1-fits", selection["checkpoint"], "checkpoint")
            require(
                history["selection_version"] == "topolab.b3.selection.v1"
                and history["context_sha256"] == source_context
                and history["recipe"] == spec["selection_wrapper_recipe"]
                and history["seed"] == seed
                and history["selected_epoch"] == spec["selected_epoch"]
                and 0 < len(history["history"]) <= 200,
                "fixed model selection differs",
            )
            require(0 < checkpoint["byte_size"] <= MIB, "checkpoint declared bytes exceed cap")
        models.append(
            {
                "family": family,
                "seed": seed,
                "epoch": spec["selected_epoch"],
                "context_sha256": source_context,
                "selection": selection_ref,
                "checkpoint": checkpoint,
            }
        )
    require(len(reader.table) == 40, "R0 metadata count differs")
    require(
        sum(row["artifact"]["byte_size"] for row in labels) <= 768 * MIB
        and all(0 < row["artifact"]["byte_size"] <= 64 * MIB for row in labels),
        "declared label byte cap",
    )
    require(
        sum(row["packet"]["byte_size"] for row in scalars) <= 72 * MIB
        and all(0 < row["packet"]["byte_size"] <= 4 * MIB for row in scalars),
        "declared uniform packet byte cap",
    )
    return {
        "schema": REGISTRY_SCHEMA,
        "metadata": sorted(reader.table, key=lambda row: row["path"]),
        "models": models,
        "labels": labels,
        "scalars": scalars,
    }


def vector_sha(vector: Any, width: int, count: int, *, exact_f32: bool = False) -> str:
    require(isinstance(vector, list) and len(vector) == count, "source vector dimension differs")
    result = hashlib.sha256()
    for value in vector:
        require(type(value) in (int, float) and math.isfinite(value), "invalid vector number")
        word = struct.pack("<f" if width == 32 else "<d", value)
        if exact_f32:
            require(
                struct.pack("<d", struct.unpack("<f", word)[0]) == struct.pack("<d", value),
                "stored vector is not actual exact float32",
            )
        result.update(word)
    return result.hexdigest()


def label_views(
    source: dict[str, Any], row: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Select only contract fields; no filter, solve or complete-history analysis."""
    require(
        source["kind"] == "label" and source["label_version"] == "topolab.b3.label.v1",
        "original label version differs",
    )
    compare_words(row["entry"], source["entry"])
    require(
        source["entry"]["role"] == "train"
        and source["initialization"] == "projected_float32_uniform"
        and source["manifest_sha256"] == row["manifest_sha256"]
        and digest(canonical(source["context"])) == row["context_sha256"]
        and source["context"]["source_revision"] == row["source_revision"],
        "original label source binding differs",
    )
    stored, result = source["stored"], source["result"]
    compare_words(source["entry"]["case"], stored["case"])
    nx, ny, nz = source["entry"]["case"]["problem"]["mesh"]["element_counts"]
    require((nx, ny, nz) in ((12, 6, 3), (24, 12, 6)), "label scale differs")
    count = nx * ny * nz
    require(
        stored["tensor_dtype"] == "float32"
        and stored["tensor_axis_order"] == "channel,z,y,x"
        and stored["tensor_shape"] == [1, nz, ny, nx],
        "stored tensor identity differs",
    )
    history = result["history"]
    require(
        isinstance(history, list)
        and 0 < len(history) <= 360
        and stored["iterations"] == len(history)
        and stored["stop_reason"] in ("design_max", "physical_plateau")
        and (stored["stop_reason"] != "physical_plateau" or len(history) >= 11),
        "stored termination/window fields differ",
    )
    membership = {key: value for key, value in source["entry"].items() if key != "case"}
    binding = dict(
        row["artifact"],
        context_sha256=row["context_sha256"],
        manifest_sha256=row["manifest_sha256"],
    )
    common = {
        "case": source["entry"]["case"],
        "membership": membership,
        "initialization": source["initialization"],
        "source": binding,
    }
    production_stored = {
        key: stored[key]
        for key in ("tensor_dtype", "tensor_axis_order", "tensor_shape", "design_density")
    }
    bits = {
        "/stored/design_density": vector_sha(stored["design_density"], 32, count, exact_f32=True)
    }
    producer = dict(
        common,
        schema="topolab.v2.m2-nn-producer-view.v1",
        stored=production_stored,
        bit_digests=bits.copy(),
    )
    for name in ("physical_density", "sensitivity_weight"):
        bits["/stored/" + name] = vector_sha(stored[name], 32, count, exact_f32=True)
    for name in ("design_density", "physical_density"):
        bits["/result/" + name] = vector_sha(result[name], 64, count)
    recent = []
    for index in range(max(0, len(history) - 11), len(history)):
        state = history[index]
        require(state["iteration"] == index + 1, "recent state ordinal differs")
        recent.append({key: state[key] for key in RECENT_FIELDS})
        for name in ("design_density", "physical_density"):
            bits[f"/result/history/{index}/{name}"] = vector_sha(state[name], 64, count)
    terminal = {
        key: result[key]
        for key in ("design_density", "physical_density", "compliance", "converged")
    }
    require(type(terminal["converged"]) is bool, "terminal convergence type differs")
    return producer, dict(
        common,
        schema="topolab.v2.m2-nn-audit-view.v1",
        stored={key: stored[key] for key in STORED_FIELDS},
        terminal=terminal,
        total_updates=len(history),
        recent=recent,
        bit_digests=bits,
    )


def scalar_view(packet: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    outcome = packet["outcome"]
    attempt = outcome["attempt"]
    require(
        packet["version"] == "topolab.b4_30.z-reflection-repair.v2"
        and packet["case_id"] == row["case_id"]
        and packet["policy"] == "uniform"
        and packet["context_sha256"] == row["context_sha256"]
        and outcome["method"] == "uniform"
        and outcome["seed"] is None
        and outcome["route"] == "baseline"
        and outcome["fallback"] is None
        and attempt["succeeded"] is True
        and attempt["failure_code"] is None
        and attempt["failure_type"] is None,
        "uniform source attempt differs",
    )
    value = attempt["metrics"]["final_compliance"]
    require(
        type(value) in (float, int) and math.isfinite(value) and value > 0,
        "uniform compliance is invalid",
    )
    compare_words(value, attempt["state"]["result"]["compliance"])
    return {
        "case_id": row["case_id"],
        "compliance": value,
        "compliance_bits_sha256": digest(struct.pack("<d", value)),
        "initialization": {"method": "uniform", "seed": None, "route": "baseline"},
        "solver_identity": {
            "context_sha256": row["context_sha256"],
            "packet_version": packet["version"],
        },
        "source": dict(
            row["packet"],
            json_pointer="/outcome/attempt/metrics/final_compliance",
            unit=row["unit"],
        ),
    }


def check_safetensors(raw: bytes, model: dict[str, Any]) -> None:
    require(8 < len(raw) <= MIB, "Safetensors file byte cap")
    header_size = int.from_bytes(raw[:8], "little")
    require(2 < header_size <= 65536 and 8 + header_size < len(raw), "Safetensors header length")
    header = parse(raw[8 : 8 + header_size])
    require(set(header) == {"__metadata__", *TENSOR_SHAPES}, "Safetensors tensor keys differ")
    if model["family"] == "W":
        metadata = {
            "version": "topolab.b4_5.checkpoint.v1",
            "context_sha256": model["context_sha256"],
            "seed": model["seed"],
            "epoch": model["epoch"],
            "objective": "topolab.b4_5.weighted-terminal.v1",
        }
    else:
        metadata = {
            "checkpoint_version": "topolab.b3.checkpoint.v1",
            "context_sha256": model["context_sha256"],
            "recipe": model["family"],
            "seed": model["seed"],
            "selected_epoch": model["epoch"],
        }
    require(
        header["__metadata__"] == {"topolab": canonical(metadata).decode("ascii")},
        "Safetensors original provenance metadata differs",
    )
    ranges = []
    for name, shape in TENSOR_SHAPES.items():
        tensor = header[name]
        require(
            set(tensor) == {"dtype", "shape", "data_offsets"}
            and tensor["dtype"] == "F32"
            and tensor["shape"] == shape,
            "Safetensors dtype/shape differs",
        )
        start, end = tensor["data_offsets"]
        require(
            type(start) is int
            and type(end) is int
            and 0 <= start < end
            and end - start == 4 * math.prod(shape),
            "Safetensors data range differs",
        )
        ranges.append((start, end))
    expected_start = 0
    for start, end in sorted(ranges):
        require(start == expected_start, "Safetensors gap/overlap")
        expected_start = end
    require(expected_start == 105732 == len(raw) - 8 - header_size, "Safetensors body size differs")
    require(
        all(math.isfinite(v) for (v,) in struct.iter_unpack("<f", raw[8 + header_size :])),
        "Safetensors nonfinite float32",
    )


def native_profile(raw: bytes, platform: str) -> dict[str, Any]:
    """Independently parse supplied new profile bytes with explicit native units."""
    lines = [line.split() for line in raw.decode("ascii").splitlines()]
    if platform == "darwin":
        clocks = [p for p in lines if len(p) == 6 and p[1::2] == ["real", "user", "sys"]]
        peaks = [p for p in lines if p[1:] == ["maximum", "resident", "set", "size"]]
        require(len(clocks) == len(peaks) == 1, "Darwin native profile incomplete")
        wall, user, system = (float(clocks[0][i]) for i in (0, 2, 4))
        rss = int(peaks[0][0])
    elif platform == "linux":
        clocks = [p for p in lines if len(p) == 5 and p[0] == "TOPOLAB_NATIVE"]
        require(len(clocks) == 1, "GNU native profile incomplete")
        wall, user, system = (float(clocks[0][i]) for i in (1, 2, 3))
        rss = int(clocks[0][4]) * 1024
    else:
        raise ValueError("native profile platform unregistered")
    require(
        all(math.isfinite(v) and v >= 0 for v in (wall, user, system)) and rss > 0,
        "native profile values invalid",
    )
    return {"wall_seconds": wall, "user_seconds": user, "system_seconds": system, "rss_bytes": rss}


def _nonnegative(value: Any, *, integer: bool = False, positive: bool = False) -> float:
    require(
        type(value) is int if integer else type(value) in (int, float),
        "resource numeric type differs",
    )
    require(
        math.isfinite(value) and (value > 0 if positive else value >= 0),
        "resource numeric domain differs",
    )
    return value


def _timer_peak(value: dict[str, Any], expected_pid: int, platform: str,
                *, expected_exit: int = 0) -> int:
    _nonnegative(expected_pid, integer=True, positive=True)
    require(
        value["statistics_source"] == "os.wait4"
        and value["wall_source"] == "controller_monotonic_observed"
        and type(value["exit_code"]) is int and value["exit_code"] == expected_exit
        and value["pid"] == expected_pid
        and value["rss_unit"] == ("bytes" if platform == "darwin" else "KiB*1024"),
        "timer native exit binding differs",
    )
    for key in ("wall_seconds", "user_seconds", "system_seconds"):
        _nonnegative(value["native"][key])
    rss = value["native"]["rss_bytes"]
    _nonnegative(rss, integer=True, positive=True)
    return rss


def stable_cleanup_checked(cleanup: dict[str, Any], expected_exit: int) -> None:
    """Require complete new cleanup facts, preserving initial false observations."""
    require(isinstance(cleanup, dict) and cleanup.get("group_gone") is True
            and cleanup.get("final_group_gone") is True
            and type(expected_exit) is int and cleanup.get("leader_exit") == expected_exit
            and cleanup.get("observation_limit_seconds") == 5
            and cleanup.get("observation_limit_exceeded") is False,
            "new cleanup final exit/group/observation incomplete")
    elapsed = _nonnegative(cleanup["post_signal_observation_seconds"])
    require(elapsed <= 5, "new cleanup observation exceeds5s")
    rows = cleanup["observations"]
    require(isinstance(rows, list) and rows and isinstance(cleanup.get("signals"), list)
            and all(isinstance(sig, str) for sig in cleanup["signals"]),
            "new cleanup observations/signals missing")
    previous = 0.0
    for row in rows:
        require(isinstance(row, dict) and type(row.get("group_gone")) is bool
                and (row.get("leader_exit") is None or type(row["leader_exit"]) is int),
                "new cleanup observation UNKNOWN")
        offset = _nonnegative(row["elapsed_seconds"])
        require(offset >= previous, "new cleanup observation order differs")
        previous = offset
    require(cleanup.get("initial_group_gone") == rows[0]["group_gone"]
            and cleanup["final_group_gone"] == rows[-1]["group_gone"]
            and rows[-1]["leader_exit"] == expected_exit,
            "new cleanup initial/final facts differ")


def audit_native_record(
    record: dict[str, Any],
    *,
    profile: bytes,
    log: bytes,
    helper_profiles: dict[str, bytes],
    expected_role: str,
    expected_argv: list[str],
    platform: str,
    failure_recording: bool = False,
) -> dict[str, Any]:
    """Reconcile only explicit NEW receipts; read no path and trust no PASS.

    The outer timer/supervisor peaks and their observed exits remain caller work.
    This is native RSS/exit empirical bookkeeping, never B or a lifetime theorem.
    """
    require(
        record["schema"] == "topolab.v2.m2-native-rss-exit-assurance.v1"
        and record["status"] == "PENDING_POSTEXIT"
        and record["role"] == expected_role
        and record["argv"] == expected_argv
        and record["platform"] == platform
        and record["software_only"] is True
        and record["scientific_resource_admission"] == "NOT_RUN"
        and record["controller_complete_exit"] == "UNKNOWN_PENDING_OUTER_PROFILE",
        "resource identity/status differs",
    )
    require(
        type(record["exit_code"]) is int
        and (record["exit_code"] == 0 or failure_recording)
        and record["software_result"] == (
            "PUBLIC_COMMAND_EXIT_OBSERVED" if record["exit_code"] == 0 else "FAIL_PUBLIC_COMMAND"
        )
        and record["cleanup"]["group_gone"] is True
        and record["cleanup"]["leader_exit"] == record["exit_code"],
        "role child exit incomplete",
    )
    require(
        record["ps_rss_unit"] == "KiB*1024"
        and record["native_rss_unit"] == ("bytes" if platform == "darwin" else "KiB*1024")
        and record["profile_sha256"] == digest(profile)
        and record["log_sha256"] == digest(log),
        "native units/profile/log binding differs",
    )
    measured = native_profile(profile, platform)
    compare_words(measured, record["native"])
    limit = _nonnegative(record["limit_bytes"], integer=True, positive=True)
    require(limit <= 4294967296, "RSS ceiling exceeds retained 4GiB")
    elapsed = _nonnegative(record["observed_outer_wall_seconds"])
    timeout = _nonnegative(record["timeout_seconds"], positive=True)
    interval = _nonnegative(record["target_sample_interval_seconds"], positive=True)
    require(elapsed <= timeout and interval <= 0.5, "role timeout/sample interval cap")
    controller = _nonnegative(record["controller_rss_peak_bytes"], integer=True, positive=True)
    launch_pid = record["pid"]
    _nonnegative(launch_pid, integer=True, positive=True)
    timer_peak = _timer_peak(
        record["timer_native_exit"], launch_pid, platform,
        expected_exit=record["exit_code"] if failure_recording else 0,
    )
    helpers, samples = record["helpers"], record["samples"]
    require(
        isinstance(helpers, list)
        and isinstance(samples, list)
        and 0 < len(helpers) == len(samples),
        "resource sample/helper coverage differs",
    )
    require(
        set(helper_profiles) == {f"sampler-{i}.time" for i in range(len(helpers))},
        "literal helper profile set differs",
    )
    helper_peak = 0
    empirical_peak = measured["rss_bytes"]
    previous = None
    for index, (helper, sample) in enumerate(zip(helpers, samples, strict=True)):
        name = f"sampler-{index}.time"
        require(
            helper["profile"] == name
            and helper["role"] == f"rss-sampler-{index}"
            and helper["profile_sha256"] == digest(helper_profiles[name])
            and helper["exit_code"] == 0
            and helper["problem"] is None
            and helper["cleanup"]["group_gone"] is True
            and helper["cleanup"]["leader_exit"] == 0,
            "helper profile/exit differs",
        )
        helper_native = native_profile(helper_profiles[name], platform)
        compare_words(helper_native, helper["native"])
        helper_timer = _timer_peak(helper["timer_native_exit"], helper["pid"], platform)
        chain_peak = helper_native["rss_bytes"] + helper_timer
        helper_peak = max(helper_peak, chain_peak)
        offset = _nonnegative(sample["offset_seconds"])
        require(offset <= elapsed, "resource sample after command exit")
        if previous is None:
            require(sample["actual_interval_seconds"] is None, "initial interval fabricated")
        else:
            actual_interval = _nonnegative(sample["actual_interval_seconds"])
            require(
                offset >= previous and abs(actual_interval - (offset - previous)) <= 1e-12,
                "actual sample interval arithmetic differs",
            )
        previous = offset
        sample_controller = _nonnegative(
            sample["controller_rss_bytes"], integer=True, positive=True
        )
        require(sample_controller <= controller, "controller sample exceeds high-water")
        process_rows = sample["roles"]
        require(
            len(process_rows) <= 2
            and len({row["pid"] for row in process_rows}) == len(process_rows),
            "unregistered/duplicate process in role",
        )
        group = 0
        for row in process_rows:
            _nonnegative(row["pid"], integer=True, positive=True)
            _nonnegative(row["parent"], integer=True)
            require(
                row["pgid"] == launch_pid
                and (row["pid"] == launch_pid or row["parent"] == launch_pid),
                "observed process escaped role tree",
            )
            group += _nonnegative(row["rss_bytes"], integer=True)
        require(
            sample["group_plus_controller_rss_bytes"] == group + sample_controller,
            "sample RSS addition differs",
        )
        empirical_peak = max(empirical_peak, group + sample_controller + chain_peak)
    overlap = measured["rss_bytes"] + timer_peak + controller + helper_peak
    require(
        record["native_plus_controller_and_sampler_rss_bytes"] == overlap,
        "native overlap addition differs",
    )
    empirical_peak = max(empirical_peak, overlap)
    require(
        empirical_peak <= limit
        and all(item["group_gone"] is True for item in record["escaped_group_cleanup"]),
        "role RSS cap/escaped cleanup incomplete",
    )
    return {
        "record_canonical_sha256": digest(canonical(record)),
        "inner_empirical_RSS_bytes": empirical_peak,
        "inner_observed_wall_seconds": elapsed,
        "native_profile_wall_seconds": measured["wall_seconds"],
        "inner_minimum_charge_seconds": max(elapsed, measured["wall_seconds"]) + 10,
        "outer_timer_supervisor_exits_and_full_role_cost": "CALLER_MUST_CLOSE",
        "B_C_admission": False,
        "a_priori_allocation_guarantee": False,
    }


def audit_v2_resource_components(
    completion: dict[str, Any],
    *,
    inner_evidence: dict[str, Any] | None = None,
    native_profiles: dict[str, bytes] | None = None,
    failure_recording: bool = False,
    execution_identity: str | None = None,
) -> dict[str, Any]:
    """Reconcile raw native evidence; future external exit remains PENDING.

    Preserve available failed-process peaks before rejecting incomplete evidence.
    Callers must never use this resource-only return as successor admission.
    """
    completion_is_object = isinstance(completion, dict)
    stable = execution_identity == EXECUTION_STABLE
    recording = failure_recording or stable
    if not completion_is_object:
        completion = {}
    result: dict[str, Any] = {
        "status": "PENDING_EXTERNAL_EXIT",
        "execution_identity": completion.get("execution_identity"),
        "role": completion.get("role"),
        "plan_sha256": completion.get("plan_sha256"),
        "pending_sha256": completion.get("pending_sha256"),
        "frozen_FULL_seconds": completion.get("frozen_FULL_seconds"),
        "reason": None,
        "RSS_envelope_bytes": None,
        "RSS_components_bytes": {},
        "inner_minimum_charge_seconds": None,
        "actual_component_exit_codes": [],
        "full_role_evidence_accepted": False,
        "evidence_complete": False,
    }
    try:
        require(completion_is_object, "completion must be an object")
        require(execution_identity is None or stable, "unregistered explicit replay identity")
        require(completion["execution_identity"] == (
            EXECUTION_STABLE if stable else EXECUTION_F if failure_recording else EXECUTION_V2),
                "resource completion v2 identity differs")
        peaks: dict[int, int] = {}
        components = completion["resource_components"]
        require(isinstance(components, list) and components, "UNKNOWN_MISSING_OUTER_RSS")
        serializer_seen = False
        profile_names: set[str] = set()
        for item in components:
            pid = item["pid"]
            _nonnegative(pid, integer=True, positive=True)
            kind = item["kind"]
            if kind == "native_profile":
                name = item["profile"]
                require(native_profiles is not None and name in native_profiles,
                        "UNKNOWN_MISSING_NATIVE_PROFILE")
                require(name not in profile_names, "duplicate outer native profile")
                profile_names.add(name)
                raw = native_profiles[name]
                require(item["profile_sha256"] == digest(raw), "outer native profile hash")
                peak = native_profile(raw, item["platform"])["rss_bytes"]
                code = item["actual_exit_code"]
            elif kind == "wait4":
                record = item["record"]
                require(record["statistics_source"] == "os.wait4"
                        and record["wall_source"] == "controller_monotonic_observed"
                        and record["pid"] == pid
                        and record["rss_unit"] == (
                            "bytes" if item["platform"] == "darwin" else "KiB*1024"
                        ), "outer wait4 identity/units differ")
                for name in ("wall_seconds", "user_seconds", "system_seconds"):
                    _nonnegative(record["native"][name])
                peak = _nonnegative(record["native"]["rss_bytes"], integer=True, positive=True)
                code = record["exit_code"]
            else:
                require(kind == "self_high_water", "unregistered outer RSS component")
                require(item["statistics_source"] == "resource.getrusage"
                        and item["rss_unit"] == "bytes"
                        and item["phases"] == ["preflush", "postflush"],
                        "final serializer sample source/units/phases differ")
                samples = item["samples_bytes"]
                require(isinstance(samples, list) and len(samples) == 2,
                        "UNKNOWN_MISSING_SERIALIZER_RSS")
                peak = max(_nonnegative(v, integer=True, positive=True) for v in samples)
                serializer_seen |= pid == completion["final_serializer_pid"]
                code = None  # This process's actual exit belongs to the external event.
            peaks[pid] = max(peaks.get(pid, 0), peak)
            result["RSS_components_bytes"] = {str(k): v for k, v in sorted(peaks.items())}
            if kind != "self_high_water":
                result["actual_component_exit_codes"].append(code)
        require(set(native_profiles or {}) == profile_names, "unregistered outer native profile")
        require(serializer_seen, "UNKNOWN_MISSING_SERIALIZER_RSS")
        inner_peak, minimum = 0, 0.0
        if inner_evidence is not None:
            inner = audit_native_record(**inner_evidence, failure_recording=recording)
            inner_peak = inner["inner_empirical_RSS_bytes"]
            minimum = inner["inner_minimum_charge_seconds"]
            result["inner_record_sha256"] = inner["record_canonical_sha256"]
            result["inner_actual_exit_code"] = inner_evidence["record"]["exit_code"]
            if stable:
                record = inner_evidence["record"]
                stable_cleanup_checked(record["cleanup"], record["exit_code"])
                for sampler in record["helpers"]:
                    stable_cleanup_checked(sampler["cleanup"], sampler["exit_code"])
                stable_cleanup_checked(completion["cleanup"], record["exit_code"])
        else:
            require(completion["role"] == "shared-closeout", "UNKNOWN_MISSING_INNER_EVIDENCE")
        result["RSS_components_bytes"]["independently_reconciled_inner"] = inner_peak
        result["inner_minimum_charge_seconds"] = minimum
        if recording:
            require(completion["role"] in (FULL_STABLE if stable else {"public-fixture": 120})
                    and type(completion["frozen_FULL_seconds"]) is int
                    and completion["frozen_FULL_seconds"] == (
                        FULL_STABLE[completion["role"]] if stable else 120),
                    "immutable recording role/FULL differs")
            kinds = [item["kind"] for item in components]
            require(sorted(kinds) == ["native_profile", "self_high_water", "self_high_water",
                                      "wait4"]
                    and len(peaks) == 4, "UNKNOWN_INCOMPLETE_F_OUTER_INVENTORY")
            require(inner_evidence is not None and next(
                item["pid"] for item in components if item["kind"] == "native_profile"
            ) == inner_evidence["record"]["controller_pid"],
                    "F outer profile/controller identity differs")
        result["RSS_envelope_bytes"] = sum(peaks.values()) + inner_peak
        require(all(type(code) is int and (code == 0 or recording)
                    for code in result["actual_component_exit_codes"]),
                "native/helper actual exit nonzero or missing")
        require(completion["cleanup"]["group_gone"] is True,
                "UNKNOWN_INCOMPLETE_GROUP_CLEANUP")
        require(result["RSS_envelope_bytes"] <= 4294967296, "retained 4GiB RSS cap exceeded")
        result["evidence_complete"] = True
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        result.update(status="STOP_NO_RETRY", reason=f"{type(error).__name__}: {error}")
    return result


def actor_window(record: dict[str, Any], *, stable: bool = False) -> tuple[float, float]:
    """Validate the NEW readiness-triggered window, without opening any path."""
    activation = _nonnegative(record["actor_activation_UTC_seconds"], positive=True)
    require(round(activation * 1000) / 1000 == activation,
            "actor activation must have millisecond resolution")
    window = 4500 if stable else 2700
    require(type(record["actor_window_seconds"]) is int
            and record["actor_window_seconds"] == window,
            "prospective actor window differs")
    deadline = activation + window
    expected = datetime.fromtimestamp(deadline, UTC).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")
    require(record["actor_deadlines_UTC"] == {
        "exporter": expected, "independent": expected,
    }, "actor deadlines must equal the immutable activation plus registered window")
    return activation, deadline


def audit_full_role_v2(
    pending: dict[str, Any],
    completion: dict[str, Any],
    *,
    raw_tool_events: list[dict[str, Any]],
    expected_role: str,
    expected_plan_sha256: str,
    inner_evidence: dict[str, Any] | None = None,
    native_profiles: dict[str, bytes] | None = None,
    failure_recording: bool = False,
    expected_pending_sha256: str | None = None,
    execution_identity: str | None = None,
) -> dict[str, Any]:
    """Independently bind supplied *actual* external events, never a PASS oracle.

    This pure auditor opens no path. The caller supplies the execution tool's raw
    observed start/end/exit events at the finite, adopted observation boundary.
    The last event must follow final serialization; an internal PENDING record
    cannot certify that future exit. Failure preserves available measurements and
    never opens the source-role suffix. Inner evidence is reconciled afresh.
    """
    def evidence_digest(value: Any) -> str | None:
        try:
            return digest(canonical(value))
        except (ValueError, TypeError, OverflowError):
            return None  # Malformed numeric evidence still receives a STOP record.

    original_pending, original_completion = pending, completion
    pending_is_object = isinstance(pending, dict)
    completion_is_object = isinstance(completion, dict)
    pending = pending if pending_is_object else {}
    completion = completion if completion_is_object else {}
    events_are_list = isinstance(raw_tool_events, list)
    raw_tool_events = raw_tool_events if events_are_list else []
    stable = execution_identity == EXECUTION_STABLE
    recording = failure_recording or stable
    identity = EXECUTION_STABLE if stable else EXECUTION_F if failure_recording else EXECUTION_V2
    caps = FULL_STABLE if stable else {"public-fixture": 120} if failure_recording else FULL_V2
    result: dict[str, Any] = {
        "schema": "topolab.v2.m2-source-stable-export-exit.v1" if stable else
                  "topolab.v2.m2-input-failure-exit.v1" if failure_recording
                  else "topolab.v2.m2-input-export-exit.v2",
        "execution_identity": identity,
        "role": expected_role,
        "plan_sha256": expected_plan_sha256,
        "pending_sha256": evidence_digest(original_pending),
        "completion_sha256": evidence_digest(original_completion),
        "frozen_FULL_seconds": caps.get(expected_role),
        "status": "STOP_NO_RETRY",
        "reason": "UNKNOWN_INCOMPLETE_OUTER_EVIDENCE",
        "clock_domain": None,
        "T0": None,
        "T1": None,
        "whole_wall_seconds": None,
        "inner_minimum_charge_seconds": None,
        "RSS_envelope_bytes": None,
        "RSS_components_bytes": {},
        "actual_exit_codes": [event.get("exit_code") if isinstance(event, dict) else None
                              for event in raw_tool_events],
        "raw_tool_event_ids_and_hashes": [
            {"event_id": event.get("event_id") if isinstance(event, dict) else None,
             "sha256": evidence_digest(event)}
            for event in raw_tool_events
        ],
        "cleanup": completion.get("cleanup"),
        "known_cost_lower_bound_seconds": caps.get(expected_role),
        "missing_evidence_cost": "UNKNOWN_NOT_ZERO",
        "source_successor_admitted": False,
        "full_role_evidence_accepted": False,
        "charge_record_sha256": evidence_digest(pending),
        "B_C_admission": False,
        "a_priori_allocation_guarantee": False,
        "evidence_complete": False,
        "domain_status": "STOP",
        "primary_failure": completion.get("primary_failure"),
        "secondary_failures": completion.get("secondary_failures", []),
    }
    resources = audit_v2_resource_components(
        completion, inner_evidence=inner_evidence, native_profiles=native_profiles,
        failure_recording=failure_recording,
        execution_identity=execution_identity,
    )
    for key in ("RSS_envelope_bytes", "RSS_components_bytes", "inner_minimum_charge_seconds"):
        result[key] = resources[key]
    result["resource_evidence"] = resources
    try:
        require(pending_is_object, "pending must be an object")
        require(execution_identity is None or stable, "unregistered explicit replay identity")
        require(expected_role in caps and bool(SHA.fullmatch(expected_plan_sha256)),
                "unregistered v3 role/plan")
        cap = caps[expected_role]
        activation, deadline = actor_window(pending, stable=stable)
        result["actor_activation_UTC_seconds"] = activation
        result["actor_window_seconds"] = 4500 if stable else 2700
        result["actor_deadlines_UTC"] = pending["actor_deadlines_UTC"]
        for record in (pending,):
            require(
                record["execution_identity"] == identity
                and record["role"] == expected_role
                and record["plan_sha256"] == expected_plan_sha256
                and type(record["frozen_FULL_seconds"]) is int
                and record["frozen_FULL_seconds"] == cap,
                "v3 identity/plan/immutable FULL differs",
            )
            require(record["clock_domain"] == CLOCK_V2
                    and record["clock_resolution_seconds"] == 0.001,
                    "unfrozen external clock identity/resolution")
        require(events_are_list and raw_tool_events
                and all(isinstance(event, dict) for event in raw_tool_events),
                "UNKNOWN_MISSING_OR_MALFORMED_ACTUAL_OUTER_EVENT")
        first = raw_tool_events[0]
        result["clock_domain"] = first["clock_domain"]
        result["T0"] = _nonnegative(first["start_seconds"])
        result["T1"] = _nonnegative(raw_tool_events[-1]["end_seconds"])
        whole = result["T1"] - result["T0"]
        require(whole >= 0, "outer clock regression")
        previous_end = result["T0"]
        ids: set[str] = set()
        for event in raw_tool_events:
            start = _nonnegative(event["start_seconds"])
            end = _nonnegative(event["end_seconds"])
            native_wall = _nonnegative(event["wall_seconds"])
            require(
                isinstance(event["event_id"], str) and event["event_id"]
                and event["event_id"] not in ids,
                "duplicate/missing raw event identity",
            )
            ids.add(event["event_id"])
            require(
                isinstance(event["argv"], list) and event["argv"]
                and all(isinstance(word, str) for word in event["argv"])
                and event["clock_domain"] == result["clock_domain"]
                and isinstance(event["clock_domain"], str) and event["clock_domain"]
                and previous_end <= start <= end <= result["T1"]
                and event["clock_domain"] == CLOCK_V2
                and native_wall <= end - start + 0.001,
                "raw event clock/order/argv/native-wall differs",
            )
            previous_end = end
        if "external_argv" in pending:
            require(pending["external_argv"] == [event["argv"] for event in raw_tool_events],
                    "external literal argv differs")
        # Certify the clock interval only after validating the entire raw stream.
        # Actor-window STOP or missing exits/completion cannot erase that cost fact.
        result["whole_wall_seconds"] = whole
        minimum = resources["inner_minimum_charge_seconds"]
        result["known_cost_lower_bound_seconds"] = max(
            cap, math.ceil(whole + 10), math.ceil(minimum) if minimum is not None else 0
        )
        require(activation <= result["T0"] <= result["T1"] <= deadline,
                "actual full role lies outside immutable actor window")
        require(all(event.get("complete") is True and type(event.get("exit_code")) is int
                    for event in raw_tool_events), "UNKNOWN_MISSING_ACTUAL_FINAL_EXIT")
        require(completion_is_object, "completion must be an object")
        require(actor_window(completion, stable=stable) == (activation, deadline),
                "completion actor window differs")
        require(all(completion.get(key) == pending[key] for key in (
            "execution_identity", "role", "plan_sha256", "frozen_FULL_seconds",
            "clock_domain", "clock_resolution_seconds")), "completion identity differs")
        require(completion["status"] == "PENDING_EXTERNAL_EXIT"
                and completion["pending_sha256"] == result["pending_sha256"]
                and (not recording or expected_pending_sha256 == result["pending_sha256"]),
                "internal completion/pending binding differs")
        require(resources["status"] == "PENDING_EXTERNAL_EXIT", resources["reason"])
        require(max(whole + 10, minimum) <= cap, "FAIL_FULL_NAMED_WALL_CHARGE_BINDING")
        result["evidence_complete"] = True
        result["missing_evidence_cost"] = None
        require(all(code == 0 for code in result["actual_exit_codes"]),
                "actual outer/final serializer exit nonzero")
        if recording:
            require(inner_evidence is not None and inner_evidence["record"]["exit_code"] == 0
                    and all(code == 0 for code in resources["actual_component_exit_codes"])
                    and (completion.get("domain_status") == "PASS" if stable else
                         completion.get("domain_status") != "STOP"),
                    "payload/domain failure")
        result.update(status="PASS_R_STABLE_FULL_ROLE" if stable else
                      "PASS_PUBLIC_SOFTWARE" if failure_recording else "PASS_R_V3_FULL_ROLE",
                      reason=None, domain_status="PASS" if stable else "PASS_PUBLIC_SOFTWARE",
                      missing_evidence_cost=None, full_role_evidence_accepted=True)
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        result["reason"] = f"{type(error).__name__}: {error}"
    return result


def audit_full_role_f(
    pending: dict[str, Any], *, completion: dict[str, Any],
    raw_tool_events: list[dict[str, Any]], expected_plan_sha256: str,
    expected_pending_sha256: str, expected_role: str = "public-fixture",
    inner_evidence: dict[str, Any] | None = None,
    native_profiles: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    """Pure F-only public fixture audit: no path access and no R dispatch."""
    return audit_full_role_v2(
        pending, completion, raw_tool_events=raw_tool_events, expected_role=expected_role,
        expected_plan_sha256=expected_plan_sha256, inner_evidence=inner_evidence,
        native_profiles=native_profiles, failure_recording=True,
        expected_pending_sha256=expected_pending_sha256,
    )


def audit_full_role_stable(
    pending: dict[str, Any], *, completion: dict[str, Any],
    raw_tool_events: list[dict[str, Any]], expected_role: str,
    expected_plan_sha256: str, expected_pending_sha256: str,
    inner_evidence: dict[str, Any] | None = None,
    native_profiles: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    """Explicit new identity only; reconcile raw facts, never a producer PASS."""
    return audit_full_role_v2(
        pending, completion, raw_tool_events=raw_tool_events, expected_role=expected_role,
        expected_plan_sha256=expected_plan_sha256,
        expected_pending_sha256=expected_pending_sha256, inner_evidence=inner_evidence,
        native_profiles=native_profiles, execution_identity=EXECUTION_STABLE,
    )


def identity_sidecar(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema": "topolab.v2.m2-source-identity-sidecar.v1",
            "execution_identity": EXECUTION_STABLE, "rows": rows}


def compare_source_identities(
    own: list[dict[str, Any]], producer: dict[str, Any], count: int,
) -> int:
    """Compare actual per-path observations, including equal-SHA replacement."""
    require(set(producer) == {"schema", "execution_identity", "rows"}
            and producer["schema"] == "topolab.v2.m2-source-identity-sidecar.v1"
            and producer["execution_identity"] == EXECUTION_STABLE,
            "source identity sidecar binding differs")
    tables = []
    for rows in (own, producer["rows"]):
        require(isinstance(rows, list) and len(rows) == count, "source identity exact count")
        table = {}
        for row in rows:
            require(set(row) == {"path", "byte_size", "sha256", "declared", "before",
                                 "after", "closing"}, "source identity field set")
            name = row["path"]
            require(isinstance(name, str) and name not in table, "source identity duplicate path")
            pieces = PurePosixPath(name)
            require(not pieces.is_absolute() and ".." not in pieces.parts
                    and name == pieces.as_posix() and name not in ("", "."),
                    "source identity unsafe path")
            require(type(row["byte_size"]) is int and row["byte_size"] > 0
                    and isinstance(row["sha256"], str) and SHA.fullmatch(row["sha256"]) is not None,
                    "source identity bytes/hash")
            for stage in ("declared", "before", "after", "closing"):
                value = row[stage]
                require(isinstance(value, dict) and set(value) == {
                    "st_dev", "st_ino", "st_size", "st_mtime_ns"}
                    and all(type(v) is int and v >= 0 for v in value.values()),
                    "source identity tuple missing")
                require(value == row["before"] and value["st_size"] == row["byte_size"],
                        "source identity changed within read")
            table[name] = row
        tables.append(table)
    return compare_words(tables[0], tables[1])


def accept_source_controls(
    controls: dict[str, Any], activation: float, controlsha: str | None = None,
) -> dict[str, Any]:
    """Independently check attributed control content, never infer actual custody.

    The reviewer still assesses each basis before activation. Passing this
    structural check cannot discover writers or turn unknown coverage into true.
    The controller separately binds the actual frozen lease and absence of release.
    """
    require(isinstance(controls, dict)
            and controls["schema"] == "topolab.v2.m2-writer-quiescence.v1"
            and controls["execution_identity"] == EXECUTION_STABLE,
            "source control identity differs")
    custodian = controls["custodian"]
    require(isinstance(custodian, str) and bool(custodian.strip())
            and controls["no_write_until_release"] is True,
            "source custodian/no-write interval missing")
    namespaces, writers = controls["namespaces"], controls["writers"]
    require(isinstance(namespaces, dict) and set(namespaces) == SOURCE_NAMESPACES
            and isinstance(writers, list), "source control namespace coverage differs")
    registered: set[tuple[str, str]] = set()
    populated: set[str] = set()
    states = {"pause": "PAUSED_ACKNOWLEDGED", "exclude": "EXCLUDED_CUSTODIAN_CONTROL"}
    for writer in writers:
        require(isinstance(writer, dict) and all(isinstance(writer.get(key), str)
                and writer[key].strip() for key in ("name", "namespace", "action", "status",
                                                    "evidence")),
                "source writer attribution incomplete")
        namespace, name = writer["namespace"], writer["name"]
        require(namespace in SOURCE_NAMESPACES and (namespace, name) not in registered
                and writer["action"] in states
                and writer["status"] == states[writer["action"]],
                "source writer pause/exclusion unconfirmed")
        registered.add((namespace, name))
        populated.add(namespace)
    for namespace, coverage in namespaces.items():
        require(isinstance(coverage, dict) and coverage.get("accepted") is True
                and isinstance(coverage.get("basis"), str) and coverage["basis"].strip(),
                "source control coverage UNKNOWN or unattributed")
        if namespace not in populated:
            require(isinstance(coverage.get("no_writer_explanation"), str)
                    and coverage["no_writer_explanation"].strip(),
                    "empty writer scope requires affirmative explanation")
    acknowledgment = controls["acquisition_ack"]
    acquired = _nonnegative(acknowledgment["UTC_seconds"], positive=True)
    require(acknowledgment["by"] == custodian
            and isinstance(acknowledgment.get("basis"), str) and acknowledgment["basis"].strip()
            and _nonnegative(activation, positive=True) <= acquired <= activation + 300,
            "source acquisition acknowledgment outside formal setup")
    actual_sha = digest(canonical(controls))
    require(controlsha is None or controlsha == actual_sha, "source control hash differs")
    return {"status": "PASS_ATTRIBUTED_SOURCE_CONTROL_CONTENT",
            "source_controls_sha256": actual_sha, "custodian": custodian,
            "coverage_basis_requires_independent_judgment": True,
            "outside_writers_discovered_or_excluded_by_software": False}


def stable_source_entry(plan_path: Path | None, plan_sha: str | None, role: str) -> dict[str, Any]:
    require(plan_path is not None
            and Path(os.path.abspath(plan_path)) == AUTHORIZED_STABLE_ROOT / "launch_plan.json"
            and isinstance(plan_sha, str) and SHA.fullmatch(plan_sha) is not None,
            "R-STABLE requires literal frozen plan/hash")
    # -I omits script-directory imports: bind only this committed source path.
    spec = importlib.util.spec_from_file_location(
        "independent_stable_control_gate",
        Path(__file__).resolve().with_name("p17_m2_input_export_control.py"),
    )
    require(spec is not None and spec.loader is not None, "source controller unavailable")
    control = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(control)
    plan = control.validate_stable_source_entry(plan_path, plan_sha, role)
    stable_argv_checked(plan, plan_sha, role)
    accept_source_controls(plan["source_controls"], plan["actor_activation_UTC_seconds"],
                           plan["source_controls_sha256"])
    return plan


def stable_argv_checked(plan: dict[str, Any], plan_sha: str, role: str) -> None:
    """Bind the complete isolated Python invocation, including -I and all paths."""
    expected = [word.replace("<PLAN_SHA256>", plan_sha) for word in plan["roles"][role]["argv"]]
    actual = getattr(sys, "orig_argv", None)
    require(isinstance(actual, list) and actual == expected,
            "actual complete argv differs from frozen source role")


def audit_final_filing(
    record: dict[str, Any], *, actual_exit: int | None, whole_wall_seconds: float,
    expected_argv: list[str], native_evidence: dict[str, Any],
    expected_plan_sha256: str, expected_shared_packet_sha256: str | None = None,
) -> dict[str, Any]:
    """After-return NEW-only helper audit; never a seventh source-role admission.

    expected_argv is the literal child command from the frozen helper table.
    The caller supplies the actual outer tool return and trusted packet hash.
    This pure function opens no path and retains a measured failure's facts.
    """
    result: dict[str, Any] = {
        "schema": "topolab.v2.m2-source-stable-final-filing-exit.v1",
        "execution_identity": EXECUTION_STABLE, "status": "STOP_NO_RETRY",
        "reason": "UNKNOWN_INCOMPLETE_FINAL_FILING", "helper_cap_seconds": 180,
        "actual_exit_code": actual_exit if type(actual_exit) is int else None,
        "whole_wall_seconds": None, "known_cost_lower_bound_seconds": None,
        "RSS_envelope_bytes": None, "RSS_components_bytes": {}, "evidence_complete": False,
        "domain_status": "STOP", "preparation_complete": False, "B_C_admission": False,
        "source_successor_admitted": False,
        "formal_source_role_or_window": False, "missing_evidence_cost": "UNKNOWN_NOT_ZERO",
        "primary_failure": record.get("primary_failure") if isinstance(record, dict) else None,
        "secondary_failures": record.get("secondary_failures", [])
        if isinstance(record, dict) else [],
    }
    try:
        whole = _nonnegative(whole_wall_seconds)
        result["whole_wall_seconds"] = whole
        result["known_cost_lower_bound_seconds"] = math.ceil(whole + 10)
        require(isinstance(record, dict)
                and record["schema"] == "topolab.v2.m2-source-stable-final-filing.v1"
                and record["execution_identity"] == EXECUTION_STABLE,
                "final filing identity/status differs")
        require(isinstance(expected_plan_sha256, str)
                and SHA.fullmatch(expected_plan_sha256) is not None
                and record["plan_sha256"] == expected_plan_sha256,
                "final filing frozen plan differs")
        require(isinstance(expected_argv, list) and expected_argv
                and all(isinstance(word, str) and word for word in expected_argv)
                and record["inner_argv_sha256"] == digest(canonical(expected_argv))
                and native_evidence["expected_role"] == "final-filing"
                and native_evidence["expected_argv"] == expected_argv,
                "final filing literal child argv differs")
        parent_samples = record["controller_RSS_samples_bytes"]
        require(record["controller_RSS_unit"] == "bytes"
                and isinstance(parent_samples, list) and len(parent_samples) == 2,
                "final filing parent RSS samples/units missing")
        parent = max(_nonnegative(value, integer=True, positive=True) for value in parent_samples)
        result["RSS_components_bytes"]["parent_high_water_bytes"] = parent
        inner = audit_native_record(**native_evidence, failure_recording=True)
        native_record = native_evidence["record"]
        result["actual_child_exit_code"] = native_record["exit_code"]
        stable_cleanup_checked(native_record["cleanup"], native_record["exit_code"])
        for sampler in native_record["helpers"]:
            stable_cleanup_checked(sampler["cleanup"], sampler["exit_code"])
        minimum = inner["inner_minimum_charge_seconds"]
        result["inner_minimum_charge_seconds"] = minimum
        result["known_cost_lower_bound_seconds"] = math.ceil(max(whole + 10, minimum))
        result["RSS_components_bytes"]["independent_inner_envelope_bytes"] = (
            inner["inner_empirical_RSS_bytes"]
        )
        # Intentional conservative overlap: the recorded inner controller may
        # be this parent. No shared-page or duplicate-process credit is taken.
        result["RSS_envelope_bytes"] = parent + inner["inner_empirical_RSS_bytes"]
        require(result["RSS_envelope_bytes"] <= 4294967296, "final filing retained4GiB exceeded")
        require(type(actual_exit) is int, "UNKNOWN_ACTUAL_FINAL_HELPER_EXIT")
        require(max(whole + 10, minimum) <= 180, "final filing whole-wall+10 exceeds180")
        require(record["status"] == "PENDING_EXTERNAL_EXIT",
                "final filing internal completion failed")
        result["evidence_complete"] = True
        result["missing_evidence_cost"] = None
        require(actual_exit == 0 and native_record["exit_code"] == 0,
                "final filing actual parent/child exit nonzero")
        filing = parse(native_evidence["log"], canonical_required=True)
        result["filing_result"] = filing
        compare_words(filing, record["filing_result"])
        require(filing["status"] == "PASS_INDEPENDENT_NEW_BACKUP"
                and filing["plan_sha256"] == expected_plan_sha256
                and filing["shared_role_status"] == "PASS_R_STABLE_FULL_ROLE"
                and isinstance(expected_shared_packet_sha256, str)
                and SHA.fullmatch(expected_shared_packet_sha256) is not None
                and filing["shared_packet_sha256"] == expected_shared_packet_sha256,
                "final filing independent backup/trusted shared packet binding differs")
        require(type(filing["member_count"]) is int and 0 < filing["member_count"] <= 20000
                and type(filing["total_bytes"]) is int
                and 0 < filing["total_bytes"] <= 512 * MIB,
                "final filing complete backup counts/bytes differ")
        result["formal_close_UTC_seconds"] = _nonnegative(
            filing["formal_close_UTC_seconds"], positive=True,
        )
        result.update(status="PASS_FINAL_NEW_FILING", domain_status="PASS", reason=None,
                      filing_result=filing, source_successor_admitted=False)
    except (KeyError, TypeError, ValueError, OSError, OverflowError) as error:
        result["reason"] = f"{type(error).__name__}: {error}"
    return result


def audit_new_backup(
    root: Path,
    backup: Path,
    *,
    excluded_prefixes: tuple[str, ...] = (),
    public_fixture: bool = False,
    execution_identity: str | None = None,
) -> dict[str, Any]:
    """Compare only NEW artifacts, including empty logs, by exact bytes and SHA.

    Production roots are literal NEW R-STABLE roots. The explicit public-fixture switch
    cannot open anything below DATA; it exists only for newly created test files.
    Prefix exclusions are literal frozen names, not a glob or alternate source.
    """
    root, backup = Path(os.path.abspath(root)), Path(os.path.abspath(backup))
    result: dict[str, Any] = {
        "status": "STOP_NO_RETRY", "reason": "UNKNOWN_INCOMPLETE_NEW_BACKUP",
        "member_count": 0, "total_bytes": 0, "members": [],
        "old_input_reads": 0, "B_C_admission": False,
        "excluded_prefixes": list(excluded_prefixes),
    }
    try:
        if public_fixture:
            require(not root.is_relative_to(AUTHORIZED_DATA_ROOT)
                    and not backup.is_relative_to(AUTHORIZED_DATA_ROOT),
                    "public fixture cannot open DATA")
        else:
            require(execution_identity == EXECUTION_STABLE
                    and root == AUTHORIZED_STABLE_ROOT
                    and backup == root.with_name(root.name + "-independent-backup"),
                    "backup requires literal NEW v3 closed; explicit R-STABLE roots only")
        require(root != backup and not root.is_relative_to(backup)
                and not backup.is_relative_to(root), "backup roots overlap")
        for prefix in excluded_prefixes:
            require(isinstance(prefix, str) and prefix
                    and not PurePosixPath(prefix).is_absolute()
                    and ".." not in PurePosixPath(prefix).parts,
                    "unsafe backup exclusion")

        def inventory(base: Path) -> set[str]:
            for ancestor in reversed((base, *base.parents)):
                info = ancestor.lstat()
                require(stat.S_ISDIR(info.st_mode), "NEW backup root ancestor/symlink")
            found: set[str] = set()
            total_bytes = 0
            for folder, directories, filenames in os.walk(base, followlinks=False):
                for name in list(directories):
                    path = Path(folder) / name
                    relative = path.relative_to(base).as_posix()
                    if any(relative.startswith(prefix) for prefix in excluded_prefixes):
                        directories.remove(name)
                    else:
                        require(stat.S_ISDIR(path.lstat().st_mode), "NEW backup directory symlink")
                for name in filenames:
                    path = Path(folder) / name
                    relative = path.relative_to(base).as_posix()
                    if any(relative.startswith(prefix) for prefix in excluded_prefixes):
                        continue
                    info = path.lstat()
                    require(stat.S_ISREG(info.st_mode), "NEW backup nonregular/symlink member")
                    require(info.st_size <= 64 * MIB, "NEW backup single-file cap")
                    total_bytes += info.st_size
                    require(total_bytes <= 512 * MIB, "NEW backup inventory byte cap")
                    found.add(relative)
                    require(len(found) <= 20000, "NEW backup member cap")
            return found

        def member(base: Path, relative: str) -> bytes:
            path = base / relative
            before = path.lstat()
            directory = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
            try:
                for piece in path.parts[1:-1]:
                    next_fd = os.open(piece, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                      dir_fd=directory)
                    os.close(directory)
                    directory = next_fd
                fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
            finally:
                os.close(directory)
            try:
                opened = os.fstat(fd)
                require(stat.S_ISREG(opened.st_mode) and opened.st_size <= 64 * MIB,
                        "NEW backup changed/large/nonregular descriptor")
                raw = bytearray()
                while True:
                    chunk = os.read(fd, min(MIB, 64 * MIB + 1 - len(raw)))
                    if not chunk:
                        break
                    raw.extend(chunk)
                    require(len(raw) <= 64 * MIB, "NEW backup grew past file cap")
                after = os.fstat(fd)
            finally:
                os.close(fd)
            def identity(info: os.stat_result) -> tuple[int, int, int, int]:
                return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
            require(identity(before) == identity(opened) == identity(after)
                    == identity(path.lstat()) and len(raw) == before.st_size,
                    "NEW backup member changed during read")
            return bytes(raw)

        source_members, copied_members = inventory(root), inventory(backup)
        require(source_members == copied_members, "NEW backup exact member set differs")
        for relative in sorted(source_members):
            source, copied = member(root, relative), member(backup, relative)
            result["total_bytes"] += len(source)
            require(result["total_bytes"] <= 512 * MIB, "NEW backup total byte cap")
            require(source == copied and digest(source) == digest(copied),
                    "NEW backup member bytes/hash differ")
            result["members"].append(reference(relative, source))
            result["member_count"] += 1
        require(source_members == inventory(root) == inventory(backup),
                "NEW backup inventory changed during comparison")
        result.update(status="PASS_INDEPENDENT_NEW_BACKUP", reason=None)
    except (KeyError, TypeError, ValueError, OSError, OverflowError) as error:
        result["reason"] = f"{type(error).__name__}: {error}"
    return result


def check_registry_shape(registry: dict[str, Any], contract: dict[str, Any]) -> None:
    require(
        set(registry) == {"schema", "metadata", "models", "labels", "scalars"}
        and registry["schema"] == REGISTRY_SCHEMA,
        "source registry schema differs",
    )
    require(
        len(registry["metadata"]) == 40
        and len(registry["models"]) == 12
        and len(registry["labels"]) == 528
        and len(registry["scalars"]) == 18,
        "source registry exact counts differ",
    )
    require(
        [(r["family"], r["seed"], r["epoch"]) for r in registry["models"]]
        == [
            (r["family"], r["seed"], r["selected_epoch"])
            for r in contract["checkpoints"]["fixed_rows"]
        ],
        "registry fixed models differ",
    )
    require(
        [r["case_id"] for r in registry["scalars"]] == contract["scalars"]["case_ids"],
        "registry fixed sentinel differs",
    )
    ids = [r["case_id"] for r in registry["labels"]]
    require(ids == sorted(set(ids)), "registry train identifiers duplicated/unordered")
    require(
        all(r["entry"]["role"] == "train" for r in registry["labels"])
        and Counter(
            tuple(r["entry"]["case"]["problem"]["mesh"]["element_counts"])
            for r in registry["labels"]
        )
        == {(12, 6, 3): 432, (24, 12, 6): 96},
        "registry train population differs",
    )


def audit_exports(
    reader: OnceReader, exports: OnceReader, registry: dict[str, Any]
) -> dict[str, Any]:
    words = 0
    model_bindings = []
    for model in registry["models"]:
        source = model["checkpoint"]
        raw = reader.read(
            source["path"], MIB, sha256=source["sha256"], byte_size=source["byte_size"]
        )
        with reader.validation(source["path"]):
            check_safetensors(raw, model)
        actual = exports.read(f"checkpoints/{model['family']}-{model['seed']}.safetensors", MIB)
        require(actual == raw, "checkpoint copy bytes differ")
        model_bindings.append(
            {key: model[key] for key in ("family", "seed", "epoch", "context_sha256")}
        )
        model_bindings[-1].update(
            source=source,
            selection=model["selection"],
            output={
                "path": f"checkpoints/{model['family']}-{model['seed']}.safetensors",
                "byte_size": len(actual),
                "sha256": digest(actual),
            },
        )
    models_raw = exports.read("models.json", 65536)
    words += compare_words(
        {"schema": "topolab.v2.m2-checkpoint-view.v1", "models": model_bindings},
        parse(models_raw, canonical_required=True),
    )
    labels_bytes = producer_bytes = audit_bytes = 0
    for row in registry["labels"]:
        source = row["artifact"]
        raw = reader.read(
            source["path"], 64 * MIB, sha256=source["sha256"], byte_size=source["byte_size"]
        )
        with reader.validation(source["path"], "json_parse"):
            packet = parse(raw)
        with reader.validation(source["path"]):
            labels_bytes += len(raw)
            require(labels_bytes <= 768 * MIB, "total label bytes exceed cap")
            producer, audit = label_views(packet, row)
        case_id = row["case_id"]
        production_raw = exports.read(f"nn/producer/{case_id}.json", 128 * 1024)
        audit_raw = exports.read(f"nn/audit/{case_id}.json", 2 * MIB)
        producer_bytes += len(production_raw)
        audit_bytes += len(audit_raw)
        require(producer_bytes <= 32 * MIB and audit_bytes <= 256 * MIB, "NN output total cap")
        words += compare_words(producer, parse(production_raw, canonical_required=True))
        words += compare_words(audit, parse(audit_raw, canonical_required=True))
    values = []
    for row in registry["scalars"]:
        source = row["packet"]
        raw = reader.read(
            source["path"], 4 * MIB, sha256=source["sha256"], byte_size=source["byte_size"]
        )
        with reader.validation(source["path"], "json_parse"):
            packet = parse(raw)
        with reader.validation(source["path"]):
            values.append(scalar_view(packet, row))
    scalar_raw = exports.read("uniform-scalars.json", 65536)
    words += compare_words(
        {"schema": "topolab.v2.m2-uniform-scalar-view.v1", "values": values},
        parse(scalar_raw, canonical_required=True),
    )
    return {
        "status": "PASS_R1_ALL_SOURCE_FIELDS",
        "checkpoint_count": len(registry["models"]),
        "NN_cases": len(registry["labels"]),
        "NN_view_files": 2 * len(registry["labels"]),
        "scalar_count": len(values),
        "compared_scalar_fields": words,
        "old_read_table": reader.table,
        "new_read_table": exports.table,
        "FEM_inference_or_complete_history_analysis": False,
        "B_C_authorized_or_run": False,
        "resource_acceptance": "EXTERNAL_EXIT_RECORD_REQUIRED",
    }


def public_label(mesh: tuple[int, int, int], ordinal: int = 1) -> dict[str, Any]:
    """New synthetic serialization fixture, with no solver or historical source."""
    nx, ny, nz = mesh
    count = nx * ny * nz
    x = [0.5] * count
    rho = [0.625] * count  # Deliberately distinct: a transcript is no filter audit.
    case = {
        "case_id": "tlcase-v1-" + f"{ordinal:064x}",
        "problem": {
            "mesh": {"element_counts": list(mesh)},
            "optimization": {"volume_fraction": 0.5, "max_iterations": 360},
        },
    }
    recent = [
        {
            "iteration": i,
            "compliance": float(20 - i),
            "volume_fraction": 0.625,
            "density_change": 0.005,
            "design_density": x,
            "physical_density": rho,
        }
        for i in range(1, 12)
    ]
    context = {"source_revision": "a" * 40, "fixture": "new R public IO only"}
    return {
        "kind": "label",
        "label_version": "topolab.b3.label.v1",
        "context": context,
        "manifest_sha256": "b" * 64,
        "initialization": "projected_float32_uniform",
        "entry": {
            "case": case,
            "role": "train",
            "training_sets": ["expanded"],
            "source_case_id": None,
            "physical_fingerprint": "c" * 64,
        },
        "stored": {
            "case": case,
            "volume": 0.5,
            "tensor_dtype": "float32",
            "tensor_axis_order": "channel,z,y,x",
            "tensor_shape": [1, nz, ny, nx],
            "design_density": x,
            "physical_density": rho,
            "sensitivity_weight": [1.0] * count,
            "compliance": 9.0,
            "physical_volume_fraction": 0.625,
            "iterations": 11,
            "terminal_density_change": 0.005,
            "stop_reason": "design_max",
        },
        "result": {
            "design_density": x,
            "physical_density": rho,
            "compliance": 9.0,
            "converged": True,
            "history": recent,
            "displacements": [0.0],
            "reactions": [0.0],
        },
    }


def public_model(model: dict[str, Any]) -> bytes:
    if model["family"] == "W":
        metadata = {
            "version": "topolab.b4_5.checkpoint.v1",
            "context_sha256": model["context_sha256"],
            "seed": model["seed"],
            "epoch": model["epoch"],
            "objective": "topolab.b4_5.weighted-terminal.v1",
        }
    else:
        metadata = {
            "checkpoint_version": "topolab.b3.checkpoint.v1",
            "context_sha256": model["context_sha256"],
            "recipe": model["family"],
            "seed": model["seed"],
            "selected_epoch": model["epoch"],
        }
    header: dict[str, Any] = {"__metadata__": {"topolab": canonical(metadata).decode("ascii")}}
    offset = 0
    for key, shape in TENSOR_SHAPES.items():
        end = offset + 4 * math.prod(shape)
        header[key] = {"dtype": "F32", "shape": shape, "data_offsets": [offset, end]}
        offset = end
    raw_header = canonical(header).rstrip(b"\n")
    raw_header += b" " * (-len(raw_header) % 8)
    return struct.pack("<Q", len(raw_header)) + raw_header + struct.pack("<f", 0.25) * 26433


def public_check(root: Path) -> dict[str, Any]:
    """ONE post-freeze IO check; caller supplies an exclusive NEW fixture root."""
    root.mkdir(parents=True, exist_ok=False)
    originals, outputs = root / "new-public-sources", root / "new-public-exports"
    originals.mkdir()
    outputs.mkdir()
    registry: dict[str, Any] = {"models": [], "labels": [], "scalars": []}

    def write(base: Path, path: str, raw: bytes) -> None:
        target = base / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())

    bindings = []
    for family in ("C", "W"):
        model = {
            "family": family,
            "seed": 17,
            "epoch": 1,
            "context_sha256": "d" * 64,
            "selection": {"path": "new-public-selection.json", "byte_size": 1, "sha256": "e" * 64},
        }
        raw = public_model(model)
        model["checkpoint"] = reference(f"{family}.safetensors", raw)
        registry["models"].append(model)
        write(originals, f"{family}.safetensors", raw)
        output = f"checkpoints/{family}-17.safetensors"
        write(outputs, output, raw)
        bindings.append({key: model[key] for key in ("family", "seed", "epoch", "context_sha256")})
        bindings[-1].update(
            source=model["checkpoint"], selection=model["selection"], output=reference(output, raw)
        )
    write(
        outputs,
        "models.json",
        canonical({"schema": "topolab.v2.m2-checkpoint-view.v1", "models": bindings}),
    )
    for i, mesh in enumerate(((12, 6, 3), (24, 12, 6)), 1):
        source = public_label(mesh, i)
        raw = canonical(source)
        row = {
            "case_id": source["entry"]["case"]["case_id"],
            "entry": source["entry"],
            "manifest_sha256": source["manifest_sha256"],
            "context_sha256": digest(canonical(source["context"])),
            "source_revision": source["context"]["source_revision"],
            "artifact": reference(f"label-{i}.json", raw),
        }
        registry["labels"].append(row)
        write(originals, f"label-{i}.json", raw)
        production, audit = label_views(source, row)
        write(outputs, f"nn/producer/{row['case_id']}.json", canonical(production))
        write(outputs, f"nn/audit/{row['case_id']}.json", canonical(audit))
    packet = {
        "version": "topolab.b4_30.z-reflection-repair.v2",
        "case_id": "public-uniform",
        "context_sha256": "f" * 64,
        "policy": "uniform",
        "outcome": {
            "method": "uniform",
            "seed": None,
            "route": "baseline",
            "fallback": None,
            "attempt": {
                "succeeded": True,
                "failure_code": None,
                "failure_type": None,
                "metrics": {"final_compliance": 7.25},
                "state": {"result": {"compliance": 7.25}},
            },
        },
    }
    raw = canonical(packet)
    row = {
        "case_id": "public-uniform",
        "context_sha256": "f" * 64,
        "unit": {"path": "new-public-unit.json", "byte_size": 1, "sha256": "0" * 64},
        "packet": reference("uniform.json", raw),
    }
    registry["scalars"].append(row)
    write(originals, "uniform.json", raw)
    write(
        outputs,
        "uniform-scalars.json",
        canonical(
            {"schema": "topolab.v2.m2-uniform-scalar-view.v1", "values": [scalar_view(packet, row)]}
        ),
    )
    result = audit_exports(
        OnceReader(originals, 5, 16 * MIB), OnceReader(outputs, 8, 8 * MIB), registry
    )
    rejected = 0
    for mutate in (
        lambda p: p["outcome"].update(fallback={}),
        lambda p: p.update(policy="candidate"),
    ):
        malformed = deepcopy(packet)
        mutate(malformed)
        try:
            scalar_view(malformed, row)
        except ValueError:
            rejected += 1
    require(rejected == 2, "public damaged controls did not stop")
    result.update(
        status="PASS_PUBLIC_IO_ONLY",
        damaged_controls_rejected=rejected,
        old_source_read_set=[],
        B_quota_consumed=0,
        fixture_root=str(root),
        historical_source_or_scientific_acceptance=False,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("public-check", "r0", "r1"))
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--fixture-root", type=Path)
    parser.add_argument("--exports-root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--authorize-old-read", action="store_true")
    parser.add_argument("--execution-identity")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--plan-sha")
    args = parser.parse_args()
    if args.mode == "public-check":
        require(args.fixture_root is not None, "public check needs an exclusive NEW root")
        if args.execution_identity == EXECUTION_STABLE:
            require(Path(os.path.abspath(args.fixture_root))
                    == AUTHORIZED_STABLE_ROOT / "public-fixtures"
                    and Path(os.path.abspath(args.output))
                    == AUTHORIZED_STABLE_ROOT / "independent-public-check.json",
                    "R-STABLE public role requires literal new paths")
            stable_source_entry(args.plan, args.plan_sha, "independent-public-check")
        else:
            for new_path in (args.fixture_root, args.output):
                require(not Path(os.path.abspath(new_path)).is_relative_to(AUTHORIZED_DATA_ROOT),
                        "public fixture cannot open DATA")
            require(args.execution_identity is None,
                    "public fixture cannot select another production identity")
        require(not args.output.exists(), "independent output exists; no retry")
        result = public_check(args.fixture_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(canonical(result))
            stream.flush()
            os.fsync(stream.fileno())
        return 0
    require(args.execution_identity == EXECUTION_STABLE,
            "historical R CLI closed; explicit R-STABLE identity required")
    require(args.authorize_old_read, "explicit frozen role launch acknowledgement required")
    require(
        args.contract is not None and args.registry is not None and args.data_root is not None,
        "source role requires literal contract/registry/root",
    )
    require(
        Path(os.path.abspath(args.data_root)) == AUTHORIZED_DATA_ROOT,
        "source role requires the authorized literal data root",
    )
    require(
        Path(os.path.abspath(args.contract))
        == Path(__file__).resolve().parents[1]
        / "docs/planning/p17_m2_input_export_preparation_proposal.json",
        "source role requires the frozen versioned contract",
    )
    for new_path in (args.registry, args.output, args.exports_root):
        if new_path is not None:
            require(
                Path(os.path.abspath(new_path)).is_relative_to(AUTHORIZED_STABLE_ROOT),
                "source role new path outside R root",
            )
    # Deliberately lazy: closed identities and lexical root failures cannot
    # import a controller or stat DATA. The gate binds actual readiness/lease.
    stable_source_entry(args.plan, args.plan_sha, f"independent-{args.mode}")
    require(not args.output.exists(), "independent output exists; no retry")
    contract_raw = args.contract.read_bytes()
    require(digest(contract_raw) == CONTENT_CONTRACT_SHA256,
            "frozen content-only contract hash differs")
    contract = parse(contract_raw)
    registry_raw = OnceReader(AUTHORIZED_STABLE_ROOT, 1, 32 * MIB).read(
        Path(os.path.abspath(args.registry)).relative_to(AUTHORIZED_STABLE_ROOT).as_posix(),
        32 * MIB,
    )
    registry = parse(registry_raw, canonical_required=True)
    check_registry_shape(registry, contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path = args.output.with_name(args.output.stem + "-source-identities.json")
    require(not sidecar_path.exists(), "independent source sidecar exists; no retry")
    old_reader = OnceReader(
        args.data_root,
        40 if args.mode == "r0" else 558,
        32 * MIB if args.mode == "r0" else (12 + 768 + 72) * MIB,
        source_identity_checks=True,
        journal=args.output.with_name(args.output.stem + "-source-failures.jsonl"),
    )
    try:
        if args.mode == "r0":
            own = build_registry(old_reader, contract)
            count = compare_words(own, registry)
            result = {
                "status": "PASS_R0_SOURCE_REGISTRY",
                "registry_sha256": digest(registry_raw),
                "own_registry": own,
                "compared_scalar_fields": count,
                "old_read_table": old_reader.table,
                "payload_open_or_stat": False,
                "B_C_authorized_or_run": False,
            }
        else:
            require(args.exports_root is not None, "R1 needs literal new exports root")
            new_reader = OnceReader(args.exports_root, 1070, (12 + 32 + 256 + 1) * MIB)
            result = audit_exports(old_reader, new_reader, registry)
            result["registry_sha256"] = digest(registry_raw)
        producer_sidecar_reader = OnceReader(AUTHORIZED_STABLE_ROOT, 1, 4 * MIB)
        producer_sidecar_raw = producer_sidecar_reader.read(
            f"exporter-{args.mode}/source-identities.json", 4 * MIB,
        )
        result["compared_source_identity_fields"] = compare_source_identities(
            old_reader.observations, parse(producer_sidecar_raw, canonical_required=True),
            40 if args.mode == "r0" else 558,
        )
        own_sidecar_raw = canonical(identity_sidecar(old_reader.observations))
        with sidecar_path.open("xb") as stream:
            stream.write(own_sidecar_raw)
            stream.flush()
            os.fsync(stream.fileno())
        result["producer_source_identities_sha256"] = digest(producer_sidecar_raw)
        result["independent_source_identities_sha256"] = digest(own_sidecar_raw)
        result["execution_identity"] = EXECUTION_STABLE
    except (ValueError, KeyError, TypeError, OSError, OverflowError, struct.error) as error:
        result = {
            "status": "STOP",
            "reason_type": type(error).__name__,
            "reason": str(error),
            "old_read_table": old_reader.table,
            "attempted_paths": sorted(old_reader.seen),
            "source_failures": old_reader.failures,
            "source_identities": old_reader.observations,
            "retry": False,
            "B_C_authorized_or_run": False,
        }
    with args.output.open("xb") as stream:
        stream.write(canonical(result))
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if result["status"].startswith("PASS_") else 2


if __name__ == "__main__":
    sys.exit(main())
