"""B4's fixed development screen, immutable case ledger and prospective freeze."""

import fcntl
from collections.abc import Callable
from datetime import UTC, datetime
from math import isfinite
from pathlib import Path
from time import perf_counter
from typing import Annotated, Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import Field, model_validator
from torch import nn

from topolab.b3_access import B3Access, B3ArtifactReference
from topolab.b3_artifacts import _parse_record, _read_bytes, atomic_write, safe_path
from topolab.b3_catalog import B3CatalogEntry, CaseId, Sha256, canonical_metadata_bytes
from topolab.b3_dataset import B3DataContext, B3LabelRecord, NonnegativeSeconds
from topolab.b3_materialization import B3DataSuccess, _peak_rss_bytes
from topolab.b3_queries import (
    METHODS,
    QueryOutcome,
    QueryResourceExceeded,
    audit_witness,
    evaluate_query,
    policy_route,
)
from topolab.b3_training import SEEDS, Recipe
from topolab.b3_training_artifacts import B3TrainingIndex, digest, read_selected_model
from topolab.baselines import BaselineMetrics, NearestNeighborIndex
from topolab.dataset_cli import validate_external_output_root
from topolab.experiment import encode_case
from topolab.problem import ContractModel

TRAINING_INDEX_SHA256 = "229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7"
SCREEN_SECONDS = 21_600.0
SCREEN_RSS_BYTES = 2_147_483_648
FINALIZATION_ALLOWANCE = 10.0
STATISTICS_SPEC = {
    "statistics_version": "topolab.b3.statistics.v1",
    "bootstrap_resamples": 10_000,
    "rng": "numpy.default_rng",
    "seed": 20260930,
    "percentiles": [2.5, 97.5],
    "quantile_method": "linear",
    "resampling": "paired physical cases within each scale/direction/volume cell",
    "cell_order": "small/large; x/y/z as present; ascending volume; case_id within cell",
    "rng_reset_units": ["each ID scale", "each OOD scale", "pooled ID"],
    "primary": "arithmetic per-case selected-primary/uniform end-to-end ratio by mesh",
    "method_order_version": "topolab.b3.method-order.v1",
    "final_order": "canonical ID then canonical OOD; uniform first; hash-rotated remainder",
    "contract_sha256": "452a6c1b3664e007a258a914877c935f333c1823f3ec3d977ee0d09583129af8",
}


def screen_entries() -> tuple[B3CatalogEntry, ...]:
    return B3Access(consumer="screen").case_entries()


def method_name(method: str, seed: int | None) -> str:
    return method if seed is None else f"{method}/{seed}"


class B3ScreenContext(ContractModel):
    evaluation_version: Literal["topolab.b3.evaluation.v1"] = "topolab.b3.evaluation.v1"
    phase: Literal["screen"] = "screen"
    source: B3DataContext
    training_index_sha256: Literal[
        "229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7"
    ] = "229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7"
    training_index: B3TrainingIndex

    @model_validator(mode="after")
    def validate_fit_gate(self) -> "B3ScreenContext":
        if (
            digest(canonical_metadata_bytes(self.training_index.model_dump(mode="json")))
            != self.training_index_sha256
            or not self.training_index.fitting_gate_passed
        ):
            raise ValueError("screen requires the unchanged passed B4.1 fitting receipt")
        return self

    def sha256(self) -> str:
        return digest(canonical_metadata_bytes(self.model_dump(mode="json")))


class QueryMeasure(ContractModel):
    name: str
    succeeded: bool
    candidate_failed: bool
    rejected: bool
    fallback_used: bool
    end_to_end_seconds: Annotated[float, Field(gt=0)]
    paired_time_ratio: Annotated[float, Field(gt=0)]
    candidate: BaselineMetrics | None
    operational: BaselineMetrics | None


class CaseMeasures(ContractModel):
    entry: B3CatalogEntry
    fatal_code: Literal["uniform_failure", "uniform_mismatch", "fallback_failure"] | None = None
    queries: tuple[QueryMeasure, ...]


class B3CaseRecord(ContractModel):
    record_version: Literal["topolab.b3.case-outcomes.v1"] = "topolab.b3.case-outcomes.v1"
    context_sha256: Sha256
    entry: B3CatalogEntry
    mandatory_uniform_compliance: Annotated[float, Field(gt=0)]
    fatal_code: Literal["uniform_failure", "uniform_mismatch", "fallback_failure"] | None = None
    outcomes: tuple[QueryOutcome, ...]

    @model_validator(mode="after")
    def validate_population(self) -> "B3CaseRecord":
        if self.entry not in screen_entries():
            raise ValueError("screen records require the exact frozen screening assignment")
        actual = tuple((q.method, q.seed) for q in self.outcomes)
        if not actual or actual != METHODS[: len(actual)]:
            raise ValueError("case outcomes must retain the exact frozen method prefix")
        if self.fatal_code is None and len(actual) != 15:
            raise ValueError("complete case requires all fifteen outcomes")
        for q in self.outcomes:
            if q.route != policy_route(self.entry.case, q.method):
                raise ValueError("persisted query route differs from the frozen policy")
            if q.method == "nearest_neighbor" and q.attempt is not None:
                permitted = {
                    e.case.case_id for e in B3Access(consumer="nearest_neighbor").case_entries()
                }
                if (
                    q.attempt.matched_case_id is not None
                    and q.attempt.matched_case_id not in permitted
                ):
                    raise ValueError("nearest-neighbor outcome matched a forbidden case")
        uniform = self.outcomes[0].operational
        expected = "uniform_failure" if uniform is None else None
        if uniform is not None:
            assert uniform.metrics is not None
            if not np.isclose(
                uniform.metrics.final_compliance,
                self.mandatory_uniform_compliance,
                rtol=1e-9,
                atol=0,
            ):
                expected = "uniform_mismatch"
        if expected is None and any(q.operational is None for q in self.outcomes):
            expected = "fallback_failure"
        if self.fatal_code != expected:
            raise ValueError("case fatal status differs from the recorded operational outcomes")
        return self

    def measures(self) -> CaseMeasures:
        denominator = self.outcomes[0].seconds
        values = []
        for q in self.outcomes:
            failed = q.attempt is not None and not q.attempt.succeeded
            operational = q.operational
            values.append(
                QueryMeasure(
                    name=method_name(q.method, q.seed),
                    succeeded=operational is not None and not failed,
                    candidate_failed=failed,
                    rejected=q.route == "reject",
                    fallback_used=failed and q.fallback is not None,
                    end_to_end_seconds=q.seconds,
                    paired_time_ratio=q.seconds / denominator,
                    candidate=None if q.attempt is None else q.attempt.metrics,
                    operational=None if operational is None else operational.metrics,
                )
            )
        return CaseMeasures(entry=self.entry, fatal_code=self.fatal_code, queries=tuple(values))


class CaseFile(ContractModel):
    access: B3ArtifactReference
    byte_size: Annotated[int, Field(strict=True, gt=0)]
    measures: CaseMeasures

    @model_validator(mode="after")
    def validate_case(self) -> "CaseFile":
        if self.access.kind != "outcome" or self.access.entry != self.measures.entry:
            raise ValueError("case artifact and summary differ")
        B3Access(consumer="screen").reference_metadata(self.access)
        return self

    @property
    def relative_path(self) -> str:
        return (
            f"artifacts/outcome/{self.access.entry.case.case_id}/{self.access.artifact_sha256}.json"
        )


class B3EvaluationIndex(ContractModel):
    index_version: Literal["topolab.b3.evaluation-index.v1"] = "topolab.b3.evaluation-index.v1"
    context: B3ScreenContext
    context_sha256: Sha256
    cases: tuple[CaseFile, ...] = ()
    attempted_cases: Annotated[int, Field(strict=True, ge=0)] = 0
    setup_seconds: NonnegativeSeconds = 0
    cumulative_seconds: NonnegativeSeconds = 0
    peak_rss_bytes: Annotated[int, Field(strict=True, ge=0)] = 0
    active_checkpoint_at: datetime | None = None
    setup_active: bool = False
    resource_failed: bool = False
    integrity_failed: bool = False
    numerical_failed: bool = False
    audited_case_ids: tuple[CaseId, ...] = ()

    @model_validator(mode="after")
    def validate_prefix(self) -> "B3EvaluationIndex":
        expected = screen_entries()
        if (
            self.context_sha256 != self.context.sha256()
            or tuple(f.access.entry for f in self.cases) != expected[: len(self.cases)]
            or len(self.cases) > 48
            or self.attempted_cases < len(self.cases)
        ):
            raise ValueError("screen index must preserve its identity and exact case prefix")
        ids = tuple(f.access.entry.case.case_id for f in self.cases)
        if self.audited_case_ids != tuple(c for c in ids if c in self.audited_case_ids):
            raise ValueError("audited cases must be an ordered unique retained subset")
        if self.active_checkpoint_at is not None and self.active_checkpoint_at.utcoffset() != (
            UTC.utcoffset(self.active_checkpoint_at)
        ):
            raise ValueError("resource checkpoint must use UTC")
        if self.setup_active and self.active_checkpoint_at is None:
            raise ValueError("active setup requires a durable resource checkpoint")
        if any(f.measures.fatal_code is not None for f in self.cases) and not self.numerical_failed:
            raise ValueError("terminal operational failures cannot be omitted from the ledger")
        return self

    @property
    def completeness_passed(self) -> bool:
        return (
            len(self.cases) == 48
            and self.audited_case_ids == tuple(e.case.case_id for e in screen_entries())
            and not (self.resource_failed or self.integrity_failed or self.numerical_failed)
            and self.active_checkpoint_at is None
            and self.cumulative_seconds <= SCREEN_SECONDS
            and self.peak_rss_bytes <= SCREEN_RSS_BYTES
        )


def read_screen_index(root: Path, context: B3ScreenContext) -> B3EvaluationIndex:
    contents = safe_path(root, "b3_screen.json").read_bytes()
    index = B3EvaluationIndex.model_validate_json(contents)
    if (
        canonical_metadata_bytes(index.model_dump(mode="json")) != contents
        or index.context != context
    ):
        raise ValueError("screen index canonical bytes or context differ")
    return index


def read_case(root: Path, context: B3ScreenContext, reference: CaseFile) -> B3CaseRecord:
    reference = CaseFile.model_validate(reference.model_dump(mode="json"))
    contents = B3Access(consumer="screen").read_artifact(
        reference.access, lambda _: safe_path(root, reference.relative_path).read_bytes()
    )
    record = B3CaseRecord.model_validate_json(contents)
    if (
        len(contents) != reference.byte_size
        or record.context_sha256 != context.sha256()
        or canonical_metadata_bytes(record.model_dump(mode="json")) != contents
        or record.measures() != reference.measures
    ):
        raise ValueError("case bytes, provenance or measures differ from the retained reference")
    expected = next(
        o for o in context.training_index.context.data_index.entries if o.entry == record.entry
    )
    if not isinstance(expected, B3DataSuccess) or (
        record.mandatory_uniform_compliance != expected.uniform_compliance
    ):
        raise ValueError("screen case changed its mandatory uniform reference")
    return record


def write_case(root: Path, record: B3CaseRecord) -> CaseFile:
    root = validate_external_output_root(Path(__file__).resolve().parents[2], root)
    record = B3CaseRecord.model_validate(record.model_dump(mode="json"))
    contents = canonical_metadata_bytes(record.model_dump(mode="json"))
    access = B3ArtifactReference(
        kind="outcome",
        entry=record.entry,
        artifact_sha256=digest(contents),
        origins=(record.entry.case,),
    )
    reference = CaseFile(access=access, byte_size=len(contents), measures=record.measures())
    target = safe_path(root, reference.relative_path)
    if target.exists() and target.read_bytes() != contents:
        raise ValueError("content-addressed outcome bytes differ")
    atomic_write(target, contents)
    return reference


def write_screen_index(root: Path, index: B3EvaluationIndex) -> None:
    index = B3EvaluationIndex.model_validate(index.model_dump(mode="json"))
    target = safe_path(root, "b3_screen.json")
    if target.exists():
        old = read_screen_index(root, index.context)
        if (
            index.cases[: len(old.cases)] != old.cases
            or index.attempted_cases < old.attempted_cases
            or index.cumulative_seconds < old.cumulative_seconds
            or index.setup_seconds < old.setup_seconds
            or index.peak_rss_bytes < old.peak_rss_bytes
            or any(
                getattr(old, flag) and not getattr(index, flag)
                for flag in ("resource_failed", "integrity_failed", "numerical_failed")
            )
        ):
            raise ValueError("screen case outcomes, resource charges and failures are append-only")
        new = index.cases[len(old.cases) :]
    else:
        new = index.cases
    for reference in new:
        read_case(root, index.context, reference)
    atomic_write(target, canonical_metadata_bytes(index.model_dump(mode="json")))


def load_neighbors(
    data_root: Path, context: B3ScreenContext, checkpoint: Callable[[], None]
) -> dict[tuple[int, int, int], NearestNeighborIndex]:
    """Stream exactly 528 guarded train labels into the original ten-channel shape indexes."""
    data = context.training_index.context.data_index
    references = tuple(
        o.artifact for o in data.entries if isinstance(o, B3DataSuccess) and o.entry.role == "train"
    )
    ordered = sorted(references, key=lambda a: a.access.entry.case.case_id)
    by_id = {a.access.entry.case.case_id: a for a in ordered}
    contents = B3Access(consumer="nearest_neighbor").iter_population(
        (a.access for a in ordered),
        "label",
        lambda a: _read_bytes(data_root, by_id[a.entry.case.case_id]),
    )
    buckets: dict[
        tuple[int, int, int], list[tuple[str, NDArray[np.float32], NDArray[np.float32]]]
    ] = {}
    for raw, artifact in zip(contents, ordered, strict=True):
        checkpoint()
        record = _parse_record(raw, artifact, data.manifest)
        if not isinstance(record, B3LabelRecord):
            raise ValueError("nearest neighbor requires B3 train terminal labels")
        case = record.entry.case
        encoded = encode_case(case)
        nx, ny, nz = case.problem.mesh.element_counts
        shape = nz, ny, nx
        design = np.asarray(record.stored.design_density, dtype=np.float32).reshape(1, *shape)
        buckets.setdefault(shape, []).append((case.case_id, encoded.input_tensor, design))
    return {
        shape: NearestNeighborIndex(
            case_ids=tuple(r[0] for r in records),
            input_tensors=np.stack([r[1] for r in records]),
            design_tensors=np.stack([r[2] for r in records]),
        )
        for shape, records in buckets.items()
    }


def evaluate_screen_case(
    entry: B3CatalogEntry,
    context: B3ScreenContext,
    models: dict[tuple[Recipe, int], nn.Module],
    neighbors: NearestNeighborIndex,
    checkpoint: Callable[[], None],
) -> B3CaseRecord:
    B3Access(consumer="screen").reference_metadata(
        B3ArtifactReference(
            kind="outcome", entry=entry, artifact_sha256="0" * 64, origins=(entry.case,)
        )
    )
    expected = next(
        o for o in context.training_index.context.data_index.entries if o.entry == entry
    )
    if not isinstance(expected, B3DataSuccess):
        raise ValueError("screen mandatory reference is missing")
    outcomes = []
    compliance = None
    fatal: Literal["uniform_failure", "uniform_mismatch", "fallback_failure"] | None = None
    for method, seed in METHODS:
        query = evaluate_query(entry.case, method, seed, compliance, models, neighbors, checkpoint)
        outcomes.append(query)
        operational = query.operational
        if operational is None:
            fatal = "uniform_failure" if method == "uniform" else "fallback_failure"
            break
        if method == "uniform":
            assert operational.metrics is not None
            compliance = operational.metrics.final_compliance
            if not np.isclose(compliance, expected.uniform_compliance, rtol=1e-9, atol=0):
                fatal = "uniform_mismatch"
                break
    return B3CaseRecord(
        context_sha256=context.sha256(),
        entry=entry,
        mandatory_uniform_compliance=expected.uniform_compliance,
        fatal_code=fatal,
        outcomes=tuple(outcomes),
    )


def audit_case(record: B3CaseRecord, checkpoint: Callable[[], None]) -> None:
    uniform = record.outcomes[0].operational
    reference = None
    if uniform is not None:
        assert uniform.metrics is not None
        reference = uniform.metrics.final_compliance
    for outcome in record.outcomes:
        for attempt in (outcome.attempt, outcome.fallback):
            checkpoint()
            if attempt is not None and attempt.succeeded:
                assert attempt.state is not None
                checked = audit_witness(record.entry.case, attempt.state, reference, accepted=True)
                if checked != attempt.metrics:
                    raise ValueError("accepted metrics differ from independently audited state")
        if outcome.fallback is not None and outcome.fallback.succeeded:
            assert outcome.fallback.metrics is not None and reference is not None
            if not np.isclose(
                outcome.fallback.metrics.final_compliance, reference, rtol=1e-9, atol=0
            ):
                raise ValueError(
                    "retained fresh uniform fallback differs from its matched reference"
                )


class PolicySummary(ContractModel):
    method: str
    overall_mean: float
    scale_means: dict[str, float]
    direction_means: dict[str, float]
    failures: int
    fallbacks: int
    non_specialist_y_failures: int
    worst_scale_mean: float
    worst_direction_mean: float
    seed_gate_passed: bool | None = None
    primary_eligible: bool | None = None


def _valid_measures(row: CaseMeasures) -> bool:
    if not row.queries or row.queries[0].operational is None:
        return False
    uniform = row.queries[0]
    assert uniform.operational is not None
    for query in row.queries:
        metrics = query.operational
        if (
            metrics is None
            or query.rejected
            or query.paired_time_ratio != query.end_to_end_seconds / uniform.end_to_end_seconds
            or query.candidate_failed != (not query.succeeded)
            or query.fallback_used != query.candidate_failed
            or (query.succeeded and query.candidate != metrics)
            or metrics.iterations > 360
            or metrics.physical_volume_error > 0.005
            or metrics.final_compliance > 1.001 * uniform.operational.final_compliance
            or (
                query.fallback_used
                and not np.isclose(
                    metrics.final_compliance,
                    uniform.operational.final_compliance,
                    rtol=1e-9,
                    atol=0,
                )
            )
        ):
            return False
    return uniform.succeeded and not uniform.candidate_failed and uniform.paired_time_ratio == 1.0


def selection_decision(rows: tuple[CaseMeasures, ...]) -> dict[str, object]:
    """Apply the preregistered seed panel, quality cells and primary tie order."""
    expected_names = tuple(method_name(m, s) for m, s in METHODS)
    complete = tuple(r.entry for r in rows) == screen_entries() and all(
        r.fatal_code is None
        and _valid_measures(r)
        and tuple(q.name for q in r.queries) == expected_names
        and all(q.operational is not None and not q.rejected for q in r.queries)
        for r in rows
    )
    if not complete:
        return {
            "complete": False,
            "model_gate_passed": False,
            "selected_seed": None,
            "passing_seeds": [],
            "selection_table": [],
            "quality_cells": {},
        }
    ratios: dict[str, list[tuple[B3CatalogEntry, QueryMeasure]]] = {
        name: [] for name in expected_names
    }
    for row in rows:
        for query in row.queries:
            ratios[query.name].append((row.entry, query))
    table: dict[str, PolicySummary] = {}
    overall = {
        name: float(np.mean([q.paired_time_ratio for _, q in values]))
        for name, values in ratios.items()
    }
    for name, values in ratios.items():
        scales = {
            scale: float(
                np.mean(
                    [
                        q.paired_time_ratio
                        for e, q in values
                        if (e.case.problem.mesh.element_counts[0] == 12) == (scale == "small")
                    ]
                )
            )
            for scale in ("small", "large")
        }
        directions = {
            f"{scale}/{direction}": float(
                np.mean(
                    [
                        q.paired_time_ratio
                        for e, q in values
                        if (e.case.problem.mesh.element_counts[0] == 12) == (scale == "small")
                        and e.case.problem.loads[0].direction == direction
                    ]
                )
            )
            for scale in ("small", "large")
            for direction in ("y", "z")
        }
        failures = sum(q.candidate_failed for _, q in values)
        y_failures = sum(
            q.candidate_failed
            for e, q in values
            if e.case.problem.loads[0].direction == "y"
            and policy_route(e.case, "P") != "specialist"
        )
        table[name] = PolicySummary(
            method=name,
            overall_mean=overall[name],
            scale_means=scales,
            direction_means=directions,
            failures=failures,
            fallbacks=sum(q.fallback_used for _, q in values),
            non_specialist_y_failures=y_failures,
            worst_scale_mean=max(scales.values()),
            worst_direction_mean=max(directions.values()),
        )
    passing = []
    eligible = []
    for seed in SEEDS:
        name, control = f"P/{seed}", table[f"C/{seed}"]
        policy = table[name]
        passed = (
            policy.worst_scale_mean <= 0.90
            and policy.worst_direction_mean <= 1.0
            and policy.failures <= min(2, control.failures)
            and policy.non_specialist_y_failures <= control.non_specialist_y_failures
            and overall[name] < min(overall["physics_heuristic"], overall["nearest_neighbor"])
        )
        primary = (
            passed
            and policy.failures == 0
            and policy.fallbacks == 0
            and overall[name] < overall[f"C/{seed}"]
        )
        table[name] = policy.model_copy(
            update={"seed_gate_passed": passed, "primary_eligible": primary}
        )
        if passed:
            passing.append(seed)
        if primary:
            eligible.append(seed)
    cells = {
        str(volume): sum(
            q.succeeded
            for seed in SEEDS
            for e, q in ratios[f"P/{seed}"]
            if e.case.problem.mesh.element_counts == (24, 12, 6)
            and e.case.problem.loads[0].direction == "y"
            and e.case.problem.optimization.volume_fraction == volume
        )
        for volume in (0.5351, 0.5931)
    }
    selected = (
        min(
            eligible,
            key=lambda seed: (
                table[f"P/{seed}"].worst_scale_mean,
                table[f"P/{seed}"].worst_direction_mean,
                overall[f"P/{seed}"],
                SEEDS.index(seed),
            ),
        )
        if eligible
        else None
    )
    return {
        "complete": True,
        "selection_table": [table[n].model_dump(mode="json") for n in expected_names],
        "passing_seeds": passing,
        "selected_seed": selected,
        "quality_cells": cells,
        "model_gate_passed": len(passing) >= 2
        and min(cells.values()) >= 6
        and selected is not None,
    }


def screen_summary(index: B3EvaluationIndex) -> dict[str, object]:
    decision = selection_decision(tuple(f.measures for f in index.cases))
    return {
        "summary_version": "topolab.b3.screen-summary.v1",
        **decision,
        "context_sha256": index.context_sha256,
        "index_sha256": digest(canonical_metadata_bytes(index.model_dump(mode="json"))),
        "retained_cases": len(index.cases),
        "outcomes": sum(len(f.measures.queries) for f in index.cases),
        "attempted_cases": index.attempted_cases,
        "audited_cases": len(index.audited_case_ids),
        "setup_seconds": index.setup_seconds,
        "cumulative_seconds": index.cumulative_seconds,
        "peak_rss_bytes": index.peak_rss_bytes,
        "completeness_passed": index.completeness_passed,
        "b4_gate_passed": index.completeness_passed and decision["model_gate_passed"],
    }


def run_screen(
    root: Path,
    data_root: Path,
    fit_root: Path,
    context: B3ScreenContext,
    *,
    repository_root: Path,
    audit_only: bool = False,
    startup_seconds: float = 0,
) -> B3EvaluationIndex:
    if not isfinite(startup_seconds) or startup_seconds < 0:
        raise ValueError("startup resource charge must be finite and nonnegative")
    started = perf_counter() - startup_seconds
    context = B3ScreenContext.model_validate(context.model_dump(mode="json"))
    root = validate_external_output_root(repository_root, root)
    data_root = validate_external_output_root(repository_root, data_root)
    fit_root = validate_external_output_root(repository_root, fit_root)
    roots = (root, data_root, fit_root)
    if any(
        a.is_relative_to(b) or b.is_relative_to(a)
        for i, a in enumerate(roots)
        for b in roots[i + 1 :]
    ):
        raise ValueError("data, fitting and screening roots must be separate")
    root.mkdir(parents=True, exist_ok=True)
    with safe_path(root, ".b3-screen-writer.lock").open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("another B3 screen writer owns this root") from error
        target = safe_path(root, "b3_screen.json")
        if audit_only and not target.exists():
            raise ValueError("audit requires an existing screen index")
        index = (
            read_screen_index(root, context)
            if target.exists()
            else B3EvaluationIndex(context=context, context_sha256=context.sha256())
        )
        base = index.cumulative_seconds
        if index.active_checkpoint_at is not None:
            unclosed = max(0, (datetime.now(UTC) - index.active_checkpoint_at).total_seconds())
            base += unclosed
            if index.setup_active:
                index = index.model_copy(update={"setup_seconds": index.setup_seconds + unclosed})
        last_flush = started
        setup_started: float | None = None
        setup_base = index.setup_seconds

        def checkpoint(*, force: bool = False, close: bool = False) -> None:
            nonlocal index, last_flush
            now = perf_counter()
            elapsed, rss = base + now - started, max(index.peak_rss_bytes, _peak_rss_bytes())
            if close:
                elapsed += FINALIZATION_ALLOWANCE
            exhausted = elapsed >= SCREEN_SECONDS or rss > SCREEN_RSS_BYTES
            if force or close or exhausted or now - last_flush >= 5:
                index = index.model_copy(
                    update={
                        "cumulative_seconds": elapsed,
                        "peak_rss_bytes": rss,
                        "active_checkpoint_at": None if close else datetime.now(UTC),
                        "resource_failed": index.resource_failed or exhausted,
                        "setup_active": setup_started is not None and not close,
                        "setup_seconds": index.setup_seconds
                        if setup_started is None
                        else (setup_base + now - setup_started),
                    }
                )
                write_screen_index(root, index)
                last_flush = now
            if exhausted and not close:
                raise QueryResourceExceeded("B4 screen resource budget is exhausted")

        try:
            if index.resource_failed or index.integrity_failed or index.numerical_failed:
                raise ValueError("screen index retains a permanent failure")
            index = index.model_copy(update={"audited_case_ids": ()})
            checkpoint(force=True)
            for reference in index.cases:
                checkpoint()
                read_case(root, context, reference)
            if not audit_only and len(index.cases) < 48:
                setup_started = perf_counter()
                checkpoint(force=True)
                models: dict[tuple[Recipe, int], nn.Module] = {}
                for outcome in context.training_index.outcomes:
                    checkpoint()
                    _, models[(outcome.recipe, outcome.seed)] = read_selected_model(
                        fit_root, context.training_index.context, outcome
                    )
                neighbors = load_neighbors(data_root, context, checkpoint)
                checkpoint(force=True)
                setup_started = None
                for entry in screen_entries()[len(index.cases) :]:
                    index = index.model_copy(update={"attempted_cases": index.attempted_cases + 1})
                    checkpoint(force=True)
                    nx, ny, nz = entry.case.problem.mesh.element_counts
                    record = evaluate_screen_case(
                        entry, context, models, neighbors[(nz, ny, nx)], checkpoint
                    )
                    reference = write_case(root, record)
                    index = index.model_copy(
                        update={
                            "cases": (*index.cases, reference),
                            "numerical_failed": record.fatal_code is not None,
                        }
                    )
                    checkpoint(force=True)
                    print(
                        f"B4 screen {len(index.cases)}/48: {record.entry.case.case_id}", flush=True
                    )
                    if record.fatal_code is not None:
                        break
            audited = []
            for reference in index.cases:
                checkpoint()
                audit_case(read_case(root, context, reference), checkpoint)
                audited.append(reference.access.entry.case.case_id)
                index = index.model_copy(update={"audited_case_ids": tuple(audited)})
                checkpoint(force=True)
        except QueryResourceExceeded:
            index = index.model_copy(update={"resource_failed": True})
        except (ValueError, RuntimeError, PermissionError, FileNotFoundError):
            index = index.model_copy(update={"integrity_failed": True})
            raise
        finally:
            checkpoint(close=True)
        return index


class B3Freeze(ContractModel):
    freeze_version: Literal["topolab.b3.freeze.v1"] = "topolab.b3.freeze.v1"
    context: B3ScreenContext
    screen_index: B3EvaluationIndex
    screen_index_sha256: Sha256
    selected_seed: Literal[17, 29, 43]
    screen_summary: dict[str, object]
    statistics: dict[str, object]

    @model_validator(mode="after")
    def validate_decision(self) -> "B3Freeze":
        if (
            self.statistics != STATISTICS_SPEC
            or not self.screen_summary.get("b4_gate_passed")
            or self.screen_summary.get("selected_seed") != self.selected_seed
            or self.screen_summary.get("index_sha256") != self.screen_index_sha256
            or self.screen_summary.get("context_sha256") != self.context.sha256()
            or self.screen_index.context != self.context
            or self.screen_summary != screen_summary(self.screen_index)
        ):
            raise ValueError("freeze requires the passed prospective screen and exact statistics")
        return self


def publish_freeze(root: Path, index: B3EvaluationIndex) -> Path | None:
    summary = screen_summary(index)
    if not summary["b4_gate_passed"]:
        return None
    freeze = B3Freeze.model_validate(
        {
            "context": index.context,
            "screen_index": index,
            "screen_index_sha256": summary["index_sha256"],
            "selected_seed": summary["selected_seed"],
            "screen_summary": summary,
            "statistics": STATISTICS_SPEC,
        }
    )
    contents = canonical_metadata_bytes(freeze.model_dump(mode="json"))
    reference = safe_path(root, f"artifacts/freeze/{digest(contents)}.json")
    target = safe_path(root, "b3_freeze.json")
    if target.exists():
        previous = B3Freeze.model_validate_json(target.read_bytes())
        if (
            previous.context != freeze.context
            or previous.selected_seed != freeze.selected_seed
            or previous.screen_index.cases != freeze.screen_index.cases
            or previous.screen_index.cumulative_seconds > freeze.screen_index.cumulative_seconds
            or previous.screen_summary["selection_table"] != summary["selection_table"]
        ):
            raise ValueError("a frozen policy or retained comparison cannot change")
    atomic_write(reference, contents)
    atomic_write(target, contents)
    return reference
