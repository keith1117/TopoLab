"""Stage-A public software entry; no scientific/input discovery mode exists.

Example: uv run python scripts/p17_m2_homotopy.py --public-fixture tiny-prefix
         --output /new/external/software-only/result.json
Formal preflight/scientific execution require separately authorized future code.
"""

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from time import perf_counter

VERSION = "topolab.v2.p17-m2-native-homotopy.stage-a.v1"
SEEDS = (17, 29, 43)
METHODS = (
    "uniform",
    "physics_heuristic",
    "nearest_neighbor",
    *(f"{name}/{seed}" for name in ("C", "P-keep", "W", "P", "H") for seed in SEEDS),
    "uniform-homotopy",
)
REPO = Path(__file__).resolve().parents[1]
PUBLIC_FIXTURE = REPO / "tests/fixtures/p17_m2_public_case.json"
PUBLIC_FIXTURE_BYTES = 638
PUBLIC_FIXTURE_SHA256 = "c6fdfdd46f722f3dad8910ec0941ed1adfbc4009d8f65ffacbab19a2bfe63b9a"


def atomic_new(path, value):
    """Publish complete bytes without replacing a prior attempt or symlink."""
    data = (json.dumps(value, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".pending-{os.getpid()}")
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def read_public_manifest(path, expected_sha256, *, expected_bytes, maximum_bytes=65536):
    """Exact registered new fixture only; no roots, globs or embedded paths.

    This is deliberately not a loader for an unregistered future C view.
    Validate the byte limit and path class before opening any payload.
    """
    if (
        Path(path).absolute() != PUBLIC_FIXTURE
        or Path(path).is_symlink()
        or type(expected_bytes) is not int
        or not 0 < expected_bytes <= maximum_bytes <= 65536
        or expected_sha256 != PUBLIC_FIXTURE_SHA256
        or expected_bytes != PUBLIC_FIXTURE_BYTES
    ):
        raise PermissionError("only the registered new public fixture is readable in A")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as stream:
        raw = stream.read(expected_bytes + 1)
    if len(raw) != expected_bytes or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("public fixture identity differs")
    value = json.loads(raw)
    if (
        set(value) != {"schema", "purpose", "problem"}
        or value["schema"] != ("topolab.v2.m2-new-public-fixture.v1")
        or value["purpose"] != "new authored software fixture; no historical input"
    ):
        raise ValueError("unregistered public fixture schema")
    from topolab.experiment import ExperimentCase
    from topolab.problem import TopologyProblem

    case = ExperimentCase.from_problem(TopologyProblem.model_validate(value["problem"]))
    if case.problem.mesh.element_counts != (3, 2, 1):
        raise ValueError("public fixture shape changed")
    return case


def public_assets(case, specification):
    """Load an exact NEW public in-memory model/NN manifest, with no paths.

    This A-only schema cannot masquerade as the future source-attested 528-label
    export or any historical checkpoint. No old label parser/index is involved.
    """
    import numpy as np
    import torch

    from topolab.b2_12_context_cnn import ContextCNN
    from topolab.baselines import NearestNeighborIndex
    from topolab.experiment import encode_case

    expected = {
        "schema": "topolab.v2.m2-new-public-assets.v1",
        "case_id": case.case_id,
        "model_roles": [f"{family}/{seed}" for family in ("C", "P", "W", "S") for seed in SEEDS],
        "weight_source": "new ContextCNN initialization; not historical weights",
        "neighbor_source": "new constant public field; not a label or historical terminal",
    }
    if specification != expected:
        raise PermissionError("only the exact new public asset manifest is allowed in A")
    models, identities = {}, {}
    with torch.random.fork_rng(devices=[]):
        for family in ("C", "P", "W", "S"):
            for seed in SEEDS:
                torch.manual_seed(seed)
                model = ContextCNN().cpu().eval()
                models[(family, seed)] = model
                identities[f"{family}/{seed}"] = hashlib.sha256(
                    b"".join(p.detach().numpy().tobytes() for p in model.parameters())
                ).hexdigest()
    nx, ny, nz = case.problem.mesh.element_counts
    neighbors = NearestNeighborIndex(
        case_ids=(case.case_id,),
        input_tensors=encode_case(case).input_tensor[np.newaxis],
        design_tensors=np.full(
            (1, 1, nz, ny, nx), case.problem.optimization.volume_fraction, dtype=np.float32
        ),
    )
    return models, neighbors, identities


def public_asset_specification(case):
    return {
        "schema": "topolab.v2.m2-new-public-assets.v1",
        "case_id": case.case_id,
        "model_roles": [f"{family}/{seed}" for family in ("C", "P", "W", "S") for seed in SEEDS],
        "weight_source": "new ContextCNN initialization; not historical weights",
        "neighbor_source": "new constant public field; not a label or historical terminal",
    }


def _selected(case, method, models):
    from topolab.b3_queries import policy_route

    route = policy_route(case, "P")
    name, seed = method.split("/")
    seed = int(seed)
    recipe = "S" if route == "specialist" else ("P" if name in ("H", "P-keep") else name)
    return route, recipe, seed, None if route == "reject" else models[(recipe, seed)]


def evaluate_query(case, method, reference, models, neighbors, checkpoint):
    """Nineteen fixed query policies; models/NN must already be authorized views.

    A callers supply original new public weights only. No filesystem loader is
    called from this function. Future scientific byte/role tables are NOT granted.
    """
    import numpy as np
    import torch

    from topolab.b2_5_evaluation import _predict, _raw_uniform
    from topolab.b2_9_vector_load import encode_vector_load_case
    from topolab.b3_queries import QueryResourceExceeded, TerminalWitness
    from topolab.b4_polish import polish
    from topolab.b4_terminal_preservation import select_terminal
    from topolab.baselines import _physics_heuristic_raw_density, validate_refinement_quality
    from topolab.experiment import project_design_density
    from topolab.p17_m2_homotopy import h_active, quality, solve_phases
    from topolab.problem import TopologyProblem, solve_problem

    if method not in METHODS:
        raise ValueError("method is outside the fixed19")
    if (
        case.problem.optimization.max_iterations != 360
        or case.problem.optimization.penalty != 3
        or case.problem.optimization.convergence_tolerance != 0.01
    ):
        raise ValueError("query differs from the fixed p3/.01/360 contract")
    if reference is not None and (not math.isfinite(reference) or reference <= 0):
        raise ValueError("reference must be finite positive")
    checkpoint()
    started = perf_counter()
    route, recipe, seed, model = "baseline", None, None, None
    if "/" in method:
        route, recipe, seed, model = _selected(case, method, models)
    active = h_active(case, route if method.startswith("H/") else "generalist") and (
        method.startswith("H/") or method == "uniform-homotopy"
    )

    def attempt(selected):
        phase = "setup_error"
        phase_witness, legacy_witness, matched, continuation = None, None, None, None
        before = perf_counter()
        try:
            checkpoint()
            if selected == "uniform":
                raw = _raw_uniform(case)
            elif selected == "physics_heuristic":
                raw = _physics_heuristic_raw_density(case)
            elif selected == "nearest_neighbor":
                if neighbors is None:
                    raise ValueError("registered train-only NN view missing")
                match = neighbors.query(case)
                raw, matched = match.design_density, match.case_id
            else:
                if model is None:
                    raise ValueError("registered selected model missing")
                raw = _predict(case, model, encoder=encode_vector_load_case)
            phase = "projection_error"
            checkpoint()
            projected = project_design_density(case, raw)
            phase = "refinement_error"
            payload = case.problem.model_dump(mode="json")
            payload["initial_density"] = projected.design_density.tolist()
            if active and selected != "uniform":
                phase_witness = solve_phases(
                    case,
                    projected.design_density,
                    active=True,
                    checkpoint=checkpoint,
                )
                result = phase_witness.result
                succeeded = quality(
                    phase_witness, reference, case.problem.optimization.volume_fraction
                )
            else:
                result = solve_problem(
                    TopologyProblem.model_validate(payload),
                    termination_policy="physical_plateau",
                    iteration_callback=lambda _: checkpoint(),
                )
                if selected.startswith("P-keep/") and route == "generalist":
                    after = polish(case, result, checkpoint)
                    choice = select_terminal(case, result, after)
                    continuation = {
                        "before": result.model_dump(mode="json"),
                        "after": after.model_dump(mode="json"),
                        "choice": choice,
                    }
                    if choice != "original":
                        result = after
                phase = "quality_error"
                # Preserve a failed control's own finite terminal/trajectory
                # before quality classification can reject it. Fallback never
                # erases the failed attempt's witness or its charged work.
                legacy_witness = TerminalWitness.from_result(result).model_dump(mode="json")
                validate_refinement_quality(case, result, reference)
                succeeded = True
            checkpoint()
            return {
                "succeeded": succeeded,
                "failure_code": None if succeeded else "quality_error",
                "failure_type": None if succeeded else "QualityRejected",
                "phase_witness": None
                if phase_witness is None
                else phase_witness.model_dump(mode="json"),
                "legacy_witness": legacy_witness,
                "matched_case_id": matched,
                "continuation": continuation,
                "wall_seconds": perf_counter() - before,
            }
        except (MemoryError, torch.OutOfMemoryError, QueryResourceExceeded, TimeoutError):
            raise  # Resource STOP must never turn into an ordinary uniform fallback.
        except (ValueError, RuntimeError, ArithmeticError) as error:
            return {
                "succeeded": False,
                "failure_code": phase,
                "failure_type": type(error).__name__,
                "phase_witness": None
                if phase_witness is None
                else phase_witness.model_dump(mode="json"),
                "legacy_witness": legacy_witness,
                "matched_case_id": matched,
                "continuation": continuation,
                "wall_seconds": perf_counter() - before,
            }

    # uniform-homotopy starts uniform but still runs the active fixed schedule.
    if method == "uniform-homotopy" and active:

        class UniformModel(torch.nn.Module):
            def forward(self, inputs):
                return torch.full_like(inputs[:, :1], case.problem.optimization.volume_fraction)

        model = UniformModel()
    selected = "uniform" if method == "uniform-homotopy" and not active else method
    first = None if route == "reject" else attempt(selected)
    fallback = None
    if route == "reject" or first is not None and not first["succeeded"] and selected != "uniform":
        fallback = attempt("uniform")
        if fallback["succeeded"] and reference is not None:
            got = fallback["legacy_witness"]["result"]["compliance"]
            if not np.isclose(got, reference, rtol=1e-9, atol=0):
                fallback.update(
                    succeeded=False,
                    failure_code="quality_error",
                    failure_type="UniformReferenceMismatch",
                )
    checkpoint()
    elapsed = perf_counter() - started
    return {
        "schema": "topolab.v2.m2-native-query.v1",
        "software_only": True,
        "method": method,
        "seed": seed,
        "route": route,
        "selected_recipe": recipe,
        "homotopy_active": active,
        "attempt": first,
        "fallback": fallback,
        "wall_seconds": elapsed,
        "charged_seconds": elapsed + 1,
        "recording_allowance_seconds": 1,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-fixture", required=True, choices=("tiny-prefix", "tiny-plain"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)  # Unknown scientific/root/preflight options reject before reads.
    output = args.output.absolute()
    if output == REPO or REPO in output.parents or output.exists() or output.is_symlink():
        parser.error("new external software-only output required")
    # Read the new public fixture at its literal identity, never an old root.
    case = read_public_manifest(
        PUBLIC_FIXTURE, PUBLIC_FIXTURE_SHA256, expected_bytes=PUBLIC_FIXTURE_BYTES
    )
    import numpy as np
    import torch

    from topolab.b2_5_evaluation import _predict
    from topolab.b2_9_vector_load import encode_vector_load_case
    from topolab.b2_12_context_cnn import ContextCNN
    from topolab.experiment import project_design_density
    from topolab.p17_m2_homotopy import solve_phases

    torch.set_num_threads(1)
    torch.set_num_interop_threads(8)
    torch.manual_seed(17)
    model = ContextCNN().cpu().eval()  # NEW public initialization, never old fixed P/17 bits.
    prediction = _predict(case, model, encoder=encode_vector_load_case)
    initial = project_design_density(case, prediction).design_density
    started = perf_counter()
    witness = solve_phases(
        case, initial, active=args.public_fixture == "tiny-prefix", checkpoint=lambda: None
    )
    payload = {
        "schema": VERSION,
        "status": "PUBLIC_SOFTWARE_ONLY_NOT_B_OR_C",
        "fixture": args.public_fixture,
        "case": case.model_dump(mode="json"),
        "new_weight_identity": hashlib.sha256(
            b"".join(p.detach().numpy().tobytes() for p in model.parameters())
        ).hexdigest(),
        "historical_model": False,
        "old_input_read_set": [],
        "formal_attempts": 0,
        "methods": METHODS,
        "witness": witness.model_dump(mode="json"),
        "wall_seconds": perf_counter() - started,
        "runtime": {
            "python": sys.executable,
            "numpy_origin": np.__file__,
            "torch_origin": torch.__file__,
            "cwd": str(Path.cwd()),
            "lock_sha256": hashlib.sha256((REPO / "uv.lock").read_bytes()).hexdigest(),
            "threads": {
                "torch_intraop": torch.get_num_threads(),
                "torch_interop": torch.get_num_interop_threads(),
            },
        },
    }
    atomic_new(output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
