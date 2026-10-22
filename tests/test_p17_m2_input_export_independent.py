"""New public IO/transcription checks, independently authored from R fields."""

import importlib.util
import json
import os
import shutil
import struct
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "separate_R_source_comparator",
    Path(__file__).parents[1] / "scripts/p17_m2_input_export_independent.py",
)
assert _SPEC is not None and _SPEC.loader is not None
checker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(checker)


def binding(source):  # type: ignore[no-untyped-def]
    return {
        "case_id": source["entry"]["case"]["case_id"],
        "entry": source["entry"],
        "manifest_sha256": source["manifest_sha256"],
        "context_sha256": checker.digest(checker.canonical(source["context"])),
        "source_revision": source["context"]["source_revision"],
        "artifact": checker.reference("new-public-label.json", checker.canonical(source)),
    }


def test_original_public_IO_complete_source_comparison(tmp_path: Path) -> None:
    result = checker.public_check(tmp_path / "new-original-public-fixtures")
    assert result["status"] == "PASS_PUBLIC_IO_ONLY"
    assert result["checkpoint_count"] == 2
    assert result["NN_cases"] == 2
    assert result["scalar_count"] == 1
    assert result["compared_scalar_fields"] > 50000
    assert result["old_source_read_set"] == []
    assert result["FEM_inference_or_complete_history_analysis"] is False
    assert result["damaged_controls_rejected"] == 2


@pytest.mark.parametrize("text", [b'{"a":1,"a":2}', b'{"x":NaN}', b'{"x":1e9999}'])
def test_strict_JSON_refuses_duplicate_nonfinite(text: bytes) -> None:
    with pytest.raises(ValueError):
        checker.parse(text)


def test_JSON_depth_limit() -> None:
    with pytest.raises(ValueError, match="depth"):
        checker.parse(b"[" * 65 + b"0" + b"]" * 65)


@pytest.mark.parametrize("actual", [{"x": 0.0}, {"x": -0.0, "extra": 1}, {"x": 0}])
def test_all_fields_and_signed_zero_are_compared(actual: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        checker.compare_words({"x": -0.0}, actual)


def test_once_reader_refuses_second_read(tmp_path: Path) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    reader = checker.OnceReader(tmp_path, 2, 100)
    assert reader.read("original.json", 100) == b"{}\n"
    with pytest.raises(ValueError, match="repeat"):
        reader.read("original.json", 100)


@pytest.mark.parametrize("relative", ["../outside.json", "/etc/passwd", "a/../original.json"])
def test_once_reader_refuses_path_escape_before_open(tmp_path: Path, relative: str) -> None:
    reader = checker.OnceReader(tmp_path, 1, 100)
    with pytest.raises(ValueError, match="unsafe"):
        reader.read(relative, 100)
    assert reader.seen == set()


def test_once_reader_refuses_symlink(tmp_path: Path) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    (tmp_path / "alias.json").symlink_to("original.json")
    reader = checker.OnceReader(tmp_path, 1, 100)
    with pytest.raises(ValueError, match="symlink"):
        reader.read("alias.json", 100)


def test_once_reader_checks_bytes_and_hash(tmp_path: Path) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    reader = checker.OnceReader(tmp_path, 1, 100)
    with pytest.raises(ValueError, match="SHA"):
        reader.read("original.json", 100, sha256="f" * 64)
    assert reader.table == [checker.reference("original.json", b"{}\n")]
    assert reader.seen == {"original.json"}


@pytest.mark.parametrize("maximum,total,files", [(2, 100, 1), (100, 2, 1), (100, 100, 0)])
def test_once_reader_file_byte_caps(tmp_path: Path, maximum: int, total: int, files: int) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    reader = checker.OnceReader(tmp_path, files, total)
    with pytest.raises(ValueError, match="cap"):
        reader.read("original.json", maximum)


def test_actual_stored_physical_is_preserved_not_reconstructed() -> None:
    source = checker.public_label((12, 6, 3))
    source["stored"]["physical_density"][0] = 0.75
    row = binding(source)
    producer, audit = checker.label_views(source, row)
    assert audit["stored"]["physical_density"][0] == 0.75
    assert producer["stored"]["design_density"][0] == 0.5
    assert "physical_density" not in producer["stored"]
    assert "sensitivity_weight" not in producer["stored"]
    assert "history" not in audit
    assert "displacements" not in audit["terminal"]
    assert "reactions" not in audit["terminal"]
    assert audit["total_updates"] == 11
    assert len(audit["recent"]) == 11


def test_full_history_prefix_is_never_analyzed_or_exported() -> None:
    source = checker.public_label((12, 6, 3))
    # Prefix has no numerical fields, proving the comparator uses only n/recent.
    source["result"]["history"].insert(0, {"deliberately_unanalyzed_prefix": True})
    for state in source["result"]["history"][-11:]:
        state["iteration"] += 1
    source["stored"]["iterations"] = 12
    _, audit = checker.label_views(source, binding(source))
    assert len(audit["recent"]) == 11
    assert audit["recent"][0]["iteration"] == 2
    assert "deliberately_unanalyzed_prefix" not in json.dumps(audit)


@pytest.mark.parametrize("change", ["role", "initialization", "context", "shape", "float32"])
def test_label_binding_or_format_mismatch_stops(change: str) -> None:
    source = checker.public_label((12, 6, 3))
    row = deepcopy(binding(source))
    if change == "role":
        source["entry"]["role"] = "fit_validation"
    elif change == "initialization":
        source["initialization"] = "candidate"
    elif change == "context":
        source["context"]["source_revision"] = "0" * 40
    elif change == "shape":
        source["stored"]["tensor_shape"] = [1, 3, 6, 13]
    else:
        source["stored"]["design_density"][0] = 0.1
    with pytest.raises(ValueError):
        checker.label_views(source, row)


def test_short_physical_plateau_window_stops() -> None:
    source = checker.public_label((12, 6, 3))
    source["result"]["history"] = source["result"]["history"][-10:]
    source["stored"]["iterations"] = 10
    source["stored"]["stop_reason"] = "physical_plateau"
    with pytest.raises(ValueError, match="window"):
        checker.label_views(source, binding(source))


def model(family: str = "C"):  # type: ignore[no-untyped-def]
    return {"family": family, "seed": 17, "epoch": 1, "context_sha256": "a" * 64}


@pytest.mark.parametrize("family", ["C", "W"])
def test_exact_synthetic_Safetensors_header_body(family: str) -> None:
    row = model(family)
    checker.check_safetensors(checker.public_model(row), row)


def test_unweighted_checkpoint_cannot_replace_W() -> None:
    with pytest.raises(ValueError, match="provenance"):
        checker.check_safetensors(checker.public_model(model("C")), model("W"))


def test_Safetensors_nonfinite_tensor_stops() -> None:
    row = model()
    raw = checker.public_model(row)
    bad = raw[:-4] + struct.pack("<f", float("nan"))
    with pytest.raises(ValueError, match="nonfinite"):
        checker.check_safetensors(bad, row)


def test_source_fields_compared_even_if_claimed_digest_is_unchanged() -> None:
    source = checker.public_label((12, 6, 3))
    producer, _ = checker.label_views(source, binding(source))
    altered = deepcopy(producer)
    altered["stored"]["design_density"][0] = 0.75
    assert altered["bit_digests"] == producer["bit_digests"]
    with pytest.raises(ValueError, match="binary64"):
        checker.compare_words(producer, altered)


def test_output_extra_history_field_stops() -> None:
    source = checker.public_label((12, 6, 3))
    producer, _ = checker.label_views(source, binding(source))
    altered = dict(producer, history=source["result"]["history"])
    with pytest.raises(ValueError, match="field set"):
        checker.compare_words(producer, altered)


def primary_subject():  # type: ignore[no-untyped-def]
    """Post-authorship exposure: exporter is a subject, never comparator oracle."""
    spec = importlib.util.spec_from_file_location(
        "R_exporter_subject", Path(__file__).parents[1] / "scripts/p17_m2_input_export.py"
    )
    assert spec and spec.loader
    subject = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subject)
    return subject


@pytest.mark.parametrize("mesh", [(12, 6, 3), (24, 12, 6)])
def test_primary_projections_match_independently_authored_source_fields(mesh) -> None:  # type: ignore[no-untyped-def]
    subject = primary_subject()
    source = checker.public_label(mesh)
    row = binding(source)
    expected = checker.label_views(source, row)
    actual = subject.label_views(source, row)
    assert checker.compare_words(list(expected), list(actual)) > 1000


@pytest.mark.parametrize("family", ["C", "P", "W", "S"])
def test_primary_accepts_independently_authored_original_weight_bytes(family: str) -> None:
    subject = primary_subject()
    row = model(family)
    raw = checker.public_model(row)
    contract = checker.parse(subject.CONTRACT.read_bytes())
    subject.check_weights(raw, row, contract)
    checker.check_safetensors(raw, row)


def test_R0_wire_from_new_synthetic_metadata_only(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    # Reuse the primary's new metadata as a test subject, filling the committed
    # schema's fields its minimal fixture omitted. No historical path is read.
    spec = importlib.util.spec_from_file_location(
        "new_R_metadata_subject", Path(__file__).with_name("test_p17_m2_input_export.py")
    )
    assert spec and spec.loader
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    contract = fixture.source_metadata(tmp_path)
    subject = primary_subject()
    fit_path = tmp_path / "b3-v1-fits/b3_training.json"
    fits = checker.parse(fit_path.read_bytes())
    data = fits["context"]["data_index"]
    for i, outcome in enumerate(data["entries"], 1):
        entry = outcome["entry"]
        case_id = "tlcase-v1-" + f"{i:064x}"
        entry["case"]["case_id"] = case_id
        artifact = outcome["artifact"]
        artifact["access"]["entry"] = deepcopy(entry)
        artifact["relative_path"] = (
            f"artifacts/label/{case_id}/{artifact['access']['artifact_sha256']}.json"
        )
    manifest = data["manifest"]
    manifest["catalog"] = {
        "catalog_version": "topolab.b3.catalog.v1",
        "entries": [o["entry"] for o in data["entries"]],
    }
    manifest_sha = checker.digest(checker.canonical(manifest))
    data["manifest_sha256"] = manifest_sha
    for outcome in data["entries"]:
        outcome["artifact"]["manifest_sha256"] = manifest_sha
    data_sha = checker.digest(checker.canonical(data))
    fits["context"]["data_index_sha256"] = data_sha
    fits["index_version"] = "topolab.b3.training-index.v1"
    fits["context_sha256"] = checker.digest(checker.canonical(fits["context"]))
    contract["R0"]["embedded_B3_data_index_sha256"] = data_sha
    monkeypatch.setattr(checker, "B3_DATA_HASH", data_sha)
    monkeypatch.setattr(
        checker, "CATALOG_HASH", checker.digest(checker.canonical(manifest["catalog"]))
    )
    wroot = "b4-5-weighted-terminal/fit"
    for row in contract["checkpoints"]["fixed_rows"]:
        weighted = row["family"] == "W"
        if weighted:
            ordinal = [17, 29, 43].index(row["seed"])
            unit_path = tmp_path / f"{wroot}/units/{ordinal:04d}.json"
            unit = checker.parse(unit_path.read_bytes())
            ref = unit["payload"]
            root = wroot
        else:
            outcome = next(
                o
                for o in fits["outcomes"]
                if (o["recipe"], o["seed"]) == (row["family"], row["seed"])
            )
            ref = outcome["selection"]
            root = "b3-v1-fits"
        selection = checker.parse(
            (tmp_path / root / f"artifacts/selection/{ref['sha256']}.json").read_bytes()
        )
        history = selection["history_schema"] if weighted else selection
        history["selection_version"] = "topolab.b3.selection.v1"
        if not weighted:
            history["context_sha256"] = fits["context_sha256"]
        raw = checker.canonical(selection)
        ref.update(sha256=checker.digest(raw), byte_size=len(raw))
        (tmp_path / root / f"artifacts/selection/{ref['sha256']}.json").write_bytes(raw)
        if weighted:
            unit_path.write_bytes(checker.canonical(unit))
    fit_path.write_bytes(checker.canonical(fits))
    for base, count in ((wroot, 3), ("b4-30-z-reflection-repair-v2/sentinel/reference", 18)):
        previous = "0" * 64
        for i in range(count):
            path = tmp_path / f"{base}/units/{i:04d}.json"
            unit = checker.parse(path.read_bytes())
            unit["previous_sha256"] = previous
            raw = checker.canonical(unit)
            path.write_bytes(raw)
            previous = checker.digest(raw)
        progress_path, summary_path = (
            tmp_path / base / "progress.json",
            tmp_path / base / "summary.json",
        )
        progress = checker.parse(progress_path.read_bytes())
        progress["head_sha256"] = previous
        progress_path.write_bytes(checker.canonical(progress))
        summary = {
            key: progress[key]
            for key in ("context_sha256", "completed", "attempted", "head_sha256")
        }
        summary_path.write_bytes(checker.canonical(summary))
    for item in contract["R0"]["literal_bootstrap_files"]:
        item["expected_sha256"] = checker.digest((tmp_path / item["relative_path"]).read_bytes())
    expected = checker.build_registry(checker.OnceReader(tmp_path, 40, 32 * checker.MIB), contract)
    actual = subject.register(subject.Reader(tmp_path), contract)
    assert checker.compare_words(expected, actual) > 6000
    assert len(expected["metadata"]) == 40
    assert len(expected["labels"]) == 528
    assert not any(
        "artifacts/label/" in r["path"] or r["path"].endswith(".safetensors")
        for r in expected["metadata"]
    )


def resource_subject():  # type: ignore[no-untyped-def]
    profile = b" 1.00 real 0.10 user 0.00 sys\n100 maximum resident set size\n"
    sampler = b" 0.02 real 0.01 user 0.00 sys\n20 maximum resident set size\n"

    def timer(pid):  # type: ignore[no-untyped-def]
        return {
            "statistics_source": "os.wait4",
            "wall_source": "controller_monotonic_observed",
            "exit_code": 0,
            "pid": pid,
            "rss_unit": "bytes",
            "native": {
                "wall_seconds": 1.0,
                "user_seconds": 0.1,
                "system_seconds": 0.0,
                "rss_bytes": 10,
            },
        }

    record = {
        "schema": "topolab.v2.m2-native-rss-exit-assurance.v1",
        "status": "PENDING_POSTEXIT",
        "role": "synthetic-r-io",
        "argv": ["new-public-tool"],
        "platform": "darwin",
        "software_only": True,
        "scientific_resource_admission": "NOT_RUN",
        "controller_complete_exit": "UNKNOWN_PENDING_OUTER_PROFILE",
        "exit_code": 0,
        "software_result": "PUBLIC_COMMAND_EXIT_OBSERVED",
        "cleanup": {"group_gone": True, "leader_exit": 0},
        "ps_rss_unit": "KiB*1024",
        "native_rss_unit": "bytes",
        "profile_sha256": checker.digest(profile),
        "log_sha256": checker.digest(b""),
        "native": {
            "wall_seconds": 1.0,
            "user_seconds": 0.1,
            "system_seconds": 0.0,
            "rss_bytes": 100,
        },
        "limit_bytes": 4294967296,
        "observed_outer_wall_seconds": 1.2,
        "timeout_seconds": 100,
        "target_sample_interval_seconds": 0.5,
        "controller_rss_peak_bytes": 50,
        "pid": 10,
        "timer_native_exit": timer(10),
        "helpers": [
            {
                "profile": "sampler-0.time",
                "role": "rss-sampler-0",
                "profile_sha256": checker.digest(sampler),
                "exit_code": 0,
                "problem": None,
                "cleanup": {"group_gone": True, "leader_exit": 0},
                "pid": 20,
                "native": {
                    "wall_seconds": 0.02,
                    "user_seconds": 0.01,
                    "system_seconds": 0.0,
                    "rss_bytes": 20,
                },
                "timer_native_exit": timer(20),
            }
        ],
        "samples": [
            {
                "offset_seconds": 0.1,
                "actual_interval_seconds": None,
                "controller_rss_bytes": 50,
                "group_plus_controller_rss_bytes": 150,
                "roles": [
                    {"pid": 10, "parent": 1, "pgid": 10, "rss_bytes": 10},
                    {"pid": 11, "parent": 10, "pgid": 10, "rss_bytes": 90},
                ],
            }
        ],
        "native_plus_controller_and_sampler_rss_bytes": 190,
        "escaped_group_cleanup": [],
    }
    return record, profile, {"sampler-0.time": sampler}


def test_resource_reconciliation_requires_outer_exit_and_cost_closure() -> None:
    record, profile, helpers = resource_subject()
    result = checker.audit_native_record(
        record,
        profile=profile,
        log=b"",
        helper_profiles=helpers,
        expected_role="synthetic-r-io",
        expected_argv=["new-public-tool"],
        platform="darwin",
    )
    assert result["inner_empirical_RSS_bytes"] == 190
    assert result["inner_minimum_charge_seconds"] == 11.2
    assert result["outer_timer_supervisor_exits_and_full_role_cost"] == "CALLER_MUST_CLOSE"
    assert result["B_C_admission"] is False


@pytest.mark.parametrize("field", ["native", "units", "timer", "helper", "sum", "exit", "escape"])
def test_resource_forgery_cannot_be_hidden_by_PASS(field: str) -> None:
    record, profile, helpers = resource_subject()
    if field == "native":
        record["native"]["rss_bytes"] = 1
    elif field == "units":
        record["ps_rss_unit"] = "bytes"
    elif field == "timer":
        record["timer_native_exit"]["exit_code"] = 1
    elif field == "helper":
        helpers = {}
    elif field == "sum":
        record["samples"][0]["group_plus_controller_rss_bytes"] = 1
    elif field == "exit":
        record["cleanup"]["group_gone"] = None
    else:
        record["samples"][0]["roles"][1]["pgid"] = 99
    with pytest.raises(ValueError):
        checker.audit_native_record(
            record,
            profile=profile,
            log=b"",
            helper_profiles=helpers,
            expected_role="synthetic-r-io",
            expected_argv=["new-public-tool"],
            platform="darwin",
        )


def test_native_profile_GNU_units_and_missing_identity() -> None:
    parsed = checker.native_profile(b"TOPOLAB_NATIVE 0.1 0.0 0.0 20\n", "linux")
    assert parsed["rss_bytes"] == 20480
    with pytest.raises(ValueError):
        checker.native_profile(b"no native profile", "darwin")


def full_v2_subject():  # type: ignore[no-untyped-def]
    pending = {
        "execution_identity": checker.EXECUTION_V2,
        "role": "independent-public-check",
        "plan_sha256": "a" * 64,
        "frozen_FULL_seconds": 120,
        "clock_domain": checker.CLOCK_V2,
        "clock_resolution_seconds": 0.001,
        "actor_activation_UTC_seconds": 1000.0,
        "actor_window_seconds": 2700,
        "actor_deadlines_UTC": {
            "exporter": "1970-01-01T01:01:40.000Z",
            "independent": "1970-01-01T01:01:40.000Z",
        },
        "external_argv": [["new-supervisor"], ["new-finalizer"]],
    }
    completion = dict(
        pending,
        status="PENDING_EXTERNAL_EXIT",
        pending_sha256=checker.digest(checker.canonical(pending)),
        cleanup={"group_gone": True},
        final_serializer_pid=102,
        resource_components=[
            {
                "pid": 101,
                "kind": "self_high_water",
                "statistics_source": "resource.getrusage",
                "rss_unit": "bytes",
                "phases": ["preflush", "postflush"],
                "samples_bytes": [200, 210],
            },
            {
                "pid": 102,
                "kind": "self_high_water",
                "statistics_source": "resource.getrusage",
                "rss_unit": "bytes",
                "phases": ["preflush", "postflush"],
                "samples_bytes": [100, 150],
            },
        ],
    )
    events = [
        {
            "event_id": "raw-observed-1",
            "clock_domain": checker.CLOCK_V2,
            "start_seconds": 1000.0,
            "end_seconds": 1007.015,
            "wall_seconds": 7.014,
            "argv": ["new-supervisor"],
            "exit_code": 0,
            "complete": True,
        },
        {
            "event_id": "raw-observed-2",
            "clock_domain": checker.CLOCK_V2,
            "start_seconds": 1109.118,
            "end_seconds": 1109.224,
            "wall_seconds": 0.106,
            "argv": ["new-finalizer"],
            "exit_code": 0,
            "complete": True,
        },
    ]
    record, profile, helpers = resource_subject()
    inner = {
        "record": record,
        "profile": profile,
        "log": b"",
        "helper_profiles": helpers,
        "expected_role": "synthetic-r-io",
        "expected_argv": ["new-public-tool"],
        "platform": "darwin",
    }
    return pending, completion, events, inner


def full_v2_audit(pending, completion, events, inner):  # type: ignore[no-untyped-def]
    return checker.audit_full_role_v2(
        pending, completion, raw_tool_events=events,
        expected_role="independent-public-check", expected_plan_sha256="a" * 64,
        inner_evidence=inner,
    )


def test_new_FULL_retains_complete_disjoint_wall_and_same_process_peak() -> None:
    pending, completion, events, inner = full_v2_subject()
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "PASS_R_V3_FULL_ROLE"
    assert result["whole_wall_seconds"] == pytest.approx(109.224)
    assert result["frozen_FULL_seconds"] == 120
    assert result["known_cost_lower_bound_seconds"] == 120
    assert result["RSS_envelope_bytes"] == 210 + 150 + 190
    assert result["source_successor_admitted"] is False
    assert result["B_C_admission"] is False


@pytest.mark.parametrize("damage", [
    "missing_activation", "submillisecond", "window", "deadline", "completion", "late_event",
])
def test_new_readiness_window_is_bound_to_complete_actual_role(damage: str) -> None:
    pending, completion, events, inner = full_v2_subject()
    if damage == "missing_activation":
        pending.pop("actor_activation_UTC_seconds")
    elif damage == "submillisecond":
        pending["actor_activation_UTC_seconds"] = 1000.0001
    elif damage == "window":
        pending["actor_window_seconds"] = 2701
    elif damage == "deadline":
        pending["actor_deadlines_UTC"]["independent"] = "1970-01-01T01:01:41.000Z"
    elif damage == "completion":
        completion["actor_activation_UTC_seconds"] = 1001.0
    else:
        for event in events:
            event["start_seconds"] += 3000
            event["end_seconds"] += 3000
    completion["pending_sha256"] = checker.digest(checker.canonical(pending))
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["RSS_envelope_bytes"] == 550
    assert result["source_successor_admitted"] is False


@pytest.mark.parametrize("last_end,accepted", [(1110.0, True), (1110.0001, False)])
def test_complete_outer_plus_ten_exact_and_just_over_cap(last_end: float, accepted: bool) -> None:
    pending, completion, events, inner = full_v2_subject()
    events[-1]["end_seconds"] = last_end
    result = full_v2_audit(pending, completion, events, inner)
    assert result["full_role_evidence_accepted"] is accepted
    if not accepted:
        assert result["known_cost_lower_bound_seconds"] == 121


@pytest.mark.parametrize("damage", [
    "old20", "old_identity", "final_exit", "missing_exit", "clock", "missing_RSS",
    "inner_only", "changed_plan", "changed_pending", "wrong_argv", "cleanup",
])
def test_full_role_faults_close_suffix_and_preserve_available_peaks(damage: str) -> None:
    pending, completion, events, inner = full_v2_subject()
    if damage == "old20":
        pending["frozen_FULL_seconds"] = completion["frozen_FULL_seconds"] = 20
    elif damage == "old_identity":
        pending["execution_identity"] = completion["execution_identity"] = "v1"
    elif damage == "final_exit":
        events[-1]["exit_code"] = 1
    elif damage == "missing_exit":
        events[-1]["exit_code"] = None
    elif damage == "clock":
        events[-1]["end_seconds"] = 999
    elif damage == "missing_RSS":
        completion["resource_components"].pop()
    elif damage == "inner_only":
        events.clear()
    elif damage == "changed_plan":
        completion["plan_sha256"] = "b" * 64
    elif damage == "changed_pending":
        completion["pending_sha256"] = "b" * 64
    elif damage == "wrong_argv":
        events[-1]["argv"] = ["unregistered-glue"]
    else:
        completion["cleanup"]["group_gone"] = None
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["source_successor_admitted"] is False
    if damage == "final_exit":
        assert result["RSS_envelope_bytes"] == 550
        assert result["actual_exit_codes"][-1] == 1


def test_failed_native_exit_keeps_own_available_peak_before_rejection() -> None:
    _, completion, _, inner = full_v2_subject()
    record = {
        "statistics_source": "os.wait4", "wall_source": "controller_monotonic_observed",
        "pid": 103, "rss_unit": "bytes", "exit_code": 1,
        "native": {"wall_seconds": 0.1, "user_seconds": 0.0, "system_seconds": 0.0,
                   "rss_bytes": 250},
    }
    completion["resource_components"].append(
        {"pid": 103, "kind": "wait4", "platform": "darwin", "record": record}
    )
    result = checker.audit_v2_resource_components(completion, inner_evidence=inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["RSS_components_bytes"]["103"] == 250
    assert result["RSS_envelope_bytes"] == 800


def test_outer_native_profile_and_wait4_are_independently_parsed_and_added() -> None:
    _, completion, _, inner = full_v2_subject()
    profile = b"0.1 real 0.0 user 0.0 sys\n180 maximum resident set size\n"
    completion["resource_components"].extend([
        {
            "pid": 101, "kind": "native_profile", "profile": "outer.time",
            "profile_sha256": checker.digest(profile), "platform": "darwin",
            "actual_exit_code": 0,
        },
        {
            "pid": 103, "kind": "wait4", "platform": "darwin",
            "record": {
                "statistics_source": "os.wait4",
                "wall_source": "controller_monotonic_observed", "pid": 103,
                "rss_unit": "bytes", "exit_code": 0,
                "native": {"wall_seconds": 0.1, "user_seconds": 0.0,
                           "system_seconds": 0.0, "rss_bytes": 250},
            },
        },
    ])
    result = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, native_profiles={"outer.time": profile},
    )
    assert result["status"] == "PENDING_EXTERNAL_EXIT"
    assert result["RSS_envelope_bytes"] == 210 + 150 + 250 + 190
    assert result["RSS_components_bytes"]["101"] == 210  # Same supervisor, not double counted.
    completion["resource_components"][-2]["profile_sha256"] = "b" * 64
    rejected = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, native_profiles={"outer.time": profile},
    )
    assert rejected["status"] == "STOP_NO_RETRY"
    assert "profile hash" in rejected["reason"]


@pytest.mark.parametrize("excess,accepted", [(0.001, True), (0.001001, False)])
def test_tool_wall_display_resolution_is_frozen_not_a_cap_slack(
    excess: float, accepted: bool,
) -> None:
    pending, completion, events, inner = full_v2_subject()
    events[0]["wall_seconds"] = events[0]["end_seconds"] - events[0]["start_seconds"] + excess
    result = full_v2_audit(pending, completion, events, inner)
    assert result["full_role_evidence_accepted"] is accepted


def test_arbitrary_larger_clock_resolution_cannot_loosen_outer_checks() -> None:
    pending, completion, events, inner = full_v2_subject()
    pending["clock_resolution_seconds"] = completion["clock_resolution_seconds"] = 1.0
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert "resolution" in result["reason"]


def test_nonfinite_raw_clock_still_retains_failure_and_RSS_evidence() -> None:
    pending, completion, events, inner = full_v2_subject()
    events[-1]["end_seconds"] = float("nan")
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["RSS_envelope_bytes"] == 550
    assert result["raw_tool_event_ids_and_hashes"][-1]["sha256"] is None


def test_content_snapshot_guard_retains_literal_frozen_scope() -> None:
    contract = (
        Path(__file__).parents[1]
        / "docs/planning/p17_m2_input_export_preparation_proposal.json"
    )
    assert checker.digest(contract.read_bytes()) == checker.CONTENT_CONTRACT_SHA256


def test_independent_new_backup_compares_complete_bytes_including_empty_log(tmp_path: Path) -> None:
    root, backup = tmp_path / "new-prefix", tmp_path / "new-backup"
    for folder in (root, backup):
        folder.mkdir()
        (folder / "new-view.json").write_bytes(b'{"new":true}\n')
        (folder / "empty-native.log").write_bytes(b"")
    result = checker.audit_new_backup(root, backup, public_fixture=True)
    assert result["status"] == "PASS_INDEPENDENT_NEW_BACKUP"
    assert result["member_count"] == 2
    assert result["total_bytes"] == len(b'{"new":true}\n')
    assert result["old_input_reads"] == 0
    (backup / "new-view.json").write_bytes(b'{"new":false}')
    rejected = checker.audit_new_backup(root, backup, public_fixture=True)
    assert rejected["status"] == "STOP_NO_RETRY"
    assert "bytes/hash" in rejected["reason"]


@pytest.mark.parametrize("damage", ["extra", "symlink", "ancestor_symlink"])
def test_new_backup_rejects_extra_or_symlink_member(tmp_path: Path, damage: str) -> None:
    root, backup = tmp_path / "new-prefix", tmp_path / "new-backup"
    for folder in (root, backup):
        folder.mkdir()
        (folder / "data.json").write_bytes(b"{}\n")
    if damage == "extra":
        (backup / "extra.json").write_bytes(b"{}\n")
    elif damage == "symlink":
        (backup / "data.json").unlink()
        (backup / "data.json").symlink_to(root / "data.json")
    else:
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        root = alias
    result = checker.audit_new_backup(root, backup, public_fixture=True)
    assert result["status"] == "STOP_NO_RETRY"


def test_new_backup_exclusion_is_literal_and_preserves_stable_prefix(tmp_path: Path) -> None:
    root, backup = tmp_path / "new-prefix", tmp_path / "new-backup"
    for folder in (root, backup):
        (folder / "receipts").mkdir(parents=True)
        (folder / "stable.json").write_bytes(b"{}\n")
    (root / "receipts/shared-closeout-controller.log").write_bytes(b"active-new-log")
    result = checker.audit_new_backup(
        root, backup, public_fixture=True, excluded_prefixes=("receipts/shared-closeout",),
    )
    assert result["status"] == "PASS_INDEPENDENT_NEW_BACKUP"
    assert result["member_count"] == 1


@pytest.mark.parametrize("version", (1, 2))
def test_backup_refuses_closed_identity_before_stat(
    monkeypatch: pytest.MonkeyPatch, version: int,
) -> None:
    def forbidden_stat(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("no old path may be stat'ed")

    monkeypatch.setattr(Path, "lstat", forbidden_stat)
    old = checker.AUTHORIZED_DATA_ROOT / f"p17-m2-input-export-preparation-v{version}"
    result = checker.audit_new_backup(old, old.with_name(old.name + "-independent-backup"))
    assert result["status"] == "STOP_NO_RETRY"
    assert "literal NEW v3" in result["reason"]
    result = checker.audit_new_backup(old, old.with_name(old.name + "-copy"), public_fixture=True)
    assert result["status"] == "STOP_NO_RETRY"
    assert "public fixture cannot open DATA" in result["reason"]


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
def test_trusted_JS_boundary_matches_raw_gap_cap_and_actual_exit() -> None:
    pending, completion, events, inner = full_v2_subject()
    resources = checker.audit_v2_resource_components(completion, inner_evidence=inner)
    cases = []
    for damage in (
        "none", "cap", "exit", "pending", "resource_identity", "missing_exit", "wrong_clock",
    ):
        row = deepcopy([pending, completion, events, resources, completion["pending_sha256"]])
        if damage == "cap":
            row[2][-1]["end_seconds"] = 1110.001
        elif damage == "exit":
            row[2][-1]["exit_code"] = 1
        elif damage == "pending":
            row[4] = "b" * 64
        elif damage == "resource_identity":
            row[3]["role"] = "exporter-r1"
        elif damage == "missing_exit":
            row[2][-1]["exit_code"] = None
        elif damage == "wrong_clock":
            for event in row[2]:
                event["clock_domain"] = "unregistered-derived-clock"
        cases.append(row)
    script = Path(__file__).parents[1] / "scripts/p17_m2_input_export_dispatch.js"
    command = (
        "const fs=require('fs');const {finishExternal}=require(process.argv[1]);"
        "console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8'))"
        ".map(args=>finishExternal(...args))))"
    )
    observed = subprocess.run(
        ["node", "-e", command, str(script)], input=json.dumps(cases),
        text=True, capture_output=True, check=True,
    )
    results = json.loads(observed.stdout)
    assert results[0]["whole_wall_seconds"] == pytest.approx(109.224)
    assert results[0]["status"] == "PASS_R_V3_FULL_ROLE"
    assert all(result["status"] == "STOP_NO_RETRY" for result in results[1:])
    assert results[2]["RSS_envelope_bytes"] == 550


@pytest.mark.parametrize("damage", ["failed_completion", "missing_status", "missing_completion"])
def test_failure_recording_valid_raw_span_survives_internal_failure(damage: str) -> None:
    """Raw endpoints are the oracle, not an internal completion's PASS flag."""
    pending, completion, events, inner = full_v2_subject()
    events[-1].update(start_seconds=1017.0, end_seconds=1017.25, wall_seconds=0.25,
                      exit_code=1)
    if damage == "failed_completion":
        completion["status"] = "FAILED_INTERNAL_COMPLETION"
    elif damage == "missing_status":
        completion.pop("status")
    else:
        completion = {}
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["T0"] == 1000.0 and result["T1"] == 1017.25
    assert result["whole_wall_seconds"] == 17.25
    assert result["actual_exit_codes"] == [0, 1]
    assert result["known_cost_lower_bound_seconds"] == 120
    assert result["full_role_evidence_accepted"] is False
    assert result["source_successor_admitted"] is False
    assert result["B_C_admission"] is False
    if damage == "missing_completion":
        assert result["RSS_envelope_bytes"] is None


def test_failure_recording_overrun_is_not_lost_when_internal_completion_failed() -> None:
    pending, completion, events, inner = full_v2_subject()
    completion["status"] = "FAILED_INTERNAL_COMPLETION"
    events[-1].update(end_seconds=1110.001, exit_code=1)
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["whole_wall_seconds"] == pytest.approx(110.001)
    assert result["known_cost_lower_bound_seconds"] == 121
    assert result["actual_exit_codes"] == [0, 1]


@pytest.mark.parametrize("damage", ["clock", "order", "duplicate", "missing_event"])
def test_failure_recording_invalid_stream_has_no_certified_whole_span(damage: str) -> None:
    pending, completion, events, inner = full_v2_subject()
    if damage == "clock":
        events[-1]["clock_domain"] = "untrusted-other-clock"
    elif damage == "order":
        events[-1]["start_seconds"] = 1001.0
    elif damage == "duplicate":
        events[-1]["event_id"] = events[0]["event_id"]
    else:
        events.pop()
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["whole_wall_seconds"] is None
    assert result["full_role_evidence_accepted"] is False


def test_failure_recording_missing_final_exit_preserves_separate_clock_fact() -> None:
    pending, completion, events, inner = full_v2_subject()
    events[-1].update(start_seconds=1017.0, end_seconds=1017.25, wall_seconds=0.25,
                      exit_code=None)
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["whole_wall_seconds"] == 17.25
    assert result["actual_exit_codes"] == [0, None]
    assert result["full_role_evidence_accepted"] is False


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
@pytest.mark.parametrize("damage", [
    "failed_completion", "missing_status", "missing_completion", "payload_exit",
    "missing_exit", "overrun", "bad_clock",
])
def test_failure_recording_JS_Python_retains_same_independent_facts(damage: str) -> None:
    pending, completion, events, inner = full_v2_subject()
    events[-1].update(start_seconds=1017.0, end_seconds=1017.25, wall_seconds=0.25)
    if damage == "failed_completion":
        completion["status"] = "FAILED_INTERNAL_COMPLETION"
    elif damage == "missing_status":
        completion.pop("status")
    elif damage == "missing_completion":
        completion = {}
    elif damage == "payload_exit":
        events[0]["exit_code"] = 1
    elif damage == "missing_exit":
        events[-1]["exit_code"] = None
    elif damage == "overrun":
        completion["status"] = "FAILED_INTERNAL_COMPLETION"
        events[-1]["end_seconds"] = 1110.001
    else:
        events[-1]["clock_domain"] = "not-the-frozen-external-clock"
    resources = checker.audit_v2_resource_components(completion, inner_evidence=inner)
    script = Path(__file__).parents[1] / "scripts/p17_m2_input_export_dispatch.js"
    command = (
        "const fs=require('fs');const {finishExternal}=require(process.argv[1]);"
        "console.log(JSON.stringify(finishExternal(...JSON.parse(fs.readFileSync(0,'utf8')))))"
    )
    observed = subprocess.run(
        ["node", "-e", command, str(script)],
        input=json.dumps([pending, completion, events, resources,
                          checker.digest(checker.canonical(pending))]),
        text=True, capture_output=True, check=True,
    )
    js = json.loads(observed.stdout)
    py = full_v2_audit(pending, completion, events, inner)
    expected_whole = (None if damage == "bad_clock" else
                      pytest.approx(110.001) if damage == "overrun" else 17.25)
    expected_charge = 121 if damage == "overrun" else 120
    for result in (js, py):
        assert result["status"] == "STOP_NO_RETRY"
        assert result["whole_wall_seconds"] == expected_whole
        assert result["known_cost_lower_bound_seconds"] == expected_charge
        assert result["actual_exit_codes"] == [
            1 if damage == "payload_exit" else 0,
            None if damage == "missing_exit" else 0,
        ]
        assert result["full_role_evidence_accepted"] is False
        assert result["source_successor_admitted"] is False
    for key in ("status", "whole_wall_seconds", "known_cost_lower_bound_seconds",
                "actual_exit_codes", "RSS_envelope_bytes", "full_role_evidence_accepted"):
        assert js[key] == py[key], key


def failure_recording_subject(*, failed: bool = False):  # type: ignore[no-untyped-def]
    """Original tiny F-only values; no historical execution receipt is replayed."""
    pending, completion, events, inner = full_v2_subject()
    identity = "topolab.v2.p17-m2-input-failure-diagnostic-repair.v1"
    for item in (pending, completion):
        item.update(execution_identity=identity, role="public-fixture")
    completion["pending_sha256"] = checker.digest(checker.canonical(pending))
    completion["domain_status"] = "STOP" if failed else "PASS_PUBLIC_SOFTWARE"
    events[-1].update(start_seconds=1017.0, end_seconds=1017.25, wall_seconds=0.25)
    inner["record"]["role"] = inner["expected_role"] = "new-public-payload"
    inner["record"]["controller_pid"] = 103
    profile = failure_recording_profiles()["F-outer-native"]
    completion["supervisor_pid"] = 101
    completion["resource_components"][:0] = [
        {"pid": 103, "kind": "native_profile", "profile": "F-outer-native",
         "profile_sha256": checker.digest(profile), "platform": "darwin",
         "actual_exit_code": 1 if failed else 0},
        {"pid": 104, "kind": "wait4", "platform": "darwin", "record": {
            "statistics_source": "os.wait4", "wall_source": "controller_monotonic_observed",
            "pid": 104, "rss_unit": "bytes", "exit_code": 1 if failed else 0,
            "native": {"wall_seconds": 1.2, "user_seconds": 0.1,
                       "system_seconds": 0.0, "rss_bytes": 250},
        }},
    ]
    if failed:
        inner["record"]["exit_code"] = 1
        inner["record"]["software_result"] = "FAIL_PUBLIC_COMMAND"
        inner["record"]["cleanup"]["leader_exit"] = 1
        inner["record"]["timer_native_exit"]["exit_code"] = 1
        events[0]["exit_code"] = 1
        completion["primary_failure"] = {
            "stage": "payload", "type": "ValueError", "reason": "new public expected failure",
        }
    return pending, completion, events, inner


def failure_recording_profiles() -> dict[str, bytes]:
    return {"F-outer-native": b"0.1 real 0.0 user 0.0 sys\n180 maximum resident set size\n"}


def failure_recording_audit(pending, completion, events, inner):  # type: ignore[no-untyped-def]
    return checker.audit_full_role_f(
        pending, completion=completion, raw_tool_events=events,
        expected_role="public-fixture", expected_plan_sha256="a" * 64,
        expected_pending_sha256=checker.digest(checker.canonical(pending)),
        inner_evidence=inner, native_profiles=failure_recording_profiles(),
    )


@pytest.mark.parametrize("failed", [False, True])
def test_F_separates_complete_measurement_from_payload_outcome(failed: bool) -> None:
    pending, completion, events, inner = failure_recording_subject(failed=failed)
    result = failure_recording_audit(pending, completion, events, inner)
    assert result["whole_wall_seconds"] == 17.25
    assert result["known_cost_lower_bound_seconds"] == 120
    assert result["RSS_envelope_bytes"] == 180 + 250 + 210 + 150 + 190
    assert result["evidence_complete"] is True
    assert result["missing_evidence_cost"] is None
    assert result["domain_status"] == ("STOP" if failed else "PASS_PUBLIC_SOFTWARE")
    assert result["actual_exit_codes"] == [1 if failed else 0, 0]
    assert result["source_successor_admitted"] is False
    assert result["B_C_admission"] is False
    if failed:
        assert result["status"] == "STOP_NO_RETRY"
        assert result["full_role_evidence_accepted"] is False
        assert result["primary_failure"] == completion["primary_failure"]


def test_F_independent_inner_charge_is_retained_even_when_completion_failed() -> None:
    pending, completion, events, inner = failure_recording_subject(failed=True)
    inner["record"]["observed_outer_wall_seconds"] = 130.0
    inner["record"]["timeout_seconds"] = 200.0
    completion["status"] = "FAILED_INTERNAL_COMPLETION"
    result = failure_recording_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["whole_wall_seconds"] == 17.25
    assert result["inner_minimum_charge_seconds"] == 140.0
    assert result["known_cost_lower_bound_seconds"] == 140
    assert result["evidence_complete"] is False
    assert result["primary_failure"] == completion["primary_failure"]


def test_F_primary_success_flag_cannot_hide_observed_failed_payload() -> None:
    pending, completion, events, inner = failure_recording_subject(failed=True)
    completion["domain_status"] = "PASS_PUBLIC_SOFTWARE"
    events[0]["exit_code"] = 0
    completion["resource_components"][0]["actual_exit_code"] = 0
    completion["resource_components"][1]["record"]["exit_code"] = 0
    result = failure_recording_audit(pending, completion, events, inner)
    assert result["domain_status"] == "STOP"
    assert result["status"] == "STOP_NO_RETRY"
    assert result["full_role_evidence_accepted"] is False
    assert result["source_successor_admitted"] is False


def test_F_resource_failure_mode_cannot_upgrade_old_R_measurement() -> None:
    _, completion, _, inner = full_v2_subject()
    inner["record"]["exit_code"] = 1
    inner["record"]["software_result"] = "FAIL_PUBLIC_COMMAND"
    inner["record"]["cleanup"]["leader_exit"] = 1
    inner["record"]["timer_native_exit"]["exit_code"] = 1
    result = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, failure_recording=True,
    )
    assert result["status"] == "STOP_NO_RETRY"


def test_F_secondary_recording_failure_does_not_replace_payload_cause() -> None:
    pending, completion, events, inner = failure_recording_subject(failed=True)
    completion["status"] = "FAILED_INTERNAL_COMPLETION"
    defect = {"stage": "public-serializer", "type": "OSError",
              "reason": "new fixture recording defect"}
    completion["secondary_failures"] = [defect]
    result = failure_recording_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["primary_failure"] == completion["primary_failure"]
    assert defect in result["secondary_failures"]
    assert result["whole_wall_seconds"] == 17.25


@pytest.mark.parametrize("damage", ["old_identity", "R_role", "increased_FULL", "pending_hash"])
def test_F_is_exact_public_identity_and_cannot_admit_R(damage: str) -> None:
    pending, completion, events, inner = failure_recording_subject()
    pending_sha = checker.digest(checker.canonical(pending))
    if damage == "old_identity":
        pending["execution_identity"] = completion["execution_identity"] = checker.EXECUTION_V2
    elif damage == "R_role":
        pending["role"] = completion["role"] = "exporter-r0"
    elif damage == "increased_FULL":
        pending["frozen_FULL_seconds"] = completion["frozen_FULL_seconds"] = 121
    else:
        pending_sha = "b" * 64
    completion["pending_sha256"] = checker.digest(checker.canonical(pending))
    result = checker.audit_full_role_f(
        pending, completion=completion, raw_tool_events=events,
        expected_role="public-fixture", expected_plan_sha256="a" * 64,
        expected_pending_sha256=pending_sha, inner_evidence=inner,
        native_profiles=failure_recording_profiles(),
    )
    assert result["status"] == "STOP_NO_RETRY"
    assert result["evidence_complete"] is False
    assert result["source_successor_admitted"] is False


@pytest.mark.parametrize("damage", [
    "helper_missing", "helper_exit", "serializer_RSS", "actual_exit", "cleanup",
    "inner_cleanup", "inner_RSS", "overrun", "completion", "event_order",
    "outer_native", "outer_timer", "supervisor_RSS",
])
def test_F_missing_mandatory_recording_component_cannot_become_complete(damage: str) -> None:
    pending, completion, events, inner = failure_recording_subject(failed=True)
    if damage == "helper_missing":
        inner["helper_profiles"] = {}
    elif damage == "helper_exit":
        inner["record"]["helpers"][0]["exit_code"] = 1
    elif damage == "serializer_RSS":
        completion["resource_components"].pop()
    elif damage == "actual_exit":
        events[-1]["exit_code"] = None
    elif damage == "cleanup":
        completion["cleanup"]["group_gone"] = None
    elif damage == "inner_cleanup":
        inner["record"]["cleanup"]["group_gone"] = None
    elif damage == "inner_RSS":
        inner["record"]["native"]["rss_bytes"] = 0
    elif damage == "overrun":
        events[-1]["end_seconds"] = 1110.001
    elif damage == "completion":
        completion["status"] = "FAILED_INTERNAL_COMPLETION"
        completion["secondary_failures"] = [{"stage": "new-public-finalizer", "reason": "fixture"}]
    elif damage == "outer_native":
        completion["resource_components"].pop(0)
    elif damage == "outer_timer":
        completion["resource_components"].pop(1)
    elif damage == "supervisor_RSS":
        completion["resource_components"].pop(2)
    else:
        events[-1]["start_seconds"] = 1001.0
    result = failure_recording_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["evidence_complete"] is False
    assert result["domain_status"] == "STOP"
    assert result["missing_evidence_cost"] == "UNKNOWN_NOT_ZERO"
    assert result["source_successor_admitted"] is False
    if damage != "event_order":
        assert result["whole_wall_seconds"] == pytest.approx(
            110.001 if damage == "overrun" else 17.25
        )
    assert result["known_cost_lower_bound_seconds"] == (121 if damage == "overrun" else 120)
    assert result["primary_failure"] == completion["primary_failure"]


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
@pytest.mark.parametrize("damage", [
    "none", "helper", "completion", "exit", "cleanup", "cap", "hidden_payload",
])
def test_F_JS_Python_agree_without_a_primary_PASS_oracle(damage: str) -> None:
    pending, completion, events, inner = failure_recording_subject(failed=True)
    if damage == "helper":
        inner["helper_profiles"] = {}
    elif damage == "completion":
        completion["status"] = "FAILED_INTERNAL_COMPLETION"
        completion["secondary_failures"] = [{"stage": "new-public-finalizer", "reason": "fixture"}]
    elif damage == "exit":
        events[-1]["exit_code"] = None
    elif damage == "cleanup":
        completion["cleanup"]["group_gone"] = None
    elif damage == "cap":
        events[-1]["end_seconds"] = 1110.001
    elif damage == "hidden_payload":
        events[0]["exit_code"] = 0
        completion["domain_status"] = "PASS_PUBLIC_SOFTWARE"
        completion["resource_components"][0]["actual_exit_code"] = 0
        completion["resource_components"][1]["record"]["exit_code"] = 0
    resources = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, native_profiles=failure_recording_profiles(),
        failure_recording=True,
    )
    script = Path(__file__).parents[1] / "scripts/p17_m2_input_export_dispatch.js"
    command = (
        "const fs=require('fs');const {finishExternalF}=require(process.argv[1]);"
        "console.log(JSON.stringify(finishExternalF(...JSON.parse(fs.readFileSync(0,'utf8')))))"
    )
    observed = subprocess.run(
        ["node", "-e", command, str(script)],
        input=json.dumps([pending, completion, events, resources,
                          checker.digest(checker.canonical(pending))]),
        text=True, capture_output=True, check=True,
    )
    js = json.loads(observed.stdout)
    py = failure_recording_audit(pending, completion, events, inner)
    for result in (js, py):
        assert result["status"] == "STOP_NO_RETRY"
        assert result["domain_status"] == "STOP"
        assert result["evidence_complete"] is (damage in ("none", "hidden_payload"))
        assert result["whole_wall_seconds"] == pytest.approx(110.001 if damage == "cap" else 17.25)
        assert result["known_cost_lower_bound_seconds"] == (121 if damage == "cap" else 120)
        assert result["primary_failure"] == completion["primary_failure"]
        assert result["source_successor_admitted"] is False
        if damage == "completion":
            assert completion["secondary_failures"][0] in result["secondary_failures"]
    for key in ("status", "domain_status", "evidence_complete", "whole_wall_seconds",
                "known_cost_lower_bound_seconds", "actual_exit_codes", "RSS_envelope_bytes",
                "full_role_evidence_accepted", "primary_failure"):
        assert js[key] == py[key], key


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
def test_F_serializer_failure_keeps_component_truth_and_closes_full_packet() -> None:
    pending, completion, events, inner = failure_recording_subject(failed=True)
    completion["status"] = "FAILED_INTERNAL_COMPLETION"
    completion["secondary_failures"] = [
        {"stage": "completion", "type": "OSError", "reason": "new public serializer write"}
    ]
    events[-1]["exit_code"] = 1
    resources = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, native_profiles=failure_recording_profiles(),
        failure_recording=True,
    )
    assert resources["status"] == "PENDING_EXTERNAL_EXIT"
    assert resources["evidence_complete"] is True
    assert resources["RSS_envelope_bytes"] == 980
    script = Path(__file__).parents[1] / "scripts/p17_m2_input_export_dispatch.js"
    command = (
        "const fs=require('fs');const {finishExternalF}=require(process.argv[1]);"
        "console.log(JSON.stringify(finishExternalF(...JSON.parse(fs.readFileSync(0,'utf8')))))"
    )
    observed = subprocess.run(
        ["node", "-e", command, str(script)],
        input=json.dumps([pending, completion, events, resources,
                          checker.digest(checker.canonical(pending))]),
        text=True, capture_output=True, check=True,
    )
    js = json.loads(observed.stdout)
    py = failure_recording_audit(pending, completion, events, inner)
    for result in (js, py):
        assert result["status"] == "STOP_NO_RETRY"
        assert result["evidence_complete"] is False
        assert result["domain_status"] == "STOP"
        assert result["RSS_envelope_bytes"] == 980
        assert result["whole_wall_seconds"] == 17.25
        assert result["known_cost_lower_bound_seconds"] == 120
        assert result["actual_exit_codes"] == [1, 1]
        assert result["primary_failure"] == completion["primary_failure"]
        assert result["secondary_failures"] == completion["secondary_failures"]


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
@pytest.mark.parametrize("bad_event", [None, 5, "new malformed public event", {}])
def test_F_malformed_event_entry_emits_bounded_STOP(bad_event: object) -> None:
    pending, completion, _, inner = failure_recording_subject(failed=True)
    events = [bad_event]
    resources = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, native_profiles=failure_recording_profiles(),
        failure_recording=True,
    )
    script = Path(__file__).parents[1] / "scripts/p17_m2_input_export_dispatch.js"
    command = (
        "const fs=require('fs');const {finishExternalF}=require(process.argv[1]);"
        "console.log(JSON.stringify(finishExternalF(...JSON.parse(fs.readFileSync(0,'utf8')))))"
    )
    observed = subprocess.run(
        ["node", "-e", command, str(script)],
        input=json.dumps([pending, completion, events, resources,
                          checker.digest(checker.canonical(pending))]),
        text=True, capture_output=True, check=True,
    )
    js = json.loads(observed.stdout)
    py = failure_recording_audit(pending, completion, events, inner)
    for result in (js, py):
        assert result["status"] == "STOP_NO_RETRY"
        assert result["domain_status"] == "STOP"
        assert result["evidence_complete"] is False
        assert result["whole_wall_seconds"] is None
        assert result["actual_exit_codes"] == [None]
        assert result["known_cost_lower_bound_seconds"] == 120
        assert result["primary_failure"] == completion["primary_failure"]


def test_stable_reader_records_same_transaction_source_identity(tmp_path: Path) -> None:
    original = tmp_path / "new-public.json"
    original.write_bytes(b"{}\n")
    reader = checker.OnceReader(tmp_path, 1, 100, source_identity_checks=True)
    assert reader.read(original.name, 100) == b"{}\n"
    row = reader.observations[0]
    assert row["path"] == original.name
    assert row["byte_size"] == 3
    assert row["sha256"] == checker.digest(b"{}\n")
    assert row["declared"] == row["before"] == row["after"] == row["closing"]
    assert row["closing"] == checker.source_identity(original.stat())
    assert checker.compare_source_identities(
        reader.observations, checker.identity_sidecar(reader.observations), 1,
    ) > 10


@pytest.mark.parametrize("replacement", ["leaf", "ancestor"])
def test_stable_reader_closing_path_detects_same_byte_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replacement: str,
) -> None:
    parent = tmp_path / "source"
    parent.mkdir()
    original = parent / "original.json"
    original.write_bytes(b"{}\n")
    real_read = os.read
    changed = False

    def read_and_replace(fd: int, maximum: int) -> bytes:
        nonlocal changed
        raw = real_read(fd, maximum)
        if raw and not changed:
            changed = True
            if replacement == "leaf":
                original.rename(parent / "retained-original.json")
            else:
                parent.rename(tmp_path / "retained-original-directory")
                parent.mkdir()
            original.write_bytes(raw)
        return raw

    monkeypatch.setattr(os, "read", read_and_replace)
    reader = checker.OnceReader(tmp_path, 1, 100, source_identity_checks=True)
    with pytest.raises(ValueError, match="closing literal path"):
        reader.read("source/original.json", 100)
    facts = reader.failures[0]
    assert facts["execution_identity"] == checker.EXECUTION_STABLE
    assert facts["stage"] == "closing_path_identity"
    assert facts["returned_bytes"] == 3
    assert facts["before"] == facts["after"]
    assert facts["before"]["st_ino"] != facts["closing"]["st_ino"]
    assert "st_ino" in facts["changed_fields"]
    assert reader.observations == []
    assert reader.seen == {"source/original.json"}


@pytest.mark.parametrize("mutation", ["mtime", "size"])
def test_stable_reader_preserves_change_failure_and_read_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    original = tmp_path / "original.json"
    original.write_bytes(b"{}\n")
    before = original.stat()
    real_read = os.read
    changed = False

    def change_during_read(fd: int, maximum: int) -> bytes:
        nonlocal changed
        raw = real_read(fd, maximum)
        if raw and not changed:
            changed = True
            if mutation == "mtime":
                os.utime(original, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000))
            else:
                original.write_bytes(b"{\"new\":true}\n")
        return raw

    monkeypatch.setattr(os, "read", change_during_read)
    journal = tmp_path / "new-failure.jsonl"
    reader = checker.OnceReader(tmp_path, 1, 100, source_identity_checks=True, journal=journal)
    with pytest.raises(ValueError, match="changed during"):
        reader.read(original.name, 100)
    failure = reader.failures[0]
    assert failure["returned_bytes"] >= 3
    assert failure["stage"] == "after_read_identity"
    assert "st_mtime_ns" in failure["changed_fields"]
    if mutation == "size":
        assert "st_size" in failure["changed_fields"]
    assert checker.parse(journal.read_bytes()) == failure


def test_stable_reader_partial_read_failure_retains_actual_prefix_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    real_read = os.read
    calls = 0

    def partial_then_failure(fd: int, maximum: int) -> bytes:
        nonlocal calls
        calls += 1
        if calls == 1:
            return real_read(fd, 1)
        raise OSError("new public read failure")

    monkeypatch.setattr(os, "read", partial_then_failure)
    reader = checker.OnceReader(tmp_path, 1, 100, source_identity_checks=True)
    with pytest.raises(OSError, match="new public"):
        reader.read("original.json", 100)
    failure = reader.failures[0]
    assert failure["returned_bytes"] == 1
    assert failure["after"] is None and failure["closing"] is None
    assert failure["stage"] == "bounded_read"
    assert reader.table == []


@pytest.mark.parametrize("damage", ["missing", "extra", "inode", "closing", "duplicate"])
def test_cross_author_source_identity_sidecar_cannot_accept_changed_original(
    tmp_path: Path, damage: str,
) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    reader = checker.OnceReader(tmp_path, 1, 100, source_identity_checks=True)
    reader.read("original.json", 100)
    producer = deepcopy(checker.identity_sidecar(reader.observations))
    if damage == "missing":
        producer["rows"] = []
    elif damage == "extra":
        producer["rows"][0]["extra"] = True
    elif damage == "inode":
        # Equal bytes and SHA cannot hide cross-author replacement.
        for stage in ("declared", "before", "after", "closing"):
            producer["rows"][0][stage]["st_ino"] += 1
    elif damage == "closing":
        producer["rows"][0]["closing"] = None
    else:
        producer["rows"].append(deepcopy(producer["rows"][0]))
    with pytest.raises(ValueError):
        checker.compare_source_identities(reader.observations, producer, 1)


def stable_recording_subject(*, role="independent-public-check", failed=False):  # type: ignore[no-untyped-def]
    pending, completion, events, inner = failure_recording_subject(failed=failed)
    for record in (pending, completion):
        record.update(
            execution_identity=checker.EXECUTION_STABLE,
            role=role, frozen_FULL_seconds=checker.FULL_STABLE[role],
            actor_window_seconds=4500,
            actor_deadlines_UTC={
                "exporter": "1970-01-01T01:31:40.000Z",
                "independent": "1970-01-01T01:31:40.000Z",
            },
        )
    completion["pending_sha256"] = checker.digest(checker.canonical(pending))
    completion["domain_status"] = "STOP" if failed else "PASS"
    cleanup = {"group_gone": True, "leader_exit": 1 if failed else 0,
               "initial_group_gone": False, "final_group_gone": True,
               "signals": ["SIGTERM"], "observation_limit_seconds": 5,
               "post_signal_observation_seconds": 0.02, "observation_limit_exceeded": False,
               "observations": [{"elapsed_seconds": 0.0, "group_gone": False,
                                 "leader_exit": None},
                                {"elapsed_seconds": 0.02, "group_gone": True,
                                 "leader_exit": 1 if failed else 0}]}
    completion["cleanup"] = deepcopy(cleanup)
    inner["record"]["cleanup"] = deepcopy(cleanup)
    helper_cleanup = deepcopy(cleanup)
    helper_cleanup["leader_exit"] = helper_cleanup["observations"][-1]["leader_exit"] = 0
    inner["record"]["helpers"][0]["cleanup"] = helper_cleanup
    return pending, completion, events, inner


def stable_recording_audit(pending, completion, events, inner):  # type: ignore[no-untyped-def]
    return checker.audit_full_role_stable(
        pending, completion=completion, raw_tool_events=events,
        expected_role=pending["role"], expected_plan_sha256="a" * 64,
        expected_pending_sha256=checker.digest(checker.canonical(pending)),
        inner_evidence=inner, native_profiles=failure_recording_profiles(),
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
@pytest.mark.parametrize("fault", ["none", "late_event", "late_close"])
def test_stable_shared_closeout_retains_packet_after_frontier_failure(fault: str) -> None:
    # Exercise the real six-role dispatcher; only time and external tool returns are synthetic.
    subjects = {}
    for role in checker.FULL_STABLE:
        pending, completion, _, inner = stable_recording_subject(role=role)
        pending_sha = checker.digest(checker.canonical(pending))
        resources = checker.audit_v2_resource_components(
            completion, inner_evidence=inner, native_profiles=failure_recording_profiles(),
            execution_identity=checker.EXECUTION_STABLE, failure_recording=True,
        )
        subjects[role] = {"pending": pending, "pending_sha": pending_sha,
                          "completion": completion, "resourceEvidence": resources,
                          "full_collector_record": {
                              "path": f"receipts/{role}-final-wire-source.json",
                              "byte_size": 17, "sha256": "c" * 64}}
    command = r'''
const fs = require('fs'), vm = require('vm');
const subjects = JSON.parse(fs.readFileSync(0,'utf8')), fault = process.argv[2];
const state = new Map(), calls = [], packets = [];
let clock = 1000000, closing = 0;
const roles = Object.keys(subjects), first = subjects[roles[0]].pending;
const context = {...first, repository:'/NEW_PUBLIC_FIXTURE_ONLY', thread_environment:{},
  source_controls:{custodian:'/root'},
  FULL_caps_seconds:Object.fromEntries(roles.map(r=>[r,subjects[r].pending.frozen_FULL_seconds])),
  external_argv:Object.fromEntries(roles.map(r=>[r,subjects[r].pending.external_argv])),
  python_executable:'/NEW/python', output_root:'/NEW/output',
  final_helper_external_argv:['/NEW/python','-I',
    '/NEW_PUBLIC_FIXTURE_ONLY/scripts/p17_m2_input_export_control.py','final-helper','--r-stable',
    '--plan','/NEW/output/launch_plan.json','--plan-sha','<PLAN_SHA256>']};
const sandbox = {module:{exports:{}}, load:k=>state.get(k), store:(k,v)=>state.set(k,v),
  text:()=>{}, Date:class extends Date {static now(){
    if (closing && --closing===0 && fault==='late_close') clock=5500000;
    return ++clock;
  }}, tools:{exec_command:async args=>{
    const role=state.get('rstable-active-role'), final=calls.length%2===1;
    calls.push(args); clock+=2000;
    if(role==='shared-closeout' && final) {
      closing=2;
      if(fault==='late_event') clock=5500000;
    }
    return {output:JSON.stringify(final ? subjects[role] : {
      pending:subjects[role].pending, pending_sha256:subjects[role].pending_sha}),
      exit_code:0, wall_time_seconds:2};
  }}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),sandbox);
(async()=>{
  let error=null;
  try {for(const role of roles) packets.push(await sandbox.module.exports.dispatchRoleStable(
    context,role));} catch(e) {error=e.message;}
  const packet=state.get('rstable-packet-shared-closeout')??null, before=calls.length;
  let retryRefused=false, filingRefused=false;
  try {await sandbox.module.exports.dispatchRoleStable(context,'shared-closeout');}
  catch(e) {retryRefused=true;}
  if(fault!=='none') {
    try {await sandbox.module.exports.dispatchFinalFilingStable(context);}
    catch(e) {filingRefused=true;}
  }
  process.stdout.write(JSON.stringify({packet,error,packets,calls:before,
    active:state.get('rstable-active-role'),last:state.get('rstable-last-packet'),
    formalClose:state.get('rstable-formal-close')??null,retryRefused,filingRefused,
    extraCalls:calls.length-before}));
})().catch(e=>{process.stderr.write(e.stack);process.exitCode=1;});
'''
    script = Path(__file__).parents[1] / "scripts/p17_m2_input_export_dispatch.js"
    observed = subprocess.run(
        ["node", "-e", command, str(script), fault], input=json.dumps(subjects),
        text=True, capture_output=True, check=True,
    )
    result = json.loads(observed.stdout)
    packet = result["packet"]
    assert packet is not None, result["error"]
    assert result["error"] is None
    assert packet == result["last"] == result["packets"][-1]
    assert result["active"] is None
    assert result["calls"] == 12
    assert result["retryRefused"] and result["extraCalls"] == 0
    subject = subjects["shared-closeout"]
    assert packet["pending"] == subject["pending"]
    assert packet["completion"] == subject["completion"]
    assert packet["full_collector_record"] == subject["full_collector_record"]
    assert len(packet["events"]) == 2
    assert all(event["tool_results"] for event in packet["events"])
    assert packet["terminal"]["actual_exit_codes"] == [0, 0]
    if fault == "none":
        assert packet["terminal"]["status"] == "PASS_R_STABLE_FULL_ROLE"
        assert result["formalClose"] == packet["formal_close_UTC_seconds"]
    else:
        assert packet["terminal"]["status"] == "STOP_NO_RETRY"
        assert packet["terminal"]["full_role_evidence_accepted"] is False
        assert packet["terminal"]["domain_status"] == "STOP"
        assert result["formalClose"] is None
        assert "formal_close_UTC_seconds" not in packet
        assert "custodian_release" not in packet
        assert result["filingRefused"]
        assert any(item["reason"] == "final frontier retention/release exceeds reserve"
                   for item in packet["terminal"]["secondary_failures"])
        if fault == "late_event":
            assert "outside immutable actor window" in packet["terminal"]["reason"]
        else:
            assert packet["events"][-1]["end_seconds"] < 5500
            assert packet["terminal"]["reason"] == (
                "final frontier retention/release exceeds reserve")


@pytest.mark.parametrize("role", checker.FULL_STABLE)
def test_stable_full_role_uses_only_new_role_cap_and_4500_window(role: str) -> None:
    pending, completion, events, inner = stable_recording_subject(role=role)
    result = stable_recording_audit(pending, completion, events, inner)
    assert result["status"] == "PASS_R_STABLE_FULL_ROLE"
    assert result["frozen_FULL_seconds"] == checker.FULL_STABLE[role]
    assert result["actor_window_seconds"] == 4500
    assert result["whole_wall_seconds"] == 17.25
    assert result["RSS_envelope_bytes"] == 980
    assert result["source_successor_admitted"] is False
    assert result["B_C_admission"] is False


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
@pytest.mark.parametrize("adapter", ["js", "independent"])
@pytest.mark.parametrize("end,damage,span,charge", [
    (5500.0, "none", 4500.0, 4510),
    (5500.001, "none", 4500.001, 4511),
    (5501.0, "none", 4501.0, 4511),
    (5500.001, "missing_exit", 4500.001, 4511),
    (5500.001, "completion", 4500.001, 4511),
    (5500.001, "clock", None, 300),
    (5500.001, "argv", None, 300),
])
def test_stable_outside_actor_window_keeps_valid_span_and_full_charge(
    adapter: str, end: float, damage: str, span: float | None, charge: int,
) -> None:
    pending, completion, events, inner = stable_recording_subject()
    events[-1]["end_seconds"] = end
    if damage == "missing_exit":
        events[-1]["exit_code"] = None
    elif damage == "completion":
        completion["pending_sha256"] = "f" * 64
    elif damage == "clock":
        events[-1]["clock_domain"] = "unregistered-clock"
    elif damage == "argv":
        events[-1]["argv"] = ["different-finalizer"]
    resources = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, native_profiles=failure_recording_profiles(),
        execution_identity=checker.EXECUTION_STABLE, failure_recording=True,
    )
    script = Path(__file__).parents[1] / "scripts/p17_m2_input_export_dispatch.js"
    command = (
        "const fs=require('fs');const {finishExternalStable}=require(process.argv[1]);"
        "console.log(JSON.stringify(finishExternalStable(...JSON.parse(fs.readFileSync(0,'utf8')))))"
    )
    observed = subprocess.run(
        ["node", "-e", command, str(script)],
        input=json.dumps([pending, completion, events, resources,
                          checker.digest(checker.canonical(pending))]),
        text=True, capture_output=True, check=True,
    )
    result = json.loads(observed.stdout) if adapter == "js" else stable_recording_audit(
        pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    if span is None:
        assert result["whole_wall_seconds"] is None
    else:
        assert result["whole_wall_seconds"] == pytest.approx(span, rel=0, abs=1e-9)
    assert result["known_cost_lower_bound_seconds"] == charge
    assert result["actual_exit_codes"] == [0, None if damage == "missing_exit" else 0]
    assert result["full_role_evidence_accepted"] is False
    assert result["source_successor_admitted"] is result["B_C_admission"] is False
    if damage not in ("clock", "argv") and end > 5500:
        assert "outside immutable actor window" in result["reason"]


@pytest.mark.parametrize("damage", ["old_identity", "old_FULL", "old_window", "missing_outer",
                                   "missing_inner", "cleanup", "missing_exit", "pending"])
def test_stable_replay_missing_or_closed_evidence_fails_first(damage: str) -> None:
    pending, completion, events, inner = stable_recording_subject()
    pending_sha = checker.digest(checker.canonical(pending))
    if damage == "old_identity":
        pending["execution_identity"] = completion["execution_identity"] = checker.EXECUTION_V2
    elif damage == "old_FULL":
        pending["frozen_FULL_seconds"] = completion["frozen_FULL_seconds"] = 120
    elif damage == "old_window":
        pending["actor_window_seconds"] = completion["actor_window_seconds"] = 2700
    elif damage == "missing_outer":
        completion["resource_components"].pop()
    elif damage == "missing_inner":
        inner = None
    elif damage == "cleanup":
        completion["cleanup"]["group_gone"] = None
    elif damage == "missing_exit":
        events[-1]["exit_code"] = None
    else:
        pending_sha = "f" * 64
    result = checker.audit_full_role_stable(
        pending, completion=completion, raw_tool_events=events,
        expected_role="independent-public-check", expected_plan_sha256="a" * 64,
        expected_pending_sha256=pending_sha, inner_evidence=inner,
        native_profiles=failure_recording_profiles(),
    )
    assert result["status"] == "STOP_NO_RETRY"
    assert result["full_role_evidence_accepted"] is False
    assert result["B_C_admission"] is False
    if damage == "missing_exit":
        assert result["whole_wall_seconds"] == 17.25


def test_stable_measured_payload_failure_and_overrun_are_never_PASS() -> None:
    pending, completion, events, inner = stable_recording_subject(failed=True)
    measured_failure = stable_recording_audit(pending, completion, events, inner)
    assert measured_failure["evidence_complete"] is True
    assert measured_failure["domain_status"] == "STOP"
    assert measured_failure["status"] == "STOP_NO_RETRY"
    completion["status"] = "FAILED_INTERNAL_COMPLETION"
    events[-1]["end_seconds"] = 1290.001
    overrun = stable_recording_audit(pending, completion, events, inner)
    assert overrun["whole_wall_seconds"] == pytest.approx(290.001)
    assert overrun["known_cost_lower_bound_seconds"] == 301
    assert overrun["status"] == "STOP_NO_RETRY"
    assert overrun["actual_exit_codes"] == [1, 0]


def test_stable_resource_api_explicit_F_recording_preserves_new_binding() -> None:
    _, completion, _, inner = stable_recording_subject(failed=True)
    result = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, native_profiles=failure_recording_profiles(),
        execution_identity=checker.EXECUTION_STABLE, failure_recording=True,
    )
    assert result["evidence_complete"] is True
    assert result["actual_component_exit_codes"] == [1, 1]
    assert result["RSS_envelope_bytes"] == 980


@pytest.mark.parametrize("mode", ["r0", "r1", "public-check"])
def test_independent_CLI_refuses_unauthorized_DATA_before_any_stat(
    monkeypatch: pytest.MonkeyPatch, mode: str,
) -> None:
    argv = ["independent", mode, "--output", str(checker.AUTHORIZED_DATA_ROOT / "denied.json")]
    if mode == "public-check":
        argv += ["--fixture-root", str(checker.AUTHORIZED_DATA_ROOT / "denied-fixture")]
    else:
        argv += ["--authorize-old-read"]
    monkeypatch.setattr("sys.argv", argv)

    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("denied entry must not stat DATA")

    monkeypatch.setattr(Path, "exists", forbidden)
    with pytest.raises(ValueError, match="historical R CLI closed|public fixture cannot open DATA"):
        checker.main()


def stable_control_subject():  # type: ignore[no-untyped-def]
    return {
        "schema": "topolab.v2.m2-writer-quiescence.v1",
        "execution_identity": checker.EXECUTION_STABLE,
        "custodian": "/root",
        "namespaces": {
            namespace: {"accepted": True,
                        "basis": "new public custodian fixture; no original queried",
                        "no_writer_explanation": "fixture has no original writer"}
            for namespace in checker.SOURCE_NAMESPACES
        },
        "writers": [], "no_write_until_release": True,
        "acquisition_ack": {"by": "/root", "UTC_seconds": 1001.0,
                            "basis": "new public acknowledgment only"},
    }


def test_source_controls_empty_writers_need_explicit_attributed_coverage() -> None:
    controls = stable_control_subject()
    result = checker.accept_source_controls(controls, 1000.0,
                                           checker.digest(checker.canonical(controls)))
    assert result["status"] == "PASS_ATTRIBUTED_SOURCE_CONTROL_CONTENT"
    assert result["coverage_basis_requires_independent_judgment"] is True
    assert result["outside_writers_discovered_or_excluded_by_software"] is False


@pytest.mark.parametrize("damage", ["identity", "namespace", "unknown_coverage", "empty_basis",
                                   "no_explanation", "interval", "custodian", "early", "late",
                                   "hash", "unpaused_writer", "writer_unknown_namespace"])
def test_source_controls_unknown_or_unattributed_coverage_cannot_admit(
    damage: str,
) -> None:
    controls = stable_control_subject()
    expected_sha = None
    namespace = "b3-v1-fits"
    if damage == "identity":
        controls["execution_identity"] = checker.EXECUTION_V2
    elif damage == "namespace":
        controls["namespaces"].pop(namespace)
    elif damage == "unknown_coverage":
        controls["namespaces"][namespace]["accepted"] = None
    elif damage == "empty_basis":
        controls["namespaces"][namespace]["basis"] = ""
    elif damage == "no_explanation":
        controls["namespaces"][namespace].pop("no_writer_explanation")
    elif damage == "interval":
        controls["no_write_until_release"] = False
    elif damage == "custodian":
        controls["acquisition_ack"]["by"] = "other"
    elif damage == "early":
        controls["acquisition_ack"]["UTC_seconds"] = 999.0
    elif damage == "late":
        controls["acquisition_ack"]["UTC_seconds"] = 1300.001
    elif damage == "hash":
        expected_sha = "f" * 64
    else:
        controls["writers"] = [{
            "name": "fixture-writer", "namespace": namespace if damage == "unpaused_writer"
            else "undeclared", "action": "pause", "status": "UNKNOWN",
            "evidence": "fixture cannot acknowledge pause",
        }]
    with pytest.raises(ValueError):
        checker.accept_source_controls(controls, 1000.0, expected_sha)


@pytest.mark.parametrize("action,status", [("pause", "PAUSED_ACKNOWLEDGED"),
                                          ("exclude", "EXCLUDED_CUSTODIAN_CONTROL")])
def test_source_controls_accept_only_acknowledged_named_writer_action(
    action: str, status: str,
) -> None:
    controls = stable_control_subject()
    namespace = "b3-v1-fits"
    controls["namespaces"][namespace].pop("no_writer_explanation")
    controls["writers"] = [{"name": "fixture-writer", "namespace": namespace,
                            "action": action, "status": status,
                            "evidence": "new public fixture attributed action acknowledgment"}]
    assert checker.accept_source_controls(controls, 1000.0)["status"].startswith("PASS_")
    controls["writers"].append(deepcopy(controls["writers"][0]))
    with pytest.raises(ValueError, match="unconfirmed"):
        checker.accept_source_controls(controls, 1000.0)


def test_stable_public_entry_requires_plan_before_stat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", [
        "independent", "public-check", "--execution-identity", checker.EXECUTION_STABLE,
        "--fixture-root", str(checker.AUTHORIZED_STABLE_ROOT / "public-fixtures"),
        "--output", str(checker.AUTHORIZED_STABLE_ROOT / "independent-public-check.json"),
    ])

    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("unbound stable entry must not stat DATA")

    monkeypatch.setattr(Path, "exists", forbidden)
    with pytest.raises(ValueError, match="literal frozen plan/hash"):
        checker.main()


def test_stable_reader_before_open_replacement_has_no_fabricated_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = tmp_path / "original.json"
    original.write_bytes(b"{}\n")
    real_open = os.open
    replaced = False

    def replaced_open(name, flags, *args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal replaced
        if name == original.name and not replaced:
            replaced = True
            original.rename(tmp_path / "retained-original.json")
            original.write_bytes(b"{}\n")
        return real_open(name, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", replaced_open)
    reader = checker.OnceReader(tmp_path, 1, 100, source_identity_checks=True)
    with pytest.raises(ValueError, match="changed before"):
        reader.read(original.name, 100)
    failure = reader.failures[0]
    assert failure["stage"] == "before_read_identity"
    assert failure["returned_bytes"] is None
    assert failure["declared"]["st_ino"] != failure["before"]["st_ino"]
    assert failure["after"] is None and failure["closing"] is None


def test_stable_failure_journal_error_is_secondary_to_source_hash(
    tmp_path: Path,
) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    reader = checker.OnceReader(tmp_path, 1, 100, source_identity_checks=True,
                                journal=tmp_path / "absent" / "new-journal.jsonl")
    with pytest.raises(ValueError, match="source SHA differs"):
        reader.read("original.json", 100, sha256="f" * 64)
    failure = reader.failures[0]
    assert failure["primary_reason"] == "source SHA differs"
    assert "FileNotFoundError" in failure["recording_error"]
    assert failure["returned_bytes"] == 3
    assert failure["before"] == failure["after"] == failure["closing"]
    assert reader.observations[0]["sha256"] == checker.digest(b"{}\n")


@pytest.mark.parametrize("damage", ["missing", "initial", "final", "unknown", "order", "late",
                                   "overrun_flag", "exit", "helper_missing", "inner_missing"])
def test_stable_cleanup_raw_facts_are_required_not_only_final_true(damage: str) -> None:
    pending, completion, events, inner = stable_recording_subject()
    cleanup = completion["cleanup"]
    if damage == "missing":
        cleanup.pop("observations")
    elif damage == "initial":
        cleanup["initial_group_gone"] = True
    elif damage == "final":
        cleanup["final_group_gone"] = False
    elif damage == "unknown":
        cleanup["observations"][0]["group_gone"] = None
        cleanup["initial_group_gone"] = None
    elif damage == "order":
        cleanup["observations"][0]["elapsed_seconds"] = 1.0
    elif damage == "late":
        cleanup["post_signal_observation_seconds"] = 5.001
    elif damage == "overrun_flag":
        cleanup["observation_limit_exceeded"] = True
    elif damage == "exit":
        cleanup["observations"][-1]["leader_exit"] = 1
    elif damage == "helper_missing":
        inner["record"]["helpers"][0]["cleanup"].pop("observations")
    else:
        inner["record"]["cleanup"].pop("observations")
    result = stable_recording_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["evidence_complete"] is False
    assert result["domain_status"] == "STOP"
    assert result["actual_exit_codes"] == [0, 0]
    assert result["whole_wall_seconds"] == 17.25


@pytest.mark.parametrize("domain_status", [None, "UNKNOWN", "PASS_PUBLIC_SOFTWARE", True])
def test_stable_domain_requires_exact_PASS_after_complete_evidence(domain_status) -> None:  # type: ignore[no-untyped-def]
    pending, completion, events, inner = stable_recording_subject()
    completion["domain_status"] = domain_status
    result = stable_recording_audit(pending, completion, events, inner)
    assert result["evidence_complete"] is True
    assert result["status"] == "STOP_NO_RETRY"
    assert result["domain_status"] == "STOP"


def test_actual_isolated_public_CLI_uses_only_new_fixture_paths(tmp_path: Path) -> None:
    import sys

    output = tmp_path / "new-independent-public-result.json"
    completed = subprocess.run([
        sys.executable, "-I", str(Path(__file__).parents[1]
                                 / "scripts/p17_m2_input_export_independent.py"),
        "public-check", "--fixture-root", str(tmp_path / "new-public-CLI-fixtures"),
        "--output", str(output),
    ], text=True, capture_output=True, check=False, timeout=30)
    assert completed.returncode == 0, completed.stderr
    result = checker.parse(output.read_bytes())
    assert result["status"] == "PASS_PUBLIC_IO_ONLY"
    assert result["old_source_read_set"] == []
    assert result["compared_scalar_fields"] > 50000


def test_actual_isolated_stable_CLI_refuses_nonliteral_plan_before_DATA(tmp_path: Path) -> None:
    import sys

    completed = subprocess.run([
        sys.executable, "-I", str(Path(__file__).parents[1]
                                 / "scripts/p17_m2_input_export_independent.py"),
        "public-check", "--execution-identity", checker.EXECUTION_STABLE,
        "--plan", str(tmp_path / "nonliteral-plan.json"), "--plan-sha", "a" * 64,
        "--fixture-root", str(checker.AUTHORIZED_STABLE_ROOT / "public-fixtures"),
        "--output", str(checker.AUTHORIZED_STABLE_ROOT / "independent-public-check.json"),
    ], text=True, capture_output=True, check=False, timeout=30)
    assert completed.returncode != 0
    assert "literal frozen plan/hash" in completed.stderr


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
@pytest.mark.parametrize("damage", ["none", "payload", "missing_exit", "cleanup", "outer",
                                   "malformed_clock", "overrun", "pending", "domain"])
def test_stable_JS_and_independent_replay_agree_on_raw_facts(damage: str) -> None:
    pending, completion, events, inner = stable_recording_subject(failed=damage == "payload")
    pending_sha = checker.digest(checker.canonical(pending))
    if damage == "missing_exit":
        events[-1]["exit_code"] = None
    elif damage == "cleanup":
        completion["cleanup"]["observations"][0]["group_gone"] = None
    elif damage == "outer":
        completion["resource_components"].pop()
    elif damage == "malformed_clock":
        events[-1]["clock_domain"] = "unregistered-clock"
    elif damage == "overrun":
        events[-1]["end_seconds"] = 1290.001
    elif damage == "pending":
        pending_sha = "f" * 64
    elif damage == "domain":
        completion["domain_status"] = "UNKNOWN"
    resources = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, native_profiles=failure_recording_profiles(),
        execution_identity=checker.EXECUTION_STABLE, failure_recording=True,
    )
    script = Path(__file__).parents[1] / "scripts/p17_m2_input_export_dispatch.js"
    command = (
        "const fs=require('fs');const {finishExternalStable}=require(process.argv[1]);"
        "console.log(JSON.stringify(finishExternalStable(...JSON.parse(fs.readFileSync(0,'utf8')))))"
    )
    observed = subprocess.run(
        ["node", "-e", command, str(script)],
        input=json.dumps([pending, completion, events, resources, pending_sha]),
        text=True, capture_output=True, check=True,
    )
    js = json.loads(observed.stdout)
    py = checker.audit_full_role_stable(
        pending, completion=completion, raw_tool_events=events,
        expected_role="independent-public-check", expected_plan_sha256="a" * 64,
        expected_pending_sha256=pending_sha, inner_evidence=inner,
        native_profiles=failure_recording_profiles(),
    )
    for key in ("status", "domain_status", "evidence_complete", "whole_wall_seconds",
                "known_cost_lower_bound_seconds", "actual_exit_codes", "RSS_envelope_bytes",
                "full_role_evidence_accepted", "primary_failure"):
        assert js[key] == py[key], key
    assert js["status"] == ("PASS_R_STABLE_FULL_ROLE" if damage == "none" else "STOP_NO_RETRY")
    assert js["B_C_admission"] is False
    if damage == "malformed_clock":
        assert py["whole_wall_seconds"] is None
    elif damage == "overrun":
        assert py["known_cost_lower_bound_seconds"] == 301
    else:
        assert py["whole_wall_seconds"] == 17.25


def test_stable_predecessor_replay_binds_actual_pending_bytes_before_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = importlib.util.spec_from_file_location(
        "new_public_stable_controller_subject",
        Path(__file__).parents[1] / "scripts/p17_m2_input_export_control.py",
    )
    assert spec and spec.loader
    control = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(control)
    control.configure_stable()
    monkeypatch.setattr(control, "ROOT", tmp_path / "new-controller-root")
    (control.ROOT / "receipts").mkdir(parents=True)
    pending, completion, events, inner = stable_recording_subject()
    role = pending["role"]
    pending_raw = checker.canonical(pending)
    (control.ROOT / "receipts" / f"{role}-pending.json").write_bytes(pending_raw)
    terminal = stable_recording_audit(pending, completion, events, inner)
    assert terminal["status"] == "PASS_R_STABLE_FULL_ROLE"
    packet = {"pending": pending, "completion": completion, "events": events,
              "terminal": terminal}
    monkeypatch.setenv("TOPOLAB_RSTABLE_PREVIOUS_TOOL_RECORDS", json.dumps([packet]))
    monkeypatch.setattr(control, "resource_inputs", lambda *args, **kwargs: {
        "inner_evidence": inner, "native_profiles": failure_recording_profiles(),
    })
    control.ingest_external({"execution_identity": checker.EXECUTION_STABLE}, "a" * 64)
    observed = checker.parse((control.ROOT / "receipts" / f"{role}-observed.json").read_bytes())
    assert observed["status"] == "PASS_R_STABLE_FULL_ROLE"
    assert observed["pending_sha256"] == checker.digest(pending_raw)
    assert not (control.ROOT / "STOP.json").exists()


def final_filing_subject():  # type: ignore[no-untyped-def]
    _, completion, _, native = stable_recording_subject()
    child_argv = ["new-python", "-I", "new-control", "final-file", "--r-stable"]
    native["expected_role"] = native["record"]["role"] = "final-filing"
    native["expected_argv"] = native["record"]["argv"] = child_argv
    filing = {"status": "PASS_INDEPENDENT_NEW_BACKUP", "member_count": 100,
              "total_bytes": 1000, "shared_packet_sha256": "b" * 64,
              "shared_role_status": "PASS_R_STABLE_FULL_ROLE", "plan_sha256": "a" * 64,
              "formal_close_UTC_seconds": 1017.25}
    native["log"] = checker.canonical(filing)
    native["record"]["log_sha256"] = checker.digest(native["log"])
    record = {"schema": "topolab.v2.m2-source-stable-final-filing.v1",
              "execution_identity": checker.EXECUTION_STABLE,
              "status": "PENDING_EXTERNAL_EXIT", "plan_sha256": "a" * 64,
              "inner_argv_sha256": checker.digest(checker.canonical(child_argv)),
              "controller_RSS_samples_bytes": [200, 210], "controller_RSS_unit": "bytes",
              "filing_result": filing}
    return record, native, child_argv


def final_filing_audit(record, native, argv, **kwargs):  # type: ignore[no-untyped-def]
    options = {"actual_exit": 0, "whole_wall_seconds": 17.25,
               "expected_argv": argv, "native_evidence": native,
               "expected_plan_sha256": "a" * 64, "expected_shared_packet_sha256": "b" * 64}
    options.update(kwargs)
    return checker.audit_final_filing(record, **options)


def test_final_filing_after_return_is_new_only_not_seventh_source_role() -> None:
    record, native, argv = final_filing_subject()
    result = final_filing_audit(record, native, argv)
    assert result["status"] == "PASS_FINAL_NEW_FILING"
    assert result["RSS_envelope_bytes"] == 210 + 190
    assert result["whole_wall_seconds"] == 17.25
    assert result["known_cost_lower_bound_seconds"] == 28
    assert result["actual_exit_code"] == result["actual_child_exit_code"] == 0
    assert result["evidence_complete"] is True
    assert result["preparation_complete"] is False
    assert result["formal_source_role_or_window"] is False
    assert result["B_C_admission"] is False
    assert "final-filing" not in checker.FULL_STABLE


@pytest.mark.parametrize("damage", ["identity", "plan", "argv", "parent_RSS", "parent_units",
                                   "helper", "cleanup", "missing_exit", "parent_exit",
                                   "backup_status", "backup_extra", "packet", "shared_STOP",
                                   "missing_packet", "overrun", "RSS_cap"])
def test_final_filing_missing_required_or_failed_evidence_stays_STOP(damage: str) -> None:
    record, native, argv = final_filing_subject()
    options = {}
    if damage == "identity":
        record["execution_identity"] = checker.EXECUTION_F
    elif damage == "plan":
        record["plan_sha256"] = "f" * 64
    elif damage == "argv":
        record["inner_argv_sha256"] = "f" * 64
    elif damage == "parent_RSS":
        record["controller_RSS_samples_bytes"].pop()
    elif damage == "parent_units":
        record["controller_RSS_unit"] = "UNKNOWN"
    elif damage == "helper":
        native["helper_profiles"] = {}
    elif damage == "cleanup":
        native["record"]["cleanup"]["group_gone"] = None
    elif damage == "missing_exit":
        options["actual_exit"] = None
    elif damage == "parent_exit":
        options["actual_exit"] = 1
    elif damage == "backup_status":
        record["filing_result"]["status"] = "STOP_NO_RETRY"
        native["log"] = checker.canonical(record["filing_result"])
        native["record"]["log_sha256"] = checker.digest(native["log"])
    elif damage == "backup_extra":
        record["filing_result"]["extra_claim"] = "not in raw child log"
    elif damage == "packet":
        options["expected_shared_packet_sha256"] = "f" * 64
    elif damage == "shared_STOP":
        record["filing_result"]["shared_role_status"] = "STOP_NO_RETRY"
        native["log"] = checker.canonical(record["filing_result"])
        native["record"]["log_sha256"] = checker.digest(native["log"])
    elif damage == "missing_packet":
        options["expected_shared_packet_sha256"] = None
    elif damage == "overrun":
        options["whole_wall_seconds"] = 170.001
    else:
        record["controller_RSS_samples_bytes"][-1] = 4294967296
    result = final_filing_audit(record, native, argv, **options)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["whole_wall_seconds"] == (170.001 if damage == "overrun" else 17.25)
    assert result["actual_exit_code"] == options.get("actual_exit", 0)
    assert result["preparation_complete"] is False
    assert result["B_C_admission"] is False
    if damage == "overrun":
        assert result["known_cost_lower_bound_seconds"] == 181
    if damage == "parent_exit":
        assert result["evidence_complete"] is True
        assert result["actual_child_exit_code"] == 0


def test_final_filing_exact_time_boundary_does_not_use_tolerance() -> None:
    record, native, argv = final_filing_subject()
    assert final_filing_audit(record, native, argv, whole_wall_seconds=170.0)["status"] == (
        "PASS_FINAL_NEW_FILING"
    )
    rejected = final_filing_audit(record, native, argv, whole_wall_seconds=170.000001)
    assert rejected["status"] == "STOP_NO_RETRY"
    assert rejected["known_cost_lower_bound_seconds"] == 181


def test_final_filing_bad_completion_preserves_obtainable_RSS_wall_and_actual_exit() -> None:
    record, native, argv = final_filing_subject()
    record["status"] = "FAILED_INTERNAL_COMPLETION"
    result = final_filing_audit(record, native, argv, actual_exit=1)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["whole_wall_seconds"] == 17.25
    assert result["actual_exit_code"] == 1
    assert result["actual_child_exit_code"] == 0
    assert result["RSS_envelope_bytes"] == 400
    assert result["known_cost_lower_bound_seconds"] == 28
    assert result["evidence_complete"] is False


@pytest.mark.parametrize("damage", [None, "isolated", "registry", "output", "extra", "missing"])
def test_stable_complete_actual_argv_binds_all_source_role_arguments(
    monkeypatch: pytest.MonkeyPatch, damage: str | None,
) -> None:
    frozen = ["new-python", "-I", "new-independent.py", "r0", "--registry",
              "new-root/registry.json", "--output", "new-root/result.json", "--plan-sha",
              "<PLAN_SHA256>"]
    plan = {"roles": {"independent-r0": {"argv": frozen}}}
    actual = [word.replace("<PLAN_SHA256>", "a" * 64) for word in frozen]
    if damage == "isolated":
        actual.remove("-I")
    elif damage == "registry":
        actual[5] = "another-allowlisted-file.json"
    elif damage == "output":
        actual[7] = "new-root/another-result.json"
    elif damage == "extra":
        actual.append("--unfrozen-extra")
    elif damage == "missing":
        actual = None
    monkeypatch.setattr("sys.orig_argv", actual)
    if damage is None:
        checker.stable_argv_checked(plan, "a" * 64, "independent-r0")
    else:
        with pytest.raises(ValueError, match="complete argv"):
            checker.stable_argv_checked(plan, "a" * 64, "independent-r0")
