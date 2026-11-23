"""A2 recovery verification uses synthetic receipts and software only."""

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def subject():
    path = REPO / "scripts/input_cycle_r1_proof.py"
    spec = importlib.util.spec_from_file_location("declared_r1_recovery_proof", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixed_a2_verifier_cannot_launch_old_or_real_reader_roles():
    module = subject()
    assert module.verify_args() == [
        "/usr/bin/timeout",
        "-k",
        "2",
        "290",
        module.PYTHON,
        "-I",
        str(module.REPO / module.WORKER),
        "verify",
    ]
    assert module.IDENTITY.endswith(".cycle-20261123-a2.v1")


def test_unbound_real_observation_fails_before_label_comparison(monkeypatch):
    module = subject()
    monkeypatch.setattr(module, "_checker", lambda: pytest.fail("unbound label compared"))
    with pytest.raises(ValueError):
        module.verify_observation(
            1, b"{}\n", b"{}\n", b"{}\n", b"{}\n", item={}, anchor={}, source_main="d" * 40
        )


def observation_fixture(module, monkeypatch, slot=2, *, damage=None, cold=True):
    """All payloads, physical identities and original tool packets here are synthetic."""
    base = module._base()
    checked = module._checker()
    source = checked.public_label((12, 6, 3))
    if damage == "label-domain":
        source["stored"]["tensor_dtype"] = "float16"
    raw = checked.canonical(source)
    pin = module.sha(raw)
    relative = f"b3-v1-data/artifacts/label/{source['entry']['case']['case_id']}/{pin}.json"
    monkeypatch.setattr(module, "LABEL_SIZE", len(raw))
    monkeypatch.setattr(module, "LABEL_SHA", pin)
    monkeypatch.setattr(module, "RELATIVE", relative)
    artifact = dict(path=relative, byte_size=len(raw), sha256=pin)
    item = dict(
        case_id=source["entry"]["case"]["case_id"],
        entry=source["entry"],
        context_sha256=module.sha(checked.canonical(source["context"])),
        manifest_sha256=source["manifest_sha256"],
        source_revision=source["context"]["source_revision"],
        artifact=artifact,
    )
    anchor = dict(st_dev=1, st_ino=2, st_size=len(raw), st_mtime_ns=100)
    facts = dict(
        schema="topolab.v2.m2-input-read-failure.v1",
        execution_identity="topolab.v2.p17-m2-local-input-version.v1",
        attempt_ordinal=1,
        path=relative,
        stage="source_validation",
        returned_bytes=len(raw),
        changed_fields=[],
        identity_policy="topolab.source-identity.prebound-sha256.v1",
        expected_sha256=pin,
        source=artifact,
        mtime_changes={point: 0 for point in module.POINTS[1:]},
        **{point: deepcopy(anchor) for point in module.POINTS},
    )
    trace = [
        dict(
            stage=point,
            flags=0x40000060 if cold and i < 2 else 0x40,
            blocks=0 if cold and i < 2 else 8,
            monotonic_ns=1000 + i * 10,
        )
        for i, point in enumerate(module.POINTS)
    ]
    if slot == 2:
        facts["storage"] = {
            row["stage"]: dict(flags=row["flags"], blocks=row["blocks"]) for row in trace
        }
    tree = {name: module.sha(name.encode()) for name in module.READER_SOURCES}
    worker = module.BASELINE_WORKER_SHA if slot == 1 else tree[module.RECHECK]
    first = module.START + slot * 1000
    repo = module.OLD_REPO if slot == 1 else module.REPO
    head = module.PREVIOUS_MAIN if slot == 1 else "d" * 40
    claim = dict(
        schema="topolab.r1-label-claim.v1",
        slot=slot,
        argv=module.recheck_args(slot),
        repo=str(repo),
        source_main=head,
        worker_sha256=worker,
        charge_FULL=1200,
        budget_sha256=module.CAMPAIGN_SHA,
        failed_archive_sha256=module.ARCHIVE_SHA,
        path=relative,
        claimed_ms=first - 1,
    )
    claim_raw = base.canonical(claim)
    entry = dict(slot=slot, claim_sha256=module.sha(claim_raw), entered_ms=first + 1)
    report = dict(
        schema="topolab.r1-label-recheck.v1",
        slot=slot,
        source_main=head,
        archive_sha256=module.ARCHIVE_SHA,
        worker_sha256=worker,
        started_ms=first + 1,
        ended_ms=first + 10,
        rss_bytes=1000,
        claim_sha256=module.sha(claim_raw),
        anchor=anchor,
        status="PASS",
        error=None,
        trace=trace,
        elapsed_ns=3_000_000,
        facts=facts,
        attempts=[relative],
        source_observations=[
            dict(
                artifact,
                **{p: facts[p] for p in module.POINTS},
                identity_policy=facts["identity_policy"],
                expected_sha256=pin,
                mtime_changes=deepcopy(facts["mtime_changes"]),
            )
        ],
        raw_base64=module.base64.b64encode(raw).decode(),
    )
    if slot == 2:
        report["reader_source_sha256"] = dict(tree)
    if damage == "raw-short":
        report["raw_base64"] = module.base64.b64encode(raw[:-1]).decode()
    elif damage == "wrong-inode":
        facts["before"]["st_ino"] += 1
    elif damage == "missing-closing":
        facts["closing"] = None
    elif damage == "mtime-bool":
        facts["mtime_changes"]["before"] = False
    elif damage == "extra-attempt":
        report["attempts"].append("other.json")
    elif damage == "false-pass":
        facts["status"] = "STOP_NO_RETRY"
    elif damage == "trace-order":
        report["trace"] = list(reversed(trace))
    elif damage == "trace-type":
        trace[0]["blocks"] = False
    elif damage == "storage-mismatch":
        facts["storage"]["before"]["flags"] += 1
    elif damage == "reader-source":
        report["reader_source_sha256"][module.READER_SOURCES[0]] = "0" * 64
    elif damage == "reader-inventory":
        report["reader_source_sha256"].pop(module.READER_SOURCES[0])
    elif damage == "old-candidate-head":
        report["source_main"] = module.PREVIOUS_MAIN
    elif damage == "rss-bool":
        report["rss_bytes"] = True
    report_raw = base.canonical(report)
    wire = base._wire()
    request = dict(
        cmd=wire.literal_command(module.recheck_args(slot)),
        workdir=str(repo),
        max_output_tokens=5000,
    )
    result = dict(
        exit_code=0,
        output=base.canonical(
            dict(
                status="PASS",
                slot=slot,
                report_sha256=module.sha(report_raw),
                own_future_return="NOT_CLAIMED",
            )
        ).decode(),
    )
    if damage == "exit-bool":
        result["exit_code"] = False
    elif damage == "exit-one":
        result["exit_code"] = 1
    elif damage == "wrong-stdout":
        result["output"] = "{}\n"
    actual = dict(
        schema=wire.ACTUAL_SCHEMA,
        author="/root",
        argv=module.recheck_args(slot),
        request=request,
        responses=[
            dict(
                tool="exec_command",
                arguments=request,
                requested_ms=first,
                returned_ms=first + 20,
                result=result,
            )
        ],
    )
    if damage == "actual-actor":
        actual["author"] = module.AUTHOR
    elif damage == "actual-late":
        actual["responses"][0]["returned_ms"] = first + 1200000
    actual_raw = base.canonical(actual)
    if slot == 1:
        monkeypatch.setattr(module, "BASELINE_REPORT_SHA", module.sha(report_raw))
        monkeypatch.setattr(module, "BASELINE_ACTUAL_SHA", module.sha(actual_raw))
    return (claim_raw, base.canonical(entry), report_raw, actual_raw), item, anchor, tree


@pytest.mark.parametrize("slot,cold", [(1, True), (2, True), (2, False)])
def test_complete_original_observation_and_independent_label_comparison(monkeypatch, slot, cold):
    module = subject()
    parts, item, anchor, tree = observation_fixture(module, monkeypatch, slot, cold=cold)
    value = module.verify_observation(
        slot, *parts, item=item, anchor=anchor, source_main="d" * 40, source_tree=tree
    )
    assert value["byte_size"] == module.LABEL_SIZE
    assert value["raw_sha256"] == module.LABEL_SHA
    assert value["FULL"] == 1200
    assert value["historical_reader_loaded_digest"] == (
        "NOT_RECORDED" if slot == 1 else "CURRENT_TREE_BOUND"
    )


@pytest.mark.parametrize(
    "damage",
    [
        "raw-short",
        "wrong-inode",
        "missing-closing",
        "mtime-bool",
        "extra-attempt",
        "false-pass",
        "trace-order",
        "trace-type",
        "storage-mismatch",
        "reader-source",
        "reader-inventory",
        "old-candidate-head",
        "rss-bool",
        "exit-bool",
        "exit-one",
        "wrong-stdout",
        "actual-actor",
        "actual-late",
        "label-domain",
    ],
)
def test_observation_refuses_fabricated_raw_identity_source_domain_and_return(monkeypatch, damage):
    module = subject()
    parts, item, anchor, tree = observation_fixture(module, monkeypatch, damage=damage)
    with pytest.raises(ValueError):
        module.verify_observation(
            2, *parts, item=item, anchor=anchor, source_main="d" * 40, source_tree=tree
        )


def readiness_fixture(module, monkeypatch, tmp_path):
    base = module._base()
    campaign_raw = b'{"declared":"campaign"}\n'
    attempt_raw = b'{"declared":"attempt2"}\n'
    monkeypatch.setattr(module, "CAMPAIGN_SHA", module.sha(campaign_raw))
    monkeypatch.setattr(module, "ATTEMPT_SHA", module.sha(attempt_raw))
    monkeypatch.setattr(module, "E", tmp_path / "a2")
    monkeypatch.setattr(module, "CAMPAIGN", tmp_path / "campaign")
    one, item, anchor, tree = observation_fixture(module, monkeypatch, 1)
    two, second_item, second_anchor, second_tree = observation_fixture(module, monkeypatch, 2)
    assert item == second_item and anchor == second_anchor and tree == second_tree
    predecessor = dict(
        closed_ms=module.START + 500,
        source_main=module.PREVIOUS_MAIN,
        archive_sha256=module.ARCHIVE_SHA,
        closed_sha256=module.CLOSED_SHA,
    )
    monkeypatch.setattr(module, "_anchor", lambda: (item, anchor, predecessor))
    records = {}
    for slot, parts in ((1, one), (2, two)):
        for name, raw in zip(("claim", "entered", "report", "actual"), parts, strict=True):
            records[(str(module.CAMPAIGN), f"real-{slot:02d}-{name}.json")] = raw
    records[(str(module.CAMPAIGN), "campaign-budget.json")] = campaign_raw
    records[(str(module.CAMPAIGN), "attempt-2-budget.json")] = attempt_raw

    def pair(root, name, expected=None):
        raw = records[(str(root), name)]
        module.need(expected is None or module.sha(raw) == expected, "declared pair SHA differs")
        return raw

    monkeypatch.setattr(base, "pair", pair)
    tree = dict(tree)
    tree.update(
        {
            module.PROTOCOL: "b" * 64,
            module.WORKER: "9" * 64,
            module.BASE: module.BASE_SHA,
            module.CHECKER: base.SOURCE_PINS[module.CHECKER],
            base.WIRE: base.SOURCE_PINS[base.WIRE],
        }
    )
    monkeypatch.setattr(module, "_self_sha", lambda: "9" * 64)
    recovered = module._recover("d" * 40, tree)
    policy = dict(
        execution_identity=module.IDENTITY,
        campaign_budget=dict(
            path=str(module.CAMPAIGN / "campaign-budget.json"), sha256=module.CAMPAIGN_SHA
        ),
        new_input_budget=dict(
            path=str(module.CAMPAIGN / "attempt-2-budget.json"), sha256=module.ATTEMPT_SHA
        ),
        r1_recovery_verification_paths=dict(
            package=str(module.E / module.PACKAGE), actual=str(module.E / module.ACTUAL)
        ),
        predecessor_terminal=dict(
            path=str(module.A1 / "attempt-one-closed.json"), sha256=module.CLOSED_SHA
        ),
        predecessor_independent_audit=dict(
            path=str(module.A1 / "independent-a1-terminal-audit.json"), sha256=module.AUDIT_SHA
        ),
    )
    first = module.START + 3000
    claim = dict(
        schema="topolab.input-cycle-offline-claim.v1",
        slot=2,
        actor=module.AUTHOR,
        argv=module.verify_args(),
        repo=str(module.REPO),
        source_main="d" * 40,
        worker_sha256=tree[module.WORKER],
        budget_sha256=module.CAMPAIGN_SHA,
        attempt_budget_sha256=module.ATTEMPT_SHA,
        charge_FULL=300,
        claimed_ms=first - 1,
    )
    claim_raw = base.canonical(claim)
    entry = dict(
        slot=2,
        execution_identity=module.IDENTITY,
        started_ms=first + 1,
        claim_sha256=module.sha(claim_raw),
    )
    report = dict(
        schema="topolab.r1-recovery-report.v1",
        status=module.SUCCESS,
        slot=2,
        execution_identity=module.IDENTITY,
        campaign_budget_sha256=module.CAMPAIGN_SHA,
        attempt_budget_sha256=module.ATTEMPT_SHA,
        claim_sha256=module.sha(claim_raw),
        entered_sha256=module.sha(base.canonical(entry)),
        started_ms=first + 1,
        ended_ms=first + 2,
        self_rss_bytes=5000,
        recovered=recovered,
        source_main="d" * 40,
        repo=str(module.REPO),
        authority_sha256=tree[module.PROTOCOL],
        worker_sha256=tree[module.WORKER],
        checker_sha256=tree[module.CHECKER],
        recheck_worker_sha256=tree[module.RECHECK],
        reader_source_sha256={name: tree[name] for name in module.READER_SOURCES},
    )
    wire = base._wire()
    request = dict(
        cmd=wire.literal_command(module.verify_args()),
        workdir=str(module.REPO),
        max_output_tokens=5000,
    )
    actual = dict(
        schema=wire.ACTUAL_SCHEMA,
        author=module.AUTHOR,
        argv=module.verify_args(),
        request=request,
        responses=[
            dict(
                tool="exec_command",
                arguments=request,
                requested_ms=first,
                returned_ms=first + 3,
                result=dict(exit_code=0, output=""),
            )
        ],
    )

    def save():
        raw = base.canonical(report)
        actual["responses"][0]["result"]["output"] = base.canonical(
            module.verify_return(module.sha(raw))
        ).decode()
        for root, name, value in (
            (module.E, module.PACKAGE, report),
            (module.E, module.ACTUAL, actual),
            (module.CAMPAIGN, "offline-02-claim.json", claim),
            (module.CAMPAIGN, "offline-02-entered.json", entry),
        ):
            records[(str(root), name)] = base.canonical(value)

    save()
    return policy, tree, report, actual, claim, entry, records, save


def test_complete_readiness_replays_two_original_buffers_without_git_or_source_access(
    monkeypatch, tmp_path
):
    module = subject()
    policy, tree, *_ = readiness_fixture(module, monkeypatch, tmp_path)
    monkeypatch.setattr(
        module.subprocess,
        "check_output",
        lambda *_a, **_k: pytest.fail("live Git/source operation"),
    )
    value = module.verified_readiness(policy, tree)
    assert (
        value["source_main"] == "d" * 40 and value["previous_source_main"] == module.PREVIOUS_MAIN
    )
    assert value["accepted_real_slots"] == [1, 2]
    assert value["verified_returned_ms"] == module.START + 3003
    assert value["slot"] == 2


@pytest.mark.parametrize(
    "damage",
    [
        "worker",
        "recheck-worker",
        "reader-map",
        "protocol",
        "history",
        "exit",
        "author",
        "clock",
        "slot",
        "budget",
        "entry-slot",
        "policy",
        "before-close",
        "before-real-return",
    ],
)
def test_readiness_rejects_mixed_release_claims_and_original_returns(monkeypatch, tmp_path, damage):
    module = subject()
    policy, tree, report, actual, _claim, entry, _records, save = readiness_fixture(
        module, monkeypatch, tmp_path
    )
    if damage in ("worker", "recheck-worker", "protocol"):
        key = {
            "worker": "worker_sha256",
            "recheck-worker": "recheck_worker_sha256",
            "protocol": "authority_sha256",
        }[damage]
        report[key] = "0" * 64
    elif damage == "reader-map":
        report["reader_source_sha256"][module.READER_SOURCES[0]] = "0" * 64
    elif damage == "history":
        report["recovered"] = deepcopy(report["recovered"])
        report["recovered"]["new_original_reads_by_verifier"] = False
    elif damage == "exit":
        actual["responses"][0]["result"]["exit_code"] = False
    elif damage == "author":
        actual["author"] = "/root"
    elif damage == "clock":
        actual["responses"][0]["returned_ms"] += 300000
    elif damage == "slot":
        report["slot"] = True
    elif damage == "budget":
        report["attempt_budget_sha256"] = "0" * 64
    elif damage == "entry-slot":
        entry["slot"] = True
        report["entered_sha256"] = module.sha(module._base().canonical(entry))
    elif damage == "policy":
        policy["r1_recovery_verification_paths"]["package"] = "/other/report.json"
    elif damage == "before-close":
        item, anchor, pred = module._anchor()
        monkeypatch.setattr(
            module, "_anchor", lambda: (item, anchor, dict(pred, closed_ms=module.START + 10000))
        )
    elif damage == "before-real-return":
        actual["responses"][0]["requested_ms"] = module.START + 1500
    save()
    with pytest.raises(ValueError):
        module.verified_readiness(policy, tree)
