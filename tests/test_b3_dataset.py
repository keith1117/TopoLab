"""B3 provenance and numerical label/reference contracts, without B3 optimization."""

from collections import Counter

import numpy as np
import pytest
from pydantic import ValidationError

import topolab.b2_4_labels as uniform
import topolab.b3_dataset as dataset
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_dataset import B3DataContext, B3DatasetManifest, B3LabelRecord, B3ReferenceRecord
from topolab.experiment import project_design_density


def test_manifest_population_and_roundtrip(b3_manifest):  # type: ignore[no-untyped-def]
    restored = B3DatasetManifest.model_validate_json(
        canonical_metadata_bytes(b3_manifest.model_dump(mode="json"))
    )
    assert restored == b3_manifest
    assert restored.sha256() == b3_manifest.sha256()
    assert len(restored.catalog.entries) == 752
    assert Counter(e.role for e in restored.data_entries()) == {
        "train": 528,
        "fit_validation": 32,
        "screen_validation": 48,
    }
    assert all(e.case.problem.optimization.max_iterations == 360 for e in restored.data_entries())
    assert all(e.case.problem.initial_density is None for e in restored.data_entries())


@pytest.mark.parametrize(
    "field,value",
    [
        ("numerical_source_anchor", "b" * 40),
        ("contract_sha256", "b" * 64),
        ("catalog_sha256", "b" * 64),
        ("exposure_sha256", "b" * 64),
        ("source_tree_clean", False),
        ("source_revision", "not-a-revision"),
    ],
)
def test_context_rejects_changed_bindings(b3_manifest, field, value):  # type: ignore[no-untyped-def]
    payload = b3_manifest.context.model_dump(mode="json")
    payload[field] = value
    with pytest.raises(ValidationError):
        B3DataContext.model_validate(payload)


@pytest.mark.parametrize(
    "section,field,value",
    [
        ("environment", "python_version", "3.12.11"),
        ("environment", "lockfile_sha256", "b" * 64),
        ("runtime", "cpu", "Apple M3"),
        ("runtime", "machine", "x86_64"),
        ("runtime", "blas_threads", 2),
        ("runtime", "torch_interop_threads", 1),
    ],
)
def test_context_rejects_changed_execution(b3_manifest, section, field, value):  # type: ignore[no-untyped-def]
    payload = b3_manifest.context.model_dump(mode="json")
    payload[section][field] = value
    with pytest.raises(ValidationError):
        B3DataContext.model_validate(payload)


def test_separate_full_precision_and_stored_state_audits(b3_label, b3_reference):  # type: ignore[no-untyped-def]
    assert (
        B3LabelRecord.model_validate_json(
            canonical_metadata_bytes(b3_label.model_dump(mode="json"))
        )
        == b3_label
    )
    assert "stored" not in b3_reference.model_dump()
    assert b3_label.stored.compliance != b3_label.result.compliance
    assert b3_label.stored.design_density != b3_label.result.design_density
    dataset.audit_b3_record(b3_label)
    dataset.audit_b3_record(b3_reference)

    # Explicit synthetic eleven-state plateau witness, testing the other stop
    # branch without optimizing a B3 case or claiming a production outcome.
    plateau = b3_label.model_dump(mode="json")
    last = plateau["result"]["history"][-1]
    plateau["result"]["history"] = [
        dict(last, iteration=iteration, density_change=0.02) for iteration in range(1, 12)
    ]
    plateau["stored"].update(
        iterations=11, terminal_density_change=0.02, stop_reason="physical_plateau"
    )
    dataset.audit_b3_record(B3LabelRecord.model_validate(plateau))
    plateau["result"]["history"][0]["compliance"] *= 1.01
    with pytest.raises(ValidationError, match="physical-plateau stop"):
        B3LabelRecord.model_validate(plateau)

    payload = b3_label.model_dump(mode="json")
    payload["result"]["compliance"] *= 1.001
    payload["result"]["history"][-1]["compliance"] = payload["result"]["compliance"]
    with pytest.raises(RuntimeError, match="compliance"):
        dataset.audit_b3_record(B3LabelRecord.model_validate(payload))

    payload = b3_label.model_dump(mode="json")
    payload["stored"]["compliance"] *= 1.001
    with pytest.raises(ValueError, match="stored compliance"):
        dataset.audit_b3_record(B3LabelRecord.model_validate(payload))

    payload = b3_label.model_dump(mode="json")
    weights = payload["stored"]["sensitivity_weight"]
    lo, hi = int(np.argmin(weights)), int(np.argmax(weights))
    weights[lo], weights[hi] = weights[hi], weights[lo]
    with pytest.raises(ValueError, match="weights failed independent audit"):
        dataset.audit_b3_record(B3LabelRecord.model_validate(payload))


@pytest.mark.parametrize(
    "corruption",
    ["float32", "filter", "full_filter", "history_order", "dofs", "stop", "cap", "old_schema"],
)
def test_label_rejects_state_corruption(b3_label, corruption):  # type: ignore[no-untyped-def]
    payload = b3_label.model_dump(mode="json")
    if corruption == "float32":
        payload["stored"]["design_density"][0] += 1e-12
    elif corruption == "filter":
        payload["stored"]["physical_density"][0] = 0.25
    elif corruption == "full_filter":
        payload["result"]["physical_density"][0] += 1e-6
        payload["result"]["history"][-1]["physical_density"][0] += 1e-6
    elif corruption == "history_order":
        payload["result"]["history"][0]["iteration"] = 2
    elif corruption == "dofs":
        payload["result"]["reactions"] = []
    elif corruption == "stop":
        payload["result"]["history"][0]["density_change"] = 0.02
    elif corruption == "cap":
        payload["entry"]["case"]["problem"]["optimization"]["max_iterations"] = 240
    elif corruption == "old_schema":
        payload["label_version"] = "topolab.b2_3.label.v1"
    with pytest.raises(ValidationError):
        B3LabelRecord.model_validate(payload)


def test_reference_and_label_role_boundaries(b3_label, b3_reference):  # type: ignore[no-untyped-def]
    payload = b3_reference.model_dump(mode="json")
    payload["entry"] = b3_label.entry.model_dump(mode="json")
    with pytest.raises(ValidationError):
        B3ReferenceRecord.model_validate(payload)


def test_generator_forbids_final_and_forged_entry_before_solver(b3_manifest, monkeypatch):  # type: ignore[no-untyped-def]
    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("forbidden case reached numerical generation")

    monkeypatch.setattr(dataset, "solve_uniform_terminal", forbidden)
    for role in ("final_id", "final_ood"):
        with pytest.raises(PermissionError):
            dataset.generate_b3_record(b3_manifest, b3_manifest.catalog.for_role(role)[0])
    entry = b3_manifest.catalog.for_role("train")[0].model_copy(update={"role": "fit_validation"})
    with pytest.raises((ValueError, PermissionError)):
        dataset.generate_b3_record(b3_manifest, entry)
    final = b3_manifest.catalog.for_role("final_id")[0]
    forged = final.model_copy(update={"role": "train", "training_sets": ("base",)})
    catalog = b3_manifest.catalog.model_copy(update={"entries": (forged,)})
    with pytest.raises(ValueError):
        dataset.generate_b3_record(b3_manifest.model_copy(update={"catalog": catalog}), forged)


def test_generator_wires_frozen_projected_uniform_policy(b3_manifest, b3_label, monkeypatch):  # type: ignore[no-untyped-def]
    calls = []
    callback = lambda state: None  # noqa: E731

    def solve(problem, **kwargs):  # type: ignore[no-untyped-def]
        calls.append((problem, kwargs))
        return b3_label.result

    monkeypatch.setattr(uniform, "solve_problem", solve)
    record = dataset.generate_b3_record(b3_manifest, b3_label.entry, iteration_callback=callback)
    assert record == b3_label
    problem, options = calls[0]
    assert problem.optimization.max_iterations == 360
    assert options == {"termination_policy": "physical_plateau", "iteration_callback": callback}
    nx, ny, nz = problem.mesh.element_counts
    raw = np.full((1, nz, ny, nx), problem.optimization.volume_fraction, dtype=np.float32)
    assert problem.initial_density == tuple(
        project_design_density(b3_label.entry.case, raw).design_density
    )
