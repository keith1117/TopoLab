"""Connected synthetic40/558/1071 pipeline; no historical input or formal CLI."""

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / (name + ".py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def complete_sources(root, checker, monkeypatch):
    """Construct a new closed reference graph from independently authored public bytes."""
    root.mkdir()
    contract = json.loads((REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json")
                          .read_bytes())

    def put(relative, value, *, raw=False):
        data = value if raw else checker.canonical(value)
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
        return {"sha256": checker.digest(data), "byte_size": len(data)}

    entries = [checker.public_label((12, 6, 3) if i < 432 else (24, 12, 6), i + 1)["entry"]
               for i in range(528)]
    source_context = checker.public_label((12, 6, 3))["context"]
    catalog = {"catalog_version": "topolab.b3.catalog.v1", "entries": entries}
    manifest = {"context": source_context, "catalog": catalog}
    manifest_sha = checker.digest(checker.canonical(manifest))
    outcomes = []
    for ordinal, entry in enumerate(entries, 1):
        mesh = tuple(entry["case"]["problem"]["mesh"]["element_counts"])
        label = checker.public_label(mesh, ordinal)
        label["manifest_sha256"] = manifest_sha
        raw = checker.canonical(label)
        digest = checker.digest(raw)
        relative = f"artifacts/label/{entry['case']['case_id']}/{digest}.json"
        put("b3-v1-data/" + relative, raw, raw=True)
        outcomes.append({"entry": entry, "status": "succeeded", "artifact": {
            "access": {"kind": "label", "entry": entry, "artifact_sha256": digest},
            "relative_path": relative, "manifest_sha256": manifest_sha,
            "source_revision": source_context["source_revision"], "byte_size": len(raw),
        }})
    index = {"manifest": manifest, "manifest_sha256": manifest_sha, "entries": outcomes}
    index_sha = checker.digest(checker.canonical(index))
    fit_context = {"data_index": index, "data_index_sha256": index_sha}
    fit_context_sha = checker.digest(checker.canonical(fit_context))
    fits = {"index_version": "topolab.b3.training-index.v1", "context": fit_context,
            "context_sha256": fit_context_sha, "outcomes": []}
    weighted = []
    for row in contract["checkpoints"]["fixed_rows"]:
        family, seed, epoch = row["family"], row["seed"], row["selected_epoch"]
        context = contract["R0"]["W_context_sha256"] if family == "W" else fit_context_sha
        model = {"family": family, "seed": seed, "epoch": epoch, "context_sha256": context}
        raw = checker.public_model(model)
        fitroot = "b4-5-weighted-terminal/fit" if family == "W" else "b3-v1-fits"
        checkpoint = put(f"{fitroot}/artifacts/checkpoint/{checker.digest(raw)}.safetensors",
                         raw, raw=True) | {"kind": "checkpoint"}
        history = {"selection_version": "topolab.b3.selection.v1", "context_sha256": context,
                   "recipe": "P" if family == "W" else family, "seed": seed,
                   "selected_epoch": epoch, "history": [{}], "checkpoint": checkpoint}
        selection = ({"version": "topolab.b4_5.selection.v1",
                      "objective": "topolab.b4_5.weighted-terminal.v1",
                      "history_schema": history, "checkpoint": checkpoint}
                     if family == "W" else history)
        raw = checker.canonical(selection)
        reference = put(f"{fitroot}/artifacts/selection/{checker.digest(raw)}.json", raw,
                        raw=True) | {"kind": "selection"}
        if family == "W":
            weighted.append(reference)
        else:
            fits["outcomes"].append({"recipe": family, "seed": seed, "selection": reference})
    put("b3-v1-fits/b3_training.json", fits)

    def journal(base, context, names, payloads):
        previous = "0" * 64
        for ordinal, (name, payload) in enumerate(zip(names, payloads, strict=True)):
            packet = {"version": "topolab.b4.unit.v1", "unit": name,
                      "context_sha256": context, "previous_sha256": previous, "payload": payload}
            previous = put(f"{base}/units/{ordinal:04d}.json", packet)["sha256"]
        progress = {"version": "topolab.b4.progress.v1", "context_sha256": context,
                    "units_sha256": checker.digest(checker.canonical(names)),
                    "completed": len(names), "attempted": len(names), "active_at": None,
                    "pending": None, "integrity_failed": False, "resource_failed": False,
                    "head_sha256": previous}
        put(base + "/progress.json", progress)
        put(base + "/summary.json", {key: progress[key] for key in (
            "context_sha256", "completed", "attempted", "head_sha256")})

    journal("b4-5-weighted-terminal/fit", contract["R0"]["W_context_sha256"],
            ["W/17", "W/29", "W/43"], weighted)
    base = "b4-30-z-reflection-repair-v2"
    context_sha = put(base + "/context.json", {"public": "entirely new local pipeline fixture"})[
        "sha256"]
    put(base + "/sentinel/independent_audit.json", {"public": "synthetic source marker only"})
    references = []
    for case_id in contract["scalars"]["case_ids"]:
        packet = {"version": "topolab.b4_30.z-reflection-repair.v2", "case_id": case_id,
                  "context_sha256": context_sha, "policy": "uniform", "outcome": {
                      "method": "uniform", "seed": None, "route": "baseline", "fallback": None,
                      "attempt": {"succeeded": True, "failure_code": None, "failure_type": None,
                                  "metrics": {"final_compliance": 7.25},
                                  "state": {"result": {"compliance": 7.25}}}}}
        raw = checker.canonical(packet)
        relative = f"artifacts/outcome/{checker.digest(raw)}.json"
        references.append(put(base + "/sentinel/reference/" + relative, raw, raw=True)
                          | {"path": relative})
    journal(base + "/sentinel/reference", context_sha, contract["scalars"]["case_ids"], references)
    for literal in contract["R0"]["literal_bootstrap_files"]:
        literal["expected_sha256"] = checker.digest((root / literal["relative_path"]).read_bytes())
    contract["R0"]["embedded_B3_data_index_sha256"] = index_sha
    monkeypatch.setattr(checker, "B3_DATA_HASH", index_sha)
    monkeypatch.setattr(checker, "CATALOG_HASH", checker.digest(checker.canonical(catalog)))
    return contract


def sidecar(identity, rows):
    return {"schema": "topolab.v2.m2-source-identity-sidecar.v1",
            "execution_identity": identity, "rows": rows}


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    producer = load("p17_m2_input_export")
    local = load("p17_m2_local_input_version")
    independent = load("p17_m2_local_input_independent")
    checker = independent.base
    sources = tmp_path / "new-public-sources"
    contract = complete_sources(sources, checker, monkeypatch)
    r0 = producer.Reader(sources, execution_identity=local.IDENTITY, source_identity_checks=True)
    registry = producer.register(r0, contract)
    other_r0 = checker.OnceReader(sources, 40, 32 * checker.MIB, source_identity_checks=True)
    expected = checker.build_registry(other_r0, contract)
    assert checker.compare_words(expected, registry) > 6000
    independent.compare_source_sets(sidecar(local.IDENTITY, r0.source_observations),
                                    sidecar(local.IDENTITY, other_r0.observations), "r0")
    content = local.LocalContent(tmp_path / "content", registry, "f" * 64)
    content.write("source_registry.json", producer.canonical(registry))
    r1 = producer.Reader(sources, execution_identity=local.IDENTITY, source_identity_checks=True)
    producer.export(r1, registry, contract, content.root, local_content=content)
    closed = content.finish()
    return producer, local, independent, contract, registry, sources, content, closed, r0, r1


def test_complete_connected_public_pipeline_preserves_40_558_1071_and_independent_values(pipeline):
    producer, local, independent, _, registry, sources, content, closed, r0, r1 = pipeline
    checker = independent.base
    assert len(r0.rows) == 40 and len(r1.rows) == 558
    assert len(closed["manifest"]["members"]) == 1071
    assert not (content.root / "export_manifest.json").exists()
    independent_r1 = checker.OnceReader(
        sources, 558, 852 * checker.MIB, source_identity_checks=True)
    exported = checker.OnceReader(content.root, 1070, 301 * checker.MIB)
    compared = checker.audit_exports(independent_r1, exported, registry)
    assert compared["status"] == "PASS_R1_ALL_SOURCE_FIELDS"
    assert len(independent_r1.table) == 558 and len(exported.table) == 1070
    identity_result = independent.compare_source_sets(
        sidecar(local.IDENTITY, r1.source_observations),
        sidecar(local.IDENTITY, independent_r1.observations), "r1")
    assert identity_result["source_count"] == 558
    result = independent.audit_local_content(content.root, closed["manifest"], registry,
                                              closed["local_identity_rows"], "f" * 64)
    assert result["new_member_reads"] == 1071 and result["old_source_reads"] == 0
    assert result["original_semantics_accepted"] is False
    assert producer.parse((content.root / "uniform-scalars.json").read_bytes())["values"][0][
        "compliance"] == 7.25


def test_connected_pipeline_independent_comparison_rejects_changed_producer_view(pipeline):
    _, _, independent, _, registry, sources, content, _, _, _ = pipeline
    checker = independent.base
    view_path = content.root / "nn/producer" / (registry["labels"][0]["case_id"] + ".json")
    view = checker.parse(view_path.read_bytes())
    view["stored"]["design_density"][0] = 0.25
    view_path.write_bytes(checker.canonical(view))
    independent_sources = checker.OnceReader(sources, 558, 852 * checker.MIB,
                                              source_identity_checks=True)
    with pytest.raises(ValueError):
        checker.audit_exports(independent_sources,
                              checker.OnceReader(content.root, 1070, 301 * checker.MIB), registry)
    assert len(independent_sources.table) == 13


def test_connected_pipeline_same_bytes_with_changed_source_tuple_cannot_accept_version(pipeline):
    import os

    _, local, independent, _, registry, sources, content, _, _, r1 = pipeline
    checker = independent.base
    path = sources / registry["models"][0]["checkpoint"]["path"]
    before = path.stat()
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1))
    independent_sources = checker.OnceReader(sources, 558, 852 * checker.MIB,
                                              source_identity_checks=True)
    compared = checker.audit_exports(
        independent_sources, checker.OnceReader(content.root, 1070, 301 * checker.MIB), registry)
    assert compared["status"] == "PASS_R1_ALL_SOURCE_FIELDS"
    with pytest.raises(ValueError):
        independent.compare_source_sets(sidecar(local.IDENTITY, r1.source_observations),
                                         sidecar(local.IDENTITY, independent_sources.observations),
                                         "r1")
    assert len(independent_sources.table) == 558
