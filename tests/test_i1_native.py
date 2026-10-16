"""Public software regression of the I1 path; no historical payload or experiment."""

import ctypes as ct
import hashlib
import json
import platform
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from safetensors.torch import save

from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_12_context_cnn import ContextCNN
from topolab.experiment import ExperimentCase, encode_case, project_design_density
from topolab.fem import (
    assemble_global_stiffness,
    build_constrained_dofs,
    build_load_vector,
    hex8_element_stiffness,
)
from topolab.mesh import generate_structured_hex8
from topolab.model import FixedFaceSupport, PointLoad
from topolab.problem import (
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)
from topolab.simp import (
    SimpConfig,
    backpropagate_density_gradient,
    build_density_filter,
    evaluate_compliance,
    optimality_criteria_update,
    optimize_simp,
)

ROOT = Path(__file__).resolve().parents[1]
N = 1728
STATES = 361
FP = ct.POINTER(ct.c_float)
DP = ct.POINTER(ct.c_double)


class Case(ct.Structure):
    _fields_ = (
        [(s, ct.c_int) for s in ("nx", "ny", "nz")]
        + [
            (s, ct.c_double)
            for s in (
                "lx",
                "ly",
                "lz",
                "young",
                "nu",
                "emin",
                "radius",
                "volume",
                "minimum",
                "move",
            )
        ]
        + [(s, ct.c_int) for s in ("load_x", "load_y", "load_z", "direction")]
        + [("magnitude", ct.c_double)]
    )


class History(ct.Structure):
    _fields_ = (
        [
            (s, ct.c_int)
            for s in (
                "updates",
                "analyses",
                "converged",
                "phase_count",
                "selected",
                "polish_updates",
                "initial_analyses",
                "polish_rechecks",
            )
        ]
        + [("penalty", ct.c_int * STATES)]
        + [
            (s, ct.c_double * STATES)
            for s in ("compliance", "volume", "design_change", "physical_change")
        ]
        + [(s, (ct.c_double * N) * STATES) for s in ("design", "physical")]
    )


def ptr(a):
    return a.ctypes.data_as(FP if a.dtype == np.float32 else DP)


@pytest.fixture(scope="module")
def lib(tmp_path_factory):
    directory = tmp_path_factory.mktemp("i1-native-public")
    compiler = shutil.which("cc")
    assert compiler is not None, "I1 public software regression requires a C compiler"
    binary = directory / "i1.so"
    subprocess.run(
        [
            compiler,
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fPIC",
            "-shared",
            "-fno-math-errno",
            "-ffp-contract=off",
            *(
                str(ROOT / "native" / "i1" / n)
                for n in ("query.c", "vectors.c", "readers.c", "audit.c", "sha256.c")
            ),
            "-lm",
            "-o",
            str(binary),
        ],
        check=True,
    )
    library = ct.CDLL(str(binary))
    library.i1_setup.argtypes = [ct.POINTER(Case)]
    library.i1_model_role.argtypes = [ct.POINTER(Case), ct.c_int]
    library.i1_encode.argtypes = [FP]
    library.i1_predict.argtypes = [FP, FP]
    library.i1_element.argtypes = [ct.c_double] * 4 + [DP]
    library.i1_filter.argtypes = [DP, DP]
    library.i1_project.argtypes = [DP, DP, DP]
    library.i1_analyze.argtypes = [DP, ct.c_int, DP, DP, DP]
    library.i1_recover.argtypes = [ct.POINTER(Case), DP, ct.c_int, DP, DP, DP]
    library.i1_audit_full.argtypes = [ct.POINTER(Case), DP, DP, DP]
    library.i1_update.argtypes = [DP, DP, DP]
    library.i1_physics_raw.argtypes = [DP]
    library.i1_encode_legacy.argtypes = [FP]
    library.i1_nn_offer.argtypes = [FP, FP, ct.c_char_p]
    library.i1_nn_result.argtypes = [DP]
    library.i1_nn_metadata.argtypes = [ct.c_void_p, DP]
    library.i1_run.argtypes = [DP, ct.c_int, ct.c_int]
    library.i1_polish_keep.argtypes = [ct.c_int]
    library.i1_evaluate.argtypes = [
        DP,
        ct.c_int,
        ct.c_int,
        ct.c_double,
        ct.POINTER(ct.c_int),
        ct.POINTER(ct.c_int),
    ]
    library.i1_history.restype = ct.POINTER(History)
    library.i1_attempt_history.restype = ct.POINTER(History)
    library.i1_model_read.argtypes = [ct.c_void_p, ct.c_ulong, FP]
    library.i1_case_read.argtypes = [
        ct.c_void_p,
        ct.c_ulong,
        ct.POINTER(Case),
        ct.POINTER(ct.c_int),
        ct.POINTER(ct.c_int),
        ct.POINTER(ct.c_int),
    ]
    library.i1_audit_analysis.argtypes = [ct.POINTER(Case), DP, ct.c_int, DP, DP, DP]
    library.i1_audit_density.argtypes = [ct.POINTER(Case), DP, DP, ct.c_double, DP]
    library.i1_storage_bytes.restype = ct.c_ulong
    library.i1_audit_storage_bytes.restype = ct.c_ulong
    library.i1_sha256.argtypes = [ct.c_void_p, ct.c_ulong, ct.c_void_p]
    return library


def spec(shape=(3, 2, 1), volume=0.48321, direction=1):
    nx, ny, nz = shape
    return Case(
        nx, ny, nz, 12, 6, 3, 1000, 0.3, 1, 1.5, volume, 0.05, 0.2, nx, ny // 2, nz, direction, -1
    )


def problem(c):
    return TopologyProblem(
        mesh=MeshDefinition(element_counts=(c.nx, c.ny, c.nz), lengths=(c.lx, c.ly, c.lz)),
        material=MaterialDefinition(
            solid_modulus=c.young, minimum_modulus=c.emin, poisson_ratio=c.nu
        ),
        supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
        loads=(
            PointLoadDefinition(
                node=c.load_x + (c.nx + 1) * (c.load_y + (c.ny + 1) * c.load_z),
                direction=c.direction,
                magnitude=c.magnitude,
            ),
        ),
        optimization=OptimizationDefinition(
            volume_fraction=c.volume,
            filter_radius=c.radius,
            penalty=3,
            minimum_density=c.minimum,
            move_limit=c.move,
            convergence_tolerance=0.01,
            max_iterations=360,
        ),
    )


def core(c):
    mesh = generate_structured_hex8(c.nx, c.ny, c.nz, lengths=(c.lx, c.ly, c.lz))
    fixed = build_constrained_dofs(mesh, [FixedFaceSupport(axis="x", side="min")])
    load = build_load_vector(
        mesh,
        [
            PointLoad(
                node=c.load_x + (c.nx + 1) * (c.load_y + (c.ny + 1) * c.load_z),
                direction=c.direction,
                magnitude=c.magnitude,
            )
        ],
    )
    return mesh, fixed, load


def analyze(lib, c, rho, penalty=3, audit=False):
    gradient = np.empty(c.nx * c.ny * c.nz, dtype=np.float64)
    u = np.empty(3 * c.nx * (c.ny + 1) * (c.nz + 1), dtype=np.float64)
    cc = ct.c_double()
    if audit:
        code = lib.i1_audit_analysis(
            ct.byref(c), ptr(rho), penalty, ct.byref(cc), ptr(gradient), ptr(u)
        )
    else:
        code = lib.i1_analyze(ptr(rho), penalty, ct.byref(cc), ptr(gradient), ptr(u))
    assert code == 0, f"native analysis failed: {code}"
    return cc.value, gradient, u


@pytest.mark.parametrize("dimensions", [(2.0, 3.0, 4.0), (1.0, 1.0, 1.0), (0.5, 0.5, 0.5)])
def test_element_matches_frozen_n1_matrix_tolerances(lib, dimensions):
    actual = np.empty((24, 24), dtype=np.float64)
    assert lib.i1_element(*dimensions, 0.3, ptr(actual)) == 0
    expected = hex8_element_stiffness(1.0, 0.3, dimensions=dimensions)
    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(actual, actual.T, rtol=1e-12, atol=1e-12)
    eig = np.linalg.eigvalsh(actual)
    assert np.max(np.abs(eig[:6])) <= np.max(np.abs(eig)) * 1e-12


@pytest.mark.parametrize("shape", [(3, 2, 1), (12, 6, 3), (24, 12, 6)])
@pytest.mark.parametrize("penalty", [1, 2, 3])
def test_both_native_derivations_match_existing_fem_and_gradient(lib, shape, penalty):
    c = spec(shape)
    assert lib.i1_setup(ct.byref(c)) == 0
    rho = np.linspace(0.33, 0.61, c.nx * c.ny * c.nz)
    mesh, fixed, load = core(c)
    expected = evaluate_compliance(
        mesh,
        rho,
        load,
        fixed,
        solid_modulus=c.young,
        minimum_modulus=c.emin,
        poisson_ratio=c.nu,
        penalty=penalty,
    )
    a, ga, ua = analyze(lib, c, rho, penalty)
    b, gb, ub = analyze(lib, c, rho, penalty, audit=True)
    assert a == pytest.approx(expected.compliance, rel=1e-9, abs=0)
    assert b == pytest.approx(expected.compliance, rel=1e-9, abs=0)
    np.testing.assert_allclose(ga, expected.sensitivity, rtol=1e-9, atol=1e-10)
    np.testing.assert_allclose(gb, expected.sensitivity, rtol=1e-9, atol=1e-10)
    free = []
    for x in range(1, c.nx + 1):
        for y in range(c.ny + 1):
            for z in range(c.nz + 1):
                free.extend(3 * (x + (c.nx + 1) * (y + (c.ny + 1) * z)) + d for d in range(3))
    np.testing.assert_allclose(ua, expected.displacements[free], rtol=1e-9, atol=1e-10)
    np.testing.assert_allclose(ub, expected.displacements[free], rtol=1e-9, atol=1e-10)
    unit = hex8_element_stiffness(1.0, c.nu, dimensions=(c.lx / c.nx, c.ly / c.ny, c.lz / c.nz))
    stiffness = assemble_global_stiffness(
        mesh, unit, element_factors=c.emin + (c.young - c.emin) * rho**penalty
    )
    displacement = np.zeros(load.size)
    displacement[free] = ua
    residual = stiffness @ displacement - load
    np.testing.assert_allclose(residual[free], 0, rtol=0, atol=1e-10)
    balance = residual[fixed].reshape(-1, 3).sum(axis=0) + load.reshape(-1, 3).sum(axis=0)
    np.testing.assert_allclose(balance, 0, rtol=0, atol=1e-10)
    full = np.empty(6825, dtype=np.float64)
    reaction = np.empty_like(full)
    assert lib.i1_recover(ct.byref(c), ptr(rho), penalty, ptr(ua), ptr(full), ptr(reaction)) == 0
    np.testing.assert_allclose(full[: load.size], displacement, rtol=1e-9, atol=1e-10)
    np.testing.assert_allclose(reaction[: load.size], expected.reactions, rtol=1e-9, atol=1e-10)
    if penalty == 3:
        assert lib.i1_audit_full(ct.byref(c), ptr(rho), ptr(full), ptr(reaction)) == 0
        reaction[0] += 0.01
        assert lib.i1_audit_full(ct.byref(c), ptr(rho), ptr(full), ptr(reaction)) != 0


def test_projection_oc_and_native_query_match_unchanged_core(lib):
    c = spec()
    assert lib.i1_setup(ct.byref(c)) == 0
    case = ExperimentCase.from_problem(problem(c))
    raw = np.linspace(0.1, 0.8, c.nx * c.ny * c.nz)
    x, rho = np.empty_like(raw), np.empty_like(raw)
    assert lib.i1_project(ptr(raw), ptr(x), ptr(rho)) == 0
    expected = project_design_density(case, raw.reshape(1, c.nz, c.ny, c.nx))
    np.testing.assert_allclose(x, expected.design_density, rtol=0, atol=2e-11)
    np.testing.assert_allclose(rho, expected.physical_density, rtol=0, atol=2e-11)
    _, grad, _ = analyze(lib, c, rho)
    next_x = np.empty_like(x)
    assert lib.i1_update(ptr(x), ptr(grad), ptr(next_x)) == 0
    mesh, fixed, load = core(c)
    filt = build_density_filter(mesh, c.radius)
    oc = optimality_criteria_update(
        x,
        backpropagate_density_gradient(filt, grad),
        backpropagate_density_gradient(filt, np.full(raw.size, 1 / raw.size)),
        filt,
        volume_fraction=c.volume,
        minimum_density=c.minimum,
        move_limit=c.move,
    )
    np.testing.assert_allclose(next_x, oc, rtol=0, atol=2e-11)
    assert lib.i1_run(ptr(raw), 0, 3) == 0
    h = lib.i1_history().contents
    existing = optimize_simp(
        mesh,
        load,
        fixed,
        config=SimpConfig(
            volume_fraction=c.volume,
            filter_radius=c.radius,
            minimum_density=c.minimum,
            move_limit=c.move,
            penalty=3,
            max_iterations=3,
        ),
        solid_modulus=c.young,
        minimum_modulus=c.emin,
        poisson_ratio=c.nu,
        initial_density=x,
    )
    np.testing.assert_allclose(
        np.asarray(h.design[h.updates])[: raw.size], existing.design_density, rtol=0, atol=2e-11
    )
    assert h.compliance[h.updates] == pytest.approx(existing.compliance, rel=1e-9, abs=0)
    assert h.analyses == h.updates + 2


@pytest.mark.parametrize("shape", [(12, 6, 3), (24, 12, 6)])
def test_encoding_safetensors_and_inference_against_frozen_graph(lib, shape):
    c = spec(shape)
    assert lib.i1_setup(ct.byref(c)) == 0
    n = c.nx * c.ny * c.nz
    encoded = np.empty((13, c.nz, c.ny, c.nx), dtype=np.float32)
    assert lib.i1_encode(ptr(encoded)) == 0
    case = ExperimentCase.from_problem(problem(c))
    expected = encode_vector_load_case(case).input_tensor
    np.testing.assert_array_equal(encoded, expected)
    model = ContextCNN()
    with torch.no_grad():
        for i, value in enumerate(model.parameters()):
            value.copy_(
                ((torch.arange(value.numel()).reshape(value.shape) % 11) - 5) * 0.001 + i * 0.0001
            )
    payload = save(
        model.state_dict(),
        metadata={
            "topolab": json.dumps(
                {
                    "checkpoint_version": "topolab.b3.checkpoint.v1",
                    "context_sha256": "0" * 64,
                    "recipe": "P",
                    "seed": 17,
                    "selected_epoch": 1,
                }
            )
        },
    )
    weights = np.empty(26433, dtype=np.float32)
    assert lib.i1_model_read(payload, len(payload), ptr(weights)) == 0
    actual = np.empty(n, dtype=np.float32)
    assert lib.i1_predict(ptr(weights), ptr(actual)) == 0
    with torch.no_grad():
        reference = model(torch.from_numpy(expected[None])).numpy().reshape(-1)
    # New CPU-float32 port parity, not a relaxed physics or historical acceptance tolerance.
    np.testing.assert_allclose(
        actual, reference, rtol=np.finfo(np.float32).eps, atol=np.finfo(np.float32).eps
    )
    with pytest.raises(AssertionError):
        np.testing.assert_array_equal(actual, np.full(n, 0.5, dtype=np.float32))


def test_homotopy_phase_history_is_not_rewritten_and_counts_all_analyses(lib):
    c = spec((24, 12, 6))
    assert lib.i1_setup(ct.byref(c)) == 0
    raw = np.full(N, 0.48321)
    assert lib.i1_run(ptr(raw), 1, 17) == 0
    h = lib.i1_history().contents
    assert h.updates == 17 and not h.converged
    assert list(h.penalty[:18]) == [1] * 9 + [2] * 8 + [3]
    assert h.phase_count == 1
    assert h.analyses == 17 + 2 + 2
    for index in (8, 16, 17):
        rho = np.array(h.physical[index])
        cc, _, _ = analyze(lib, c, rho, h.penalty[index], audit=True)
        assert h.compliance[index] == pytest.approx(cc, rel=1e-9, abs=0)


@pytest.mark.parametrize(
    "field,value",
    [
        ("nx", 25),
        ("ny", 13),
        ("nu", 0.5),
        ("emin", 1000),
        ("volume", float("nan")),
        ("load_x", 0),
        ("direction", -1),
    ],
)
def test_rejects_invalid_case_before_any_numerical_access(lib, field, value):
    c = spec()
    setattr(c, field, value)
    assert lib.i1_setup(ct.byref(c)) != 0


def public_request(shape=(3, 2, 1)):
    c = spec(shape)

    def bits(x):
        return struct.pack(">d", float(x)).hex()

    return {
        "schema": "topolab.i1.public-case.v1",
        "mesh": list(shape),
        "lengths": [bits(x) for x in (12, 6, 3)],
        "young": bits(1000),
        "nu": bits(0.3),
        "emin": bits(1),
        "radius": bits(1.5),
        "volume": bits(c.volume),
        "minimum": bits(0.05),
        "move": bits(0.2),
        "load": [c.load_x, c.load_y, c.load_z, 1],
        "magnitude": bits(-1),
        "limit": 3,
        "method": "uniform",
    }


def test_case_and_model_reader_failures_are_explicit_and_bounded(lib):
    c = Case()
    h, limit, initial = ct.c_int(), ct.c_int(), ct.c_int()
    payload = json.dumps(public_request()).encode()
    assert (
        lib.i1_case_read(
            payload, len(payload), ct.byref(c), ct.byref(h), ct.byref(limit), ct.byref(initial)
        )
        == 0
    )
    assert limit.value == 3 and initial.value == 0
    assert struct.pack(">d", c.volume).hex() == public_request()["volume"]
    assert struct.pack(">d", c.nu).hex() == public_request()["nu"]
    for bad in [
        payload[:-1],
        payload + b"garbage",
        payload.replace(b'"limit": 3', b'"limit": 3, "limit": 3'),
        b'{"a":' + b"[" * 18 + b"1" + b"]" * 18 + b"}",
        json.dumps({**public_request(), "volume": "7ff8000000000000"}).encode(),
    ]:
        assert (
            lib.i1_case_read(
                bad, len(bad), ct.byref(c), ct.byref(h), ct.byref(limit), ct.byref(initial)
            )
            != 0
        )
    weights = np.empty(26433, dtype=np.float32)
    for bad in [b"", b"\xff" * 8, b"\x00" * 131073, b"\x02" + b"\x00" * 7 + b"{}"]:
        assert lib.i1_model_read(bad, len(bad), ptr(weights)) != 0
    assert lib.i1_storage_bytes() <= 256 * 1024**2
    assert lib.i1_audit_storage_bytes() <= 256 * 1024**2


def test_candidate_free_density_audit_rejects_tampering(lib):
    c = spec()
    assert lib.i1_setup(ct.byref(c)) == 0
    x = np.full(6, c.volume)
    rho = np.empty_like(x)
    assert lib.i1_filter(ptr(x), ptr(rho)) == 0
    cc, _, _ = analyze(lib, c, rho)
    actual = ct.c_double()
    assert lib.i1_audit_density(ct.byref(c), ptr(x), ptr(rho), cc, ct.byref(actual)) == 0
    assert lib.i1_audit_density(ct.byref(c), ptr(x), ptr(rho), cc * 1.01, ct.byref(actual)) != 0
    rho[0] += 0.001
    assert lib.i1_audit_density(ct.byref(c), ptr(x), ptr(rho), cc, ct.byref(actual)) != 0


@pytest.mark.parametrize("volume", [1.0, 0.0500003])
def test_legacy_projection_endpoint_short_circuits_are_retained(lib, volume):
    c = spec(volume=volume)
    assert lib.i1_setup(ct.byref(c)) == 0
    raw = np.full(6, 0.2)
    x, rho = np.empty_like(raw), np.empty_like(raw)
    assert lib.i1_project(ptr(raw), ptr(x), ptr(rho)) == 0
    expected = project_design_density(
        ExperimentCase.from_problem(problem(c)), raw.reshape(1, 1, 2, 3)
    )
    np.testing.assert_array_equal(x, expected.design_density)
    np.testing.assert_array_equal(rho, expected.physical_density)


def test_physics_control_and_streaming_nearest_neighbor_match_existing_definitions(lib):
    c = spec()
    assert lib.i1_setup(ct.byref(c)) == 0
    raw = np.empty(6, dtype=np.float64)
    assert lib.i1_physics_raw(ptr(raw)) == 0
    _, gradient, _ = analyze(lib, c, np.full(6, c.volume))
    score = np.maximum(0, -gradient)
    expected = ((score - score.min()) / (score.max() - score.min())).astype(np.float32)
    np.testing.assert_array_equal(raw, expected.astype(np.float64))
    assert lib.i1_run(ptr(raw), 0, 1) == 0
    assert lib.i1_history().contents.initial_analyses == 1
    assert lib.i1_history().contents.analyses == 4
    encoded = np.empty((10, c.nz, c.ny, c.nx), dtype=np.float32)
    assert lib.i1_encode_legacy(ptr(encoded)) == 0
    expected_input = encode_case(ExperimentCase.from_problem(problem(c))).input_tensor
    np.testing.assert_array_equal(encoded, expected_input)
    assert lib.i1_nn_begin() == 0
    first = np.full(6, 0.25, dtype=np.float32)
    second = np.full(6, 0.75, dtype=np.float32)
    for index, label in enumerate((first, second)):
        assert lib.i1_nn_offer(ptr(encoded), ptr(label), f"tlcase-v1-{index:064x}".encode()) == 0
    assert lib.i1_nn_result(ptr(raw)) == 0
    np.testing.assert_array_equal(raw, first.astype(np.float64))
    identifier = ct.create_string_buffer(75)
    distance = ct.c_double()
    assert lib.i1_nn_metadata(identifier, ct.byref(distance)) == 0
    assert identifier.value == b"tlcase-v1-" + b"0" * 64 and distance.value == 0
    assert lib.i1_nn_offer(ptr(encoded), ptr(second), b"tlcase-v1-" + b"0" * 64) != 0
    for index in range(2, 528):
        assert lib.i1_nn_offer(ptr(encoded), ptr(second), f"tlcase-v1-{index:064x}".encode()) == 0
    assert lib.i1_nn_offer(ptr(encoded), ptr(second), f"tlcase-v1-{528:064x}".encode()) != 0


def test_failed_attempt_is_not_repaired_by_uniform_fallback(lib):
    c = spec()
    assert lib.i1_setup(ct.byref(c)) == 0
    bad = np.full(6, np.nan)
    succeeded, fallback = ct.c_int(), ct.c_int()
    assert lib.i1_evaluate(ptr(bad), 0, 360, 1e30, ct.byref(succeeded), ct.byref(fallback)) == 0
    assert fallback.value == 1 and succeeded.value == 1
    assert lib.i1_attempt_status() == 1
    assert lib.i1_attempt_history().contents.updates == 0
    h = lib.i1_history().contents
    assert h.analyses == h.updates + 2
    assert h.penalty[h.selected] == 3
    assert h.converged
    assert lib.i1_setup(ct.byref(c)) == 0
    raw = np.full(6, c.volume)
    assert lib.i1_evaluate(ptr(raw), 0, 360, 1e-30, ct.byref(succeeded), ct.byref(fallback)) == 0
    assert fallback.value == 1 and succeeded.value == 0
    assert lib.i1_attempt_status() == 4
    assert lib.i1_attempt_history().contents.analyses > 2


def test_fixed_specialist_route_and_rejection_do_not_change_seed_or_schedule(lib):
    for shape in ((12, 6, 3), (24, 12, 6)):
        for direction in (1, 2):
            for volume in (0.48321, 0.55):
                c = spec(shape, volume, direction)
                for method in range(3):
                    expected = 3 if shape[0] == 24 and direction == 1 and volume >= 0.55 else method
                    assert lib.i1_model_role(ct.byref(c), method) == expected
    c = spec((12, 6, 3), direction=0)
    assert lib.i1_model_role(ct.byref(c), 1) == -1


@pytest.mark.parametrize("step", [1e-4, 5e-5])
def test_native_compliance_gradient_matches_two_step_finite_difference(lib, step):
    c = spec()
    assert lib.i1_setup(ct.byref(c)) == 0
    rho = np.linspace(0.3, 0.65, 6)
    _, gradient, _ = analyze(lib, c, rho)
    for index in (0, 3, 5):
        plus, minus = rho.copy(), rho.copy()
        plus[index] += step
        minus[index] -= step
        cp, _, _ = analyze(lib, c, plus, audit=True)
        cm, _, _ = analyze(lib, c, minus, audit=True)
        assert (cp - cm) / (2 * step) == pytest.approx(gradient[index], rel=1e-6, abs=1e-8)


@pytest.mark.parametrize(
    "data",
    [b"", b"abc", b"a" * 55, b"a" * 56, b"a" * 64, bytes(range(256)) * 4096],
    ids=["empty", "abc", "padding55", "padding56", "block64", "oneMiB"],
)
def test_bounded_sha256_known_answers_and_multiblock_padding(lib, data):
    output = ct.create_string_buffer(32)
    assert lib.i1_sha256(data, len(data), output) == 0
    assert output.raw == hashlib.sha256(data).digest()


def test_parser_rejects_checkpoint_shape_offsets_duplicates_and_nonfinite_bits(lib):
    model = ContextCNN()
    payload = save(model.state_dict())
    length = int.from_bytes(payload[:8], "little")
    header = json.loads(payload[8 : 8 + length])
    values = payload[8 + length :]
    weights = np.empty(26433, dtype=np.float32)
    assert lib.i1_model_read(payload, len(payload), ptr(weights)) == 0
    bad_headers = []
    for field, value in (
        ("dtype", "F64"),
        ("shape", [16, 10, 3, 3, 3]),
        ("data_offsets", [-1, 5616 * 4 - 1]),
        ("data_offsets", [4, 5616 * 4 + 4]),
    ):
        changed = json.loads(json.dumps(header))
        changed["network.0.weight"][field] = value
        bad_headers.append(json.dumps(changed).encode())
    duplicate = json.dumps(header).encode().replace(b'"F32"', b'"F32", "dtype": "F32"', 1)
    bad_headers.append(duplicate)
    for bad_header in bad_headers:
        bad = len(bad_header).to_bytes(8, "little") + bad_header + values
        assert lib.i1_model_read(bad, len(bad), ptr(weights)) != 0
    bad = payload[: 8 + length] + b"\x00\x00\xc0\x7f" + values[4:]
    assert lib.i1_model_read(bad, len(bad), ptr(weights)) != 0


@pytest.mark.skipif(
    platform.system() != "Linux" or platform.machine() != "x86_64",
    reason="freestanding program requires the selected Linux x86-64 surface",
)
def test_linux_no_libc_programs_preflight_query_and_audit(tmp_path):
    build = tmp_path / "bin"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/i1_native_build.py"), str(build)], check=True
    )
    result = subprocess.run(
        [
            str(build / "i1-controller"),
            "--public-preflight",
            str(build / "i1-query"),
            str(build / "i1-audit"),
        ],
        env={},
        capture_output=True,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert result.stdout.count(b"MAPS_BEGIN") == 3
    assert b"PILOT=DENIED" in result.stdout
    manifest = json.loads((build / "build.json").read_text())
    hashes = [
        line.split(b"=", 1)[1].decode()
        for line in result.stdout.splitlines()
        if line.startswith(b"EXECUTABLE_SHA256=")
    ]
    assert hashes == [manifest["roles"][r]["sha256"] for r in ("controller", "query", "audit")]
    assert result.stdout.count(b"OBSERVED_THREADS=1") == 3
    assert result.stdout.count(b"ROLE_ENV_EMPTY=1") == 3
    assert result.stdout.count(b"DUMPABLE_AFTER_SETUP=0") == 3
    assert result.stdout.count(b"AUXV_SELECTED_BEGIN") == 3
    assert result.stdout.count(b"AUXV_ORIGIN=INITIAL_STACK") == 3
    assert result.stdout.count(b"LIMITS_BEGIN") == 3
    direct = subprocess.run(
        [
            str(build / "i1-controller"),
            "--ci-public-preflight",
            str(build / "i1-query"),
            str(build / "i1-audit"),
            "unused-script",
        ],
        env={"I1_PUBLIC_FIXTURE": "new public software only"},
        capture_output=True,
        check=True,
    )
    assert b"CI_INCOMING_ENV_ENTRIES=1" in direct.stdout
    assert b"new public software only" not in direct.stdout
    assert direct.stdout.count(b"ROLE_ENV_EMPTY=1") == 3
    request = tmp_path / "case.json"
    request.write_text(json.dumps(public_request()))
    output = subprocess.run(
        [str(build / "i1-query"), "--public-case", str(request), "unused"],
        env={},
        capture_output=True,
        check=True,
    )
    assert output.stdout.startswith(b"I1PUB003")
    record = tmp_path / "result.bin"
    record.write_bytes(output.stdout)
    wire = tmp_path / "case.bin"
    wire.write_bytes(bytes(spec()))
    checked = subprocess.run(
        [str(build / "i1-audit"), "--public-terminal", str(wire), str(record)],
        env={},
        capture_output=True,
        check=True,
    )
    assert b"PUBLIC_TERMINAL_CHECK=PASS" in checked.stdout
    malformed_polish = bytearray(output.stdout)
    small_history = History.from_buffer(malformed_polish, 8)
    small_history.polish_updates = 1
    small_history.polish_rechecks = 2
    small_history.analyses += 2
    bad_polish = tmp_path / "ineligible-small-polish.bin"
    bad_polish.write_bytes(malformed_polish)
    assert (
        subprocess.run(
            [str(build / "i1-audit"), "--public-terminal", str(wire), str(bad_polish)],
            env={},
            capture_output=True,
        ).returncode
        != 0
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/i1_native_inspect.py"), str(build)], check=True
    )
    large = spec((24, 12, 6))
    payload = public_request((24, 12, 6))
    payload.update(method="H", limit=17)
    request.write_text(json.dumps(payload))
    wire.write_bytes(bytes(large))
    model = ContextCNN()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.fill_(0.001)
    checkpoint = tmp_path / "public.safetensors"
    checkpoint.write_bytes(save(model.state_dict(), metadata={"topolab": "public fixture only"}))
    integrated = tmp_path / "integrated.bin"
    command = [
        str(build / "i1-controller"),
        "--public-run",
        str(build / "i1-query"),
        str(build / "i1-audit"),
        str(request),
        str(checkpoint),
        str(wire),
        str(integrated),
    ]
    result = subprocess.run(command, env={}, capture_output=True, check=True)
    assert b"PUBLIC_TERMINAL_CHECK=PASS" in result.stdout and b"PILOT=DENIED" in result.stdout
    history = History.from_buffer_copy(integrated.read_bytes()[8:])
    assert list(history.penalty[:18]) == [1] * 9 + [2] * 8 + [3]
    assert history.analyses == 21
    payload["method"] = "plainP"
    request.write_text(json.dumps(payload))
    plain = subprocess.run(
        [str(build / "i1-query"), "--public-case", str(request), str(checkpoint)],
        env={},
        capture_output=True,
        check=True,
    )
    plain_record = tmp_path / "public-plain.bin"
    plain_record.write_bytes(plain.stdout)
    subprocess.run(
        [str(build / "i1-audit"), "--public-terminal", str(wire), str(plain_record)],
        env={},
        capture_output=True,
        check=True,
    )
    malformed_polish = bytearray(plain.stdout)
    plain_history = History.from_buffer(malformed_polish, 8)
    assert not plain_history.converged and plain_history.updates == 17
    plain_history.polish_updates = 1
    plain_history.polish_rechecks = 2
    plain_history.analyses += 2
    bad_polish = tmp_path / "nonplateau-large-polish.bin"
    bad_polish.write_bytes(malformed_polish)
    assert (
        subprocess.run(
            [str(build / "i1-audit"), "--public-terminal", str(wire), str(bad_polish)],
            env={},
            capture_output=True,
        ).returncode
        != 0
    )
    payload["method"] = "H"
    request.write_text(json.dumps(payload))
    reference = tmp_path / "public-reference.bin"
    reference.write_bytes(struct.pack("<d", 1e30))
    evaluation = tmp_path / "public-evaluation.bin"
    evaluated = subprocess.run(
        [
            str(build / "i1-controller"),
            "--public-evaluate",
            str(build / "i1-query"),
            str(build / "i1-audit"),
            str(request),
            str(checkpoint),
            str(wire),
            str(reference),
            str(evaluation),
        ],
        env={},
        capture_output=True,
        check=True,
    )
    assert b"PUBLIC_EVALUATION_CHECK=PASS" in evaluated.stdout
    audit_counts = [
        int(line.split(b"=", 1)[1])
        for line in evaluated.stdout.splitlines()
        if line.startswith(b"PUBLIC_AUDIT_ANALYSES=")
    ]
    assert len(audit_counts) == 1 and audit_counts[0] <= 48
    bundle = evaluation.read_bytes()
    assert bundle[:8] == b"I1EVAL01"
    succeeded, fallback, attempt_status, status = struct.unpack_from("<4i", bundle, 8)
    assert (fallback, attempt_status, status) == (1, 4, 0)
    attempted = History.from_buffer_copy(bundle[24:])
    returned_offset = 24 + ct.sizeof(History)
    assert bundle[returned_offset : returned_offset + 8] == b"I1PUB003"
    returned = History.from_buffer_copy(bundle[returned_offset + 8 :])
    assert attempted.penalty[0] == 1 and attempted.analyses == 21
    assert returned.penalty[0] == 3 and returned.initial_analyses == 0
    assert succeeded == returned.converged
    # Independent parser/classifier must not erase the failed attempt flag.
    tampered_bundle = bytearray(bundle)
    struct.pack_into("<i", tampered_bundle, 16, 0)
    tampered_evaluation = tmp_path / "tampered-evaluation.bin"
    tampered_evaluation.write_bytes(tampered_bundle)
    rejected_attempt = subprocess.run(
        [
            str(build / "i1-audit"),
            "--public-evaluation",
            str(wire),
            str(tampered_evaluation),
            str(reference),
        ],
        env={},
        capture_output=True,
    )
    assert rejected_attempt.returncode != 0
    repeated = subprocess.run(command, env={}, capture_output=True)
    assert repeated.returncode == 73
    corrupted = tmp_path / "corrupted-query"
    corrupted.write_bytes((build / "i1-query").read_bytes() + b"changed")
    corrupted.chmod(0o700)
    rejected_origin = subprocess.run(
        [
            str(build / "i1-controller"),
            "--public-preflight",
            str(corrupted),
            str(build / "i1-audit"),
        ],
        env={},
        capture_output=True,
    )
    assert rejected_origin.returncode == 65
    small = spec()
    request.write_text(json.dumps(public_request()))
    wire.write_bytes(bytes(small))
    nn_input = encode_case(ExperimentCase.from_problem(problem(small))).input_tensor
    training_view = tmp_path / "new-public-nn.bin"
    training_view.write_bytes(
        b"I1NN0001"
        + struct.pack("<II", 1, 6)
        + b"tlcase-v1-"
        + b"0" * 64
        + b"\0"
        + nn_input.astype("<f4").tobytes()
        + np.full(6, 0.4, dtype="<f4").tobytes()
    )
    for method, data_file in (("NN", training_view), ("physics", checkpoint)):
        payload = public_request()
        payload["method"] = method
        request.write_text(json.dumps(payload))
        target = tmp_path / f"public-{method}.bin"
        check = subprocess.run(
            [
                str(build / "i1-controller"),
                "--public-run",
                str(build / "i1-query"),
                str(build / "i1-audit"),
                str(request),
                str(data_file),
                str(wire),
                str(target),
            ],
            env={},
            capture_output=True,
            check=True,
        )
        assert b"PUBLIC_TERMINAL_CHECK=PASS" in check.stdout
        if method == "NN":
            assert b"PUBLIC_NN_MATCH=tlcase-v1-" + b"0" * 64 in check.stderr
    accepted_request = public_request()
    accepted_request.update(method="uniform", limit=360)
    request.write_text(json.dumps(accepted_request))
    accepted_target = tmp_path / "public-accepted-evaluation.bin"
    accepted = subprocess.run(
        [
            str(build / "i1-controller"),
            "--public-evaluate",
            str(build / "i1-query"),
            str(build / "i1-audit"),
            str(request),
            "unused",
            str(wire),
            str(reference),
            str(accepted_target),
        ],
        env={},
        capture_output=True,
        check=True,
    )
    assert struct.unpack_from("<4i", accepted_target.read_bytes(), 8) == (1, 0, 0, 0)
    audit_counts = [
        int(line.split(b"=", 1)[1])
        for line in accepted.stdout.splitlines()
        if line.startswith(b"PUBLIC_AUDIT_ANALYSES=")
    ]
    assert len(audit_counts) == 1 and audit_counts[0] <= 12
    # A finite, correctly described checkpoint may fail numerically at inference.
    # That is a retained failed attempt with fresh fallback, not malformed bytes.
    overflow_spec = spec((12, 6, 3))
    overflow_request = public_request((12, 6, 3))
    overflow_request["method"] = "plainP"
    request.write_text(json.dumps(overflow_request))
    wire.write_bytes(bytes(overflow_spec))
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.fill_(torch.finfo(torch.float32).max)
    checkpoint.write_bytes(save(model.state_dict()))
    target = tmp_path / "public-inference-failure.bin"
    overflow = subprocess.run(
        [
            str(build / "i1-controller"),
            "--public-evaluate",
            str(build / "i1-query"),
            str(build / "i1-audit"),
            str(request),
            str(checkpoint),
            str(wire),
            str(reference),
            str(target),
        ],
        env={},
        capture_output=True,
        check=True,
    )
    assert b"PUBLIC_INITIALIZATION_FAILURE=PREDICT\n" in overflow.stderr
    assert b"PUBLIC_EVALUATION_CHECK=PASS" in overflow.stdout
    bundle = target.read_bytes()
    assert struct.unpack_from("<4i", bundle, 8)[1:] == (1, 1, 0)
    assert History.from_buffer_copy(bundle[24:]).analyses == 0
    fallback_history = History.from_buffer_copy(bundle[24 + ct.sizeof(History) + 8 :])
    assert fallback_history.analyses == fallback_history.updates + 2
    # A valid public case with overflowing external work retains both the failed
    # initializer analysis and the fresh fallback's failed initial analysis.
    payload = public_request()
    payload.update(method="physics", magnitude=struct.pack(">d", 1e308).hex())
    request.write_text(json.dumps(payload))
    failed_initialization = subprocess.run(
        [str(build / "i1-query"), "--public-evaluate", str(request), "unused", str(reference)],
        env={},
        capture_output=True,
    )
    assert failed_initialization.returncode == 66
    assert b"PUBLIC_INITIALIZATION_FAILURE=PHYSICS\n" in failed_initialization.stderr
    prefix = failed_initialization.stdout
    assert struct.unpack_from("<4i", prefix, 8) == (0, 1, 1, 2)
    assert History.from_buffer_copy(prefix[24:]).analyses == 1
    failure_offset = 24 + ct.sizeof(History)
    assert prefix[failure_offset : failure_offset + 8] == b"I1FAIL01"
    assert History.from_buffer_copy(prefix[failure_offset + 8 :]).analyses == 1
    rejected = subprocess.run(
        [str(build / "i1-query"), "--pilot", str(request), "unused"], env={}, capture_output=True
    )
    assert rejected.returncode == 64
