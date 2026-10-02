"""Shared charged execution for fixed-model development experiments."""

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from torch import nn

from topolab import b4_evidence as evidence
from topolab.b3_access import B3Access, B3ArtifactReference
from topolab.b3_artifacts import B3DataArtifact, _parse_record, _read_bytes, safe_path
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_dataset import audit_b3_record
from topolab.b3_materialization import B3DataSuccess
from topolab.b3_queries import QueryOutcome
from topolab.b3_screening import B3ScreenContext, load_neighbors
from topolab.b3_training import Recipe
from topolab.b4_telemetry import Journal, durable_write
from topolab.b4_weighted_terminal import read_units
from topolab.experiment import ExperimentCase

ModelPanel = dict[tuple[Recipe, int], nn.Module]


@dataclass(frozen=True)
class DevelopmentSpec:
    version: str
    receipt_version: str
    caps: dict[str, tuple[float, int]]
    cases: tuple[ExperimentCase, ...]
    assignments: tuple[tuple[str, str], ...]
    gate: Callable[[Iterable[dict[str, Any]]], dict[str, Any]]
    upstream_fits: Callable[[Path], list[dict[str, Any]]]

    def units(self, stage: str) -> tuple[str, ...]:
        if stage == "reference":
            return tuple(c.case_id for c in self.cases)
        if stage == "screen":
            return tuple(f"{c}:{m}" for c, m in self.assignments)
        if stage != "audit":
            raise ValueError("fixed-model development has no fitting stage")
        return (
            "inputs",
            "nn_labels",
            *(f"reference:{c}" for c in self.units("reference")),
            *(f"screen:{u}" for u in self.units("screen")),
        )


def run_development(
    stage: str,
    output: Path,
    data: Path,
    old: Path,
    weighted_root: Path,
    context: B3ScreenContext,
    sha: str,
    startup: float,
    *,
    spec: DevelopmentSpec,
    load_models: Callable[[B3ScreenContext, Path, Path], tuple[ModelPanel, ModelPanel]],
    evaluate_query: Callable[..., QueryOutcome],
) -> dict[str, Any]:
    def receipt(root: Path, ordinal: int, ref: dict[str, Any], sha: str) -> None:
        evidence.recording_receipt(root, ordinal, ref, sha, spec.receipt_version)

    def read_packet(
        root: Path, ref: dict[str, Any], sha: str, case: str, policy: str
    ) -> dict[str, Any]:
        return evidence.read_packet(root, ref, sha, case, policy, spec.version)

    def pulse() -> None:
        journal.pulse()

    journal = Journal(
        output / stage, sha, spec.units(stage), *spec.caps[stage], opening_seconds=startup
    )
    cases = {c.case_id: c for c in spec.cases}
    summary: dict[str, Any] = {"version": spec.version, "stage": stage, "context_sha256": sha}
    try:
        spec.upstream_fits(weighted_root)
        if stage == "reference":
            for i, retained in enumerate(journal.records):
                receipt(journal.root, i, retained["payload"], sha)
                evidence.check_packet(
                    read_packet(
                        journal.root, retained["payload"], sha, spec.units(stage)[i], "uniform"
                    ),
                    None,
                    cases[spec.units(stage)[i]],
                )
            for case_id in spec.units(stage)[journal.state.completed :]:
                packet = evidence.query(
                    journal,
                    cases[case_id],
                    "uniform",
                    None,
                    {},
                    None,
                    sha,
                    spec.version,
                    spec.receipt_version,
                    evaluate_query,
                )
                evidence.check_packet(packet, None, cases[case_id])
                print(json.dumps({"references": journal.state.completed}), flush=True)
        else:
            references = read_units(
                output / "reference", sha, spec.units("reference"), caps=spec.caps
            )
            compliance = {}
            for i, (case_id, ref) in enumerate(
                zip(spec.units("reference"), references, strict=True)
            ):
                receipt(output / "reference", i, ref, sha)
                packet = read_packet(output / "reference", ref, sha, case_id, "uniform")
                outcome = QueryOutcome.model_validate(packet["outcome"])
                if outcome.operational is None or outcome.operational.metrics is None:
                    raise ValueError("mandatory reference failed")
                compliance[case_id] = outcome.operational.metrics.final_compliance
            if stage == "screen":
                models, weighted = load_models(context, old, weighted_root)
                neighbors = load_neighbors(data, context, pulse)
                for i, retained in enumerate(journal.records):
                    receipt(journal.root, i, retained["payload"], sha)
                for case_id, policy in spec.assignments[journal.state.completed :]:
                    case = cases[case_id]
                    nx, ny, nz = case.problem.mesh.element_counts
                    packet = evidence.query(
                        journal,
                        case,
                        policy,
                        compliance[case_id],
                        weighted if policy.startswith("W/") else models,
                        neighbors[(nz, ny, nx)],
                        sha,
                        spec.version,
                        spec.receipt_version,
                        evaluate_query,
                    )
                    evidence.check_packet(packet, compliance[case_id], case)
                    print(
                        json.dumps({"queries": journal.state.completed, "policy": policy}),
                        flush=True,
                    )
                screen_refs = [r["payload"] for r in journal.records]
            else:
                screen_refs = read_units(
                    output / "screen", sha, spec.units("screen"), caps=spec.caps
                )
                for unit in spec.units("audit")[journal.state.completed :]:
                    journal.begin(unit)
                    result: dict[str, Any] = {}
                    if unit == "inputs":
                        models, weighted = load_models(context, old, weighted_root)
                        result["audited_checkpoints"] = len(models) + 3
                        del models, weighted
                    elif unit == "nn_labels":
                        index = context.training_index.context.data_index
                        artifacts = sorted(
                            (
                                o.artifact
                                for o in index.entries
                                if isinstance(o, B3DataSuccess) and o.entry.role == "train"
                            ),
                            key=lambda a: a.access.entry.case.case_id,
                        )
                        by_id = {a.access.entry.case.case_id: a for a in artifacts}

                        def open_label(
                            a: B3ArtifactReference,
                            by_id: dict[str, B3DataArtifact] = by_id,
                        ) -> bytes:
                            return _read_bytes(data, by_id[a.entry.case.case_id])

                        contents = B3Access(consumer="nearest_neighbor").iter_population(
                            (a.access for a in artifacts),
                            "label",
                            open_label,
                        )
                        count = 0
                        for raw, artifact in zip(contents, artifacts, strict=True):
                            audit_b3_record(_parse_record(raw, artifact, index.manifest))
                            count += 1
                            journal.pulse()
                        result["audited_nn_labels"] = count
                    else:
                        is_ref = unit.startswith("reference:")
                        target = "reference" if is_ref else "screen"
                        i = spec.units(target).index(unit.removeprefix(target + ":"))
                        case_id, policy = (
                            (spec.units(target)[i], "uniform") if is_ref else spec.assignments[i]
                        )
                        ref = (references if is_ref else screen_refs)[i]
                        receipt(output / target, i, ref, sha)
                        result["audited_attempts"] = evidence.check_packet(
                            read_packet(output / target, ref, sha, case_id, policy),
                            None if is_ref else compliance[case_id],
                            cases[case_id],
                        )
                    journal.publish(unit, result)
                    if journal.state.completed % 48 == 0:
                        print(json.dumps({"audited_units": journal.state.completed}), flush=True)
            summary["decision"] = spec.gate(
                read_packet(output / "screen", ref, sha, case_id, policy)
                for (case_id, policy), ref in zip(spec.assignments, screen_refs, strict=True)
            )
        journal.close()
        summary.update(
            completed=journal.state.completed,
            attempted=journal.state.attempted,
            charged_seconds=journal.state.charged_seconds,
            peak_rss_bytes=journal.state.peak_rss_bytes,
            head_sha256=journal.state.head_sha256,
        )
        durable_write(safe_path(journal.root, "summary.json"), canonical_metadata_bytes(summary))
        return summary
    except KeyboardInterrupt:
        journal.close()
        raise
    except BaseException:
        if not journal.lock.closed:
            journal.close(integrity_failed=True)
        raise
