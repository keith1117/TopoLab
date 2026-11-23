"""A3 admission uses sealed metadata and synthetic dispatch only."""

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def subject():
    path = REPO / "scripts/input_cycle_filing_proof.py"
    spec = importlib.util.spec_from_file_location("declared_filing_proof", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixed_a3_metadata_only_entry_does_not_reopen_formal_or_old_reader():
    module = subject()
    assert module.verify_args() == [
        "/usr/bin/timeout", "-k", "2", "290", module.PYTHON, "-I",
        str(module.REPO / module.WORKER), "verify",
    ]
    assert module.IDENTITY.endswith(".cycle-20261123-a3.v1")
    assert module.PREVIOUS_MAIN == "fe6d7ff2b716b4a02b42709171faf48e9f849125"
    assert module.PACKAGE == "filing-verification-a3.json"


def test_unbound_predecessor_is_denied_before_any_historical_replay(monkeypatch):
    module = subject()
    monkeypatch.setattr(module, "_historical_recovery", lambda *_: pytest.fail("old code ran"))
    with pytest.raises((ValueError, KeyError)):
        module.verify_stop_buffers({}, {}, {}, {}, {}, b"", {})


def stop_fixture(module, monkeypatch):
    """Invented records only; no real actor, target or source is opened."""
    base = module._base()
    actor_raw = b"// declared synthetic actor\n"
    monkeypatch.setattr(module, "ACTOR_SHA", module.sha(actor_raw))
    plan = dict(execution_identity=module.PREVIOUS_IDENTITY,
                root="/declared/synthetic-target", source_tree={})
    pin = module.sha(base.canonical(plan))
    closed = dict(status="CLOSED_AUTO_REVIEW_DECLINED_RECORD_FILING", formal_roles_accepted=0,
                  formal_booked=600, formal_closed_unused=3360, cumulative_known_FULL=352899,
                  metadata=[0, 0], payload=[0, 0], plan_sha256=pin,
                  source_main=module.PREVIOUS_MAIN, new_lease="HELD")
    audit = dict(status="VERIFIED_A2_STOP_APPROVAL_REJECTION_ORIGINAL_ACTOR",
                 plan_sha256=pin, source_main=module.PREVIOUS_MAIN,
                 synthetic_original_actor_replay=dict(rows_consumed=15, actual_tool_dispatches=0,
                     checks=dict.fromkeys(("reason", "secondary", "observed", "raw", "active"),
                                          True), program_sha256=module.PROGRAM_SHA))
    rows = [dict(tool="exec_command", arguments=dict(cmd="declared synthetic metadata"),
                 requested_ms=module.START+i*2, returned_ms=module.START+i*2+1,
                 result=dict(exit_code=0, output="{}\n")) for i in range(15)]
    record_packet = dict(schema="declared-synthetic-original", responses=[deepcopy(rows[9])])
    saved = dict(path=str(module.PREVIOUS_E / "declared-record.json"), packet=record_packet,
                 sha256=module.sha(base.canonical(record_packet)))
    words = [module.PYTHON, "-I", str(module.OLD_REPO / "scripts/cycle_r1_input_filer.py"),
             "file", "--root", plan["root"], "--plan-sha", pin,
             "--role", "independent-public-check", "--event-mode", "record",
             "--packet", saved["path"], "--packet-sha", saved["sha256"]]
    rows[12]["arguments"]["cmd"] = module.shlex.join(words)
    rows[12].pop("result")
    rows[12]["error"] = "Rejected: synthetic original SUP/REC filing refusal"
    phase = dict(ended=True, on_time=True, exit_code=0, error=None)
    independent = dict(status="STOP_RETAINED_NO_RETRY", secondary=[], observed=[], raw=rows,
                       reason="synthetic caller " + rows[12]["error"],
                       active=dict(role="independent-public-check", supervise=deepcopy(phase),
                                   record=deepcopy(phase)),
                       packets={"independent-public-check-record": saved})
    root = dict(status="STOP_RETAINED_NO_RETRY", secondary=[], observed=[],
                reason="Error: predecessor STOP closes this graph",
                raw=[deepcopy(rows[0]) for _ in range(17)])
    members = {"independent-public-check-supervise-actual-event.json": b"{}\n"}
    return closed, audit, root, independent, plan, actor_raw, members


def test_complete_synthetic_original_refusal_cannot_claim_an_accepted_role(monkeypatch):
    module = subject()
    value = module.verify_stop_buffers(*stop_fixture(module, monkeypatch))
    assert value["accepted_roles"] == 0 and value["formal_FULL"] == 600
    assert value["original_SUP_REC_exits"] == [0, 0] and value["lease"] == "HELD"
    assert value["absolute_host_no_unrecorded_dispatch"] == "NOT_PROVEN"


@pytest.mark.parametrize("damage", [
    "accepted", "refund", "exit-bool", "late", "approval-removed", "extra-row",
    "repeated-command", "packet", "mode", "scope", "replay", "new-rec-event",
    "successor", "secondary", "actor-source", "root-reason",
])
def test_stop_replay_rejects_mixed_status_source_event_and_originals(monkeypatch, damage):
    module = subject()
    parts = stop_fixture(module, monkeypatch)
    closed, audit, root, independent, plan, _actor, members = parts
    if damage == "accepted":
        closed["formal_roles_accepted"] = 1
    elif damage == "refund":
        closed["formal_booked"] = 0
    elif damage == "exit-bool":
        independent["active"]["record"]["exit_code"] = False
    elif damage == "late":
        independent["active"]["record"]["on_time"] = False
    elif damage == "approval-removed":
        independent["raw"][12]["error"] = "unexpected error"
    elif damage == "extra-row":
        independent["raw"].append(deepcopy(independent["raw"][0]))
    elif damage == "repeated-command":
        independent["raw"][11]["arguments"] = deepcopy(independent["raw"][12]["arguments"])
    elif damage == "packet":
        independent["packets"]["independent-public-check-record"]["sha256"] = "0" * 64
    elif damage == "mode":
        independent["raw"][12]["arguments"]["cmd"] = independent["raw"][12][
            "arguments"]["cmd"].replace("--event-mode record", "--event-mode supervise")
    elif damage == "scope":
        plan["execution_identity"] = module.IDENTITY
    elif damage == "replay":
        audit["synthetic_original_actor_replay"]["checks"]["raw"] = False
    elif damage == "new-rec-event":
        members["independent-public-check-record-actual-event.json"] = b"{}\n"
    elif damage == "successor":
        members["exporter-r0-dispatch-charge.json"] = b"{}\n"
    elif damage == "secondary":
        independent["secondary"] = ["another failure"]
    elif damage == "actor-source":
        parts = (*parts[:5], b"another source", parts[6])
    else:
        root["reason"] = "COMPLETE"
    with pytest.raises(ValueError):
        module.verify_stop_buffers(*parts)


def readiness_fixture(module, monkeypatch):
    base = module._base()
    wire = base._wire()
    records = {}
    policy = dict(execution_identity=module.IDENTITY,
        campaign_budget=dict(path=str(module.CAMPAIGN / "campaign-budget.json"),
                             sha256=module.CAMPAIGN_SHA),
        new_input_budget=dict(path=str(module.CAMPAIGN / "attempt-3-budget.json"),
                              sha256=module.ATTEMPT_SHA),
        filing_verification_paths=dict(package=str(module.E / module.PACKAGE),
                                        actual=str(module.E / module.ACTUAL)),
        predecessor_terminal=dict(path=str(module.PREVIOUS_E / "attempt-two-closed.json"),
                                  sha256=module.CLOSED_SHA),
        predecessor_independent_audit=dict(
            path=str(module.PREVIOUS_E / "independent-a2-terminal-audit.json"),
            sha256=module.AUDIT_SHA), filing_repair_sources=list(module.REPAIR_SOURCES))

    def pair(root, name, *_):
        if name in ("campaign-budget.json", "attempt-3-budget.json"):
            return b"{}\n"
        return records[(str(root), name)]

    monkeypatch.setattr(base, "pair", pair)
    first = module.START + 1000
    tree = {path: module.sha(path.encode()) for path in (*module.REPAIR_SOURCES,
        module.PROTOCOL, module.WORKER, module.CHECKER, module.BASE, base.WIRE)}
    tree.update({module.BASE: module.BASE_SHA, module.CHECKER: base.SOURCE_PINS[module.CHECKER],
                 base.WIRE: wire.compiled_sha256})
    monkeypatch.setattr(module, "_self_sha", lambda: tree[module.WORKER])
    predecessor = dict(closed_ms=first-10, prior_recovery=dict(verified_returned_ms=first-11))
    repair = dict(source_sha256={name: tree[name] for name in module.REPAIR_SOURCES},
                  approval_outcome="NOT_GUARANTEED", actual_tool_dispatches=0)
    monkeypatch.setattr(module, "_predecessor", lambda: deepcopy(predecessor))
    monkeypatch.setattr(module, "_repair", lambda *_: deepcopy(repair))
    claim = dict(schema="topolab.input-cycle-offline-claim.v1", slot=3, actor=module.AUTHOR,
                 argv=module.verify_args(), repo=str(module.REPO), source_main="d"*40,
                 worker_sha256=tree[module.WORKER], budget_sha256=module.CAMPAIGN_SHA,
                 attempt_budget_sha256=module.ATTEMPT_SHA, charge_FULL=300, claimed_ms=first-1)
    entry = dict(slot=3, execution_identity=module.IDENTITY, started_ms=first+1,
                 claim_sha256=module.sha(base.canonical(claim)))
    report = dict(schema="topolab.filing-verification-report.v1", status=module.SUCCESS, slot=3,
                  execution_identity=module.IDENTITY, source_main="d"*40, repo=str(module.REPO),
                  authority_sha256=tree[module.PROTOCOL], worker_sha256=tree[module.WORKER],
                  checker_sha256=tree[module.CHECKER], repair_source_sha256=repair["source_sha256"],
                  campaign_budget_sha256=module.CAMPAIGN_SHA,
                  attempt_budget_sha256=module.ATTEMPT_SHA,
                  claim_sha256=module.sha(base.canonical(claim)),
                  entered_sha256=module.sha(base.canonical(entry)), started_ms=first+1,
                  ended_ms=first+2, self_rss_bytes=5000, predecessor=deepcopy(predecessor),
                  repair=deepcopy(repair))
    request = dict(cmd=wire.literal_command(module.verify_args()), workdir=str(module.REPO),
                   max_output_tokens=5000)
    actual = dict(schema=wire.ACTUAL_SCHEMA, author=module.AUTHOR, argv=module.verify_args(),
                  request=request, responses=[dict(tool="exec_command", arguments=request,
                    requested_ms=first, returned_ms=first+3, result=dict(exit_code=0, output=""))])

    def save():
        actual["responses"][0]["result"]["output"] = base.canonical(
            module.verify_return(module.sha(base.canonical(report)))).decode()
        for root, name, value in (
            (module.E, module.PACKAGE, report), (module.E, module.ACTUAL, actual),
            (module.CAMPAIGN, "offline-03-claim.json", claim),
            (module.CAMPAIGN, "offline-03-entered.json", entry),
        ):
            records[(str(root), name)] = base.canonical(value)

    save()
    return policy, tree, report, actual, claim, entry, predecessor, repair, save


def test_complete_readiness_binds_current_release_and_original_independent_return(monkeypatch):
    module = subject()
    policy, tree, *_ = readiness_fixture(module, monkeypatch)
    monkeypatch.setattr(module.subprocess, "check_output",
                        lambda *_a, **_k: pytest.fail("new subprocess or business read"))
    value = module.verified_readiness(policy, tree)
    assert value["source_main"] == "d" * 40 and value["accepted_real_slots"] == [1, 2]
    assert value["previous_source_main"] == module.PREVIOUS_MAIN
    assert value["slot"] == 3 and value["approval_result"] == "NOT_GUARANTEED"


@pytest.mark.parametrize("damage", [
    "source", "worker", "repair-map", "authority", "checker", "history", "exit-bool",
    "exit-one", "author", "clock", "slot", "claim-slot", "budget", "entry-slot",
    "policy", "closed-after-start", "prior-return-after-start", "repair", "rss-bool",
])
def test_readiness_rejects_mixed_release_original_time_and_repair(monkeypatch, damage):
    module = subject()
    policy, tree, report, actual, claim, entry, predecessor, repair, save = readiness_fixture(
        module, monkeypatch)
    if damage == "source":
        report["source_main"] = module.PREVIOUS_MAIN
    elif damage in ("worker", "authority", "checker"):
        report[damage + "_sha256"] = "0" * 64
    elif damage == "repair-map":
        report["repair_source_sha256"][module.INTENT] = "0" * 64
    elif damage == "history":
        report["predecessor"]["closed_ms"] -= 1
    elif damage in ("exit-bool", "exit-one"):
        actual["responses"][0]["result"]["exit_code"] = False if damage == "exit-bool" else 1
    elif damage == "author":
        actual["author"] = "/root"
    elif damage == "clock":
        actual["responses"][0]["returned_ms"] += 300000
    elif damage == "slot":
        report["slot"] = 2
    elif damage == "claim-slot":
        claim["slot"] = 2
    elif damage == "budget":
        report["attempt_budget_sha256"] = "0" * 64
    elif damage == "entry-slot":
        entry["slot"] = 2
    elif damage == "policy":
        policy["filing_repair_sources"] = []
    elif damage == "closed-after-start":
        predecessor["closed_ms"] = module.START + 1001
    elif damage == "prior-return-after-start":
        predecessor["prior_recovery"]["verified_returned_ms"] = module.START + 1001
    elif damage == "repair":
        repair["approval_outcome"] = "GUARANTEED"
    else:
        report["self_rss_bytes"] = True
    save()
    with pytest.raises((ValueError, KeyError)):
        module.verified_readiness(policy, tree)


def test_real_production_validator_is_exercised_only_with_synthetic_buffers():
    module = subject()
    base = module._base()
    tree = {name: module.sha(base._read(REPO / name)) for name in module.REPAIR_SOURCES}
    value = module._repair(dict(filing_repair_sources=list(module.REPAIR_SOURCES)), tree)
    assert value["synthetic_positive"] and len(value["rejected_synthetic_cases"]) == 17
    assert value["actual_intents_written"] == value["actual_events_filed"] == 0


def test_repair_probe_rejects_current_source_mixed_with_another_freeze():
    module = subject()
    base = module._base()
    tree = {name: module.sha(base._read(REPO / name)) for name in module.REPAIR_SOURCES}
    tree[module.INTENT] = "0" * 64
    with pytest.raises(ValueError, match="source buffer"):
        module._repair(dict(filing_repair_sources=list(module.REPAIR_SOURCES)), tree)


def test_repair_inventory_cannot_omit_actor_or_its_privileged_entry():
    module = subject()
    with pytest.raises(ValueError, match="inventory"):
        module._repair(dict(filing_repair_sources=[module.INTENT]), {})
