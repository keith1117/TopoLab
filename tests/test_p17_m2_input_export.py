"""New public synthetic records only: no old files and no numerical execution."""

import copy
import importlib.util
import json
import struct
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "r_export", Path(__file__).parents[1] / "scripts/p17_m2_input_export.py"
)
assert SPEC and SPEC.loader
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)
CONTRACT = json.loads(r.CONTRACT.read_text())


def label(n=216, updates=12):
    mesh = [12, 6, 3] if n == 216 else [24, 12, 6]
    case = {"case_id": "public-synthetic", "problem": {"mesh": {"element_counts": mesh}}}
    entry = {
        "case": case,
        "role": "train",
        "training_sets": ["base", "expanded"],
        "source_case_id": "public-parent",
        "physical_fingerprint": "a" * 64,
    }
    context = {"source_revision": "b" * 40}
    stored = {
        "case": case,
        "volume": 0.5,
        "tensor_dtype": "float32",
        "tensor_axis_order": "channel,z,y,x",
        "tensor_shape": [1, *reversed(mesh)],
        "design_density": [0.5] * n,
        "physical_density": [0.625] * n,
        "sensitivity_weight": [1.0] * n,
        "compliance": 2.0,
        "physical_volume_fraction": 0.625,
        "iterations": updates,
        "terminal_density_change": 0.02,
        "stop_reason": "physical_plateau",
    }
    history = [
        {
            "iteration": i + 1,
            "compliance": 3.0,
            "volume_fraction": 0.5,
            "density_change": 0.02,
            "design_density": [0.5] * n,
            "physical_density": [0.5] * n,
        }
        for i in range(updates)
    ]
    raw = {
        "kind": "label",
        "label_version": "topolab.b3.label.v1",
        "entry": entry,
        "context": context,
        "manifest_sha256": "c" * 64,
        "initialization": "projected_float32_uniform",
        "stored": stored,
        "result": {
            "design_density": [0.5] * n,
            "physical_density": [0.500000001] * n,
            "compliance": 3.0,
            "converged": True,
            "history": history,
            "displacements": [123.0],
            "reactions": [456.0],
        },
    }
    item = {
        "case_id": case["case_id"],
        "entry": entry,
        "context_sha256": r.sha(r.canonical(context)),
        "manifest_sha256": "c" * 64,
        "source_revision": "b" * 40,
        "artifact": r.ref("public-label.json", r.canonical(raw)),
    }
    return raw, item


@pytest.mark.parametrize(
    "raw", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e9999}', b"[" * 66 + b"0" + b"]" * 66]
)
def test_strict_json(raw):
    with pytest.raises(ValueError):
        r.parse(raw)


def test_reader_caps_and_once(tmp_path):
    (tmp_path / "a").write_bytes(b"1234")
    reader = r.Reader(tmp_path)
    assert reader.read("a", 4, expected=r.sha(b"1234"), size=4) == b"1234"
    with pytest.raises(ValueError, match="reread"):
        reader.read("a", 4)
    for kwargs in ({"limit": 3}, {"limit": 4, "expected": "0" * 64}, {"limit": 4, "total": 3}):
        with pytest.raises(ValueError):
            r.Reader(tmp_path).read("a", **kwargs)


def test_path_escape_and_symlink(tmp_path):
    (tmp_path / "x").write_bytes(b"x")
    (tmp_path / "alias").symlink_to(tmp_path / "x")
    (tmp_path / "aliasdir").symlink_to(tmp_path, target_is_directory=True)
    for name in ("../x", "/absolute", "alias", "aliasdir/x"):
        with pytest.raises((ValueError, OSError)):
            r.Reader(tmp_path).read(name, 10)


@pytest.mark.parametrize("n", [216, 1728])
def test_restricted_projection_and_actual_float32_state(n):
    raw, item = label(n)
    producer, audit = r.label_views(raw, item)
    assert set(producer["stored"]) == {
        "tensor_dtype",
        "tensor_axis_order",
        "tensor_shape",
        "design_density",
    }
    assert producer["membership"] == {k: v for k, v in item["entry"].items() if k != "case"}
    assert len(audit["recent"]) == 11 and audit["recent"][0]["iteration"] == 2
    assert audit["stored"]["physical_density"] == [0.625] * n
    assert audit["terminal"]["physical_density"] == [0.500000001] * n
    assert "history" not in audit and "displacements" not in audit["terminal"]
    assert "/result/history/0/design_density" not in audit["bit_digests"]
    assert audit["bit_digests"]["/stored/design_density"] == r.sha(
        struct.pack("<" + "f" * n, *([0.5] * n))
    )
    assert r.parse(r.canonical(audit)) == audit


@pytest.mark.parametrize("alter", ["shape", "role", "bits", "short", "unknownfield"])
def test_bad_label_refuses(alter):
    raw, item = label()
    if alter == "shape":
        raw["stored"]["tensor_shape"] = [216]
    if alter == "role":
        raw["entry"]["role"] = "fit_validation"
    if alter == "bits":
        raw["stored"]["design_density"][0] = 0.1
    if alter == "short":
        raw["result"]["history"] = raw["result"]["history"][:3]
    if alter == "unknownfield":
        raw["stored"]["extra_training_feature"] = 1
    with pytest.raises(ValueError):
        r.label_views(raw, item)


def checkpoint(item):
    tensors = CONTRACT["checkpoints"]["tensor_header_schema"]["keys_exact"]
    header, offset = {}, 0
    for key, spec in tensors.items():
        length = 4 * r.math.prod(spec["shape"])
        header[key] = {**spec, "data_offsets": [offset, offset + length]}
        offset += length
    meta = {
        "checkpoint_version": "topolab.b3.checkpoint.v1",
        "context_sha256": item["context_sha256"],
        "recipe": item["family"],
        "seed": item["seed"],
        "selected_epoch": item["epoch"],
    }
    header["__metadata__"] = {"topolab": r.canonical(meta).decode()}
    h = r.canonical(header)
    return struct.pack("<Q", len(h)) + h + b"\0" * offset


def test_checkpoint_header_and_original_bits():
    item = {"family": "P", "seed": 17, "epoch": 123, "context_sha256": "a" * 64}
    raw = checkpoint(item)
    r.check_weights(raw, item, CONTRACT)
    corrupted = raw[:-4] + struct.pack("<f", float("nan"))
    with pytest.raises(ValueError):
        r.check_weights(corrupted, item, CONTRACT)
    wrong = {**item, "epoch": 124}
    with pytest.raises(ValueError):
        r.check_weights(raw, wrong, CONTRACT)
    with pytest.raises(ValueError):
        r.check_weights(b"bad", item, CONTRACT)


def test_original_uniform_only():
    item = {"case_id": "public", "context_sha256": "a" * 64, "unit": {}, "packet": {}}
    raw = {
        "version": "topolab.b4_30.z-reflection-repair.v2",
        "case_id": "public",
        "context_sha256": "a" * 64,
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
                "metrics": {"final_compliance": 1.25},
                "state": {"result": {"compliance": 1.25}},
            },
        },
    }
    view = r.scalar_view(raw, item)
    assert view["compliance_bits_sha256"] == r.sha(struct.pack("<d", 1.25))
    assert set(view) == {
        "case_id",
        "compliance",
        "compliance_bits_sha256",
        "initialization",
        "solver_identity",
        "source",
    }
    for edit in ("fallback", "different"):
        bad = copy.deepcopy(raw)
        if edit == "fallback":
            bad["outcome"]["fallback"] = {"succeeded": True}
        else:
            bad["outcome"]["attempt"]["state"]["result"]["compliance"] = 1.2500000000001
        with pytest.raises(ValueError):
            r.scalar_view(bad, item)


def test_cli_denies_unregistered_root_before_reader(monkeypatch, tmp_path):
    def denied(*args, **kwargs):
        raise AssertionError("reader must not be constructed")

    monkeypatch.setattr(r, "Reader", denied)
    with pytest.raises(ValueError):
        r.main(
            [
                "r0",
                "--data-root",
                str(tmp_path),
                "--output",
                str(tmp_path / "out"),
                "--authorize-old-read",
            ]
        )


def test_output_nonoverwrite(tmp_path):
    r.new_file(tmp_path / "new.json", b"{}")
    with pytest.raises(FileExistsError):
        r.new_file(tmp_path / "new.json", b"replace")


def source_metadata(tmp_path):
    """All40 synthetic metadata files; none of the558 payload files exists."""
    contract = copy.deepcopy(CONTRACT)
    packets = {}
    context = {"source_revision": "b" * 40}
    manifest = {"context": context, "public": True}
    manifest_sha = r.sha(r.canonical(manifest))
    entries = []
    for i in range(528):
        case_id = f"public-train-{i:04d}"
        entry = {
            "role": "train",
            "case": {
                "case_id": case_id,
                "problem": {"mesh": {"element_counts": [12, 6, 3] if i < 432 else [24, 12, 6]}},
            },
        }
        h = r.sha(case_id.encode())
        entries.append(
            {
                "entry": entry,
                "status": "succeeded",
                "artifact": {
                    "access": {"kind": "label", "entry": entry, "artifact_sha256": h},
                    "relative_path": f"artifacts/label/{case_id}/{h}.json",
                    "manifest_sha256": manifest_sha,
                    "source_revision": "b" * 40,
                    "byte_size": 100,
                },
            }
        )
    index = {"manifest": manifest, "manifest_sha256": manifest_sha, "entries": entries}
    ctx = {"data_index": index}
    ctx_sha = r.sha(r.canonical(ctx))
    contract["R0"]["embedded_B3_data_index_sha256"] = r.sha(r.canonical(index))
    weighted, outcomes = [], []
    for row in contract["checkpoints"]["fixed_rows"]:
        family, seed = row["family"], row["seed"]
        cp = {
            "sha256": r.sha(f"{family}-{seed}".encode()),
            "byte_size": 105732,
            "kind": "checkpoint",
        }
        history = {
            "context_sha256": contract["R0"]["W_context_sha256"] if family == "W" else ctx_sha,
            "seed": seed,
            "recipe": "P" if family == "W" else family,
            "selected_epoch": row["selected_epoch"],
            "history": [{}],
            "checkpoint": cp,
        }
        if family == "W":
            root = "b4-5-weighted-terminal/fit"
            packet = {
                "version": "topolab.b4_5.selection.v1",
                "objective": "topolab.b4_5.weighted-terminal.v1",
                "history_schema": history,
                "checkpoint": cp,
            }
        else:
            root, packet = "b3-v1-fits", history
        raw = r.canonical(packet)
        h = r.sha(raw)
        packets[root + "/artifacts/selection/" + h + ".json"] = packet
        value = {"sha256": h, "byte_size": len(raw), "kind": "selection"}
        if family == "W":
            weighted.append(value)
        else:
            outcomes.append({"recipe": family, "seed": seed, "selection": value})
    packets["b3-v1-fits/b3_training.json"] = {
        "context": ctx,
        "context_sha256": ctx_sha,
        "outcomes": outcomes,
    }

    def journal(base, context_sha, names, payloads):
        previous = "0" * 64
        for i, (name, payload) in enumerate(zip(names, payloads, strict=True)):
            packet = {
                "version": "topolab.b4.unit.v1",
                "unit": name,
                "context_sha256": context_sha,
                "previous_sha256": previous,
                "payload": payload,
            }
            packets[f"{base}/units/{i:04d}.json"] = packet
            previous = r.sha(r.canonical(packet))
        packets[base + "/progress.json"] = {
            "version": "topolab.b4.progress.v1",
            "context_sha256": context_sha,
            "units_sha256": r.sha(r.canonical(names)),
            "completed": len(names),
            "attempted": len(names),
            "active_at": None,
            "pending": None,
            "integrity_failed": False,
            "resource_failed": False,
            "head_sha256": previous,
        }
        packets[base + "/summary.json"] = {"context_sha256": context_sha, "head_sha256": previous}

    journal(
        "b4-5-weighted-terminal/fit",
        contract["R0"]["W_context_sha256"],
        ["W/17", "W/29", "W/43"],
        weighted,
    )
    base = "b4-30-z-reflection-repair-v2"
    packets[base + "/context.json"] = {"public": "mock-source-not-historical"}
    packets[base + "/sentinel/independent_audit.json"] = {"public": "mock-audit"}
    rctx = r.sha(r.canonical(packets[base + "/context.json"]))
    payloads = [
        {
            "sha256": r.sha(c.encode()),
            "byte_size": 100,
            "path": f"artifacts/outcome/{r.sha(c.encode())}.json",
        }
        for c in contract["scalars"]["case_ids"]
    ]
    journal(base + "/sentinel/reference", rctx, contract["scalars"]["case_ids"], payloads)
    for item in contract["R0"]["literal_bootstrap_files"]:
        item["expected_sha256"] = r.sha(r.canonical(packets[item["relative_path"]]))
    for name, packet in packets.items():
        r.new_file(tmp_path / name, r.canonical(packet))
    return contract


def test_r0_exact_metadata_only(tmp_path):
    contract = source_metadata(tmp_path)
    reader = r.Reader(tmp_path)
    registry = r.register(reader, contract)
    assert len(reader.rows) == 40
    assert len(registry["models"]) == 12 and len(registry["labels"]) == 528
    assert len(registry["scalars"]) == 18
    assert all("artifacts/label/" not in x["path"] for x in reader.rows)
    assert all(not x["path"].endswith(".safetensors") for x in reader.rows)
    assert [x["epoch"] for x in registry["models"] if x["family"] == "W"] == [93, 156, 142]


def test_r0_hash_failure_stops_before_other_metadata(tmp_path):
    contract = source_metadata(tmp_path)
    first = contract["R0"]["literal_bootstrap_files"][0]["relative_path"]
    (tmp_path / first).write_bytes(b"{}\n")
    reader = r.Reader(tmp_path)
    with pytest.raises(ValueError, match="source SHA"):
        r.register(reader, contract)
    assert len(reader.rows) == 1
