"""Original public software fixtures; no historical case/model/label is opened."""

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from topolab import p17_m2_homotopy as h
from topolab.b2_12_context_cnn import ContextCNN
from topolab.experiment import ExperimentCase, project_design_density
from topolab.problem import TopologyProblem, solve_problem

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def query(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "scripts"))
    return importlib.import_module("p17_m2_homotopy")


@pytest.fixture
def case():
    raw = json.loads((REPO / "tests/fixtures/p17_m2_public_case.json").read_text())
    return ExperimentCase.from_problem(TopologyProblem.model_validate(raw["problem"]))


def test_plain_driver_matches_original_solver(case):
    raw = np.linspace(0.2, 0.7, 6).reshape(1, 1, 2, 3)
    initial = project_design_density(case, raw).design_density
    witness = h.solve_phases(case, initial, active=False, checkpoint=lambda: None)
    payload = case.problem.model_dump(mode="json")
    payload["initial_density"] = initial.tolist()
    old = solve_problem(
        TopologyProblem.model_validate(payload), termination_policy="physical_plateau"
    )
    assert witness.result.design_density == old.design_density
    assert witness.result.physical_density == old.physical_density
    assert witness.result.compliance == old.compliance
    assert witness.result.converged == old.converged
    assert len(witness.trace) == len(old.history)
    assert witness.result.history == old.history[-11:]
    assert witness.fem_solves == len(witness.trace) + 2
    assert witness.model_dump(mode="json")["schema"] == h.WITNESS_VERSION


def test_real_public_prefix_and_transitions(case):
    initial = np.full(6, 0.47)
    observed = []
    witness = h.solve_phases(case, initial, active=True, checkpoint=lambda: observed.append(1))
    assert len(witness.prefix) == 16
    assert [p.penalty for p in witness.prefix] == [1] * 8 + [2] * 8
    assert [(p.iteration, p.penalty, p.phase_iteration) for p in witness.transitions] == [
        (8, 2, 0),
        (16, 3, 0),
    ]
    assert all(s.penalty == 3 and s.iteration >= 17 for s in witness.recent)
    assert witness.fem_solves == len(witness.trace) + 4
    assert len(observed) >= 2 * len(witness.trace)


def test_p3_window_excludes_prefix_and_entry(case, monkeypatch):
    # Alternating design and constant physical field decouple the two stop
    # signals. The fixed plateau can first certify at p3 update11, global27.
    calls = []

    def analyze(mesh, densities, loads, constrained_dofs, **kwargs):
        calls.append(kwargs["penalty"])
        return SimpleNamespace(
            compliance=1.0,
            sensitivity=-np.ones(6),
            displacements=np.zeros(72),
            reactions=np.zeros(72),
        )

    def update(design, *args, **kwargs):
        return 0.94 - design

    monkeypatch.setattr(h, "evaluate_compliance", analyze)
    monkeypatch.setattr(h, "optimality_criteria_update", update)
    monkeypatch.setattr(h, "apply_density_filter", lambda filt, values: np.full(6, 0.47))
    result = h.solve_phases(case, np.array([0.3, 0.64] * 3), active=True, checkpoint=lambda: None)
    assert len(result.trace) == 27
    assert result.recent[0].iteration == 17
    assert result.recent[-1].phase_iteration == 11
    assert all(s.density_change > 0.01 for s in result.recent)
    assert result.result.converged
    assert calls == [1] * 9 + [2] * 9 + [3] * 13


@pytest.mark.parametrize(
    "field,value", [("max_iterations", 16), ("penalty", 2), ("convergence_tolerance", 0.02)]
)
def test_driver_rejects_changed_fixed_rules(case, field, value):
    changed = case.problem.optimization.model_copy(update={field: value})
    case = case.model_copy(
        update={"problem": case.problem.model_copy(update={"optimization": changed})}
    )
    with pytest.raises(ValueError):
        h.solve_phases(case, np.full(6, 0.47), active=True, checkpoint=lambda: None)


def test_resource_checkpoint_never_swallowed(case):
    def stop():
        raise MemoryError("new public fault")

    with pytest.raises(MemoryError):
        h.solve_phases(case, np.full(6, 0.47), active=True, checkpoint=stop)


def test_activation_boundaries(case):
    # Original public metadata, no historical IDs or stored inputs.
    problem = case.problem.model_copy(
        update={
            "mesh": case.problem.mesh.model_copy(update={"element_counts": (24, 12, 6)}),
        }
    )
    large = case.model_copy(update={"problem": problem})
    assert h.h_active(large, "generalist")
    assert not h.h_active(large, "specialist")
    high = problem.optimization.model_copy(update={"volume_fraction": 0.55})
    assert not h.h_active(
        large.model_copy(
            update={
                "problem": problem.model_copy(update={"optimization": high}),
            }
        ),
        "generalist",
    )
    assert not h.h_active(case, "generalist")


def test_manifest_identity_and_no_discovery(query, tmp_path, monkeypatch):
    assert query.read_public_manifest(
        query.PUBLIC_FIXTURE, query.PUBLIC_FIXTURE_SHA256, expected_bytes=query.PUBLIC_FIXTURE_BYTES
    )
    absent = tmp_path / "old-model-or-index.json"
    with pytest.raises(PermissionError):
        query.read_public_manifest(absent, "0" * 64, expected_bytes=4)
    with pytest.raises(PermissionError):
        query.read_public_manifest(
            query.PUBLIC_FIXTURE, "0" * 64, expected_bytes=query.PUBLIC_FIXTURE_BYTES
        )
    with pytest.raises(PermissionError):
        query.read_public_manifest(
            query.PUBLIC_FIXTURE, query.PUBLIC_FIXTURE_SHA256, expected_bytes=65537
        )
    # Unknown formal modes reject before touching a public or old payload.
    monkeypatch.setattr(query, "read_public_manifest", lambda *a, **k: pytest.fail("read"))
    with pytest.raises(SystemExit):
        query.main(["--preflight", "--output", str(tmp_path / "blocked")])


def test_all19_routes_weights_and_fatal_memory(query, case, monkeypatch):
    from topolab import b2_5_evaluation as inference
    from topolab import b3_queries

    assert len(query.METHODS) == len(set(query.METHODS)) == 19
    monkeypatch.setattr(b3_queries, "policy_route", lambda c, m: "generalist")
    objects = {(r, s): object() for r in ("C", "P", "W", "S") for s in (17, 29, 43)}
    assert query._selected(case, "H/17", objects)[1:] == ("P", 17, objects[("P", 17)])
    assert query._selected(case, "W/29", objects)[1:] == ("W", 29, objects[("W", 29)])
    monkeypatch.setattr(b3_queries, "policy_route", lambda c, m: "specialist")
    assert query._selected(case, "P-keep/43", objects)[1:] == ("S", 43, objects[("S", 43)])
    monkeypatch.setattr(b3_queries, "policy_route", lambda c, m: "generalist")

    def memory(*args, **kwargs):
        raise MemoryError("new public inference failure")

    monkeypatch.setattr(inference, "_predict", memory)
    with pytest.raises(MemoryError):
        query.evaluate_query(case, "H/17", None, objects, None, lambda: None)


def test_public_model_inference_plain_h_equivalence(query, case, monkeypatch):
    from topolab import b3_queries

    monkeypatch.setattr(b3_queries, "policy_route", lambda c, m: "generalist")
    torch.manual_seed(17)
    models = {("P", 17): ContextCNN()}
    plain = query.evaluate_query(case, "P/17", None, models, None, lambda: None)
    homotopy = query.evaluate_query(case, "H/17", None, models, None, lambda: None)
    assert not homotopy["homotopy_active"]
    assert homotopy["attempt"]["legacy_witness"] == plain["attempt"]["legacy_witness"]
    assert homotopy["attempt"]["succeeded"] == plain["attempt"]["succeeded"]
    assert homotopy["charged_seconds"] == homotopy["wall_seconds"] + 1


def test_new_public_manifest_nn_and_active_query(query, case, monkeypatch):
    from topolab import b3_queries

    manifest = query.public_asset_specification(case)
    models, neighbors, identities = query.public_assets(case, manifest)
    assert len(models) == len(identities) == 12
    assert neighbors.input_tensors.shape[1] == 10
    assert neighbors.query(case).case_id == case.case_id
    with pytest.raises(PermissionError):
        query.public_assets(case, {**manifest, "old_index": "forbidden"})
    monkeypatch.setattr(b3_queries, "policy_route", lambda c, m: "generalist")
    # Exercise actual composition on NEW tiny data; production activation tests
    # above separately retain the unchanged fixed large-mesh domain.
    monkeypatch.setattr(h, "h_active", lambda c, r: r == "generalist")
    outcome = query.evaluate_query(case, "H/17", None, models, neighbors, lambda: None)
    assert outcome["homotopy_active"]
    assert len(outcome["attempt"]["phase_witness"]["prefix"]) == 16
    assert outcome["selected_recipe"] == "P" and outcome["seed"] == 17
    uniform = query.evaluate_query(case, "uniform-homotopy", None, models, neighbors, lambda: None)
    assert len(uniform["attempt"]["phase_witness"]["prefix"]) == 16
    assert np.allclose(
        uniform["attempt"]["phase_witness"]["initial"]["design_density"], 0.47, rtol=0, atol=1e-6
    )


def test_atomic_record_never_overwrites(query, tmp_path):
    path = tmp_path / "new.json"
    query.atomic_new(path, {"complete": True})
    with pytest.raises(FileExistsError):
        query.atomic_new(path, {"complete": False})
    assert json.loads(path.read_text()) == {"complete": True}
    assert not list(tmp_path.glob("*.pending-*"))


def test_failed_control_retains_its_terminal_and_paid_fallback(query, case, monkeypatch):
    from topolab import b3_queries

    monkeypatch.setattr(b3_queries, "policy_route", lambda c, m: "generalist")
    torch.manual_seed(17)
    models = {("P", 17): ContextCNN()}
    failed = query.evaluate_query(case, "P/17", 1e-15, models, None, lambda: None)
    assert failed["attempt"]["succeeded"] is False
    assert failed["attempt"]["failure_code"] == "quality_error"
    assert failed["attempt"]["legacy_witness"] is not None
    assert failed["fallback"] is not None
    assert failed["fallback"]["legacy_witness"] is not None
    assert failed["wall_seconds"] >= sum(
        failed[name]["wall_seconds"] for name in ("attempt", "fallback")
    )
