"""New public reference graph, extracted from TopoLab's connected public regression.

No historical payload or scientific model is used. Expected source identities
are local to the explicitly PUBLIC fixture contract, never production globals.
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def create_sources(root, checker):
    """Construct a new closed reference graph from independently authored public bytes."""
    root.mkdir()
    contract = json.loads(
        (REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json").read_bytes()
    )

    def put(relative, value, *, raw=False):
        data = value if raw else checker.canonical(value)
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
        return {"sha256": checker.digest(data), "byte_size": len(data)}

    def maximum_json(value, size):
        # Public-only ignored source field: must never appear in restricted exports.
        value["new_public_ignored_padding"] = ""
        gap = size - len(checker.canonical(value))
        if gap < 0:
            raise ValueError("maximum public object already exceeds cap")
        value["new_public_ignored_padding"] = "x" * gap
        return value

    entries = [
        checker.public_label((12, 6, 3) if i < 432 else (24, 12, 6), i + 1)["entry"]
        for i in range(528)
    ]
    source_context = checker.public_label((12, 6, 3))["context"]
    catalog = {"catalog_version": "topolab.b3.catalog.v1", "entries": entries}
    manifest = {"context": source_context, "catalog": catalog}
    manifest_sha = checker.digest(checker.canonical(manifest))
    outcomes = []
    for ordinal, entry in enumerate(entries, 1):
        mesh = tuple(entry["case"]["problem"]["mesh"]["element_counts"])
        label = checker.public_label(mesh, ordinal)
        label["manifest_sha256"] = manifest_sha
        if ordinal == 433:
            prototype = label["result"]["history"][-1]
            label["result"]["history"] = [dict(prototype, iteration=i) for i in range(1, 361)]
            label["stored"]["iterations"] = 360
            maximum_json(label, 64 * 1048576)
        raw = checker.canonical(label)
        digest = checker.digest(raw)
        relative = f"artifacts/label/{entry['case']['case_id']}/{digest}.json"
        put("b3-v1-data/" + relative, raw, raw=True)
        outcomes.append(
            {
                "entry": entry,
                "status": "succeeded",
                "artifact": {
                    "access": {"kind": "label", "entry": entry, "artifact_sha256": digest},
                    "relative_path": relative,
                    "manifest_sha256": manifest_sha,
                    "source_revision": source_context["source_revision"],
                    "byte_size": len(raw),
                },
            }
        )
    index = {"manifest": manifest, "manifest_sha256": manifest_sha, "entries": outcomes}
    index_sha = checker.digest(checker.canonical(index))
    fit_context = {"data_index": index, "data_index_sha256": index_sha}
    fit_context_sha = checker.digest(checker.canonical(fit_context))
    fits = {
        "index_version": "topolab.b3.training-index.v1",
        "context": fit_context,
        "context_sha256": fit_context_sha,
        "outcomes": [],
    }
    weighted = []
    for row in contract["checkpoints"]["fixed_rows"]:
        family, seed, epoch = row["family"], row["seed"], row["selected_epoch"]
        context = contract["R0"]["W_context_sha256"] if family == "W" else fit_context_sha
        model = {"family": family, "seed": seed, "epoch": epoch, "context_sha256": context}
        raw = checker.public_model(model)
        if family == "C" and seed == 17:
            header_size = int.from_bytes(raw[:8], "little")
            header = raw[8 : 8 + header_size]
            raw = (
                (65536).to_bytes(8, "little")
                + header
                + b" " * (65536 - len(header))
                + raw[8 + header_size :]
            )
        fitroot = "b4-5-weighted-terminal/fit" if family == "W" else "b3-v1-fits"
        checkpoint = put(
            f"{fitroot}/artifacts/checkpoint/{checker.digest(raw)}.safetensors", raw, raw=True
        ) | {"kind": "checkpoint"}
        history = {
            "selection_version": "topolab.b3.selection.v1",
            "context_sha256": context,
            "recipe": "P" if family == "W" else family,
            "seed": seed,
            "selected_epoch": epoch,
            "history": [{}],
            "checkpoint": checkpoint,
        }
        selection = (
            {
                "version": "topolab.b4_5.selection.v1",
                "objective": "topolab.b4_5.weighted-terminal.v1",
                "history_schema": history,
                "checkpoint": checkpoint,
            }
            if family == "W"
            else history
        )
        if family == "C" and seed == 17:
            history["history"] = [{}] * 200
            maximum_json(selection, 256 * 1024)
        raw = checker.canonical(selection)
        reference = put(
            f"{fitroot}/artifacts/selection/{checker.digest(raw)}.json", raw, raw=True
        ) | {"kind": "selection"}
        if family == "W":
            weighted.append(reference)
        else:
            fits["outcomes"].append({"recipe": family, "seed": seed, "selection": reference})
    put("b3-v1-fits/b3_training.json", maximum_json(fits, 16 * 1048576))

    def journal(base, context, names, payloads):
        previous = "0" * 64
        for ordinal, (name, payload) in enumerate(zip(names, payloads, strict=True)):
            packet = {
                "version": "topolab.b4.unit.v1",
                "unit": name,
                "context_sha256": context,
                "previous_sha256": previous,
                "payload": payload,
            }
            if ordinal == 0:
                maximum_json(packet, 32 * 1024)
            previous = put(f"{base}/units/{ordinal:04d}.json", packet)["sha256"]
        progress = {
            "version": "topolab.b4.progress.v1",
            "context_sha256": context,
            "units_sha256": checker.digest(checker.canonical(names)),
            "completed": len(names),
            "attempted": len(names),
            "active_at": None,
            "pending": None,
            "integrity_failed": False,
            "resource_failed": False,
            "head_sha256": previous,
        }
        put(base + "/progress.json", progress)
        put(
            base + "/summary.json",
            {
                key: progress[key]
                for key in ("context_sha256", "completed", "attempted", "head_sha256")
            },
        )

    journal(
        "b4-5-weighted-terminal/fit",
        contract["R0"]["W_context_sha256"],
        ["W/17", "W/29", "W/43"],
        weighted,
    )
    base = "b4-30-z-reflection-repair-v2"
    context_sha = put(
        base + "/context.json",
        maximum_json({"public": "entirely new local pipeline fixture"}, 1048576),
    )["sha256"]
    put(base + "/sentinel/independent_audit.json", {"public": "synthetic source marker only"})
    references = []
    for case_id in contract["scalars"]["case_ids"]:
        packet = {
            "version": "topolab.b4_30.z-reflection-repair.v2",
            "case_id": case_id,
            "context_sha256": context_sha,
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
        if not references:
            maximum_json(packet, 4 * 1048576)
        raw = checker.canonical(packet)
        relative = f"artifacts/outcome/{checker.digest(raw)}.json"
        references.append(
            put(base + "/sentinel/reference/" + relative, raw, raw=True) | {"path": relative}
        )
    journal(base + "/sentinel/reference", context_sha, contract["scalars"]["case_ids"], references)
    for literal in contract["R0"]["literal_bootstrap_files"]:
        literal["expected_sha256"] = checker.digest((root / literal["relative_path"]).read_bytes())
    contract["R0"]["embedded_B3_data_index_sha256"] = index_sha
    return contract, {
        "B3_DATA_HASH": index_sha,
        "CATALOG_HASH": checker.digest(checker.canonical(catalog)),
    }
