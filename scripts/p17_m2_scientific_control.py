"""Fixed M2 scientific orchestration over checked local buffers and owned solvers.

This module performs no discovery and imports no numerical code at startup. A
call table is metadata, never a scientific/input/resource execution capability.
Native pending/start/exit and the distinct auditor remain external authorities.
"""

import hashlib
import importlib.util
import json
import math
import re
import struct
import sys
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from time import perf_counter

REPO = Path(__file__).resolve().parents[1]
IDENTITY = "topolab.v2.p17-m2-native-homotopy.rss.v1"
SEEDS = (17, 29, 43)
METHODS = (
    "uniform",
    "physics_heuristic",
    "nearest_neighbor",
    *(f"{family}/{seed}" for family in ("C", "P-keep", "W", "plain-P", "H") for seed in SEEDS),
    "uniform-homotopy",
)


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def load(name):
    path = Path(__file__).with_name(name + ".py")
    existing = sys.modules.get(name)
    if existing is not None and Path(existing.__file__).resolve() == path.resolve():
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec and spec.loader, "frozen scientific helper missing")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_call_plan(proposal):
    """Close every fixed prospective producer call; no original or target IO."""
    pilot = proposal["prospective_pilot"]
    ids = pilot["case_ids"]
    need(
        isinstance(ids, list) and len(ids) == 18 and ids == sorted(set(ids)),
        "exact sorted18 case IDs required",
    )
    need(
        pilot["methods"] == list(METHODS)
        and pilot["new_references"] == 18
        and pilot["new_queries"] == 342
        and pilot["producer_FEM_analyses_max"] == 254808
        and pilot["independent_FEM_analyses_max"] == 19056,
        "fixed scientific population or cap differs",
    )
    partitions = {
        "terminal_and_windows": 16632,
        "homotopy_prefix_and_transitions": 1368,
        "NN_label_input_reanalysis": 1056,
    }
    need(
        pilot["independent_analysis_partition"] == partitions,
        "untransferable independent partitions differ",
    )
    references = [
        {"ordinal": i, "case_id": case_id, "method": "uniform", "fem_max": 362, "projection_max": 1}
        for i, case_id in enumerate(ids, 1)
    ]
    queries = []
    for case_id in ids:
        for method in METHODS:
            queries.append(
                {
                    "ordinal": len(queries) + 1,
                    "case_id": case_id,
                    "method": method,
                    "fem_max": 362 if method == "uniform" else 726,
                    "projection_max": 1 if method == "uniform" else 2,
                    "prediction_max": int("/" in method or method == "uniform-homotopy"),
                    "NN_query_max": int(method == "nearest_neighbor"),
                }
            )
    return {
        "schema": "topolab.v2.m2-fixed-scientific-call-plan.v1",
        "execution_identity": IDENTITY,
        "case_definitions_sha256": pilot["case_definitions_sha256"],
        "references": references,
        "queries": queries,
        "producer_FEM_max": 254808,
        "independent_partitions": partitions,
        "input_reads_per_role": {
            "scientific-producer": 542,
            "scientific-auditor": 1070,
            "reference-compatibility": 1,
        },
        "input_role_view_union": (
            "producer541/auditor1069 plus uniform scalar1 under one actual role lease"
        ),
        "NN_train_counts_per_scale": {"12,6,3": 432, "24,12,6": 96},
        "checkpoint_count": 12,
        "FEM_derivation": {
            "plain_with_quality": "initial1 + updates<=360 + quality1 =362",
            "P_keep_with_quality": (
                "main+polish updates<=360 + initial1 + polish_recheck1 + quality1 <=363"
            ),
            "H_with_terminal": "initial1 + transitions2 + updates<=360 + terminal1 <=364",
            "fallback": "plain uniform<=362; never erases attempted work",
            "all_query_bound": "max(363+362,364+362)=726",
            "fixed_whole_ceiling": "342*726+18*362=254808",
        },
        "formal_or_resource_admission": False,
    }


def decode_checkpoint(raw, item):
    """Decode the checked buffer once; Safetensors never receives a path."""
    import torch
    from safetensors.torch import load as decode

    from topolab.b2_12_context_cnn import ContextCNN

    exporter = load("p17_m2_input_export")
    contract = exporter.parse(
        (REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json").read_bytes()
    )
    exporter.check_weights(raw, item, contract)
    tensors = decode(raw)
    # Initialization supplies the fixed architecture only; every parameter is
    # overwritten under strict loading, with no global RNG side effect.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(0)
        model = ContextCNN()
    need(
        set(tensors) == set(model.state_dict())
        and all(
            t.dtype == torch.float32 and t.device.type == "cpu" and bool(torch.isfinite(t).all())
            for t in tensors.values()
        ),
        "fixed finite CPU F32 checkpoint required",
    )
    model.load_state_dict(tensors, strict=True)
    model.eval()
    return model


def decode_nn_producer(raw, expected_case_id):
    """Re-encode the train case; keep its original stored F32 design bits."""
    import numpy as np

    from topolab.experiment import ExperimentCase, encode_case

    packet = load("p17_m2_input_export").parse(raw)
    need(
        set(packet)
        == {"schema", "case", "membership", "initialization", "source", "stored", "bit_digests"}
        and packet["schema"] == "topolab.v2.m2-nn-producer-view.v1"
        and packet["membership"].get("role") == "train",
        "train-only NN view required",
    )
    case = ExperimentCase.model_validate(packet["case"])
    need(case.case_id == expected_case_id, "NN source-attested case identity differs")
    nx, ny, nz = case.problem.mesh.element_counts
    stored = packet["stored"]
    need(
        set(stored) == {"tensor_dtype", "tensor_axis_order", "tensor_shape", "design_density"}
        and stored["tensor_dtype"] == "float32"
        and stored["tensor_axis_order"] == "channel,z,y,x"
        and stored["tensor_shape"] == [1, nz, ny, nx],
        "NN stored tensor schema differs",
    )
    values = np.asarray(stored["design_density"], dtype=np.float64)
    design = np.asarray(stored["design_density"], dtype=np.float32)
    need(
        values.shape == design.shape == (nx * ny * nz,)
        and bool(np.all(np.isfinite(values)))
        and bool(np.all((values >= 0) & (values <= 1)))
        and bool(np.array_equal(values, design.astype(np.float64)))
        and packet["bit_digests"]
        == {"/stored/design_density": hashlib.sha256(design.astype("<f4").tobytes()).hexdigest()},
        "NN stored F32 words differ",
    )
    return case, encode_case(case).input_tensor, design.reshape(1, nz, ny, nx)


def parameter_digest(model):
    """Bind every sorted CPU F32 parameter word without reopening a checkpoint."""
    state = model.state_dict()
    result = hashlib.sha256()
    for name in sorted(state):
        tensor = state[name].detach().cpu().contiguous()
        result.update(
            canonical({"name": name, "shape": list(tensor.shape), "dtype": str(tensor.dtype)})
        )
        result.update(tensor.numpy().astype("<f4").tobytes())
    return result.hexdigest()


def _scientific_binding(consumer, contract_sha256, *, public_fixture_only=False):
    verified = load("p17_m2_source_verified_input")
    need(
        isinstance(consumer, verified.VerifiedAcquisitionInput),
        "actual opaque scientific consumer required",
    )
    need(
        type(public_fixture_only) is bool and re.fullmatch(r"[0-9a-f]{64}", contract_sha256),
        "frozen scientific contract identity required",
    )
    binding = consumer.certificate.binding_for(consumer.role, reader_lease=consumer.lease)
    need(
        binding.get("scientific_execution_identity") == IDENTITY
        and binding.get("scientific_contract_sha256") == contract_sha256
        and binding.get("scientific_public_fixture_only") is public_fixture_only
        and (
            binding["scope"] == "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
            if public_fixture_only
            else binding["scope"] == "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
        ),
        "separate scientific scope/grant required",
    )
    return binding


_ASSET_AUTHORITY = object()


class ScientificAssets:
    def __init__(self, models, neighbors, identities, metadata, *, _authority=None):
        need(_authority is _ASSET_AUTHORITY, "assets require checked scientific buffers")
        self.models, self.neighbors, self.identities, self.metadata = (
            models,
            neighbors,
            identities,
            metadata,
        )
        self.row_buffers, self.model_rows, self.nn_rows = {}, {}, {}
        self.row_setup_counts = dict.fromkeys(
            ("checkpoint_decodes", "NN_case_reencodes", "NN_index_builds", "buffer_rehashes"), 0
        )

    def load_for_row(self, case, method):
        """Rehash/decode selected immutable admitted buffers inside row timing."""
        from topolab.b3_queries import policy_route

        scale = tuple(case.problem.mesh.element_counts)
        started = perf_counter()
        facts = dict.fromkeys(self.row_setup_counts, 0)
        facts.update(source_file_rereads=0, selected_buffers=[])
        models, neighbors = {}, None
        if self.metadata.get("new_public_assets") is not None:
            # The tiny dispatch-only fixture has deliberately synthetic assets.
            facts["public_synthetic_assets_only"] = True
            return self.models, self.neighbors.get(scale), facts

        def raw_buffer(name, expected):
            raw = self.row_buffers[name]
            need(
                type(raw) is bytes and hashlib.sha256(raw).hexdigest() == expected,
                "verified query buffer hash changed",
            )
            self.row_setup_counts["buffer_rehashes"] += 1
            facts["buffer_rehashes"] += 1
            facts["selected_buffers"].append({"path": name, "sha256": expected})
            return raw

        if "/" in method and policy_route(case, "P") != "reject":
            family, seed = method.split("/")
            family = (
                "S"
                if policy_route(case, "P") == "specialist"
                else "P"
                if family in ("plain-P", "P-keep", "H")
                else family
            )
            key = family, int(seed)
            item = self.model_rows[key]
            need(
                parameter_digest(self.models[key]) == self.identities[key]["parameter_sha256"],
                "cached fixed model parameter words changed",
            )
            need(
                self.row_setup_counts["checkpoint_decodes"] < 270,
                "query checkpoint decode cap exhausted",
            )
            self.row_setup_counts["checkpoint_decodes"] += 1
            facts["checkpoint_decodes"] = 1
            raw = raw_buffer(item["output"]["path"], item["output"]["sha256"])
            models[key] = decode_checkpoint(raw, item)
            need(
                parameter_digest(models[key]) == self.identities[key]["parameter_sha256"],
                "reloaded fixed model parameter words changed",
            )
        elif method == "nearest_neighbor":
            import numpy as np

            from topolab.baselines import NearestNeighborIndex

            need(
                self.row_setup_counts["NN_index_builds"] < 18, "query NN index build cap exhausted"
            )
            self.row_setup_counts["NN_index_builds"] += 1
            facts["NN_index_builds"] = 1
            rows = []
            for name, expected in self.nn_rows[scale]:
                need(
                    self.row_setup_counts["NN_case_reencodes"] < 2736,
                    "query NN case encode cap exhausted",
                )
                self.row_setup_counts["NN_case_reencodes"] += 1
                facts["NN_case_reencodes"] += 1
                raw = raw_buffer(name, expected)
                case, inputs, design = decode_nn_producer(raw, Path(name).stem)
                rows.append((case.case_id, inputs, design))
            neighbors = NearestNeighborIndex(
                case_ids=tuple(row[0] for row in rows),
                input_tensors=np.stack([row[1] for row in rows]),
                design_tensors=np.stack([row[2] for row in rows]),
            )
        facts["wall_seconds"] = perf_counter() - started
        return models, neighbors, facts


def load_assets(consumer, contract_sha256, *, public_fixture_only=False):
    """Consume only12 checkpoints/models/528 producer views, each once."""
    binding = _scientific_binding(
        consumer, contract_sha256, public_fixture_only=public_fixture_only
    )
    need(
        consumer.role == "scientific-producer"
        and binding["scientific_permissions"].get("producer") is True,
        "producer scientific role required",
    )
    import numpy as np

    from topolab.baselines import NearestNeighborIndex

    member_rows = {row["path"]: row for row in binding["manifest"]["members"]}
    view = list(binding["role_views"][consumer.role])
    expected_models = {(family, seed) for family in ("C", "P", "W", "S") for seed in SEEDS}
    exporter = load("p17_m2_input_export")
    content_path = REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json"
    content_contract = exporter.parse(content_path.read_bytes())
    fixed_epochs = {
        (r["family"], r["seed"]): r["selected_epoch"]
        for r in content_contract["checkpoints"]["fixed_rows"]
    }

    def model_manifest(raw):
        value = exporter.parse(raw)
        need(
            set(value) == {"schema", "models"}
            and value["schema"] == "topolab.v2.m2-checkpoint-view.v1"
            and len(value["models"]) == 12,
            "exact12 source-attested models required",
        )
        rows = value["models"]
        need(
            {(r["family"], r["seed"]) for r in rows} == expected_models,
            "fixed model families/seeds differ",
        )
        for row in rows:
            key = (row["family"], row["seed"])
            name = f"checkpoints/{key[0]}-{key[1]}.safetensors"
            need(
                row["epoch"] == fixed_epochs[key]
                and row["output"]["path"] == name
                and name in view
                and member_rows[name]["type"] == "checkpoint"
                and all(
                    row["output"][k] == member_rows[name][k]
                    for k in ("path", "byte_size", "sha256")
                ),
                "fixed checkpoint epoch/output provenance differs",
            )
        return rows

    rows = consumer.consume("models.json", model_manifest)
    models, identities, buffers = {}, {}, {}

    def retain(name, decoder):
        def same_buffer(raw):
            result = decoder(raw)
            buffers[name] = raw
            return result

        return consumer.consume(name, same_buffer)

    for item in rows:
        key = (item["family"], item["seed"])
        model = retain(item["output"]["path"], lambda raw, item=item: decode_checkpoint(raw, item))
        models[key] = model
        identities[key] = {
            "family": key[0],
            "seed": key[1],
            "epoch": item["epoch"],
            "context_sha256": item["context_sha256"],
            "checkpoint_sha256": item["output"]["sha256"],
            "parameter_sha256": parameter_digest(model),
        }
    label_paths = sorted(name for name in view if name.startswith("nn/producer/"))
    need(
        len(label_paths) == 528
        and len(view) == 542
        and set(view)
        == {
            "models.json",
            "uniform-scalars.json",
            *(r["output"]["path"] for r in rows),
            *label_paths,
        },
        "exact scientific producer542 union required",
    )
    grouped, nn_rows = {}, {}
    for name in label_paths:
        expected_id = Path(name).stem
        case, inputs, design = retain(
            name, lambda raw, expected_id=expected_id: decode_nn_producer(raw, expected_id)
        )
        scale = tuple(case.problem.mesh.element_counts)
        need(scale in ((12, 6, 3), (24, 12, 6)), "NN scale outside frozen two scales")
        grouped.setdefault(scale, []).append((case.case_id, inputs, design))
        nn_rows.setdefault(scale, []).append((name, member_rows[name]["sha256"]))
    neighbors = {}
    for scale, count in (((12, 6, 3), 432), ((24, 12, 6), 96)):
        population = grouped.get(scale, [])
        ids = tuple(r[0] for r in population)
        need(
            len(population) == count and ids == tuple(sorted(set(ids))),
            "exact per-scale train-only NN population required",
        )
        neighbors[scale] = NearestNeighborIndex(
            case_ids=ids,
            input_tensors=np.stack([r[1] for r in population]),
            design_tensors=np.stack([r[2] for r in population]),
        )
    result = ScientificAssets(
        models,
        neighbors,
        identities,
        {
            "contract_sha256": contract_sha256,
            "version_id": binding["version_id"],
            "public_fixture_only": public_fixture_only,
            "member_reads": 541,
            "checkpoint_decodes": 12,
            "NN_case_reencodes": 528,
            "FEM_analyses": 0,
        },
        _authority=_ASSET_AUTHORITY,
    )
    result.row_buffers, result.model_rows, result.nn_rows = (
        buffers,
        {(item["family"], item["seed"]): item for item in rows},
        nn_rows,
    )
    return result


def load_references(consumer, contract_sha256, case_ids, *, public_fixture_only=False):
    """Read old scalar comparisons once; they never become timed denominators."""
    binding = _scientific_binding(
        consumer, contract_sha256, public_fixture_only=public_fixture_only
    )
    need(
        binding["scientific_permissions"].get("reference_compatibility") is True
        and "uniform-scalars.json" in binding["role_views"][consumer.role],
        "reference compatibility grant required",
    )

    def decode(raw):
        value = load("p17_m2_input_export").parse(raw)
        need(
            set(value) == {"schema", "values"}
            and value["schema"] == "topolab.v2.m2-uniform-scalar-view.v1"
            and len(value["values"]) == len(case_ids) == 18,
            "exact18 scalar comparison view required",
        )
        rows = value["values"]
        need(
            len({r["case_id"] for r in rows}) == 18
            and {r["case_id"] for r in rows} == set(case_ids),
            "uniform scalar cases differ",
        )
        for row in rows:
            compliance = row["compliance"]
            need(
                type(compliance) in (float, int)
                and math.isfinite(compliance)
                and compliance > 0
                and row["compliance_bits_sha256"]
                == hashlib.sha256(struct.pack("<d", compliance)).hexdigest(),
                "uniform scalar words differ",
            )
        return {r["case_id"]: r["compliance"] for r in rows}

    return consumer.consume("uniform-scalars.json", decode)


class MeasuredQueries:
    """Count actual owned numerical calls; no numerical return value is changed.

    The context is process-local and sequential. All aliases used by the frozen
    query driver are replaced together and restored even on a resource STOP.
    No measured call/failed attempt is removed when uniform fallback occurs.
    """

    def __init__(self, models, neighbors, *, checkpoint, fem_cap=254808, model_identities=None):
        need(type(fem_cap) is int and 0 <= fem_cap <= 254808, "finite FEM cap required")
        self.models, self.neighbors, self.checkpoint = models, neighbors, checkpoint
        self.fem_cap = fem_cap
        self.totals = dict.fromkeys(
            ("FEM", "predictions", "projections", "NN_queries", "OC_updates", "checkpoints"), 0
        )
        self.events, self.rows, self.failure = [], [], None
        self._current, self._row_counts = None, None
        self.model_identities = model_identities or {}
        self._initializations, self._NN_matches = [], []

    def _event(self, name, function, *args, **kwargs):
        from topolab.b3_queries import QueryResourceExceeded

        row = self._current
        need(row is not None, "numerical operation outside registered row")
        limits = {
            "FEM": 362 if row["method"] == "uniform" else 726,
            "projections": 1 if row["method"] == "uniform" else 2,
            "predictions": int("/" in row["method"] or row["method"] == "uniform-homotopy"),
            "NN_queries": int(row["method"] == "nearest_neighbor"),
            "OC_updates": 360 if row["method"] == "uniform" else 720,
        }
        event = {
            "ordinal": len(self.events) + 1,
            "case_id": row["case_id"],
            "method": row["method"],
            "phase": row["phase"],
            "operation": name,
            "status": "BEFORE_CALL",
        }
        self.events.append(event)
        if (
            self._row_counts[name] >= limits[name]
            or name == "FEM"
            and self.totals[name] >= self.fem_cap
        ):
            event["status"] = "REFUSED_BEFORE_CALL"
            raise QueryResourceExceeded(f"{name} registered operation cap exhausted")
        self._row_counts[name] += 1
        self.totals[name] += 1
        initialization = None
        if name == "projections":
            raw = args[1]
            initialization = {
                "status": "BEFORE_PROJECTION",
                "raw_dtype": str(raw.dtype),
                "raw_shape": list(raw.shape),
                "raw_density": raw.reshape(-1).tolist(),
                "raw_sha256": hashlib.sha256(
                    raw.astype(raw.dtype.newbyteorder("<")).tobytes()
                ).hexdigest(),
            }
            self._initializations.append(initialization)
        try:
            if name == "predictions" and self.model_identities:
                selected = [key for key, model in self.models.items() if model is args[1]]
                if row["method"] == "uniform-homotopy":
                    kind = type(args[1])
                    if (
                        kind.__module__ != "p17_m2_homotopy"
                        or kind.__qualname__ != "evaluate_query.<locals>.UniformModel"
                        or args[1].state_dict()
                    ):
                        raise QueryResourceExceeded("UNIFORM_CONTROL_MODEL_CHANGED")
                    event["model_identity"] = {
                        "fixed_derived_control": "uniform-homotopy",
                        "parameter_sha256": parameter_digest(args[1]),
                    }
                elif len(selected) != 1:
                    raise QueryResourceExceeded("MODEL_STATE_IDENTITY_CHANGED: unregistered model")
                else:
                    identity = self.model_identities[selected[0]]
                    actual = parameter_digest(args[1])
                    event.update(model_identity=identity, actual_parameter_sha256=actual)
                    if actual != identity["parameter_sha256"]:
                        raise QueryResourceExceeded("MODEL_STATE_IDENTITY_CHANGED")
            result = function(*args, **kwargs)
            if name == "predictions" and row["method"] == "uniform-homotopy":
                import numpy as np

                expected_uniform = np.float32(args[0].problem.optimization.volume_fraction)
                if not bool(np.all(result == expected_uniform)):
                    raise QueryResourceExceeded("UNIFORM_CONTROL_DENSITY_CHANGED")
        except BaseException as error:
            event.update(status="RAISED", error_type=type(error).__name__, reason=str(error))
            if initialization is not None:
                initialization.update(
                    status="PROJECTION_RAISED", error_type=type(error).__name__, reason=str(error)
                )
            raise
        if initialization is not None:
            initialization.update(
                status="PROJECTED",
                projected_design_density=result.design_density.tolist(),
                projected_physical_density=result.physical_density.tolist(),
            )
        if name == "NN_queries":
            self._NN_matches.append(
                {"case_id": result.case_id, "mean_squared_distance": result.mean_squared_distance}
            )
        event["status"] = "RETURNED"
        return result

    @contextmanager
    def _instrument(self):
        from topolab import b2_5_evaluation, b4_polish, baselines, experiment, p17_m2_homotopy, simp
        from topolab.baselines import NearestNeighborIndex

        changes = []

        def wrap(owner, name, operation):
            original = getattr(owner, name)
            need(not getattr(original, "_m2_measured", False), "nested numerical instrumentation")

            @wraps(original)
            def measured(*args, **kwargs):
                return self._event(operation, original, *args, **kwargs)

            measured._m2_measured = True
            changes.append((owner, name, original))
            setattr(owner, name, measured)

        try:
            for module in (simp, b4_polish, baselines, p17_m2_homotopy):
                wrap(module, "evaluate_compliance", "FEM")
            for module in (simp, b4_polish, p17_m2_homotopy):
                wrap(module, "optimality_criteria_update", "OC_updates")
            wrap(b2_5_evaluation, "_predict", "predictions")
            wrap(experiment, "project_design_density", "projections")
            wrap(NearestNeighborIndex, "query", "NN_queries")
            yield
        finally:
            for owner, name, original in reversed(changes):
                setattr(owner, name, original)

    def evaluate(self, case, method, reference=None, *, phase="query"):
        """One query over in-memory inputs; caller owns grants and native evidence."""
        from topolab.b3_queries import TerminalWitness
        from topolab.problem import TopologyResult

        need(method in METHODS, "method outside fixed scientific19")
        need(
            phase in ("reference", "query") and (phase == "query" or method == "uniform"),
            "registered reference/query phase required",
        )
        need(self.failure is None and self._current is None, "STOP_NO_RETRY")
        row_id = {"case_id": case.case_id, "method": method, "phase": phase}
        need(row_id not in self.rows, "duplicate scientific row")
        self.rows.append(row_id)
        self._current = row_id
        self._row_counts = dict.fromkeys(self.totals, 0)
        self._initializations, self._NN_matches = [], []
        event_start, started = len(self.events), perf_counter()

        def checkpoint():
            self.totals["checkpoints"] += 1
            self._row_counts["checkpoints"] += 1
            self.checkpoint()

        dispatched = method.replace("plain-P/", "P/", 1)
        try:
            with self._instrument():
                result = load("p17_m2_homotopy").evaluate_query(
                    case, dispatched, reference, self.models, self.neighbors, checkpoint
                )
            # The unchanged own-state choice has already completed. Preserve all
            # scalar points and exact terminal/window densities, rather than two
            # full density trajectories in the new phase-aware representation.
            initializations = iter(self._initializations)
            for attempt in (result["attempt"], result["fallback"]):
                if attempt is not None:
                    attempt["initialization_witness"] = (
                        None
                        if attempt["failure_code"] == "setup_error"
                        else next(initializations, None)
                    )
                if attempt is not None and attempt["continuation"] is not None:
                    continuation = attempt["continuation"]
                    attempt["continuation"] = {
                        key: TerminalWitness.from_result(
                            TopologyResult.model_validate(value)
                        ).model_dump(mode="json")
                        if key in ("before", "after")
                        else value
                        for key, value in continuation.items()
                    }
            elapsed = perf_counter() - started
            result.update(
                schema="topolab.v2.m2-scientific-query.v1",
                method=method,
                dispatched_method=dispatched,
                case_id=case.case_id,
                phase=phase,
                wall_seconds=elapsed,
                charged_seconds=elapsed + 1,
                measured_operations=dict(self._row_counts),
                operation_events=self.events[event_start:],
                NN_match_witnesses=list(self._NN_matches),
                selected_weight_identity=self.model_identities.get(
                    (result["selected_recipe"], result["seed"])
                ),
            )
            return result
        except BaseException as error:
            self.failure = {
                **row_id,
                "error_type": type(error).__name__,
                "reason": str(error),
                "wall_seconds": perf_counter() - started,
                "measured_operations": dict(self._row_counts),
                "operation_events": self.events[event_start:],
                "initialization_witnesses": self._initializations,
                "NN_match_witnesses": self._NN_matches,
            }
            raise
        finally:
            self._current, self._row_counts = None, None


def _file(writer, relative, packet):
    raw = canonical(packet)
    expected = {"path": relative, "byte_size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    receipt = writer(relative, packet)
    need(receipt == expected, "actual immutable scientific writer receipt differs")
    return expected


def _terminal(attempt):
    if attempt is None:
        return None
    witness = attempt["phase_witness"] or attempt["legacy_witness"]
    return None if witness is None else witness["result"]


def _run_panel(
    cases,
    table,
    assets,
    scalar_references,
    *,
    contract_sha256,
    checkpoint,
    writer,
    public_fixture_only,
    role_started,
):
    """One finite streaming panel; classified quality failures do not truncate it."""
    from topolab.b3_queries import QueryResourceExceeded

    case_map = {case.case_id: case for case in cases}
    rows, references, attempts, internal_charge = [], {}, 0, 0.0
    measured = None
    current_row, current_packet = None, None

    def bounded_checkpoint():
        checkpoint()
        if max(internal_charge, perf_counter() - role_started + attempts + 10) > 10800:
            raise QueryResourceExceeded("producer10800 full charge exhausted")

    measured = MeasuredQueries(
        assets.models, None, checkpoint=bounded_checkpoint, model_identities=assets.identities
    )
    try:
        for phase, ordered in (("reference", table["references"]), ("query", table["queries"])):
            for expected in ordered:
                bounded_checkpoint()
                row_started = perf_counter()
                attempts += 1
                current_row, current_packet = {"phase": phase, **expected}, None
                case_id, method = expected["case_id"], expected["method"]
                case = case_map[case_id]
                measured.models, measured.neighbors, setup = assets.load_for_row(case, method)
                packet = measured.evaluate(case, method, references.get(case_id), phase=phase)
                packet["row_input_setup"] = setup
                setup_wall = setup.get("wall_seconds", 0)
                packet["wall_seconds"] += setup_wall
                packet["charged_seconds"] = packet["wall_seconds"] + 1
                current_packet = packet
                packet.update(
                    execution_identity=IDENTITY,
                    scientific_contract_sha256=contract_sha256,
                    software_only=public_fixture_only,
                )
                result = _terminal(packet["attempt"])
                compatibility = True
                if phase == "reference":
                    need(
                        packet["attempt"] is not None
                        and packet["attempt"]["succeeded"] is True
                        and packet["fallback"] is None
                        and result is not None,
                        "STOP_ROUTE_NOT_ISOLATED: mandatory new uniform reference failed",
                    )
                    compliance = result["compliance"]
                    references[case_id] = compliance
                    if scalar_references is not None:
                        old = scalar_references[case_id]
                        compatibility = abs(compliance - old) <= 1e-9 * abs(old)
                        packet["uniform_reference_compatibility"] = {
                            "new_compliance": compliance,
                            "approved_old_scalar": old,
                            "rtol": 1e-9,
                            "atol": 0,
                            "passed": compatibility,
                        }
                slug = method.replace("/", "-")
                directory = "references" if phase == "reference" else "queries"
                relative = f"{directory}/{expected['ordinal']:03}-{case_id}-{slug}.json"
                receipt = _file(writer, relative, packet)
                # The separate closure observes the actual packet write return.
                # Native whole-role accounting additionally contains this small
                # closure's own serialization/write and the final tool return.
                inclusive_wall = perf_counter() - row_started
                cost = {
                    "schema": "topolab.v2.m2-scientific-row-cost.v1",
                    "phase": phase,
                    "ordinal": expected["ordinal"],
                    "case_id": case_id,
                    "method": method,
                    "packet_sha256": receipt["sha256"],
                    "through_actual_packet_writer_return_seconds": inclusive_wall,
                    "charged_seconds": max(packet["charged_seconds"], inclusive_wall + 1),
                    "recording_allowance_seconds": 1,
                    "own_closure_and_outer_exit": "IN_WHOLE_NATIVE_ROLE_PENDING_EXIT",
                }
                cost_receipt = _file(
                    writer, f"row-costs/{phase}-{expected['ordinal']:03}.json", cost
                )
                internal_charge += cost["charged_seconds"]
                rows.append(
                    {
                        "phase": phase,
                        "ordinal": expected["ordinal"],
                        "case_id": case_id,
                        "method": method,
                        "packet": receipt,
                        "cost": cost_receipt,
                        "charged_seconds": cost["charged_seconds"],
                        "attempt_succeeded": (
                            packet["attempt"] is not None and packet["attempt"]["succeeded"]
                        ),
                        "fallback_occurred": packet["fallback"] is not None,
                        "final_compliance": None if result is None else result["compliance"],
                    }
                )
                need(compatibility, "STOP_ROUTE_NOT_ISOLATED: approved uniform scalar mismatch")
                if (
                    not public_fixture_only
                    and phase == "query"
                    and method == "plain-P/17"
                    and case_id
                    == (
                        "tlcase-v1-55c1b3e64135c23125fc286de5d780fc5d9a1e226d5e43ff0dbc8925b423936a"
                    )
                ):
                    need(
                        not (
                            packet["attempt"] is not None
                            and packet["attempt"]["succeeded"] is True
                        ),
                        "STOP_ROUTE_NOT_ISOLATED: fixed plain-P17 counterexample removed",
                    )
                bounded_checkpoint()
        elapsed = perf_counter() - role_started
        summary = {
            "schema": "topolab.v2.m2-scientific-producer-summary.v1",
            "status": "PRODUCER_PANEL_COMPLETE_PENDING_INDEPENDENT_AUDIT",
            "execution_identity": IDENTITY,
            "scientific_contract_sha256": contract_sha256,
            "software_only": public_fixture_only,
            "attempted_rows": attempts,
            "rows": rows,
            "new_references": references,
            "measured_operations": dict(measured.totals),
            "input_load": assets.metadata,
            "query_input_setup_operations": dict(assets.row_setup_counts),
            "internal_row_charge_seconds": internal_charge,
            "through_summary_preparation_wall_seconds": elapsed,
            "known_role_charge_lower_bound_seconds": max(internal_charge, elapsed + attempts + 10),
            "resource_and_actual_exit": "PENDING_INDEPENDENT_NATIVE_OUTER_RETURN",
            "seed17_repaired": "NOT_ESTABLISHED_BY_PRODUCER",
        }
        summary["summary_packet"] = _file(writer, "producer-summary.json", summary)
        return summary
    except BaseException as error:
        failure = {
            "schema": "topolab.v2.m2-scientific-producer-failure.v1",
            "status": "STOP_NO_RETRY",
            "execution_identity": IDENTITY,
            "scientific_contract_sha256": contract_sha256,
            "error_type": type(error).__name__,
            "reason": str(error),
            "attempted_rows": attempts,
            "completed_rows": rows,
            "current_row": current_row,
            "current_packet": current_packet,
            "measured_operations": dict(measured.totals),
            "current_query_failure": measured.failure,
            "wall_seconds": perf_counter() - role_started,
            "internal_row_charge_seconds": internal_charge,
            "known_role_charge_lower_bound_seconds": max(
                internal_charge, perf_counter() - role_started + attempts + 10
            ),
            "resource_and_actual_exit": "UNKNOWN_UNTIL_NATIVE_OUTER_RETURN",
            "secondary_errors": [],
        }
        try:
            _file(writer, "producer-failure.json", failure)
        except BaseException as secondary:
            failure["secondary_errors"].append(
                {
                    "stage": "failure filing",
                    "type": type(secondary).__name__,
                    "reason": str(secondary),
                }
            )
        error.scientific_failure = failure
        raise


def _produce_granted(contract, consumer, *, contract_sha256, checkpoint, writer):
    """Execute C only from a separate opaque scientific grant and accepted buffers."""
    role_started = perf_counter()
    public = contract.get("public_fixture_only", False)
    binding = _scientific_binding(consumer, contract_sha256, public_fixture_only=public)
    need(
        hashlib.sha256(canonical(contract)).hexdigest() == contract_sha256
        and contract.get("schema") == "topolab.v2.m2-scientific-contract.v1"
        and contract.get("execution_identity") == IDENTITY
        and contract["acquisition"]["version_id"] == binding["version_id"],
        "frozen scientific contract/input version differs",
    )
    proposal_raw = (REPO / "docs/planning/p17_m2_native_homotopy_proposal.json").read_bytes()
    need(
        hashlib.sha256(proposal_raw).hexdigest() == contract["proposal_sha256"],
        "frozen scientific proposal differs",
    )
    proposal = json.loads(proposal_raw)
    table = build_call_plan(proposal)
    need(
        canonical(contract["call_plan"]) == canonical(table),
        "complete scientific call table differs",
    )
    from topolab.experiment import ExperimentCase

    definitions = contract["case_definitions"]
    cases = [ExperimentCase.model_validate(value) for value in definitions]
    need(
        hashlib.sha256(canonical(definitions)).hexdigest() == table["case_definitions_sha256"]
        and [case.case_id for case in cases] == proposal["prospective_pilot"]["case_ids"],
        "exact18 source-frozen case definitions required",
    )
    checkpoint()
    assets = load_assets(consumer, contract_sha256, public_fixture_only=public)
    references = load_references(
        consumer, contract_sha256, [case.case_id for case in cases], public_fixture_only=public
    )
    result = _run_panel(
        cases,
        table,
        assets,
        references,
        contract_sha256=contract_sha256,
        checkpoint=checkpoint,
        writer=writer,
        public_fixture_only=public,
        role_started=role_started,
    )
    return {"result": result, "reader_pending": consumer.lease.pending_return()}


def produce(contract, consumer, *, contract_sha256, checkpoint, writer):
    """Retain source/decoder and row failures without replacing the first error."""
    _scientific_binding(
        consumer, contract_sha256, public_fixture_only=contract.get("public_fixture_only", False)
    )
    started = perf_counter()
    try:
        return _produce_granted(
            contract,
            consumer,
            contract_sha256=contract_sha256,
            checkpoint=checkpoint,
            writer=writer,
        )
    except BaseException as error:
        packet = {
            "schema": "topolab.v2.m2-scientific-stop-context.v1",
            "status": "STOP_NO_RETRY",
            "scientific_contract_sha256": contract_sha256,
            "error_type": type(error).__name__,
            "reason": str(error),
            "row_failure": getattr(error, "scientific_failure", None),
            "input_failure": consumer.failure,
            "input_source_facts": consumer.reader.source_facts,
            "input_source_identities": consumer.reader.source_observations,
            "wall_seconds": perf_counter() - started,
            "secondary_errors": [],
            "outer_charge_and_RSS": "UNKNOWN_UNTIL_ACTUAL_NATIVE_OUTER_RETURN",
        }
        try:
            _file(writer, "producer-stop-context.json", packet)
        except BaseException as secondary:
            packet["secondary_errors"].append(
                {
                    "stage": "source/STOP context filing",
                    "type": type(secondary).__name__,
                    "reason": str(secondary),
                }
            )
        error.scientific_stop_context = packet
        raise


def public_fixture_panel(*, writer):
    """Exercise the same complete streaming/charge loop using only NEW tiny data."""
    query = load("p17_m2_homotopy")
    case = query.read_public_manifest(
        query.PUBLIC_FIXTURE, query.PUBLIC_FIXTURE_SHA256, expected_bytes=query.PUBLIC_FIXTURE_BYTES
    )
    started = perf_counter()
    models, neighbors, identities = query.public_assets(
        case, query.public_asset_specification(case)
    )
    assets = ScientificAssets(
        models,
        {tuple(case.problem.mesh.element_counts): neighbors},
        {},
        {"new_public_assets": identities, "source_member_reads": 0},
        _authority=_ASSET_AUTHORITY,
    )
    table = {
        "references": [{"ordinal": 1, "case_id": case.case_id, "method": "uniform"}],
        "queries": [
            {"ordinal": i, "case_id": case.case_id, "method": method}
            for i, method in enumerate(METHODS, 1)
        ],
    }
    return _run_panel(
        [case],
        table,
        assets,
        None,
        contract_sha256=query.PUBLIC_FIXTURE_SHA256,
        checkpoint=lambda: None,
        writer=writer,
        public_fixture_only=True,
        role_started=started,
    )
