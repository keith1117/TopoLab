"""R-only bounded source registration and literal restricted field transcription.

No TopoLab imports, model execution, numerical validation or scientific dispatch.
Actual source access requires the owner grant and the externally frozen role plan.
"""

import argparse
import hashlib
import json
import math
import os
import re
import stat
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = Path("/Users/keith1117/Documents/TopoLab-data")
CONTRACT = REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json"
MIB = 1024 * 1024


def need(ok, reason):
    if not ok:
        raise ValueError("STOP: " + reason)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            need(k not in result, "duplicate JSON key")
            result[k] = v
        return result

    def number(text):
        value = float(text)
        need(math.isfinite(value), "nonfinite JSON number")
        return value

    def bad(_):
        raise ValueError("STOP: nonfinite JSON literal")

    result = json.loads(raw, object_pairs_hook=pairs, parse_float=number, parse_constant=bad)

    def depth(value, n=0):
        need(n <= 64, "JSON depth")
        if isinstance(value, dict):
            for v in value.values():
                depth(v, n + 1)
        elif isinstance(value, list):
            for v in value:
                depth(v, n + 1)

    depth(result)
    return result


def new_file(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def ref(path, raw):
    return {"path": path, "byte_size": len(raw), "sha256": sha(raw)}


class Reader:
    """One bounded read per literal file; identities journaled even on failure."""

    def __init__(self, root, journal=None):
        self.root, self.journal = Path(root).absolute(), journal
        self.rows, self.total, self.seen, self.attempts = [], {}, set(), []

    def read(self, relative, limit, *, expected=None, size=None, group="metadata", total=None):
        need(isinstance(relative, str) and relative not in self.seen, "unregistered reread")
        self.seen.add(relative)
        parts = Path(relative).parts
        need(
            parts and not Path(relative).is_absolute() and all(p not in (".", "..") for p in parts),
            "literal relative path",
        )
        need(group != "metadata" or len(self.rows) < 40, "metadata file count")
        self.attempts.append(relative)
        if self.journal:
            with self.journal.open("ab") as stream:
                stream.write(canonical({"attempt": relative}))
                stream.flush()
                os.fsync(stream.fileno())
        parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in (*self.root.parts[1:], *parts[:-1]):
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                os.close(parent)
                parent = child
            declared = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            need(
                stat.S_ISREG(declared.st_mode) and 0 < declared.st_size <= limit,
                "file byte cap/type",
            )
            need(size is None or declared.st_size == size, "declared source size")
            need(
                total is None or self.total.get(group, 0) + declared.st_size <= total,
                "aggregate byte cap before open",
            )
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        finally:
            os.close(parent)
        try:
            before = os.fstat(fd)
            need(
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                == (declared.st_dev, declared.st_ino, declared.st_size, declared.st_mtime_ns),
                "source replaced before read",
            )
            with os.fdopen(fd, "rb", closefd=False) as stream:
                raw = stream.read(limit + 1)
            after = os.fstat(fd)
            need(
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
                "source changed",
            )
        finally:
            os.close(fd)
        row = ref(relative, raw)
        self.rows.append(row)
        if self.journal:
            with self.journal.open("ab") as stream:
                stream.write(canonical(row))
                stream.flush()
                os.fsync(stream.fileno())
        self.total[group] = self.total.get(group, 0) + len(raw)
        need(len(raw) <= limit and (size is None or len(raw) == size), "read size")
        need(total is None or self.total[group] <= total, "aggregate byte cap")
        need(expected is None or row["sha256"] == expected, "source SHA " + relative)
        return raw

    def packet(self, relative, limit, **kwargs):
        raw = self.read(relative, limit, **kwargs)
        packet = parse(raw)
        need(canonical(packet) == raw, "original canonical JSON " + relative)
        return packet


def fit_ref(root, value, kind):
    suffix = "safetensors" if kind == "checkpoint" else "json"
    h = value["sha256"]
    need(
        re.fullmatch("[0-9a-f]{64}", h) is not None
        and type(value["byte_size"]) is int
        and value["byte_size"] > 0,
        "artifact identity",
    )
    path = f"artifacts/{kind}/{h}.{suffix}"
    need("path" not in value or value["path"] == path, "content path")
    return {"path": root + "/" + path, "byte_size": value["byte_size"], "sha256": h}


def read_ref(reader, value, cap, **kwargs):
    return reader.read(
        value["path"], cap, expected=value["sha256"], size=value["byte_size"], **kwargs
    )


def units(reader, base, progress, context, names):
    need(
        progress["version"] == "topolab.b4.progress.v1"
        and progress["context_sha256"] == context
        and progress["units_sha256"] == sha(canonical(names))
        and progress["completed"] == len(names)
        and progress["attempted"] == len(names)
        and progress["active_at"] is None
        and progress["pending"] is None
        and not progress["integrity_failed"]
        and not progress["resource_failed"],
        "closed unit ledger",
    )
    previous, out = "0" * 64, []
    for n, name in enumerate(names):
        path = f"{base}/units/{n:04d}.json"
        packet = reader.packet(path, 32768, total=32 * MIB)
        need(
            packet["version"] == "topolab.b4.unit.v1"
            and packet["context_sha256"] == context
            and packet["unit"] == name
            and packet["previous_sha256"] == previous,
            "unit chain",
        )
        previous = reader.rows[-1]["sha256"]
        out.append((packet["payload"], reader.rows[-1]))
    need(progress["head_sha256"] == previous, "unit head")
    return out


def register(reader, contract):
    bootstrap = {}
    for item in contract["R0"]["literal_bootstrap_files"]:
        bootstrap[item["relative_path"]] = reader.packet(
            item["relative_path"],
            item["max_bytes"],
            expected=item["expected_sha256"],
            total=32 * MIB,
        )
    fit = bootstrap["b3-v1-fits/b3_training.json"]
    ctx = fit["context"]
    need(sha(canonical(ctx)) == fit["context_sha256"], "B3 context")
    index = ctx["data_index"]
    need(sha(canonical(index)) == contract["R0"]["embedded_B3_data_index_sha256"], "B3 data index")
    manifest = index["manifest"]
    need(sha(canonical(manifest)) == index["manifest_sha256"], "B3 manifest")
    source_context = sha(canonical(manifest["context"]))
    labels = []
    for item in index["entries"]:
        entry = item["entry"]
        if entry["role"] != "train":
            continue
        artifact = item["artifact"]
        identity = entry["case"]["case_id"]
        h = artifact["access"]["artifact_sha256"]
        path = f"artifacts/label/{identity}/{h}.json"
        need(
            item["status"] == "succeeded"
            and artifact["access"]["kind"] == "label"
            and artifact["access"]["entry"] == entry
            and artifact["relative_path"] == path
            and artifact["manifest_sha256"] == index["manifest_sha256"]
            and artifact["source_revision"] == manifest["context"]["source_revision"],
            "train provenance",
        )
        labels.append(
            {
                "case_id": identity,
                "entry": entry,
                "context_sha256": source_context,
                "manifest_sha256": index["manifest_sha256"],
                "source_revision": artifact["source_revision"],
                "artifact": {
                    "path": "b3-v1-data/" + path,
                    "byte_size": artifact["byte_size"],
                    "sha256": h,
                },
            }
        )
    need(
        all(0 < x["artifact"]["byte_size"] <= 64 * MIB for x in labels)
        and sum(x["artifact"]["byte_size"] for x in labels) <= 768 * MIB,
        "declared train byte caps",
    )
    labels.sort(key=lambda x: x["case_id"])
    need(len(labels) == 528 and len({x["case_id"] for x in labels}) == 528, "train population")
    meshes = [x["entry"]["case"]["problem"]["mesh"]["element_counts"] for x in labels]
    need(meshes.count([12, 6, 3]) == 432 and meshes.count([24, 12, 6]) == 96, "train scales")
    outcomes = {(x["recipe"], x["seed"]): x for x in fit["outcomes"]}
    wp = bootstrap["b4-5-weighted-terminal/fit/progress.json"]
    wctx = contract["R0"]["W_context_sha256"]
    wunits = units(reader, "b4-5-weighted-terminal/fit", wp, wctx, ["W/17", "W/29", "W/43"])
    summary = bootstrap["b4-5-weighted-terminal/fit/summary.json"]
    need(
        summary["context_sha256"] == wctx and summary["head_sha256"] == wp["head_sha256"],
        "W summary",
    )
    models = []
    for row in contract["checkpoints"]["fixed_rows"]:
        family, seed = row["family"], row["seed"]
        weighted = family == "W"
        root = "b4-5-weighted-terminal/fit" if weighted else "b3-v1-fits"
        value = (
            wunits[[17, 29, 43].index(seed)][0]
            if weighted
            else outcomes[(family, seed)]["selection"]
        )
        selection = fit_ref(root, value, "selection")
        packet = parse(read_ref(reader, selection, 256 * 1024, total=32 * MIB))
        history = packet["history_schema"] if weighted else packet
        expected_context = wctx if weighted else fit["context_sha256"]
        need(
            history["context_sha256"] == expected_context
            and history["seed"] == seed
            and history["recipe"] == ("P" if weighted else family)
            and history["selected_epoch"] == row["selected_epoch"]
            and 1 <= len(history["history"]) <= 200,
            "fixed selection",
        )
        if weighted:
            need(
                packet["version"] == "topolab.b4_5.selection.v1"
                and packet["objective"] == "topolab.b4_5.weighted-terminal.v1",
                "W objective",
            )
        if weighted:
            inner = history["checkpoint"]
            need(
                inner["sha256"] == packet["checkpoint"]["sha256"]
                and inner["byte_size"] == packet["checkpoint"]["byte_size"],
                "W inner/outer checkpoint binding",
            )
        checkpoint = fit_ref(root, packet["checkpoint"], "checkpoint")
        need(checkpoint["byte_size"] <= MIB, "checkpoint declared cap")
        models.append(
            {
                "family": family,
                "seed": seed,
                "epoch": row["selected_epoch"],
                "context_sha256": expected_context,
                "selection": selection,
                "checkpoint": checkpoint,
            }
        )
    base = "b4-30-z-reflection-repair-v2"
    rp = bootstrap[base + "/sentinel/reference/progress.json"]
    rctx = contract["R0"]["literal_bootstrap_files"][3]["expected_sha256"]
    ru = units(reader, base + "/sentinel/reference", rp, rctx, contract["scalars"]["case_ids"])
    rs = bootstrap[base + "/sentinel/reference/summary.json"]
    need(
        rs["context_sha256"] == rctx and rs["head_sha256"] == rp["head_sha256"], "reference summary"
    )
    scalars = []
    for case_id, (value, unit) in zip(contract["scalars"]["case_ids"], ru, strict=True):
        packet = fit_ref(base + "/sentinel/reference", value, "outcome")
        need(packet["byte_size"] <= 4 * MIB, "uniform declared cap")
        scalars.append({"case_id": case_id, "context_sha256": rctx, "unit": unit, "packet": packet})
    need(
        sum(x["packet"]["byte_size"] for x in scalars) <= 72 * MIB, "declared uniform aggregate cap"
    )
    need(len(reader.rows) == 40, "R0 exact metadata count")
    return {
        "schema": "topolab.v2.m2-input-source-registry.v1",
        "metadata": sorted(reader.rows, key=lambda x: x["path"]),
        "models": models,
        "labels": labels,
        "scalars": scalars,
    }


def array_digest(values, fmt, count=None):
    need(isinstance(values, list) and (count is None or len(values) == count), "array length")
    need(all(type(v) in (int, float) and math.isfinite(v) for v in values), "array finite/type")
    return sha(b"".join(struct.pack("<" + fmt, v) for v in values))


def label_views(raw, item):
    need(
        raw["kind"] == "label"
        and raw["label_version"] == "topolab.b3.label.v1"
        and raw["entry"] == item["entry"]
        and raw["entry"]["role"] == "train"
        and sha(canonical(raw["context"])) == item["context_sha256"]
        and raw["manifest_sha256"] == item["manifest_sha256"],
        "label source binding",
    )
    stored, result = raw["stored"], raw["result"]
    history = result["history"]
    nx, ny, nz = item["entry"]["case"]["problem"]["mesh"]["element_counts"]
    n = nx * ny * nz
    need(
        stored["case"] == item["entry"]["case"]
        and stored["tensor_dtype"] == "float32"
        and stored["tensor_axis_order"] == "channel,z,y,x"
        and stored["tensor_shape"] == [1, nz, ny, nx]
        and 1 <= len(history) <= 360
        and stored["iterations"] == len(history)
        and result["converged"] is True,
        "label shape/terminal status",
    )
    need(
        stored["stop_reason"] in ("design_max", "physical_plateau")
        and (stored["stop_reason"] != "physical_plateau" or len(history) >= 11),
        "stop certificate",
    )
    common = {
        "case": raw["entry"]["case"],
        "membership": {k: v for k, v in raw["entry"].items() if k != "case"},
        "initialization": raw["initialization"],
        "source": {
            **item["artifact"],
            "context_sha256": item["context_sha256"],
            "manifest_sha256": item["manifest_sha256"],
        },
    }
    digests = {
        "/stored/" + k: array_digest(stored[k], "f", n)
        for k in ("design_density", "physical_density", "sensitivity_weight")
    }
    for k in ("design_density", "physical_density", "sensitivity_weight"):
        need(
            all(struct.unpack("<f", struct.pack("<f", v))[0] == v for v in stored[k]),
            "stored exactF32",
        )
    need(
        array_digest(result["design_density"], "f", n) == digests["/stored/design_density"],
        "f64->f32 design",
    )
    for k in ("design_density", "physical_density"):
        digests["/result/" + k] = array_digest(result[k], "d", n)
    recent = []
    for i in range(max(0, len(history) - 11), len(history)):
        state = history[i]
        need(
            set(state)
            == {
                "iteration",
                "compliance",
                "volume_fraction",
                "density_change",
                "design_density",
                "physical_density",
            }
            and state["iteration"] == i + 1,
            "recent original fields/order",
        )
        recent.append(state)
        for k in ("design_density", "physical_density"):
            digests[f"/result/history/{i}/{k}"] = array_digest(state[k], "d", n)
    producer = {
        **common,
        "schema": "topolab.v2.m2-nn-producer-view.v1",
        "stored": {
            k: stored[k]
            for k in ("tensor_dtype", "tensor_axis_order", "tensor_shape", "design_density")
        },
        "bit_digests": {"/stored/design_density": digests["/stored/design_density"]},
    }
    audit = {
        **common,
        "schema": "topolab.v2.m2-nn-audit-view.v1",
        "stored": {k: v for k, v in stored.items() if k != "case"},
        "terminal": {
            k: result[k] for k in ("design_density", "physical_density", "compliance", "converged")
        },
        "total_updates": len(history),
        "recent": recent,
        "bit_digests": digests,
    }
    need(
        set(audit["stored"])
        == {
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
        },
        "stored field whitelist",
    )
    return producer, audit


def check_weights(raw, item, contract):
    need(8 < len(raw) <= MIB, "Safetensors bytes")
    length = int.from_bytes(raw[:8], "little")
    need(0 < length < len(raw) - 8, "Safetensors header length")
    header = parse(raw[8 : 8 + length])
    tensors = contract["checkpoints"]["tensor_header_schema"]["keys_exact"]
    need(set(header) == set(tensors) | {"__metadata__"}, "tensor keys")
    meta = parse(header["__metadata__"]["topolab"])
    if item["family"] == "W":
        expected = {
            "version": "topolab.b4_5.checkpoint.v1",
            "context_sha256": item["context_sha256"],
            "seed": item["seed"],
            "epoch": item["epoch"],
            "objective": "topolab.b4_5.weighted-terminal.v1",
        }
    else:
        expected = {
            "checkpoint_version": "topolab.b3.checkpoint.v1",
            "context_sha256": item["context_sha256"],
            "recipe": item["family"],
            "seed": item["seed"],
            "selected_epoch": item["epoch"],
        }
    need(
        meta == expected and set(header["__metadata__"]) == {"topolab"},
        "checkpoint original provenance",
    )
    body, intervals = raw[8 + length :], []
    for key, spec in tensors.items():
        tensor = header[key]
        start, end = tensor["data_offsets"]
        need(
            tensor["dtype"] == "F32"
            and tensor["shape"] == spec["shape"]
            and type(start) is int
            and type(end) is int
            and 0 <= start < end <= len(body)
            and end - start == math.prod(spec["shape"]) * 4,
            "tensor layout",
        )
        need(
            all(math.isfinite(x[0]) for x in struct.iter_unpack("<f", body[start:end])),
            "tensor finite",
        )
        intervals.append((start, end))
    intervals.sort()
    need(
        len(body) == 105732
        and intervals[0][0] == 0
        and intervals[-1][1] == len(body)
        and all(a[1] == b[0] for a, b in zip(intervals, intervals[1:], strict=False)),
        "tensor coverage",
    )


def scalar_view(raw, item):
    outcome = raw["outcome"]
    attempt = outcome["attempt"]
    need(
        raw["version"] == "topolab.b4_30.z-reflection-repair.v2"
        and raw["context_sha256"] == item["context_sha256"]
        and raw["case_id"] == item["case_id"]
        and raw["policy"] == "uniform"
        and outcome["method"] == "uniform"
        and outcome["seed"] is None
        and outcome["route"] == "baseline"
        and outcome["fallback"] is None
        and attempt["succeeded"] is True
        and attempt["failure_code"] is None
        and attempt["failure_type"] is None,
        "original uniform successful attempt",
    )
    value = attempt["metrics"]["final_compliance"]
    need(
        type(value) in (float, int)
        and math.isfinite(value)
        and value > 0
        and struct.pack("<d", value) == struct.pack("<d", attempt["state"]["result"]["compliance"]),
        "uniform scalar exact",
    )
    return {
        "case_id": item["case_id"],
        "compliance": value,
        "compliance_bits_sha256": sha(struct.pack("<d", value)),
        "initialization": {k: outcome[k] for k in ("method", "seed", "route")},
        "solver_identity": {
            "context_sha256": item["context_sha256"],
            "packet_version": raw["version"],
        },
        "source": {
            **item["packet"],
            "json_pointer": "/outcome/attempt/metrics/final_compliance",
            "unit": item["unit"],
        },
    }


def export(reader, registry, contract, output):
    need(
        len(registry["models"]) == 12
        and len(registry["labels"]) == 528
        and len(registry["scalars"]) == 18,
        "fixed registry counts",
    )
    written, totals = [], {}

    def emit(path, value, each, total, group, raw=False):
        data = value if raw else canonical(value)
        totals[group] = totals.get(group, 0) + len(data)
        need(len(data) <= each and totals[group] <= total, "view byte cap")
        new_file(output / path, data)
        written.append(ref(path, data))

    models = []
    for item in registry["models"]:
        raw = read_ref(reader, item["checkpoint"], MIB, group="checkpoint", total=12 * MIB)
        check_weights(raw, item, contract)
        path = f"checkpoints/{item['family']}-{item['seed']}.safetensors"
        emit(path, raw, MIB, 12 * MIB, "checkpoint", raw=True)
        models.append(
            {k: item[k] for k in ("family", "seed", "epoch", "context_sha256")}
            | {"source": item["checkpoint"], "selection": item["selection"], "output": written[-1]}
        )
    emit(
        "models.json",
        {"schema": "topolab.v2.m2-checkpoint-view.v1", "models": models},
        MIB,
        MIB,
        "models",
    )
    for item in registry["labels"]:
        packet = parse(read_ref(reader, item["artifact"], 64 * MIB, group="label", total=768 * MIB))
        producer, audit = label_views(packet, item)
        emit("nn/producer/" + item["case_id"] + ".json", producer, 128 * 1024, 32 * MIB, "producer")
        emit("nn/audit/" + item["case_id"] + ".json", audit, 2 * MIB, 256 * MIB, "audit")
    values = []
    for item in registry["scalars"]:
        raw = read_ref(reader, item["packet"], 4 * MIB, group="uniform", total=72 * MIB)
        values.append(scalar_view(parse(raw), item))
    emit(
        "uniform-scalars.json",
        {"schema": "topolab.v2.m2-uniform-scalar-view.v1", "values": values},
        65536,
        65536,
        "scalar",
    )
    manifest = {
        "schema": "topolab.v2.m2-input-export-manifest.v1",
        "source_registry_sha256": sha(canonical(registry)),
        "outputs": written,
        "old_read_table": reader.rows,
        "B_C_run": False,
        "FEM_inference_calls": 0,
        "status": "TRANSCRIPTION_PENDING_INDEPENDENT_COMPARISON",
    }
    new_file(output / "export_manifest.json", canonical(manifest))
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("r0", "r1"))
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--independent-r0", type=Path)
    parser.add_argument("--authorize-old-read", action="store_true")
    args = parser.parse_args(argv)
    need(
        args.authorize_old_read and args.data_root.absolute() == DATA,
        "literal authorized R source root only",
    )
    need(
        args.output.absolute().is_relative_to(DATA / "p17-m2-input-export-preparation-v1")
        and args.output.resolve() == args.output.absolute(),
        "new R output only",
    )
    need(args.contract.absolute() == CONTRACT, "literal frozen R contract")
    for named in (args.registry, args.independent_r0):
        if named is not None:
            need(
                named.absolute().is_relative_to(DATA / "p17-m2-input-export-preparation-v1")
                and named.resolve() == named.absolute(),
                "new registry/review paths only",
            )
    args.output.mkdir(parents=True, exist_ok=False)
    new_file(
        args.output / "pending.json",
        canonical({"stage": args.stage, "status": "PENDING_BEFORE_OLD_READ"}),
    )
    reader = Reader(args.data_root, args.output / "source-read.jsonl")
    try:
        contract = parse(args.contract.read_bytes())
        if args.stage == "r0":
            result = register(reader, contract)
            new_file(args.output / "source_registry.json", canonical(result))
        else:
            need(
                args.registry is not None and args.independent_r0 is not None,
                "independent R0 before payload",
            )
            raw = args.registry.read_bytes()
            registry = parse(raw)
            reviewed = parse(args.independent_r0.read_bytes())
            need(
                reviewed["status"] == "PASS_R0_SOURCE_REGISTRY"
                and reviewed["registry_sha256"] == sha(raw),
                "independent registered-source acceptance",
            )
            result = export(reader, registry, contract, args.output / "exports")
        new_file(
            args.output / "terminal.json",
            canonical(
                {
                    "status": "ROLE_COMPLETE_PENDING_EXTERNAL_RSS_EXIT",
                    "stage": args.stage,
                    "old_files_read": len(reader.rows),
                    "attempted_source_paths": reader.attempts,
                    "B_C_run": False,
                }
            ),
        )
    except Exception as exc:
        new_file(
            args.output / "failure.json",
            canonical(
                {
                    "status": "STOP_NO_RETRY",
                    "stage": args.stage,
                    "error_type": type(exc).__name__,
                    "reason": str(exc)[:512],
                    "old_files_read": len(reader.rows),
                    "attempted_source_paths": reader.attempts,
                }
            ),
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
