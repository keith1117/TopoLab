"""Failure evidence at real R0/R1 boundaries; newly authored local sources only."""

import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


def load(name, directory="scripts"):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parents[1] / directory / (name + ".py")
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


producer = load("p17_m2_input_export")
independent = load("p17_m2_input_export_independent")


def source_reader(kind, root, journal):
    if kind == "producer":
        return producer.Reader(root, journal, execution_identity=producer.STABLE_IDENTITY,
                               source_identity_checks=True)
    return independent.OnceReader(root, 558, 1024 * 1024 * 1024,
                                  source_identity_checks=True, journal=journal)


@pytest.mark.parametrize("kind", ["producer", "independent"])
@pytest.mark.parametrize("raw,stage", [
    (b'{"x":', "json_parse"),
    (b'{"x":1,"x":2}\n', "json_parse"),
    (b'{}', "canonical_json"),
])
def test_r0_parse_stop_keeps_full_source_context(tmp_path, kind, raw, stage):
    source = tmp_path / "new-source.json"
    source.write_bytes(raw)
    journal = tmp_path / "new-journal.jsonl"
    reader = source_reader(kind, tmp_path, journal)
    contract = {"R0": {"literal_bootstrap_files": [{
        "relative_path": source.name, "max_bytes": 1024,
        "expected_sha256": producer.sha(raw),
    }]}}
    register = producer.register if kind == "producer" else independent.build_registry
    with pytest.raises(ValueError) as stopped:
        register(reader, contract)

    assert len(reader.failures) == 1
    failure = reader.failures[0]
    assert failure["path"] == source.name and failure["attempt_ordinal"] == 1
    assert failure["stage"] == stage
    assert failure["status"] == "STOP_NO_RETRY"
    assert failure["primary_reason"] == str(stopped.value)
    assert failure["exception_type"] == type(stopped.value).__name__
    assert failure["returned_bytes"] == len(raw)
    assert failure["source"] == producer.ref(source.name, raw)
    assert failure["changed_fields"] == []
    actual = source.stat()
    expected = {key: getattr(actual, key)
                for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")}
    assert all(failure[key] == expected for key in ("declared", "before", "after", "closing"))
    assert json.loads(journal.read_bytes().splitlines()[-1]) == failure


    with pytest.raises(ValueError, match="reread|repeat"):
        reader.read(source.name, 1024)


@pytest.mark.parametrize("journal_fails", [False, True])
def test_stage_failure_json_keeps_prefix_tuples_and_secondary_error(
    tmp_path, monkeypatch, journal_fails
):
    root, output = tmp_path / "new-sources", tmp_path / "new-result"
    output.mkdir()
    producer.new_file(root / "new-prefix.json", b'{}\n')
    contract = json.loads(producer.CONTRACT.read_bytes())
    first = contract["R0"]["literal_bootstrap_files"][0]["relative_path"]
    source = root / first
    producer.new_file(source, b'{}\n')
    journal = output / "source-read.jsonl"
    reader = source_reader("producer", root, journal)
    reader.read("new-prefix.json", 1024)
    real_fstat, real_open = os.fstat, Path.open
    observed = []

    def fstat(fd):
        if len(observed) == 1:
            before = source.stat()
            os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns + 1))
        value = real_fstat(fd)
        observed.append(value)
        return value

    def open_file(path, mode="r", *args, **kwargs):
        if journal_fails and path == journal and mode == "ab" and len(observed) == 2:
            raise OSError("new injected journal failure")
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(os, "fstat", fstat)
    monkeypatch.setattr(Path, "open", open_file)
    args = SimpleNamespace(stage="r0", contract=producer.CONTRACT, output=output)
    assert producer.execute_stage(args, reader) == 1
    result = json.loads((output / "failure.json").read_bytes())
    assert result["status"] == "STOP_NO_RETRY"
    assert result["error_type"] == "ValueError" and result["reason"] == "STOP: source changed"
    assert result["old_files_read"] == 1 and len(observed) == 2
    assert result["source_identities"] == reader.source_observations
    assert result["old_read_table"] == reader.rows
    assert result["source_failures"] == reader.failures
    failure = result["source_failures"][0]
    assert failure["path"] == first and failure["attempt_ordinal"] == 2
    assert failure["stage"] == "after_read_identity"
    assert failure["returned_bytes"] == 3 and failure["changed_fields"] == ["st_mtime_ns"]
    assert failure["after"]["st_mtime_ns"] == failure["before"]["st_mtime_ns"] + 1
    assert failure["closing"] is None
    if journal_fails:
        assert failure["recording_error"] == "OSError: new injected journal failure"
    else:
        assert "recording_error" not in failure
        assert json.loads(journal.read_bytes().splitlines()[-1]) == failure
    assert not (output / "terminal.json").exists()
    assert not (output / "source-identities.json").exists()
    with pytest.raises(ValueError, match="reread|repeat"):
        reader.read(first, 1024)


@pytest.mark.parametrize("kind", ["producer", "independent"])
def test_r0_schema_stop_names_the_source_validated_not_the_last_read(tmp_path, kind):
    names = ["b3-v1-fits/b3_training.json", "new-unrelated.json"]
    for name in names:
        producer.new_file(tmp_path / name, b'{}\n')
    journal = tmp_path / "new-journal.jsonl"
    reader = source_reader(kind, tmp_path, journal)
    contract = {"R0": {"literal_bootstrap_files": [
        {"relative_path": name, "max_bytes": 1024,
         "expected_sha256": producer.sha(b'{}\n')} for name in names
    ]}}
    register = producer.register if kind == "producer" else independent.build_registry
    with pytest.raises(KeyError, match="context") as stopped:
        register(reader, contract)
    assert len(reader.failures) == 1
    failure = reader.failures[0]
    assert failure["path"] == names[0] and failure["attempt_ordinal"] == 1
    assert failure["stage"] == "source_validation"
    assert failure["returned_bytes"] == 3 and failure["changed_fields"] == []
    assert failure["before"] == failure["after"] == failure["closing"]
    assert failure["primary_reason"] == str(stopped.value)
    assert json.loads(journal.read_bytes().splitlines()[-1]) == failure


@pytest.mark.parametrize("kind", ["producer", "independent"])
@pytest.mark.parametrize("fault", ["progress", "unit"])
def test_r0_ledger_validation_keeps_its_source_context(tmp_path, kind, fault):
    folder = "new-ledger"
    context = "a" * 64
    unit = {"version": "bad" if fault == "unit" else "topolab.b4.unit.v1",
            "context_sha256": context, "unit": "new-unit", "previous_sha256": "0" * 64,
            "payload": {}}
    progress = {"version": "bad" if fault == "progress" else "topolab.b4.progress.v1",
                "context_sha256": context,
                "units_sha256": producer.sha(producer.canonical(["new-unit"])),
                "completed": 1, "attempted": 1, "active_at": None, "pending": None,
                "integrity_failed": False, "resource_failed": False,
                "head_sha256": producer.sha(producer.canonical(unit))}
    summary = {key: progress[key]
               for key in ("context_sha256", "completed", "attempted", "head_sha256")}
    for name, value in [("progress.json", progress), ("summary.json", summary),
                        ("units/0000.json", unit)]:
        producer.new_file(tmp_path / folder / name, producer.canonical(value))
    journal = tmp_path / "new-journal.jsonl"
    reader = source_reader(kind, tmp_path, journal)
    progress = reader.packet(folder + "/progress.json", 1024)
    summary = reader.packet(folder + "/summary.json", 1024)
    with pytest.raises(ValueError):
        if kind == "producer":
            producer.units(reader, folder, progress, context, ["new-unit"])
        else:
            independent.closed_units(reader, folder, context, ["new-unit"], progress, summary)
    assert len(reader.failures) == 1
    failure = reader.failures[0]
    assert failure["path"] == folder + ("/progress.json" if fault == "progress"
                                        else "/units/0000.json")
    assert failure["stage"] == "source_validation"
    assert failure["returned_bytes"] > 0 and failure["changed_fields"] == []
    assert failure["declared"] == failure["before"] == failure["after"] == failure["closing"]
    assert json.loads(journal.read_bytes().splitlines()[-1]) == failure


@pytest.mark.parametrize("fault", ["selection", "summary", "selection_reference"])
def test_r0_registered_field_stop_keeps_source_context(tmp_path, fault):
    fixture = load("test_p17_m2_input_export", "tests")
    contract = fixture.source_metadata(tmp_path)
    if fault in ("selection", "selection_reference"):
        fit_path = tmp_path / "b3-v1-fits/b3_training.json"
        fits = json.loads(fit_path.read_bytes())
        selection = fits["outcomes"][0]["selection"]
        folder = "b3-v1-fits/artifacts/selection/"
        packet = json.loads((tmp_path / (folder + selection["sha256"] + ".json")).read_bytes())
        packet["seed"] = -1
        raw = producer.canonical(packet)
        selection.update(sha256=producer.sha(raw), byte_size=len(raw))
        source = folder + selection["sha256"] + ".json"
        producer.new_file(tmp_path / source, raw)
        if fault == "selection_reference":
            selection["byte_size"] = 0
            source = "b3-v1-fits/b3_training.json"
        fit_path.write_bytes(producer.canonical(fits))
    else:
        source = "b4-5-weighted-terminal/fit/summary.json"
        summary = json.loads((tmp_path / source).read_bytes())
        summary["context_sha256"] = "0" * 64
        (tmp_path / source).write_bytes(producer.canonical(summary))
    for item in contract["R0"]["literal_bootstrap_files"]:
        item["expected_sha256"] = producer.sha((tmp_path / item["relative_path"]).read_bytes())
    journal = tmp_path / "new-journal.jsonl"
    reader = source_reader("producer", tmp_path, journal)
    with pytest.raises(ValueError, match="fixed selection|W summary|artifact identity"):
        producer.register(reader, contract)
    assert len(reader.failures) == 1
    failure = reader.failures[0]
    assert failure["path"] == source and failure["stage"] == "source_validation"
    assert failure["returned_bytes"] == (tmp_path / source).stat().st_size
    assert failure["declared"] == failure["before"] == failure["after"] == failure["closing"]
    assert json.loads(journal.read_bytes().splitlines()[-1]) == failure


def payload_registry(root, fault):
    registry = {"models": [], "labels": [], "scalars": []}
    for ordinal in range(12):
        model = {"family": "P", "seed": 17 + ordinal, "epoch": 1,
                 "context_sha256": "d" * 64, "selection": {}}
        raw = b"bad" if fault == "checkpoint" and ordinal == 0 else independent.public_model(model)
        name = f"model-{ordinal}.safetensors"
        producer.new_file(root / name, raw)
        model["checkpoint"] = producer.ref(name, raw)
        registry["models"].append(model)
    for ordinal in range(528):
        label = independent.public_label((12, 6, 3), ordinal + 1)
        if fault == "label" and ordinal == 0:
            label["stored"]["design_density"][0] = 0.1  # Finite, but not exact float32.
        raw = producer.canonical(label)
        name = f"label-{ordinal}.json"
        producer.new_file(root / name, raw)
        registry["labels"].append({
            "case_id": label["entry"]["case"]["case_id"], "entry": label["entry"],
            "context_sha256": producer.sha(producer.canonical(label["context"])),
            "manifest_sha256": label["manifest_sha256"],
            "source_revision": label["context"]["source_revision"],
            "artifact": producer.ref(name, raw),
        })
    for ordinal in range(18):
        packet = {"version": "topolab.b4_30.z-reflection-repair.v2", "case_id": "public",
                  "context_sha256": "f" * 64, "policy": "uniform", "outcome": {
                      "method": "uniform", "seed": None, "route": "baseline", "fallback": None,
                      "attempt": {"succeeded": True, "failure_code": None, "failure_type": None,
                                  "metrics": {"final_compliance": 7.25},
                                  "state": {"result": {"compliance": 8.0 if fault == "scalar"
                                                       and ordinal == 0 else 7.25}}}}}
        raw = producer.canonical(packet)
        name = f"scalar-{ordinal}.json"
        producer.new_file(root / name, raw)
        registry["scalars"].append({"case_id": "public", "context_sha256": "f" * 64,
                                    "unit": {}, "packet": producer.ref(name, raw)})
    return registry


@pytest.mark.parametrize("kind", ["producer", "independent"])
@pytest.mark.parametrize("fault,source", [
    ("checkpoint", "model-0.safetensors"),
    ("label", "label-0.json"),
    ("scalar", "scalar-0.json"),
])
def test_r1_field_stop_keeps_original_read_context(tmp_path, kind, fault, source):
    originals, output = tmp_path / "new-sources", tmp_path / "new-exports"
    registry = payload_registry(originals, fault)
    journal = tmp_path / "new-journal.jsonl"
    reader = source_reader(kind, originals, journal)
    if kind == "independent":
        # Valid new exports from the real producer; no old source or formal entrypoint.
        valid = tmp_path / "new-valid-sources"
        valid_registry = payload_registry(valid, None)
        producer.export(producer.Reader(valid), valid_registry,
                        json.loads(producer.CONTRACT.read_bytes()), output)
    with pytest.raises(ValueError) as stopped:
        if kind == "producer":
            producer.export(reader, registry, json.loads(producer.CONTRACT.read_bytes()), output)
        else:
            independent.audit_exports(reader, independent.OnceReader(output, 1100, 10**8), registry)
    assert len(reader.failures) == 1
    failure = reader.failures[0]
    assert failure["path"] == source
    assert failure["stage"] == "source_validation"
    assert failure["status"] == "STOP_NO_RETRY"
    assert failure["returned_bytes"] == (originals / source).stat().st_size
    assert failure["declared"] == failure["before"] == failure["after"] == failure["closing"]
    assert failure["changed_fields"] == []
    assert failure["primary_reason"] == str(stopped.value)
    assert json.loads(journal.read_bytes().splitlines()[-1]) == failure
