"""Separately authored public H witness checks; never a resource-admission oracle.

Only unchanged foundational FEM/filter/OC primitives are shared with the producer.
No candidate H driver, query classifier, Gate or resource conclusion is imported.
Full prior conversation exposure is disclosed in the independent stage-A report.
"""

import hashlib
import json
import re
from typing import Any

import numpy as np

from topolab.experiment import ExperimentCase
from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.mesh import generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport, PointLoad
from topolab.simp import (
    apply_density_filter,
    backpropagate_density_gradient,
    build_density_filter,
    evaluate_compliance,
    optimality_criteria_update,
)

SCHEMA = "topolab.v2.m2-homotopy-witness.v1"
POINT_FIELDS = {
    "iteration",
    "phase_iteration",
    "penalty",
    "compliance",
    "volume_fraction",
    "density_change",
    "physical_change",
}
STATE_FIELDS = POINT_FIELDS | {"design_density", "physical_density"}
OLD_STATE_FIELDS = {
    "iteration",
    "compliance",
    "volume_fraction",
    "density_change",
    "design_density",
    "physical_density",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _number(value: Any, name: str, *, positive: bool = False) -> float:
    _require(type(value) in (int, float), name + " must be a finite number")
    result = float(value)
    _require(bool(np.isfinite(result)), name + " must be finite")
    _require(result > 0 if positive else result >= 0, name + " is out of range")
    return result


def _integer(value: Any, name: str) -> int:
    _require(type(value) is int and value >= 0, name + " must be a nonnegative integer")
    return int(value)


def _sequence(value: Any, name: str) -> list[Any]:
    _require(type(value) is list, name + " must be a JSON array")
    return value


def _vector(value: Any, count: int, name: str) -> Any:
    rows = _sequence(value, name)
    _require(len(rows) == count, name + " length differs")
    _require(all(type(v) in (int, float) for v in rows), name + " must be numeric")
    result = np.asarray(rows, dtype=np.float64)
    _require(bool(np.all(np.isfinite(result))), name + " must be finite")
    return result


def _close(left: Any, right: Any, message: str) -> None:
    _require(bool(np.allclose(left, right, rtol=1e-9, atol=0)), message)


def _schedule(iteration: int, active: bool) -> tuple[int, int]:
    if not active:
        return 3, iteration
    if iteration <= 8:
        return 1, iteration
    if iteration <= 16:
        return 2, iteration - 8
    return 3, iteration - 16


def _point(value: Any, iteration: int, active: bool) -> dict[str, Any]:
    _require(type(value) is dict and set(value) == POINT_FIELDS, "scalar point fields differ")
    penalty, phase = _schedule(iteration, active)
    for key, expected in (
        ("iteration", iteration),
        ("penalty", penalty),
        ("phase_iteration", phase),
    ):
        _require(_integer(value[key], key) == expected, "scalar phase/iteration differs")
    _number(value["compliance"], "compliance", positive=True)
    _require(_number(value["volume_fraction"], "volume_fraction") <= 1, "invalid volume")
    _number(value["density_change"], "density_change")
    _number(value["physical_change"], "physical_change")
    return value


def _stop(points: list[dict[str, Any]], tolerance: float) -> bool:
    """Original design stop, or eleven *post-update* p3 states, independently."""
    if not points:
        return False
    if points[-1]["density_change"] <= tolerance:
        return True
    if len(points) < 11:
        return False
    window = points[-11:]
    gain = (window[0]["compliance"] - window[-1]["compliance"]) / window[0]["compliance"]
    return max(row["physical_change"] for row in window[1:]) <= tolerance and 0 <= gain <= 0.0002


def audit_witness(
    case: ExperimentCase,
    witness: dict[str, Any],
    reference: float | None = None,
    accepted: bool = False,
) -> dict[str, Any]:
    """Reject corrupt witness evidence and false acceptance, without the H driver.

    Reconstruct all 16 prefix updates and both transitions, then each bounded
    recent p3 state and the final state. Earlier p3 scalar points are structurally
    checked, not represented as a replay of the entire p3 trajectory. With no
    reference, the compliance-ratio criterion remains unchecked explicitly.
    """
    _require(type(accepted) is bool, "accepted must be boolean")
    _require(
        type(witness) is dict
        and set(witness)
        == {
            "schema",
            "active",
            "initial",
            "prefix",
            "transitions",
            "trace",
            "recent",
            "result",
            "fem_solves",
        },
        "witness fields differ",
    )
    _require(witness["schema"] == SCHEMA, "witness schema differs")
    _require(type(witness["active"]) is bool, "active must be boolean")
    active = witness["active"]
    if reference is not None:
        reference = _number(reference, "reference", positive=True)
    problem, settings = case.problem, case.problem.optimization
    _require(settings.penalty == 3 and settings.convergence_tolerance == 0.01, "p3 rules differ")
    trace = _sequence(witness["trace"], "trace")
    updates = len(trace)
    _require(
        (17 if active else 1) <= updates <= min(360, settings.max_iterations), "update cap differs"
    )
    points = [_point(row, i, active) for i, row in enumerate(trace, 1)]
    p3 = [row for row in points if row["penalty"] == 3]
    prefix = _sequence(witness["prefix"], "prefix")
    transitions = _sequence(witness["transitions"], "transitions")
    recent = _sequence(witness["recent"], "recent")
    _require(len(prefix) == (16 if active else 0), "prefix length differs")
    _require(len(transitions) == (2 if active else 0), "transition count differs")
    _require(len(recent) == min(11, len(p3)), "p3 recent window differs")
    _require(
        _integer(witness["fem_solves"], "fem_solves") == updates + (4 if active else 2),
        "driver FEM count differs",
    )
    for value in [witness["initial"], *prefix, *transitions, *recent]:
        _require(type(value) is dict and set(value) == STATE_FIELDS, "density state fields differ")
        for key in ("iteration", "phase_iteration", "penalty"):
            _integer(value[key], key)
        _number(value["compliance"], "state compliance", positive=True)
        _require(_number(value["volume_fraction"], "state volume") <= 1, "invalid state volume")
        _number(value["density_change"], "state design change")
        _number(value["physical_change"], "state physical change")

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
    count = mesh.connectivity.shape[0]
    fem_count = 0

    def analyze(physical: Any, penalty: int) -> Any:
        nonlocal fem_count
        fem_count += 1
        return evaluate_compliance(
            mesh,
            physical,
            loads,
            constrained,
            solid_modulus=problem.material.solid_modulus,
            minimum_modulus=problem.material.minimum_modulus,
            poisson_ratio=problem.material.poisson_ratio,
            penalty=penalty,
        )

    def state(value: Any, expected: dict[str, Any]) -> tuple[Any, Any]:
        _require(type(value) is dict and set(value) == STATE_FIELDS, "density state fields differ")
        _require({k: value[k] for k in POINT_FIELDS} == expected, "density/scalar identity differs")
        design = _vector(value["design_density"], count, "design_density")
        physical = _vector(value["physical_density"], count, "physical_density")
        _require(
            bool(np.all((design >= settings.minimum_density) & (design <= 1))),
            "density bounds differ",
        )
        _require(
            bool(np.array_equal(apply_density_filter(density_filter, design), physical)),
            "physical filter differs",
        )
        _require(
            abs(float(np.mean(physical)) - value["volume_fraction"]) <= 1e-12,
            "state volume differs",
        )
        return design, physical

    def boundary(value: Any, iteration: int, penalty: int) -> tuple[Any, Any, Any]:
        expected = dict(
            iteration=iteration,
            phase_iteration=0,
            penalty=penalty,
            compliance=_number(value["compliance"], "boundary compliance", positive=True),
            volume_fraction=_number(value["volume_fraction"], "boundary volume"),
            density_change=0,
            physical_change=0,
        )
        design, physical = state(value, expected)
        analysis = analyze(physical, penalty)
        _close(value["compliance"], analysis.compliance, "boundary compliance differs")
        return design, physical, analysis

    design, physical, analysis = boundary(witness["initial"], 0, 1 if active else 3)
    volume_gradient = backpropagate_density_gradient(density_filter, np.full(count, 1 / count))

    def update(
        previous: Any, previous_physical: Any, previous_analysis: Any, value: Any
    ) -> tuple[Any, Any]:
        reconstructed = optimality_criteria_update(
            previous,
            backpropagate_density_gradient(density_filter, previous_analysis.sensitivity),
            volume_gradient,
            density_filter,
            volume_fraction=settings.volume_fraction,
            minimum_density=settings.minimum_density,
            move_limit=settings.move_limit,
        )
        actual_design, actual_physical = state(value, {k: value[k] for k in POINT_FIELDS})
        _require(bool(np.array_equal(reconstructed, actual_design)), "OC update differs")
        expected_design_change = float(np.max(np.abs(actual_design - previous)))
        expected_physical_change = float(np.max(np.abs(actual_physical - previous_physical)))
        _require(value["density_change"] == expected_design_change, "design change differs")
        _require(value["physical_change"] == expected_physical_change, "physical change differs")
        return actual_design, actual_physical

    for index, value in enumerate(prefix):
        if index == 8:
            next_design, next_physical, analysis = boundary(transitions[0], 8, 2)
            _require(
                bool(
                    np.array_equal(next_design, design) and np.array_equal(next_physical, physical)
                ),
                "transition changes density",
            )
        _require({k: value[k] for k in POINT_FIELDS} == points[index], "prefix trace differs")
        design, physical = update(design, physical, analysis, value)
        analysis = analyze(physical, 1 if index < 8 else 2)
        _close(value["compliance"], analysis.compliance, "prefix compliance differs")
    if active:
        next_design, next_physical, analysis = boundary(transitions[1], 16, 3)
        _require(
            bool(np.array_equal(next_design, design) and np.array_equal(next_physical, physical)),
            "transition changes density",
        )
    prefix_analyses = fem_count if active else 0
    previous_known = recent[0]["iteration"] == p3[0]["iteration"]
    for value, point in zip(recent, p3[-11:], strict=True):
        next_design, next_physical = state(value, point)
        if previous_known:
            next_design, next_physical = update(design, physical, analysis, value)
        analysis = analyze(next_physical, 3)
        _close(value["compliance"], analysis.compliance, "p3-window compliance differs")
        design, physical = next_design, next_physical
        previous_known = True

    result = witness["result"]
    _require(
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
        },
        "terminal result fields differ",
    )
    _require(type(result["converged"]) is bool, "converged must be boolean")
    history = _sequence(result["history"], "result history")
    _require(len(history) == len(recent), "terminal history differs")
    for old, value in zip(history, recent, strict=True):
        _require(type(old) is dict and set(old) == OLD_STATE_FIELDS, "old history fields differ")
        _integer(old["iteration"], "old history iteration")
        _require(old == {k: value[k] for k in OLD_STATE_FIELDS}, "terminal/recent identity differs")
    _require(
        result["design_density"] == recent[-1]["design_density"]
        and result["physical_density"] == recent[-1]["physical_density"],
        "terminal density differs",
    )
    _require(result["compliance"] == recent[-1]["compliance"], "terminal scalar differs")
    analysis = analyze(physical, 3)
    _close(
        _number(result["compliance"], "terminal compliance", positive=True),
        analysis.compliance,
        "terminal compliance differs",
    )
    dofs = mesh.coordinates.shape[0] * 3
    _close(
        _vector(result["displacements"], dofs, "displacements"),
        analysis.displacements,
        "terminal displacement differs",
    )
    _close(
        _vector(result["reactions"], dofs, "reactions"),
        analysis.reactions,
        "terminal reaction differs",
    )

    first_stop = next((i for i in range(1, len(p3) + 1) if _stop(p3[:i], 0.01)), None)
    converged = first_stop is not None
    _require(not converged or first_stop == len(p3), "p3 continued after its first stop")
    _require(result["converged"] == converged, "convergence flag differs")
    _require(
        converged or updates == min(360, settings.max_iterations),
        "unconverged trajectory truncated",
    )
    volume_error = abs(float(np.mean(physical)) - settings.volume_fraction)
    quality = (
        converged
        and volume_error <= 0.005
        and (reference is None or analysis.compliance <= 1.001 * reference)
    )
    _require(not accepted or quality, "false accepted classification")
    return {
        "passed": True,
        "accepted": bool(quality),
        "quality_passed": bool(quality),
        "reference_checked": reference is not None,
        "converged": converged,
        "updates": updates,
        "prefix_analyses": prefix_analyses,
        "terminal_analyses": 1,
        "total_audit_fem": fem_count,
        "compliance": float(analysis.compliance),
        "volume_error": volume_error,
        "whole_p3_trajectory_replayed": False,
        "resource_admission": "NOT_RUN",
    }


def _native_bytes(raw: bytes, platform: str) -> dict[str, float | int]:
    """Independent explicit-unit parser; no candidate parser/helper is called."""
    _require(type(raw) is bytes, "native profile must be explicit bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid native text") from exc
    if platform == "darwin":
        times = re.findall(
            r"^\s*([0-9.]+)\s+real\s+([0-9.]+)\s+user\s+([0-9.]+)\s+sys\s*$", text, re.M
        )
        peaks = re.findall(r"^\s*(\d+)\s+maximum resident set size\s*$", text, re.M)
        _require(len(times) == len(peaks) == 1, "incomplete/ambiguous Darwin native profile")
        wall, user, system = (float(s) for s in times[0])
        rss = int(peaks[0])
    elif platform == "linux":
        matches = re.findall(r"^TOPOLAB_NATIVE ([0-9.]+) ([0-9.]+) ([0-9.]+) (\d+)\s*$", text, re.M)
        _require(len(matches) == 1, "incomplete/ambiguous Linux native profile")
        wall, user, system = (float(s) for s in matches[0][:3])
        rss = int(matches[0][3]) * 1024
    else:
        raise ValueError("unregistered native units")
    for value in (wall, user, system):
        _number(value, "native time")
    _require(rss > 0, "native RSS is unknown")
    return {"wall_seconds": wall, "user_seconds": user, "system_seconds": system, "rss_bytes": rss}


def audit_role_charge(
    native_wall: float,
    observed_wall: float,
    attempted_rows: int,
    internal_charge: float,
    reported_charge: float,
) -> float:
    """Reconstruct the failure-inclusive charge floor; unknown is never zero."""
    native_wall = _number(native_wall, "native wall")
    observed_wall = _number(observed_wall, "observed wall")
    internal_charge = _number(internal_charge, "internal charge")
    reported_charge = _number(reported_charge, "reported charge")
    attempted_rows = _integer(attempted_rows, "attempted rows")
    floor = max(native_wall, observed_wall) + attempted_rows + 10
    expected = max(internal_charge, floor)
    _require(reported_charge == expected, "whole-role charge differs")
    return expected


def _timer_exit(value: Any, exit_code: int, platform: str) -> int:
    """Check explicit parent-wait4 statistics without inventing native real time."""
    _require(type(exit_code) is int, "observed timer exit must be integer")
    _require(
        type(value) is dict
        and value.get("statistics_source") == "os.wait4"
        and value.get("wall_source") == "controller_monotonic_observed",
        "missing timer exit statistics/source",
    )
    _require(
        type(value.get("exit_code")) is int and value["exit_code"] == exit_code,
        "timer exit differs",
    )
    _require(
        value.get("rss_unit") == ("bytes" if platform == "darwin" else "KiB*1024"),
        "wait4 RSS units differ",
    )
    native = value.get("native")
    _require(
        type(native) is dict
        and {"wall_seconds", "user_seconds", "system_seconds", "rss_bytes"} <= set(native),
        "incomplete timer rusage",
    )
    for key in ("wall_seconds", "user_seconds", "system_seconds"):
        _number(native[key], "timer " + key)
    peak = _integer(native["rss_bytes"], "timer RSS")
    _require(peak > 0, "timer native RSS unknown")
    return peak


def audit_resource_record(
    record: dict[str, Any],
    *,
    profile: bytes,
    log: bytes,
    helper_profiles: dict[str, bytes],
    expected_role: str,
    expected_argv: list[str],
    platform: str,
    require_success: bool = False,
) -> dict[str, Any]:
    """Audit explicitly supplied new public receipts, never follow their paths.

    This checks empirical software records only. The controller and final binder
    exit remain pending until independently observed; no 4GiB/pre-entry guarantee
    or B/C admission follows from consistent samples and native high-water marks.
    """
    required = {
        "schema",
        "role",
        "software_only",
        "argv",
        "platform",
        "status",
        "software_result",
        "exit_code",
        "cleanup",
        "observed_outer_wall_seconds",
        "native",
        "samples",
        "helpers",
        "controller_rss_peak_bytes",
        "profile_sha256",
        "log_sha256",
        "controller_complete_exit",
        "scientific_resource_admission",
        "limit_bytes",
        "timeout_seconds",
        "ps_rss_unit",
        "native_rss_unit",
        "target_sample_interval_seconds",
        "pid",
        "timer_native_exit",
    }
    _require(type(record) is dict and required <= set(record), "incomplete public resource record")
    _require(
        record["schema"] == "topolab.v2.m2-native-rss-exit-assurance.v1", "resource schema differs"
    )
    _require(
        record["role"] == expected_role and record["argv"] == expected_argv,
        "registered role/command differs",
    )
    _require(
        record["platform"] == platform and record["software_only"] is True,
        "software platform differs",
    )
    _require(record["status"] == "PENDING_POSTEXIT", "pre-exit record must remain pending")
    _require(
        record["controller_complete_exit"] == "UNKNOWN_PENDING_OUTER_PROFILE",
        "controller exit falsely closed",
    )
    _require(
        record["scientific_resource_admission"] == "NOT_RUN",
        "public receipt claims scientific admission",
    )
    _require(record["ps_rss_unit"] == "KiB*1024", "ps units differ")
    _require(
        record["native_rss_unit"] == ("bytes" if platform == "darwin" else "KiB*1024"),
        "native units differ",
    )
    _require(type(require_success) is bool, "require_success must be boolean")
    _require(
        type(profile) is bytes and type(log) is bytes and type(helper_profiles) is dict,
        "explicit new evidence bytes required",
    )
    _require(
        record["profile_sha256"] == hashlib.sha256(profile).hexdigest(),
        "native profile hash differs",
    )
    _require(record["log_sha256"] == hashlib.sha256(log).hexdigest(), "command log hash differs")
    measured = _native_bytes(profile, platform)
    _require(record["native"] == measured, "native values/units differ from bytes")
    limit = _integer(record["limit_bytes"], "memory cap")
    _require(0 < limit <= 4294967296, "memory cap differs")
    timeout = _number(record["timeout_seconds"], "timeout", positive=True)
    interval = _number(record["target_sample_interval_seconds"], "target interval", positive=True)
    _require(interval <= 0.5, "target sample interval exceeds proposal")
    elapsed = _number(record["observed_outer_wall_seconds"], "outer wall")
    peak = _integer(record["controller_rss_peak_bytes"], "controller peak")
    _require(peak > 0, "controller peak unknown")
    samples = _sequence(record["samples"], "samples")
    helpers = _sequence(record["helpers"], "helpers")
    _require(samples and len(samples) == len(helpers), "sample/helper coverage differs")
    _require(
        all(type(h) is dict and type(h.get("profile")) is str for h in helpers),
        "malformed helper identity",
    )
    _require(
        set(helper_profiles) == {h.get("profile") for h in helpers},
        "explicit helper-profile coverage differs",
    )
    previous = None
    high = int(measured["rss_bytes"])
    helper_peak = 0
    launch_pid = _integer(record["pid"], "launch pid")
    command_timer = _timer_exit(record["timer_native_exit"], record["exit_code"], platform)
    _require(record["timer_native_exit"].get("pid") == launch_pid, "command timer pid differs")
    observed_success = record["software_result"] == "PUBLIC_COMMAND_EXIT_OBSERVED"
    for index, (sample, helper) in enumerate(zip(samples, helpers, strict=True)):
        _require(type(sample) is dict and type(helper) is dict, "sample/helper type differs")
        _require(
            {
                "offset_seconds",
                "actual_interval_seconds",
                "roles",
                "controller_rss_bytes",
                "group_plus_controller_rss_bytes",
            }
            <= set(sample),
            "incomplete sample",
        )
        _require(
            {
                "role",
                "exit_code",
                "native",
                "profile",
                "profile_sha256",
                "cleanup",
                "problem",
                "timer_native_exit",
                "pid",
            }
            <= set(helper),
            "incomplete helper",
        )
        _require(helper["role"] == f"rss-sampler-{index}", "sampler role order differs")
        helper_raw = helper_profiles[helper["profile"]]
        _require(
            helper["profile_sha256"] == hashlib.sha256(helper_raw).hexdigest(),
            "helper profile hash differs",
        )
        helper_native = _native_bytes(helper_raw, platform)
        _require(
            helper["native"] == helper_native and helper["exit_code"] == 0,
            "helper native/exit differs",
        )
        _require(type(helper["cleanup"]) is dict, "malformed sampler cleanup")
        _require(
            helper["problem"] is None
            and helper["cleanup"].get("group_gone") is True
            and helper["cleanup"].get("leader_exit") == helper["exit_code"],
            "sampler cleanup incomplete",
        )
        sampler_timer = _timer_exit(helper["timer_native_exit"], helper["exit_code"], platform)
        _require(
            helper["timer_native_exit"].get("pid") == helper["pid"], "sampler timer pid differs"
        )
        sampler_chain = int(helper_native["rss_bytes"]) + sampler_timer
        helper_peak = max(helper_peak, sampler_chain)
        offset = _number(sample["offset_seconds"], "sample time")
        _require(offset <= elapsed, "sample after observed outer exit")
        if previous is None:
            _require(sample["actual_interval_seconds"] is None, "initial interval fabricated")
        else:
            observed_interval = _number(sample["actual_interval_seconds"], "actual interval")
            _require(
                offset >= previous and abs(observed_interval - (offset - previous)) <= 1e-12,
                "sample interval differs",
            )
        previous = offset
        controller = _integer(sample["controller_rss_bytes"], "sample controller RSS")
        _require(0 < controller <= peak, "controller RSS exceeds recorded peak")
        rows = _sequence(sample["roles"], "process rows")
        _require(all(type(row) is dict for row in rows), "malformed process rows")
        if observed_success:
            _require(
                len(rows) <= 2
                and all(
                    r.get("pgid") == launch_pid
                    and (r.get("pid") == launch_pid or r.get("parent") == launch_pid)
                    for r in rows
                ),
                "unregistered descendant in successful receipt",
            )
        identities = set()
        group_rss = 0
        for row in rows:
            _require(
                type(row) is dict and {"pid", "parent", "pgid", "rss_bytes"} <= set(row),
                "incomplete process row",
            )
            pid = _integer(row["pid"], "pid")
            _require(pid > 0 and pid not in identities, "duplicate/invalid process identity")
            identities.add(pid)
            _integer(row["parent"], "parent")
            _integer(row["pgid"], "pgid")
            group_rss += _integer(row["rss_bytes"], "process RSS")
        summed = _integer(sample["group_plus_controller_rss_bytes"], "sample RSS sum")
        _require(summed == group_rss + controller, "sample group/controller arithmetic differs")
        high = max(high, summed + sampler_chain)
    native_overlap = int(measured["rss_bytes"]) + command_timer + peak + helper_peak
    high = max(high, native_overlap)
    if "native_plus_controller_and_sampler_rss_bytes" in record:
        _require(
            record["native_plus_controller_and_sampler_rss_bytes"] == native_overlap,
            "native overlap arithmetic differs",
        )
    cleanup = record["cleanup"]
    _require(
        type(cleanup) is dict and {"group_gone", "leader_exit"} <= set(cleanup),
        "missing group cleanup evidence",
    )
    _require(cleanup["leader_exit"] == record["exit_code"], "leader exit identity differs")
    if observed_success:
        _require(
            record["exit_code"] == 0 and cleanup["group_gone"] is True,
            "false complete process exit",
        )
        _require(high <= limit and elapsed <= timeout, "successful receipt exceeds complete cap")
        _require(
            all(row.get("group_gone") is True for row in record.get("escaped_group_cleanup", [])),
            "escaped group exit is unknown",
        )
    _require(
        not require_success or observed_success, "public command did not complete successfully"
    )
    return {
        "software_record_consistent": True,
        "public_command_success": observed_success,
        "empirical_recorded_peak_bytes": high,
        "observed_outer_wall_seconds": elapsed,
        "controller_exit": "PENDING_OUTER_PROFILE",
        "resource_admission": "NOT_RUN",
        "instantaneous_or_preentry_bound_proved": False,
        "a_priori_allocation_proof_required_for_new_identity": False,
        "individual_timer_native_coverage": "PARENT_WAIT4_STATISTICS_CHECKED",
    }


def audit_exit_binding(
    binding: dict[str, Any],
    *,
    prior: bytes,
    profile: bytes,
    log: bytes,
    expected_label: str,
    observed_exit_code: int,
    platform: str,
) -> dict[str, Any]:
    """Verify one append-only public binding from explicitly supplied bytes.

    The caller observes the outer command exit independently. This function
    cannot observe its own eventual exit and never closes the final observer.
    """
    _require(type(binding) is dict, "binding must be a JSON object")
    transitions = {
        "controller": ("PENDING_POSTEXIT", "PENDING_BINDER_EXIT"),
        "binder": ("PENDING_BINDER_EXIT", "PENDING_VERIFIER_EXIT"),
        "verifier": ("PENDING_VERIFIER_EXIT", "PENDING_VERIFIER_EXIT"),
    }
    _require(
        expected_label in transitions and type(observed_exit_code) is int,
        "unregistered observed exit",
    )
    _require(
        type(prior) is bytes and type(log) is bytes and type(profile) is bytes,
        "explicit immutable binding bytes required",
    )
    previous = json.loads(prior)
    before, after = transitions[expected_label]
    _require(
        type(previous) is dict and previous.get("status") == before, "prior binding order differs"
    )
    _require(
        previous.get("schema") == "topolab.v2.m2-native-rss-exit-assurance.v1"
        and previous.get("software_only") is True,
        "prior public identity differs",
    )
    _require(
        binding.get("record_sha256") == hashlib.sha256(prior).hexdigest()
        and binding.get("profile_sha256") == hashlib.sha256(profile).hexdigest()
        and binding.get("log_sha256") == hashlib.sha256(log).hexdigest(),
        "exit binding byte identity differs",
    )
    _require(
        binding.get("schema") == previous["schema"] and binding.get("software_only") is True,
        "binding identity differs",
    )
    _require(
        binding.get("prior_status") == before
        and binding.get("status") == after
        and binding.get("bound_role") == expected_label,
        "binding transition differs",
    )
    _require(
        type(binding.get("exit_code")) is int and binding["exit_code"] == observed_exit_code,
        "observed exit differs",
    )
    measured = _native_bytes(profile, platform)
    _require(binding.get("native") == measured, "binding native statistics differ")
    _require(
        binding.get("resource_cap_exceeded") is (measured["rss_bytes"] > 4294967296),
        "post-exit cap classification differs",
    )
    _require(
        binding.get("scientific_resource_admission") == "NOT_RUN"
        and binding.get("actual_observer_verification") == "REQUIRED_AFTER_THIS_ROLE_EXITS",
        "binding falsely closes resource/observer admission",
    )
    return {
        "binding_consistent": True,
        "observed_exit_code": observed_exit_code,
        "final_observer_exit": "NOT_SELF_OBSERVABLE",
        "resource_admission": "NOT_RUN",
    }


def audit_public_fixture(payload: dict[str, Any], *, fixture_bytes: bytes) -> dict[str, Any]:
    """Rebuild only the literal NEW seed17 public model, encoding and projection."""
    import torch

    from topolab.b2_9_vector_load import encode_vector_load_case
    from topolab.b2_12_context_cnn import ContextCNN
    from topolab.experiment import project_design_density
    from topolab.problem import TopologyProblem

    _require(
        type(payload) is dict
        and type(payload.get("witness")) is dict
        and type(payload["witness"].get("initial")) is dict,
        "public payload fields differ",
    )
    _require(
        type(fixture_bytes) is bytes
        and len(fixture_bytes) == 638
        and hashlib.sha256(fixture_bytes).hexdigest()
        == "c6fdfdd46f722f3dad8910ec0941ed1adfbc4009d8f65ffacbab19a2bfe63b9a",
        "literal new public fixture differs",
    )
    fixture = json.loads(fixture_bytes)
    _require(
        set(fixture) == {"schema", "purpose", "problem"}
        and fixture["schema"] == "topolab.v2.m2-new-public-fixture.v1"
        and fixture["purpose"] == "new authored software fixture; no historical input",
        "fixture identity differs",
    )
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(fixture["problem"]))
    _require(
        payload.get("schema") == "topolab.v2.p17-m2-native-homotopy.stage-a.v1"
        and payload.get("status") == "PUBLIC_SOFTWARE_ONLY_NOT_B_OR_C"
        and payload.get("historical_model") is False
        and payload.get("old_input_read_set") == []
        and type(payload.get("formal_attempts")) is int
        and payload["formal_attempts"] == 0,
        "public invocation authority/identity differs",
    )
    _require(payload.get("case") == case.model_dump(mode="json"), "public case identity differs")
    _require(payload.get("fixture") in ("tiny-prefix", "tiny-plain"), "public fixture mode differs")
    _require(
        payload["witness"]["active"] is (payload["fixture"] == "tiny-prefix"),
        "public schedule differs",
    )
    encoded = encode_vector_load_case(case).input_tensor
    _require(
        encoded.shape[0] == 13 and encoded.dtype == np.float32, "public encoder identity differs"
    )
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(17)
        model = ContextCNN().cpu().eval()
        _require(sum(p.numel() for p in model.parameters()) == 26433, "model architecture differs")
        model_hash = hashlib.sha256(
            b"".join(p.detach().numpy().tobytes() for p in model.parameters())
        ).hexdigest()
        with torch.inference_mode():
            prediction = (
                model(torch.from_numpy(encoded.copy()).unsqueeze(0)).squeeze(0).numpy().copy()
            )
    _require(payload.get("new_weight_identity") == model_hash, "new public weight identity differs")
    projected = project_design_density(case, prediction)
    initial = payload["witness"]["initial"]
    _require(
        initial["design_density"] == projected.design_density.tolist()
        and initial["physical_density"] == projected.physical_density.tolist(),
        "public model/legacy projection differs from initial state",
    )
    result = audit_witness(case, payload["witness"])
    return {
        "new_model_encoding_projection_checked": True,
        "historical_model_used": False,
        "weight_sha256": model_hash,
        "witness": result,
        "scientific_resource_admission": "NOT_RUN",
    }
