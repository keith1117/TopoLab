"""Separate M2 scientific audit over explicit checked buffers and finite witnesses.

No candidate driver, classifier, Gate or resource-result helper is an oracle.
Foundational FEM/filter/OC and the published independent phase/native checker are
shared explicitly. Metadata functions do not grant execution or establish repair.
"""

import hashlib
import importlib.machinery
import importlib.metadata
import importlib.util
import json
import math
import os
import re
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IDENTITY = "topolab.v2.p17-m2-native-homotopy.rss.v1"
PARTITIONS = {
    "terminal_and_windows": 16632,
    "homotopy_prefix_and_transitions": 1368,
    "NN_label_input_reanalysis": 1056,
}
OPERATIONS = {
    "model_predictions": 270,
    "model_case_encodings": 270,
    "NN_distance_queries": 18,
    "NN_train_reencodings": 528,
    "checkpoint_decodes": 12,
    "projection_checks": 702,
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def resolve_argv(words, contract_sha):
    require(
        type(words) is list
        and words
        and all(type(w) is str and w for w in words)
        and type(contract_sha) is str
        and re.fullmatch(r"[0-9a-f]{64}", contract_sha),
        "scientific actual argv/hash required",
    )
    return [word.replace("@SCIENTIFIC_CONTRACT_SHA256@", contract_sha) for word in words]


def startup_argv(command, runtime):
    """Keep the observed startup executable distinct from the launch entry."""
    require(
        type(command) is list
        and command
        and command[0] == runtime["python_entry"]
        and type(runtime["python_startup_entry"]) is str
        and Path(runtime["python_startup_entry"]).is_absolute(),
        "scientific logical launch entry differs",
    )
    return [runtime["python_startup_entry"], *command[1:]]


def check_returned_startup(contract, role, payload, contract_sha):
    expected = startup_argv(
        resolve_argv(contract["roles"][role]["inner_starts"][0]["argv"], contract_sha),
        contract["runtime"],
    )
    actual = payload.get("actual_numerical_runtime", {})
    require(
        actual.get("python_entry") == contract["runtime"]["python_entry"]
        and actual.get("startup_orig_argv") == expected,
        "actual scientific startup argv differs",
    )


def helper(name):
    path = Path(__file__).with_name(name + ".py")
    existing = sys.modules.get(name)
    if existing is not None and Path(existing.__file__).resolve() == path.resolve():
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec and spec.loader, "independent scientific helper missing")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class AuditBudget:
    """Before-call disjoint numerical counters; no partition can borrow another."""

    def __init__(self, checkpoint=lambda: None):
        self.counts = dict.fromkeys(PARTITIONS, 0)
        self.operations = dict.fromkeys(OPERATIONS, 0)
        self.checkpoint = checkpoint

    def before(self, partition):
        self.checkpoint()
        require(
            partition in PARTITIONS and self.counts[partition] < PARTITIONS[partition],
            "STOP_SCOPE_OR_WORK_CAP: independent numerical partition exhausted",
        )
        self.counts[partition] += 1

    def before_operation(self, name):
        self.checkpoint()
        require(
            name in OPERATIONS and self.operations[name] < OPERATIONS[name],
            "STOP_SCOPE_OR_WORK_CAP: independent operation exhausted",
        )
        self.operations[name] += 1


def audit_terminal(case, witness, reference, *, accepted, budget=None, continuation_from=None):
    """Re-solve <=11 recent ordinary states plus terminal without a query oracle.

    Complete scalar trace is checked, while density replay is limited to the
    retained last eleven states. Earlier physical-plateau decisions are not
    represented as a replay of the full trajectory.
    """
    import numpy as np

    from topolab.fem import build_constrained_dofs, build_load_vector
    from topolab.mesh import generate_structured_hex8
    from topolab.model import FaceLoad, FixedFaceSupport, PointLoad
    from topolab.simp import apply_density_filter, build_density_filter, evaluate_compliance

    require(
        type(accepted) is bool
        and type(witness) is dict
        and set(witness) == {"witness_version", "trace", "result"}
        and witness["witness_version"] == "topolab.b3.query-state.v1",
        "ordinary witness identity differs",
    )
    require(
        type(reference) in (int, float) and math.isfinite(reference) and reference > 0,
        "finite positive uniform reference required",
    )
    problem, settings = case.problem, case.problem.optimization
    trace, result = witness["trace"], witness["result"]
    require(
        type(trace) is list and 1 <= len(trace) <= min(360, settings.max_iterations),
        "ordinary trace count differs",
    )
    fields = {"iteration", "compliance", "volume_fraction", "density_change"}
    for ordinal, row in enumerate(trace, 1):
        require(
            type(row) is dict
            and set(row) == fields
            and type(row["iteration"]) is int
            and row["iteration"] == ordinal
            and all(
                type(row[k]) in (int, float) and math.isfinite(row[k])
                for k in fields - {"iteration"}
            )
            and row["compliance"] > 0
            and 0 <= row["volume_fraction"] <= 1
            and row["density_change"] >= 0,
            "ordinary trace fields differ",
        )
    require(
        type(result) is dict
        and set(result)
        == {
            "design_density",
            "physical_density",
            "compliance",
            "displacements",
            "reactions",
            "history",
            "converged",
        }
        and type(result["converged"]) is bool,
        "ordinary terminal fields differ",
    )
    history = result["history"]
    require(
        type(history) is list and len(history) == min(11, len(trace)),
        "ordinary recent window differs",
    )
    mesh = generate_structured_hex8(*problem.mesh.element_counts, lengths=problem.mesh.lengths)
    constrained = build_constrained_dofs(
        mesh,
        [
            FixedFaceSupport(axis=s.axis, side=s.side, directions=s.directions)
            for s in problem.supports
        ],
    )
    loads = build_load_vector(
        mesh,
        [
            PointLoad(node=load.node, direction=load.direction, magnitude=load.magnitude)
            if load.kind == "point"
            else FaceLoad(
                axis=load.axis, side=load.side, direction=load.direction, total=load.total
            )
            for load in problem.loads
        ],
    )
    density_filter = build_density_filter(mesh, settings.filter_radius)
    count, fem = len(mesh.connectivity), 0

    def vector(value, size):
        array = np.asarray(value, dtype=np.float64)
        require(
            array.shape == (size,) and bool(np.isfinite(array).all()),
            "ordinary finite density/vector shape differs",
        )
        return array

    def analyze(physical):
        nonlocal fem
        if budget is not None:
            budget.before("terminal_and_windows")
        fem += 1
        return evaluate_compliance(
            mesh,
            physical,
            loads,
            constrained,
            solid_modulus=problem.material.solid_modulus,
            minimum_modulus=problem.material.minimum_modulus,
            poisson_ratio=problem.material.poisson_ratio,
            penalty=3,
        )

    previous, changes = None, []
    for state, point in zip(history, trace[-11:], strict=True):
        require(
            type(state) is dict
            and set(state) == fields | {"design_density", "physical_density"}
            and {k: state[k] for k in fields} == point,
            "ordinary scalar/state identity differs",
        )
        design = vector(state["design_density"], count)
        physical = vector(state["physical_density"], count)
        require(
            bool(np.all((design >= settings.minimum_density) & (design <= 1)))
            and bool(np.array_equal(apply_density_filter(density_filter, design), physical))
            and abs(float(np.mean(physical)) - state["volume_fraction"]) <= 1e-12,
            "ordinary bounds/filter/volume differ",
        )
        if previous is not None:
            require(
                float(np.max(np.abs(design - previous[0]))) == state["density_change"],
                "ordinary design change differs",
            )
            changes.append(float(np.max(np.abs(physical - previous[1]))))
        analysis = analyze(physical)
        require(
            bool(np.isclose(analysis.compliance, state["compliance"], rtol=1e-9, atol=0)),
            "ordinary window compliance differs",
        )
        previous = design, physical
    last = history[-1]
    require(
        result["design_density"] == last["design_density"]
        and result["physical_density"] == last["physical_density"]
        and result["compliance"] == last["compliance"],
        "ordinary terminal/state differs",
    )
    terminal = analyze(previous[1])
    require(
        bool(np.isclose(terminal.compliance, result["compliance"], rtol=1e-9, atol=0)),
        "ordinary terminal compliance differs",
    )
    dofs = len(mesh.coordinates) * 3
    require(
        bool(
            np.allclose(
                vector(result["displacements"], dofs), terminal.displacements, rtol=1e-9, atol=0
            )
        ),
        "terminal displacements differ",
    )
    require(
        bool(np.allclose(vector(result["reactions"], dofs), terminal.reactions, rtol=1e-9, atol=0)),
        "terminal reactions differ",
    )
    design_stop = last["density_change"] <= 0.01
    gain = (history[0]["compliance"] - last["compliance"]) / history[0]["compliance"]
    plateau = len(history) == 11 and max(changes) <= 0.01 and 0 <= gain <= 0.0002
    require(
        continuation_from is not None
        or not any(row["density_change"] <= 0.01 for row in trace[:-1]),
        "ordinary trajectory continued after design stop",
    )
    complete = continuation_from is None or len(trace) - continuation_from == 20
    require(
        result["converged"] is (complete and (design_stop or plateau)),
        "ordinary convergence flag differs",
    )
    require(
        result["converged"]
        or len(trace) == min(360, settings.max_iterations)
        or (continuation_from is not None and complete),
        "ordinary unconverged trajectory truncated",
    )
    volume = abs(float(np.mean(previous[1])) - settings.volume_fraction)
    quality = result["converged"] and volume <= 0.005 and terminal.compliance <= 1.001 * reference
    require(not accepted or quality, "false accepted ordinary classification")
    return {
        "quality_passed": bool(quality),
        "audit_fem": fem,
        "compliance": float(terminal.compliance),
        "volume_error": volume,
        "whole_trajectory_replayed": False,
    }


def _analysis(case, physical, budget, partition):
    from topolab.fem import build_constrained_dofs, build_load_vector
    from topolab.mesh import generate_structured_hex8
    from topolab.model import FaceLoad, FixedFaceSupport, PointLoad
    from topolab.simp import evaluate_compliance

    p = case.problem
    mesh = generate_structured_hex8(*p.mesh.element_counts, lengths=p.mesh.lengths)
    constraints = build_constrained_dofs(
        mesh,
        [FixedFaceSupport(axis=s.axis, side=s.side, directions=s.directions) for s in p.supports],
    )
    loads = build_load_vector(
        mesh,
        [
            PointLoad(node=x.node, direction=x.direction, magnitude=x.magnitude)
            if x.kind == "point"
            else FaceLoad(axis=x.axis, side=x.side, direction=x.direction, total=x.total)
            for x in p.loads
        ],
    )
    if budget is not None:
        budget.before(partition)
    return evaluate_compliance(
        mesh,
        physical,
        loads,
        constraints,
        solid_modulus=p.material.solid_modulus,
        minimum_modulus=p.material.minimum_modulus,
        poisson_ratio=p.material.poisson_ratio,
        penalty=3,
    )


def _initialization(case, method, models, neighbors, budget):
    import numpy as np
    import torch

    from topolab.experiment import encode_case

    p = case.problem
    nx, ny, nz = p.mesh.element_counts
    shape = (1, nz, ny, nx)
    if method in ("uniform", "uniform-homotopy"):
        return np.full(shape, p.optimization.volume_fraction, dtype=np.float32), None
    if method == "physics_heuristic":
        rho = np.full(nx * ny * nz, p.optimization.volume_fraction, dtype=np.float64)
        solved = _analysis(case, rho, budget, "terminal_and_windows")
        score = np.maximum(0, -solved.sensitivity)
        low, high = float(score.min()), float(score.max())
        raw = (score - low) / (high - low) if high > low else rho
        return raw.astype(np.float32).reshape(shape), None
    if method == "nearest_neighbor":
        budget.before_operation("NN_distance_queries")
        cohort = neighbors[(nx, ny, nz)]
        ids, inputs, designs = cohort
        query = encode_case(case).input_tensor
        delta = inputs.astype(np.float64) - query.astype(np.float64)
        distances = np.mean(delta * delta, axis=(1, 2, 3, 4))
        selected = int(np.argmin(distances))
        return designs[selected].copy(), {
            "case_id": ids[selected],
            "mean_squared_distance": float(distances[selected]),
        }
    family, seed = method.split("/")
    route = (
        "specialist"
        if (
            (nx, ny, nz) == (24, 12, 6)
            and p.loads[0].direction == "y"
            and p.optimization.volume_fraction >= 0.55
        )
        else "generalist"
    )
    recipe = (
        "S" if route == "specialist" else "P" if family in ("H", "P-keep", "plain-P") else family
    )
    model = models[(recipe, int(seed))]
    budget.before_operation("model_case_encodings")
    original = encode_case(case).input_tensor
    encoded = np.zeros((13, nz, ny, nx), dtype=np.float32)
    encoded[:10] = original
    encoded[3:6] = 0
    load = p.loads[0]
    axis = {"x": 0, "y": 1, "z": 2}[load.direction]
    encoded[3 + axis] = np.sign(load.magnitude)
    coordinates = (
        load.node % (nx + 1),
        load.node // (nx + 1) % (ny + 1),
        load.node // ((nx + 1) * (ny + 1)),
    )
    for dimension, (coordinate, cells) in enumerate(zip(coordinates, (nx, ny, nz), strict=True)):
        encoded[10 + dimension] = encoded[6 + dimension] - np.float32(coordinate / cells)
    model.eval()
    budget.before_operation("model_predictions")
    with torch.no_grad():
        predicted = model(torch.from_numpy(encoded.copy()).unsqueeze(0))
    require(
        predicted.shape == (1, 1, nz, ny, nx)
        and predicted.dtype == torch.float32
        and predicted.device.type == "cpu"
        and bool(torch.isfinite(predicted).all())
        and bool(((predicted >= 0) & (predicted <= 1)).all()),
        "independent model prediction is outside frozen domain",
    )
    return predicted[0].detach().numpy().copy(), (recipe, int(seed))


def _check_initialization(case, attempt, raw, budget):
    import numpy as np

    from topolab.experiment import project_design_density

    witness = attempt.get("initialization_witness")
    require(
        type(witness) is dict
        and witness.get("status") == "PROJECTED"
        and witness.get("raw_dtype") == str(raw.dtype)
        and witness.get("raw_shape") == list(raw.shape)
        and np.array_equal(np.asarray(witness["raw_density"]), raw.reshape(-1))
        and witness.get("raw_sha256") == digest(raw.astype(raw.dtype.newbyteorder("<")).tobytes()),
        "initialization raw words differ",
    )
    budget.before_operation("projection_checks")
    projected = project_design_density(case, raw)
    require(
        np.array_equal(projected.design_density, witness["projected_design_density"])
        and np.array_equal(projected.physical_density, witness["projected_physical_density"]),
        "initialization projection words differ",
    )
    phase = attempt.get("phase_witness")
    if phase is not None:
        require(
            phase["initial"]["design_density"] == witness["projected_design_density"]
            and phase["initial"]["physical_density"] == witness["projected_physical_density"],
            "homotopy initial state differs from actual projection",
        )


def audit_query(case, row, reference, *, models, neighbors, identities, budget=None):
    """Recompute initialization and all retained candidate/fallback witnesses."""
    budget = AuditBudget() if budget is None else budget
    old = helper("p17_m2_independent_audit")
    before = dict(budget.counts)
    method = row["method"]
    require(
        row.get("schema") == "topolab.v2.m2-scientific-query.v1"
        and row.get("case_id") == case.case_id
        and row.get("dispatched_method") == method.replace("plain-P/", "P/", 1),
        "scientific query identity differs",
    )
    baseline = method in ("uniform", "physics_heuristic", "nearest_neighbor", "uniform-homotopy")
    direction = case.problem.loads[0].direction
    scale = tuple(case.problem.mesh.element_counts)
    route = (
        "baseline"
        if baseline
        else "reject"
        if (direction not in ("y", "z") or scale not in ((12, 6, 3), (24, 12, 6)))
        else (
            "specialist"
            if scale == (24, 12, 6)
            and direction == "y"
            and case.problem.optimization.volume_fraction >= 0.55
            else "generalist"
        )
    )
    active = (method.startswith("H/") or method == "uniform-homotopy") and (
        scale == (24, 12, 6)
        and direction == "y"
        and case.problem.optimization.volume_fraction < 0.55
        and route != "specialist"
    )
    require(
        row["route"] == route and row["homotopy_active"] is active,
        "independent route/activation differs",
    )
    attempt, fallback = row["attempt"], row["fallback"]

    def inspect(packet, selected_method):
        if packet is None:
            return False, None
        require(type(packet.get("succeeded")) is bool, "attempt success must be boolean")
        raw, selected = _initialization(case, selected_method, models, neighbors, budget)
        _check_initialization(case, packet, raw, budget)
        if selected_method == "nearest_neighbor":
            require(
                packet["matched_case_id"] == selected["case_id"]
                and row["NN_match_witnesses"] == [selected],
                "independent NN match differs",
            )
        elif isinstance(selected, tuple):
            require(
                row["selected_weight_identity"] == identities[selected],
                "selected checked checkpoint identity differs",
            )
        phase, legacy, continuation = (
            packet["phase_witness"],
            packet["legacy_witness"],
            packet["continuation"],
        )
        if phase is not None:
            require(active and phase["active"] is True, "unexpected phase witness")
            original, numerical_calls = old.evaluate_compliance, 0

            def bounded_phase_analysis(*args, **kwargs):
                nonlocal numerical_calls
                partition = (
                    "homotopy_prefix_and_transitions"
                    if numerical_calls < 19
                    else "terminal_and_windows"
                )
                budget.before(partition)
                numerical_calls += 1
                return original(*args, **kwargs)

            old.evaluate_compliance = bounded_phase_analysis
            try:
                solved = old.audit_witness(case, phase, reference, accepted=packet["succeeded"])
            finally:
                old.evaluate_compliance = original
            require(
                solved["prefix_analyses"] == 19 and numerical_calls == solved["total_audit_fem"],
                "independent phase actual numerical count differs",
            )
            quality, terminal = solved["quality_passed"], phase["result"]
        elif continuation is not None:
            require(
                selected_method.startswith("P-keep/") and route == "generalist",
                "unexpected continuation witness",
            )
            first, last = continuation["before"], continuation["after"]
            first_result = audit_terminal(case, first, reference, accepted=False, budget=budget)
            count = len(first["trace"])
            require(last["trace"][:count] == first["trace"], "continuation changes original trace")
            qualifies = (
                scale == (24, 12, 6)
                and direction == "y"
                and case.problem.optimization.volume_fraction < 0.55
                and first["result"]["converged"]
                and first["trace"][-1]["density_change"] > 0.01
            )
            expected_updates = min(20, 360 - count) if qualifies else 0
            require(
                len(last["trace"]) - count == expected_updates, "continuation update count differs"
            )
            last_result = audit_terminal(
                case,
                last,
                reference,
                accepted=False,
                budget=budget,
                continuation_from=count if expected_updates else None,
            )
            choice = (
                "original"
                if qualifies and expected_updates == 20 and not (last["result"]["converged"])
                else "endpoint"
            )
            require(continuation["choice"] == choice, "independent own-state choice differs")
            chosen, solved = (first, first_result) if choice == "original" else (last, last_result)
            require(legacy == chosen, "selected own terminal witness differs")
            quality, terminal = solved["quality_passed"], chosen["result"]
        else:
            require(legacy is not None, "scientific ordinary attempt witness missing")
            solved = audit_terminal(
                case, legacy, reference, accepted=packet["succeeded"], budget=budget
            )
            quality, terminal = solved["quality_passed"], legacy["result"]
        require(packet["succeeded"] is bool(quality), "attempt quality classification differs")
        return bool(quality), terminal

    attempt_ok, terminal = (False, None) if route == "reject" else inspect(attempt, method)
    require((route == "reject") is (attempt is None), "rejected route attempt differs")
    needed_fallback = route == "reject" or (not attempt_ok and method != "uniform")
    require((fallback is not None) is needed_fallback, "fallback occurrence differs")
    fallback_ok = False
    if fallback is not None:
        fallback_ok, _ = inspect(fallback, "uniform")
    charged, wall = row["charged_seconds"], row["wall_seconds"]
    require(
        type(wall) in (int, float) and math.isfinite(wall) and wall >= 0 and charged == wall + 1,
        "scientific query row charge differs",
    )
    delta = {key: budget.counts[key] - before[key] for key in PARTITIONS}
    require(
        delta["terminal_and_windows"] <= 48 and delta["homotopy_prefix_and_transitions"] <= 19,
        "query independent partition cap exceeded",
    )
    return {
        "case_id": case.case_id,
        "method": method,
        "attempt_accepted": attempt_ok,
        "fallback_occurred": fallback is not None,
        "fallback_accepted": fallback_ok,
        "terminal_compliance": None if terminal is None else terminal["compliance"],
        "charged_seconds": charged,
        "independent_FEM": delta,
        "whole_trajectory_replayed": False,
    }


def audit_nn_pair(producer, audit, *, budget):
    """Check two same-buffer train views and exactly two independent FEM analyses."""
    import numpy as np

    from topolab.experiment import ExperimentCase, encode_case
    from topolab.mesh import generate_structured_hex8
    from topolab.simp import (
        apply_density_filter,
        backpropagate_density_gradient,
        build_density_filter,
    )

    require(
        producer.get("schema") == "topolab.v2.m2-nn-producer-view.v1"
        and audit.get("schema") == "topolab.v2.m2-nn-audit-view.v1"
        and all(
            producer.get(k) == audit.get(k)
            for k in ("case", "membership", "initialization", "source")
        )
        and producer["membership"].get("role") == "train",
        "independent train-only NN view provenance differs",
    )
    case = ExperimentCase.model_validate(producer["case"])
    p, stored, terminal = case.problem, audit["stored"], audit["terminal"]
    nx, ny, nz = p.mesh.element_counts
    count = nx * ny * nz
    data = helper("p17_m2_input_export_independent")
    require(
        producer["stored"]
        == {
            k: stored[k]
            for k in ("tensor_dtype", "tensor_axis_order", "tensor_shape", "design_density")
        }
        and stored["tensor_dtype"] == "float32"
        and stored["tensor_shape"] == [1, nz, ny, nx]
        and stored["tensor_axis_order"] == "channel,z,y,x",
        "NN stored producer words differ",
    )
    for name in ("design_density", "physical_density", "sensitivity_weight"):
        require(
            data.vector_sha(stored[name], 32, count, exact_f32=True)
            == audit["bit_digests"]["/stored/" + name],
            "NN stored bit digest differs",
        )
    require(
        producer["bit_digests"]
        == {"/stored/design_density": audit["bit_digests"]["/stored/design_density"]},
        "NN producer bit digest differs",
    )
    mesh = generate_structured_hex8(nx, ny, nz, lengths=p.mesh.lengths)
    filt = build_density_filter(mesh, p.optimization.filter_radius)
    design = np.asarray(stored["design_density"], dtype=np.float32)
    physical = np.asarray(stored["physical_density"], dtype=np.float32)
    require(
        bool(np.all((design >= np.float32(p.optimization.minimum_density)) & (design <= 1)))
        and np.array_equal(
            apply_density_filter(filt, design.astype(np.float64)).astype(np.float32), physical
        )
        and float(np.mean(physical, dtype=np.float64)) == stored["physical_volume_fraction"]
        and abs(stored["physical_volume_fraction"] - p.optimization.volume_fraction) <= 0.005,
        "NN stored density/filter/volume differs",
    )
    solved = _analysis(case, physical.astype(np.float64), budget, "NN_label_input_reanalysis")
    require(
        np.isclose(solved.compliance, stored["compliance"], rtol=1e-9, atol=0),
        "NN stored compliance differs",
    )
    gradient = np.abs(backpropagate_density_gradient(filt, solved.sensitivity))
    require(np.isfinite(gradient).all() and gradient.mean() > 0, "NN sensitivity scale differs")
    clipped = np.clip(gradient / float(gradient.mean()), 0.25, 4)
    weights = (clipped / float(clipped.mean())).astype(np.float32)
    require(np.array_equal(weights, stored["sensitivity_weight"]), "NN stored weights differ")
    terminal_design = np.asarray(terminal["design_density"], dtype=np.float64)
    terminal_physical = np.asarray(terminal["physical_density"], dtype=np.float64)
    require(
        np.array_equal(apply_density_filter(filt, terminal_design), terminal_physical)
        and np.array_equal(terminal_design.astype(np.float32), design)
        and terminal["converged"] is True,
        "NN terminal/filter/stored design differs",
    )
    for name in ("design_density", "physical_density"):
        require(
            data.vector_sha(terminal[name], 64, count) == audit["bit_digests"]["/result/" + name],
            "NN terminal bits differ",
        )
    terminal_solved = _analysis(case, terminal_physical, budget, "NN_label_input_reanalysis")
    require(
        np.isclose(terminal_solved.compliance, terminal["compliance"], rtol=1e-9, atol=0)
        and abs(float(terminal_physical.mean()) - p.optimization.volume_fraction) <= 0.005,
        "NN original terminal compliance/volume differs",
    )
    recent, updates = audit["recent"], audit["total_updates"]
    require(
        type(updates) is int
        and 1 <= updates <= 360
        and stored["iterations"] == updates
        and len(recent) == min(11, updates),
        "NN original termination count differs",
    )
    changes, previous = [], None
    for i, state in enumerate(recent, updates - len(recent) + 1):
        require(state["iteration"] == i, "NN recent state ordinal differs")
        x, rho = np.asarray(state["design_density"]), np.asarray(state["physical_density"])
        require(
            np.isfinite(x).all()
            and np.isfinite(rho).all()
            and np.all((x >= p.optimization.minimum_density) & (x <= 1))
            and np.array_equal(apply_density_filter(filt, x), rho)
            and abs(float(rho.mean()) - state["volume_fraction"]) <= 1e-12,
            "NN recent state density/filter differs",
        )
        for name in ("design_density", "physical_density"):
            require(
                data.vector_sha(state[name], 64, count)
                == audit["bit_digests"][f"/result/history/{i - 1}/{name}"],
                "NN recent bits differ",
            )
        if previous is not None:
            require(
                float(np.max(np.abs(x - previous[0]))) == state["density_change"],
                "NN recent design change differs",
            )
            changes.append(float(np.max(np.abs(rho - previous[1]))))
        previous = x, rho
    last = recent[-1]
    gain = (recent[0]["compliance"] - last["compliance"]) / recent[0]["compliance"]
    require(
        all(last[k] == terminal[k] for k in ("design_density", "physical_density", "compliance"))
        and stored["terminal_density_change"] == last["density_change"]
        and (
            last["density_change"] <= 0.01
            or (len(recent) == 11 and max(changes) <= 0.01 and 0 <= gain <= 0.0002)
        ),
        "NN original terminal convergence differs",
    )
    budget.before_operation("NN_train_reencodings")
    return case, encode_case(case).input_tensor, design.reshape(1, nz, ny, nx)


def load_audit_assets(consumer, contract_sha256, *, budget):
    """Read exactly the new auditor1070 union once, retaining no full old history."""
    import numpy as np
    import torch
    from safetensors.torch import load as decode_weights

    from topolab.b2_12_context_cnn import ContextCNN

    require(
        torch.get_num_threads() == 1 and torch.get_num_interop_threads() == 8,
        "actual independent numerical Torch threads differ",
    )
    verified = helper("p17_m2_source_verified_input")
    require(
        isinstance(consumer, verified.VerifiedAcquisitionInput)
        and isinstance(consumer.certificate, CheckedScientificInput)
        and consumer.role == "scientific-auditor",
        "opaque scientific auditor input required",
    )
    binding = consumer.certificate.binding_for(consumer.role, reader_lease=consumer.lease)
    require(
        binding["scientific_contract_sha256"] == contract_sha256
        and binding["scientific_permissions"].get("auditor") is True,
        "separate scientific auditor grant required",
    )
    parser = helper("p17_m2_input_export_independent")
    manifest = {r["path"]: r for r in binding["manifest"]["members"]}
    model_view = consumer.consume("models.json", parser.parse)
    expected_models = {(f, s) for f in ("C", "P", "W", "S") for s in (17, 29, 43)}
    require(
        model_view["schema"] == "topolab.v2.m2-checkpoint-view.v1"
        and len(model_view["models"]) == 12
        and {(m["family"], m["seed"]) for m in model_view["models"]} == expected_models,
        "auditor fixed12 models differ",
    )
    content = parser.parse(acquisition.native._software_bytes(REPO / acquisition.CONTENT_CONTRACT))
    epochs = {
        (m["family"], m["seed"]): m["selected_epoch"] for m in content["checkpoints"]["fixed_rows"]
    }
    models, identities = {}, {}
    for item in model_view["models"]:
        key = item["family"], item["seed"]
        name = f"checkpoints/{key[0]}-{key[1]}.safetensors"
        require(
            item["epoch"] == epochs[key]
            and item["output"] == {k: manifest[name][k] for k in ("path", "byte_size", "sha256")},
            "auditor fixed checkpoint epoch/output differs",
        )

        def weights(raw, item=item):
            parser.check_safetensors(raw, item)
            budget.before_operation("checkpoint_decodes")
            return decode_weights(raw)

        tensors = consumer.consume(name, weights)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(0)
            model = ContextCNN()
        require(
            set(tensors) == set(model.state_dict())
            and all(
                t.dtype == torch.float32
                and t.device.type == "cpu"
                and bool(torch.isfinite(t).all())
                for t in tensors.values()
            ),
            "auditor finite CPU F32 model differs",
        )
        model.load_state_dict(tensors, strict=True)
        model.eval()
        word_hash = hashlib.sha256()
        for parameter, tensor in sorted(model.state_dict().items()):
            word_hash.update(
                canonical(
                    {"name": parameter, "shape": list(tensor.shape), "dtype": str(tensor.dtype)}
                )
            )
            word_hash.update(tensor.detach().numpy().astype("<f4").tobytes())
        models[key] = model
        identities[key] = {
            "family": key[0],
            "seed": key[1],
            "epoch": item["epoch"],
            "context_sha256": item["context_sha256"],
            "checkpoint_sha256": item["output"]["sha256"],
            "parameter_sha256": word_hash.hexdigest(),
        }
    paths = sorted(
        name for name in binding["role_views"][consumer.role] if name.startswith("nn/producer/")
    )
    require(len(paths) == 528, "auditor exact528 NN inputs required")
    grouped = {}
    for name in paths:
        producer = consumer.consume(name, parser.parse)
        audit = consumer.consume(name.replace("/producer/", "/audit/"), parser.parse)
        case, encoded, design = audit_nn_pair(producer, audit, budget=budget)
        require(Path(name).stem == case.case_id, "auditor NN member case differs")
        grouped.setdefault(tuple(case.problem.mesh.element_counts), []).append(
            (case.case_id, encoded, design)
        )
    neighbors = {}
    for scale, n in (((12, 6, 3), 432), ((24, 12, 6), 96)):
        rows = grouped.get(scale, [])
        ids = tuple(row[0] for row in rows)
        require(
            len(rows) == n and ids == tuple(sorted(set(ids))),
            "auditor exact ordered per-scale NN population differs",
        )
        neighbors[scale] = (ids, np.stack([r[1] for r in rows]), np.stack([r[2] for r in rows]))
    scalar_packet = consumer.consume("uniform-scalars.json", parser.parse)
    require(
        scalar_packet["schema"] == "topolab.v2.m2-uniform-scalar-view.v1"
        and len(scalar_packet["values"]) == 18,
        "auditor exact18 scalar references required",
    )
    references = {}
    import struct

    for value in scalar_packet["values"]:
        scalar = value["compliance"]
        require(
            type(scalar) in (int, float)
            and math.isfinite(scalar)
            and scalar > 0
            and value["compliance_bits_sha256"] == digest(struct.pack("<d", scalar))
            and value["case_id"] not in references,
            "auditor scalar words/case differ",
        )
        references[value["case_id"]] = scalar
    require(
        len(consumer.reader.source_observations) == 1070
        and budget.counts["NN_label_input_reanalysis"] == 1056,
        "auditor input read/numerical closure differs",
    )
    return {
        "models": models,
        "identities": identities,
        "neighbors": neighbors,
        "old_uniform_scalars": references,
        "member_reads": 1070,
        "member_hashes": {name: value["sha256"] for name, value in manifest.items()},
    }


def check_row_input_setup(case, row, member_hashes, neighbors):
    """Bind measured cold row setup to the independently checked source buffers."""
    method, facts = row["method"], row["row_input_setup"]
    expected = dict.fromkeys(
        ("checkpoint_decodes", "NN_case_reencodes", "NN_index_builds", "buffer_rehashes"), 0
    )
    scale = tuple(case.problem.mesh.element_counts)
    paths = []
    if "/" in method and scale in ((12, 6, 3), (24, 12, 6)):
        direction = case.problem.loads[0].direction
        if direction in ("y", "z"):
            family, seed = method.split("/")
            family = (
                "S"
                if scale == (24, 12, 6)
                and direction == "y"
                and case.problem.optimization.volume_fraction >= 0.55
                else "P"
                if family in ("H", "plain-P", "P-keep")
                else family
            )
            paths = [f"checkpoints/{family}-{seed}.safetensors"]
            expected["checkpoint_decodes"] = 1
    elif method == "nearest_neighbor":
        ids = neighbors[scale][0]
        count = 432 if scale == (12, 6, 3) else 96
        require(
            len(ids) == count and tuple(ids) == tuple(sorted(set(ids))),
            "row exact independent NN population differs",
        )
        paths = [f"nn/producer/{case_id}.json" for case_id in ids]
        expected["NN_case_reencodes"], expected["NN_index_builds"] = count, 1
    expected["buffer_rehashes"] = len(paths)
    require(
        type(facts) is dict
        and set(facts)
        == set(expected) | {"source_file_rereads", "selected_buffers", "wall_seconds"}
        and all(type(facts.get(k)) is int and facts[k] == v for k, v in expected.items())
        and type(facts.get("source_file_rereads")) is int
        and facts["source_file_rereads"] == 0
        and type(facts.get("wall_seconds")) in (int, float)
        and math.isfinite(facts["wall_seconds"])
        and 0 <= facts["wall_seconds"] <= row["wall_seconds"],
        "row cold input work/count/wall differs",
    )
    require(
        facts["selected_buffers"]
        == [{"path": path, "sha256": member_hashes[path]} for path in paths],
        "row selected verified buffers differ",
    )
    return expected


def assess_panel(proposal, case_metadata, rows, historical_accepted):
    """Independent arithmetic on already checked rows; no resource/repair grant."""
    pilot, acceptance = proposal["prospective_pilot"], proposal["acceptance"]
    ids, methods = pilot["case_ids"], pilot["methods"]
    lookup = {(row["case_id"], row["method"]): row for row in rows}
    require(
        len(rows) == len(lookup) == 342
        and set(lookup) == {(case, method) for case in ids for method in methods}
        and set(case_metadata) == set(ids),
        "complete independent18x19 panel required",
    )
    for row in rows:
        require(
            type(row["attempt_accepted"]) is bool
            and type(row["fallback_occurred"]) is bool
            and type(row["charged_seconds"]) in (int, float)
            and math.isfinite(row["charged_seconds"])
            and row["charged_seconds"] >= 1,
            "independent scientific metric fields differ",
        )
    negative = set(acceptance["negative_control_case_ids"])
    target = "tlcase-v1-55c1b3e64135c23125fc286de5d780fc5d9a1e226d5e43ff0dbc8925b423936a"
    historical_failures = {(target, seed) for seed in (17, 29, 43)} | {
        (case_id, 29) for case_id in negative
    }
    expected_old = {
        (case_id, seed) for case_id in ids for seed in (17, 29, 43)
    } - historical_failures
    actual_old = {(r["case_id"], r["seed"]) for r in historical_accepted}
    require(
        len(historical_accepted) == len(actual_old) == 49 and actual_old == expected_old,
        "complete historical49 accepted P cells required",
    )
    predicates, metrics = {}, {}

    def population(method, selected):
        require(selected, "empty scientific metric population")
        values = [lookup[(case, method)]["charged_seconds"] for case in selected]
        uniform = [lookup[(case, "uniform")]["charged_seconds"] for case in selected]
        return {
            "mean_ratio": sum(v / u for v, u in zip(values, uniform, strict=True)) / len(values),
            "sum_ratio": sum(values) / sum(uniform),
            "failed_attempts": sum(
                not lookup[(case, method)]["attempt_accepted"] for case in selected
            ),
        }

    primary = [lookup[(case, "H/17")] for case in ids]
    predicates["fixed_H17_zero_failed_attempts_and_fallbacks"] = all(
        row["attempt_accepted"] and not row["fallback_occurred"] for row in primary
    )
    predicates["all_seven_historical_target_predicates_repaired"] = all(
        lookup[(r["case_id"], r["policy"])]["attempt_accepted"]
        for r in acceptance["target_predicates"]
    )
    predicates["historical_49_P_acceptances_preserved"] = all(
        lookup[(case_id, f"H/{seed}")]["attempt_accepted"] for case_id, seed in actual_old
    )
    predicates["matched_plain_P_and_P_keep_acceptances_preserved"] = all(
        not lookup[(case_id, f"{control}/{seed}")]["attempt_accepted"]
        or lookup[(case_id, f"H/{seed}")]["attempt_accepted"]
        for case_id in ids
        for seed in (17, 29, 43)
        for control in ("plain-P", "P-keep")
    )
    predicates["two_old_small_z_negative_failures_retained"] = all(
        not lookup[(case_id, method)]["attempt_accepted"]
        for case_id in negative
        for method in ("plain-P/29", "H/29")
    )
    predicates["fixed_plain_P17_counterexample_retained"] = not lookup[(target, "plain-P/17")][
        "attempt_accepted"
    ]
    target_ids = [
        case
        for case in ids
        if case_metadata[case]["scale"] == (24, 12, 6)
        and case_metadata[case]["direction"] == "y"
        and case_metadata[case]["volume"] < 0.55
    ]
    require(len(target_ids) == 13, "exact13 fixed target population required")
    target_metric = population("H/17", target_ids)
    predicates["primary_target_mean_and_sum_at_most_one"] = (
        target_metric["mean_ratio"] <= 1 and target_metric["sum_ratio"] <= 1
    )
    metrics["H17_target"] = target_metric
    for method in methods:
        metrics[method] = population(method, ids)
    h17 = metrics["H/17"]
    predicates["primary_strictly_better_fixed_controls"] = all(
        h17["mean_ratio"] < metrics[method]["mean_ratio"]
        for method in ("C/17", "physics_heuristic", "nearest_neighbor", "uniform-homotopy")
    )
    predicates["primary_better_than_W17"] = (
        h17["mean_ratio"] < metrics["W/17"]["mean_ratio"]
        or h17["failed_attempts"] < metrics["W/17"]["failed_attempts"]
    )
    passing, seed_gates = [], {}
    predicates["primary_each_scale_mean_and_sum_at_most_point_nine"] = True
    for seed in (17, 29, 43):
        method = f"H/{seed}"
        seed_ok = True
        for scale in ((12, 6, 3), (24, 12, 6)):
            group = [case for case in ids if case_metadata[case]["scale"] == scale]
            result = population(method, group)
            metrics[f"{method}:{scale}"] = result
            seed_ok &= result["mean_ratio"] <= 0.90
            if seed == 17:
                predicates["primary_each_scale_mean_and_sum_at_most_point_nine"] &= (
                    result["mean_ratio"] <= 0.90 and result["sum_ratio"] <= 0.90
                )
            for direction in sorted({case_metadata[case]["direction"] for case in group}):
                directed = [case for case in group if case_metadata[case]["direction"] == direction]
                seed_ok &= population(method, directed)["mean_ratio"] <= 1
        seed_ok &= metrics[method]["failed_attempts"] <= min(
            2, metrics[f"C/{seed}"]["failed_attempts"], metrics[f"W/{seed}"]["failed_attempts"]
        )
        non_specialist_y = [
            case
            for case in ids
            if case_metadata[case]["direction"] == "y"
            and not (
                case_metadata[case]["scale"] == (24, 12, 6)
                and case_metadata[case]["volume"] >= 0.55
            )
        ]
        seed_ok &= population(method, non_specialist_y)["failed_attempts"] <= min(
            population(f"C/{seed}", non_specialist_y)["failed_attempts"],
            population(f"W/{seed}", non_specialist_y)["failed_attempts"],
        )
        seed_ok &= all(
            metrics[method]["mean_ratio"] < metrics[baseline]["mean_ratio"]
            for baseline in ("physics_heuristic", "nearest_neighbor")
        )
        seed_gates[method] = bool(seed_ok)
        if seed_ok:
            passing.append(seed)
    predicates["at_least_two_H_seeds_and_fixed_H17_pass"] = len(passing) >= 2 and 17 in passing
    failed = [name for name, passed in predicates.items() if not passed]
    outcome = (
        "STOP_ROUTE_NOT_ISOLATED"
        if not predicates["fixed_plain_P17_counterexample_retained"]
        else "FAIL_SCIENCE_GATE" if failed
        else "SCIENTIFIC_PREDICATES_PASS_PENDING_NATIVE_EXIT"
    )
    return {
        "scientific_predicates_passed": not failed,
        "outcome_status": outcome,
        "predicates": predicates,
        "failed_predicates": failed,
        "metrics": metrics,
        "passing_H_seeds": passing,
        "seed_gate_results": seed_gates,
        "resource_and_actual_return": "NOT_ESTABLISHED_BY_METRIC_ARITHMETIC",
    }


def checked_output_reference(desc, phase, expected):
    """Validate the producer's literal streamed packet/cost path before opening it."""
    case_id, method, ordinal = expected["case_id"], expected["method"], expected["ordinal"]
    require(phase in ("reference", "query"), "scientific output phase differs")
    directory = "references" if phase == "reference" else "queries"
    require(
        desc["phase"] == phase
        and desc["case_id"] == case_id
        and desc["method"] == method
        and desc["ordinal"] == ordinal
        and desc["packet"]["path"]
        == (f"{directory}/{ordinal:03}-{case_id}-{method.replace('/', '-')}.json")
        and desc["cost"]["path"] == f"row-costs/{phase}-{ordinal:03}.json",
        "producer exact packet/cost literal order differs",
    )
    return desc["packet"], desc["cost"]


def retain_audit_failure(error, failure, writer):
    """Keep the original error and complete facts when persistent filing fails."""
    error.scientific_failure = failure
    error.scientific_failure_stderr_written = False
    try:
        writer("auditor-failure.json", failure)
    except BaseException as secondary:
        failure["secondary_errors"].append(
            {
                "stage": "auditor-failure.json",
                "type": type(secondary).__name__,
                "reason": str(secondary),
            }
        )
        try:
            raw = canonical(
                {
                    "schema": "topolab.v2.m2-scientific-auditor-native-failure.v1",
                    "failure": failure,
                }
            )
            require(len(raw) <= 64 * 1024**2, "native auditor failure log64MiB cap exceeded")
            sys.stderr.write(raw.decode("ascii"))
            sys.stderr.flush()
            error.scientific_failure_stderr_written = True
        except BaseException as recording:
            failure["secondary_errors"].append(
                {
                    "stage": "native-stderr-fallback",
                    "type": type(recording).__name__,
                    "reason": str(recording),
                }
            )


def audit_panel(
    contract, consumer, *, contract_sha256, producer_root, producer_return, checkpoint, writer
):
    """Audit the exact complete streamed panel against actual producer return bytes."""
    from time import perf_counter

    from topolab.experiment import ExperimentCase

    require(
        isinstance(producer_return, CheckedScientificReturn)
        and producer_return.role == "scientific-producer"
        and producer_return.contract_sha256 == contract_sha256,
        "actual checked producer return required before panel audit",
    )
    require(check_contract(contract) == contract_sha256, "scientific audit contract hash differs")
    expected_root = Path(contract["roles"]["scientific-producer"]["root"]) / "rows"
    require(
        Path(producer_root).absolute() == expected_root, "scientific producer literal root differs"
    )
    began, attempted, internal_charge = perf_counter(), 0, 0.0
    completed, current_row = [], None

    def bounded():
        checkpoint()
        require(
            max(internal_charge, perf_counter() - began + attempted + 10) <= 3600,
            "STOP_SCOPE_OR_WORK_CAP: complete independent audit3600 exhausted",
        )

    budget = AuditBudget(bounded)
    source_reader = helper("p17_m2_input_export").Reader(
        expected_root,
        execution_identity=helper("p17_m2_input_export").LOCAL_IDENTITY,
        source_identity_checks=True,
    )
    parser = helper("p17_m2_input_export_independent")

    def read_new(ref):
        raw = source_reader.read(
            ref["path"],
            16 * 1024**2,
            expected=ref["sha256"],
            size=ref["byte_size"],
            group="new-scientific-output",
            total=8 * 1024**3,
        )
        return parser.parse(raw, canonical_required=True)

    def write_new(name, value):
        raw = canonical(value)
        require(len(raw) <= 16 * 1024**2, "independent output member cap exceeded")
        receipt = writer(name, value)
        require(
            receipt == {"path": name, "byte_size": len(raw), "sha256": digest(raw)},
            "independent actual writer receipt differs",
        )
        return receipt

    try:
        assets = load_audit_assets(consumer, contract_sha256, budget=budget)
        proposal = parser.parse(
            acquisition.native._software_bytes(
                REPO / "docs/planning/p17_m2_native_homotopy_proposal.json"
            )
        )
        cases = [ExperimentCase.model_validate(value) for value in contract["case_definitions"]]
        require(
            [c.case_id for c in cases] == proposal["prospective_pilot"]["case_ids"]
            and digest(canonical(contract["case_definitions"]))
            == proposal["prospective_pilot"]["case_definitions_sha256"],
            "independent frozen18 case definitions differ",
        )
        case_map = {case.case_id: case for case in cases}
        returned = parser.parse(producer_return.command_log)
        anchored_summary = returned["result"]
        summary_ref = anchored_summary["summary_packet"]
        require(summary_ref["path"] == "producer-summary.json", "producer summary literal differs")
        summary = read_new(summary_ref)
        require(
            dict(summary, summary_packet=summary_ref) == anchored_summary
            and summary["scientific_contract_sha256"] == contract_sha256
            and summary["status"] == "PRODUCER_PANEL_COMPLETE_PENDING_INDEPENDENT_AUDIT"
            and summary["attempted_rows"] == len(summary["rows"]) == 360,
            "actual producer summary/complete population differs",
        )
        table = contract["call_plan"]
        ordered = [
            (phase, row)
            for phase, key in (("reference", "references"), ("query", "queries"))
            for row in table[key]
        ]
        expected_pairs = [
            (case.case_id, method)
            for case in cases
            for method in proposal["prospective_pilot"]["methods"]
        ]
        require(
            len(table["references"]) == 18
            and len(table["queries"]) == 342
            and [(r["case_id"], r["method"]) for r in table["queries"]] == expected_pairs
            and [r["case_id"] for r in table["references"]] == list(case_map),
            "complete independent call order differs",
        )
        references, metrics_rows, producer_operations = {}, [], {}
        setup_totals = dict.fromkeys(
            ("checkpoint_decodes", "NN_case_reencodes", "NN_index_builds", "buffer_rehashes"), 0
        )
        for desc, (phase, expected) in zip(summary["rows"], ordered, strict=True):
            current_row = {"phase": phase, **expected}
            bounded()
            row_started = perf_counter()
            attempted += 1
            case_id, method = expected["case_id"], expected["method"]
            ordinal = expected["ordinal"]
            checked_output_reference(desc, phase, expected)
            row, cost = read_new(desc["packet"]), read_new(desc["cost"])
            require(
                row["phase"] == phase
                and row["execution_identity"] == IDENTITY
                and row["scientific_contract_sha256"] == contract_sha256
                and cost["packet_sha256"] == desc["packet"]["sha256"]
                and cost["phase"] == phase
                and cost["ordinal"] == ordinal
                and cost["case_id"] == case_id
                and cost["method"] == method
                and cost["charged_seconds"] == desc["charged_seconds"]
                and cost["charged_seconds"] >= row["charged_seconds"]
                and cost["charged_seconds"]
                >= cost["through_actual_packet_writer_return_seconds"] + 1,
                "producer row actual write/cost identity differs",
            )
            reference = (
                assets["old_uniform_scalars"][case_id]
                if phase == "reference"
                else references[case_id]
            )
            setup = check_row_input_setup(
                case_map[case_id], row, assets["member_hashes"], assets["neighbors"]
            )
            for name, count in setup.items():
                setup_totals[name] += count
            audited = audit_query(
                case_map[case_id],
                row,
                reference,
                models=assets["models"],
                neighbors=assets["neighbors"],
                identities=assets["identities"],
                budget=budget,
            )
            audited["charged_seconds"] = cost["charged_seconds"]
            if phase == "reference":
                compliance = audited["terminal_compliance"]
                require(
                    method == "uniform"
                    and audited["attempt_accepted"]
                    and not audited["fallback_occurred"]
                    and abs(compliance - reference) <= 1e-9 * abs(reference),
                    "STOP_ROUTE_NOT_ISOLATED: independent uniform scalar mismatch",
                )
                references[case_id] = compliance
                require(
                    audited["independent_FEM"]["terminal_and_windows"] <= 12,
                    "independent reference12 numerical cap exceeded",
                )
            else:
                metrics_rows.append(audited)
            for name, count in row["measured_operations"].items():
                producer_operations[name] = producer_operations.get(name, 0) + count
            require(
                producer_operations.get("FEM", 0) <= 254808,
                "producer actual operation ceiling exceeded",
            )
            duration = perf_counter() - row_started
            internal_charge += duration + 1
            audit_packet = {
                "phase": phase,
                "ordinal": ordinal,
                **audited,
                "audit_wall_seconds": duration,
                "audit_charged_seconds": duration + 1,
            }
            write_new(f"audited/{phase}-{ordinal:03}.json", audit_packet)
            completed.append(
                {
                    "phase": phase,
                    "ordinal": ordinal,
                    "case_id": case_id,
                    "method": method,
                    "attempt_accepted": audited["attempt_accepted"],
                }
            )
        require(
            producer_operations == summary["measured_operations"]
            and setup_totals == summary["query_input_setup_operations"]
            and setup_totals
            == {
                "checkpoint_decodes": 270,
                "NN_case_reencodes": 2736,
                "NN_index_builds": 18,
                "buffer_rehashes": 3006,
            }
            and abs(
                sum(r["charged_seconds"] for r in summary["rows"])
                - summary["internal_row_charge_seconds"]
            )
            <= 1e-9,
            "complete producer accounting closure differs",
        )
        for path_key, sha_key in (
            ("report_path", "report_sha256"),
            ("contract_path", "contract_sha256"),
        ):
            evidence = contract["historical_accepted_P_evidence"]
            allowed = {
                "docs/validation/b4_30_paid_continuation.md",
                "docs/planning/b4_30_z_reflection_repair_contract.json",
            }
            require(
                evidence[path_key] in allowed
                and digest(acquisition.native._software_bytes(REPO / evidence[path_key]))
                == evidence[sha_key],
                "historical accepted P metadata freeze differs",
            )
        metadata = {
            case.case_id: {
                "scale": tuple(case.problem.mesh.element_counts),
                "direction": case.problem.loads[0].direction,
                "volume": case.problem.optimization.volume_fraction,
            }
            for case in cases
        }
        decision = assess_panel(
            proposal, metadata, metrics_rows, contract["historical_accepted_P_units"]
        )
        summary = {
            "schema": "topolab.v2.m2-scientific-auditor-summary.v1",
            "execution_identity": IDENTITY,
            "scientific_contract_sha256": contract_sha256,
            "status": decision["outcome_status"],
            "attempted_rows": attempted,
            "completed_rows": completed,
            "decision": decision,
            "independent_FEM": dict(budget.counts),
            "independent_operations": dict(budget.operations),
            "producer_query_input_setup_operations": setup_totals,
            "internal_row_charge_seconds": internal_charge,
            "known_role_charge_lower_bound_seconds": max(
                internal_charge, perf_counter() - began + attempted + 10
            ),
            "producer_return_verified": producer_return.proof,
            "own_resource_and_actual_exit": "PENDING_INDEPENDENT_NATIVE_OUTER_RETURN",
            "seed17_repaired": "NOT_ESTABLISHED_BEFORE_OWN_NATIVE_RETURN",
        }
        summary["summary_packet"] = write_new("auditor-summary.json", summary)
        return {"result": summary, "reader_pending": consumer.lease.pending_return()}
    except BaseException as error:
        failure = {
            "schema": "topolab.v2.m2-scientific-auditor-failure.v1",
            "status": "STOP_NO_RETRY",
            "execution_identity": IDENTITY,
            "scientific_contract_sha256": contract_sha256,
            "error_type": type(error).__name__,
            "reason": str(error),
            "attempted_rows": attempted,
            "completed_rows": completed,
            "independent_FEM": dict(budget.counts),
            "independent_operations": dict(budget.operations),
            "wall_seconds": perf_counter() - began,
            "internal_row_charge_seconds": internal_charge,
            "known_role_charge_lower_bound_seconds": max(
                internal_charge, perf_counter() - began + attempted + 10
            ),
            "secondary_errors": [],
        }
        failure.update(
            current_row=current_row,
            input_failure=deepcopy(consumer.failure),
            input_source_observations=deepcopy(consumer.reader.source_observations),
            input_source_facts=deepcopy(consumer.reader.source_facts),
            input_source_failures=deepcopy(consumer.reader.failures),
            new_output_observations=deepcopy(source_reader.source_observations),
            new_output_facts=deepcopy(source_reader.source_facts),
            new_output_failures=deepcopy(source_reader.failures),
            reader_lease={
                "path": consumer.lease.path,
                "token": consumer.lease.token,
                "state": consumer.lease.state,
            },
        )
        retain_audit_failure(error, failure, write_new)
        raise


_SCIENCE_AUTHORITY = object()
acquisition = helper("p17_m2_source_acquisition_independent")


class CheckedBAdmission:
    """Process-local independently replayed B; cannot be a serialized PASS."""

    __slots__ = ("contract_sha256", "proof")

    def __init__(self, contract_sha256, proof, *, _authority=None):
        require(_authority is _SCIENCE_AUTHORITY, "actual checked B admission required")
        self.contract_sha256, self.proof = contract_sha256, deepcopy(proof)

    def __reduce_ex__(self, protocol):
        raise TypeError("replay actual B evidence; checked admission cannot be serialized")


class CheckedScientificReturn:
    __slots__ = ("contract_sha256", "role", "proof", "command_log")

    def __init__(self, contract_sha256, role, proof, command_log, *, _authority=None):
        require(_authority is _SCIENCE_AUTHORITY, "actual checked scientific return required")
        self.contract_sha256, self.role = contract_sha256, role
        self.proof, self.command_log = deepcopy(proof), command_log

    def __reduce_ex__(self, protocol):
        raise TypeError("replay actual C evidence; checked return cannot be serialized")


class CheckedPublicScientificReturn:
    """NEW public buffer smoke return; grants no formal C acceptance."""

    __slots__ = ("contract_sha256", "role", "proof", "command_log")

    def __init__(self, contract_sha256, role, proof, command_log, *, _authority=None):
        require(
            _authority is _SCIENCE_AUTHORITY, "actual checked public scientific return required"
        )
        self.contract_sha256, self.role = contract_sha256, role
        self.proof, self.command_log = deepcopy(proof), command_log

    def __reduce_ex__(self, protocol):
        raise TypeError("public actual return cannot be serialized or used for formal C")


def _runtime_origins():
    """Independently locate declared entry files without importing initializers."""
    root = Path(sys.executable).absolute().parent.parent
    packages, extensions = {}, {}

    def item(name, spec):
        require(
            spec is not None and type(spec.origin) is str, "independent import origin unavailable"
        )
        origin = Path(spec.origin).absolute()
        require(
            origin == REPO / "src/topolab/__init__.py"
            if name == "topolab"
            else root in origin.parents,
            "independent locked import origin differs",
        )
        loaded = sys.modules.get(name)
        require(
            loaded is None or Path(loaded.__file__).absolute() == origin,
            "independent loaded import origin differs",
        )
        return {"origin": str(origin), "sha256": digest(origin.read_bytes())}

    for name in ("topolab", "numpy", "scipy", "torch", "safetensors"):
        packages[name] = item(name, importlib.util.find_spec(name))
    for name in (
        "numpy._core._multiarray_umath",
        "scipy.sparse.linalg._dsolve._superlu",
        "torch._C",
        "safetensors._safetensors_rust",
    ):
        pieces = name.split(".")
        parent = importlib.util.find_spec(pieces[0])
        for count in range(2, len(pieces) + 1):
            require(
                parent is not None and parent.submodule_search_locations,
                "independent native import parent unavailable",
            )
            parent = importlib.machinery.PathFinder.find_spec(
                ".".join(pieces[:count]), parent.submodule_search_locations
            )
        extensions[name] = item(name, parent)
    return packages, extensions


def check_contract(contract):
    """Frozen software/metadata only; no scientific input is opened here."""
    require(
        type(contract) is dict
        and contract.get("schema") == "topolab.v2.m2-scientific-contract.v1"
        and contract.get("execution_identity") == IDENTITY,
        "scientific contract metadata differs",
    )
    proposal_raw = acquisition.native._software_bytes(
        REPO / "docs/planning/p17_m2_native_homotopy_proposal.json"
    )
    require(
        contract.get("proposal_sha256") == digest(proposal_raw),
        "scientific proposal freeze differs",
    )
    require(
        canonical(contract.get("permissions")) == canonical({"B": True, "C": True})
        and type(contract.get("resource_limit_bytes")) is int
        and contract["resource_limit_bytes"] == 4294967296
        and contract.get("independent_operation_caps") == OPERATIONS,
        "scientific permissions/resource/operation caps differ",
    )
    source = contract.get("source_freeze")
    required = {
        "scripts/p17_m2_scientific_control.py",
        "scripts/p17_m2_scientific_independent.py",
        "scripts/p17_m2_scientific_orchestration.py",
        "scripts/p17_m2_independent_audit.py",
    }
    require(
        type(source) is dict and required <= set(source) and len(source) <= 2048,
        "complete scientific source freeze required",
    )
    for name, expected in source.items():
        require(
            type(name) is str
            and not Path(name).is_absolute()
            and all(part not in ("", ".", "..") for part in name.split("/"))
            and type(expected) is str
            and re.fullmatch(r"[0-9a-f]{64}", expected),
            "scientific source path/hash differs",
        )
        require(
            digest(acquisition.native._software_bytes(REPO / name)) == expected,
            "scientific source freeze changed",
        )
    entry = Path(sys.executable).absolute()
    startup_entry = Path(sys.orig_argv[0]).absolute()
    packages, extensions = _runtime_origins()
    runtime = {
        "python_entry": str(entry),
        "python_physical": str(entry.resolve()),
        "python_startup_entry": str(startup_entry),
        "python_startup_sha256": digest(startup_entry.read_bytes()),
        "python_sha256": digest(entry.read_bytes()),
        "python_version": sys.version,
        "pyvenv_cfg_sha256": digest((entry.parent.parent / "pyvenv.cfg").read_bytes()),
        "platform": sys.platform,
        "cwd": str(REPO),
        "lock_sha256": digest((REPO / "uv.lock").read_bytes()),
        "threads": {
            key: os.environ.get(key)
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
        "distributions": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "scipy", "torch", "safetensors")
        },
        "import_origins": packages,
        "native_origins": extensions,
        "torch_threads_policy": {"intraop": 1, "interop": 8},
    }
    require(
        all(value == "1" for value in runtime["threads"].values()),
        "actual independent numerical environment threads differ",
    )
    require(
        type(contract.get("runtime")) is dict
        and all(contract["runtime"].get(k) == v for k, v in runtime.items() if k != "orig_argv"),
        "scientific runtime freeze differs",
    )
    require(
        type(contract.get("public_fixture_only", False)) is bool,
        "scientific public scope must be boolean",
    )
    return digest(canonical(contract))


def checked_complete_charge(
    role, whole, native_wall, inner_wall, internal, attempted, *, _public_reader=False
):
    """The whole role includes input/setup work even when row totals are lower."""
    cap = {"resource-preflight": 180, "scientific-producer": 10800, "scientific-auditor": 3600}[
        role
    ]
    require(
        all(
            type(x) in (int, float) and math.isfinite(x) and x >= 0
            for x in (whole, native_wall, inner_wall, internal)
        )
        and type(attempted) is int
        and attempted == (0 if role == "resource-preflight" or _public_reader else 360)
        and (role != "resource-preflight" or internal >= inner_wall),
        "scientific complete wall/FULL charge exceeded",
    )
    charge = max(max(whole, native_wall) + attempted + 10, internal)
    helper("p17_m2_independent_audit").audit_role_charge(
        native_wall, whole, attempted, internal, charge
    )
    require(charge <= cap, "scientific complete wall/FULL charge exceeded")
    return charge


def check_native_dispatch(contract, role, label, evidence):
    """Close the timer and recorder at the trusted actual tool-return boundary.

    The parent's wait4 can include descendant peaks. Adding it to the command
    profile and this recorder's self highwater deliberately keeps that overlap.
    This is the published empirical observation method, not an allocation proof.
    """
    contract_sha = check_contract(contract)
    if label in ("reservation", "reader-ack"):
        spec = contract["shared_helpers"][role][label]
        timed_argv = resolve_argv(spec["argv"], contract_sha)
    else:
        spec = contract["roles"][role]["native_dispatch"][label]
        timed_argv = resolve_argv(contract["roles"][role]["exit_argv"][label], contract_sha)
    dispatch_argv = resolve_argv(spec["dispatch_argv"], contract_sha)
    platform = contract["runtime"]["platform"]
    require(platform in ("darwin", "linux"), "scientific dispatch platform/units differ")
    prefix = (
        ["/usr/bin/time", "-l", "-o", spec["profile_path"]]
        if platform == "darwin"
        else ["/usr/bin/time", "-f", "TOPOLAB_NATIVE %e %U %S %M", "-o", spec["profile_path"]]
    )
    require(
        timed_argv[:len(prefix)] == prefix
        and len(timed_argv) > len(prefix)
        and type(spec["timeout_seconds"]) in (int, float)
        and math.isfinite(spec["timeout_seconds"])
        and 0 < spec["timeout_seconds"] <= contract["roles"][role]["FULL_seconds"],
        "scientific native timed command/timeout differs",
    )
    event, raw = evidence["event"], evidence["dispatch"]
    require(
        type(raw) is bytes and 0 < len(raw) <= 1024**2
        and event.get("complete") is True
        and type(event.get("exit_code")) is int and event["exit_code"] == 0
        and type(event.get("dispatcher_exit")) is int and event["dispatcher_exit"] == 0
        and event.get("argv") == timed_argv
        and event.get("dispatch_argv") == dispatch_argv
        and event.get("dispatch_stdout") == raw.decode("ascii")
        and event.get("dispatch_stdout_sha256") == digest(raw)
        and event.get("stdout_sha256") == digest(evidence["log"])
        and event.get("profile_sha256") == digest(evidence["profile"])
        and all(type(event.get(k)) in (int, float) and math.isfinite(event[k])
                for k in ("start_seconds", "end_seconds"))
        and event["start_seconds"] <= event["end_seconds"],
        "scientific actual dispatcher return/hash/argv differs",
    )
    record = json.loads(raw)
    require(
        canonical(record) == raw
        and record.get("schema") == "topolab.v2.m2-native-dispatch.v1"
        and record.get("execution_identity") == IDENTITY
        and record.get("contract_sha256") == contract_sha
        and record.get("role") == role and record.get("label") == label
        and record.get("argv") == timed_argv
        and record.get("dispatch_argv") == dispatch_argv
        and record.get("status") == "COMPLETED_WITH_NATIVE_RETURN"
        and type(record.get("exit_code")) is int and record["exit_code"] == 0
        and record.get("group_gone") is True and record.get("cleanup_errors") == []
        and record.get("log_sha256") == digest(evidence["log"])
        and record.get("profile_sha256") == digest(evidence["profile"]),
        "scientific native dispatcher binding/cleanup differs",
    )
    require(
        record.get("python_entry") == contract["runtime"]["python_entry"]
        and record.get("startup_orig_argv") == startup_argv(dispatch_argv, contract["runtime"])
        and record.get("self_rss_phases")
        == ["pre_preview_write", "post_preview_write_pre_final_serialization"]
        and record.get("self_rss_scope")
        == "empirical before/after retained preflush packet; final serializer closed externally",
        "scientific native startup/self-observation phases differ",
    )
    preview = deepcopy(record)
    preview_sha = preview.pop("preflush_sha256")
    preview["self_rss_bytes_after_flush"] = None
    require(
        evidence["preflush"] == canonical(preview)
        and preview_sha == digest(evidence["preflush"]),
        "scientific native retained preflush identity differs",
    )
    cleanup, facts = record["cleanup"], record["native_log_facts"]
    require(
        all(type(record.get(k)) is int for k in
            ("stdout_observed_bytes", "stdout_retained_bytes", "stdout_observed_truncated_bytes"))
        and record["stdout_observed_bytes"] == record["stdout_retained_bytes"]
        == len(evidence["log"])
        and record["stdout_observed_truncated_bytes"] == 0
        and record.get("unobserved_stdout_after_cap") == "NOT_TRUNCATED",
        "scientific native stdout completeness/truncation differs",
    )
    require(
        type(cleanup) is dict
        and cleanup.get("group_gone") is True
        and cleanup.get("final_group_gone") is True
        and type(cleanup.get("leader_exit")) is int and cleanup["leader_exit"] == 0
        and cleanup.get("observation_limit_exceeded") is False
        and cleanup.get("signals") == []
        and type(cleanup.get("observations")) is list and cleanup["observations"]
        and cleanup["observations"][-1].get("group_gone") is True
        and cleanup["observations"][-1].get("leader_exit") == 0
        and record.get("descendant_groups") == [] and record.get("watchdog_helper") is None,
        "scientific native dispatch cleanup/extra helper coverage incomplete",
    )
    require(
        facts["declared"] == facts["before"] == facts["after"] == facts["closing"]
        and facts["returned_bytes"] == len(evidence["log"]) == facts["declared"]["st_size"]
        and facts["declared"]["st_nlink"] == 1
        and facts["declared"]["st_mode"] & 0o170000 == 0o100000,
        "scientific native log raw identity/complete read differs",
    )
    timer = record["timer_native_exit"]
    require(
        all(type(record.get(k)) is int and record[k] > 0 for k in ("pid", "native_pid"))
        and record["pid"] != record["native_pid"]
        and timer.get("pid") == record["native_pid"]
        and type(timer.get("exit_code")) is int and timer["exit_code"] == 0
        and timer.get("statistics_source") == "os.wait4"
        and timer.get("wall_source") == "controller_monotonic_observed"
        and timer.get("source")
        == "parent os.wait4 native exit rusage; possible descendant aggregation"
        and timer.get("rss_unit") == ("bytes" if platform == "darwin" else "KiB*1024"),
        "scientific native timer wait4 identity/units differ",
    )
    native = timer["native"]
    require(
        set(native) == {"wall_seconds", "user_seconds", "system_seconds", "rss_bytes"}
        and all(type(native[k]) in (int, float) and math.isfinite(native[k]) and native[k] >= 0
                for k in ("wall_seconds", "user_seconds", "system_seconds"))
        and type(native["rss_bytes"]) is int and native["rss_bytes"] > 0
        and all(type(record.get(k)) is int and record[k] > 0
                for k in ("started_unix_ns", "returned_unix_ns",
                          "self_rss_bytes_before_flush", "self_rss_bytes_after_flush"))
        and record["started_unix_ns"] <= record["returned_unix_ns"]
        and record["self_rss_bytes_before_flush"] <= record["self_rss_bytes_after_flush"]
        and type(record.get("elapsed_seconds")) in (int, float)
        and math.isfinite(record["elapsed_seconds"]) and record["elapsed_seconds"] >= 0,
        "scientific native dispatcher statistics incomplete",
    )
    measured = helper("p17_m2_independent_audit")._native_bytes(evidence["profile"], platform)
    span = event["end_seconds"] - event["start_seconds"]
    require(
        event["start_seconds"] - 1 <= record["started_unix_ns"] / 1e9
        <= record["returned_unix_ns"] / 1e9 <= event["end_seconds"] + 1
        and measured["wall_seconds"] <= record["elapsed_seconds"] + 1
        and native["wall_seconds"] <= record["elapsed_seconds"] + 1
        and record["elapsed_seconds"] <= span + 1
        and record["elapsed_seconds"] <= spec["timeout_seconds"] + 10,
        "scientific native dispatcher wall/actual-return bound differs",
    )
    self_peak = max(record["self_rss_bytes_before_flush"], record["self_rss_bytes_after_flush"])
    peak = measured["rss_bytes"] + native["rss_bytes"] + self_peak
    require(peak <= 4294967296, "FAIL_RESOURCE_CAP: native command/timer/dispatcher envelope")
    return {
        "native_rss_bytes": peak,
        "command_native_rss_bytes": measured["rss_bytes"],
        "timer_wait4_rss_bytes": native["rss_bytes"],
        "dispatcher_self_rss_bytes": self_peak,
        "dispatch_sha256": digest(raw),
        "actual_dispatcher_exit_observed": True,
        "monotonic_wall_seconds": record["elapsed_seconds"],
        "unobserved_post_flush_instructions": "EMPIRICAL_SELF_HIGHWATER_BOUNDARY_DISCLOSED",
    }


def check_shared_helper_return(contract, role, action, evidence):
    """Check a shared helper's own observed return, never a future-exit claim."""
    contract_sha = check_contract(contract)
    require(
        role in ("resource-preflight", "scientific-producer", "scientific-auditor")
        and action in ("reservation", "reader-ack")
        and (role != "resource-preflight" or action == "reservation")
        and contract.get("shared_FULL_seconds") == 180,
        "scientific shared helper role/action/FULL differs",
    )
    dispatched = check_native_dispatch(contract, role, action, evidence)
    event, raw = evidence["event"], evidence["log"]
    require(
        event.get("argv")
        == resolve_argv(contract["shared_helpers"][role][action]["argv"], contract_sha)
        and event.get("complete") is True
        and type(event.get("exit_code")) is int
        and event["exit_code"] == 0
        and event.get("stdout_sha256") == digest(raw)
        and event.get("profile_sha256") == digest(evidence["profile"])
        and all(
            type(event.get(k)) in (int, float) and math.isfinite(event[k])
            for k in ("start_seconds", "end_seconds")
        )
        and event["start_seconds"] <= event["end_seconds"],
        "actual scientific shared helper return differs",
    )
    span = event["end_seconds"] - event["start_seconds"]
    measured = helper("p17_m2_independent_audit")._native_bytes(
        evidence["profile"], contract["runtime"]["platform"]
    )
    require(
        measured["rss_bytes"] <= 4294967296 and measured["wall_seconds"] <= span + 1,
        "scientific shared helper native resource/return differs",
    )
    value = json.loads(raw)
    require(
        canonical(value) == raw
        and value.get("execution_identity") == IDENTITY
        and value.get("scientific_contract_sha256") == contract_sha
        and value.get("role") == role,
        "scientific shared helper returned identity differs",
    )
    if action == "reservation":
        require(
            raw == canonical(evidence["pending"])
            and value.get("status") == "CONSUMED_BEFORE_CONTROLLER_INTERPRETER"
            and value.get("FULL_seconds") == contract["roles"][role]["FULL_seconds"]
            and type(value.get("began_UTC_seconds")) in (int, float)
            and math.isfinite(value["began_UTC_seconds"])
            and event["start_seconds"] <= value["began_UTC_seconds"] <= event["end_seconds"],
            "scientific shared reservation pending/FULL differs",
        )
    else:
        require(
            value.get("status") == "SCIENTIFIC_READER_RETURN_ACKNOWLEDGED"
            and value.get("lease_state") == "RELEASED"
            and value.get("consumer_actual_exit_observed") is True,
            "scientific shared reader acknowledgement incomplete",
        )
    require(span + 1 <= 180, "scientific active shared helper charge exceeded")
    return {
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": contract_sha,
        "role": role,
        "action": action,
        "actual_exit_observed": True,
        "active_charge_seconds": span + 1,
        "native_rss_bytes": dispatched["native_rss_bytes"],
        "native_dispatch": dispatched,
        "event_sha256": digest(canonical(event)),
        "profile_sha256": digest(evidence["profile"]),
        "log_sha256": digest(raw),
    }


def check_shared_closeout(contract, evidence, *, role_evidence=None):
    """Charge exactly five active helpers; do not charge the disjoint C gaps."""
    expected = [
        ("resource-preflight", "reservation"),
        ("scientific-producer", "reservation"),
        ("scientific-producer", "reader-ack"),
        ("scientific-auditor", "reservation"),
        ("scientific-auditor", "reader-ack"),
    ]
    require(
        type(evidence) is list and len(evidence) == 5,
        "complete scientific shared helper table required",
    )
    proofs, previous_end = [], None
    for item, (role, action) in zip(evidence, expected, strict=True):
        require(
            (item.get("role"), item.get("action")) == (role, action)
            and (previous_end is None or previous_end <= item["event"]["start_seconds"]),
            "scientific shared helper order/overlap differs",
        )
        proofs.append(check_shared_helper_return(contract, role, action, item))
        previous_end = item["event"]["end_seconds"]
    require(
        type(role_evidence) is dict
        and set(role_evidence)
        == {"resource-preflight", "scientific-producer", "scientific-auditor"},
        "complete actual scientific role lifetimes required",
    )
    check_b_preflight(contract, role_evidence["resource-preflight"])
    for role in ("scientific-producer", "scientific-auditor"):
        if contract.get("public_fixture_only", False):
            check_public_scientific_reader_return(contract, role, role_evidence[role])
        else:
            check_scientific_role(contract, role, role_evidence[role])
    timelines = {
        role: (
            records["raw_tool_events"][0]["start_seconds"],
            records["raw_tool_events"][-1]["end_seconds"],
        )
        for role, records in role_evidence.items()
    }
    require(
        evidence[0]["event"]["end_seconds"] <= timelines["resource-preflight"][0]
        and timelines["resource-preflight"][1] <= evidence[1]["event"]["start_seconds"]
        and evidence[1]["event"]["end_seconds"] <= timelines["scientific-producer"][0]
        and timelines["scientific-producer"][1] <= evidence[2]["event"]["start_seconds"]
        and evidence[3]["event"]["end_seconds"] <= timelines["scientific-auditor"][0]
        and timelines["scientific-auditor"][1] <= evidence[4]["event"]["start_seconds"],
        "scientific shared helpers overlap actual role lifetimes",
    )
    active = sum(item["active_charge_seconds"] for item in proofs) + 10
    require(active <= 180, "scientific complete shared FULL180 exhausted")
    return {
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": check_contract(contract),
        "status": "SCIENTIFIC_SHARED_HELPERS_ACTUAL_RETURNS_VERIFIED",
        "FULL_charged_seconds": 180,
        "active_helper_charge_seconds": active,
        "native_peak_bytes": max(item["native_rss_bytes"] for item in proofs),
        "helpers": proofs,
        "long_scientific_gaps_charged_to_C_roles": True,
        "actual_final_ack_exit_observed": True,
        "role_lifetimes_independently_verified": True,
    }


def _check_role_envelope(contract, role, evidence, *, _public_reader=False):
    contract_sha = check_contract(contract)
    require(
        not _public_reader
        or (
            contract.get("public_fixture_only") is True
            and role in ("scientific-producer", "scientific-auditor")
        ),
        "public scientific decoder contract required",
    )
    caps = {"resource-preflight": 180, "scientific-producer": 10800, "scientific-auditor": 3600}
    require(
        role in caps
        and evidence.get("role") == role
        and evidence.get("execution_identity") == IDENTITY
        and evidence.get("scientific_contract_sha256") == contract_sha,
        "scientific role/contract binding differs",
    )
    require(
        evidence["platform"] == contract["runtime"]["platform"],
        "scientific native platform differs",
    )
    registered = contract["roles"][role]
    require(registered.get("FULL_seconds") == caps[role], "scientific FULL cap differs")
    reservation = check_shared_helper_return(
        contract, role, "reservation", evidence["reservation_helper"]
    )
    starts, cases = registered["inner_starts"], evidence["cases"]
    require(
        type(cases) is list
        and len(cases) == (3 if role == "resource-preflight" else 1)
        and len(starts) == len(cases),
        "registered scientific native starts differ",
    )
    old = helper("p17_m2_independent_audit")
    peaks, inner_wall = [], 0.0
    for case, expected in zip(cases, starts, strict=True):
        record = case["record"]
        inner_argv = resolve_argv(expected["argv"], contract_sha)
        require(
            case["name"] == expected["name"]
            and record["argv"] == inner_argv
            and record["timeout_seconds"] == expected["timeout_seconds"]
            and record["exit_code"] == expected["expected_exit_code"]
            and record["software_result"] == expected["expected_status"]
            and record["limit_bytes"] == 4294967296,
            "registered scientific native case outcome differs",
        )
        require(
            type(expected["expected_exit_code"]) is int
            and record["cwd"] == contract["runtime"]["cwd"]
            and record["controller_python"] == contract["runtime"]["python_entry"]
            and record["lock_sha256"] == contract["runtime"]["lock_sha256"]
            and record["thread_environment"] == contract["runtime"]["threads"],
            "scientific native actual runtime differs",
        )
        checked = old.audit_resource_record(
            record,
            profile=case["profile"],
            log=case["log"],
            helper_profiles=case["helper_profiles"],
            expected_role=expected["name"],
            expected_argv=inner_argv,
            platform=evidence["platform"],
            require_success=expected["expected_exit_code"] == 0,
        )
        require(
            record["cleanup"]["group_gone"] is True
            and record["cleanup"]["leader_exit"] == record["exit_code"]
            and checked["empirical_recorded_peak_bytes"] <= 4294967296,
            "scientific native cleanup/resource incomplete",
        )
        peaks.append(checked["empirical_recorded_peak_bytes"])
        inner_wall += checked["observed_outer_wall_seconds"]
    links, events = evidence["exit_bindings"], evidence["raw_tool_events"]
    labels = ("controller", "binder", "verifier")
    require(len(links) == 3 and len(events) == 4, "complete scientific final-exit chain required")
    require(
        evidence["reservation_helper"]["event"]["end_seconds"] <= events[0]["start_seconds"],
        "scientific actual reservation return must precede controller",
    )
    prior_binding, previous_end = None, None
    outer_peaks, outer_walls = [], []
    for item, event, label in zip(links, events[:3], labels, strict=True):
        dispatched = check_native_dispatch(
            contract, role, label,
            {"event": event, "dispatch": item["dispatch"], "preflush": item["preflush"],
             "profile": item["profile"], "log": item["log"]},
        )
        binding, prior = item["binding"], item["prior"]
        previous = json.loads(prior)
        before = (
            "PENDING_POSTEXIT"
            if label == "controller"
            else ("PENDING_BINDER_EXIT" if label == "binder" else "PENDING_VERIFIER_EXIT")
        )
        after = "PENDING_BINDER_EXIT" if label == "controller" else "PENDING_VERIFIER_EXIT"
        if prior_binding is None:
            require(
                previous.get("case_records_sha256")
                == digest(canonical([case["record"] for case in cases])),
                "scientific inner record chain differs",
            )
            require(
                previous.get("case_spans_sha256") == digest(canonical(evidence["case_spans"])),
                "scientific inner span chain differs",
            )
        else:
            require(prior == canonical(prior_binding), "scientific exit chain hash/order differs")
        require(
            previous.get("schema") == "topolab.v2.m2-scientific-native-exit-binding.v1"
            and previous.get("status") == before
            and previous.get("execution_identity") == IDENTITY
            and previous.get("scientific_contract_sha256") == contract_sha
            and previous.get("role") == role,
            "scientific prior exit identity differs",
        )
        require(
            binding.get("schema") == previous["schema"]
            and binding.get("execution_identity") == IDENTITY
            and binding.get("scientific_contract_sha256") == contract_sha
            and binding.get("role") == role
            and binding.get("bound_role") == label
            and binding.get("prior_status") == before
            and binding.get("status") == after
            and binding.get("record_sha256") == digest(prior)
            and binding.get("profile_sha256") == digest(item["profile"])
            and binding.get("log_sha256") == digest(item["log"]),
            "scientific exit binding fields differ",
        )
        measured = old._native_bytes(item["profile"], evidence["platform"])
        require(
            binding.get("native") == measured
            and binding.get("exit_code") == 0
            and item["observed_exit_code"] == 0
            and binding.get("resource_cap_exceeded") is False
            and measured["rss_bytes"] <= 4294967296,
            "scientific observed native exit/resource differs",
        )
        require(
            event.get("argv") == resolve_argv(registered["exit_argv"][label], contract_sha)
            and event.get("complete") is True
            and type(event.get("exit_code")) is int
            and event["exit_code"] == 0
            and event.get("stdout_sha256") == digest(item["log"])
            and all(
                type(event.get(k)) in (int, float) and math.isfinite(event[k])
                for k in ("start_seconds", "end_seconds")
            )
            and event["start_seconds"] <= event["end_seconds"]
            and (previous_end is None or previous_end <= event["start_seconds"]),
            "actual scientific tool return/order differs",
        )
        require(
            measured["wall_seconds"] <= event["end_seconds"] - event["start_seconds"] + 1,
            "native role exceeds observed actual return span",
        )
        previous_end, prior_binding = event["end_seconds"], binding
        outer_peaks.append(dispatched["native_rss_bytes"])
        outer_walls.append(max(measured["wall_seconds"], dispatched["monotonic_wall_seconds"]))
    last_event = events[-1]
    last_dispatch = check_native_dispatch(
        contract, role, "final-observer",
        {"event": last_event, "dispatch": evidence["last_observer_dispatch"],
         "preflush": evidence["last_observer_preflush"],
         "profile": evidence["last_observer_profile"], "log": evidence["last_observer_log"]},
    )
    last_native = old._native_bytes(evidence["last_observer_profile"], evidence["platform"])
    require(
        last_event.get("argv")
        == resolve_argv(registered["exit_argv"]["final-observer"], contract_sha)
        and last_event.get("complete") is True
        and type(last_event.get("exit_code")) is int
        and last_event["exit_code"] == 0
        and evidence["last_observer_exit_code"] == 0
        and last_event.get("stdout_sha256") == digest(evidence["last_observer_log"])
        and all(
            type(last_event.get(k)) in (int, float) and math.isfinite(last_event[k])
            for k in ("start_seconds", "end_seconds")
        )
        and previous_end <= last_event["start_seconds"] <= last_event["end_seconds"]
        and last_native["wall_seconds"]
        <= (last_event["end_seconds"] - last_event["start_seconds"]) + 1
        and last_native["rss_bytes"] <= 4294967296,
        "actual final observer native exit incomplete",
    )
    outer_peaks.append(last_dispatch["native_rss_bytes"])
    outer_walls.append(max(last_native["wall_seconds"], last_dispatch["monotonic_wall_seconds"]))
    span = events[-1]["end_seconds"] - events[0]["start_seconds"]
    whole, internal = evidence["whole_wall_seconds"], evidence["inner_charge_seconds"]
    attempted = evidence.get("attempted_rows")
    require(
        type(attempted) is int
        and attempted == (0 if role == "resource-preflight" or _public_reader else 360),
        "complete scientific attempted-row charge required",
    )
    require(whole >= span - 0.001, "scientific complete observed wall differs")
    if role != "resource-preflight":
        payload = json.loads(cases[0]["log"])
        require(
            payload["result"]["internal_row_charge_seconds"] == internal
            and payload["result"]["attempted_rows"] == attempted,
            "scientific inner charge/rows differ from actual returned log",
        )
    known_charge = checked_complete_charge(
        role,
        whole,
        sum(outer_walls),
        inner_wall,
        internal,
        attempted,
        _public_reader=_public_reader,
    )
    spans = evidence["case_spans"]
    require(
        type(spans) is list and len(spans) == len(cases),
        "complete scientific inner lifetime spans required",
    )
    last_end = events[0]["start_seconds"]
    for interval, case in zip(spans, cases, strict=True):
        require(
            interval.get("name") == case["name"]
            and interval.get("group_gone") is True
            and case["record"]["cleanup"]["group_gone"] is True
            and all(
                type(interval.get(k)) in (int, float) and math.isfinite(interval[k])
                for k in ("start_seconds", "end_seconds")
            )
            and last_end
            <= interval["start_seconds"]
            <= interval["end_seconds"]
            <= events[0]["end_seconds"]
            and interval["end_seconds"] - interval["start_seconds"] + 0.001
            >= case["record"]["observed_outer_wall_seconds"],
            "scientific actual disjoint inner lifetimes differ",
        )
        last_end = interval["end_seconds"]
    peak = max(max(peaks) + outer_peaks[0], max(outer_peaks[1:]), reservation["native_rss_bytes"])
    require(peak <= 4294967296, "FAIL_RESOURCE_CAP: scientific recorded-chain envelope")
    return {
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": contract_sha,
        "role": role,
        "FULL_charged_seconds": caps[role],
        "whole_wall_seconds": whole,
        "inner_charge_seconds": internal,
        "known_complete_charge_seconds": known_charge,
        "conservative_recorded_peak_bytes": peak,
        "actual_final_verifier_exit_observed": True,
        "a_priori_allocation_proved": False,
        "whole_host_unmeasured": "UNKNOWN_NOT_ZERO",
        "reservation_helper": reservation,
        "reservation_helper_charged_in_shared_FULL180": True,
    }


def check_b_preflight(contract, evidence):
    proof = _check_role_envelope(contract, "resource-preflight", evidence)
    proof["status"] = "PASS_PREFLIGHT_RSS_EXIT_EMPIRICAL"
    return CheckedBAdmission(
        proof["scientific_contract_sha256"], proof, _authority=_SCIENCE_AUTHORITY
    )


def check_scientific_role(contract, role, evidence):
    require(role in ("scientific-producer", "scientific-auditor"), "scientific role differs")
    require(
        contract.get("public_fixture_only", False) is False, "formal scientific contract required"
    )
    proof = _check_role_envelope(contract, role, evidence)
    payload = json.loads(evidence["cases"][0]["log"])
    check_returned_startup(contract, role, payload, proof["scientific_contract_sha256"])
    require(
        payload.get("actual_numerical_runtime", {}).get("torch_threads")
        == contract["runtime"]["torch_threads_policy"],
        "actual scientific returned numerical runtime differs",
    )
    proof["status"] = "PASS_RSS_EXIT_EMPIRICAL"
    record = evidence["cases"][0]["record"]
    proof["observed_command_pids"] = sorted(
        {row["pid"] for sample in record["samples"] for row in sample["roles"]}
    )
    return CheckedScientificReturn(
        proof["scientific_contract_sha256"],
        role,
        proof,
        evidence["cases"][0]["log"],
        _authority=_SCIENCE_AUTHORITY,
    )


def check_public_scientific_reader_return(contract, role, evidence):
    """Observe a real public decoder/lease return without claiming a C panel."""
    require(
        contract.get("public_fixture_only") is True, "public scientific decoder contract required"
    )
    proof = _check_role_envelope(contract, role, evidence, _public_reader=True)
    payload = json.loads(evidence["cases"][0]["log"])
    check_returned_startup(contract, role, payload, proof["scientific_contract_sha256"])
    result = payload["result"]
    require(
        payload.get("schema") == "topolab.v2.m2-public-scientific-reader.v1"
        and result.get("status") == "PUBLIC_SCIENTIFIC_BUFFERS_DECODED"
        and result.get("member_reads") == (542 if role == "scientific-producer" else 1070)
        and result.get("attempted_rows") == 0
        and result.get("loaded_models") == 12
        and result.get("NN_producer_views") == 528
        and result.get("auditor_reanalysis") == (1056 if role == "scientific-auditor" else 0)
        and payload.get("actual_numerical_runtime", {}).get("torch_threads")
        == contract["runtime"]["torch_threads_policy"],
        "public scientific decoder complete result differs",
    )
    proof["simulated_FULL_bound_seconds"] = proof.pop("FULL_charged_seconds")
    proof.update(
        status="PUBLIC_SCIENTIFIC_READER_RETURN_OBSERVED",
        public_software_only=True,
        formal_SCI_FULL_charged_seconds=0,
    )
    proof["observed_command_pids"] = sorted(
        {
            row["pid"]
            for sample in evidence["cases"][0]["record"]["samples"]
            for row in sample["roles"]
        }
    )
    return CheckedPublicScientificReturn(
        proof["scientific_contract_sha256"],
        role,
        proof,
        evidence["cases"][0]["log"],
        _authority=_SCIENCE_AUTHORITY,
    )


class CheckedScientificInput(acquisition.CheckedAcquisitionInput):
    """Separate scientific grant over an already independently accepted version."""

    __slots__ = ("_scientific_contract", "_upstream_source_sha256")

    def __init__(self, binding, contract, *, _authority=None):
        require(_authority is _SCIENCE_AUTHORITY, "actual scientific input grant required")
        self._scientific_contract = deepcopy(contract)
        self._upstream_source_sha256 = acquisition.MODULE_SOURCE_SHA256
        super().__init__(binding, _authority=acquisition._ACQUISITION_AUTHORITY)

    def _reader_identity(self):
        return IDENTITY

    def _reader_scope(self):
        return (
            "NEW_PUBLIC_SCIENTIFIC_INTEGRATION_ONLY"
            if self._scientific_contract.get("public_fixture_only", False)
            else "SCIENTIFIC_SOURCE_ATTESTED_FIXED_P17"
        )

    def _reader_schema(self):
        return "topolab.v2.m2-scientific-reader-lease.v1"

    def _reader_source_digest(self):
        require(
            digest(Path(acquisition.__file__).read_bytes()) == self._upstream_source_sha256,
            "upstream acquisition verifier source changed",
        )
        return digest(Path(__file__).read_bytes())

    def _reader_argv(self, action, role):
        require(
            not self._reader_failed and role in self._binding["role_views"],
            "STOP_NO_RETRY: scientific reader unavailable",
        )
        key = (
            "consume" if action == "public-consumer" else "ack" if action == "reader-ack" else None
        )
        require(key is not None, "scientific reader action differs")
        return startup_argv(
            resolve_argv(
                self._scientific_contract["reader_actions"][role][key],
                digest(canonical(self._scientific_contract)),
            ),
            self._scientific_contract["runtime"],
        )


def grant_scientific_input(certificate, contract, role, admission):
    require(isinstance(admission, CheckedBAdmission), "actual checked B admission required")
    contract_sha = check_contract(contract)
    require(
        admission.contract_sha256 == contract_sha,
        "scientific B admission belongs to another contract",
    )
    require(
        isinstance(certificate, acquisition.CheckedAcquisitionInput)
        and not isinstance(certificate, CheckedScientificInput),
        "actual independently accepted acquisition certificate required",
    )
    require(role in ("scientific-producer", "scientific-auditor"), "scientific reader role differs")
    binding = deepcopy(certificate._binding)
    public = contract.get("public_fixture_only", False)
    required_scope = acquisition.REHEARSAL_SCOPE if public else acquisition.FORMAL_SCOPE
    require(
        binding["scope"] == required_scope
        and binding["verified_plan"]["formal_authority"] is (not public),
        "scientific input formal/public scope differs",
    )
    actual = {
        "plan_sha256": binding["plan_sha256"],
        "version_id": binding["version_id"],
        "manifest_sha256": digest(canonical(binding["manifest"])),
        "content_root": binding["root"],
        "shared_packet_sha256": binding["shared_packet_sha256"],
    }
    require(
        contract.get("acquisition") == actual
        and contract.get("input_version_id", actual["version_id"]) == actual["version_id"],
        "scientific accepted input identity differs",
    )
    view = list(
        dict.fromkeys(
            [*binding["role_views"][role], *binding["role_views"]["reference-compatibility"]]
        )
    )
    require(
        contract["input_role_views"][role] == view
        and len(view) == (542 if role == "scientific-producer" else 1070),
        "scientific exact input union differs",
    )
    actions = contract["reader_actions"][role]
    require(
        set(actions) == {"consume", "ack"}
        and all(
            type(words) is list and words and all(type(w) is str and w for w in words)
            for words in actions.values()
        ),
        "scientific actual reader argv required",
    )
    binding["role_views"] = {role: view}
    binding.update(
        scientific_execution_identity=IDENTITY,
        scientific_contract_sha256=contract_sha,
        scientific_permissions={
            "producer" if role == "scientific-producer" else "auditor": True,
            "reference_compatibility": True,
        },
        scientific_public_fixture_only=public,
        independent_source_sha256=digest(Path(__file__).read_bytes()),
        plan_sha256=contract_sha,
    )
    return CheckedScientificInput(binding, contract, _authority=_SCIENCE_AUTHORITY)


def acknowledge_scientific_reader(certificate, receipt, checked_return):
    """Release only this scientific reader after separately observed full return.

    The acknowledgement's own eventual exit remains pending for its caller.
    No acquisition-only public metadata cap or status is repurposed for C.
    """
    require(
        isinstance(checked_return, (CheckedScientificReturn, CheckedPublicScientificReturn)),
        "actual checked scientific return required",
    )
    require(
        isinstance(certificate, CheckedScientificInput), "actual scientific input grant required"
    )
    contract_sha = digest(canonical(certificate._scientific_contract))
    public = certificate._scientific_contract.get("public_fixture_only", False)
    require(
        (
            isinstance(checked_return, CheckedPublicScientificReturn)
            and public is True
            and certificate._binding["scope"] == acquisition.REHEARSAL_SCOPE
        )
        or (isinstance(checked_return, CheckedScientificReturn) and public is False),
        "public/formal scientific actual return scope differs",
    )
    role = checked_return.role
    binding = certificate._binding
    require(
        checked_return.contract_sha256 == contract_sha
        and getattr(sys, "orig_argv", None) == certificate._reader_argv("reader-ack", role),
        "scientific reader acknowledgement role/argv differs",
    )
    require(
        type(receipt) is dict
        and receipt.get("status") == "PENDING_ACTUAL_OUTER_RETURN"
        and receipt.get("scope") == certificate._reader_scope()
        and receipt.get("execution_identity") == IDENTITY
        and receipt.get("root") == binding["root"]
        and receipt.get("version_id") == binding["version_id"]
        and receipt.get("root_identity") == binding["root_identity"]
        and receipt.get("role") == role
        and receipt.get("certificate_binding_sha256") == certificate._certificate_id
        and receipt.get("consumer_orig_argv") == certificate._reader_argv("public-consumer", role)
        and receipt.get("independent_source_sha256") == binding["independent_source_sha256"]
        and type(receipt.get("consumer_pid")) is int
        and receipt["consumer_pid"] in checked_return.proof["observed_command_pids"],
        "scientific pending reader identity/observed process differs",
    )
    returned = json.loads(checked_return.command_log)
    require(
        type(returned) is dict and returned.get("reader_pending") == receipt,
        "scientific pending lease not bound to actual command log",
    )
    root = certificate._reader_root(Path(binding["root"]))
    require(
        certificate._reader_root_identity(root) == binding["root_identity"],
        "scientific reader local root identity changed",
    )
    path = root.with_name(root.name + ".cooperative-reader.lease")
    require(receipt["lease_path"] == str(path), "scientific reader lease path differs")
    native = acquisition.native
    directory = native.base.nofollow_parent(path)
    fd = -1
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        raw, physical = native._lease_read(directory, path.name, fd)
        require(
            physical == receipt["lease_identity"] and digest(raw) == receipt["lease_record_sha256"],
            "scientific returned lease physical/content differs",
        )
        record = native.base.parse(raw, canonical_required=True)
        require(
            dict(
                record,
                status="PENDING_ACTUAL_OUTER_RETURN",
                lease_identity=physical,
                lease_record_sha256=digest(raw),
            )
            == receipt,
            "scientific returned lease metadata differs",
        )
        os.unlink(path.name, dir_fd=directory)
        os.fsync(directory)
    except BaseException:
        certificate._reader_failed = True
        raise
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(directory)
    return {
        "status": "SCIENTIFIC_READER_RETURN_ACKNOWLEDGED",
        "execution_identity": IDENTITY,
        "scientific_contract_sha256": contract_sha,
        "role": role,
        "lease_state": "RELEASED",
        "consumer_actual_exit_observed": True,
        "reader_receipt_sha256": digest(canonical(receipt)),
        "ack_own_future_exit": "UNKNOWN_PENDING_ACTUAL_OUTER_RETURN",
    }
