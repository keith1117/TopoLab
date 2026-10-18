"""Original small public fixtures for the separately authored witness checker."""

import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from topolab.experiment import ExperimentCase
from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.mesh import generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport
from topolab.problem import (
    FaceLoadDefinition,
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    TopologyProblem,
)
from topolab.simp import (
    apply_density_filter,
    backpropagate_density_gradient,
    build_density_filter,
    evaluate_compliance,
    optimality_criteria_update,
)

_SPEC = importlib.util.spec_from_file_location(
    "independently_authored_m2_audit",
    Path(__file__).parents[1] / "scripts/p17_m2_independent_audit.py",
)
assert _SPEC is not None and _SPEC.loader is not None
checker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(checker)


def original_public_witness(active: bool):  # type: ignore[no-untyped-def]
    """Produce original two-element evidence with no candidate-driver dependency."""
    case = ExperimentCase.from_problem(
        TopologyProblem(
            mesh=MeshDefinition(element_counts=(2, 1, 1), lengths=(2, 1, 1)),
            material=MaterialDefinition(solid_modulus=1000, minimum_modulus=1, poisson_ratio=0.3),
            supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
            loads=(FaceLoadDefinition(axis="x", side="max", direction="y", total=-1),),
            optimization=OptimizationDefinition(
                volume_fraction=0.47,
                filter_radius=1.5,
                minimum_density=0.05,
                convergence_tolerance=0.01,
                max_iterations=60,
            ),
        )
    )
    mesh = generate_structured_hex8(2, 1, 1, lengths=(2, 1, 1))
    loads = build_load_vector(mesh, [FaceLoad(axis="x", side="max", direction="y", total=-1)])
    constraints = build_constrained_dofs(mesh, [FixedFaceSupport(axis="x", side="min")])
    filt = build_density_filter(mesh, 1.5)
    dv = backpropagate_density_gradient(filt, np.full(2, 0.5))

    def analyze(rho, penalty):  # type: ignore[no-untyped-def]
        return evaluate_compliance(
            mesh,
            rho,
            loads,
            constraints,
            solid_modulus=1000,
            minimum_modulus=1,
            poisson_ratio=0.3,
            penalty=penalty,
        )

    def state(i, pi, penalty, x, rho, analysis, dc=0.0, pc=0.0):  # type: ignore[no-untyped-def]
        return dict(
            iteration=i,
            phase_iteration=pi,
            penalty=penalty,
            compliance=float(analysis.compliance),
            volume_fraction=float(np.mean(rho)),
            density_change=dc,
            physical_change=pc,
            design_density=x.tolist(),
            physical_density=rho.tolist(),
        )

    design = np.array([0.36, 0.58])
    physical = apply_density_filter(filt, design)
    penalty = 1 if active else 3
    analysis = analyze(physical, penalty)
    initial = state(0, 0, penalty, design, physical, analysis)
    full, prefix, transitions, p3 = [], [], [], []
    converged = False
    for iteration in range(1, 61):
        if active and iteration in (9, 17):
            penalty += 1
            analysis = analyze(physical, penalty)
            transitions.append(state(iteration - 1, 0, penalty, design, physical, analysis))
        updated = optimality_criteria_update(
            design,
            backpropagate_density_gradient(filt, analysis.sensitivity),
            dv,
            filt,
            volume_fraction=0.47,
            minimum_density=0.05,
            move_limit=0.2,
        )
        rho = apply_density_filter(filt, updated)
        dc = float(np.max(np.abs(updated - design)))
        pc = float(np.max(np.abs(rho - physical)))
        design, physical = updated, rho
        analysis = analyze(physical, penalty)
        phase_iteration = iteration - (16 if active and penalty == 3 else 8 if penalty == 2 else 0)
        row = state(iteration, phase_iteration, penalty, design, physical, analysis, dc, pc)
        full.append(row)
        if penalty != 3:
            prefix.append(row)
            continue
        p3.append(row)
        design_stop = dc <= 0.01
        physical_stop = False
        if len(p3) >= 11:
            window = p3[-11:]
            gain = (window[0]["compliance"] - window[-1]["compliance"]) / window[0]["compliance"]
            physical_stop = (
                all(s["physical_change"] <= 0.01 for s in window[1:]) and 0 <= gain <= 0.0002
            )
        if design_stop or physical_stop:
            converged = True
            break
    recent = p3[-11:]
    analysis = analyze(physical, 3)
    result = dict(
        design_density=design.tolist(),
        physical_density=physical.tolist(),
        compliance=float(analysis.compliance),
        displacements=analysis.displacements.tolist(),
        reactions=analysis.reactions.tolist(),
        converged=converged,
        history=[{k: s[k] for k in checker.OLD_STATE_FIELDS} for s in recent],
    )
    witness = dict(
        schema=checker.SCHEMA,
        active=active,
        initial=initial,
        prefix=prefix,
        transitions=transitions,
        recent=recent,
        result=result,
        trace=[{k: s[k] for k in checker.POINT_FIELDS} for s in full],
        fem_solves=len(full) + (4 if active else 2),
    )
    return case, witness


@pytest.fixture(scope="module", params=[False, True])
def original(request):  # type: ignore[no-untyped-def]
    return original_public_witness(request.param)


def test_original_public_fem_witness_and_explicit_scope(original):  # type: ignore[no-untyped-def]
    case, witness = original
    result = checker.audit_witness(case, witness, witness["result"]["compliance"], accepted=True)
    assert result["passed"] and result["accepted"] and result["converged"]
    assert result["prefix_analyses"] == (19 if witness["active"] else 0)
    assert (
        result["total_audit_fem"] == (19 if witness["active"] else 1) + len(witness["recent"]) + 1
    )
    assert result["resource_admission"] == "NOT_RUN"
    assert result["whole_p3_trajectory_replayed"] is False


def test_reference_failure_cannot_be_accepted(original):  # type: ignore[no-untyped-def]
    case, witness = original
    reference = witness["result"]["compliance"] / 1.002
    assert checker.audit_witness(case, witness, reference)["quality_passed"] is False
    with pytest.raises(ValueError, match="false accepted"):
        checker.audit_witness(case, witness, reference, accepted=True)
    assert checker.audit_witness(case, witness)["reference_checked"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "phase",
        "bool_iteration",
        "nan",
        "fem_count",
        "physical",
        "reaction",
        "convergence",
        "terminal_history",
        "recent_prefix",
        "unknown_field",
    ],
)
def test_reject_corrupt_public_witness(original, mutation):  # type: ignore[no-untyped-def]
    case, initial = original
    witness = deepcopy(initial)
    if mutation == "phase":
        witness["trace"][0]["penalty"] = 2
    elif mutation == "bool_iteration":
        witness["initial"]["iteration"] = False
    elif mutation == "nan":
        witness["trace"][-1]["compliance"] = float("nan")
    elif mutation == "fem_count":
        witness["fem_solves"] += 1
    elif mutation == "physical":
        witness["recent"][-1]["physical_density"][0] += 0.01
    elif mutation == "reaction":
        witness["result"]["reactions"][0] += 0.01
    elif mutation == "convergence":
        witness["result"]["converged"] = False
    elif mutation == "terminal_history":
        witness["result"]["history"][-1]["density_change"] += 0.01
    elif mutation == "recent_prefix":
        witness["recent"].insert(0, witness["initial"])
    else:
        witness["unknown"] = "not registered"
    with pytest.raises(ValueError):
        checker.audit_witness(case, witness, witness["result"]["compliance"], accepted=True)


@pytest.mark.parametrize("mutation", ["schedule", "transition", "OC", "prefix_compliance"])
def test_reject_active_prefix_forgery(mutation):  # type: ignore[no-untyped-def]
    case, witness = original_public_witness(True)
    if mutation == "schedule":
        witness["prefix"][8]["phase_iteration"] = 9
    elif mutation == "transition":
        witness["transitions"][0]["penalty"] = 1
    elif mutation == "OC":
        witness["prefix"][0]["design_density"][0] += 0.01
    else:
        witness["prefix"][0]["compliance"] *= 1.01
        witness["trace"][0]["compliance"] *= 1.01
    with pytest.raises(ValueError):
        checker.audit_witness(case, witness)


def test_physical_plateau_requires_eleven_completed_p3_updates():
    states = [dict(density_change=0.02, physical_change=0.001, compliance=10.0) for _ in range(11)]
    assert checker._stop(states[:10], 0.01) is False
    assert checker._stop(states, 0.01) is True
    states[-1]["compliance"] = 10.00001
    assert checker._stop(states, 0.01) is False
    states[-1]["compliance"] = 9.99
    assert checker._stop(states, 0.01) is False
    assert checker._stop([dict(density_change=0.01)], 0.01) is True


def test_independent_source_does_not_import_candidate_driver():
    source = (Path(__file__).parents[1] / "scripts/p17_m2_independent_audit.py").read_text()
    assert "from topolab.p17_m2_homotopy" not in source
    assert "import topolab.p17_m2_homotopy" not in source


@pytest.mark.parametrize("active", [False, True])
def test_audit_actual_candidate_as_subject_after_independent_authorship(active):
    from topolab.p17_m2_homotopy import solve_phases

    case, original = original_public_witness(active)
    actual = solve_phases(
        case,
        np.asarray(original["initial"]["design_density"]),
        active=active,
        checkpoint=lambda: None,
    ).model_dump(mode="json")
    result = checker.audit_witness(case, actual, original["result"]["compliance"], accepted=True)
    assert result["converged"] and result["reference_checked"]


def resource_evidence(platform="darwin"):
    profile = (
        b"0.05 real 0.02 user 0.01 sys\n4096 maximum resident set size\n"
        if platform == "darwin"
        else b"TOPOLAB_NATIVE 0.05 0.02 0.01 4\n"
    )
    log = b"new public command output\n"
    measured = dict(wall_seconds=0.05, user_seconds=0.02, system_seconds=0.01, rss_bytes=4096)

    def timer(pid):
        return dict(
            exit_code=0,
            pid=pid,
            statistics_source="os.wait4",
            wall_source="controller_monotonic_observed",
            rss_unit="bytes" if platform == "darwin" else "KiB*1024",
            native=dict(wall_seconds=0.06, user_seconds=0.02, system_seconds=0.01, rss_bytes=2048),
        )

    record = dict(
        schema="topolab.v2.m2-native-rss-exit-assurance.v1",
        role="new-public",
        software_only=True,
        argv=["original-public-command"],
        platform=platform,
        status="PENDING_POSTEXIT",
        software_result="PUBLIC_COMMAND_EXIT_OBSERVED",
        exit_code=0,
        cleanup=dict(group_gone=True, leader_exit=0),
        pid=111,
        timer_native_exit=timer(111),
        observed_outer_wall_seconds=0.1,
        native=measured,
        samples=[
            dict(
                offset_seconds=0.01,
                actual_interval_seconds=None,
                roles=[
                    dict(pid=111, parent=100, pgid=111, rss_bytes=1024),
                ],
                controller_rss_bytes=2048,
                group_plus_controller_rss_bytes=3072,
            )
        ],
        helpers=[
            dict(
                role="rss-sampler-0",
                exit_code=0,
                native=measured,
                profile="sampler-0.time",
                profile_sha256=hashlib.sha256(profile).hexdigest(),
                cleanup=dict(group_gone=True, leader_exit=0),
                problem=None,
                pid=222,
                timer_native_exit=timer(222),
            )
        ],
        controller_rss_peak_bytes=2048,
        profile_sha256=hashlib.sha256(profile).hexdigest(),
        log_sha256=hashlib.sha256(log).hexdigest(),
        controller_complete_exit="UNKNOWN_PENDING_OUTER_PROFILE",
        scientific_resource_admission="NOT_RUN",
        limit_bytes=4294967296,
        timeout_seconds=1,
        target_sample_interval_seconds=0.5,
        ps_rss_unit="KiB*1024",
        native_rss_unit="bytes" if platform == "darwin" else "KiB*1024",
    )
    return record, dict(
        profile=profile,
        log=log,
        helper_profiles={"sampler-0.time": profile},
        expected_role="new-public",
        expected_argv=["original-public-command"],
        platform=platform,
        require_success=True,
    )


@pytest.mark.parametrize("platform", ["darwin", "linux"])
def test_explicit_native_units_and_empirical_scope(platform):
    record, evidence = resource_evidence(platform)
    result = checker.audit_resource_record(record, **evidence)
    assert result["software_record_consistent"] and result["public_command_success"]
    assert result["empirical_recorded_peak_bytes"] == 14336
    assert result["instantaneous_or_preentry_bound_proved"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "hash",
        "native_units",
        "sum",
        "missing_helper",
        "false_exit",
        "controller_exit",
        "admission",
        "postexit_cap",
        "wall_cap",
        "argv",
        "duplicate_pid",
        "bool_bytes",
    ],
)
def test_reject_false_resource_evidence(mutation):
    record, evidence = resource_evidence()
    if mutation == "hash":
        evidence["profile"] += b"tamper"
    elif mutation == "native_units":
        record["native"]["rss_bytes"] *= 1024
    elif mutation == "sum":
        record["samples"][0]["group_plus_controller_rss_bytes"] += 1
    elif mutation == "missing_helper":
        evidence["helper_profiles"] = {}
    elif mutation == "false_exit":
        record["cleanup"]["group_gone"] = False
    elif mutation == "controller_exit":
        record["controller_complete_exit"] = "PASS"
    elif mutation == "admission":
        record["scientific_resource_admission"] = "PASS"
    elif mutation == "postexit_cap":
        record["limit_bytes"] = 4096
    elif mutation == "wall_cap":
        record["timeout_seconds"] = 0.05
    elif mutation == "argv":
        record["argv"] = ["unregistered-command"]
    elif mutation == "duplicate_pid":
        record["samples"][0]["roles"] *= 2
    else:
        record["samples"][0]["controller_rss_bytes"] = True
    with pytest.raises(ValueError):
        checker.audit_resource_record(record, **evidence)


def test_failed_public_receipt_never_becomes_admission():
    record, evidence = resource_evidence()
    record["software_result"] = "FAIL_PUBLIC_COMMAND"
    record["exit_code"] = record["cleanup"]["leader_exit"] = 7
    record["timer_native_exit"]["exit_code"] = 7
    evidence["require_success"] = False
    result = checker.audit_resource_record(record, **evidence)
    assert result["public_command_success"] is False
    assert result["resource_admission"] == "NOT_RUN"


@pytest.mark.parametrize(
    "mutation", ["missing", "rss", "source", "unit", "exit", "sampler", "overlap"]
)
def test_timer_native_role_coverage_cannot_be_silently_omitted(mutation):
    record, evidence = resource_evidence()
    if mutation == "missing":
        record["timer_native_exit"] = None
    elif mutation == "rss":
        record["timer_native_exit"]["native"]["rss_bytes"] = 0
    elif mutation == "source":
        record["timer_native_exit"]["wall_source"] = "wait4 real time"
    elif mutation == "unit":
        record["timer_native_exit"]["rss_unit"] = "unknown"
    elif mutation == "exit":
        record["timer_native_exit"]["exit_code"] = 7
    elif mutation == "sampler":
        record["helpers"][0]["timer_native_exit"] = None
    else:
        record["native_plus_controller_and_sampler_rss_bytes"] = 1
    with pytest.raises(ValueError):
        checker.audit_resource_record(record, **evidence)


@pytest.mark.parametrize("mutation", ["helper", "cleanup", "rows", "bool_exit"])
def test_malformed_resource_subrecords_fail_closed(mutation):
    record, evidence = resource_evidence()
    if mutation == "helper":
        record["helpers"] = [None]
    elif mutation == "cleanup":
        record["helpers"][0]["cleanup"] = False
    elif mutation == "rows":
        record["samples"][0]["roles"] = [None]
    else:
        record["exit_code"] = False
    with pytest.raises(ValueError):
        checker.audit_resource_record(record, **evidence)


@pytest.mark.parametrize(
    "args,expected", [((1.0, 2.0, 3, 4.0, 15.0), 15.0), ((1.0, 2.0, 0, 30.0, 30.0), 30.0)]
)
def test_independent_failure_inclusive_charge(args, expected):
    assert checker.audit_role_charge(*args) == expected


@pytest.mark.parametrize(
    "args",
    [
        (1.0, 2.0, 3, 4.0, 14.0),
        (None, 2.0, 0, 0.0, 12.0),
        (1.0, 2.0, True, 0.0, 13.0),
        (1.0, float("nan"), 0, 0.0, 12.0),
    ],
)
def test_charge_unknown_undercharge_and_boolean_counters_reject(args):
    with pytest.raises(ValueError):
        checker.audit_role_charge(*args)


@pytest.fixture(scope="module")
def new_model_public_payload():
    import torch

    from topolab.b2_9_vector_load import encode_vector_load_case
    from topolab.b2_12_context_cnn import ContextCNN
    from topolab.experiment import project_design_density
    from topolab.p17_m2_homotopy import solve_phases

    raw = (Path(__file__).parent / "fixtures/p17_m2_public_case.json").read_bytes()
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(json.loads(raw)["problem"]))
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(17)
        model = ContextCNN().cpu().eval()
        weight_sha = hashlib.sha256(
            b"".join(p.detach().numpy().tobytes() for p in model.parameters())
        ).hexdigest()
        with torch.no_grad():
            prediction = (
                model(torch.from_numpy(encode_vector_load_case(case).input_tensor).unsqueeze(0))
                .squeeze(0)
                .numpy()
            )
    projected = project_design_density(case, prediction)
    witness = solve_phases(case, projected.design_density, active=True, checkpoint=lambda: None)
    return dict(
        schema="topolab.v2.p17-m2-native-homotopy.stage-a.v1",
        status="PUBLIC_SOFTWARE_ONLY_NOT_B_OR_C",
        historical_model=False,
        old_input_read_set=[],
        formal_attempts=0,
        case=case.model_dump(mode="json"),
        fixture="tiny-prefix",
        new_weight_identity=weight_sha,
        witness=witness.model_dump(mode="json"),
    ), raw


def test_new_public_model_encoding_projection_and_rng_preservation(new_model_public_payload):
    import torch

    payload, raw = new_model_public_payload
    before = torch.random.get_rng_state().clone()
    result = checker.audit_public_fixture(payload, fixture_bytes=raw)
    assert torch.equal(before, torch.random.get_rng_state())
    assert result["new_model_encoding_projection_checked"]
    assert result["historical_model_used"] is False
    assert result["witness"]["reference_checked"] is False
    assert result["scientific_resource_admission"] == "NOT_RUN"


@pytest.mark.parametrize("mutation", ["weight", "projection", "mode", "old_model", "fixture"])
def test_public_model_misbinding_rejects(new_model_public_payload, mutation):
    original, raw = new_model_public_payload
    payload = deepcopy(original)
    if mutation == "weight":
        payload["new_weight_identity"] = "a" * 64
    elif mutation == "projection":
        payload["witness"]["initial"]["design_density"][0] += 0.01
    elif mutation == "mode":
        payload["fixture"] = "tiny-plain"
    elif mutation == "old_model":
        payload["historical_model"] = True
    else:
        raw += b" "
    with pytest.raises(ValueError):
        checker.audit_public_fixture(payload, fixture_bytes=raw)


def binding_evidence(label="controller"):
    record, resource = resource_evidence()
    before = {
        "controller": "PENDING_POSTEXIT",
        "binder": "PENDING_BINDER_EXIT",
        "verifier": "PENDING_VERIFIER_EXIT",
    }[label]
    after = "PENDING_BINDER_EXIT" if label == "controller" else "PENDING_VERIFIER_EXIT"
    record["status"] = before
    prior = json.dumps(record, sort_keys=True).encode()
    profile, log = resource["profile"], resource["log"]
    binding = dict(
        schema=record["schema"],
        software_only=True,
        prior_status=before,
        status=after,
        bound_role=label,
        exit_code=0,
        record_sha256=hashlib.sha256(prior).hexdigest(),
        profile_sha256=hashlib.sha256(profile).hexdigest(),
        log_sha256=hashlib.sha256(log).hexdigest(),
        native=record["native"],
        resource_cap_exceeded=False,
        scientific_resource_admission="NOT_RUN",
        actual_observer_verification="REQUIRED_AFTER_THIS_ROLE_EXITS",
    )
    return binding, dict(
        prior=prior,
        profile=profile,
        log=log,
        expected_label=label,
        observed_exit_code=0,
        platform="darwin",
    )


@pytest.mark.parametrize("label", ["controller", "binder", "verifier"])
def test_append_only_binding_stays_pending_for_actual_observer(label):
    binding, raw = binding_evidence(label)
    result = checker.audit_exit_binding(binding, **raw)
    assert result["binding_consistent"]
    assert result["final_observer_exit"] == "NOT_SELF_OBSERVABLE"


@pytest.mark.parametrize("mutation", ["prior", "order", "exit", "peak", "observer", "stats"])
def test_false_exit_binding_rejects(mutation):
    binding, raw = binding_evidence()
    if mutation == "prior":
        raw["prior"] += b" "
    elif mutation == "order":
        binding["prior_status"] = "PENDING_VERIFIER_EXIT"
    elif mutation == "exit":
        binding["exit_code"] = 7
    elif mutation == "peak":
        binding["resource_cap_exceeded"] = True
    elif mutation == "observer":
        binding["actual_observer_verification"] = "PASS"
    else:
        binding["native"]["rss_bytes"] *= 1024
    with pytest.raises(ValueError):
        checker.audit_exit_binding(binding, **raw)
