import hashlib

import pytest

from topolab.b3_access import B3Access, B3ArtifactReference
from topolab.b3_catalog import build_b3_case_catalog
from topolab.experiment import ExperimentCase
from topolab.problem import TopologyProblem

_BYTES = b"synthetic artifact; no numerical result"
_SHA = hashlib.sha256(_BYTES).hexdigest()


def _reference(entry, kind="label"):
    return B3ArtifactReference(entry=entry, kind=kind, artifact_sha256=_SHA, origins=(entry.case,))


@pytest.mark.parametrize(
    "consumer", ("planning", "data_audit", "fitting", "screen", "nearest_neighbor", "final_query")
)
@pytest.mark.parametrize(
    "role", ("train", "fit_validation", "screen_validation", "final_id", "final_ood")
)
@pytest.mark.parametrize("kind", ("label", "reference", "outcome"))
def test_byte_permission_matrix_rejects_before_opener(consumer, role, kind) -> None:
    access = B3Access(consumer=consumer, training_set="base" if consumer == "fitting" else None)
    entry = build_b3_case_catalog().for_role(role)[0]
    if role == "train":
        entry = build_b3_case_catalog().for_training_set("base")[0]
    reference = _reference(entry, kind)
    calls = []

    def opener(ref):
        calls.append(ref)
        return _BYTES

    permitted = (
        (consumer == "data_audit" and kind == "label" and role in ("train", "fit_validation"))
        or (consumer == "data_audit" and kind == "reference" and role == "screen_validation")
        or (consumer == "fitting" and kind == "label" and role in ("train", "fit_validation"))
        or (consumer == "screen" and kind == "outcome" and role == "screen_validation")
        or (consumer == "final_query" and kind == "outcome" and role in ("final_id", "final_ood"))
    )
    if permitted:
        assert access.read_artifact(reference, opener) == _BYTES
        assert calls == [reference]
    else:
        with pytest.raises(PermissionError):
            access.read_artifact(reference, opener)
        assert calls == []


def test_fitting_scopes_and_specialist_metric_subset() -> None:
    catalog = build_b3_case_catalog()
    for membership, train_count, fit_count in (
        ("base", 468, 32),
        ("expanded", 508, 32),
        ("specialist", 488, 4),
    ):
        access = B3Access(consumer="fitting", training_set=membership)
        entries = access.case_entries()
        assert sum(e.role == "train" for e in entries) == train_count
        assert sum(e.role == "fit_validation" for e in entries) == fit_count
        calls = []
        for entry in catalog.for_role("train"):
            if membership not in entry.training_sets:
                with pytest.raises(PermissionError):
                    access.read_artifact(
                        _reference(entry), lambda ref, calls=calls: calls.append(ref)
                    )
        assert calls == []
    specialist = B3Access(consumer="fitting", training_set="specialist")
    for entry in catalog.for_role("fit_validation"):
        eligible = (
            entry.case.problem.loads[0].direction == "y"
            and entry.case.problem.optimization.volume_fraction == 0.5951
        )
        if eligible:
            assert specialist.read_artifact(_reference(entry), lambda ref: _BYTES) == _BYTES
        else:
            with pytest.raises(PermissionError):
                specialist.read_artifact(_reference(entry), lambda ref: pytest.fail("opened label"))


def test_nn_requires_exact_complete_train_population_before_first_read() -> None:
    access = B3Access(consumer="nearest_neighbor")
    entries = access.case_entries()
    assert len(entries) == 528
    refs = tuple(_reference(entry) for entry in entries)
    calls = []

    def opener(ref):
        calls.append(ref.entry.case.case_id)
        return _BYTES

    for bad in (
        refs[:-1],
        (*refs, refs[0]),
        (*refs[:-1], _reference(build_b3_case_catalog().for_role("final_id")[0])),
    ):
        with pytest.raises((ValueError, PermissionError)):
            access.read_population(bad, "label", opener)
        assert calls == []
    assert access.read_population(reversed(refs), "label", opener) == (_BYTES,) * 528
    assert calls == sorted(ref.entry.case.case_id for ref in refs)


def test_data_audit_complete_label_and_screen_reference_populations() -> None:
    access = B3Access(consumer="data_audit")
    for kind, expected_count in (("label", 560), ("reference", 48)):
        refs = tuple(
            _reference(e, kind)
            for e in access.case_entries()
            if (kind == "label" and e.role != "screen_validation")
            or (kind == "reference" and e.role == "screen_validation")
        )
        assert len(refs) == expected_count
        assert len(access.read_population(refs, kind, lambda ref: _BYTES)) == expected_count


def test_planning_and_screen_reference_metadata_never_open_bytes() -> None:
    planning = B3Access(consumer="planning")
    assert len(planning.case_entries()) == 752
    final = _reference(build_b3_case_catalog().for_role("final_id")[0])
    assert planning.reference_metadata(final) == final
    with pytest.raises(PermissionError):
        planning.read_artifact(final, lambda ref: pytest.fail("opened final label"))
    screen = B3Access(consumer="screen")
    reference = _reference(screen.case_entries()[0], "reference")
    assert screen.reference_metadata(reference) == reference
    with pytest.raises(PermissionError):
        screen.read_artifact(reference, lambda ref: pytest.fail("opened reference bytes"))


@pytest.mark.parametrize(
    "change",
    (
        "role",
        "source",
        "membership",
        "fingerprint",
        "catalog",
        "exposure",
        "missing_origin",
        "final_origin",
        "budget_origin",
    ),
)
def test_forged_and_derived_metadata_rejected_before_artifact_read(change: str) -> None:
    entry = build_b3_case_catalog().for_training_set("base")[0]
    reference = _reference(entry)
    updates = {}
    if change == "role":
        updates["entry"] = entry.model_copy(
            update={"role": "final_id", "source_case_id": None, "training_sets": ()}
        )
    elif change == "source":
        updates["entry"] = entry.model_copy(update={"source_case_id": "tlcase-v1-" + "0" * 64})
    elif change == "membership":
        updates["entry"] = entry.model_copy(update={"training_sets": ("expanded",)})
    elif change == "fingerprint":
        updates["entry"] = entry.model_copy(update={"physical_fingerprint": "0" * 64})
    elif change == "catalog":
        updates["catalog_sha256"] = "0" * 64
    elif change == "exposure":
        updates["exposure_sha256"] = "0" * 64
    elif change == "missing_origin":
        updates["origins"] = ()
    elif change == "final_origin":
        updates["origins"] = (build_b3_case_catalog().for_role("final_id")[0].case,)
    else:
        problem = entry.case.problem.model_dump(mode="json")
        problem["optimization"]["max_iterations"] = 240
        source = ExperimentCase.from_problem(TopologyProblem.model_validate(problem))
        updates["origins"] = (source,)
    forged = reference.model_copy(update=updates)
    access = B3Access(consumer="fitting", training_set="base")
    with pytest.raises(ValueError):
        access.read_artifact(forged, lambda ref: pytest.fail("opened forged artifact"))


def test_wrong_checksum_and_invalid_consumer_scope() -> None:
    entry = build_b3_case_catalog().for_training_set("base")[0]
    access = B3Access(consumer="fitting", training_set="base")
    with pytest.raises(ValueError, match="checksum"):
        access.read_artifact(_reference(entry), lambda ref: b"changed bytes")
    with pytest.raises(ValueError, match="training_set"):
        B3Access(consumer="fitting")
    with pytest.raises(ValueError, match="training_set"):
        B3Access(consumer="screen", training_set="base")


def test_streaming_population_authorizes_all_metadata_before_lazy_reads() -> None:
    access = B3Access(consumer="nearest_neighbor")
    references = tuple(_reference(e) for e in access.case_entries())
    opened = []

    def opener(ref):
        opened.append(ref.entry.case.case_id)
        return _BYTES

    with pytest.raises(ValueError, match="population"):
        access.iter_population(references[:-1], "label", opener)
    assert not opened
    stream = access.iter_population(references, "label", opener)
    assert not opened
    assert next(stream) == _BYTES and len(opened) == 1
    assert len(tuple(stream)) == 527 and len(opened) == 528
