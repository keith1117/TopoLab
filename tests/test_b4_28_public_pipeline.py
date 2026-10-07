"""Full public synthetic panel; production readers and release are never called."""

import json
import sys
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import b4_28_active_set_numerical_evidence as candidate  # noqa: E402
import b4_28_independent_audit as independent  # noqa: E402
from b4_28_common import Journal, canonical, entries, plan_payload  # noqa: E402

from topolab.baselines import _case_system
from topolab.experiment import ExperimentCase


def public_fixture():
    template = entries()[0].case.problem
    cases, records, labels, setup, rows = [], {}, [], [], []
    for number in range(8):
        mesh = (
            template.mesh
            if number == 0
            else template.mesh.model_copy(update={"element_counts": (2, 2, 2)})
        )
        settings = template.optimization.model_copy(update={"volume_fraction": 0.4 + 0.01 * number})
        loads = (
            template.loads
            if number == 0
            else tuple(load.model_copy(update={"node": 14}) for load in template.loads)
        )
        case = ExperimentCase.from_problem(
            template.model_copy(update={"mesh": mesh, "loads": loads, "optimization": settings})
        )
        entry = SimpleNamespace(case=case)
        cases.append(entry)
        system, loads, constrained = _case_system(case)
        matrix, sums, operator, weights = independent.independent_filter(
            system, settings.filter_radius
        )
        anchor = np.full(system.element_dofs.shape[0], settings.volume_fraction)
        physical = np.asarray(operator @ anchor)
        stored = physical.astype(np.float32).astype(np.float64)
        cs = independent.energy(case, stored, system, loads, constrained)
        cc = independent.energy(case, physical, system, loads, constrained)
        signed = np.asarray(matrix.T @ (cc[1] / sums)) / cs[0]
        artifact = {"public_synthetic_case": case.case_id}
        records[case.case_id] = (
            SimpleNamespace(
                stored=SimpleNamespace(
                    design_density=anchor.tolist(),
                    physical_density=stored.tolist(),
                    compliance=cs[0],
                )
            ),
            artifact,
        )
        labels.append(
            {
                "case_id": case.case_id,
                "artifact": artifact,
                "normalizer": cs[0],
                "anchor": anchor.tolist(),
                "stored_physical": stored.tolist(),
                "continuous_physical": physical.tolist(),
                "stored_compliance": cs[0],
                "continuous_compliance": cc[0],
                "intercept": cc[0] / cs[0],
                "design_gradient": signed.tolist(),
                "old_equality_rejects_new_anchor": not bool(
                    np.isclose(cc[0], cs[0], rtol=1e-9, atol=0)
                ),
            }
        )
        setup.append(
            {
                "case_id": case.case_id,
                "wall_seconds": 0.1,
                "cpu_seconds": 0.05,
                "retained_array_bytes": sum(
                    a.nbytes
                    for a in (anchor, signed, sums, matrix.data, matrix.indices, matrix.indptr)
                ),
            }
        )

        def own_state(
            raw,
            case=case,
            operator=operator,
            weights=weights,
            settings=settings,
            system=system,
            loads=loads,
            constrained=constrained,
            signed=signed,
            cs=cs,
            cc=cc,
            anchor=anchor,
            matrix=matrix,
            sums=sums,
        ):
            design, rho, free, info = independent.root(
                raw, operator, weights, settings.volume_fraction, settings.minimum_density
            )
            exact = independent.energy(case, rho, system, loads, constrained)
            gradient = independent.cotangent(signed, weights, free)
            exact_gradient = independent.cotangent(
                np.asarray(matrix.T @ (exact[1] / sums)) / cs[0], weights, free
            )
            return {
                "design": design.tolist(),
                "physical": rho.tolist(),
                "free": free.tolist(),
                "projection": info,
                "surrogate": cc[0] / cs[0] + float(signed @ (design - anchor)),
                "gradient": gradient.tolist(),
                "exact": exact[0] / cs[0],
                "exact_gradient": exact_gradient.tolist(),
                "physics": {
                    "design": design.tolist(),
                    "physical": rho.tolist(),
                    "free": free.tolist(),
                    "projection": info,
                },
            }

        for state, raw in enumerate(candidate.states(anchor, settings.volume_fraction)):
            value = own_state(raw)
            if state == 8:
                spec = ["uniform", 0.0, "none", 0]
            else:
                spec = [
                    "local" if state < 4 else "outside",
                    0.001 if state < 4 else 0.05,
                    "sine" if state % 4 < 2 else "cosine",
                    1 if state % 2 == 0 else -1,
                ]
            metrics = independent.fidelity(
                value["surrogate"],
                value["exact"],
                np.asarray(value["gradient"]),
                np.asarray(value["exact_gradient"]),
            )
            accepted = (
                metrics["normalized_value_error"] <= 1e-4
                and metrics["increment_relative_error"] <= 0.25
                and metrics["gradient_relative_error"] <= 0.25
                and metrics["increment_sign_agrees"]
            )
            row = {
                "case_id": case.case_id,
                "state": state,
                "spec": spec,
                "raw": raw.tolist(),
                "scale": "small" if raw.size == 216 else "large",
                **value,
                "timings": [
                    {"repeat": j, "wall_seconds": 0.01 + j * 0.001, "cpu_seconds": 0.005}
                    for j in range(3)
                ],
                "repeat_values": [value["surrogate"]] * 3,
                "repeat_gradient_max_difference": 0,
                "fidelity": metrics,
                "local_pass": bool(accepted) if state < 4 else None,
                "maximum_design_distance": float(np.max(abs(np.asarray(value["design"]) - anchor))),
                "maximum_physical_distance": float(
                    np.max(abs(np.asarray(value["physical"]) - stored))
                ),
                "volume_error": abs(float(np.mean(value["physical"])) - settings.volume_fraction),
                "gradient_shift_sum": float(sum(value["gradient"])),
                "differences": [],
            }
            if state in (0, 4):
                for name in ("sine", "cosine"):
                    d = candidate.direction(raw.size, name)
                    for h in (1e-4, 2e-4):
                        sides = [own_state(raw + sign * h * d) for sign in (1, -1)]
                        fd = (sides[0]["surrogate"] - sides[1]["surrogate"]) / (2 * h)
                        derivative = float(np.asarray(value["gradient"]) @ d)
                        row["differences"].append(
                            {
                                "direction": name,
                                "step": h,
                                "sides": sides,
                                "surrogate_fd": fd,
                                "surrogate_derivative": derivative,
                                "surrogate_error": abs(fd - derivative)
                                / max(abs(fd), abs(derivative), 1e-8),
                                "same_active_set": all(
                                    side["free"] == value["free"] for side in sides
                                ),
                                "exact_fd": (sides[0]["exact"] - sides[1]["exact"]) / (2 * h),
                                "exact_derivative": float(np.asarray(value["exact_gradient"]) @ d),
                            }
                        )
            rows.append(row)
    return cases, records, {"labels": labels, "setup": setup, "rows": rows}


def test_entire_public_fixture_pipeline_has_all_states_calls_and_legacy_fields(
    tmp_path, monkeypatch
):
    cases, records, legacy = public_fixture()
    monkeypatch.setattr(candidate, "entries", lambda: cases)
    monkeypatch.setattr(independent, "entries", lambda: cases)
    # An explicit in-memory fixture adapter; no B3 index, artifact or production
    # release reader is reachable from these directly called software functions.
    monkeypatch.setattr(
        candidate, "train_label", lambda _data, _index, entry: records[entry.case.case_id]
    )
    monkeypatch.setattr(
        independent, "train_label", lambda _data, _index, entry: records[entry.case.case_id]
    )
    journal = Journal(tmp_path / "producer.jsonl", "a" * 40)
    produced = candidate.producer(None, legacy, None, journal, perf_counter())
    journal.close()
    assert {k: c["completed"] for k, c in journal.counts.items()} == {
        "label": 8,
        "fem": 16,
        "projection": 400,
        "pointwise": 200,
        "interval": 64,
    }
    produced.update(
        plan=plan_payload(), legacy_condition_results=[True] * 3976, legacy_failed_positions=[]
    )
    produced = json.loads(canonical(produced))
    # After production in this public fixture, independently rebuilding physics
    # must not call any candidate evidence/projection/tangent implementation.
    import pytest

    for name in ("check_interval", "certify_interval", "pointwise", "trace_interval"):
        if hasattr(candidate, name):
            monkeypatch.setattr(candidate, name, lambda *_a, **_k: pytest.fail("candidate called"))
    journal = Journal(tmp_path / "independent.jsonl", "a" * 40)
    result = independent.audit(
        produced,
        legacy,
        {"condition_results": [True] * 3976, "failed_condition_indices": []},
        None,
        None,
        journal,
        perf_counter(),
    )
    journal.close()
    assert result["integrity_passed"]
    assert len(result["new_predicates"]) == 3232 and all(result["new_predicates"])
    assert result["legacy_arithmetic_conditions"] == 960
    assert {k: c["completed"] for k, c in journal.counts.items()} == {
        "label": 8,
        "fem": 216,
        "projection": 200,
        "pointwise": 200,
        "interval": 64,
    }
    assert len(result["local_states"]) == 32 and len(result["intervals"]) == 64
    assert len(result["central_diagnostics"]) == 72
    assert sum(r["region"] == "outside" for r in result["central_diagnostics"]) == 32
    assert sum(r["region"] == "uniform" for r in result["central_diagnostics"]) == 8
    assert result["full_training_memory"] == "PENDING" and not result["cost_feasible"]
