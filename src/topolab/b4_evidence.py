"""Shared complete query envelopes and independent terminal/recording audits."""

import json
from collections.abc import Callable
from functools import partial
from pathlib import Path
from time import perf_counter
from typing import Any, cast

from torch import nn

from topolab.b3_artifacts import safe_path
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_queries import QueryMethod, QueryOutcome, audit_witness
from topolab.b3_training import Recipe
from topolab.b4_telemetry import CheckpointMeter, Journal, durable_write, timed_query
from topolab.b4_weighted_terminal import RECORDING_ALLOWANCE, publish_blob, read_blob
from topolab.experiment import ExperimentCase


def read_packet(
    root: Path, ref: dict[str, Any], context_sha: str, case_id: str, policy: str, version: str
) -> dict[str, Any]:
    raw = read_blob(root, ref, "outcome")
    packet = json.loads(raw)
    if (
        raw != canonical_metadata_bytes(packet)
        or packet["version"] != version
        or packet["context_sha256"] != context_sha
        or packet["case_id"] != case_id
        or packet["policy"] != policy
    ):
        raise ValueError("outcome source, case, policy or canonical bytes differ")
    return cast(dict[str, Any], packet)


def check_packet(packet: dict[str, Any], reference: float | None, case: ExperimentCase) -> int:
    outcome = QueryOutcome.model_validate(packet["outcome"])
    audited = 0
    for attempt in (outcome.attempt, outcome.fallback):
        if attempt is not None:
            if attempt.state is None:
                raise ValueError("complete screen requires each attempt's terminal witness")
            metrics = audit_witness(case, attempt.state, reference, accepted=attempt.succeeded)
            if metrics != attempt.metrics:
                raise ValueError("independent terminal metrics differ")
            if attempt is outcome.fallback or packet["policy"] == "uniform":
                if (
                    not attempt.succeeded
                    or reference is not None
                    and abs(metrics.final_compliance / reference - 1) > 1e-9
                ):
                    raise ValueError("uniform or fallback differs from mandatory reference")
            audited += 1
    if outcome.operational is None:
        raise ValueError("mandatory uniform or operational fallback failed")
    return audited


def query(
    journal: Journal,
    case: ExperimentCase,
    policy: str,
    reference: float | None,
    models: dict[tuple[Recipe, int], nn.Module],
    neighbors: Any,
    context_sha: str,
    version: str,
    receipt_version: str,
    evaluator: Callable[..., QueryOutcome],
) -> dict[str, Any]:
    ordinal = journal.state.completed
    # Charge the full allowance in addition to actual elapsed resource wall.
    # begin durably records it before any numerical work; repeats pay it again.
    journal.prior += RECORDING_ALLOWANCE
    boundary = perf_counter()
    journal.begin(journal.units[ordinal])
    opening = perf_counter() - boundary
    # B4.4's meter records inclusively; the stress force is deliberately ignored.
    meter = CheckpointMeter(lambda _: journal.pulse())
    name, _, text = policy.partition("/")
    method = cast(QueryMethod, "P" if name == "W" else name)
    outcome, timing = timed_query(
        partial(
            evaluator,
            case,
            method,
            int(text) if text else None,
            reference,
            models,
            neighbors,
            meter,
        )
    )
    publication = perf_counter()
    packet = {
        "version": version,
        "context_sha256": context_sha,
        "case_id": case.case_id,
        "policy": policy,
        "outcome": outcome.model_dump(mode="json"),
        "timing": timing,
        "callback": meter.summary(),
        "recording_allowance_seconds": RECORDING_ALLOWANCE,
    }
    ref = publish_blob(journal.root, "outcome", canonical_metadata_bytes(packet))
    journal.publish(journal.units[ordinal], ref)
    recording = opening + perf_counter() - publication
    receipt = {
        "version": receipt_version,
        "context_sha256": context_sha,
        "outcome_sha256": ref["sha256"],
        "recording_seconds_before_receipt": recording,
    }
    durable_write(
        safe_path(journal.root, f"recording/{ordinal:04d}.json"), canonical_metadata_bytes(receipt)
    )
    if opening + perf_counter() - publication > RECORDING_ALLOWANCE:
        raise ValueError("query recording exceeded its frozen conservative allowance")
    return packet


def recording_receipt(
    root: Path, ordinal: int, ref: dict[str, Any], context_sha: str, receipt_version: str
) -> None:
    raw = safe_path(root, f"recording/{ordinal:04d}.json").read_bytes()
    receipt = json.loads(raw)
    if (
        canonical_metadata_bytes(receipt) != raw
        or receipt["version"] != receipt_version
        or receipt["context_sha256"] != context_sha
        or receipt["outcome_sha256"] != ref["sha256"]
        or not 0 <= receipt["recording_seconds_before_receipt"] <= RECORDING_ALLOWANCE
    ):
        raise ValueError("recording receipt lacks its bound or complete query binding")
