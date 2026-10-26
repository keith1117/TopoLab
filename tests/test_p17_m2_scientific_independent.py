"""Original public finite witnesses for the separately authored scientific auditor."""

import importlib.util
import json
import sys
import time
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def checker():
    name = "p17_m2_scientific_independent"
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / (name + ".py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def public_legacy():
    spec = importlib.util.spec_from_file_location(
        "scientific_original_independent_fixtures", REPO / "tests/test_p17_m2_independent_audit.py"
    )
    assert spec and spec.loader
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    case, phase = original.original_public_witness(False)
    return case, {
        "witness_version": "topolab.b3.query-state.v1",
        "trace": [
            {
                key: point[key]
                for key in ("iteration", "compliance", "volume_fraction", "density_change")
            }
            for point in phase["trace"]
        ],
        "result": phase["result"],
    }


def test_ordinary_terminal_is_independently_resolved_inside_twelve_call_partition():
    audit = checker()
    case, witness = public_legacy()
    result = audit.audit_terminal(case, witness, witness["result"]["compliance"], accepted=True)
    assert result["quality_passed"] is True
    assert 1 <= result["audit_fem"] <= 12
    assert result["whole_trajectory_replayed"] is False
    wrong = deepcopy(witness)
    wrong["result"]["reactions"][0] += 1
    with pytest.raises(ValueError, match="terminal reactions differ"):
        audit.audit_terminal(case, wrong, witness["result"]["compliance"], accepted=True)


def test_serialized_b_pass_never_grants_scientific_reader():
    audit = checker()
    with pytest.raises(ValueError, match="actual checked B admission required"):
        audit.grant_scientific_input(None, {}, "scientific-producer", {"status": "PASS"})


def test_serialized_c_return_cannot_release_scientific_lease():
    audit = checker()
    with pytest.raises(ValueError, match="actual checked scientific return required"):
        audit.acknowledge_scientific_reader(None, {}, {"status": "PASS"})


def test_new_public_uniform_query_initialization_and_quality_are_independent():
    audit = checker()
    driver = audit.helper("p17_m2_scientific_control")
    public = audit.helper("p17_m2_homotopy")
    case = public.read_public_manifest(
        public.PUBLIC_FIXTURE,
        public.PUBLIC_FIXTURE_SHA256,
        expected_bytes=public.PUBLIC_FIXTURE_BYTES,
    )
    measured = driver.MeasuredQueries({}, None, checkpoint=lambda: None)
    row = measured.evaluate(case, "uniform")
    reference = row["attempt"]["legacy_witness"]["result"]["compliance"]
    result = audit.audit_query(case, row, reference, models={}, neighbors={}, identities={})
    assert result["attempt_accepted"] is True and result["fallback_occurred"] is False
    corrupt = deepcopy(row)
    corrupt["attempt"]["initialization_witness"]["raw_density"][0] += 0.125
    with pytest.raises(ValueError, match="initialization raw words differ"):
        audit.audit_query(case, corrupt, reference, models={}, neighbors={}, identities={})


def test_contract_argv_hash_placeholder_is_resolved_without_self_reference():
    audit = checker()
    words = [
        "/usr/bin/python3",
        "-I",
        "science.py",
        "--contract-sha",
        "@SCIENTIFIC_CONTRACT_SHA256@",
    ]
    expected = ["/usr/bin/python3", "-I", "science.py", "--contract-sha", "a" * 64]
    assert audit.resolve_argv(words, "a" * 64) == expected
    assert words[-1] == "@SCIENTIFIC_CONTRACT_SHA256@"


def public_metric_panel():
    audit = checker()
    proposal = json.loads(
        (REPO / "docs/planning/p17_m2_native_homotopy_proposal.json").read_bytes()
    )
    ids, methods = (proposal["prospective_pilot"][key] for key in ("case_ids", "methods"))
    negatives = set(proposal["acceptance"]["negative_control_case_ids"])
    target = "tlcase-v1-55c1b3e64135c23125fc286de5d780fc5d9a1e226d5e43ff0dbc8925b423936a"
    rows, historical = [], []
    cases = {}
    for i, case_id in enumerate(ids):
        cases[case_id] = {
            "scale": (24, 12, 6) if i < 13 else (12, 6, 3),
            "direction": "y" if i < 13 else "z",
            "volume": 0.47,
        }
        for seed in (17, 29, 43):
            if case_id != target and not (case_id in negatives and seed == 29):
                historical.append({"case_id": case_id, "seed": seed})
        for method in methods:
            failed = method.startswith(("plain-P/", "P-keep/")) and (
                case_id == target or case_id in negatives and method.endswith("/29")
            )
            failed |= case_id in negatives and method in ("H/29", "C/29", "W/29")
            cost = 100 if method == "uniform" else 80 if method.startswith("H/") else 90
            rows.append(
                {
                    "case_id": case_id,
                    "method": method,
                    "attempt_accepted": not failed,
                    "fallback_occurred": bool(failed),
                    "fallback_accepted": bool(failed),
                    "charged_seconds": cost,
                }
            )
    return audit, proposal, cases, rows, historical


def test_primary_failure_is_not_hidden_by_successful_uniform_fallback():
    audit, proposal, cases, rows, historical = public_metric_panel()
    result = audit.assess_panel(proposal, cases, rows, historical)
    assert result["scientific_predicates_passed"] is True
    primary = next(row for row in rows if row["method"] == "H/17")
    primary.update(attempt_accepted=False, fallback_occurred=True, fallback_accepted=True)
    failed = audit.assess_panel(proposal, cases, rows, historical)
    assert failed["scientific_predicates_passed"] is False
    assert "fixed_H17_zero_failed_attempts_and_fallbacks" in failed["failed_predicates"]


def test_two_seed_gate_keeps_mean_only_while_primary_keeps_separate_cost_sum():
    audit, proposal, cases, rows, historical = public_metric_panel()
    first = {}
    for case_id, metadata in cases.items():
        first.setdefault(metadata["scale"], case_id)
    expensive = set(first.values())
    for row in rows:
        uniform = 1000 if row["case_id"] in expensive else 100
        ratio = (1 if row["method"] == "uniform" else 0.7 if row["method"] == "H/17"
                 else (1.2 if row["case_id"] in expensive else 0.8)
                 if row["method"] == "H/29" else 0.95)
        row["charged_seconds"] = ratio * uniform
    result = audit.assess_panel(proposal, cases, rows, historical)
    assert result["passing_H_seeds"] == [17, 29]
    assert result["scientific_predicates_passed"] is True
    assert result["seed_gate_results"]["H/43"] is False
    assert result["metrics"]["H/29:(12, 6, 3)"]["sum_ratio"] > 0.9
    assert result["metrics"]["H/29:(24, 12, 6)"]["sum_ratio"] > 0.9
    by_key = {(row["case_id"], row["method"]): row for row in rows}
    for case_id in cases:
        h17, h29 = by_key[(case_id, "H/17")], by_key[(case_id, "H/29")]
        h17["charged_seconds"], h29["charged_seconds"] = (
            h29["charged_seconds"], h17["charged_seconds"]
        )
    primary_failed = audit.assess_panel(proposal, cases, rows, historical)
    assert primary_failed["scientific_predicates_passed"] is False
    assert not primary_failed["predicates"]["primary_each_scale_mean_and_sum_at_most_point_nine"]


def test_plain_P17_runtime_counterexample_loss_is_route_isolation_STOP():
    audit, proposal, cases, rows, historical = public_metric_panel()
    target = "tlcase-v1-55c1b3e64135c23125fc286de5d780fc5d9a1e226d5e43ff0dbc8925b423936a"
    row = next(row for row in rows if (row["case_id"], row["method"]) == (target, "plain-P/17"))
    row.update(attempt_accepted=True, fallback_occurred=False)
    result = audit.assess_panel(proposal, cases, rows, historical)
    assert result["scientific_predicates_passed"] is False
    assert result["outcome_status"] == "STOP_ROUTE_NOT_ISOLATED"


def test_new_public_active_H_query_counts_prefix_before_independent_FEM():
    import torch

    from topolab.b2_12_context_cnn import ContextCNN
    from topolab.experiment import ExperimentCase
    from topolab.problem import (
        FixedFaceSupportDefinition,
        MaterialDefinition,
        MeshDefinition,
        OptimizationDefinition,
        PointLoadDefinition,
        TopologyProblem,
    )

    audit = checker()
    driver = audit.helper("p17_m2_scientific_control")
    case = ExperimentCase.from_problem(
        TopologyProblem(
            mesh=MeshDefinition(element_counts=(24, 12, 6), lengths=(2.3, 0.8, 0.6)),
            material=MaterialDefinition(solid_modulus=1000, minimum_modulus=1, poisson_ratio=0.27),
            supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
            loads=(PointLoadDefinition(node=998, direction="y", magnitude=-1),),
            optimization=OptimizationDefinition(
                volume_fraction=0.47,
                filter_radius=0.18,
                minimum_density=0.05,
                convergence_tolerance=0.01,
                max_iterations=360,
            ),
        )
    )
    proposal = json.loads(
        (REPO / "docs/planning/p17_m2_native_homotopy_proposal.json").read_bytes()
    )
    assert case.case_id not in proposal["prospective_pilot"]["case_ids"]
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(20017)
        model = ContextCNN().cpu().eval()
    import hashlib

    parameter_hash = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        parameter_hash.update(
            audit.canonical({"name": name, "shape": list(tensor.shape), "dtype": str(tensor.dtype)})
        )
        parameter_hash.update(tensor.detach().numpy().astype("<f4").tobytes())
    models = {("P", 17): model}
    identities = {
        ("P", 17): {"new_public_weights": True, "parameter_sha256": parameter_hash.hexdigest()}
    }
    measured = driver.MeasuredQueries(
        models, None, checkpoint=lambda: None, model_identities=identities
    )
    uniform = measured.evaluate(case, "uniform", phase="reference")
    reference = uniform["attempt"]["legacy_witness"]["result"]["compliance"]
    row = measured.evaluate(case, "H/17", reference)
    budget = audit.AuditBudget()
    result = audit.audit_query(
        case, row, reference, models=models, neighbors={}, identities=identities, budget=budget
    )
    assert row["homotopy_active"] is True
    assert result["independent_FEM"]["homotopy_prefix_and_transitions"] == 19
    assert result["independent_FEM"]["terminal_and_windows"] <= 24
    assert budget.operations["model_predictions"] == 1


def test_independent_reader_accepts_actual_streamed_query_path():
    audit = checker()
    driver = audit.helper("p17_m2_scientific_control")

    def writer(name, value):
        raw = driver.canonical(value)
        return {"path": name, "byte_size": len(raw), "sha256": audit.digest(raw)}

    summary = driver.public_fixture_panel(writer=writer)
    for desc in summary["rows"]:
        expected = {key: desc[key] for key in ("case_id", "method", "ordinal")}
        packet, cost = audit.checked_output_reference(desc, desc["phase"], expected)
        assert packet == desc["packet"] and cost == desc["cost"]


def test_new_public_NN_views_reanalyse_stored_and_terminal_states_exactly_twice():
    import numpy as np

    from topolab.mesh import generate_structured_hex8
    from topolab.simp import (
        apply_density_filter,
        backpropagate_density_gradient,
        build_density_filter,
    )

    audit = checker()
    driver, public = audit.helper("p17_m2_scientific_control"), audit.helper("p17_m2_homotopy")
    case = public.read_public_manifest(
        public.PUBLIC_FIXTURE,
        public.PUBLIC_FIXTURE_SHA256,
        expected_bytes=public.PUBLIC_FIXTURE_BYTES,
    )
    row = driver.MeasuredQueries({}, None, checkpoint=lambda: None).evaluate(case, "uniform")
    witness = row["attempt"]["legacy_witness"]
    result = witness["result"]
    p, n = case.problem, len(result["design_density"])
    mesh = generate_structured_hex8(*p.mesh.element_counts, lengths=p.mesh.lengths)
    filt = build_density_filter(mesh, p.optimization.filter_radius)
    design = np.asarray(result["design_density"], dtype=np.float32)
    physical = apply_density_filter(filt, design.astype(np.float64)).astype(np.float32)
    analysis = audit._analysis(case, physical.astype(np.float64), None, "NN_label_input_reanalysis")
    gradient = np.abs(backpropagate_density_gradient(filt, analysis.sensitivity))
    clipped = np.clip(gradient / gradient.mean(), 0.25, 4)
    weights = (clipped / clipped.mean()).astype(np.float32)
    nx, ny, nz = p.mesh.element_counts
    stored = {
        "volume": p.optimization.volume_fraction,
        "tensor_dtype": "float32",
        "tensor_axis_order": "channel,z,y,x",
        "tensor_shape": [1, nz, ny, nx],
        "design_density": design.tolist(),
        "physical_density": physical.tolist(),
        "sensitivity_weight": weights.tolist(),
        "compliance": float(analysis.compliance),
        "physical_volume_fraction": float(physical.mean(dtype=np.float64)),
        "iterations": len(witness["trace"]),
        "terminal_density_change": result["history"][-1]["density_change"],
        "stop_reason": "design_max",
    }
    common = {
        "case": case.model_dump(mode="json"),
        "membership": {"role": "train"},
        "initialization": "new public fixture",
        "source": {"new_public": True},
    }
    data = audit.helper("p17_m2_input_export_independent")
    bits = {
        "/stored/" + k: data.vector_sha(stored[k], 32, n, exact_f32=True)
        for k in ("design_density", "physical_density", "sensitivity_weight")
    }
    bits.update(
        {
            "/result/" + k: data.vector_sha(result[k], 64, n)
            for k in ("design_density", "physical_density")
        }
    )
    for i, state in enumerate(result["history"], len(witness["trace"]) - len(result["history"])):
        for key in ("design_density", "physical_density"):
            bits[f"/result/history/{i}/{key}"] = data.vector_sha(state[key], 64, n)
    producer = {
        **common,
        "schema": "topolab.v2.m2-nn-producer-view.v1",
        "stored": {
            k: stored[k]
            for k in ("tensor_dtype", "tensor_axis_order", "tensor_shape", "design_density")
        },
        "bit_digests": {"/stored/design_density": bits["/stored/design_density"]},
    }
    packet = {
        **common,
        "schema": "topolab.v2.m2-nn-audit-view.v1",
        "stored": stored,
        "terminal": {
            k: result[k] for k in ("design_density", "physical_density", "compliance", "converged")
        },
        "total_updates": len(witness["trace"]),
        "recent": result["history"],
        "bit_digests": bits,
    }
    budget = audit.AuditBudget()
    decoded, inputs, actual = audit.audit_nn_pair(producer, packet, budget=budget)
    assert decoded == case and inputs.shape == (10, nz, ny, nx)
    assert np.array_equal(actual, design.reshape(1, nz, ny, nx))
    assert budget.counts["NN_label_input_reanalysis"] == 2
    corrupt = deepcopy(packet)
    corrupt["stored"]["compliance"] *= 1.01
    with pytest.raises(ValueError, match="NN stored compliance differs"):
        audit.audit_nn_pair(producer, corrupt, budget=audit.AuditBudget())


def test_whole_C_charge_keeps_input_load_when_row_totals_are_lower():
    audit = checker()
    assert audit.checked_complete_charge("scientific-producer", 600, 590, 500, 460, 360) == 970
    with pytest.raises(ValueError, match="complete wall/FULL charge exceeded"):
        audit.checked_complete_charge("resource-preflight", 20, 19, 18, 0, 0)


def test_completed_fixed_continuation_endpoint_can_be_unconverged_before_case_cap():
    from topolab.b3_queries import TerminalWitness
    from topolab.experiment import ExperimentCase
    from topolab.problem import TopologyProblem, solve_problem

    audit = checker()
    definition = {
        "mesh": {"element_counts": [24, 12, 6], "lengths": [2.3, 0.8, 0.6]},
        "material": {"solid_modulus": 1000, "minimum_modulus": 1, "poisson_ratio": 0.27},
        "supports": [{"axis": "x", "side": "min"}],
        "loads": [{"kind": "point", "node": 998, "direction": "y", "magnitude": -1}],
        "optimization": {
            "volume_fraction": 0.47,
            "filter_radius": 0.18,
            "minimum_density": 0.05,
            "convergence_tolerance": 0.01,
            "max_iterations": 360,
        },
    }
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(definition))
    bounded = deepcopy(definition)
    bounded["optimization"]["max_iterations"] = 30
    actual = solve_problem(TopologyProblem.model_validate(bounded))
    assert len(actual.history) == 30 and not actual.converged
    witness = TerminalWitness.from_result(actual).model_dump(mode="json")
    # These are actual OC states. The endpoint is checked as a completed fixed
    # continuation, without accepting its quality or choosing it over a prior state.
    result = audit.audit_terminal(
        case, witness, actual.compliance, accepted=False, continuation_from=10
    )
    assert result["quality_passed"] is False
    with pytest.raises(ValueError, match="ordinary unconverged trajectory truncated"):
        audit.audit_terminal(case, witness, actual.compliance, accepted=False)


def test_auditor_failed_filing_retains_raw_source_facts_in_native_stderr(tmp_path, capsys):
    audit = checker()
    source = tmp_path / "new-public-source.json"
    source.write_bytes(b'{"public":true}\n')
    observed = source.stat()
    failure = {
        "schema": "topolab.v2.m2-scientific-auditor-failure.v1",
        "error_type": "ValueError",
        "reason": "original new public validation failure",
        "input_source_facts": {
            str(source): {
                "before_read": {
                    "st_dev": observed.st_dev,
                    "st_ino": observed.st_ino,
                    "st_size": observed.st_size,
                    "st_mtime_ns": observed.st_mtime_ns,
                }
            }
        },
        "secondary_errors": [],
    }
    primary = ValueError(failure["reason"])

    def failed_writer(name, packet):
        raise OSError("new public failure reserve exhausted")

    audit.retain_audit_failure(primary, failure, failed_writer)
    retained = json.loads(capsys.readouterr().err)
    assert retained["failure"]["input_source_facts"] == failure["input_source_facts"]
    assert retained["failure"]["reason"] == str(primary)
    assert retained["failure"]["secondary_errors"][0]["reason"] == (
        "new public failure reserve exhausted"
    )
    assert primary.scientific_failure is failure
    assert primary.scientific_failure_stderr_written is True


def shared_evidence(audit, role, action, start):
    contract_sha = "b" * 64
    caps = {"resource-preflight": 180, "scientific-producer": 10800, "scientific-auditor": 3600}
    payload = {
        "execution_identity": audit.IDENTITY,
        "role": role,
        "scientific_contract_sha256": contract_sha,
    }
    if action == "reservation":
        payload.update(
            status="CONSUMED_BEFORE_CONTROLLER_INTERPRETER",
            FULL_seconds=caps[role],
            began_UTC_seconds=start + 0.02,
        )
    else:
        payload.update(
            status="SCIENTIFIC_READER_RETURN_ACKNOWLEDGED",
            lease_state="RELEASED",
            consumer_actual_exit_observed=True,
        )
    argv = ["/usr/bin/time", "-l", "new-public-helper", role, action, contract_sha]
    raw = audit.canonical(payload)
    evidence = {
        "role": role,
        "action": action,
        "event": {
            "argv": argv,
            "start_seconds": start,
            "end_seconds": start + 0.1,
            "exit_code": 0,
            "complete": True,
            "stdout_sha256": audit.digest(raw),
        },
        "profile": b"0.05 real 0.02 user 0.01 sys\n4096 maximum resident set size\n",
        "log": raw,
    }
    evidence["event"]["profile_sha256"] = audit.digest(evidence["profile"])
    if action == "reservation":
        evidence["pending"] = payload
    dispatched_evidence(audit, shared_contract(audit), evidence, role, action)
    return evidence


def shared_contract(audit):
    roles = ("resource-preflight", "scientific-producer", "scientific-auditor")
    caps = (180, 10800, 3600)
    contract = {
        "runtime": {"platform": "darwin", "python_entry": "/new/python",
                    "python_startup_entry": "/new/Framework/Python"},
        "shared_FULL_seconds": 180,
        "roles": {r: {"FULL_seconds": cap} for r, cap in zip(roles, caps, strict=True)},
        "shared_helpers": {},
    }
    for role in roles:
        contract["shared_helpers"][role] = {}
        for action in ("reservation", "reader-ack"):
            contract["shared_helpers"][role][action] = {
                "argv": ["/usr/bin/time", "-l", "-o", "/new/helper.time", "new-helper"],
                "dispatch_argv": ["/new/python", "-I", "/new/dispatch.py", role, action, "b" * 64],
                "dispatch_path": "/new/dispatch.json",
                "profile_path": "/new/helper.time",
                "log_path": "/new/helper.log",
                "timeout_seconds": 1,
            }
    return contract


@pytest.mark.parametrize(
    "mutation", (None, "incomplete", "wrong-hash", "wrong-pending", "rss", "profile-anchor")
)
def test_shared_reservation_requires_native_actual_return_and_exact_pending(monkeypatch, mutation):
    audit = checker()
    # Isolate this byte-level checker; actual full-contract/B integration is external.
    monkeypatch.setattr(audit, "check_contract", lambda value: "b" * 64)
    contract = shared_contract(audit)
    evidence = shared_evidence(audit, "resource-preflight", "reservation", 10)
    if mutation == "incomplete":
        evidence["event"]["complete"] = False
    elif mutation == "wrong-hash":
        evidence["event"]["stdout_sha256"] = "c" * 64
    elif mutation == "wrong-pending":
        evidence["pending"] = dict(evidence["pending"], FULL_seconds=0)
    elif mutation == "rss":
        evidence["profile"] = evidence["profile"].replace(b"4096", b"4294967297")
    elif mutation == "profile-anchor":
        evidence["profile"] = evidence["profile"].replace(b"4096", b"2048")
    if mutation is not None:
        with pytest.raises(ValueError):
            audit.check_shared_helper_return(
                contract, "resource-preflight", "reservation", evidence
            )
    else:
        result = audit.check_shared_helper_return(
            contract, "resource-preflight", "reservation", evidence
        )
        assert result["actual_exit_observed"] is True
        assert result["active_charge_seconds"] == pytest.approx(1.1)


def test_shared_closeout_charges_active_helpers_without_charging_long_C_gaps(monkeypatch):
    audit = checker()
    monkeypatch.setattr(audit, "check_contract", lambda value: "b" * 64)
    contract = shared_contract(audit)
    order = [
        ("resource-preflight", "reservation"),
        ("scientific-producer", "reservation"),
        ("scientific-producer", "reader-ack"),
        ("scientific-auditor", "reservation"),
        ("scientific-auditor", "reader-ack"),
    ]
    records = [
        shared_evidence(audit, role, action, start)
        for (role, action), start in zip(order, (10, 200, 11000, 12000, 15600), strict=True)
    ]
    role_evidence = {
        role: {
            "raw_tool_events": [
                {"start_seconds": begin, "end_seconds": begin + 0.1},
                {"start_seconds": begin + 0.2, "end_seconds": begin + 0.3},
                {"start_seconds": end - 0.3, "end_seconds": end - 0.2},
                {"start_seconds": end - 0.1, "end_seconds": end},
            ]
        }
        for role, begin, end in (
            ("resource-preflight", 20, 100),
            ("scientific-producer", 201, 10900),
            ("scientific-auditor", 12001, 15500),
        )
    }
    monkeypatch.setattr(audit, "check_b_preflight", lambda *args: None)
    monkeypatch.setattr(audit, "check_scientific_role", lambda *args: None)
    result = audit.check_shared_closeout(contract, records, role_evidence=role_evidence)
    assert result["FULL_charged_seconds"] == 180
    assert result["active_helper_charge_seconds"] == pytest.approx(15.5)
    overlap = deepcopy(records)
    overlap[1]["event"]["start_seconds"] = 10.05
    with pytest.raises(ValueError, match="shared helper order/overlap"):
        audit.check_shared_closeout(contract, overlap, role_evidence=role_evidence)
    overlapping_role = deepcopy(role_evidence)
    overlapping_role["scientific-producer"]["raw_tool_events"][-1]["end_seconds"] = 11000.05
    with pytest.raises(ValueError, match="overlap actual role lifetimes"):
        audit.check_shared_closeout(contract, records, role_evidence=overlapping_role)
    invalid_ack = deepcopy(records[2])
    payload = json.loads(invalid_ack["log"])
    payload["consumer_actual_exit_observed"] = False
    invalid_ack["log"] = audit.canonical(payload)
    invalid_ack["event"]["stdout_sha256"] = audit.digest(invalid_ack["log"])
    with pytest.raises(ValueError):
        audit.check_shared_helper_return(contract, "scientific-producer", "reader-ack", invalid_ack)


def test_row_cold_input_cost_uses_specialist_checkpoint_and_exact_hash(monkeypatch):
    from topolab.experiment import ExperimentCase
    from topolab.problem import TopologyProblem

    audit = checker()
    case = ExperimentCase.from_problem(
        TopologyProblem.model_validate(
            {
                "mesh": {"element_counts": [24, 12, 6], "lengths": [2.3, 0.8, 0.6]},
                "material": {"solid_modulus": 1000, "minimum_modulus": 1, "poisson_ratio": 0.27},
                "supports": [{"axis": "x", "side": "min"}],
                "loads": [{"kind": "point", "node": 998, "direction": "y", "magnitude": -1}],
                "optimization": {
                    "volume_fraction": 0.61,
                    "filter_radius": 0.18,
                    "max_iterations": 360,
                },
            }
        )
    )
    path = "checkpoints/S-17.safetensors"
    hashes = {path: "d" * 64}
    row = {
        "method": "C/17",
        "wall_seconds": 0.5,
        "row_input_setup": {
            "checkpoint_decodes": 1,
            "NN_case_reencodes": 0,
            "NN_index_builds": 0,
            "buffer_rehashes": 1,
            "source_file_rereads": 0,
            "selected_buffers": [{"path": path, "sha256": "d" * 64}],
            "wall_seconds": 0.2,
        },
    }
    counts = audit.check_row_input_setup(case, row, hashes, {})
    assert counts["checkpoint_decodes"] == counts["buffer_rehashes"] == 1
    wrong = deepcopy(row)
    wrong["row_input_setup"]["selected_buffers"][0]["path"] = "checkpoints/C-17.safetensors"
    with pytest.raises(ValueError, match="row selected verified buffers"):
        audit.check_row_input_setup(case, wrong, hashes, {})
    wrong = deepcopy(row)
    wrong["row_input_setup"]["source_file_rereads"] = 1
    with pytest.raises(ValueError):
        audit.check_row_input_setup(case, wrong, hashes, {})


def test_public_decoder_return_has_no_formal_C_or_unchecked_return_authority():
    audit = checker()
    with pytest.raises(ValueError, match="public scientific decoder contract required"):
        audit.check_public_scientific_reader_return(
            {"public_fixture_only": False}, "scientific-producer", {}
        )
    with pytest.raises(ValueError, match="formal scientific contract required"):
        audit.check_scientific_role({"public_fixture_only": True}, "scientific-producer", {})
    with pytest.raises(ValueError, match="actual checked public scientific return required"):
        audit.CheckedPublicScientificReturn("a" * 64, "scientific-producer", {}, b"{}")


def test_scientific_startup_identity_preserves_actual_entry_and_strict_tail():
    audit = checker()
    runtime = {
        "python_entry": "/new-public/venv/bin/python",
        "python_startup_entry": "/new-public/Framework/Python.app/Contents/MacOS/Python",
    }
    command = [runtime["python_entry"], "-I", "new-public-reader.py", "consume"]
    expected = [runtime["python_startup_entry"], *command[1:]]
    assert audit.startup_argv(command, runtime) == expected
    contract = {
        "runtime": runtime,
        "roles": {"scientific-producer": {"inner_starts": [{"argv": command}]}},
    }
    payload = {
        "actual_numerical_runtime": {
            "python_entry": runtime["python_entry"],
            "startup_orig_argv": expected,
        }
    }
    audit.check_returned_startup(contract, "scientific-producer", payload, "a" * 64)
    wrong = deepcopy(payload)
    wrong["actual_numerical_runtime"]["startup_orig_argv"][-1] = "ack"
    with pytest.raises(ValueError, match="actual scientific startup argv differs"):
        audit.check_returned_startup(contract, "scientific-producer", wrong, "a" * 64)
    with pytest.raises(ValueError):
        audit.startup_argv(["/new-public/other-python", *command[1:]], runtime)


def dispatched_evidence(audit, contract, evidence, role, label):
    """Synthetic public native units, including the wrapper's separate wait4."""
    spec = contract["shared_helpers"][role][label]
    spec.update(
        dispatch_argv=["/new/python", "-I", "/new/dispatch.py", role, label, "b" * 64],
        dispatch_path="/new/dispatch.json",
        profile_path="/new/helper.time",
        log_path="/new/helper.log",
        timeout_seconds=1,
    )
    spec["argv"] = ["/usr/bin/time", "-l", "-o", spec["profile_path"], "new-helper"]
    event = evidence["event"]
    event["argv"] = spec["argv"]
    event["dispatch_argv"] = spec["dispatch_argv"]
    event["dispatcher_exit"] = 0
    record = {
        "schema": "topolab.v2.m2-native-dispatch.v1",
        "execution_identity": audit.IDENTITY,
        "contract_sha256": "b" * 64,
        "role": role,
        "label": label,
        "argv": list(spec["argv"]),
        "dispatch_argv": list(spec["dispatch_argv"]),
        "python_entry": contract["runtime"]["python_entry"],
        "startup_orig_argv": [contract["runtime"]["python_startup_entry"],
                              *spec["dispatch_argv"][1:]],
        "pid": 101,
        "native_pid": 102,
        "started_unix_ns": int((event["start_seconds"] + 0.01) * 1e9),
        "returned_unix_ns": int((event["start_seconds"] + 0.09) * 1e9),
        "elapsed_seconds": 0.08,
        "exit_code": 0,
        "log_sha256": audit.digest(evidence["log"]),
        "stdout_observed_bytes": len(evidence["log"]),
        "stdout_retained_bytes": len(evidence["log"]),
        "stdout_observed_truncated_bytes": 0,
        "unobserved_stdout_after_cap": "NOT_TRUNCATED",
        "profile_sha256": audit.digest(evidence["profile"]),
        "timer_native_exit": {
            "exit_code": 0,
            "pid": 102,
            "native": {"wall_seconds": 0.06, "user_seconds": 0.02,
                       "system_seconds": 0.01, "rss_bytes": 2048},
            "source": "parent os.wait4 native exit rusage; possible descendant aggregation",
            "statistics_source": "os.wait4",
            "wall_source": "controller_monotonic_observed",
            "rss_unit": "bytes",
        },
        "self_rss_bytes_before_flush": 1024,
        "self_rss_bytes_after_flush": 1024,
        "self_rss_phases": ["pre_preview_write", "post_preview_write_pre_final_serialization"],
        "self_rss_scope": ("empirical before/after retained preflush packet; "
                           "final serializer closed externally"),
        "group_gone": True,
        "cleanup": {"group_gone": True, "final_group_gone": True, "leader_exit": 0,
                    "signals": [], "observation_limit_exceeded": False,
                    "observations": [{"group_gone": True, "leader_exit": 0}]},
        "descendant_groups": [],
        "watchdog_helper": None,
        "native_log_facts": {key: {"st_dev": 1, "st_ino": 2, "st_size": len(evidence["log"]),
                                   "st_mtime_ns": 3, "st_mode": 0o100600, "st_nlink": 1}
                             for key in ("declared", "before", "after", "closing")},
        "cleanup_errors": [],
        "status": "COMPLETED_WITH_NATIVE_RETURN",
    }
    record["native_log_facts"]["returned_bytes"] = len(evidence["log"])
    seal_dispatch(audit, evidence, record)
    return record


def seal_dispatch(audit, evidence, record):
    preview = deepcopy(record)
    preview.pop("preflush_sha256", None)
    preview["self_rss_bytes_after_flush"] = None
    evidence["preflush"] = audit.canonical(preview)
    record["preflush_sha256"] = audit.digest(evidence["preflush"])
    evidence["dispatch"] = audit.canonical(record)
    event = evidence["event"]
    event["dispatch_stdout"] = evidence["dispatch"].decode("ascii")
    event["dispatch_stdout_sha256"] = audit.digest(evidence["dispatch"])


@pytest.mark.parametrize("mutation", [None, "missing_timer", "unit", "wrapper_peak", "self_peak",
                                    "actual_return", "profile_anchor", "wrong_argv", "cleanup",
                                    "startup", "preview_anchor", "missing_preview", "phases",
                                    "truncated"])
def test_native_dispatch_closes_timer_and_dispatcher_resources(monkeypatch, mutation):
    audit = checker()
    monkeypatch.setattr(audit, "check_contract", lambda _: "b" * 64)
    contract = shared_contract(audit)
    evidence = shared_evidence(audit, "resource-preflight", "reservation", 10)
    record = dispatched_evidence(audit, contract, evidence, "resource-preflight", "reservation")
    if mutation == "missing_timer":
        del record["timer_native_exit"]
    elif mutation == "unit":
        record["timer_native_exit"]["rss_unit"] = "KiB*1024"
    elif mutation == "wrapper_peak":
        record["timer_native_exit"]["native"]["rss_bytes"] = 4294965000
    elif mutation == "self_peak":
        record["self_rss_bytes_after_flush"] = 4294965000
    elif mutation == "actual_return":
        evidence["event"]["complete"] = False
    elif mutation == "profile_anchor":
        evidence["profile"] = evidence["profile"].replace(b"4096", b"2048")
    elif mutation == "wrong_argv":
        record["argv"][-1] = "unregistered-helper"
    elif mutation == "cleanup":
        record["group_gone"] = False
    elif mutation == "startup":
        record["startup_orig_argv"][-1] = "unregistered-tail"
    elif mutation == "phases":
        record["self_rss_phases"] = ["claimed_future_exit"]
    elif mutation == "truncated":
        record["stdout_observed_truncated_bytes"] = 1
        record["unobserved_stdout_after_cap"] = "UNKNOWN"
    seal_dispatch(audit, evidence, record)
    if mutation == "preview_anchor":
        evidence["preflush"] = evidence["preflush"].replace(b"1024", b"2048")
    elif mutation == "missing_preview":
        del evidence["preflush"]
    if mutation:
        with pytest.raises((ValueError, KeyError)):
            audit.check_native_dispatch(contract, "resource-preflight", "reservation", evidence)
    else:
        result = audit.check_native_dispatch(
            contract, "resource-preflight", "reservation", evidence
        )
        assert result["native_rss_bytes"] == 7168
        assert result["timer_wait4_rss_bytes"] == 2048
        assert result["actual_dispatcher_exit_observed"] is True


def test_native_dispatch_preserves_legitimate_empty_NEW_command_stdout(monkeypatch):
    audit = checker()
    monkeypatch.setattr(audit, "check_contract", lambda _: "b" * 64)
    contract = shared_contract(audit)
    evidence = shared_evidence(audit, "resource-preflight", "reservation", 10)
    evidence["log"] = b""
    evidence["event"]["stdout_sha256"] = audit.digest(b"")
    dispatched_evidence(audit, contract, evidence, "resource-preflight", "reservation")
    result = audit.check_native_dispatch(contract, "resource-preflight", "reservation", evidence)
    assert result["native_rss_bytes"] == 7168


def test_actual_public_dispatcher_packet_matches_independent_schema(tmp_path, monkeypatch):
    """Actual native child; contract/event stubs isolate receipt-schema integration.

    The pytest interpreter has not exited: this is explicitly not an actual
    independent B admission or a proof of this test process's final RSS/exit.
    """
    audit = checker()
    driver = audit.helper("p17_m2_scientific_orchestration")
    resource, _ = driver.native_helpers()
    profile = tmp_path / "new-public.time"
    timed = resource._timed([sys.executable, "-I", "-c", "pass"], profile)
    dispatch = [sys.executable, *sys.orig_argv[1:]]
    spec = {"dispatch_argv": dispatch, "profile_path": str(profile),
            "dispatch_path": str(tmp_path / "new-public-dispatch.json"),
            "log_path": str(tmp_path / "new-public.log"), "timeout_seconds": 10}
    contract = {"runtime": {"platform": sys.platform, "python_entry": sys.executable,
                            "python_startup_entry": sys.orig_argv[0]},
                "roles": {"resource-preflight": {"FULL_seconds": 10,
                    "exit_argv": {"controller": timed},
                    "native_dispatch": {"controller": spec}}}}
    monkeypatch.setattr(audit, "check_contract", lambda _: "a" * 64)
    began = time.time()
    packet = driver.observe_native(contract, "a" * 64, "resource-preflight", "controller")
    ended = time.time()
    raw = audit.canonical(packet)
    evidence = {
        "dispatch": Path(spec["dispatch_path"]).read_bytes(),
        "preflush": (tmp_path / "new-public-dispatch-preflush.json").read_bytes(),
        "profile": profile.read_bytes(), "log": Path(spec["log_path"]).read_bytes(),
        "event": {"argv": timed, "dispatch_argv": dispatch, "dispatch_stdout": raw.decode(),
                  "dispatch_stdout_sha256": audit.digest(raw), "dispatcher_exit": 0,
                  "start_seconds": began, "end_seconds": ended, "complete": True,
                  "exit_code": 0, "stdout_sha256": packet["log_sha256"],
                  "profile_sha256": packet["profile_sha256"],
                  "observer": "UNIT_EVENT_STUB_FUNCTION_RETURN_ONLY_NOT_FORMAL_AUTHORITY"},
    }
    result = audit.check_native_dispatch(contract, "resource-preflight", "controller", evidence)
    assert result["native_rss_bytes"] > result["command_native_rss_bytes"] > 0
    assert evidence["log"] == b""
